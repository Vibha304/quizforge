"""Ollama local LLM provider using httpx."""
import json
import logging
from typing import List
from app.llm.base import LLMProvider, QuestionData
from app.config import settings

logger = logging.getLogger(__name__)


class OllamaProvider(LLMProvider):
    """LLM provider using Ollama for local model inference."""

    DEFAULT_MODEL = "mistral"
    TIMEOUT = 120.0

    def __init__(self, model: str = None):
        self.base_url = settings.OLLAMA_BASE_URL.rstrip("/")
        self.model = model or self.DEFAULT_MODEL

    def generate_questions(
        self,
        topic_name: str,
        topic_keywords: List[str],
        source_text: str,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[QuestionData]:
        try:
            import httpx
            prompt = self._build_prompt(topic_name, topic_keywords, source_text, count, difficulty)
            payload = {
                "model": self.model,
                "prompt": prompt,
                "format": "json",
                "stream": False,
                "options": {"temperature": 0.7},
            }
            response = httpx.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.TIMEOUT,
            )
            response.raise_for_status()
            data = response.json()
            result = json.loads(data.get("response", "{}"))
            questions = self._parse_response(result)
            valid = [q for q in questions if self._validate_question(q)]
            if valid:
                return valid[:count]
        except Exception as e:
            logger.warning(f"Ollama failed: {e}")
        return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

    def _build_prompt(self, topic, keywords, source, count, difficulty):
        kw_str = ", ".join(keywords) if keywords else topic
        source_excerpt = source[:1000] if len(source) > 1000 else source
        return f"""Generate {count} quiz questions about "{topic}" (keywords: {kw_str}).
Difficulty: {difficulty}. Source context: {source_excerpt}

Return JSON: {{"questions": [{{type, difficulty, bloom, stem, options, answer, explanation}}]}}
Types: mcq (4 options), true_false, short_answer"""

    def _parse_response(self, data: dict) -> List[QuestionData]:
        questions = []
        for item in data.get("questions", []):
            try:
                questions.append(QuestionData(
                    type=item.get("type", "mcq"),
                    difficulty=item.get("difficulty", "medium"),
                    bloom=item.get("bloom", "remember"),
                    stem=item.get("stem", ""),
                    options=item.get("options"),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                    source_snippet=item.get("source_snippet"),
                ))
            except Exception:
                continue
        return questions

    def _fallback(self, topic, keywords, source, count, difficulty):
        from app.llm.mock import MockProvider
        return MockProvider().generate_questions(topic, keywords, source, count, difficulty)
