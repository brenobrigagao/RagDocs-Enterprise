import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database import SessionLocal
from src.retrieval.hybrid import build_full_retriever

def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/test_retrieval.py 'sua pergunta aqui'")
        sys.exit(1)

    query = sys.argv[1]
    db = SessionLocal()
    try:
        retriever = build_full_retriever(db)
        results = retriever.invoke(query)
        print(f"{len(results)} resultado(s) para: {query!r}\n")
        for i, doc in enumerate(results):
            print(f"--- resultado {i} (fonte: {doc.metadata.get('retrieval_source')}) ---")
            print(doc.page_content[:150])
            print()
    finally:
        db.close()


if __name__ == "__main__":
    main()