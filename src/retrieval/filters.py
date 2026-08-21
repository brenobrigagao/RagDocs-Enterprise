import uuid
from pydantic import BaseModel

class RetrievalFilters(BaseModel):
    source_types: list[str] | None = None
    document_ids: list[uuid.UUID] | None = None

    def to_sql_conditions(self) -> tuple[str, dict]:
        conditions: list[str] = []
        params: dict = {}

        if self.source_types:
            conditions.append("d.source_type = ANY(:source_types)")
            params["source_types"] = self.source_types
        if self.document_ids:
            conditions.append("c.document_id = ANY(:document_ids)")
            params["document_ids"] = [str(doc_id) for doc_id in self.document_ids]

        if not conditions:
            return "", {}
        return " AND " + " AND ".join(conditions), params