.PHONY: dev backend ai frontend build test

dev:
	docker compose up --build

backend:
	cd services/backend && uvicorn app.main:app --reload --port 8000

ai:
	cd services/ai && uvicorn app.main:app --reload --port 8001

frontend:
	cd services/frontend && npm install && npm run dev

build:
	docker compose build

test:
	python3 -m compileall -q services
