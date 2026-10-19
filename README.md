
# RagDocs Enterprise

Sistema de Q&A sobre documentação técnica interna, com pipeline de
recuperação avançado (Hybrid Search + Reranking + Chunking Hierárquico),
avaliação contínua (Ragas) e observabilidade completa (Langfuse + LangSmith).

> Status: em construção, épico a épico.

## Stack

FastAPI · LangChain · Streamlit · PostgreSQL + PGVector · Groq (LLM, free tier) ·
bge embeddings/reranker (local) · Ragas · Langfuse + LangSmith · Docker Compose

## Como rodar (progresso atual)

```bash
cp .env.example .env
# edite o .env: defina POSTGRES_PASSWORD e demais chaves conforme necessário

docker compose up -d      # sobe Postgres + PGVector
python scripts/init_db.py # cria as tabelas
```

Ingestão de um arquivo local (via CLI, provisório até o endpoint da API existir):

```bash
python scripts/ingest_local.py caminho/do/arquivo.pdf
```

## Estrutura do projeto
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
