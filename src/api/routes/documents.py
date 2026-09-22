import os
import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.documents import DocumentDetail, DocumentSummary
from src.core.models import Chunk, ChunkLevel, SourceDocument

router = APIRouter(prefix="/documents", tags=["documents"])

def _get_chunk_counts(document_id: uuid.UUID, db: Session) -> tuple[int,int,int]:
    stmt = select(
        func.coalesce(func.count().filter(Chunk.chunk_level == ChunkLevel.PARENT), 0),
        func.coalesce(func.count().filter(Chunk.chunk_level == ChunkLevel.CHILD), 0),
        func.coalesce(
            func.count().filter(
                        Chunk.chunk_level == ChunkLevel.CHILD, Chunk.embedding.is_not(None)
                    )
        ),
        0,
    ).where(Chunk.document_id == document_id)
    
    return db.execute(stmt).one()

@router.get("", response_model=list[DocumentSummary])
def list_documents(
    db: Session = Depends(get_db),
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> list[DocumentSummary]:
    stmt = (
        select(
            SourceDocument,
            func.coalesce(func.count().filter(Chunk.chunk_level == ChunkLevel.PARENT), 0).label("parents"),
            func.coalesce(func.count().filter(Chunk.chunk_level == ChunkLevel.CHILD), 0).label("children"),
            func.coalesce(
                func.count().filter(
                    Chunk.chunk_level == ChunkLevel.CHILD, Chunk.embedding.is_not(None)
                ),
                0,
            ).label("embeddings"),
        )
        .outerjoin(Chunk, SourceDocument.id == Chunk.document_id)
        .group_by(SourceDocument.id)
        .order_by(SourceDocument.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    rows = db.execute(stmt).all()

    return [
        DocumentSummary(
            id=doc.id,
            file_name=doc.file_name,
            source_type=doc.source_type.value if hasattr(doc.source_type, "value") else doc.source_type,
            status=doc.status.value if hasattr(doc.status, "value") else doc.status,
            uploaded_by=doc.uploaded_by,
            created_at=doc.created_at,
            parent_chunks=parents,
            child_chunks=children,
            embeddings_generated=embeddings,
        )
        for doc, parents, children, embeddings in rows
    ]
   
@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> DocumentDetail:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    parents, children, embeddings = _get_chunk_counts(doc.id, db)

    return DocumentDetail(
        id=doc.id,
        file_name=doc.file_name,
        source_type=doc.source_type.value if hasattr(doc.source_type, "value") else doc.source_type,
        status=doc.status.value if hasattr(doc.status, "value") else doc.status,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        source_path=doc.source_path,
        error_message=doc.error_message,
        extra_metadata=doc.extra_metadata,
        parent_chunks=parents,
        child_chunks=children,
        embeddings_generated=embeddings,
    )

@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID, db: Session = Depends(get_db)
) -> None:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )
    if doc.source_path and os.path.exists(doc.source_path):
        try:
            os.remove(doc.source_path)
        except OSError:
            pass

    db.delete(doc)
    db.commit()
