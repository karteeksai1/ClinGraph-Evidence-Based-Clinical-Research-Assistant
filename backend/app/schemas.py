from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    document_id: str
    title: str
    excerpt: str = ""
    source: str = "local"
    url: str | None = None
    publication_date: str | None = None
    bm25_score: float
    dense_score: float
    hybrid_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]


class ResearchRequest(SearchRequest):
    """Request for the LangGraph evidence workflow."""


class ResearchResponse(BaseModel):
    query: str
    answer: str
    claims: list[str]
    citations: list[str]
    confidence: str
    results: list[SearchResult]


class IngestRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class IngestResponse(BaseModel):
    source: str
    imported: int
    total_documents: int
