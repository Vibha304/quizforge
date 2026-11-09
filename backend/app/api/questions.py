import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.models.questions import Question
from app.models.topics import Topic
from app.schemas.questions import QuestionResponse, QuestionListResponse
from app.core.deps import get_current_user

router = APIRouter()


@router.get("", response_model=QuestionListResponse)
def list_questions(
    topic_id: Optional[int] = Query(None),
    document_id: Optional[int] = Query(None),
    difficulty: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
    bloom: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Question)

    if topic_id is not None:
        query = query.filter(Question.topic_id == topic_id)
    elif document_id is not None:
        query = query.join(Topic).filter(Topic.document_id == document_id)

    if difficulty:
        query = query.filter(Question.difficulty == difficulty.lower())
    if type:
        query = query.filter(Question.type == type.lower())
    if bloom:
        query = query.filter(Question.bloom == bloom.lower())
    if status:
        query = query.filter(Question.status == status.lower())

    total = query.count()
    questions = query.order_by(Question.id.asc()).offset(skip).limit(limit).all()

    items = []
    for q in questions:
        opts = json.loads(q.options) if q.options else None
        items.append(
            QuestionResponse(
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
        )

    return QuestionListResponse(items=items, total=total, skip=skip, limit=limit)


@router.patch("/{question_id}", response_model=QuestionResponse)
def update_question_status(
    question_id: int,
    status_val: Optional[str] = Query(None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    q = db.query(Question).filter(Question.id == question_id).first()
    if not q:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Question not found")

    if status_val:
        q.status = status_val.lower()
        db.commit()
        db.refresh(q)

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
