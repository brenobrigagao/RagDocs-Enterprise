from fastapi import FastAPI
from src.api.routes import ingestion

app = FastAPI(
    title="RagDocs Enterprise API",
    description="Q&A on internal technical documentation via RAG",
    version="0.1.0",
)

app.include_router(ingestion.router)

@app.get("/health")
def health_check() -> dict[str,str]:
    return {"status":"ok"}
