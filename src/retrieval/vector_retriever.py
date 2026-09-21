from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models import Chunk, ChunkLevel, SourceDocument
from src.embeddings.service import embed_query
from src.retrieval.filters import RetrievalFilters

class PgVectorChildRetriever(BaseRetriever):
    model_config = {"arbitrary_types_allowed": True}

    db: Session
    top_k: int = 20
    filters: RetrievalFilters | None = None

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        query_vector = embed_query(query)

        distance_expr = Chunk.embedding.cosine_distance(query_vector)
        stmt = (
            select(
                Chunk.id,
                Chunk.content,
                Chunk.extra_metadata,
                Chunk.document_id,
                Chunk.parent_chunk_id,
                (1 - distance_expr).label("score"),
            )
            .join(SourceDocument, Chunk.document_id == SourceDocument.id)
            .where(
                Chunk.chunk_level == ChunkLevel.CHILD,
                Chunk.embedding.is_not(None),
            )
        )
        if self.filters:
            if conditions := self.filters.to_sqlalchemy_conditions():
                stmt = stmt.where(*conditions)

        stmt = stmt.order_by(distance_expr).limit(self.top_k)
        rows = self.db.execute(stmt).mappings().all()

        return [
            LCDocument(
                page_content=row["content"],
                metadata={
                    "chunk_id": str(row["id"]),
                    "document_id": str(row["document_id"]),
                    "parent_chunk_id": str(row["parent_chunk_id"])
                    if row["parent_chunk_id"]
                    else None,
                    "score": float(row["score"]),
                    "retrieval_source": "vector",
                    **row["extra_metadata"],
                },
            )
            for row in rows
        ]