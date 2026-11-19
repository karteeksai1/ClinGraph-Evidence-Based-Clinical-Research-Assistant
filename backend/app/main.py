from fastapi import FastAPI

from .config import get_settings
from .retrieval import Document, HybridRetriever
from .schemas import SearchRequest, SearchResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")

retriever = HybridRetriever(
    documents=[
        Document(
            document_id="demo-001",
            title="Evidence synthesis for hypertension interventions",
            text="hypertension blood pressure intervention clinical trial evidence",
            embedding=(0.9, 0.8, 0.1),
        ),
        Document(
            document_id="demo-002",
            title="Clinical outcomes in type 2 diabetes",
            text="type 2 diabetes clinical outcomes glucose intervention evidence",
            embedding=(0.2, 0.7, 0.9),
        ),
    ],
    bm25_weight=settings.bm25_weight,
    dense_weight=settings.dense_weight,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "environment": settings.app_env}


@app.post("/api/v1/search", response_model=SearchResponse)
def search(request: SearchRequest) -> SearchResponse:
    # Replace this deterministic vector with the configured embedding service.
    query_embedding = (0.6, 0.7, 0.4)
    return SearchResponse(
        query=request.query,
        results=retriever.search(request.query, query_embedding, request.limit),
    )
