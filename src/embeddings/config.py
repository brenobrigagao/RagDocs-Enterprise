from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "embedding.yaml"

class EmbeddingConfig(BaseModel):
    model_name: str
    dimension: int
    batch_size: int

@lru_cache
def get_embedding_config() -> EmbeddingConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return EmbeddingConfig(**raw)
