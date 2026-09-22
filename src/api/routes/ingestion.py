import uuid
from pathlib import Path
from typing import Callable

from fastapi import APIRouter, BackgroundTasks, Depends, File, UploadFile, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.ingestion import IngestedFileResult, IngestUploadResponse
from src.core.database import SessionLocal  
from src.core.models import IngestionStatus, SourceDocument
from src.ingestion.pipeline import ingest_file

router = APIRouter(prefix="/ingest", tags=["ingestion"])

RAW_DATA_DIR = Path("data/raw")

async def _save_upload_to_disk_async(upload: UploadFile) -> Path:
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    safe_filename = Path(upload.filename or "file").name
    unique_prefix = uuid.uuid4().hex[:8]
    destination = RAW_DATA_DIR / f"{unique_prefix}_{safe_filename}"

    with destination.open("wb") as buffer:
        while chunk := await upload.read(1024 * 1024): 
            buffer.write(chunk)

    return destination

def _run_ingestion_task(document_id: uuid.UUID, file_path: Path, uploaded_by: str) -> None:
    with SessionLocal as db:
        try:
            ingest_file(file_path=file_path, db=db, document_id=document_id, uploaded_by=uploaded_by)
        except Exception as exc:
            doc = db.get(SourceDocument, document_id)
            if doc:
                doc.status = IngestionStatus.FAILED
                doc.error_message = str(exc)
                db.commit()

@router.post(
        "/upload", 
        response_model=IngestUploadResponse,
        status_code=status.HTTP_202_ACCEPTED
)
async def upload_documents(
    background_tasks: BackgroundTasks,
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db)
) -> IngestUploadResponse:
    results: list[IngestedFileResult] = []

    for upload in files:
        safe_filename = Path(upload.filename or "desconhecido").name
        try:
            saved_path = await _save_upload_to_disk_async(upload)
            document = SourceDocument(
                id=uuid.uuid4(),
                file_name=safe_filename,
                source_path=str(saved_path.resolve()),
                status=IngestionStatus.PROCESSING,
                uploaded_by="api-upload",
            )
            db.add(document)
            db.commit()
            db.refresh(document)

            background_tasks.add_task(
                _run_ingestion_task,
                document_id=document.id,
                file_path=saved_path,
                uploaded_by="api-upload",
            )
            results.append(
                IngestedFileResult(
                    file_name=safe_filename,
                    status=IngestionStatus.PROCESSING.value,
                    document_id=document.id,
                    error_message=None,
                )
            )

        except Exception as exc:
            results.append(
                IngestedFileResult(
                    file_name=safe_filename,
                    status=IngestionStatus.FAILED.value,
                    document_id=None,
                    error_message=str(exc),
                )
            )

    processing_count = sum(1 for r in results if r.status == IngestionStatus.PROCESSING.value)
    failed_count = sum(1 for r in results if r.status == IngestionStatus.FAILED.value)

    return IngestUploadResponse(
        total=len(results),
        completed=processing_count,  
        failed=failed_count,
        results=results,
    )