"""
Bayesian Knowledge Tracing (BKT) implementation.

Implements the standard BKT update rules:
- Correct: pL' = pL(1−slip) / [pL(1−slip) + (1−pL)·guess]
- Wrong:   pL' = pL·slip / [pL·slip + (1−pL)(1−guess)]
- Transition: pL_next = pL' + (1−pL')·p_transit
"""
import json
import logging
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.mastery import Mastery

logger = logging.getLogger(__name__)

BKT_PARAMS = {
    "p_transit": 0.15,
    "p_slip": 0.10,
    "p_guess_mcq": 0.25,
    "p_guess_tf": 0.50,
}


def get_p_init(difficulty_prior: float) -> float:
    """Map difficulty_prior [0,1] to p_init [0.25, 0.4]."""
    return 0.25 + difficulty_prior * 0.15


def update_bkt(p_L: float, correct: bool, question_type: str) -> float:
    """
    Update mastery using Bayesian Knowledge Tracing.

    Args:
        p_L: Current mastery probability [0, 1].
        correct: Whether the student answered correctly.
        question_type: "true_false" or other (MCQ default).

    Returns:
        Updated mastery probability.
    """
    p_slip = BKT_PARAMS["p_slip"]
    p_guess = BKT_PARAMS["p_guess_tf"] if question_type == "true_false" else BKT_PARAMS["p_guess_mcq"]
    p_transit = BKT_PARAMS["p_transit"]

    if correct:
        # Evidence update: correct answer
        numerator = p_L * (1 - p_slip)
        denominator = p_L * (1 - p_slip) + (1 - p_L) * p_guess
        p_L_prime = numerator / denominator
    else:
        # Evidence update: wrong answer
        numerator = p_L * p_slip
        denominator = p_L * p_slip + (1 - p_L) * (1 - p_guess)
        p_L_prime = numerator / denominator

    # Transition: account for learning
    p_L_next = p_L_prime + (1 - p_L_prime) * p_transit
    return round(p_L_next, 4)


def get_or_create_mastery(
    db: Session,
    user_id: int,
    topic_id: int,
    difficulty_prior: float = 0.5,
) -> Mastery:
    """Get existing mastery record or create a new one with p_init."""
    mastery = (
        db.query(Mastery)
        .filter(Mastery.user_id == user_id, Mastery.topic_id == topic_id)
        .first()
    )
    if mastery is None:
        p_init = get_p_init(difficulty_prior)
        mastery = Mastery(
            user_id=user_id,
            topic_id=topic_id,
            p_L=p_init,
            attempts_count=0,
            history_json="[]",
        )
        db.add(mastery)
        db.flush()
    return mastery


def record_attempt(
    db: Session,
    user_id: int,
    topic_id: int,
    correct: bool,
    question_type: str,
    difficulty_prior: float = 0.5,
) -> tuple[float, float]:
    """
    Record an attempt and update BKT mastery.

    Args:
        db: Database session.
        user_id: ID of the user.
        topic_id: ID of the topic.
        correct: Whether the answer was correct.
        question_type: Type of question (mcq, true_false, short_answer).
        difficulty_prior: Topic difficulty prior [0, 1].

    Returns:
        Tuple of (mastery_before, mastery_after).
    """
    mastery = get_or_create_mastery(db, user_id, topic_id, difficulty_prior)
    p_before = mastery.p_L

    # Update BKT
    p_after = update_bkt(p_before, correct, question_type)

    # Update mastery record
    mastery.p_L = p_after
    mastery.attempts_count += 1
    mastery.last_attempted_at = datetime.utcnow()

    # Append to history
    history = json.loads(mastery.history_json or "[]")
    history.append({
        "ts": datetime.utcnow().isoformat(),
        "p_L": p_after,
        "correct": correct,
    })
    # Keep last 100 history entries
    mastery.history_json = json.dumps(history[-100:])
    mastery.updated_at = datetime.utcnow()

    db.flush()
    return p_before, p_after
