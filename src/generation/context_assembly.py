from dataclasses import dataclass
from uuid import UUID
from langchain_core.documents import Document as LCDocument
from sqlalchemy import select
from sqlalchemy.orm import session
from src.core.models import Chunk, SourceDocument

@dataclass
class ContextSource:
    chunk_id: UUID
    document_id: UUID
    file_name: str
    source_path: str
    content: str
    page: int | None = None

def assembly_context(retrieved_docs: list[LCDocument], db: session) -> list[ContextSource]:
    parent_ids: list[UUID] = []
    seen: set[str] = set()

    for doc in retrieved_docs:
        parent_id_str = doc.metadata.get("parent_chunk_id")
        if parent_id_str and parent_id_str not in seen:
            seen.add(parent_id_str)
            parent_ids.append(UUID(parent_id_str))

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
            continue
        chunk, source_doc = rows_by_id[parent_id]
        sources.append(
            ContextSource(
                chunk_id=chunk.id,
                document_id=source_doc.id,
                file_name=source_doc.file_name,
                source_path=source_doc.source_path,
                content=chunk.content,
                page=chunk.extra_metadata.get("page"),
            )
        )
    return sources

