import json
from typing import List, Dict
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models.users import User
from app.models.mastery import Mastery
from app.models.topics import Topic
from app.models.questions import Question
from app.models.quiz import Attempt
from app.models.gamification import UserStats
from app.schemas.analytics import (
    MasteryResponse,
    MasteryHistoryEntry,
    ProgressResponse,
    XPHistoryEntry,
    CoverageResponse,
    CoverageByTopic,
    CoverageByDifficulty,
)
from app.core.deps import get_current_user
from app.services.gamification.engine import ensure_user_stats, xp_to_next_level

router = APIRouter()


@router.get("/mastery", response_model=List[MasteryResponse])
def get_user_mastery(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    masteries = (
        db.query(Mastery)
        .filter(Mastery.user_id == current_user.id)
        .all()
    )

    results = []
    for m in masteries:
        topic_name = m.topic.name if m.topic else f"Topic {m.topic_id}"
        hist_raw = json.loads(m.history_json) if m.history_json else []
        history_entries = []
        for h in hist_raw:
            try:
                ts_val = datetime.fromisoformat(h["ts"]) if isinstance(h["ts"], str) else datetime.utcnow()
            except Exception:
                ts_val = datetime.utcnow()
            history_entries.append(
                MasteryHistoryEntry(
                    ts=ts_val,
                    p_L=h.get("p_L", m.p_L),
                    correct=h.get("correct", True),
                )
            )

        results.append(
            MasteryResponse(
                topic_id=m.topic_id,
                topic_name=topic_name,
                p_L=m.p_L,
                attempts_count=m.attempts_count,
                is_weak=m.is_weak,
                is_mastered=m.is_mastered,
                history=history_entries,
            )
        )
    return results


@router.get("/progress", response_model=ProgressResponse)
def get_user_progress(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    stats = ensure_user_stats(db, current_user.id)
    needed = xp_to_next_level(stats.xp, stats.level)
    accuracy = (
        round(stats.total_correct / stats.total_attempts, 3)
        if stats.total_attempts > 0
        else 0.0
    )

    # 7-day XP history
    today = date.today()
    xp_history = []
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        # Sum attempts for this day
        day_xp = (
            db.query(func.coalesce(func.sum(Attempt.xp_gained), 0))
            .filter(
                Attempt.user_id == current_user.id,
                func.date(Attempt.ts) == day.isoformat(),
            )
            .scalar()
        )
        xp_history.append(XPHistoryEntry(date=day, xp=int(day_xp or 0)))

    return ProgressResponse(
        xp=stats.xp,
        level=stats.level,
        xp_to_next_level=needed,
        streak=stats.streak,
        total_attempts=stats.total_attempts,
        correct_attempts=stats.total_correct,
        accuracy=accuracy,
        xp_history=xp_history,
    )


@router.get("/coverage", response_model=CoverageResponse)
def get_syllabus_coverage(
    document_id: int = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic_query = db.query(Topic)
    if document_id:
        topic_query = topic_query.filter(Topic.document_id == document_id)

    topics = topic_query.all()
    total_topics = len(topics)
    covered_topics = 0
    total_questions = 0
    by_topic = []

    for t in topics:
        q_count = len(t.questions) if t.questions else 0
        if q_count > 0:
            covered_topics += 1
        total_questions += q_count

        diff_counts = {"easy": 0, "medium": 0, "hard": 0}
        bloom_counts = {}
        for q in (t.questions or []):
            diff = q.difficulty.lower() if q.difficulty else "medium"
            if diff in diff_counts:
                diff_counts[diff] += 1
            b = q.bloom.lower() if q.bloom else "remember"
            bloom_counts[b] = bloom_counts.get(b, 0) + 1

        by_topic.append(
            CoverageByTopic(
                topic_id=t.id,
                topic_name=t.name,
                question_count=q_count,
                by_difficulty=CoverageByDifficulty(**diff_counts),
                by_bloom=bloom_counts,
            )
        )

    return CoverageResponse(
        total_topics=total_topics,
        covered_topics=covered_topics,
        total_questions=total_questions,
        by_topic=by_topic,
    )
