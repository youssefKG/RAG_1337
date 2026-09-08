from pydantic import BaseModel
from .unanswered_quetion import UnansweredQuestion
from .answered_question import AnsweredQuestion


class RagDataset(BaseModel):
    rag_questions: list[AnsweredQuestion | UnansweredQuestion]
