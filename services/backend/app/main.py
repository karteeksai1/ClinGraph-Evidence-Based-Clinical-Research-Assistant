import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .schemas import IngestResponse, ResearchResponse, SearchRequest, SearchResponse

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


async def ai_post(path: str, payload: dict) -> dict:
    try:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.post(f"{settings.ai_service_url}{path}", json=payload)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text[:500]
        raise HTTPException(status_code=exc.response.status_code, detail=detail) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=503, detail="AI service is unavailable") from exc


@app.get("/health")
async def health() -> dict[str, str]:
    try:
        async with httpx.AsyncClient(timeout=3) as client:
            response = await client.get(f"{settings.ai_service_url}/health")
            response.raise_for_status()
        return {"status": "ok", "service": "backend", "ai_service": "ok"}
    except httpx.HTTPError:
        return {"status": "degraded", "service": "backend", "ai_service": "unavailable"}


@app.post("/api/v1/search", response_model=SearchResponse)
async def search(request: SearchRequest) -> SearchResponse:
    return SearchResponse(**await ai_post("/internal/v1/search", request.model_dump()))


@app.post("/api/v1/research", response_model=ResearchResponse)
async def research(request: SearchRequest) -> ResearchResponse:
    return ResearchResponse(**await ai_post("/internal/v1/research", request.model_dump()))


@app.post("/api/v1/ingest/{source}", response_model=IngestResponse)
async def ingest(source: str, request: SearchRequest) -> IngestResponse:
    if source not in {"pubmed", "clinicaltrials"}:
        raise HTTPException(status_code=404, detail="Unsupported evidence source")
    return IngestResponse(**await ai_post(f"/internal/v1/ingest/{source}", request.model_dump()))
