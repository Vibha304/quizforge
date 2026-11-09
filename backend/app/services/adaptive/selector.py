"""
Adaptive question selector.

Uses BKT mastery weights to prioritize weak topics.
Implements difficulty staircase and no-repeat logic.
"""
import json
import random
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.questions import Question
from app.models.mastery import Mastery
from app.models.topics import Topic

logger = logging.getLogger(__name__)

NO_REPEAT_WINDOW = 10  # Don't repeat within last N questions
EXPLORATION_RATE = 0.20  # 20% chance to explore non-weak topics


def calculate_weight(
    mastery: float,
    last_attempted_at: Optional[datetime],
    now: datetime,
) -> float:
    """
    Calculate selection weight for a topic.

    Higher weight = more likely to be selected.
    Weak topics (low mastery) get higher weights.
    Topics not recently practiced get a recency bonus.

    Args:
        mastery: BKT mastery probability [0, 1].
        last_attempted_at: When the topic was last practiced.
        now: Current datetime.

    Returns:
        Weight value (non-negative float).
    """
    recency_bonus = 0.0
    if last_attempted_at:
        hours_ago = (now - last_attempted_at).total_seconds() / 3600
        # More bonus for topics not recently practiced (max 1.0 after 24 hours)
        recency_bonus = min(hours_ago / 24, 1.0)
    return (1 - mastery) ** 2 + 0.15 * recency_bonus


def select_next_question(
    db: Session,
    user_id: int,
    topic_ids: List[int],
    recent_question_ids: List[int],
    last_correct: Optional[bool] = None,
    current_difficulty: str = "medium",
    consecutive_wrong: int = 0,
    mode: str = "adaptive",
) -> Tuple[Optional[Question], str]:
    """
    Select the next question adaptively.

    Args:
        db: Database session.
        user_id: Current user ID.
        topic_ids: List of topic IDs to draw from.
        recent_question_ids: List of recently asked question IDs (for no-repeat).
        last_correct: Whether the last answer was correct (for difficulty staircase).
        current_difficulty: Current difficulty level.
        consecutive_wrong: Number of consecutive wrong answers.
        mode: Quiz mode (adaptive/sequential/random/weak_focus).

    Returns:
        Tuple of (Question or None, why_text explanation).
    """
    if not topic_ids:
        return None, "No topics available."

    if mode == "random":
        return _select_random(db, topic_ids, recent_question_ids, current_difficulty)
    elif mode == "sequential":
        return _select_sequential(db, topic_ids, recent_question_ids)
    else:
        # adaptive or weak_focus
        return _select_adaptive(
            db, user_id, topic_ids, recent_question_ids,
            last_correct, current_difficulty, consecutive_wrong, mode
        )


