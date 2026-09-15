import uuid
from pydantic import BaseModel

class QueryRequest(BaseModel):
    question: str
    source_types: list[str] | None = None
    document_ids: list[uuid.UUID] | None = None

class QuerySource(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    file_name: str
    source_path: str
    page: int | None = None

class QueryResponse(BaseModel):
    answer: str
    model_used: str
    sources: list[QuerySource]
