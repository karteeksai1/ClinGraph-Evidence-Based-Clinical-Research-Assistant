import logging

logger = logging.getLogger(__name__)


class PineconeVectorStore:
    def __init__(self, api_key: str, index_host: str, namespace: str):
        self.enabled = bool(api_key and index_host)
        self.namespace = namespace
        self.index = None
        if not self.enabled:
            return
        try:
            from pinecone import Pinecone

            self.index = Pinecone(api_key=api_key).Index(host=index_host)
        except Exception:
            logger.exception("Pinecone initialization failed; using local dense retrieval")
            self.enabled = False

    def upsert(self, documents: list, batch_size: int = 100) -> None:
        if not self.enabled or not documents:
            return
        try:
            for start in range(0, len(documents), batch_size):
                batch = documents[start:start + batch_size]
                vectors = [
                    {
                        "id": document.document_id,
                        "values": list(document.embedding),
                        "metadata": {
                            "title": document.title,
                            "source": document.source,
                            "url": document.url or "",
                            "publication_date": document.publication_date or "",
                            "text": document.text[:35000],
                        },
                    }
                    for document in batch
                ]
                self.index.upsert(vectors=vectors, namespace=self.namespace)
        except Exception:
            logger.exception("Pinecone upsert failed; continuing with local retrieval")

    def query(self, vector: tuple[float, ...], top_k: int) -> dict[str, float]:
        if not self.enabled:
            return {}
        try:
            response = self.index.query(vector=list(vector), top_k=top_k, include_metadata=False, namespace=self.namespace)
            return {match.id: float(match.score) for match in response.matches}
        except Exception:
            logger.exception("Pinecone query failed; continuing with local retrieval")
            return {}
