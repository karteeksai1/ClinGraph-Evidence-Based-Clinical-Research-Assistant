.PHONY: backend ai frontend install test

install:
	python3 -m pip install -r services/ai/requirements.txt -r services/backend/requirements.txt
	cd services/frontend && npm install

backend:
	cd services/backend && uvicorn app.main:app --reload --port 8000

ai:
	cd services/ai && uvicorn app.main:app --reload --port 8001

frontend:
	cd services/frontend && npm install && npm run dev

test:
	python3 -m compileall -q services
