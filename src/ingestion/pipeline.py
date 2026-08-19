import hashlib
from pathlib import Path

from sqlalchemy.orm import Session

from src.core.models import SourceDocument, IngestionStatus ,SourceType
from src.ingestion.loaders.factory import detect_source_type, load_file

from src.chunking.persistence import persist_chunks

def compute_file_hash(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()

def ingest_file(
        file_path: str | Path,
        db: Session,
        uploaded_by: str | None = None,
) -> SourceDocument:
    path = Path(file_path)
    content_hash = compute_file_hash(path)

    existing = db.query(SourceDocument).filter_by(content_hash=content_hash).first()
    if existing is not None:
        return existing

    document = SourceDocument(
        content_hash=content_hash,
        source_type=SourceType(detect_source_type(path)),
        source_path=str(path.resolve()),
        file_name=path.name,
        uploaded_by=uploaded_by,
        status=IngestionStatus.PROCESSING,
    )
    db.add(document)
    db.flush()

    try:
        langchain_docs = load_file(path)
        document.extra_metadata = {
            "num_pages_or_parts": len(langchain_docs),
        }
        document.status = IngestionStatus.COMPLETED

        db.flush()
        chunks = persist_chunks(
            document_id=document.id,
            langchain_docs=langchain_docs,
            db=db,
            file_extension=path.suffix.lower(),
        )
        document.extra_metadata["chunks_created"] = len(chunks)
    except Exception as exc:
        document.status = IngestionStatus.FAILED
        document.error_message = str(exc)

    db.commit()
    db.refresh(document)
    return document