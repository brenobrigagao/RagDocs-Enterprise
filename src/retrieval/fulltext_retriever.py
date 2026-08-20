from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import text
from sqlalchemy.orm import Session

class PgFullTextRetriever(BaseRetriever):
    model_config = {"arbitrary_types_allowed": True}

    db: Session
    top_k: int = 20

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:
        stmt = text(
            """
            SELECT id, content, extra_metadata, document_id, parent_chunk_id,
                   ts_rank_cd(content_tsv, websearch_to_tsquery('portuguese', :query)) AS score
            FROM chunks
            WHERE chunk_level = 'CHILD'
              AND content_tsv @@ websearch_to_tsquery('portuguese', :query)
            ORDER BY score DESC
            LIMIT :top_k
            """
        )
        rows = self.db.execute(
            stmt, {"query": query, "top_k": self.top_k}
        ).mappings().all()

        return [
            LCDocument(
                page_content=row["content"],
                metadata={
                    "chunk_id": str(row["id"]),
                    "document_id": str(row["document_id"]),
                    "parent_chunk_id": str(row["parent_chunk_id"]) if row["parent_chunk_id"] else None,
                    "score": float(row["score"]),
                    "retrieval_source": "fulltext",
                    **row["extra_metadata"],
                },
            )
            for row in rows
        ]
