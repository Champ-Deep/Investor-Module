.PHONY: dev test stress lint format typecheck migrate seed seed-taxonomy ingest derive embed cadence docker-up docker-down

export PYTHONPATH := src

dev:
	uvicorn cadence.server:app --reload --port 8123 --app-dir src

test:
	pytest

stress:
	pytest -m stress

lint:
	ruff check src tests

format:
	ruff format src tests

typecheck:
	mypy src

migrate:
	python -m cadence.db.migrate

seed-taxonomy:
	python -m cadence.taxonomy.load

seed:
	python -m cadence.seed.generate

ingest:
	python -m cadence.ingest.run

derive:
	python -m cadence.ingest.derive

embed:
	python -m cadence.embeddings.build

cadence:
	python -m cadence.cadence.compute

docker-up:
	docker compose -f ../docker-compose.yml up -d

docker-down:
	docker compose -f ../docker-compose.yml down
