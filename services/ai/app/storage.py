import logging
from dataclasses import asdict

from sqlalchemy import DateTime, String, Text, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column

from .retrieval import Document

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


class DocumentRecord(Base):
    __tablename__ = "evidence_documents"

    document_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    title: Mapped[str] = mapped_column(Text)
    text: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(100), index=True)
    url: Mapped[str | None] = mapped_column(Text, nullable=True)
    publication_date: Mapped[str | None] = mapped_column(String(100), nullable=True)


class DocumentRepository:
    def __init__(self, database_url: str):
        self.enabled = bool(database_url)
        if database_url.startswith("postgresql://"):
            database_url = database_url.replace("postgresql://", "postgresql+psycopg://", 1)
        self.engine = create_engine(database_url, pool_pre_ping=True) if self.enabled else None

    def initialize(self) -> None:
        if not self.engine:
            return
        try:
            Base.metadata.create_all(self.engine)
        except Exception:
            logger.exception("Neon database initialization failed; using memory fallback")
            self.enabled = False

    def list_documents(self) -> list[Document]:
        if not self.engine or not self.enabled:
            return []
        try:
            with Session(self.engine) as session:
                rows = session.scalars(select(DocumentRecord)).all()
                return [Document(row.document_id, row.title, row.text, row.source, row.url, row.publication_date) for row in rows]
        except Exception:
            logger.exception("Unable to load evidence documents from Neon")
            return []

    def upsert_many(self, documents: list[Document]) -> None:
        if not self.engine or not self.enabled or not documents:
            return
        try:
            with Session(self.engine) as session:
                for document in documents:
                    values = asdict(document)
                    values.pop("embedding", None)
                    session.merge(DocumentRecord(**values))
                session.commit()
        except Exception:
            logger.exception("Unable to persist evidence documents to Neon")
