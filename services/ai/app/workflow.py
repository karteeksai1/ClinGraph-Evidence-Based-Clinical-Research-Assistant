from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .retrieval import HybridRetriever


class ResearchState(TypedDict, total=False):
    query: str
    limit: int
    search_query: str
    results: list[dict]
    claims: list[str]
    citations: list[str]
    answer: str
    confidence: str


class ClinicalResearchWorkflow:
    def __init__(self, retriever: HybridRetriever, synthesizer=None):
        self.retriever = retriever
        self.synthesizer = synthesizer
        self.graph = self._build_graph()

    def _build_graph(self):
        graph = StateGraph(ResearchState)
        graph.add_node("plan", self.plan)
        graph.add_node("retrieve", self.retrieve)
        graph.add_node("synthesize", self.synthesize)
        graph.add_node("verify", self.verify)
        graph.add_edge(START, "plan")
        graph.add_edge("plan", "retrieve")
        graph.add_edge("retrieve", "synthesize")
        graph.add_edge("synthesize", "verify")
        graph.add_edge("verify", END)
        return graph.compile()

    @staticmethod
    def plan(state: ResearchState) -> dict:
        return {"search_query": " ".join(state["query"].split())}

    def retrieve(self, state: ResearchState) -> dict:
        return {"results": self.retriever.search(state["search_query"], state.get("limit", 10))}

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

    @staticmethod
    def verify(state: ResearchState) -> dict:
        citations = set(state.get("citations", []))
        errors = [claim for claim in state.get("claims", []) if not any(f"[{citation}]" in claim for citation in citations)]
        if errors:
            return {"confidence": "blocked — citation verification failed"}
        return {"confidence": "moderate — retrieved evidence requires human review" if citations else "insufficient evidence"}

    def invoke(self, query: str, limit: int = 10) -> ResearchState:
        return self.graph.invoke({"query": query, "limit": limit})
