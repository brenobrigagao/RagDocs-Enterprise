import logging
from langchain_classic.retrievers import ContextualCompressionRetriever, EnsembleRetriever
from langchain_core.retrievers import BaseRetriever
from sqlalchemy.orm import Session

from src.retrieval.config import RetrievalConfig, get_retrieval_config
from src.retrieval.filters import RetrievalFilters
from src.retrieval.fulltext_retriever import PgFullTextRetriever
from src.retrieval.reranker import build_reranking_retriever
from src.retrieval.vector_retriever import PgVectorChildRetriever

logger = logging.getLogger(__name__)

def build_hybrid_retriever(
    db: Session,
    filters: RetrievalFilters | None = None,
    config: RetrievalConfig | None = None,
) -> EnsembleRetriever:
    
    config = config or get_retrieval_config()

    vector_weight = config.fusion_weights.get("vector", 0.5)
    bm25_weight = config.fusion_weights.get("bm25", 0.5)

    logger.debug(
        "Initializing HybridRetriever | top_k(vector=%d, bm25=%d) | weights(vector=%.2f, bm25=%.2f)",
        config.vector_top_k,
        config.bm25_top_k,
        vector_weight,
        bm25_weight,
    )

    vector_retriever = PgVectorChildRetriever(
        db=db, top_k=config.vector_top_k, filters=filters
    )
    fulltext_retriever = PgFullTextRetriever(
        db=db, top_k=config.bm25_top_k, filters=filters
    )

    return EnsembleRetriever(
        retrievers=[vector_retriever, fulltext_retriever],
        weights=[vector_weight, bm25_weight],
    )

def build_full_retriever(
    db: Session,
    filters: RetrievalFilters | None = None,
    config: RetrievalConfig | None = None,
) -> BaseRetriever:
    hybrid_retriever = build_hybrid_retriever(db=db, filters=filters, config=config)
    return build_reranking_retriever(hybrid_retriever)