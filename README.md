# RagDocs Enterprise

**Production-ready RAG system for internal technical documentation.**

RagDocs Enterprise is a complete, professionally structured Retrieval-Augmented Generation platform designed to answer questions over internal product and company documentation with high accuracy, full traceability, and cost transparency.

### Key Features

- **Multi-source ingestion**: PDF, Markdown, TXT, Confluence, Notion, source code, and user uploads
- **Hierarchical (Parent-Child) chunking** for precision retrieval + rich generation context
- **Hybrid Search** (Vector + BM25) with configurable fusion
- **Local reranking** using BAAI/bge-reranker-v2-m3
- **Metadata filtering**
- **Full Ragas evaluation suite** (Faithfulness, Answer Relevancy, Context Precision/Recall, etc.)
- **Dual observability**: Langfuse + LangSmith
- **Quality & Cost Dashboard** (Streamlit) with per-question metrics and before/after experiment comparison
- **Zero LLM cost** via Groq free tier
- **FastAPI backend** + Docker Compose for reproducible deployment
- **PostgreSQL + PGVector** as the vector store

### Architecture Highlights
