"""
Gamification engine: XP calculation, level progression, badge awarding.

Badge catalogue (12+ badges):
- first_question: Answer your first question
- first_correct: Get your first correct answer
- streak_3: 3-day streak
- streak_7: 7-day streak
- streak_30: 30-day streak
- perfect_quiz: 100% score in a quiz session
- speed_demon: Answer 5 questions in under 40% of time limit
- knowledge_seeker: Complete 10 quiz sessions
- topic_master: Achieve mastery ≥0.9 on a topic
- all_rounder: Study 5+ different topics
- comeback_kid: Get 3 correct after 3 wrong
- night_owl: Complete a quiz after midnight
- early_bird: Complete a quiz before 7am
- centurion: Answer 100 questions total
- unstoppable: 20-question quiz with 0 wrong
"""
import logging
from typing import List
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.gamification import UserStats, Badge, UserBadge
from app.models.mastery import Mastery
from app.models.users import User

logger = logging.getLogger(__name__)

# Badge definitions
BADGE_DEFINITIONS = [
    ("first_question", "First Step", "Answer your first question", "🎯"),
    ("first_correct", "Sharp Mind", "Get your first correct answer", "✅"),
    ("streak_3", "On Fire", "Achieve a 3-day study streak", "🔥"),
    ("streak_7", "Week Warrior", "Achieve a 7-day study streak", "⚡"),
    ("streak_30", "Unstoppable", "Achieve a 30-day study streak", "🌟"),
    ("perfect_quiz", "Perfect Score", "Get 100% in a quiz session", "🏆"),
    ("speed_demon", "Speed Demon", "Answer 5 questions in under 40% of time limit", "⚡"),
    ("knowledge_seeker", "Knowledge Seeker", "Complete 10 quiz sessions", "📚"),
    ("topic_master", "Topic Master", "Achieve mastery ≥0.9 on any topic", "🎓"),
    ("all_rounder", "All-Rounder", "Study 5 or more different topics", "🌐"),
    ("comeback_kid", "Comeback Kid", "Get 3 correct answers after 3 wrong answers", "💪"),
    ("night_owl", "Night Owl", "Complete a quiz session after midnight", "🦉"),
    ("early_bird", "Early Bird", "Complete a quiz session before 7am", "🌅"),
    ("centurion", "Centurion", "Answer 100 questions total", "💯"),
    ("unstoppable_quiz", "Flawless Victory", "Complete a 20-question quiz with no wrong answers", "🎖️"),
    ("level_5", "Rising Star", "Reach level 5", "⭐"),
    ("level_10", "Expert", "Reach level 10", "🔷"),
]


def calculate_xp(difficulty: str, streak: int, response_ms: int, time_limit_ms: int) -> int:
    """
    Calculate XP earned for a correct answer.

    Args:
        difficulty: "easy", "medium", or "hard".
        streak: Current streak count.
        response_ms: Time taken to answer in milliseconds.
        time_limit_ms: Time limit for the question in milliseconds.

    Returns:
        XP earned (integer).
    """
    base = {"easy": 10, "medium": 20, "hard": 35}.get(difficulty, 20)
    streak_mult = 1 + min(streak, 10) * 0.1
    time_ratio = response_ms / time_limit_ms if time_limit_ms > 0 else 1.0
    speed_bonus = 1.25 if time_ratio < 0.4 else 1.0
    return int(base * streak_mult * speed_bonus)


def get_level_from_xp(xp: int) -> int:
    """
    Calculate level from total XP.
    Level n requires cumulative 100 × (n-1)^1.5 XP, or level 1 at 0 XP, level 2 at 100 XP.
    Level n requires sum_{i=1}^{n-1} 100 * i^1.5 XP.

    Args:
        xp: Total XP earned.

    Returns:
        Current level (minimum 1).
    """
    level = 1
    accumulated = 0
    while True:
        needed_for_next = int(100 * (level ** 1.5))
        if xp < accumulated + needed_for_next:
            return level
        accumulated += needed_for_next
        level += 1


def xp_for_next_level(current_level: int) -> int:
    """Return XP needed to reach the next level."""
    return int(100 * (current_level ** 1.5))


def xp_to_next_level(total_xp: int, current_level: int) -> int:
    """Return remaining XP needed to reach the next level."""
    xp_spent = sum(int(100 * (l ** 1.5)) for l in range(1, current_level))
    remaining = total_xp - xp_spent
    needed = int(100 * (current_level ** 1.5))
    return max(0, needed - remaining)


