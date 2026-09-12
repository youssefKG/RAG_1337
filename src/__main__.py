#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""

import os
from argparse import ArgumentParser, _SubParsersAction
from pydoc import describe

"""

import django

_ = os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

"""


class CLI:

    def __init__(self) -> None:
        self.__arg_parser: ArgumentParser = ArgumentParser(
            prog="CLI", description="RAG PROJECT"
        )
        self.__sub_parsers = self.__arg_parser.add_subparsers(dest="command")

        # index parser
        self.__index_parser: ArgumentParser = self.__sub_parsers.add_parser(
            "index", help="ngest data/raw/ and build the index under data/processed/."
        )
        _ = self.__index_parser.add_argument("index")
        _ = self.__index_parser.add_argument("-max_chunk_size", type=int)

        # search parser
        self.__search_parser: ArgumentParser = self.__sub_parsers.add_parser("search")
        _ = self.__search_parser.add_argument("search")
        _ = self.__search_parser.add_argument(dest="query")
        _ = self.__search_parser.add_argument("-k", type=int)

    def parse(self) -> None:
        res = self.__arg_parser.parse_args(["index"])
        print(res)


if __name__ == "__main__":
    cli = CLI()
    cli.parse()
