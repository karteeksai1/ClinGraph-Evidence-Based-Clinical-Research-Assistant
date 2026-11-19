from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    query: str = Field(min_length=2, max_length=500)
    limit: int = Field(default=10, ge=1, le=50)


class SearchResult(BaseModel):
    document_id: str
    title: str
    bm25_score: float
    dense_score: float
    hybrid_score: float


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