def _select_adaptive(
    db: Session,
    user_id: int,
    topic_ids: List[int],
    recent_question_ids: List[int],
    last_correct: Optional[bool],
    current_difficulty: str,
    consecutive_wrong: int,
    mode: str,
) -> Tuple[Optional[Question], str]:
    """Adaptive selection using mastery weights and difficulty staircase."""
    now = datetime.utcnow()

    # Get mastery records for all topics
    mastery_map = {}
    last_attempted_map = {}
    for mastery in (
        db.query(Mastery)
        .filter(Mastery.user_id == user_id, Mastery.topic_id.in_(topic_ids))
        .all()
    ):
        mastery_map[mastery.topic_id] = mastery.p_L
        last_attempted_map[mastery.topic_id] = mastery.last_attempted_at

    # Calculate weights for each topic
    topic_weights = []
    for tid in topic_ids:
        p_L = mastery_map.get(tid, 0.3)  # Default p_init for new topics
        last_at = last_attempted_map.get(tid)
        weight = calculate_weight(p_L, last_at, now)
        topic_weights.append((tid, weight, p_L))

    # Sort by weight descending
    topic_weights.sort(key=lambda x: x[1], reverse=True)

    # Determine target difficulty using staircase logic
    target_difficulty = _get_target_difficulty(
        last_correct, current_difficulty, consecutive_wrong
    )

    # Exploration: sometimes pick from non-top-weighted topics
    is_exploring = mode != "weak_focus" and random.random() < EXPLORATION_RATE

    if is_exploring:
        # Sample from all topics
        candidates_tids = [tid for tid, _, _ in topic_weights]
        why_text = "Exploring topic to broaden mastery across syllabus."
    else:
        # Focus on weakest topics
        weak_topics = [(tid, w, p) for tid, w, p in topic_weights if p < 0.6]
        if weak_topics:
            candidates_tids = [tid for tid, _, _ in weak_topics[:5]]
            why_text = "Focusing on a weak topic (mastery < 60%) to improve your grasp."
        else:
            candidates_tids = [tid for tid, _, _ in topic_weights[:5]]
            why_text = "Reinforcing topic to maintain high mastery level."

    # Remedial mode: two consecutive wrong answers → easy question on related topic
    if consecutive_wrong >= 2:
        target_difficulty = "easy"
        why_text = "Stepping back to an easier question to help you build confidence."

    # Find eligible questions
    question = _find_question(
        db, candidates_tids, recent_question_ids, target_difficulty
    )

    if question is None:
        # Fallback 1: try any question from any topic in the list without difficulty constraint
        question = _find_question(db, topic_ids, recent_question_ids, None)
        why_text = "Selected from available questions on active syllabus."

    if question is None:
        # Fallback 2: allow recycling recent questions if pool is exhausted
        question = _find_question(db, topic_ids, [], None)
        why_text = "Reviewing syllabus topic question."

    if question is None:
        return None, "No more questions available."

    return question, why_text


def _get_target_difficulty(
    last_correct: Optional[bool],
    current_difficulty: str,
    consecutive_wrong: int,
) -> str:
    """Apply difficulty staircase logic."""
    difficulties = ["easy", "medium", "hard"]
    if current_difficulty not in difficulties:
        current_difficulty = "medium"

    idx = difficulties.index(current_difficulty)

    if consecutive_wrong >= 2:
        return "easy"
    elif last_correct is True:
        # Correct → step up
        return difficulties[min(idx + 1, len(difficulties) - 1)]
    elif last_correct is False:
        # Wrong → step down
        return difficulties[max(idx - 1, 0)]
    return current_difficulty


def _find_question(
    db: Session,
    topic_ids: List[int],
    recent_question_ids: List[int],
    difficulty: Optional[str],
) -> Optional[Question]:
    """Find a question from the given topics, excluding recent ones."""
    query = (
        db.query(Question)
        .filter(
            Question.topic_id.in_(topic_ids),
            Question.status == "active",
        )
    )

    if recent_question_ids:
        query = query.filter(Question.id.notin_(recent_question_ids[-NO_REPEAT_WINDOW:]))

    if difficulty:
        query = query.filter(Question.difficulty == difficulty)

    questions = query.all()
    if not questions:
        return None

    # Weighted random selection (all equal within difficulty tier)
    return random.choice(questions)


def _select_random(
    db: Session,
    topic_ids: List[int],
    recent_question_ids: List[int],
    difficulty: str,
) -> Tuple[Optional[Question], str]:
    """Random selection."""
    q = _find_question(db, topic_ids, recent_question_ids, None)
    return q, "Randomly selected question."


def _select_sequential(
    db: Session,
    topic_ids: List[int],
    recent_question_ids: List[int],
) -> Tuple[Optional[Question], str]:
    """Sequential selection by question ID."""
    questions = (
        db.query(Question)
        .filter(Question.topic_id.in_(topic_ids), Question.status == "active")
        .order_by(Question.id)
        .all()
    )
    for q in questions:
        if q.id not in recent_question_ids:
            return q, "Next question in sequence."
    return None, "All questions completed."
