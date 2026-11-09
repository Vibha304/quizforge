from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from datetime import datetime, date


class MasteryHistoryEntry(BaseModel):
    ts: datetime
    p_L: float
    correct: bool


class MasteryResponse(BaseModel):
    topic_id: int
    topic_name: str
    p_L: float
    attempts_count: int
    is_weak: bool
    is_mastered: bool
    history: List[MasteryHistoryEntry] = []

    model_config = {"from_attributes": True}


class XPHistoryEntry(BaseModel):
    date: date
    xp: int


class ProgressResponse(BaseModel):
    xp: int
    level: int
    xp_to_next_level: int
    streak: int
    total_attempts: int
    correct_attempts: int
    accuracy: float
    xp_history: List[XPHistoryEntry] = []


class CoverageByDifficulty(BaseModel):
    easy: int = 0
    medium: int = 0
    hard: int = 0


class CoverageByTopic(BaseModel):
    topic_id: int
    topic_name: str
    question_count: int
    by_difficulty: CoverageByDifficulty
    by_bloom: Dict[str, int] = {}


class CoverageResponse(BaseModel):
    total_topics: int
    covered_topics: int
    total_questions: int
    by_topic: List[CoverageByTopic] = []
