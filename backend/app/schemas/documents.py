from pydantic import BaseModel
from typing import Optional, List, Any
from datetime import datetime


class DocumentCreate(BaseModel):
    filename: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    status: str
    topic_count: int = 0
    question_count: int = 0
    created_at: datetime
    error_message: Optional[str] = None

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    items: List[DocumentResponse]
    total: int
    skip: int
    limit: int


class ProgressEvent(BaseModel):
    stage: str  # parsing | extracting_topics | generating_questions | done | error
    message: str
    progress: float  # 0-100
    detail: Optional[Any] = None
