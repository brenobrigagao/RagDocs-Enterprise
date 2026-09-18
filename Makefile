.PHONY: up down logs ps db-shell run dashboard

## Sobe a infraestrutura (Postgres + PGVector)
up:
	docker compose up -d

## Derruba tudo
down:
	docker compose down

## Acompanha os logs de todos os serviços
logs:
	docker compose logs -f

## Lista os serviços rodando
ps:
	docker compose ps

## Abre um shell psql dentro do container do Postgres
db-shell:
	docker compose exec postgres psql -U $(POSTGRES_USER) -d $(POSTGRES_DB)

## Sobe a API em modo desenvolvimento (fora do Docker, local)
run:
	uvicorn src.api.main:app --reload --reload-dir src --reload-dir config

## Sobe o dashboard Streamlit
dashboard:
	streamlit run dashboard/app.py