migrate:
	uv run python -m src.manage makemigrations server
	uv run python -m src.manage migrate


flush: 
	uv run python -m src.manage flush 

run:
	uv run python -m src.core

clean: 
	rm -rf ./src/server/migrations ./src/db.sqlite3
