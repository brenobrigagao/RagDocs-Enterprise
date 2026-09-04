import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database import SessionLocal
from src.generation.context_assembly import assemble_context
from src.generation.groq_client import generate_answer
from src.retrieval.hybrid import build_full_retriever


def main() -> None:
    if len(sys.argv) != 2:
        print("Uso: python scripts/test_generation.py 'sua pergunta'")
        sys.exit(1)

    question = sys.argv[1]
    db = SessionLocal()
    try:
        retriever = build_full_retriever(db)
        retrieved_docs = retriever.invoke(question)

        sources = assemble_context(retrieved_docs, db)
        print(f"{len(sources)} fonte(s) (parent chunks únicos) encontrada(s)\n")

        answer, model_used = generate_answer(question, sources)

        print(f"=== Resposta (modelo: {model_used}) ===")
        print(answer)
        print("\n=== Fontes ===")
        for s in sources:
            page_info = f", pág. {s.page}" if s.page is not None else ""
            print(f"- {s.file_name}{page_info} ({s.source_path})")
    finally:
        db.close()


if __name__ == "__main__":
    main()