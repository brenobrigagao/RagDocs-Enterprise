import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.schemas.query import QueryRequest, QueryResponse, QuerySource
from src.generation.context_assembly import assemble_context
from src.generation.groq_client import generate_answer
from src.retrieval.filters import RetrievalFilters
from src.retrieval.hybrid import build_full_retriever

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/query", tags=["query"])

@router.post("", response_model=QueryResponse)
def ask_question(request: QueryRequest, db: Session = Depends(get_db)) -> QueryResponse:
    try:

        filters = None
        if request.source_types or request.document_ids:
            filters = RetrievalFilters(
                source_types=request.source_types,
                document_ids=request.document_ids,
            )

        retriever = build_full_retriever(db, filters=filters)
        retrieved_docs = retriever.invoke(request.question)

        if not retrieved_docs:
            logger.info("No relevant documents found for the question: %s", request.question)
            return QueryResponse(
                answer="Sorry, I did not find information in the document database to answer this question.",
                model_used="none",
                sources=[]
            )

        sources = assemble_context(retrieved_docs, db)
        answer, model_used = generate_answer(request.question, sources)

        return QueryResponse(
            answer=answer,
            model_used=model_used,
            sources=[
                QuerySource(
                    chunk_id=s.chunk_id,
                    document_id=s.document_id,
                    file_name=s.file_name,
                    source_path=s.source_path,
                    page=s.page,
                )
                for s in sources
            ],
        )
    except Exception as exc:
        logger.info("Error generating response for the question '%s': %s", request.question, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An internal error occurred while processing your question. Please try again later."
        )