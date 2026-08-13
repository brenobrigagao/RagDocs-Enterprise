
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
