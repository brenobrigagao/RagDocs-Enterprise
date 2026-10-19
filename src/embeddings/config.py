import os 
import logging
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "embedding.yaml"
)
CONFIG_PATH = Path(os.getenv("EMBEDDING_CONFIG_PATH", DEFAULT_CONFIG_PATH))

class EmbeddingConfig(BaseModel):
    model_name: str = Field(..., min_length=1, description="Model name in the provider")
    dimension: int = Field(..., gt=0, description="Embedding vector dimension")
    batch_size: int = Field(64, gt=0, description="Batch size for sending to the model")

@lru_cache(maxsize=1)
def get_embedding_config(path: Path = CONFIG_PATH) -> EmbeddingConfig:
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            raw = yaml.safe_load(f)
        if not isinstance(raw, dict):
            raise ValueError(f"The content of the YAML file {path} must be a dictionary.")
        return EmbeddingConfig.model_validate(raw)
    except Exception as exc:
        logger.error("Failed to load embeddings configuration (%s): %s", path, exc)
        raise exc
    
