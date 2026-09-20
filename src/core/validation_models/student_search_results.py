from pydantic import BaseModel
from .minimal_search_result import MinimalSearchResults
from typing import List


class StudentSearchResults(BaseModel):
    search_results: List[MinimalSearchResults]
    k: int
