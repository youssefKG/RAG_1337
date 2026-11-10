# ----------------------------- PYTHON -----------------------------

PYTHON := uv run python3
PYTHON_MODULE := $(PYTHON) -m src

# ----------------------------- RAG COMMANDS -----------------------------

SEARCH_DATASET := $(PYTHON_MODULE) search_dataset
INDEX := $(PYTHON_MODULE) index
EVALUATE := $(PYTHON_MODULE) evaluate
SEARCH := $(PYTHON_MODULE) search
ANSWER := $(PYTHON_MODULE) answer
ANSWER_DATASET := $(PYTHON) -m src.answer_dataset

# ----------------------------- DATA PATHS -----------------------------

CODE_PUBLIC_DATASET_PATH := data/public/UnansweredQuestions/dataset_code_public.json
CODE_SAVE_DIRECTORY_PUBLIC_PATH := data/public/UnansweredQuestions/dataset_code_docs_public.json

DOCS_PUBLIC_DATASET_PATH := data/public/UnansweredQuestions/dataset_docs_public.json
DOCS_SAVE_DIRECTORY_PUBLIC_PATH := data/output/public_doc.json

DATA_PROCESSED_PATH := data/processed
DATA_OUTPUT_PATH := data/output

# ----------------------------- CONFIGURATION -----------------------------

DEFAULT_CONFIG_PATH := src/default_config.json
CONFIG_PATH := src/config.json

# ----------------------------- LINT -----------------------------

MYPY := uv run mypy
MYPY_FLAGS_NORMAL := --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs
MYPY_FLAGS_STRICT := --strict

FLAKE8 := uv run flake8

# ----------------------------- DEFAULT -----------------------------

.PHONY: run
run:
	$(PYTHON_MODULE)

# ----------------------------- CLEAN -----------------------------

.PHONY: clean
clean:
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	rm -rf *.egg-info
	cp $(DEFAULT_CONFIG_PATH) $(CONFIG_PATH)

# ----------------------------- LINT -----------------------------

.PHONY: lint lint-strict

lint:
	$(MYPY) -m src $(MYPY_FLAGS_NORMAL)
	$(FLAKE8) src

lint-strict:
	$(MYPY) -m src $(MYPY_FLAGS_STRICT)

.PHONY: index

index:
	$(INDEX)

search:
	$(SEARCH) "$(QUERY)"

.PHONY: install

install:
	uv sync
	$(PYTHON) -m src.server.manage makemigrations server
	$(PYTHON) -m src.server.manage migrate server

# ----------------------------- DJANGO SERVER -----------------------------

.PHONY: server

server:
	$(PYTHON) -m src.server.manage runserver

# ----------------------------- DEBUG -----------------------------

.PHONY: pdb

pdb:
	$(PYTHON) -m pdb -m src
