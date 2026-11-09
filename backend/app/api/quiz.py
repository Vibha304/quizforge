import json
import logging
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.models.quiz import QuizSession, Attempt
from app.models.questions import Question
from app.models.topics import Topic
from app.models.gamification import UserStats, Badge
from app.schemas.quiz import QuizStartRequest, QuizSessionResponse, AnswerRequest, AnswerResponse
from app.schemas.questions import QuestionResponse
from app.schemas.gamification import BadgeResponse
from app.core.deps import get_current_user
from app.services.bkt.tracker import record_attempt
from app.services.adaptive.selector import select_next_question
from app.services.gamification.engine import (
    calculate_xp,
    award_xp,
    ensure_user_stats,
    check_and_award_badges,
)

router = APIRouter()
logger = logging.getLogger(__name__)


def _to_question_response(q: Question) -> QuestionResponse:
    opts = json.loads(q.options) if q.options else None
    return QuestionResponse(
        id=q.id,
        topic_id=q.topic_id,
        topic_name=q.topic.name if q.topic else None,
        type=q.type,
        difficulty=q.difficulty,
        bloom=q.bloom,
        stem=q.stem,
        options=opts,
        answer=q.answer,
        explanation=q.explanation or "",
        source_snippet=q.source_snippet,
        status=q.status,
        time_limit_ms=q.time_limit_ms,
    )


