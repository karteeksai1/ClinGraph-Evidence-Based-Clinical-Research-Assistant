import logging

from fastapi import FastAPI, HTTPException

from .config import get_settings
from .retrieval import Document, HybridRetriever, LocalEmbedder
from .schemas import IngestRequest, IngestResponse, ResearchResponse, SearchRequest, SearchResponse
from .sources import ClinicalTrialsClient, PubMedClient, SourceError
from .storage import DocumentRepository
from .vector_store import PineconeVectorStore
from .llm import GroqSynthesizer
from .workflow import ClinicalResearchWorkflow

logging.basicConfig(level=logging.INFO)
settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
repository = DocumentRepository(settings.database_url)
repository.initialize()
vector_store = PineconeVectorStore(settings.pinecone_api_key, settings.pinecone_index_host, settings.pinecone_namespace)
demo_documents = [
    Document("demo-001", "Evidence synthesis for hypertension interventions",
             "hypertension blood pressure intervention clinical trial evidence"),
    Document("demo-002", "Clinical outcomes in type 2 diabetes",
             "type 2 diabetes clinical outcomes glucose intervention evidence"),
]
retriever = HybridRetriever(repository.list_documents() or demo_documents, settings.bm25_weight, settings.dense_weight,
    embedder=LocalEmbedder(
        model_name=settings.embedding_model,
        device=settings.embedding_device,
        local_files_only=settings.embedding_local_files_only,
    ),
    vector_store=vector_store,
)
workflow = ClinicalResearchWorkflow(retriever, GroqSynthesizer(settings.groq_api_key, settings.groq_model))


@app.get("/health")
def health() -> dict[str, str | int]:
    return {"status": "ok", "service": "ai", "documents": retriever.count(),
            "pinecone": "connected" if vector_store.enabled else "fallback",
            "database": "connected" if repository.enabled else "fallback",
            "llm": "groq" if workflow.synthesizer and workflow.synthesizer.enabled else "local"}


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
    repository.upsert_many(documents)
    retriever.upsert_many(documents)
    return IngestResponse(source=source, imported=len(documents), total_documents=retriever.count())


@app.post("/internal/v1/ingest/pubmed", response_model=IngestResponse)
def ingest_pubmed(request: IngestRequest) -> IngestResponse:
    return ingest("pubmed", request)


@app.post("/internal/v1/ingest/clinicaltrials", response_model=IngestResponse)
def ingest_clinicaltrials(request: IngestRequest) -> IngestResponse:
    return ingest("clinicaltrials.gov", request)
