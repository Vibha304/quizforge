from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class BadgeResponse(BaseModel):
    code: str
    name: str
    description: str
    icon: str
    earned_at: Optional[datetime] = None

    model_config = {"from_attributes": True}


class UserStatsResponse(BaseModel):
    xp: int
    level: int
    streak: int
    last_active: Optional[datetime] = None
    badges: List[BadgeResponse] = []

    model_config = {"from_attributes": True}


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    name: str
    xp: int
    level: int
    streak: int
    badge_count: int
