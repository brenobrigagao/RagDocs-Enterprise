import uuid
from pydantic import BaseModel, Field
from sqlalchemy import ColumnElement

from src.core.models import Chunk, SourceDocument, SourceType

class RetrievalFilters(BaseModel):
    source_types: list[SourceType] | None = Field(
        None, description="Filter by source document types"
    )
    document_ids: list[uuid.UUID] | None = Field(
        None, description="Filter by specific document IDs"
    )

    def to_sql_conditions(self) -> tuple[ColumnElement[bool]]:
        conditions: list[ColumnElement[bool]] = []

        if self.source_types:
            conditions.append(SourceDocument.source_type.in_(self.source_types))
        if self.document_ids:
            conditions.append(Chunk.document_id.in_(self.document_ids))
        return conditions