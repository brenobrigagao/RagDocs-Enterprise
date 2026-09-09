import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from src.api.deps import get_db
from src.api.schemas.documents import DocumentDetail, DocumentSummary
from src.core.models import Chunk, ChunkLevel, SourceDocument

router = APIRouter(prefix="/documents", tags=["documents"])

def _chunk_counts(document_id: uuid.UUID, db: Session) -> tuple[int,int,int]:
    stmt = select(
        func.count().filter(Chunk.chunk_level == ChunkLevel.PARENT),
        func.count().filter(Chunk.chunk_level == ChunkLevel.CHILD),
        func.count().filter(
            Chunk.chunk_level == ChunkLevel.CHILD, Chunk.embedding.is_not(None)
        ),
    ).where(Chunk.document_id == document_id)
    parents, children, embeddings = db.execute(stmt).one()
    return parents, children, embeddings

@router.get("", response_model=list[DocumentSummary])
def list_documents(db: Session = Depends(get_db)) -> list[DocumentSummary]:
    documents = db.scalars(
        select(SourceDocument).order_by(SourceDocument.created_at.desc())
    ).all()

    result = []
    for doc in documents:
        parents, children, embeddings = _chunk_counts(doc.id, db)
        result.append(
            DocumentSummary(
                id=doc.id,
                file_name=doc.file_name,
                source_type=doc.source_type.value,
                status=doc.status.value,
                uploaded_by=doc.uploaded_by,
                created_at=doc.created_at,
                parent_chunks=parents,
                child_chunks=children,
                embeddings_generated=embeddings,
            )
        )
    return result

@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> DocumentDetail:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    parents, children, embeddings = _chunk_counts(doc.id, db)
    return DocumentDetail(
        id=doc.id,
        file_name=doc.file_name,
        source_type=doc.source_type.value,
        status=doc.status.value,
        uploaded_by=doc.uploaded_by,
        created_at=doc.created_at,
        source_path=doc.source_path,
        error_message=doc.error_message,
        extra_metadata=doc.extra_metadata,
        parent_chunks=parents,
        child_chunks=children,
        embeddings_generated=embeddings,
    )

@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    doc = db.get(SourceDocument, document_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(doc)
    db.commit()
