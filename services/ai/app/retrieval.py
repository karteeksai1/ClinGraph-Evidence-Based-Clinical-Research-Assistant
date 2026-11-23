import math
import re
from collections import Counter
from dataclasses import dataclass

TOKEN_PATTERN = re.compile(r"[a-z0-9]+")


def tokenize(value: str) -> list[str]:
    return TOKEN_PATTERN.findall(value.lower())


class LocalEmbedder:
    """Sentence Transformers embedder running fully on the local machine."""

    def __init__(self, model_name: str, device: str = "cpu", local_files_only: bool = False):
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError as exc:
            raise RuntimeError(
                "sentence-transformers is required for local embeddings. "
                "Install services/ai/requirements.txt."
            ) from exc
        self.model_name = model_name
        self.model = SentenceTransformer(
            model_name,
            device=device,
            local_files_only=local_files_only,
        )

    def embed_query(self, text: str) -> tuple[float, ...]:
        if hasattr(self.model, "encode_query"):
            vector = self.model.encode_query(text, normalize_embeddings=True)
        else:
            vector = self.model.encode(text, normalize_embeddings=True)
        return tuple(float(value) for value in vector)

    def embed_document(self, text: str) -> tuple[float, ...]:
        if hasattr(self.model, "encode_document"):
            vector = self.model.encode_document(text, normalize_embeddings=True)
        else:
            vector = self.model.encode(text, normalize_embeddings=True)
        return tuple(float(value) for value in vector)


@dataclass(frozen=True)
class Document:
    document_id: str
    title: str
    text: str
    source: str = "local"
    url: str | None = None
    publication_date: str | None = None
    embedding: tuple[float, ...] = ()


class HybridRetriever:
    def __init__(self, documents: list[Document] | None = None, bm25_weight: float = 0.5,
                 dense_weight: float = 0.5, embedder: LocalEmbedder | None = None,
                 vector_store=None):
        total = bm25_weight + dense_weight
        if total <= 0:
            raise ValueError("BM25 and dense weights must sum to a positive value")
        self.bm25_weight = bm25_weight / total
        self.dense_weight = dense_weight / total
        self.embedder = embedder or LocalEmbedder()
        self.vector_store = vector_store
        self.documents: list[Document] = []
        self._tokenized: dict[str, list[str]] = {}
        self._document_frequency: Counter[str] = Counter()
        self._average_document_length = 1.0
        self.upsert_many(documents or [])

    def upsert_many(self, documents: list[Document]) -> None:
        current = {document.document_id: document for document in self.documents}
        for document in documents:
            embedding = document.embedding or self.embedder.embed_document(f"{document.title} {document.text}")
            current[document.document_id] = Document(**{**document.__dict__, "embedding": embedding})
        self.documents = list(current.values())
        self._rebuild_statistics()
        if self.vector_store:
            self.vector_store.upsert(self.documents)

    def count(self) -> int:
        return len(self.documents)

    def search(self, query: str, limit: int = 10) -> list[dict]:
        query_tokens = tokenize(query)
        query_embedding = self.embedder.embed_query(query)
        bm25_scores = [self._bm25(query_tokens, document.document_id) for document in self.documents]
        pinecone_scores = self.vector_store.query(query_embedding, limit) if self.vector_store else {}
        dense_scores = [
            pinecone_scores.get(document.document_id, self._cosine(query_embedding, document.embedding))
            for document in self.documents
        ]
        max_bm25 = max(bm25_scores, default=0.0) or 1.0
        results = []
        for document, bm25_score, dense_score in zip(self.documents, bm25_scores, dense_scores):
            normalized_bm25 = bm25_score / max_bm25
            normalized_dense = max(0.0, min(1.0, (dense_score + 1.0) / 2.0))
            hybrid_score = self.bm25_weight * normalized_bm25 + self.dense_weight * normalized_dense
            results.append({
                "document_id": document.document_id,
                "title": document.title,
                "excerpt": self._excerpt(document.text),
                "source": document.source,
                "url": document.url,
                "publication_date": document.publication_date,
                "bm25_score": round(bm25_score, 4),
                "dense_score": round(normalized_dense, 4),
                "hybrid_score": round(hybrid_score, 4),
            })
        return sorted(results, key=lambda item: item["hybrid_score"], reverse=True)[:limit]

    def _rebuild_statistics(self) -> None:
        self._tokenized = {document.document_id: tokenize(f"{document.title} {document.text}") for document in self.documents}
        self._document_frequency = Counter()
        for tokens in self._tokenized.values():
            self._document_frequency.update(set(tokens))
        lengths = [len(tokens) for tokens in self._tokenized.values()]
        self._average_document_length = sum(lengths) / len(lengths) if lengths else 1.0

    def _bm25(self, query_tokens: list[str], document_id: str, k1: float = 1.2, b: float = 0.75) -> float:
        document_tokens = self._tokenized.get(document_id, [])
        term_counts = Counter(document_tokens)
        document_count = max(len(self.documents), 1)
        score = 0.0
        for token in query_tokens:
            frequency = term_counts.get(token, 0)
            if not frequency:
                continue
            idf = math.log(1 + (document_count - self._document_frequency[token] + 0.5) /
                           (self._document_frequency[token] + 0.5))
            denominator = frequency + k1 * (1 - b + b * len(document_tokens) / self._average_document_length)
            score += idf * (frequency * (k1 + 1)) / denominator
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

    @staticmethod
    def _excerpt(text: str, maximum: int = 360) -> str:
        compact = " ".join(text.split())
        return compact if len(compact) <= maximum else compact[: maximum - 1].rstrip() + "…"
