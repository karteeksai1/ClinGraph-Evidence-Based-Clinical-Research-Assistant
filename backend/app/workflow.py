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
    """LangGraph workflow for traceable evidence synthesis.

    The graph is intentionally provider-neutral. A production deployment can
    replace the planner and synthesis nodes with an LLM while keeping retrieval
    and citation verification as explicit, testable steps.
    """

    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
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
        query = state["query"].strip()
        return {"search_query": query}

    def retrieve(self, state: ResearchState) -> dict:
        # Replace this deterministic vector with the configured embedding model.
        query_embedding = (0.6, 0.7, 0.4)
        results = self.retriever.search(
            state["search_query"], query_embedding, state.get("limit", 10)
        )
        return {"results": results}

    @staticmethod
    def synthesize(state: ResearchState) -> dict:
        results = state.get("results", [])
        if not results:
            return {
                "answer": "No evidence was retrieved for this question.",
                "claims": [],
                "citations": [],
            }

        claims = [
            f"Retrieved evidence is relevant to the research question: {result['title']}."
            for result in results
        ]
        citations = [result["document_id"] for result in results]
        answer = "Evidence summary based on the retrieved sources: " + " ".join(claims)
        return {"answer": answer, "claims": claims, "citations": citations}

    @staticmethod
    def verify(state: ResearchState) -> dict:
        claims = state.get("claims", [])
        citations = state.get("citations", [])
        if claims and citations:
            return {"confidence": "low — demo evidence pipeline; human review required"}
        return {"confidence": "insufficient evidence"}

    def invoke(self, query: str, limit: int = 10) -> ResearchState:
        return self.graph.invoke({"query": query, "limit": limit})
