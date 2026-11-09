from pydantic import BaseModel
from typing import Optional, List


class TopicResponse(BaseModel):
    id: int
    document_id: int
    parent_id: Optional[int] = None
    name: str
    keywords: List[str] = []
    summary: Optional[str] = None
    difficulty_prior: float = 0.5
    question_count: int = 0

    model_config = {"from_attributes": True}


class TopicUpdate(BaseModel):
    name: Optional[str] = None
    keywords: Optional[List[str]] = None
    difficulty_prior: Optional[float] = None
    summary: Optional[str] = None


class TopicTree(BaseModel):
    id: int
    name: str
    keywords: List[str] = []
    difficulty_prior: float = 0.5
    question_count: int = 0
    children: List["TopicTree"] = []

    model_config = {"from_attributes": True}


TopicTree.model_rebuild()
