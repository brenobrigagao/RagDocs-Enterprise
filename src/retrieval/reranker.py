from functools import lru_cache
from pathlib import Path

import yaml
from langchain_core.retrievers import ContextualCompressionRetriever
from langchain_community.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.retrievers import BaseRetriever
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "reranker.yaml"

class RerankerConfig(BaseModel):
    model_name: str
    top_n: int

@lru_cache
def get_reranker_config() -> RerankerConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RerankerConfig(**raw)

@lru_cache
def get_reranker_model() -> HuggingFaceCrossEncoder:
    config = get_reranker_config()
    return HuggingFaceCrossEncoder(model_name=config.model_name)

def build_reranking_retriever(base_retriever: BaseRetriever) -> ContextualCompressionRetriever:
    config = get_reranker_config()
    reranker = CrossEncoderReranker(model=get_reranker_model(), top_n=config.top_n)

    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=base_retriever,
    )