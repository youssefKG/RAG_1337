
flush: 
	uv run python -m src.server.manage flush

run:
	uv run python -m src

clean: 
	rm -rf ./src/processed/*
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf .venv *.egg-info

lint:
	$(UV) run flake8 $(PROJECT)
	$(UV) run mypy $(PROJECT) --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

remigrate:
	rm -rf src/processed/db.sqlite3
	uv run python -m src.server.manage makemigrations server
	uv run python -m src.server.manage migrate

install:
	uv sync
	uv run python src.server.manage makemigrations server
	uv run python src.server.manage migrate
	
