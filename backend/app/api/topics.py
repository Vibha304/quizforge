import json
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.models.topics import Topic
from app.models.questions import Question
from app.schemas.topics import TopicResponse, TopicUpdate
from app.schemas.questions import QuestionResponse
from app.core.deps import get_current_user
from app.services.generation.generator import QuestionGenerator

router = APIRouter()


@router.patch("/{topic_id}", response_model=TopicResponse)
def update_topic(
    topic_id: int,
    req: TopicUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    if req.name is not None:
        topic.name = req.name.strip()
    if req.keywords is not None:
        topic.keywords = json.dumps(req.keywords)
    if req.difficulty_prior is not None:
        topic.difficulty_prior = max(0.0, min(1.0, req.difficulty_prior))
    if req.summary is not None:
        topic.summary = req.summary

    db.commit()
    db.refresh(topic)

    kws = json.loads(topic.keywords) if topic.keywords else []
    return TopicResponse(
        id=topic.id,
        document_id=topic.document_id,
        parent_id=topic.parent_id,
        name=topic.name,
        keywords=kws,
        summary=topic.summary,
        difficulty_prior=topic.difficulty_prior,
        question_count=topic.question_count,
    )


@router.post("/{topic_id}/generate", response_model=List[QuestionResponse])
def generate_questions_for_topic(
    topic_id: int,
    count: int = 5,
    difficulty: str = "mixed",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Topic not found")

    generator = QuestionGenerator(db=db)
    generated = generator.generate_for_topic(topic, count=count, difficulty=difficulty)

    results = []
    for q in generated:
        opts = json.loads(q.options) if q.options else None
        results.append(
            QuestionResponse(
                id=q.id,
                topic_id=q.topic_id,
                topic_name=topic.name,
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
    return results
