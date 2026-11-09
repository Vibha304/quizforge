"""Anthropic Claude LLM provider."""
import json
import time
import logging
from typing import List
from app.llm.base import LLMProvider, QuestionData
from app.config import settings

logger = logging.getLogger(__name__)


class AnthropicProvider(LLMProvider):
    """LLM provider using Anthropic's Claude API."""

    MODEL = "claude-3-haiku-20240307"
    MAX_RETRIES = 2
    RETRY_DELAY = 2.0

    def __init__(self):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic: {e}")
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
                response = self.client.messages.create(
                    model=self.MODEL,
                    max_tokens=4096,
                    messages=[{"role": "user", "content": prompt}],
                    system="You are an expert educational content creator. Always respond with valid JSON only.",
                )
                content = response.content[0].text
                # Extract JSON if wrapped in markdown
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                data = json.loads(content)
                questions = self._parse_response(data)
                valid = [q for q in questions if self._validate_question(q)]
                if valid:
                    return valid[:count]
            except Exception as e:
                logger.warning(f"Anthropic attempt {attempt + 1} failed: {e}")
                if attempt < self.MAX_RETRIES:
                    time.sleep(self.RETRY_DELAY * (attempt + 1))
        return self._fallback(topic_name, topic_keywords, source_text, count, difficulty)

    def _build_prompt(self, topic, keywords, source, count, difficulty):
        kw_str = ", ".join(keywords) if keywords else topic
        source_excerpt = source[:1500] if len(source) > 1500 else source
        return f"""Generate {count} quiz questions about "{topic}" (keywords: {kw_str}).
Difficulty: {difficulty}. Source: {source_excerpt}

Return JSON: {{"questions": [{{type, difficulty, bloom, stem, options, answer, explanation}}]}}
Types: mcq (4 options), true_false (True/False options), short_answer (null options)
Bloom: remember/understand/apply/analyze/evaluate/create"""

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
