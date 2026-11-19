from fastapi import FastAPI, HTTPException

from .config import get_settings
from .retrieval import Document, HybridRetriever
from .schemas import IngestRequest, IngestResponse, ResearchResponse, SearchRequest, SearchResponse
from .sources import ClinicalTrialsClient, PubMedClient, SourceError
from .workflow import ClinicalResearchWorkflow

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
retriever = HybridRetriever([
    Document("demo-001", "Evidence synthesis for hypertension interventions",
             "hypertension blood pressure intervention clinical trial evidence"),
    Document("demo-002", "Clinical outcomes in type 2 diabetes",
             "type 2 diabetes clinical outcomes glucose intervention evidence"),
], settings.bm25_weight, settings.dense_weight)
workflow = ClinicalResearchWorkflow(retriever)


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "service": "ai", "documents": retriever.count()}


@app.post("/internal/v1/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return SearchResponse(query=request.query, results=retriever.search(request.query, request.limit))


@app.post("/internal/v1/research", response_model=ResearchResponse)
def research(request: SearchRequest) -> ResearchResponse:
    state = workflow.invoke(request.query, request.limit)
    return ResearchResponse(query=request.query, answer=state.get("answer", ""), claims=state.get("claims", []),
                            citations=state.get("citations", []), confidence=state.get("confidence", "insufficient evidence"),
                            results=state.get("results", []))


def ingest(source: str, request: IngestRequest) -> IngestResponse:
    try:
        documents = (PubMedClient() if source == "pubmed" else ClinicalTrialsClient()).search(request.query, request.limit)
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    retriever.upsert_many(documents)
    return IngestResponse(source=source, imported=len(documents), total_documents=retriever.count())


@app.post("/internal/v1/ingest/pubmed", response_model=IngestResponse)
def ingest_pubmed(request: IngestRequest) -> IngestResponse:
    return ingest("pubmed", request)


@app.post("/internal/v1/ingest/clinicaltrials", response_model=IngestResponse)
def ingest_clinicaltrials(request: IngestRequest) -> IngestResponse:
    return ingest("clinicaltrials.gov", request)
