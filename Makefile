migrate:
	uv run python -m src.manage makemigrations server
	uv run python -m src.manage migrate


flush: 
	uv run python -m src.manage flush 

run:
	uv run python -m src

index: 
	time uv run python -m src index

clean: 
	rm -rf ./src/server/migrations ./src/db.sqlite3


install:
	uv sync
	uv run python src.manage makemigrations server
	uv run python src.manage migrate
	
