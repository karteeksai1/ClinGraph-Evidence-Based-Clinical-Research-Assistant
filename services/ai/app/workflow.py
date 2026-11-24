from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .retrieval import HybridRetriever
from .tools import EvidenceTools


class ResearchState(TypedDict, total=False):
    query: str
    limit: int
    search_query: str
    results: list[dict]
    claims: list[str]
    citations: list[str]
    answer: str
    confidence: str
    tool_calls: list[dict]
    judge: dict
    agent_trace: list[str]


class ClinicalResearchWorkflow:
    def __init__(self, retriever: HybridRetriever, synthesizer=None):
        self.retriever = retriever
        self.synthesizer = synthesizer
        self.tools = EvidenceTools(retriever)
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ResearchState)
        graph.add_node("plan", self.plan)
        graph.add_node("researcher", self.retrieve)
        graph.add_node("synthesize", self.synthesize)
        graph.add_node("judge", self.verify)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "researcher")
        graph.add_edge("researcher", "synthesize")
        graph.add_edge("synthesize", "judge")
        graph.add_edge("judge", END)
        return graph.compile()

    @staticmethod
    def plan(state: ResearchState) -> dict:
        return {"search_query": " ".join(state["query"].split())}

    def retrieve(self, state: ResearchState) -> dict:
        self.tools.reset()
        results = self.tools.search_evidence(state["search_query"], state.get("limit", 10))
        return {"results": results, "agent_trace": ["researcher:search_evidence"]}

    def synthesize(self, state: ResearchState) -> dict:
        results = state.get("results", [])
        if not results:
            return {"answer": "No evidence was retrieved for this question.", "claims": [], "citations": []}
        citations = [result["document_id"] for result in results]
        if self.synthesizer:
            answer = self.synthesizer.synthesize(state["query"], results)
            if answer:
                return {
                    "answer": answer,
                    "claims": [f"Evidence was synthesized from [{citation}]." for citation in citations],
                    "citations": citations,
                }
        claims = [f"{result['title']} is a retrieved source relevant to the query [{result['document_id']}]." for result in results]
        lines = [f"- {result['title']}: {result['excerpt']} [{result['document_id']}]" for result in results]
        return {"answer": "Retrieved evidence is summarized below. This is research support, not medical advice.\n" + "\n".join(lines),
                "claims": claims, "citations": citations}

    def verify(self, state: ResearchState) -> dict:
        citations = set(state.get("citations", []))
        errors = [claim for claim in state.get("claims", []) if not any(f"[{citation}]" in claim for citation in citations)]
        judge = self.synthesizer.judge(state["query"], state.get("answer", ""), state.get("results", [])) if self.synthesizer else None
        if judge is None:
            judge = {"valid": not errors and bool(citations), "score": 0.8 if citations and not errors else 0.2,
                     "issues": errors, "corrected_answer": ""}
        if judge.get("corrected_answer") and not judge.get("valid", False):
            state_answer = judge["corrected_answer"]
        else:
            state_answer = state.get("answer", "")
        if errors:
            confidence = "blocked — citation verification failed"
        elif not judge.get("valid", False):
            confidence = "low — judge found unsupported claims"
        else:
            confidence = "moderate — retrieved evidence requires human review" if citations else "insufficient evidence"
        return {"confidence": confidence, "answer": state_answer, "judge": judge,
                "tool_calls": [call.__dict__ for call in self.tools.calls],
                "agent_trace": state.get("agent_trace", []) + ["judge:grounding_check"]}

    def invoke(self, query: str, limit: int = 10) -> ResearchState:
        return self.graph.invoke({"query": query, "limit": limit})
