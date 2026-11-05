# ============================ CONFIGURATION ============================

UV = uv
PYTHON = $(UV) run python
MYPY = $(UV) run mypy
FLAKE8 = $(UV) run flake8

DEFAULT_CONFIG_PATH = ./src/default_config.json
CONFIG_PATH = ./src/config.json

# ============================== RAG DATA ==============================

PUBLIC_DATASET_DIR = data/public/UnansweredQuestions
OUTPUT_DIR = data/output

CODE_PUBLIC_DATASET = $(PUBLIC_DATASET_DIR)/dataset_code_public.json
DOCS_PUBLIC_DATASET = $(PUBLIC_DATASET_DIR)/dataset_docs_public.json

CODE_PUBLIC_OUTPUT = $(PUBLIC_DATASET_DIR)/dataset_docs_public.json
DOCS_PUBLIC_OUTPUT = $(OUTPUT_DIR)/public_doc.json

# ============================== RAG CLI ===============================

CLI = $(PYTHON) -m src

SEARCH_DATASET = $(CLI) search_dataset
INDEX = $(CLI) index
EVALUATE = $(CLI) evaluate
SEARCH = $(CLI) search --query
ANSWER = $(CLI) answer --query
ANSWER_DATASET = $(CLI) answer_dataset

# ============================== LINTING ===============================

MYPY_FLAGS_NORMAL = 
	--warn-return-any 
	--warn-unused-ignores 
	--ignore-missing-imports 
	--disallow-untyped-defs 
	--check-untyped-defs

MYPY_FLAGS_STRICT = --strict

# ============================== DEFAULT ===============================

.PHONY: run
run:
	$(CLI)

# ============================== SERVER ================================

.PHONY: server
server:
	$(PYTHON) -m src.server.manage runserver

# ============================== INSTALL ===============================

.PHONY: install
install:
	$(UV) sync
	$(PYTHON) -m src.server.manage makemigrations server
	$(PYTHON) -m src.server.manage migrate

# ============================== INDEXING ==============================

.PHONY: index
index:
	$(INDEX)

# ============================== DATASETS ==============================

.PHONY: public-code public-docs

public-code:
	$(SEARCH_DATASET) 
		--dataset_path $(CODE_PUBLIC_DATASET) 
		--save_directory $(CODE_PUBLIC_OUTPUT) 
		--k 10

public-docs:
	$(SEARCH_DATASET) 
		--dataset_path $(DOCS_PUBLIC_DATASET) 
		--save_directory $(DOCS_PUBLIC_OUTPUT) 
		--k 10

# ============================== EVALUATION ============================

.PHONY: evaluate
evaluate:
	$(EVALUATE)

# ============================== SEARCH & ANSWERS ======================

.PHONY: search answer answer-dataset

search:
	$(SEARCH) "$(QUERY)"

answer:
	$(ANSWER) "$(QUERY)"

answer-dataset:
	$(ANSWER_DATASET)

# ============================== LINTING ===============================

.PHONY: lint lint-strict

lint:
	$(MYPY) -m src $(MYPY_FLAGS_NORMAL)
	$(FLAKE8) src

lint-strict:
	$(MYPY) -m src $(MYPY_FLAGS_STRICT)

# ============================== CLEANUP ===============================

.PHONY: clean clean-cache reset-config

clean:
	rm -rf data/processed/
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +

clean-cache:
	rm -rf .mypy_cache .pytest_cache
	find . -type d -name '__pycache__' -exec rm -rf {} +

reset-config:
	cp $(DEFAULT_CONFIG_PATH) $(CONFIG_PATH)
