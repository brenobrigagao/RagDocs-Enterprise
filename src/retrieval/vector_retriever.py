from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.embeddings.service import embed_query

class PGVectorChildRetriever(BaseRetriever):
    model_config = {"arbitrary_types_allowed": True}

    db: Session
    top_k: int = 20

    def _get_relevant_documents(
            self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        query_vector = embed_query(query)
        vector_literal = "[" + ",".join(str(v) for v in query_vector) + "]"

        stmt = text(
             """
            SELECT id, content, extra_metadata, document_id, parent_chunk_id,
                   1 - (embedding <=> :query_vector::vector) AS score
            FROM chunks
            WHERE chunk_level = 'CHILD' AND embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector::vector
            LIMIT :top_k
            """
        )
        rows = self.db.execute(
            stmt, {"query_vector": vector_literal, "top_k": self.top_k}
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