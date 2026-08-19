import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.chunking.parent_child import chunk_document
from src.ingestion.loaders.factory import load_file

docs = load_file("README.md")
chunks = chunk_document(docs, file_extension=".md")

parents = [c for c in chunks if c["chunk_level"] == "parent"]
children = [c for c in chunks if c["chunk_level"] == "child"]

print(f"{len(parents)} parent(s), {len(children)} child(ren)")
for p in parents:
    print(f"  parent {p['chunk_index']}: {p['token_count']} tokens")