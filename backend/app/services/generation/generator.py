"""
Question generator service that calls LLM, validates, and deduplicates questions.
"""
import json
import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from app.llm.base import LLMProvider, QuestionData
from app.llm.factory import get_provider
from app.models.topics import Topic
from app.models.questions import Question

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """Orchestrates LLM calls to generate and persist questions for topics."""

    def __init__(self, db: Session, provider: Optional[LLMProvider] = None):
        self.db = db
        self.provider = provider or get_provider()

    def generate_for_topic(
        self,
        topic: Topic,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[Question]:
        """
        Generate questions for a topic and save them to the database.

        Args:
            topic: The Topic model instance.
            count: Number of questions to generate.
            difficulty: "easy", "medium", "hard", or "mixed".

        Returns:
            List of saved Question model instances.
        """
        try:
            # Load keywords from JSON
            keywords = json.loads(topic.keywords) if topic.keywords else []
            source_text = topic.summary or ""

            # Request slightly more than needed for deduplication
            request_count = min(count + 3, 20)
            raw_questions = self.provider.generate_questions(
                topic_name=topic.name,
                topic_keywords=keywords,
                source_text=source_text,
                count=request_count,
                difficulty=difficulty,
            )

            # Deduplicate against existing questions
            existing_stems = {
                q.stem.lower().strip()
                for q in self.db.query(Question)
                .filter(Question.topic_id == topic.id)
                .all()
            }

            saved = []
            for q_data in raw_questions:
                if q_data.stem.lower().strip() in existing_stems:
                    continue
                if len(saved) >= count:
                    break
                question = self._save_question(topic.id, q_data)
                if question:
                    saved.append(question)
                    existing_stems.add(q_data.stem.lower().strip())

            self.db.commit()
            logger.info(f"Generated {len(saved)} questions for topic '{topic.name}'")
            return saved

        except Exception as e:
            logger.error(f"Question generation failed for topic {topic.id}: {e}")
            self.db.rollback()
            return []

    def _save_question(self, topic_id: int, q_data: QuestionData) -> Optional[Question]:
        """Save a QuestionData object to the database."""
        try:
            options_json = json.dumps(q_data.options) if q_data.options else None
            time_limit = self._get_time_limit(q_data.difficulty, q_data.type)

            question = Question(
                topic_id=topic_id,
                type=q_data.type,
                difficulty=q_data.difficulty,
                bloom=q_data.bloom,
                stem=q_data.stem,
                options=options_json,
                answer=q_data.answer,
                explanation=q_data.explanation or "",
                source_snippet=q_data.source_snippet,
                status="active",
                time_limit_ms=time_limit,
            )
            self.db.add(question)
            self.db.flush()  # Get the ID without committing
            return question
        except Exception as e:
            logger.error(f"Failed to save question: {e}")
            return None

    def _get_time_limit(self, difficulty: str, qtype: str) -> int:
        """Return time limit in ms based on difficulty and question type."""
        base = {
            "easy": 20_000,
            "medium": 30_000,
            "hard": 45_000,
        }.get(difficulty, 30_000)

        if qtype == "short_answer":
            base = base * 2  # More time for short answer
        return base