def ensure_user_stats(db: Session, user_id: int) -> UserStats:
    """Get or create UserStats for a user."""
    stats = db.query(UserStats).filter(UserStats.user_id == user_id).first()
    if stats is None:
        stats = UserStats(user_id=user_id)
        db.add(stats)
        db.flush()
    return stats


def award_xp(db: Session, user_id: int, xp: int) -> UserStats:
    """Add XP to a user and update their level."""
    stats = ensure_user_stats(db, user_id)
    stats.xp += xp
    stats.level = get_level_from_xp(stats.xp)
    stats.updated_at = datetime.utcnow()
    db.flush()
    return stats


def check_and_award_badges(
    db: Session,
    user_id: int,
    context: dict,
) -> List[Badge]:
    """
    Check badge eligibility and award new badges.

    Args:
        db: Database session.
        user_id: User ID to check badges for.
        context: Dict with keys:
            - total_attempts: total questions answered
            - total_correct: total correct answers
            - streak: current streak
            - session_score: fraction correct in current session
            - session_questions: total questions in session
            - session_correct: correct in session
            - mastery_p_L: new mastery level after update
            - topic_ids_studied: list of topic IDs studied
            - response_ms: response time
            - time_limit_ms: question time limit
            - hour: hour of day (0-23)
            - consecutive_correct_after_wrong: consecutive correct answers after wrong streak

    Returns:
        List of newly awarded Badge objects.
    """
    # Ensure all badges exist in DB
    _ensure_badges(db)

    earned_codes = {
        ub.badge.code
        for ub in db.query(UserBadge)
        .filter(UserBadge.user_id == user_id)
        .all()
    }

    stats = ensure_user_stats(db, user_id)
    new_badges = []

    def try_award(code: str) -> bool:
        if code not in earned_codes:
            badge = db.query(Badge).filter(Badge.code == code).first()
            if badge:
                ub = UserBadge(user_id=user_id, badge_id=badge.id)
                db.add(ub)
                db.flush()
                new_badges.append(badge)
                earned_codes.add(code)
                return True
        return False

    total_attempts = context.get("total_attempts", 0)
    total_correct = context.get("total_correct", 0)
    streak = context.get("streak", 0)
    session_score = context.get("session_score", 0.0)
    session_questions = context.get("session_questions", 0)
    mastery_p_L = context.get("mastery_p_L", 0.0)
    topic_ids_studied = context.get("topic_ids_studied", [])
    response_ms = context.get("response_ms", 99999)
    time_limit_ms = context.get("time_limit_ms", 30000)
    hour = context.get("hour", 12)
    consec_correct = context.get("consecutive_correct_after_wrong", 0)
    session_correct = context.get("session_correct", 0)
    speed_answers = context.get("speed_answers_count", 0)
    quiz_sessions_count = context.get("quiz_sessions_count", 0)

    # Award badges
    if total_attempts >= 1:
        try_award("first_question")
    if total_correct >= 1:
        try_award("first_correct")
    if streak >= 3:
        try_award("streak_3")
    if streak >= 7:
        try_award("streak_7")
    if streak >= 30:
        try_award("streak_30")
    if session_questions >= 5 and session_score >= 1.0:
        try_award("perfect_quiz")
    if speed_answers >= 5:
        try_award("speed_demon")
    if quiz_sessions_count >= 10:
        try_award("knowledge_seeker")
    if mastery_p_L >= 0.9:
        try_award("topic_master")
    if len(set(topic_ids_studied)) >= 5:
        try_award("all_rounder")
    if consec_correct >= 3:
        try_award("comeback_kid")
    if hour >= 0 and hour < 4:
        try_award("night_owl")
    if hour >= 5 and hour < 7:
        try_award("early_bird")
    if total_attempts >= 100:
        try_award("centurion")
    if session_questions >= 20 and session_correct == session_questions:
        try_award("unstoppable_quiz")
    if stats.level >= 5:
        try_award("level_5")
    if stats.level >= 10:
        try_award("level_10")

    return new_badges


def _ensure_badges(db: Session) -> None:
    """Create badge records if they don't exist."""
    existing = {b.code for b in db.query(Badge).all()}
    for code, name, description, icon in BADGE_DEFINITIONS:
        if code not in existing:
            badge = Badge(code=code, name=name, description=description, icon=icon)
            db.add(badge)
    db.flush()
