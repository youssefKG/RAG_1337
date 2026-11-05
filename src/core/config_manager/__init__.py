import sys
from typing import Literal, TypeAlias
from enum import Enum

from pydantic import BaseModel, ValidationError, Field
from src.core.utils import Logger, permission_checker

ConfigKeyType: TypeAlias = Literal[
    "is_indexing_hybrid", "max_chunk_size", "search_type"
]


class IndexingStrategy(str, Enum):
    NONE = "none"
    LEXICAL = "lexical"
    HYBRID = "hybrid"
    SEMANTIC = "semantic"


class ConfigModel(BaseModel):
    indexing_strategy: Literal["lexical", "hybrid", "none"] = Field(
        default="lexical"
    )
    max_chunk_size: int = Field(default=2000)

    class ConfigDict:
        extra: str = "forbid"


CONFIG_FILE_PATH = "src/config.json"


class ConfigManagerError(Exception):
    pass


class ConfigManager:
    def __init__(self) -> None:
        try:
            self.__config: ConfigModel = self.__load_config_file()
        except Exception as error:
            Logger.error(
                "THE CONFIG FILE MUST NOT BE TOUCHED OR CHANGING IT",
                "LAODING CONFIG",
            )
            Logger.error(str(error), "LAODING CONFIG")
            sys.exit(0)

    @property
    def config(self) -> ConfigModel:
        return self.__config

    @property
    def indexing_strategy(self) -> IndexingStrategy:
        match self.__config.indexing_strategy:
            case "lexical":
                return IndexingStrategy.LEXICAL
            case "hybrid":
                return IndexingStrategy.HYBRID
            case "none":
                return IndexingStrategy.NONE


    def __load_config_file(self) -> ConfigModel:
        try:
            _ = permission_checker(
                file_path=CONFIG_FILE_PATH,
                exist=True,
                read=True,
                kill=True,
                fn=lambda message: Logger.error(message, "CONFIG MANAGER"),
            )
            with open(CONFIG_FILE_PATH, "r") as config_file:
                config_file_content: str = config_file.read()
                config: ConfigModel = ConfigModel.model_validate_json(
                    config_file_content
                )
                return config
        except ValidationError as error:
            raise ConfigManagerError(error.errors()[0]["msg"])
        except Exception as error:
            raise ConfigManagerError(str(error))

    @property
    def get_current_indexing_strategy(
        self,
    ) -> Literal["hybrid", "lexical", "none"]:
        return self.__config.indexing_strategy

    def get_indexing_strategy(
        self, max_chunk_size: int, is_hybrid: bool
    ) -> IndexingStrategy:
        indexing_strategy: IndexingStrategy = IndexingStrategy.NONE
        config_max_chunk_size: int = self.__config.max_chunk_size
        is_max_chunk_size_changed: bool = (
            max_chunk_size != config_max_chunk_size
        )
        match self.__config.indexing_strategy:
            case "none":
                if is_hybrid:
                    indexing_strategy = IndexingStrategy.HYBRID
                else:
                    indexing_strategy = IndexingStrategy.LEXICAL
            case "lexical":
                if is_max_chunk_size_changed and not is_hybrid:
                    indexing_strategy = IndexingStrategy.LEXICAL
                elif is_max_chunk_size_changed and is_hybrid:
                    indexing_strategy = IndexingStrategy.HYBRID
                elif not is_max_chunk_size_changed and is_hybrid:
                    indexing_strategy = IndexingStrategy.SEMANTIC
                elif config_max_chunk_size == max_chunk_size and not is_hybrid:
                    indexing_strategy = IndexingStrategy.NONE
            case "hybrid":
                if is_max_chunk_size_changed and not is_hybrid:
                    indexing_strategy = IndexingStrategy.LEXICAL
                elif is_max_chunk_size_changed and is_hybrid:
                    indexing_strategy = IndexingStrategy.HYBRID
                elif not is_max_chunk_size_changed and is_hybrid:
                    indexing_strategy = IndexingStrategy.NONE
        return indexing_strategy

    def update_indexing_config(
        self, *, max_chunk_size: int, is_hybrid: bool
    ) -> None:
        _ = permission_checker(
            file_path=CONFIG_FILE_PATH,
            exist=True,
            read=True,
            kill=True,
            fn=lambda x: Logger.error(x, "CONFIG MANAGER"),
        )
        self.__config = ConfigModel(
            max_chunk_size=max_chunk_size,
            indexing_strategy="hybrid" if is_hybrid else "lexical",
        )
        try:
            with open(CONFIG_FILE_PATH, "w") as config_file:
                _ = config_file.write(self.__config.model_dump_json(indent=4))
        except ValidationError as error:
            raise ConfigManagerError(str(error.errors()[0]["msg"]))
        except Exception as error:
            raise ConfigManagerError(str(error))


config_manager: ConfigManager = ConfigManager()

__all__ = ["config_manager", "ConfigManager", "IndexingStrategy"]
