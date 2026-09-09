import uuid
from datetime import datetime
from pydantic import BaseModel

class DocumentSummary(BaseModel):
    id: uuid.UUID
    file_name: str
    source_type: str
    status: str
    uploaded_by: str | None
    created_at: datetime
    parent_chunks: int
    child_chunks: int
    embeddings_generated: int

class DocumentDetail(DocumentSummary):
    source_path: str
    error_message: str | None
    extra_metadata: dict