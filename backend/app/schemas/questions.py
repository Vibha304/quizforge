from pydantic import BaseModel
from typing import Optional, List


class QuestionResponse(BaseModel):
    id: int
    topic_id: int
    topic_name: Optional[str] = None
    type: str
    difficulty: str
    bloom: str = "remember"
    stem: str
    options: Optional[List[str]] = None
    answer: str
    explanation: str = ""
    source_snippet: Optional[str] = None
    status: str = "active"
    time_limit_ms: int = 30000

    model_config = {"from_attributes": True}


class QuestionListResponse(BaseModel):
    items: List[QuestionResponse]
    total: int
    skip: int
    limit: int


class QuestionFilter(BaseModel):
    topic_id: Optional[int] = None
    document_id: Optional[int] = None
    difficulty: Optional[str] = None
    type: Optional[str] = None
    bloom: Optional[str] = None
    status: Optional[str] = None
    skip: int = 0
    limit: int = 50
