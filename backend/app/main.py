from fastapi import FastAPI, HTTPException

from .config import get_settings
from .retrieval import Document, HybridRetriever
from .schemas import (
    IngestRequest,
    IngestResponse,
    ResearchRequest,
    ResearchResponse,
    SearchRequest,
    SearchResponse,
)
from .sources import ClinicalTrialsClient, PubMedClient, SourceError
from .workflow import ClinicalResearchWorkflow

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

retriever = HybridRetriever(
    documents=[
        Document(
            document_id="demo-001",
            title="Evidence synthesis for hypertension interventions",
            text="hypertension blood pressure intervention clinical trial evidence",
        ),
        Document(
            document_id="demo-002",
            title="Clinical outcomes in type 2 diabetes",
            text="type 2 diabetes clinical outcomes glucose intervention evidence",
        ),
    ],
    bm25_weight=settings.bm25_weight,
    dense_weight=settings.dense_weight,
)
workflow = ClinicalResearchWorkflow(retriever)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.post("/api/v1/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    return SearchResponse(
        query=request.query,
        results=retriever.search(request.query, request.limit),
    )


@app.post("/api/v1/research", response_model=ResearchResponse)
def research(request: ResearchRequest) -> ResearchResponse:
    state = workflow.invoke(request.query, request.limit)
    return ResearchResponse(
        query=request.query,
        answer=state.get("answer", ""),
        claims=state.get("claims", []),
        citations=state.get("citations", []),
        confidence=state.get("confidence", "insufficient evidence"),
        results=state.get("results", []),
    )


@app.post("/api/v1/ingest/pubmed", response_model=IngestResponse)
def ingest_pubmed(request: IngestRequest) -> IngestResponse:
    try:
        documents = PubMedClient().search(request.query, request.limit)
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    retriever.upsert_many(documents)
    return IngestResponse(source="pubmed", imported=len(documents), total_documents=retriever.count())


@app.post("/api/v1/ingest/clinicaltrials", response_model=IngestResponse)
def ingest_clinicaltrials(request: IngestRequest) -> IngestResponse:
    try:
        documents = ClinicalTrialsClient().search(request.query, request.limit)
    except SourceError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    retriever.upsert_many(documents)
    return IngestResponse(source="clinicaltrials.gov", imported=len(documents), total_documents=retriever.count())
