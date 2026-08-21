from langchain_core.callbacks import CallbackManagerForRetrieverRun
from langchain_core.documents import Document as LCDocument
from langchain_core.retrievers import BaseRetriever
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.retrieval.filters import RetrievalFilters

class PgFullTextRetriever(BaseRetriever):
    model_config = {"arbitrary_types_allowed": True}

    db: Session
    top_k: int = 20
    filters = RetrievalFilters | None = None

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun
    ) -> list[LCDocument]:

        filter_sql, filter_params = (
            self.filters.to_sql_conditions() if self.filters else ("", {})
        )

        stmt = text(
            """
            SELECT c.id, c.content, c.extra_metadata, c.document_id, c.parent_chunk_id,
                   ts_rank_cd(c.content_tsv, websearch_to_tsquery('portuguese', :query)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            WHERE c.chunk_level = 'CHILD'
              AND c.content_tsv @@ websearch_to_tsquery('portuguese', :query)
            {filter_sql}
            ORDER BY score DESC
            LIMIT :top_k
            """
        )
        
        rows = self.db.execute(
            stmt, {"query": query, "top_k": self.top_k, **filter_params}
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
