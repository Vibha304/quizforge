import io
import csv
import json
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.users import User
from app.models.questions import Question
from app.models.topics import Topic
from app.core.deps import get_current_user

router = APIRouter()


@router.get("/questions")
def export_questions(
    format: str = Query("json", pattern="^(json|csv|docx)$"),
    token: Optional[str] = Query(None),
    topic_id: Optional[int] = Query(None),
    bloom: Optional[str] = Query(None),
    difficulty: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Question)
    if topic_id:
        query = query.filter(Question.topic_id == topic_id)
    if bloom:
        query = query.filter(Question.bloom == bloom.lower())
    if difficulty:
        query = query.filter(Question.difficulty == difficulty.lower())

    questions = query.all()

    if format == "json":
        data = []
        for q in questions:
            opts = json.loads(q.options) if q.options else None
            data.append({
                "id": q.id,
                "topic": q.topic.name if q.topic else None,
                "type": q.type,
                "difficulty": q.difficulty,
                "bloom": q.bloom,
                "stem": q.stem,
                "options": opts,
                "answer": q.answer,
                "explanation": q.explanation,
                "source_snippet": q.source_snippet,
                "status": q.status,
            })
        content = json.dumps(data, indent=2)
        return Response(
            content=content,
            media_type="application/json",
            headers={"Content-Disposition": "attachment; filename=quizforge_questions.json"},
        )

    elif format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "ID", "Topic", "Type", "Difficulty", "Bloom",
            "Stem", "Options", "Answer", "Explanation", "Source Snippet", "Status"
        ])
        for q in questions:
            opts = q.options or ""
            writer.writerow([
                q.id,
                q.topic.name if q.topic else "",
                q.type,
                q.difficulty,
                q.bloom,
                q.stem,
                opts,
                q.answer,
                q.explanation,
                q.source_snippet or "",
                q.status,
            ])
        csv_bytes = output.getvalue().encode("utf-8")
        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=quizforge_questions.csv"},
        )

    elif format == "docx":
        # Create a formatted Word document
        try:
            from docx import Document as DocxDocument
            doc = DocxDocument()
            doc.add_heading("QuizForge Question Bank Export", 0)
            doc.add_paragraph(f"Total Questions: {len(questions)}")

            for idx, q in enumerate(questions, start=1):
                p = doc.add_heading(f"Q{idx}: {q.stem}", level=2)
                t_name = q.topic.name if q.topic else "General"
                doc.add_paragraph(f"Topic: {t_name} | Type: {q.type.upper()} | Difficulty: {q.difficulty.title()} | Bloom: {q.bloom.title()}")

                if q.options:
                    opts = json.loads(q.options)
                    for opt in opts:
                        doc.add_paragraph(f"• {opt}")

                doc.add_paragraph(f"Correct Answer: {q.answer}")
                if q.explanation:
                    doc.add_paragraph(f"Explanation: {q.explanation}")
                doc.add_paragraph("-" * 40)

            docx_io = io.BytesIO()
            doc.save(docx_io)
            docx_io.seek(0)
            return Response(
                content=docx_io.getvalue(),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": "attachment; filename=quizforge_questions.docx"},
            )
        except ImportError:
            # Fallback to plain text if python-docx isn't present
            text_lines = [f"Q: {q.stem}\nA: {q.answer}\n" for q in questions]
            return Response(
                content="\n".join(text_lines),
                media_type="text/plain",
                headers={"Content-Disposition": "attachment; filename=quizforge_questions.txt"},
            )
