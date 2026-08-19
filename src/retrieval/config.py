from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "retrieval.yaml"

class RetrievalConfig(BaseModel):
    vector_top_k: int
    bm25_top_k: int
    fusion_weights: dict[str, float]

@lru_cache
def get_retrieval_config() -> RetrievalConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return RetrievalConfig(**raw)