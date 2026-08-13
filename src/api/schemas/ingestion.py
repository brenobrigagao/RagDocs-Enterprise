import uuid
from pydantic import BaseModel

class IngestedFileResult(BaseModel):
    file_name: str
    status: str
    document_id: uuid.UUID | None = None
    error_message: str | None = None

class IngestUploadResponse(BaseModel):
    total: int
    completed: int
    failed: int
    results: list[IngestedFileResult]