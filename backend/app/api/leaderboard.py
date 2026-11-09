from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.users import User
from app.models.gamification import UserStats, UserBadge
from app.schemas.gamification import LeaderboardEntry
from app.core.deps import get_current_user

router = APIRouter()


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats_list = (
        db.query(UserStats)
        .join(User, User.id == UserStats.user_id)
        .filter(User.is_active == True)
        .order_by(UserStats.xp.desc())
        .limit(limit)
        .all()
    )

    results = []
    for rank, s in enumerate(stats_list, start=1):
        user = s.user
        badge_count = db.query(func.count(UserBadge.id)).filter(UserBadge.user_id == s.user_id).scalar() or 0
        results.append(
            LeaderboardEntry(
                rank=rank,
                user_id=s.user_id,
                name=user.name if user else f"User {s.user_id}",
                xp=s.xp,
                level=s.level,
                streak=s.streak,
                badge_count=badge_count,
            )
        )

    return results
