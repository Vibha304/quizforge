import os
import json
import logging
import shutil
import threading
from typing import Dict, List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.database import get_db, SessionLocal
from app.models.users import User
from app.models.documents import Document
from app.models.topics import Topic
from app.models.questions import Question
from app.schemas.documents import DocumentResponse, DocumentListResponse, ProgressEvent
from app.schemas.topics import TopicResponse
from app.core.deps import get_current_user
from app.services.parsing.parser import parse_document
from app.services.topics.extractor import extract_topics
from app.services.generation.generator import QuestionGenerator

router = APIRouter()
logger = logging.getLogger(__name__)

# In-memory progress tracking for documents: {doc_id: ProgressEvent}
DOC_PROGRESS: Dict[int, ProgressEvent] = {}

UPLOAD_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


def process_document_background(doc_id: int, file_path: str):
    """Background processing task: Parse -> Extract Topics -> Generate Questions."""
    db: Session = SessionLocal()
    try:
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if not doc:
            return

        # Stage 1: Parsing
        doc.status = "parsing"
        db.commit()
        DOC_PROGRESS[doc_id] = ProgressEvent(stage="parsing", message="Parsing document structure...", progress=20.0)

        parsed = parse_document(file_path)
        if parsed.error or parsed.is_scanned:
            doc.status = "error"
            doc.error_message = parsed.error or "Scanned PDF detected without readable text."
            db.commit()
            DOC_PROGRESS[doc_id] = ProgressEvent(stage="error", message=doc.error_message, progress=100.0)
            return

        doc.raw_text = parsed.raw_text
        doc.page_count = parsed.page_count
        sections_data = [{"title": s.title, "level": s.level, "page": s.page_number} for s in parsed.sections]
        doc.structure_json = json.dumps(sections_data)
        doc.status = "extracting_topics"
        db.commit()

        # Stage 2: Extracting Topics
        DOC_PROGRESS[doc_id] = ProgressEvent(stage="extracting_topics", message="Extracting syllabus hierarchy & topics...", progress=50.0)
        extracted = extract_topics(parsed)
        if not extracted:
            # Fallback single root topic
            from app.services.topics.extractor import ExtractedTopic
            extracted = [ExtractedTopic(name="General Overview", keywords=["syllabus", "course"], summary=parsed.raw_text[:400])]

        topic_map = {}
        for idx, ext in enumerate(extracted):
            parent_id = topic_map.get(ext.parent_name) if ext.parent_name else None
            t = Topic(
                document_id=doc.id,
                parent_id=parent_id,
                name=ext.name,
                keywords=json.dumps(ext.keywords),
                summary=ext.summary,
                difficulty_prior=ext.difficulty_prior,
                order_index=idx,
            )
            db.add(t)
            db.flush()
            topic_map[ext.name] = t.id

        db.commit()

        # Stage 3: Generating Questions
        doc.status = "generating"
        db.commit()
        DOC_PROGRESS[doc_id] = ProgressEvent(stage="generating_questions", message="Generating initial AI questions...", progress=75.0)

        generator = QuestionGenerator(db=db)
        topics = db.query(Topic).filter(Topic.document_id == doc.id).all()
        # Generate initial questions for top subtopics/topics
        target_topics = [t for t in topics if t.parent_id is not None] or topics
        for t in target_topics[:8]:
            try:
                generator.generate_for_topic(t, count=3, difficulty="mixed")
            except Exception as gen_err:
                logger.warning(f"Error generating questions for topic {t.name}: {gen_err}")

        doc.status = "ready"
        db.commit()
        DOC_PROGRESS[doc_id] = ProgressEvent(stage="done", message="Syllabus parsed and questions ready!", progress=100.0)

    except Exception as e:
        logger.exception(f"Document processing failed for {doc_id}: {e}")
        doc = db.query(Document).filter(Document.id == doc_id).first()
        if doc:
            doc.status = "error"
            doc.error_message = str(e)
            db.commit()
        DOC_PROGRESS[doc_id] = ProgressEvent(stage="error", message=f"Failed: {str(e)}", progress=100.0)
    finally:
        db.close()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not file.filename.lower().endswith((".pdf", ".docx", ".doc")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only PDF and DOCX files are supported.",
        )

    # Save to disk
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    safe_filename = f"{timestamp}_{file.filename}"
    saved_path = os.path.join(UPLOAD_DIR, safe_filename)

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    file_size = os.path.getsize(saved_path)
    if file_size > 20 * 1024 * 1024:
        os.remove(saved_path)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds maximum limit of 20MB.",
        )

    doc = Document(
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename,
        file_size=file_size,
        mime_type=file.content_type or "application/octet-stream",
        status="pending",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    DOC_PROGRESS[doc.id] = ProgressEvent(stage="parsing", message="File uploaded, starting parsing...", progress=10.0)
    background_tasks.add_task(process_document_background, doc.id, saved_path)

    return DocumentResponse(
        id=doc.id,
        filename=doc.original_filename,
        status=doc.status,
        topic_count=0,
        question_count=0,
        created_at=doc.created_at,
        error_message=None,
    )


@router.get("", response_model=DocumentListResponse)
def list_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(Document).filter(Document.user_id == current_user.id)
    total = query.count()
    docs = query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()

    items = [
        DocumentResponse(
            id=d.id,
            filename=d.original_filename,
            status=d.status,
            topic_count=d.topic_count,
            question_count=d.question_count,
            created_at=d.created_at,
            error_message=d.error_message,
        )
        for d in docs
    ]
    return DocumentListResponse(items=items, total=total, skip=skip, limit=limit)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    return DocumentResponse(
        id=doc.id,
        filename=doc.original_filename,
        status=doc.status,
        topic_count=doc.topic_count,
        question_count=doc.question_count,
        created_at=doc.created_at,
        error_message=doc.error_message,
    )


@router.get("/{document_id}/topics", response_model=List[TopicResponse])
def get_document_topics(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    topics = db.query(Topic).filter(Topic.document_id == document_id).order_by(Topic.order_index).all()
    results = []
    for t in topics:
        kws = json.loads(t.keywords) if t.keywords else []
        results.append(
            TopicResponse(
                id=t.id,
                document_id=t.document_id,
                parent_id=t.parent_id,
                name=t.name,
                keywords=kws,
                summary=t.summary,
                difficulty_prior=t.difficulty_prior,
                question_count=t.question_count,
            )
        )
    return results


@router.get("/{document_id}/progress")
def get_document_progress(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Returns SSE progress or JSON progress for the document parsing pipeline."""
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")

    progress = DOC_PROGRESS.get(
        document_id,
        ProgressEvent(
            stage="done" if doc.status == "ready" else doc.status,
            message="Processing complete" if doc.status == "ready" else f"Status: {doc.status}",
            progress=100.0 if doc.status == "ready" else 20.0,
        ),
    )
    return progress
