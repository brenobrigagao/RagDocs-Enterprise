.PHONY: up down logs ps db-shell dashboard

up:
	docker compose up -d

down: 
	docker composer down

logs:
	docker composer logs -f

ps: 
	docker composer ps

db-shell:
	docker compose exec postgres psql -U $${POSTGRES_USER} -d $${POSTGRES_DB}

run:
	uvicorn src.api.main:app --reload --reload-dir src --reload-dir config

dashboard:
	streamlit run dashboard/app.py