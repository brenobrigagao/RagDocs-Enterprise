import logging
import os
from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent.parent / "config" / "generation.yaml"
)
CONFIG_PATH = Path(os.getenv("GENERATION_CONFIG_PATH", DEFAULT_CONFIG_PATH))


class GenerationConfig(BaseModel):
    temperature: float = Field(
        0.2,
        ge=0.0,
        le=2.0,
        description="Sampling temperature for text generation (0.0 to 2.0)",
    )
    max_tokens: int = Field(
        1024,
        gt=0,
        description="Maximum number of tokens allowed in the generated response",
    )
    max_retries: int = Field(
        3,
        ge=0,
        description="Maximum number of retry attempts for failed LLM requests",
    )


@lru_cache(maxsize=1)
def get_generation_config(path: Path = CONFIG_PATH) -> GenerationConfig:
    if not path.exists():
        raise FileNotFoundError(
            f"Generation configuration file not found: {path}"
        )

    try:
        with open(path, encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}

        if not isinstance(raw, dict):
            raise ValueError(
                f"Invalid content in configuration file (expected a dictionary): {path}"
            )

        return GenerationConfig.model_validate(raw)
    except Exception as exc:
        logger.error("Error loading generation configuration (%s): %s", path, exc)
        raise exc