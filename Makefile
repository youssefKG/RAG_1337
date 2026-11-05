PYTHON_VENV = uv run python3

# ----------------------------- RAG VARS ----------------------------
SEARCH_DATASET = $(PYTHON_VENV) -m src search_dataset
CODE_PUBLIC_DATASET_PATH = "data/public/UnansweredQuestions/dataset_code_public.json"
CODE_SAVE_DIRECTORY_PUBLIC_PATH = data/public/UnansweredQuestions/dataset_docs_public.json
DOCS_PUBLIC_DATASET_PATH = data/public/UansweredQuestions/dataset_docs_public.json
DOCS_SAVE_DIRECTORY_PUBLIC_PATH = data/output/public_doc.json
DATA_PROCESSED_PATH = data/processed
DATA_OUTPUT_PATH = data/output
INDEX = $(PYTHON_VENV) -m src index
EVALUATE = $(PYTHON_VENV) -m src evaluate
SEARCH = $(PYTHON) -m src search --query
ANSWER = $(PYTHON_VENV) -m src answer --query
ANSWER_DATASET = $(PYTHON) -m answer_dataset
DEFAULT_CONFIG_PATH = ./src/default_config.json
CONFIG_PATH = ./src/config.json


# ---------------------- LINT VARS -----------------------------
MYPY_VENV = uv run mypy 
MYPY_FLAGS_NORMAL = --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
MYPY_FLAGS_STRICT = --strict
FLAKE8_VENV = uv run flake8

run:
	uv run python -m src

clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf .venv *.egg-info
	rm -rf $(DATA_PROCESSED_PATH) $(DATA_OUTPUT_PATH)
	@cat $(DEFAULT_CONFIG_PATH) > $(CONFIG_PATH)

# ---------------------- DJANGO SERVER -----------------------
server: 
	$(UV_VENV) -m src.server.manage runserver

# ---------------- LINT RULES ------------------------------------
lint:
	$(MYPY_VENV) -m src $(FLAGS) $(MYPY_FLAGS_NORMAL)
	$(FLAKE8_VENV) src

lint-strict:
	 $(MYPY_VENV) -m src $(MYPY_FLAGS_STRICT)

# ------------------ RAG CLI RULES
public_code:
	$(SEARCH_DATASET) --dataset_path  $(CODE_PUBLIC_DATASET_PATH) --save_directory $(CODE_SAVE_DIRECTORY_PUBLIC_PATH) --k 10
public_docs:
	$(SEARCH_DATASET) --dataset_path  $(DOCS_PUBLIC_DATASET_PATH) --save_directory $(DOCS_SAVE_DIRECTORY_PUBLIC_PATH) --k 10

index: 
	$(PYTHON_VENV) -m src index

install:
	uv sync
	$(PYTHON_VENV) -m src.server.manage makemigrations server
	$(PYTHON_VENV) -m src.server.manage migrate

.PHONNY: public
