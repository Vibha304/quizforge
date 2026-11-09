import json
from app.models.documents import Document
from app.models.topics import Topic
from app.models.questions import Question


def test_health_endpoint(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "healthy"


def test_quiz_flow(client, db_session, test_user, auth_headers):
    # Setup document, topic, question
    doc = Document(user_id=test_user.id, filename="test.pdf", original_filename="test.pdf")
    db_session.add(doc)
    db_session.flush()

    top = Topic(document_id=doc.id, name="Physical Layer", difficulty_prior=0.4)
    db_session.add(top)
    db_session.flush()

    q = Question(
        topic_id=top.id,
        type="mcq",
        difficulty="medium",
        stem="Which cable has highest bandwidth?",
        options=json.dumps(["Fiber Optic", "Coaxial", "UTP", "STP"]),
        answer="Fiber Optic",
        explanation="Fiber uses light pulses with extreme bandwidth.",
        status="active",
        time_limit_ms=30000,
    )
    db_session.add(q)
    db_session.commit()

    # 1. Start Quiz
    start_res = client.post(
        "/quiz/start",
        json={"document_id": doc.id, "mode": "adaptive", "max_questions": 5},
        headers=auth_headers,
    )
    assert start_res.status_code == 200
    session_data = start_res.json()
    assert session_data["status"] == "active"
    assert session_data["current_question"]["id"] == q.id
    session_id = session_data["id"]

    # 2. Submit Correct Answer
    ans_res = client.post(
        f"/quiz/{session_id}/answer",
        json={"question_id": q.id, "answer": "Fiber Optic", "response_ms": 6000},
        headers=auth_headers,
    )
    assert ans_res.status_code == 200
    ans_data = ans_res.json()
    assert ans_data["correct"] is True
    assert ans_data["xp_gained"] > 0
    assert ans_data["streak"] == 1
    assert ans_data["mastery_delta"] > 0
