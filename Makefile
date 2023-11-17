start:
	docker compose up --build

start-prod:
	docker compose -f docker-compose.production.yml up --build