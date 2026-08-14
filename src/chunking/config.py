from functools import lru_cache
from pathlib import Path

import yaml
from pydantic import BaseModel

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "chunking.yaml"

class ChunkingConfig(BaseModel):
    parent_chunk_size: int
    parent_chunk_overlap: int
    child_chunk_size: int
    child_chunk_overlap: int

@lru_cache
def get_chunking_config() -> ChunkingConfig:
    with open(CONFIG_PATH, encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return ChunkingConfig(**raw)