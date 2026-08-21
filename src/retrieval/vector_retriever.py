from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.embeddings.service import embed_query
from src.retrieval.filters import RetrievalFilters

class PGVectorChildRetriever(BaseRetriever):
    model_config = {"arbitrary_types_allowed": True}

    db: Session
    top_k: int = 20
    filters: RetrievalFilters | None = None

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        query_vector = embed_query(query)
        vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

        filter_sql, filter_params = (
            self.filters.to_sql_conditions() if self.filters else ("", {})
        )

        stmt = text(
             """
            SELECT c.id, c.content, c.extra_metadata, c.document_id, c.parent_chunk_id,
                   1 - (c.embedding <=> :query_vector::vector) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.chunk_level = 'CHILD' AND c.embedding IS NOT NULL
            {filter_sql}
            ORDER BY c.embedding <=> :query_vector::vector
            LIMIT :top_k
            """
        )
        rows = self.db.execute(
            stmt, {"query_vector": vector_literal, "top_k": self.top_k, **filter_params}
        ).mappings().all()

        return [
            LCDocument(
                page_content=row["content"],
                metadata={
                    "chunk_id": str(row["id"]),
                    "document_id": str(row["document_id"]),
                    "parent_chunk_id": str(row["parent_chunk_id"]) if row["parent_chunk_id"] else None,
                    "score": float(row["score"]),
                    "retrieval_source": "vector",
                    **row["extra_metadata"],
                },
            )
            for row in rows
        ]