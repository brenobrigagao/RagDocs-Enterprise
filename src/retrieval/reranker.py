import logging
import os
from functools import lru_cache
from pathlib import Path

import yaml
from langchain_classic.retrievers import ContextualCompressionRetriever
from langchain_classic.retrievers.document_compressors import CrossEncoderReranker
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.retrievers import BaseRetriever
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "reranker.yaml"
)
CONFIG_PATH = Path(os.getenv("RERANKER_CONFIG_PATH", DEFAULT_CONFIG_PATH))


class RerankerConfig(BaseModel):
    model_name: str = Field(
        ..., min_length=1, description="Hugging Face model name or path"
    )
    top_n: int = Field(
        5, gt=0, description="Number of reranked documents to return"
    )
    model_kwargs: dict = Field(
        default_factory=dict,
        description="Extra model arguments (e.g., {'device': 'cuda'})",
    )


@lru_cache(maxsize=1)
def get_reranker_config(path: Path = CONFIG_PATH) -> RerankerConfig:
    if not path.exists():
        raise FileNotFoundError(f"Reranker configuration file not found: {path}")

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        if not isinstance(raw, dict):
            raise ValueError(f"Invalid content in YAML file: {path}")

        return RerankerConfig.model_validate(raw)
    except Exception as exc:
        logger.error("Error loading reranker configuration (%s): %s", path, exc)
        raise exc


@lru_cache(maxsize=1)
def get_reranker_model(config_key: str | None = None) -> HuggingFaceCrossEncoder:
    config = get_reranker_config()
    logger.info("Loading Hugging Face Cross-Encoder model: %s", config.model_name)

    return HuggingFaceCrossEncoder(
        model_name=config.model_name,
        model_kwargs=config.model_kwargs,
    )


def build_reranking_retriever(
    base_retriever: BaseRetriever,
    config: RerankerConfig | None = None,
) -> ContextualCompressionRetriever:
    config = config or get_reranker_config()
    model = get_reranker_model()

    logger.debug("Building Reranker | model=%s | top_n=%d", config.model_name, config.top_n)

    reranker = CrossEncoderReranker(model=model, top_n=config.top_n)

    return ContextualCompressionRetriever(
        base_compressor=reranker,
        base_retriever=base_retriever,
    )