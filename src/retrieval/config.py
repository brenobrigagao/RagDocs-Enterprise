import os
import logging
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "retrieval.yaml"
)
CONFIG_PATH = Path(os.getenv("RETRIEVAL_CONFIG_PATH", DEFAULT_CONFIG_PATH))

class RetrievalConfig(BaseModel):
    vector_top_k: int = Field(
        20, gt=0, description="Number of candidates returned by vector search"
    )
    bm25_top_k: int = Field(
        20, gt=0, description="Number of candidates returned by full-text search"
    )
    fusion_weights: dict[str, float] = Field(
        default_factory=lambda: {"vector": 0.5, "bm25": 0.5},
        description="Weights assigned to each strategy in result fusion",
    )

    @field_validator("fusion_weights")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        if not v:
            raise ValueError("fusion_weights cannot be empty.")
        for key, weight in v.items():
            if weight < 0:
                raise ValueError(
                    f"The weight for key '{key}' cannot be negative: {weight}"
                )
        return v

@lru_cache(maxsize=1)
def get_retrieval_config(path: Path = CONFIG_PATH) -> RetrievalConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Retrieval configuration file not found: {path}"
        )
    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
        if not isinstance(raw, dict):
            raise ValueError(
                f"The content of file {path} must be a valid YAML dictionary."
            )
        return RetrievalConfig.model_validate(raw)
    except Exception as exc:
        logger.error("Failed to load retrieval configuration (%s): %s", path, exc)
        raise exc