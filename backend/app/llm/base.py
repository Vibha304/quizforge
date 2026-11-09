from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class QuestionData:
    """Represents a single generated question."""
    type: str  # mcq | true_false | short_answer
    difficulty: str  # easy | medium | hard
    bloom: str  # remember | understand | apply | analyze | evaluate | create
    stem: str
    options: Optional[List[str]]  # None for non-MCQ
    answer: str
    explanation: str
    source_snippet: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for all LLM providers."""

    @abstractmethod
    def generate_questions(
        self,
        topic_name: str,
        topic_keywords: List[str],
        source_text: str,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[QuestionData]:
        """
        Generate questions for a given topic.

        Args:
            topic_name: Name of the topic to generate questions for.
            topic_keywords: Keywords associated with the topic.
            source_text: Relevant text from the source document.
            count: Number of questions to generate.
            difficulty: "easy", "medium", "hard", or "mixed".

        Returns:
            List of QuestionData objects.
        """
        ...

    def _validate_question(self, q: QuestionData) -> bool:
        """Validate that a question has all required fields."""
        if not q.stem or len(q.stem.strip()) < 10:
            return False
        if not q.answer or len(q.answer.strip()) == 0:
            return False
        if q.type == "mcq":
            if not q.options or len(q.options) != 4:
                return False
            if q.answer not in q.options:
                return False
        if q.type == "true_false":
            if q.answer not in ("True", "False", "true", "false"):
                return False
        if q.difficulty not in ("easy", "medium", "hard"):
            return False
        if q.bloom not in ("remember", "understand", "apply", "analyze", "evaluate", "create"):
            return False
        return True
