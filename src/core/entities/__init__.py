from dataclasses import dataclass, field
import uuid


@dataclass(frozen=False)
class File:
    """Represent a source file in the indexed corpus.

    Attributes:
        path: Path to the source file.
        last_modified_at: Last modification timestamp of the file.
        id: Unique identifier generated automatically.
    """

    path: str
    last_modified_at: float
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=False)
class Document:
    """Represent a text chunk extracted from a source file.

    Attributes:
        start_index: Starting character position of the chunk in the file.
        end_index: Ending character position of the chunk in the file.
        length: Number of characters in the chunk.
        file: Source file from which the chunk was extracted.
        content: Text content of the chunk.
        id: Unique identifier generated automatically.
    """

    start_index: int
    end_index: int
    length: int
    file: File
    content: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=False)
class Term:
    """Represent a term extracted from a document.

    Attributes:
        document: Document containing the term.
        value: Text value of the term.
        frequency: Number of occurrences of the term in the document.
        id: Unique identifier generated automatically.
    """

    document: Document
    value: str
    frequency: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=False)
class Question:
    """Represent a search query submitted to the retrieval system.

    Attributes:
        question: Text of the user's query.
        top_k: Maximum number of documents to retrieve.
        search_type: Retrieval strategy used to search for relevant documents.
        id: Unique identifier generated automatically.
    """

    question: str
    top_k: int
    search_type: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class QuestionDocument:
    """Represent the association between a question and a retrieved document.

    Attributes:
        question: Question associated with the retrieved document.
        document: Document retrieved for the question.
        id: Unique identifier generated automatically.
    """

    question: Question
    document: Document
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass(frozen=False)
class QuestionAnswer:
    """Represent an answer generated for a question.

    Attributes:
        question: Question for which the answer was generated.
        answer: Generated answer text.
        id: Unique identifier generated automatically.
    """

    question: Question
    answer: str
    max_tokens: int
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


__all__ = ["File", "Document", "Term", "QuestionDocument"]
