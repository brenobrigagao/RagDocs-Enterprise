from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.api.routes import ingestion, documents
from src.embeddings.service import get_embedding_model
from src.retrieval.reranker import get_reranker_model

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Loading embeddings model...")
    get_embedding_model()
    print("Loading reranker model...")
    get_reranker_model()
    print("Models loaded. API ready!")

    yield

app = FastAPI(
    title="RagDocs Enterprise API",
    description="Q&A on internal technical documentation via RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(ingestion.router)
app.include_router(documents.router)

@app.get("/health")
def health_check() -> dict[str,str]:
    return {"status":"ok"}
