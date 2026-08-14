import shutil 
import uuid
from pathlib import Path
from fastapi import APIRouter, Depends, File, UploadFile
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.ingestion import IngestedFileResult, IngestUploadResponse
from src.core.models import IngestionStatus
from src.ingestion.pipeline import ingest_file

router = APIRouter(prefix="/ingest", tags=["ingestion"])

RAW_DATA_DIR = Path("data/raw")

def _save_upload_to_disk(upload: UploadFile) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    unique_prefix = uuid.uuid4().hex[:8]
    destination = RAW_DATA_DIR / f"{unique_prefix}_{upload.filename}"

    with destination.open("wb") as buffer:
        shutil.copyfileobj(upload.file, buffer)

    return destination

@router.post("/uplaod", response_model=IngestUploadResponse)
async def upload_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
) -> IngestUploadResponse:
    results: list[IngestedFileResult] = []
    for upload in files:
        try:
            saved_path = _save_upload_to_disk(upload)
            document = ingest_file(
                saved_path, db, uploaded_by="api-upload"
            )
            results.append(
                IngestedFileResult(
                    file_name=upload.filename or saved_path.name,
                    status=document.status.value,
                    document_id=document.id,
                    error_message=document.error_message,
                )
            )
        except Exception as exc:
            results.append(
                file_name=upload.filename or "unknown",
                status=IngestionStatus.FAILED.value,
                document_id=None,
                error_message=str(exc),
            )

    completed = sum(1 for r in results if r.status == IngestionStatus.COMPLETED.value)
    failed = sum(1 for r in results if r.status == IngestionStatus.FAILED.value)

    return IngestUploadResponse(
        total=len(results),
        completed=completed,
        failed=failed,
        results=results,
    )