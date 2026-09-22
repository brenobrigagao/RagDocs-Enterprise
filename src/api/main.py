import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session

from src.api.deps import get_db
from src.api.routes import documents, ingestion, query
from src.embeddings.service import get_embedding_model
from src.retrieval.reranker import get_reranker_model

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing the API and preloading models...")
    try:
        logger.info("Loading embeddings model...")
        get_embedding_model()
        logger.info("Loading reranker model...")
        get_reranker_model()
        logger.info("Models loaded. API ready!")
    except Exception as exc:
        logger.critical("Failed to load models at startup: %s", exc, exc_info=True)
        raise exc

    yield
    logger.info("Shutting down the API...")

app = FastAPI(
    title="RagDocs Enterprise API",
    description="Q&A on internal technical documentation via RAG",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(ingestion.router)
app.include_router(documents.router)
app.include_router(query.router)

@app.get("/health", status_code=status.HTTP_200_OK)
def health_check(db: Session = Depends(get_db)) -> dict[str,str]:
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        logger.error("Health check failed: database inaccessible (%s)", exc)
        return {"status":"unhealthy", "database": "disconnected"}
