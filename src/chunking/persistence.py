import logging
import uuid 
from sqlalchemy.orm import Session

from src.chunking.parent_child import chunk_document
from src.core.models import Chunk, ChunkLevel
from langchain_core.documents import Document as LCDocument

logger = logging.getLogger(__name__)

def persist_chunks(
        document_id: uuid.UUID,
        langchain_docs: list[LCDocument],
        db: Session,
        file_extension: str | None = None
) -> list[Chunk]:
    chunk_dicts = chunk_document(langchain_docs,file_extension)

    parent_id_by_index: dict[int, uuid.UUID] = {}
    created_chunks: list[Chunk] = []
    try:
        for item in chunk_dicts:
            if item["chunk_level"] != "parent":
                continue

            parent_uuid = uuid.uuid4()
            parent_id_by_index[item["chunk_index"]] = parent_uuid

            chunk = Chunk(
                id=parent_uuid,
                document_id=document_id,
                parent_chunk_id=None,
                chunk_level=ChunkLevel.PARENT,
                content=item["content"],
                token_count=item["token_count"],
                chunk_index=item["chunk_index"],
                extra_metadata=dict(item["extra_metadata"]),
            )
            created_chunks.append(chunk)

        for item in chunk_dicts:
            if item["chunk_level"] != "child":
                continue

            parent_index = item["parent_index"]
            parent_db_id = parent_id_by_index.get(parent_index)

            if parent_db_id is None:
                raise ValueError(
                    f"Parent chunk with index {parent_index} was not found for the child."
                )
            chunk = Chunk(
                id=uuid.uuid4(),
                document_id=document_id,
                parent_chunk_id=parent_db_id,
                chunk_level=ChunkLevel.CHILD,
                content=item["content"],
                token_count=item["token_count"],
                chunk_index=item["chunk_index"],
                extra_metadata=dict(item["extra_metadata"]),
            )
            created_chunks.append(chunk)

        db.add_all(created_chunks)
        db.commit()
        return created_chunks

    except Exception as exc:
        db.rollback()
        logger.error(
            "Error persisting document chunks %s,: %s", document_id, exc
        )
        raise exc
