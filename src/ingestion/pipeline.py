import hashlib
from pathlib import Path
import logging
from sqlalchemy.orm import Session

from src.core.models import SourceDocument, IngestionStatus ,SourceType
from src.ingestion.loaders.factory import detect_source_type, load_file

from src.chunking.persistence import persist_chunks
from src.embeddings.generate import generate_embeddings_for_documents
import uuid

logger = logging.getLogger(__name__)

def compute_file_hash(path: Path) -> str:
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    return sha256.hexdigest()

def ingest_file(
    file_path: str | Path,
    db: Session,
    document_id: uuid.UUID | None = None,
    uploaded_by: str | None = None,
) -> SourceDocument:
    path = Path(file_path)
    content_hash = compute_file_hash(path)

    query = db.query(SourceDocument).filter(SourceDocument.content_hash == content_hash)
    if document_id:
        query = query.filter(SourceDocument.id != document_id)

    existing = query.first()
    if existing is not None:
        return existing

    if document_id:
        document = db.get(SourceDocument, document_id)
        if not document:
            raise ValueError(f"SourceDocument with ID {document_id} was not found.")
        document.content_hash = content_hash
        document.source_type = SourceType(detect_source_type(path))
    else:
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
        document.status = IngestionStatus.PROCESSING
        
        langchain_docs = load_file(path)
        document.extra_metadata = {
            "num_pages_or_parts": len(langchain_docs),
        }

        chunks = persist_chunks(
            document_id=document.id,
            langchain_docs=langchain_docs,
            db=db,
            file_extension=path.suffix.lower(),
        )
        document.extra_metadata = {
            **document.extra_metadata, 
            "chunks_created": len(chunks)}

        embeddings_count = generate_embeddings_for_documents(document.id, db)
        document.extra_metadata = document.extra_metadata = {
            **document.extra_metadata, 
            "embeddings_generated": embeddings_count}

        document.status = IngestionStatus.COMPLETED
        db.commit()

    except Exception as exc:
        logger.exception("Error ingesting document %s", document.id)
        db.rollback()
        document = db.get(SourceDocument, document.id)
        document.status = IngestionStatus.FAILED
        document.error_message = str(exc)
        db.commit()

    db.refresh(document)
    return document