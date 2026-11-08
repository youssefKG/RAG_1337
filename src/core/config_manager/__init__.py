"""Manage application configuration and indexing strategy decisions."""

import sys
from typing import Literal, TypeAlias
from enum import Enum

from pydantic import BaseModel, ValidationError, Field
from src.core.utils import get_validation_error_message
from src.core.utils import Logger, permission_checker


ConfigKeyType: TypeAlias = Literal[
    "is_indexing_hybrid", "max_chunk_size", "search_type"
]
"""Supported configuration keys."""


class IndexingStrategy(str, Enum):
    """Represent the indexing operations available to the application."""

    NONE = "none"
    """No indexing operation is required."""

    LEXICAL = "lexical"
    """Perform lexical indexing."""

    HYBRID = "hybrid"
    """Perform both lexical and semantic indexing."""

    SEMANTIC = "semantic"
    """Perform semantic indexing."""


class ConfigModel(BaseModel):
    """Define and validate the application's configuration structure.

    Attributes:
        indexing_strategy: Currently configured indexing strategy.
        max_chunk_size: Maximum preferred size of indexed text chunks.
    """

    indexing_strategy: Literal["lexical", "hybrid", "none"] = Field(
        default="lexical"
    )
    max_chunk_size: int = Field(default=2000)

    class ConfigDict:
        """Configure validation behavior for the configuration model."""

        extra: str = "forbid"


CONFIG_FILE_PATH = "src/config.json"
"""Path to the application's configuration file."""


class ConfigManagerError(Exception):
    """Represent errors encountered while loading or updating configuration."""


class ConfigManager:
    """Load, expose, and update application configuration.

    The manager determines which indexing operation is required based on
    the currently stored configuration and the requested indexing options.
    """

    def __init__(self) -> None:
        """Initialize the manager by loading the configuration file.

        Exits the application if the configuration cannot be loaded.
        """
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
        """Return the currently loaded configuration."""
        return self.__config

    @property
    def indexing_strategy(self) -> IndexingStrategy:
        """Return the configured indexing strategy as an enum value."""
        match self.__config.indexing_strategy:
            case "lexical":
                return IndexingStrategy.LEXICAL
            case "hybrid":
                return IndexingStrategy.HYBRID
            case "none":
                return IndexingStrategy.NONE

    def __load_config_file(self) -> ConfigModel:
        """Read and validate the configuration file.

        Checks file permissions before reading its contents and validates
        the JSON data against ConfigModel.

        Returns:
            The validated configuration model.

        Raises:
            ConfigManagerError: If the file cannot be accessed, read,
                or validated.
        """
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
            raise ConfigManagerError(
                get_validation_error_message(error, CONFIG_FILE_PATH)
            ) from error
        except Exception as error:
            raise ConfigManagerError(str(error))

    @property
    def get_current_indexing_strategy(
        self,
    ) -> Literal["hybrid", "lexical", "none"]:
        """Return the indexing strategy currently stored in configuration."""
        return self.__config.indexing_strategy

    def get_indexing_strategy(
        self, max_chunk_size: int, is_hybrid: bool
    ) -> IndexingStrategy:
        """Determine which indexing operation is required.

        Compares the requested chunk size and hybrid indexing setting
        against the currently stored configuration.

        Args:
            max_chunk_size: Requested maximum text chunk size.
            is_hybrid: Whether hybrid indexing is requested.

        Returns:
            The indexing strategy required to apply the requested settings.
        """
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
        """Update the configuration and persist it to the JSON file.

        Args:
            max_chunk_size: New maximum text chunk size.
            is_hybrid: Whether hybrid indexing should be enabled.

        Raises:
            ConfigManagerError: If writing the configuration fails.
        """
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
            raise ConfigManagerError(
                get_validation_error_message(error, CONFIG_FILE_PATH)
            ) from error
        except Exception as error:
            raise ConfigManagerError(str(error))


config_manager: ConfigManager = ConfigManager()
"""Application-wide configuration manager instance."""

__all__ = ["config_manager", "ConfigManager", "IndexingStrategy"]
