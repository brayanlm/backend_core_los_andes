.PHONY: migrate upgrade downgrade current history

# ─── Alembic Migrations ──────────────────────────────────────────

migrate:   ## Generate new migration:  make migrate msg="description"
	python -m alembic revision --autogenerate -m "$(msg)"

upgrade:   ## Apply all pending migrations
	python -m alembic upgrade head

downgrade: ## Rollback last migration:  make downgrade  (or pass -1, -2, etc.)
	python -m alembic downgrade $(n)

current:   ## Show current migration version
	python -m alembic current

history:   ## Show full migration history
	python -m alembic history

# ─── Development ──────────────────────────────────────────────────

run:       ## Start the FastAPI dev server
	python -m uvicorn main:app --reload --port 8010
