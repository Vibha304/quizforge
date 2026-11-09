from datetime import datetime, timedelta
from app.services.adaptive.selector import calculate_weight, select_next_question
from app.models.topics import Topic
from app.models.questions import Question
from app.models.mastery import Mastery


def test_weight_calculation_prioritizes_weak_topics():
    """Verify weak topics (low mastery) receive significantly higher weight."""
    now = datetime.utcnow()
    # Weak topic (mastery = 0.20): (1 - 0.2)^2 = 0.64
    weight_weak = calculate_weight(mastery=0.20, last_attempted_at=now, now=now)

    # Mastered topic (mastery = 0.90): (1 - 0.9)^2 = 0.01
    weight_mastered = calculate_weight(mastery=0.90, last_attempted_at=now, now=now)

    assert weight_weak > weight_mastered * 10


def test_weight_recency_bonus():
    """Verify topics not practiced recently receive a recency bonus."""
    now = datetime.utcnow()
    one_day_ago = now - timedelta(days=1)

    weight_recent = calculate_weight(mastery=0.50, last_attempted_at=now, now=now)
    weight_dormant = calculate_weight(mastery=0.50, last_attempted_at=one_day_ago, now=now)

    assert weight_dormant > weight_recent


def test_adaptive_selector_no_repeat(db_session, test_user):
    """Verify questions in recent_question_ids are not immediately repeated."""
    # Create topic and questions
    t = Topic(document_id=1, name="Routing Protocols", difficulty_prior=0.5)
    db_session.add(t)
    db_session.flush()

    q1 = Question(topic_id=t.id, stem="Q1 Dijkstra", type="mcq", difficulty="medium", answer="A", status="active")
    q2 = Question(topic_id=t.id, stem="Q2 Bellman-Ford", type="mcq", difficulty="medium", answer="B", status="active")
    db_session.add_all([q1, q2])
    db_session.flush()

    # If q1 is in recent_question_ids, selector must choose q2
    selected_q, why_text = select_next_question(
        db=db_session,
        user_id=test_user.id,
        topic_ids=[t.id],
        recent_question_ids=[q1.id],
        mode="adaptive",
    )

    assert selected_q is not None
    assert selected_q.id == q2.id
    assert "Routing Protocols" in why_text or "mastery" in why_text.lower()
