from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from app.schemas.questions import QuestionResponse
from app.schemas.gamification import BadgeResponse


class QuizStartRequest(BaseModel):
    document_id: int
    topic_ids: Optional[List[int]] = None
    mode: str = "adaptive"  # adaptive | sequential | random | weak_focus
    max_questions: int = 20


class QuizSessionResponse(BaseModel):
    id: int
    mode: str
    status: str
    score: float = 0.0
    xp_earned: int = 0
    current_question: Optional[QuestionResponse] = None
    why_text: Optional[str] = None
    attempt_count: int = 0
    correct_count: int = 0
    started_at: datetime
    completed_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class AnswerRequest(BaseModel):
    question_id: int
    answer: str
    response_ms: int = 0


class AnswerResponse(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    xp_gained: int
    new_xp_total: int
    new_level: int
    mastery_delta: float
    new_mastery: float
    badges_unlocked: List[BadgeResponse] = []
    streak: int
    combo: int
    next_question: Optional[QuestionResponse] = None
    why_text: Optional[str] = None
    session_complete: bool = False
