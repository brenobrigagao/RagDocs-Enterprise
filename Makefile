.PHONY: up down logs ps db-shell

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

