import logging
import uuid

from langchain_core.documents import Document as LCDocument
from sqlalchemy.orm import Session

from src.chunking.parent_child import chunk_document
from src.core.models import Chunk, ChunkLevel

logger = logging.getLogger(__name__)


def persist_chunks(
    document_id: uuid.UUID,
    langchain_docs: list[LCDocument],
    db: Session,
    file_extension: str | None = None,
) -> list[Chunk]:
    chunk_dicts = chunk_document(langchain_docs, file_extension)

    created_chunks: list[Chunk] = []
    parent_ids: set[uuid.UUID] = set()

    try:
        parent_counter = 0
        for item in chunk_dicts:
            if item["chunk_level"] != "parent":
                continue

            parent_uuid = uuid.UUID(item["chunk_id"])
            parent_ids.add(parent_uuid)

            created_chunks.append(
                Chunk(
                    id=parent_uuid,
                    document_id=document_id,
                    parent_chunk_id=None,
                    chunk_level=ChunkLevel.PARENT,
                    content=item["content"],
                    token_count=item["token_count"],
                    chunk_index=parent_counter,
                    extra_metadata=dict(item["extra_metadata"]),
                )
            )
            parent_counter += 1

        child_counter = 0
        for item in chunk_dicts:
            if item["chunk_level"] != "child":
                continue

            parent_uuid = uuid.UUID(item["parent_id"])
            if parent_uuid not in parent_ids:
                raise ValueError(
                    f"Parent {parent_uuid} not found for child chunk."
                )

            created_chunks.append(
                Chunk(
                    id=uuid.UUID(item["chunk_id"]),
                    document_id=document_id,
                    parent_chunk_id=parent_uuid,
                    chunk_level=ChunkLevel.CHILD,
                    content=item["content"],
                    token_count=item["token_count"],
                    chunk_index=child_counter,
                    extra_metadata=dict(item["extra_metadata"]),
                )
            )
            child_counter += 1

        db.add_all(created_chunks)
        db.commit()
        return created_chunks

    except Exception:
        db.rollback()
        logger.exception("Error persisting document chunks %s", document_id)
        raise