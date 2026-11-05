from datetime import datetime
from enum import Enum, auto
from typing import Callable
from pathlib import Path
from .constants import TOKENIZER_REGEX_PATTERN, STOP_WORDS
import os
import sys


class Stage(Enum):
    INDEXING = auto()
    RETRIEVAL = auto()
    SEARCH = auto()
    SEARCH_DATASET = auto()
    ANSWER = auto()
    ANSWER_DATASET = auto()


class COLORS(str, Enum):
    """ANSI color codes"""

    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m"
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m"
    LIGHT_CYAN = "\033[1;36m"
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"


time_formatter: Callable[[], str] = (
    lambda: "{color}[{date}]{reset_color}".format(
        color=COLORS.LIGHT_GRAY.value,
        date=str(datetime.now()),
        reset_color=COLORS.END.value,
    )
)

stage_formatter: Callable[[str], str] = (
    lambda stage: "{color}[{stage}]{reset_color}".format(
        color=COLORS.CYAN.value, stage=stage, reset_color=COLORS.END.value
    )
)

message_formatter: Callable[[str], str] = (
    lambda message: "{color}{message}".format(
        color=COLORS.BOLD.value, message=message
    )
)


class Logger:
    info_formater: str = "{bold}{color}[INFO]{reset_color}".format(
        color=COLORS.LIGHT_BLUE.value,
        bold=COLORS.BOLD.value,
        reset_color=COLORS.END.value,
    )
    warning_formater: str = "{color}[WARNNING]{reset_color}".format(
        color=COLORS.YELLOW.value, reset_color=COLORS.END.value
    )
    error_formater: str = "{color}[ERROR]{reset_color}".format(
        color=COLORS.LIGHT_RED.value, reset_color=COLORS.END.value
    )

    query_formatter: str = "{color}[ERROR]{reset_color}".format(
        color=COLORS.LIGHT_RED.value, reset_color=COLORS.END.value
    )

    @classmethod
    def info(cls, message: str, stage: str) -> None:
        info_format = (
            f"{time_formatter()}"
            f" {cls.info_formater}"
            f" {stage_formatter(stage)}"
            f": {message_formatter(message)}"
        )
        print(info_format)

    @classmethod
    def query(cls, query: str, stage: str) -> None:
        info_format = (
            f"{time_formatter()}"
            f"{cls.query_formatter}"
            f" {stage_formatter(stage)}"
            f": {message_formatter(query)}"
        )
        print(info_format)
        pass

    @classmethod
    def warn(cls, message: str, stage: str) -> None:
        warn_format = (
            f"{time_formatter()}"
            f" {cls.warning_formater}"
            f" {stage_formatter(stage)}"
            f": {message_formatter(message)}"
        )
        print(warn_format)

    @classmethod
    def error(cls, message: str, stage: str) -> None:
        error_format = (
            f"{time_formatter()}"
            f" {cls.error_formater}"
            f" {stage_formatter(stage)}"
            f": {message_formatter(message)}"
        )
        print(error_format)


def permission_checker(
    *,
    file_path: str,
    write: bool = False,
    read: bool = False,
    exist: bool = False,
    kill: bool = True,
    fn: Callable[[str], None] | None = None,
) -> bool:
    if exist and not os.access(file_path, os.F_OK):
        if fn is not None:
            fn(f"permission error: not exist {file_path}")
        if kill:
            sys.exit(126)
        return False
    if write and not os.access(file_path, os.W_OK):
        if fn is not None:
            fn(f"permission error: cannot write {file_path}")
        if kill:
            sys.exit(126)
        return False
    if read and not os.access(file_path, os.R_OK):
        if fn is not None:
            fn(f"permission error: cannot read {file_path}")
        if kill:
            sys.exit(126)
        return False
    return True


def create_file_path(file_path: str) -> None:
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)


__all__ = [
    "TOKENIZER_REGEX_PATTERN",
    "STOP_WORDS",
    "Logger",
    "Stage",
    "permission_checker",
    "INIT_DB",
]
