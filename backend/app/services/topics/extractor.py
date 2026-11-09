"""
Topic extractor with three-tier fallback:
1. Heading-based extraction (primary)
2. TF-IDF + KMeans clustering (secondary)
3. Paragraph-based fallback (tertiary)
"""
from dataclasses import dataclass, field
from typing import List, Optional
import logging
import re

from app.services.parsing.parser import ParsedDocument, Section

logger = logging.getLogger(__name__)


@dataclass
class ExtractedTopic:
    """Represents an extracted topic."""
    name: str
    keywords: List[str] = field(default_factory=list)
    summary: str = ""
    source_text: str = ""
    parent_name: Optional[str] = None
    level: int = 1
    difficulty_prior: float = 0.5


def extract_topics(parsed_doc: ParsedDocument) -> List[ExtractedTopic]:
    """
    Extract topics from a parsed document using a tiered approach.

    Tier 1: Heading-based extraction
    Tier 2: TF-IDF + KMeans if insufficient headings
    Tier 3: Paragraph-based fallback

    Args:
        parsed_doc: Result from parse_document().

    Returns:
        List of ExtractedTopic objects.
    """
    # Tier 1: Heading-based extraction
    if parsed_doc.sections and len(parsed_doc.sections) >= 3:
        topics = _heading_based_extraction(parsed_doc.sections)
        if topics:
            logger.info(f"Extracted {len(topics)} topics via headings")
            return topics

    # Tier 2: TF-IDF + KMeans
    if parsed_doc.raw_text and len(parsed_doc.raw_text) > 500:
        topics = _tfidf_kmeans_extraction(parsed_doc.raw_text)
        if topics:
            logger.info(f"Extracted {len(topics)} topics via TF-IDF+KMeans")
            return topics

    # Tier 3: Paragraph-based fallback
    topics = _paragraph_fallback(parsed_doc.raw_text)
    logger.info(f"Extracted {len(topics)} topics via paragraph fallback")
    return topics


def _heading_based_extraction(sections: List[Section]) -> List[ExtractedTopic]:
    """Extract topics from document headings."""
    topics = []
    current_parent = None

    for section in sections:
        if not section.title.strip():
            continue

        keywords = _extract_keywords(section.title + " " + section.content)
        summary = _summarize_text(section.content, max_words=50)
        difficulty = _estimate_difficulty(section.content)

        if section.level == 1:
            topic = ExtractedTopic(
                name=section.title,
                keywords=keywords,
                summary=summary,
                source_text=section.content[:1000],
                parent_name=None,
                level=1,
                difficulty_prior=difficulty,
            )
            topics.append(topic)
            current_parent = section.title
        elif section.level >= 2:
            topic = ExtractedTopic(
                name=section.title,
                keywords=keywords,
                summary=summary,
                source_text=section.content[:1000],
                parent_name=current_parent,
                level=section.level,
                difficulty_prior=difficulty,
            )
            topics.append(topic)

    return topics


def _tfidf_kmeans_extraction(text: str, n_clusters: int = 8) -> List[ExtractedTopic]:
    """Use TF-IDF vectorization + KMeans clustering to extract topics."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.cluster import KMeans
        import numpy as np

        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split("\n\n") if len(p.strip()) > 50]
        if len(paragraphs) < n_clusters:
            n_clusters = max(2, len(paragraphs))

        vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words="english",
            ngram_range=(1, 2),
            min_df=1,
        )
        X = vectorizer.fit_transform(paragraphs)

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = kmeans.fit_predict(X)

        feature_names = vectorizer.get_feature_names_out()
        topics = []

        for cluster_id in range(n_clusters):
            cluster_indices = [i for i, l in enumerate(labels) if l == cluster_id]
            if not cluster_indices:
                continue

            # Get top TF-IDF terms for this cluster
            cluster_center = kmeans.cluster_centers_[cluster_id]
            top_indices = cluster_center.argsort()[-5:][::-1]
            top_terms = [feature_names[i] for i in top_indices if cluster_center[i] > 0]

            if not top_terms:
                continue

            # Use the top term as the topic name
            topic_name = _capitalize_topic(" ".join(top_terms[:2]))
            cluster_text = " ".join(paragraphs[i] for i in cluster_indices[:3])

            topics.append(ExtractedTopic(
                name=topic_name,
                keywords=top_terms,
                summary=_summarize_text(cluster_text, max_words=30),
                source_text=cluster_text[:500],
                difficulty_prior=_estimate_difficulty(cluster_text),
            ))

        return topics

    except Exception as e:
        logger.warning(f"TF-IDF extraction failed: {e}")
        return []


def _paragraph_fallback(text: str, max_topics: int = 10) -> List[ExtractedTopic]:
    """Simple fallback: use first sentence of each substantial paragraph as a topic."""
    paragraphs = [p.strip() for p in text.split("\n") if len(p.strip()) > 80]
    topics = []

    for i, para in enumerate(paragraphs[:max_topics]):
        sentences = re.split(r'[.!?]', para)
        first_sentence = sentences[0].strip() if sentences else para[:80]
        topic_name = _capitalize_topic(first_sentence[:60])
        keywords = _extract_keywords(para)

        topics.append(ExtractedTopic(
            name=topic_name,
            keywords=keywords[:5],
            summary=_summarize_text(para, max_words=30),
            source_text=para[:500],
            difficulty_prior=0.5,
        ))

    return topics


def _extract_keywords(text: str, max_keywords: int = 8) -> List[str]:
    """Extract keywords from text using simple frequency analysis."""
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        vectorizer = TfidfVectorizer(
            max_features=max_keywords,
            stop_words="english",
            ngram_range=(1, 2),
        )
        vectorizer.fit([text])
        return list(vectorizer.get_feature_names_out())
    except Exception:
        # Simple fallback: extract nouns/content words
        words = re.findall(r'\b[A-Za-z]{4,}\b', text)
        stopwords = {
            "this", "that", "with", "from", "have", "been", "will",
            "also", "more", "than", "such", "each", "they", "their",
        }
        freq = {}
        for w in words:
            w_lower = w.lower()
            if w_lower not in stopwords:
                freq[w_lower] = freq.get(w_lower, 0) + 1
        sorted_words = sorted(freq.items(), key=lambda x: x[1], reverse=True)
        return [w for w, _ in sorted_words[:max_keywords]]


def _summarize_text(text: str, max_words: int = 50) -> str:
    """Return the first max_words words of text as a summary."""
    words = text.split()
    if len(words) <= max_words:
        return text.strip()
    return " ".join(words[:max_words]) + "..."


def _estimate_difficulty(text: str) -> float:
    """Estimate difficulty [0,1] based on text complexity."""
    if not text:
        return 0.5
    words = text.split()
    avg_word_len = sum(len(w) for w in words) / max(len(words), 1)
    sentences = re.split(r'[.!?]', text)
    avg_sent_len = len(words) / max(len(sentences), 1)
    # Normalize to [0, 1]
    difficulty = min(1.0, (avg_word_len / 10 + avg_sent_len / 30) / 2)
    return round(difficulty, 2)


def _capitalize_topic(text: str) -> str:
    """Capitalize a topic name properly."""
    if not text:
        return "Unknown Topic"
    # Title case, but preserve acronyms
    words = text.split()
    result = []
    for w in words:
        if w.isupper() and len(w) > 1:
            result.append(w)  # Preserve acronyms
        else:
            result.append(w.capitalize())
    return " ".join(result)
