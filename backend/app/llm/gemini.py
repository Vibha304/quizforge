"""Gemini LLM provider using google-generativeai."""
import json
import time
import logging
from typing import List, Optional
from app.llm.base import LLMProvider, QuestionData
from app.config import settings

logger = logging.getLogger(__name__)


class GeminiProvider(LLMProvider):
    """LLM provider using Google's Gemini API."""

    MODEL = "gemini-1.5-flash"
    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    def __init__(self):
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self.model = genai.GenerativeModel(self.MODEL)
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
            self.model = None

    def generate_questions(
        self,
        topic_name: str,
        topic_keywords: List[str],
        source_text: str,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[QuestionData]:
        if self.model is None:
            return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

        prompt = self._build_prompt(topic_name, topic_keywords, source_text, count, difficulty)
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.model.generate_content(
                    prompt,
                    generation_config={"temperature": 0.7, "response_mime_type": "application/json"},
                )
                data = json.loads(response.text)
                questions = self._parse_response(data)
                valid = [q for q in questions if self._validate_question(q)]
                if valid:
                    return valid[:count]
            except Exception as e:
                logger.warning(f"Gemini attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
        logger.error("All Gemini attempts failed, falling back to mock")
        return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

    def _build_prompt(
        self, topic: str, keywords: List[str], source: str, count: int, difficulty: str
    ) -> str:
        kw_str = ", ".join(keywords) if keywords else topic
        diff_str = difficulty if difficulty != "mixed" else "a mix of easy, medium, and hard"
        source_excerpt = source[:1500] if len(source) > 1500 else source
        return f"""Generate {count} educational quiz questions about the topic: "{topic}".
Keywords: {kw_str}
Difficulty: {diff_str}

Source text (for context):
{source_excerpt}

Return a JSON object with a "questions" array. Each question must have:
- type: "mcq", "true_false", or "short_answer"
- difficulty: "easy", "medium", or "hard"
- bloom: one of "remember", "understand", "apply", "analyze", "evaluate", "create"
- stem: the question text
- options: array of 4 strings for MCQ, ["True","False"] for true_false, null for short_answer
- answer: correct answer string (must be one of the options for MCQ/TF)
- explanation: explanation of why the answer is correct
- source_snippet: relevant excerpt from source text (optional)

Make questions educational, accurate, and varied."""

    def _parse_response(self, data: dict) -> List[QuestionData]:
        questions = []
        items = data.get("questions", [])
        for item in items:
            try:
                q = QuestionData(
                    type=item.get("type", "mcq"),
                    difficulty=item.get("difficulty", "medium"),
                    bloom=item.get("bloom", "remember"),
                    stem=item.get("stem", ""),
                    options=item.get("options"),
                    answer=item.get("answer", ""),
                    explanation=item.get("explanation", ""),
                    source_snippet=item.get("source_snippet"),
                )
                questions.append(q)
            except Exception:
                continue
        return questions

    def _fallback(self, topic, keywords, source, count, difficulty):
        from app.llm.mock import MockProvider
        return MockProvider().generate_questions(topic, keywords, source, count, difficulty)
