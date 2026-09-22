import logging
from dataclasses import dataclass
from uuid import UUID

from langchain_core.documents import Document as LCDocument
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models import Chunk, SourceDocument

logger = logging.getLogger(__name__)

@dataclass(frozen=True, slots=True)
class ContextSource:
    chunk_id: UUID
    document_id: UUID
    file_name: str
    source_path: str
    content: str
    page: int | None = None

def assemble_context(
        retrieved_docs: list[LCDocument], db: Session
) -> list[ContextSource]:
    if not retrieved_docs:
        return []
    
    parent_ids: list[UUID] = []
    seen: set[UUID] = set()

    for doc in retrieved_docs:
        raw_id = doc.metadata.get("parent_chunk_id") or doc.metadata.get("chunk_id")
        if not raw_id:
            continue
        try:
            chunk_uuid = UUID(str(raw_id)) if not isinstance(raw_id, UUID) else raw_id
            if chunk_uuid not in seen:
                seen.add(chunk_uuid)
                parent_ids.append(chunk_uuid)
        except (ValueError, TypeError) as exc:
            logger.warning("Invalid UUID found in document metadata ('%s'): %s", raw_id, exc)

    if not parent_ids:
        return []
    stmt = (
        select(Chunk, SourceDocument)
        .join(SourceDocument, SourceDocument.id == Chunk.document_id)
        .where(Chunk.id.in_(parent_ids))
    )

    rows = db.execute(stmt).all()
    rows_by_id = {chunk.id: (chunk, source_doc) for chunk, source_doc in rows}

    sources: list[ContextSource] = []
    for parent_id in parent_ids:
        if parent_id not in rows_by_id:
            logger.warning("Parent chunk ID %s not found in database.", parent_id)
            continue

        chunk, source_doc = rows_by_id[parent_id]
        extra_meta = chunk.extra_metadata or {}

        sources.append(
            ContextSource(
                chunk_id=chunk.id,
                document_id=source_doc.id,
                file_name=source_doc.file_name,
                source_path=source_doc.source_path,
                content=chunk.content,
                page=extra_meta.get("page"),
            )
        )

    return sources

