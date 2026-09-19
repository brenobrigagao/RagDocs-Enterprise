import logging
from functools import lru_cache
import torch
from langchain_huggingface import HuggingFaceEmbeddings
from src.embeddings.config import get_embedding_config

logger = logging.getLogger(__name__)

@lru_cache(maxsize=1)
def get_embedding_model() -> HuggingFaceEmbeddings:
    config = get_embedding_config()

    if torch.cuda.is_available():
        device = "cuda"
    elif torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"

    logger.info(
        "Loading embeddings model '%s' onto device '%s'",
        config.model_name,
        device,
    )

    return HuggingFaceEmbeddings(
        model_name=config.model_name,
        model_kwargs={"device": device},
        encode_kwargs={
            "normalize_embeddings": True,
            "batch_size": config.batch_size,
        },
    )

def embed_texts(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    config = get_embedding_config()
    model = get_embedding_model()
    vectors = model.embed_documents(texts)
    if vectors and len(vectors[0]) != config.dimension:
        raise ValueError(
            f"Model dimension ({len(vectors[0])}) differs from the configured dimension ({config.dimension}).",
        )
    return vectors

def embed_query(text: str) -> list[float]:
    if not text or not text.strip():
        raise ValueError("The query text cannot be empty.")

    config = get_embedding_config()
    model = get_embedding_model()
    vector =    model.embed_query(text)

    if len(vector) != config.dimension:
        raise ValueError(
            f"The query vector dimension ({len(vector)}) differs from the configured one ({config.dimension})."
        )
    return vector