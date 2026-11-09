import pytest
from app.services.bkt.tracker import update_bkt, get_p_init
from app.models.mastery import Mastery


def test_bkt_correct_mcq():
    """Verify BKT update formula on correct MCQ answer."""
    p_init = 0.40
    p_next = update_bkt(p_L=p_init, correct=True, question_type="mcq")
    # Expected: ~0.750
    assert p_next > p_init
    assert round(p_next, 2) == 0.75


def test_bkt_wrong_mcq():
    """Verify BKT update formula on incorrect MCQ answer."""
    p_init = 0.40
    p_next = update_bkt(p_L=p_init, correct=False, question_type="mcq")
    # Expected: ~0.219
    assert p_next < p_init
    assert round(p_next, 2) == 0.22


def test_bkt_true_false_guess():
    """Verify BKT update with true_false guess parameter (p_guess = 0.50)."""
    p_init = 0.50
    p_correct = update_bkt(p_L=p_init, correct=True, question_type="true_false")
    p_wrong = update_bkt(p_L=p_init, correct=False, question_type="true_false")
    assert p_correct > p_init
    assert p_wrong < p_init


def test_p_init_range():
    """Verify p_init maps difficulty_prior [0, 1] to [0.25, 0.40]."""
    assert get_p_init(0.0) == 0.25
    assert get_p_init(1.0) == 0.40
    assert round(get_p_init(0.5), 3) == 0.325


def test_mastery_weak_and_mastered_properties():
    """Verify Mastery properties: is_weak (<0.6, >=3 attempts) and is_mastered (>=0.9)."""
    m_weak = Mastery(user_id=1, topic_id=1, p_L=0.45, attempts_count=3)
    assert m_weak.is_weak is True
    assert m_weak.is_mastered is False

    m_not_enough_attempts = Mastery(user_id=1, topic_id=2, p_L=0.45, attempts_count=2)
    assert m_not_enough_attempts.is_weak is False

    m_mastered = Mastery(user_id=1, topic_id=3, p_L=0.92, attempts_count=5)
    assert m_mastered.is_mastered is True
    assert m_mastered.is_weak is False
