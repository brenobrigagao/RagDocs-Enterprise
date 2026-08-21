from langchain_core.retrievers import EnsembleRetriever
from langchain_core.retrievers import ContextualCompressionRetriever
from sqlalchemy.orm import Session

from src.retrieval.config import get_retrieval_config
from src.retrieval.reranker import build_reranking_retriever
from src.retrieval.fulltext_retriever import PgFullTextChildRetriever
from src.retrieval.vector_retriever import PgVectorChildRetriever

def build_hybrid_retriever(db: Session) -> EnsembleRetriever:
    config = get_retrieval_config()

    vector_retriever = PgVectorChildRetriever(db=db, top_k=config.vector_top_k)
    fulltext_retriever = PgFullTextChildRetriever(db=db, top_k=config.bm25_top_k)

    return EnsembleRetriever(
        retrievers=[vector_retriever, fulltext_retriever],
        weights=[config.fusion_weights["vector"], config.fusion_weights["bm25"]],
    )

def build_full_retriever(db: Session) -> ContextualCompressionRetriever:
    hybrid = build_hybrid_retriever(db)
    return build_reranking_retriever(hybrid)
