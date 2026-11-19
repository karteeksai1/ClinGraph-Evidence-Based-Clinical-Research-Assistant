import math
import re
from dataclasses import dataclass


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    text: str
    embedding: tuple[float, ...]


class HybridRetriever:
    """Initial BM25 + dense retrieval implementation.

    The dense vector is expected to come from the embedding service in production.
    This first slice keeps the retriever independent from a model provider.
    """

    def __init__(self, documents: list[Document], bm25_weight: float, dense_weight: float):
        total = bm25_weight + dense_weight
        if total <= 0:
            raise ValueError("BM25 and dense weights must sum to a positive value")
        self.documents = documents
        self.bm25_weight = bm25_weight / total
        self.dense_weight = dense_weight / total

    def search(self, query: str, query_embedding: tuple[float, ...], limit: int) -> list[dict]:
        query_tokens = TOKEN_PATTERN.findall(query.lower())
        bm25_scores = [self._bm25(query_tokens, doc.text) for doc in self.documents]
        dense_scores = [self._cosine(query_embedding, doc.embedding) for doc in self.documents]

        max_bm25 = max(bm25_scores, default=0.0) or 1.0
        ranked = []
        for doc, bm25_score, dense_score in zip(self.documents, bm25_scores, dense_scores):
            normalized_bm25 = bm25_score / max_bm25
            hybrid_score = self.bm25_weight * normalized_bm25 + self.dense_weight * dense_score
            ranked.append({
                "document_id": doc.document_id,
                "title": doc.title,
                "bm25_score": round(bm25_score, 4),
                "dense_score": round(dense_score, 4),
                "hybrid_score": round(hybrid_score, 4),
            })
        return sorted(ranked, key=lambda item: item["hybrid_score"], reverse=True)[:limit]

    @staticmethod
    def _bm25(query_tokens: list[str], text: str, k1: float = 1.2, b: float = 0.75) -> float:
        document_tokens = TOKEN_PATTERN.findall(text.lower())
        if not document_tokens:
            return 0.0
        document_length = len(document_tokens)
        average_length = max(document_length, 1)
        score = 0.0
        for token in query_tokens:
            frequency = document_tokens.count(token)
            if frequency:
                score += (frequency * (k1 + 1)) / (frequency + k1 * (1 - b + b * document_length / average_length))
        return score

    @staticmethod
    def _cosine(left: tuple[float, ...], right: tuple[float, ...]) -> float:
        if len(left) != len(right):
            return 0.0
        left_norm = math.sqrt(sum(value * value for value in left))
        right_norm = math.sqrt(sum(value * value for value in right))
        if not left_norm or not right_norm:
            return 0.0
        return sum(a * b for a, b in zip(left, right)) / (left_norm * right_norm)