@router.post("/start", response_model=QuizSessionResponse)
def start_quiz(
    req: QuizStartRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic_ids = req.topic_ids
    if not topic_ids:
        topics = []
        if req.document_id:
            topics = db.query(Topic).filter(Topic.document_id == req.document_id).all()
        if not topics:
            topics = db.query(Topic).all()
        topic_ids = [t.id for t in topics]

    if not topic_ids:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No topics found for this document.",
        )

    # Select the first question adaptively
    first_q, why_text = select_next_question(
        db=db,
        user_id=current_user.id,
        topic_ids=topic_ids,
        recent_question_ids=[],
        mode=req.mode,
    )

    if not first_q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No questions found for the selected topics.",
        )

    session = QuizSession(
        user_id=current_user.id,
        document_id=req.document_id,
        mode=req.mode,
        status="active",
        max_questions=req.max_questions,
        question_ids_json=json.dumps([first_q.id]),
        recent_question_ids_json=json.dumps([first_q.id]),
        current_streak=0,
        current_combo=0,
        attempt_count=0,
        correct_count=0,
        score=0.0,
        xp_earned=0,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)

    return QuizSessionResponse(
        id=session.id,
        mode=session.mode,
        status=session.status,
        score=session.score,
        xp_earned=session.xp_earned,
        current_question=_to_question_response(first_q),
        why_text=why_text,
        attempt_count=session.attempt_count,
        correct_count=session.correct_count,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


@router.get("/{session_id}", response_model=QuizSessionResponse)
def get_quiz_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(QuizSession)
        .filter(QuizSession.id == session_id, QuizSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz session not found")

    recent_ids = json.loads(session.recent_question_ids_json) if session.recent_question_ids_json else []
    current_q = None
    if recent_ids:
        current_q_obj = db.query(Question).filter(Question.id == recent_ids[-1]).first()
        if current_q_obj:
            current_q = _to_question_response(current_q_obj)

    return QuizSessionResponse(
        id=session.id,
        mode=session.mode,
        status=session.status,
        score=session.score,
        xp_earned=session.xp_earned,
        current_question=current_q,
        why_text=None,
        attempt_count=session.attempt_count,
        correct_count=session.correct_count,
        started_at=session.started_at,
        completed_at=session.completed_at,
    )


@router.post("/{session_id}/answer", response_model=AnswerResponse)
def submit_answer(
    session_id: int,
    req: AnswerRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(QuizSession)
        .filter(QuizSession.id == session_id, QuizSession.user_id == current_user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Quiz session not found")
    if session.status == "completed":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Quiz session is already completed")

    question = db.query(Question).filter(Question.id == req.question_id).first()
    if not question:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    # Evaluate correctness
    user_ans = req.answer.strip()
    correct_ans = question.answer.strip()
    if question.type == "true_false":
        is_correct = user_ans.lower() == correct_ans.lower()
    elif question.type == "mcq":
        is_correct = user_ans.lower() == correct_ans.lower() or (
            len(user_ans) == 1 and user_ans.upper() in ["A", "B", "C", "D"] and correct_ans.startswith(user_ans.upper())
        )
    else:  # short_answer
        is_correct = user_ans.lower() == correct_ans.lower() or correct_ans.lower() in user_ans.lower()

    # Update BKT mastery
    topic = question.topic
    difficulty_prior = topic.difficulty_prior if topic else 0.5
    m_before, m_after = record_attempt(
        db=db,
        user_id=current_user.id,
        topic_id=question.topic_id,
        correct=is_correct,
        question_type=question.type,
        difficulty_prior=difficulty_prior,
    )
    mastery_delta = round(m_after - m_before, 4)

    # Gamification: streak & combo & XP
    if is_correct:
        session.current_streak += 1
        session.current_combo += 1
        session.correct_count += 1
        xp_gained = calculate_xp(
            difficulty=question.difficulty,
            streak=session.current_streak,
            response_ms=req.response_ms,
            time_limit_ms=question.time_limit_ms,
        )
    else:
        session.current_streak = 0
        session.current_combo = 0
        xp_gained = 0

    session.attempt_count += 1
    session.xp_earned += xp_gained
    session.score = round(session.correct_count / session.attempt_count, 3)

    # Award XP and update level
    stats = award_xp(db, current_user.id, xp_gained)
    stats.total_attempts += 1
    if is_correct:
        stats.total_correct += 1
    stats.streak = max(stats.streak, session.current_streak)
    stats.last_active = datetime.utcnow()

    # Save Attempt record
    attempt = Attempt(
        session_id=session.id,
        user_id=current_user.id,
        question_id=question.id,
        answer_given=user_ans,
        correct=is_correct,
        response_ms=req.response_ms,
        xp_gained=xp_gained,
        mastery_before=m_before,
        mastery_after=m_after,
        ts=datetime.utcnow(),
    )
    db.add(attempt)
    db.flush()

    # Check Badges
    badge_context = {
        "total_attempts": stats.total_attempts,
        "total_correct": stats.total_correct,
        "streak": session.current_streak,
        "session_score": session.score,
        "session_questions": session.attempt_count,
        "session_correct": session.correct_count,
        "mastery_p_L": m_after,
        "response_ms": req.response_ms,
        "time_limit_ms": question.time_limit_ms,
        "hour": datetime.utcnow().hour,
    }
    new_badges = check_and_award_badges(db, current_user.id, badge_context)

    # Next question logic
    recent_ids = json.loads(session.recent_question_ids_json) if session.recent_question_ids_json else []
    all_q_ids = json.loads(session.question_ids_json) if session.question_ids_json else []
    if question.id not in recent_ids:
        recent_ids.append(question.id)

    is_complete = session.attempt_count >= session.max_questions

    next_q = None
    why_text = None
    if not is_complete:
        # Get topics for session
        topics = db.query(Topic).filter(Topic.document_id == session.document_id).all() if session.document_id else [topic]
        topic_ids = [t.id for t in topics] if topics else [question.topic_id]

        next_q_obj, why_text = select_next_question(
            db=db,
            user_id=current_user.id,
            topic_ids=topic_ids,
            recent_question_ids=recent_ids,
            last_correct=is_correct,
            current_difficulty=question.difficulty,
            consecutive_wrong=0 if is_correct else 1,
            mode=session.mode,
        )
        if next_q_obj:
            next_q = _to_question_response(next_q_obj)
            all_q_ids.append(next_q_obj.id)
            recent_ids.append(next_q_obj.id)
            if len(recent_ids) > 10:
                recent_ids = recent_ids[-10:]
        else:
            is_complete = True

    if is_complete:
        session.status = "completed"
        session.completed_at = datetime.utcnow()
        stats.total_quizzes += 1

    session.question_ids_json = json.dumps(all_q_ids)
    session.recent_question_ids_json = json.dumps(recent_ids)
    db.commit()

    badge_responses = [
        BadgeResponse(
            code=b.code,
            name=b.name,
            description=b.description,
            icon=b.icon,
            earned_at=datetime.utcnow(),
        )
        for b in new_badges
    ]

    return AnswerResponse(
        correct=is_correct,
        correct_answer=question.answer,
        explanation=question.explanation or "",
        xp_gained=xp_gained,
        new_xp_total=stats.xp,
        new_level=stats.level,
        mastery_delta=mastery_delta,
        new_mastery=m_after,
        badges_unlocked=badge_responses,
        streak=session.current_streak,
        combo=session.current_combo,
        next_question=next_q,
        why_text=why_text,
        session_complete=is_complete,
    )
