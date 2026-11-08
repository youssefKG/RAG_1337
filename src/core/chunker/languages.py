"""Define supported document languages for text processing."""

from enum import Enum


class Language(str, Enum):
    """Represent the supported languages used during document processing."""

    PYTHON = "python"
    """Python source code."""

    MARKDOWN = "markdown"
    """Markdown-formatted documents."""

    TEXT = "text"
    """Plain-text documents."""
