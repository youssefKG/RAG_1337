import sys
from typing import Literal, TypeAlias, cast
from pydantic import BaseModel, Field, ValidationError
from src.core.utils import Logger, permission_checker


SearchType: TypeAlias = Literal["hybrid", "semantic", "lexical"]
ConfigKeyType: TypeAlias =  Literal["is_indexing_hybrid", "max_chunk_size", "search_type"]
ConfigValueType: TypeAlias = int | SearchType | bool

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
                fn=lambda x: Logger.error(x, "CONFIG MANGER")
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
    def config(self) -> None:
        return self.config


    def update(self,
               /,
               *,
               is_indexing_hybrid: bool | None = None,
               max_chunk_size: int | None = None,
               search_type:Literal["hybrid", "semantic", "lexical"] | None = None
       ) -> None:
        is_changed: bool = False
        new_config: dict[ConfigKeyType, ConfigValueType] = cast(dict[ConfigKeyType, ConfigValueType], self.__config.model_dump())
        if is_indexing_hybrid is not None and is_indexing_hybrid != self.__config.is_indexing_hybrid:
            if not is_changed:
                is_changed = True
        if max_chunk_size is not None and max_chunk_size != self.__config.max_chunk_size:
            if not is_changed:
                is_changed = True
            self.__config.max_chunk_size = max_chunk_size
        if search_type is not None:
            pass

        if is_changed:
            try:
                self.__config = ConfigModel(**self.__config.model_dump())
                permission_checker(
                    file_path=CONFIG_FILE_PATH,
                    exist=True,
                    write=True,
                    kill=True,
                    fn=lambda x: Logger.error(x, "CONFIG")
                )
                with open(CONFIG_FILE_PATH, "w") as file_config:
                    pass
            except ValidationError as error:
                Logger.error(error.errors()[0]["msg"], "UPDATING CONFIG")

    def check_is_change(self) -> None:
        pass
    #
    # def __get_search_type(self, search: str) -> SearchType:
    #     match search.upper():
    #         case SearchType.LEXICAL.name:
    #             pass
    #         case SearchType.SEMANTIC.name:
    #             return SearchType.SEMANTIC
    #         case SearchType.HYBRID.name:
    #             return SearchType.HYBRID
    #         case _:
    #             Logger.error("Unknow search type. allowed search types: lexical, semantic, hybrid", "")
    #             sys.exit(1)
    #     return SearchType.LEXICAL



config_manager: ConfigManager = ConfigManager()

__all__ = ["config_manager"]

