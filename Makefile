
UV = uv
PROJECT = src

run:
	uv run python -m src

clean: 
	rm -rf ./data/processed/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf .venv *.egg-info
	rm -rf UV_PROJECT_ENVIROMENEMENT

bonus: 
	uv run python3 -m src.server.manage runserver

lint:
	uv run mypy -m src --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
	uv run flake8 src

lint-strict:
	uv run mypy -m src --strict

install:
	uv sync
	uv run python -m src.server.manage makemigrations server
	uv run python -m src.server.manage migrate
