from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import session

from src.core.models import Chunk, ChunkLevel
from src.embeddings.service import embed_texts

def generate_embeddings_for_documents(document_id: UUID, db: session) -> int:
    stmt = select(Chunk).where(
        Chunk.document_id == document_id,
        Chunk.chunk_level == ChunkLevel.CHILD,
        Chunk.embedding.is_(None),
    )
    pending_chunks = db.scalars(stmt).all()

    if not pending_chunks:
        return 0

    texts = [chunk.content for chunk in pending_chunks]
    vectors = embed_texts(texts)

    for chunk, vector in zip(pending_chunks, vectors, strict=True):
        chunk.embedding = vector
    db.commit()
    return len(pending_chunks)

