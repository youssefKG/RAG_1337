import sys
from src.core.utils import Logger, Stage

CORPUS_PATH = "data/raw/vllm-0.10.1"
CODE_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_code_public.json"
DOC_BASE_QUESTIONS = "data/public/UnansweredQuestions/dataset_docs_public.json"
DATASET_PATH = "data/datasets/UnansweredQuestions"
STUDENT_SEARCH_RESULTS_PATH = (
    "data/datasets/UnansweredQuestions/dataset_docs_public.json"
)
SAVE_DIRECTORY = "data/output/search_results/UnansweredQuestions"

DATA_PROCESSED_PATH = "data/processed/"
MAX_CHUNK_SIZE = 2000

class RageAgainstMachine:
    def index(self, max_chunk_size: int = MAX_CHUNK_SIZE, hybrid: str = "false") -> None:
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                 Stage.INDEXING.name
            )
            sys.exit(1)
        is_indexing_hybrid: bool = True if hybrid == "true" else False
        from src.core.indexer import indexer
        indexer(
            corpus_path=CORPUS_PATH,
            max_chunk_size=max_chunk_size,
            is_hybrid=is_indexing_hybrid
        )

    def search_dataset(
        self,
        dataset_path: str = DATASET_PATH,
        save_directory: str = "",
        k: int = 5,
        hybrid: str="false"
    ) -> None:
        if k <= 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(0)
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                 Stage.INDEXING.name
            )
            sys.exit(1)
        from src.core.question_manager import question_manager
        is_hybrid: bool = True if hybrid == "true" else False
        question_manager.search_datasets(
            dataset_path=dataset_path,
            top_k=k,
            save_directory=save_directory,
            is_hybrid=is_hybrid
        )

    def search(self, query: str, k: int, hybrid: str="false") -> None:
        if k <= 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(0)
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                 Stage.INDEXING.name
            )
            sys.exit(1)
        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)

        is_hybrid: bool = True if hybrid == "true" else False
        from src.core.question_manager import question_manager
        minimal_search_results = question_manager.search(query, k, is_hybrid)
        for document in minimal_search_results.retrieved_sources:
            print(document.file_path, f"[{document.first_character_index}:{document.last_character_index}]")

    def answer(self, query: str, k: int, hybrid: str="false") -> None:
        print(globals())
        if k <= 0:
            Logger.error(
                f"Number of requested results {k} cannot be 0 or negative.",
                Stage.SEARCH_DATASET.name
            )
            sys.exit(0)
        if hybrid != "true" and hybrid != "false":
            Logger.error(
                f"invalid value for hybrid {hybrid}. allowed values: true, false",
                 Stage.INDEXING.name
            )
            sys.exit(1)
        if not query.strip():
            Logger.error("The query should not empty", "SEARCH")
            sys.exit(1)
        is_hybrid: bool = True if hybrid == "true" else False
        from src.core.answer_manager import answer_manager
        answer: str = answer_manager.answer(query, k, is_hybrid)
        Logger.info(answer, "ANSWER")
