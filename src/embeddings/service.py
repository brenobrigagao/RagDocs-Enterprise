from functools import lru_cache
from langchain_huggingface import HuggingFaceEmbeddings
from src.embeddings.config import get_embedding_config

@lru_cache
def get_embedding_model() -> HuggingFaceEmbeddings:
    config = get_embedding_config()
    return HuggingFaceEmbeddings(
        model_name=config.model_name,
        encode_kwargs={"normalize_embeddings": True}
    )

def embed_texts(texts: list[str]) -> list[list[float]]:
    model = get_embedding_model()
    return model.embed_documents(texts)

def embed_query(text: str) -> list[float]:
    model = get_embedding_model()
    return model.embed_query(text)