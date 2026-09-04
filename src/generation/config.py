from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "generation.yaml"

class GenerationConfig(BaseModel):
    temperature: float
    max_tokens: int
    max_retries: int

@lru_cache
def get_generation_config() -> GenerationConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return GenerationConfig(**raw)