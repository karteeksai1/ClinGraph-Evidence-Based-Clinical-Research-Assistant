"""Small, auditable tools exposed to the research agent.

Tools deliberately return evidence objects rather than free-form prose. This
keeps tool output grounded and makes tool-call accuracy/efficiency measurable.
"""

from dataclasses import dataclass
from typing import Any, Callable

from .retrieval import HybridRetriever


@dataclass
class ToolCall:
    name: str
    arguments: dict[str, Any]
    result_count: int = 0
    error: str | None = None


class EvidenceTools:
    def __init__(self, retriever: HybridRetriever):
        self.retriever = retriever
        self.calls: list[ToolCall] = []

    def search_evidence(self, query: str, limit: int = 8) -> list[dict]:
        call = ToolCall("search_evidence", {"query": query, "limit": limit})
        try:
            results = self.retriever.search(query, limit)
            call.result_count = len(results)
            return results
        except Exception as exc:
            call.error = str(exc)
            raise
        finally:
            self.calls.append(call)

    def get_source_metadata(self, document_id: str) -> dict | None:
        call = ToolCall("get_source_metadata", {"document_id": document_id})
        try:
            for document in self.retriever.documents:
                if document.document_id == document_id:
                    result = {
                        "document_id": document.document_id,
                        "title": document.title,
                        "source": document.source,
                        "url": document.url,
                        "publication_date": document.publication_date,
                    }
                    call.result_count = 1
                    return result
            return None
        finally:
            self.calls.append(call)

    def reset(self) -> None:
        self.calls.clear()

    @staticmethod
    def definitions() -> list[dict]:
        return [
            {"type": "function", "function": {"name": "search_evidence", "description": "Search the indexed clinical evidence corpus.", "parameters": {"type": "object", "properties": {"query": {"type": "string"}, "limit": {"type": "integer", "minimum": 1, "maximum": 20}}, "required": ["query"]}}},
            {"type": "function", "function": {"name": "get_source_metadata", "description": "Get provenance metadata for an indexed evidence document.", "parameters": {"type": "object", "properties": {"document_id": {"type": "string"}}, "required": ["document_id"]}}},
        ]
