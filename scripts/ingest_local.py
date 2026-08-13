import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database import SessionLocal
from src.ingestion.pipeline import ingest_file

def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/ingest_local.py <caminho_do_arquivo>")
        sys.exit(1)

    file_path = sys.argv[1]
    db = SessionLocal()
    try:
        document = ingest_file(file_path, db, uploaded_by="cli-local")
        print(f"id:           {document.id}")
        print(f"status:       {document.status.value}")
        print(f"content_hash: {document.content_hash}")
        print(f"source_type:  {document.source_type.value}")
        print(f"metadata:     {document.extra_metadata}")
    finally:
        db.close()

if __name__ == "__main__":
    main()