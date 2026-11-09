"""OpenAI LLM provider."""
import json
import time
import logging
from typing import List
from app.llm.base import LLMProvider, QuestionData
from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIProvider(LLMProvider):
    """LLM provider using OpenAI's API."""

    MODEL = "gpt-4o-mini"
    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
            self.client = None

    def generate_questions(
        self,
        topic_name: str,
        topic_keywords: List[str],
        source_text: str,
        count: int = 5,
        difficulty: str = "mixed",
    ) -> List[QuestionData]:
        if self.client is None:
            return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

        prompt = self._build_prompt(topic_name, topic_keywords, source_text, count, difficulty)
        for attempt in range(self.MAX_RETRIES + 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.MODEL,
                    messages=[
                        {"role": "system", "content": "You are an expert educational content creator. Always respond with valid JSON."},
                        {"role": "user", "content": prompt},
                    ],
                    response_format={"type": "json_object"},
                    temperature=0.7,
                )
                data = json.loads(response.choices[0].message.content)
                questions = self._parse_response(data)
                valid = [q for q in questions if self._validate_question(q)]
                if valid:
                    return valid[:count]
            except Exception as e:
                logger.warning(f"OpenAI attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
        return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

    def _build_prompt(self, topic, keywords, source, count, difficulty):
        kw_str = ", ".join(keywords) if keywords else topic
        source_excerpt = source[:1500] if len(source) > 1500 else source
        return f"""Generate {count} quiz questions about "{topic}" (keywords: {kw_str}).
Difficulty: {difficulty}. Source: {source_excerpt}

Return JSON: {{"questions": [{{type, difficulty, bloom, stem, options, answer, explanation, source_snippet}}]}}
- type: mcq/true_false/short_answer
- bloom: remember/understand/apply/analyze/evaluate/create
- options: 4 strings for MCQ, ["True","False"] for TF, null for SA"""

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
