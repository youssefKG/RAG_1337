import sys
from typing import Literal, TypeAlias, get_args
from pydantic import BaseModel, Field, ValidationError
from src.core.utils import Logger, permission_checker
from dataclasses import dataclass, asdict


SearchType: TypeAlias = Literal["hybrid", "semantic", "lexical"]
ConfigKeyType: TypeAlias =  Literal["is_indexing_hybrid", "max_chunk_size", "search_type"]
ConfigValueType: TypeAlias = int | SearchType | bool


@dataclass(frozen=False)
class Config:
    is_indexing_hybrid: bool
    max_chunk_size: int
    search_type: SearchType


class ConfigModel(BaseModel):
    is_indexing_hybrid: bool = Field(default=False)
    max_chunk_size: int = Field(default=2000)
    search_type: SearchType = Field(default="lexical")

    class ConfigDict:
        extra: str = "forbid"

CONFIG_FILE_PATH = "src/config.json"


class ConfigManager:
    def __init__(self) -> None:
        self.__config: ConfigModel = self.__load_config_file()


    def __load_config_file(self) -> ConfigModel:
        try:
            permission_checker(
                file_path=CONFIG_FILE_PATH,
                exist=True,
                read=True,
                kill=True,
                fn=lambda x: Logger.error(x, "CONFIG MANAGER")
            )
            with open(CONFIG_FILE_PATH, "r") as config_file:
                config_file_content: str = config_file.read()
                config: ConfigModel = ConfigModel.model_validate_json(config_file_content)
                return config
        except ValidationError as error:
            Logger.error(error.errors()[0]["msg"], "CONFIG MANAGER")
            sys.exit(1)
        except Exception as error:
            Logger.error(str(error), "CONFIG MANAGER")
            sys.exit(1)

    @property
    def config(self) -> ConfigModel:
        return self.__config

    def update(self,
           /,
           *,
           is_indexing_hybrid: bool | None = None,
           max_chunk_size: int | None = None,
           search_type: SearchType | None = None
       ) -> None:
        new_config: Config = Config(
            is_indexing_hybrid=self.__resolve_is_indexing_hybrid(is_indexing_hybrid),
            max_chunk_size=self.__resolve_max_chunk_size(max_chunk_size),
            search_type=self.__resolve_search_type(search_type)
        )
        if asdict(new_config) != self.__config.model_dump():
            try:
                self.__config = ConfigModel(**asdict(new_config))
                permission_checker(
                    file_path=CONFIG_FILE_PATH,
                    exist=True,
                    write=True,
                    kill=True,
                    fn=lambda x: Logger.error(x, "CONFIG")
                )
                with open(CONFIG_FILE_PATH, "w") as file_config:
                    _ = file_config.write(self.__config.model_dump_json(indent=4))
            except ValidationError as error:
                Logger.error(error.errors()[0]["msg"], "UPDATING CONFIG")
                sys.exit(1)
            except Exception as error:
                Logger.error(str(error), "UPDATING CONFIG")

    def __resolve_search_type(self, search_type: SearchType | None) -> SearchType:
        if search_type is not None and search_type != self.__config.search_type:
            if search_type not in get_args(SearchType):
                Logger.error(
                    f"invalid value {search_type} for argument search_type.\n"
                    + f"allowed values: {get_args(SearchType)}",
                    "UPDATE CONFIG"
                )
                sys.exit(1)
            return search_type
        return self.__config.search_type

    def __resolve_is_indexing_hybrid(self, is_indexing_hybrid: bool | None) -> bool:
        if is_indexing_hybrid is not None and is_indexing_hybrid != self.__config.is_indexing_hybrid:
            return is_indexing_hybrid
        return self.__config.is_indexing_hybrid

    def __resolve_max_chunk_size(self, max_chunk_size: int | None) ->  int:
        if max_chunk_size is not None and max_chunk_size != self.__config.max_chunk_size:
            if not (200 <= max_chunk_size <= 2000):
                Logger.error(
                    f"Invalid max_chunk_size: {max_chunk_size}. " 
                    + "Expected a value between 200 and 2000 (inclusive).",
                    "RESOLVE MAX CHUNK SIZE"
                )
                sys.exit(1)
            return max_chunk_size
        return self.__config.max_chunk_size


config_manager: ConfigManager = ConfigManager()

__all__ = ["config_manager"]

