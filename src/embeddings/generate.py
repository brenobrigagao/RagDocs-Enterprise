import logging
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.core.models import Chunk, ChunkLevel
from src.embeddings.config import get_embedding_config
from src.embeddings.service import embed_texts

logger = logging.getLogger(__name__)

def generate_embeddings_for_documents(document_id: UUID, db: Session) -> int:
    stmt = select(Chunk).where(
        Chunk.document_id == document_id,
        Chunk.chunk_level == ChunkLevel.CHILD,
        Chunk.embedding.is_(None),
    )
    pending_chunks = list(db.scalars(stmt).all())

    if not pending_chunks:
        return 0

    config = get_embedding_config()
    batch_size = config.batch_size

    total_processed = 0
    try:
        for i in range(0, len(pending_chunks), batch_size):
            batch_chunks = pending_chunks[i : i + batch_size]
            texts = [chunk.content for chunk in batch_chunks]

            vectors = embed_texts(texts)

            for chunk, vector in zip(batch_chunks, vectors, strict=True):
                chunk.embedding = vector

            total_processed += len(batch_chunks)

        db.commit()
        return total_processed
    except Exception as exc:
        db.rollback()
        logger.error(
            "Error generating embeddings for document %s: %s", document_id, exc
        )
        raise exc


