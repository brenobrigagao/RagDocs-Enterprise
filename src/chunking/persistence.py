import uuid 
from sqlalchemy.orm import Session
from src.chunking.parent_child import chunk_document
from src.core.models import Chunk, ChunkLevel
from langchain_core.documents import Document as LCDocument

def persist_chunks(
        document_id: uuid.UUID,
        langchain_docs: list[LCDocument],
        db: Session,
        file_extension: str | None = None
) -> list[Chunk]:
    chunk_dicts = chunk_document(langchain_docs,file_extension)

    parent_id_by_index: dict[int, uuid.UUID] = {}
    created_chunks: list[Chunk] = []

    for item in chunk_dicts:
        if item["chunk_level"] != "parent":
            continue

        chunk = Chunk(
            document_id=document_id,
            parent_chunk_id=None,
            chunk_level=ChunkLevel.PARENT,
            content=item["content"],
            token_count=item["token_count"],
            chunk_index=item["chunk_index"],
            extra_metadata=item["extra_metadata"],
        )
        db.add(chunk)
        db.flush()
        parent_id_by_index[item["chunk_index"]] = chunk.id
        created_chunks.append(chunk)

    for item in chunk_dicts:
        if item["chunk_level"] != "child":
            continue

        parent_db_id = parent_id_by_index[item["parent_index"]]
        chunk = Chunk(
            document_id=document_id,
            parent_chunk_id=parent_db_id,
            chunk_level=ChunkLevel.CHILD,
            content=item["content"],
            token_count=item["token_count"],
            chunk_index=item["chunk_index"],
            extra_metadata=item["extra_metadata"],
        )
        db.add(chunk)
        created_chunks.append(chunk)

    db.commit()
    return created_chunks