"""
NLP Extractor Service for the Theory-to-Reality Evolution Tracker.

Provides automatic keyword extraction from idea descriptions using TF-IDF,
named entity recognition for laureate/topic discovery, and heuristic
stage classification from text content.
"""

import re
from typing import List, Dict, Any, Optional

from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

from backend.models import EvolutionStage
from backend.services.data_store import DataStore


# Stage-indicative keyword groups for classification heuristic
_STAGE_KEYWORDS = {
    EvolutionStage.PHILOSOPHY: {
        "theory", "concept", "philosophy", "hypothesis", "thought",
        "principle", "postulate", "conjecture", "abstract", "foundation",
        "fundamental", "idea", "framework", "model", "metaphysics",
    },
    EvolutionStage.SCIENTIFIC_VALIDATION: {
        "experiment", "validation", "proof", "evidence", "measurement",
        "observation", "confirmed", "demonstrated", "discovery", "test",
        "laboratory", "empirical", "verified", "data", "result",
    },
    EvolutionStage.ENGINEERING_APPLICATION: {
        "engineering", "application", "implementation", "design", "build",
        "prototype", "mechanism", "device", "system", "applied",
        "practical", "construction", "patent", "invention", "technique",
    },
    EvolutionStage.MODERN_TECHNOLOGY: {
        "technology", "modern", "commercial", "product", "industry",
        "production", "market", "global", "widespread", "digital",
        "platform", "infrastructure", "deployment", "scale", "AI",
    },
}

# Common stop-words to filter from keywords
_STOP_WORDS = {
    "the", "a", "an", "is", "are", "was", "were", "be", "been", "being",
    "have", "has", "had", "do", "does", "did", "will", "would", "could",
    "should", "may", "might", "can", "shall", "to", "of", "in", "for",
    "on", "with", "at", "by", "from", "as", "into", "through", "during",
    "before", "after", "above", "below", "between", "and", "but", "or",
    "not", "no", "nor", "so", "yet", "both", "either", "neither", "each",
    "every", "all", "any", "few", "more", "most", "other", "some", "such",
    "than", "too", "very", "just", "also", "this", "that", "these", "those",
    "it", "its", "new", "first", "used",
}


class NLPExtractorService:
    """
    Provides NLP-based analysis for idea text content.

    Features:
    - Auto-extract top keywords using TF-IDF
    - Detect named entities (proper nouns as potential laureates/topics)
    - Classify evolution stage from text
    """

    def __init__(self, store: DataStore):
        self._store = store

    # ------------------------------------------------------------------
    # 1. Keyword Extraction (TF-IDF)
    # ------------------------------------------------------------------

    def extract_keywords(
        self, text: str, top_n: int = 8
    ) -> List[Dict[str, Any]]:
        """
        Extract top-N keywords from a text using TF-IDF against the
        full idea corpus as background.

        Returns list of {keyword, tfidf_score}.
        """
        # Build background corpus from all ideas
        ideas = self._store.get_all_ideas()
        corpus = [
            f"{idea.title} {idea.description} {' '.join(idea.keywords)}"
            for idea in ideas
        ]
        # Add the query text as the last document
        corpus.append(text)

        vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=500,
            ngram_range=(1, 2),
        )
        tfidf_matrix = vectorizer.fit_transform(corpus)
        feature_names = vectorizer.get_feature_names_out()

        # Get scores for the query document (last row)
        query_scores = tfidf_matrix[-1].toarray().flatten()
        top_indices = query_scores.argsort()[::-1][:top_n]

        results = []
        for idx in top_indices:
            score = float(query_scores[idx])
            if score > 0:
                results.append({
                    "keyword": feature_names[idx],
                    "tfidf_score": round(score, 4),
                })
        return results

    def extract_keywords_for_idea(
        self, idea_id: str, top_n: int = 8
    ) -> List[Dict[str, Any]]:
        """Extract keywords for a specific idea by ID."""
        idea = self._store.get_idea(idea_id)
        if idea is None:
            raise ValueError(f"Idea '{idea_id}' not found")
        text = f"{idea.title} {idea.description} {idea.motivation}"
        return self.extract_keywords(text, top_n)

    # ------------------------------------------------------------------
    # 2. Named Entity Recognition (heuristic)
    # ------------------------------------------------------------------

    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        Extract named entities from text using pattern matching.

        Returns dict with keys: persons, organizations, topics.
        """
        # Find capitalized multi-word sequences (likely proper nouns)
        proper_nouns = re.findall(
            r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text
        )
        # Filter out common sentence starters
        sentence_starters = {"The", "A", "An", "This", "That", "In", "On"}
        proper_nouns = [
            pn for pn in proper_nouns if pn not in sentence_starters
        ]

        # Heuristic classification
        persons = []
        organizations = []
        topics = []

        org_indicators = {"Inc", "Corp", "Lab", "University", "Institute",
                          "NASA", "DARPA", "CERN", "MIT", "IBM", "Google"}

        for pn in proper_nouns:
            if any(ind in pn for ind in org_indicators):
                organizations.append(pn)
            elif len(pn.split()) >= 2:
                persons.append(pn)
            else:
                topics.append(pn)

        return {
            "persons": list(set(persons)),
            "organizations": list(set(organizations)),
            "topics": list(set(topics)),
        }

    # ------------------------------------------------------------------
    # 3. Stage Classification
    # ------------------------------------------------------------------

    def classify_stage(self, text: str) -> Dict[str, Any]:
        """
        Classify the likely evolution stage of an idea from its text.

        Uses keyword overlap scoring against stage-indicative term sets.
        Returns predicted stage + confidence + per-stage scores.
        """
        words = set(re.findall(r'\w+', text.lower()))
        words -= _STOP_WORDS

        scores = {}
        for stage, keywords in _STAGE_KEYWORDS.items():
            overlap = words & keywords
            scores[stage.value] = len(overlap)

        total = sum(scores.values()) or 1
        normalized = {k: round(v / total, 4) for k, v in scores.items()}

        predicted_stage = max(normalized, key=normalized.get)
        confidence = normalized[predicted_stage]

        return {
            "predicted_stage": predicted_stage,
            "confidence": confidence,
            "stage_scores": normalized,
        }

    # ------------------------------------------------------------------
    # 4. Batch Analysis
    # ------------------------------------------------------------------

    def analyze_all_ideas(self) -> List[Dict[str, Any]]:
        """
        Run keyword extraction + stage classification on every idea.
        """
        ideas = self._store.get_all_ideas()
        results = []
        for idea in ideas:
            text = f"{idea.title} {idea.description} {idea.motivation}"
            keywords = self.extract_keywords(text, top_n=5)
            stage_pred = self.classify_stage(text)
            entities = self.extract_entities(
                f"{idea.title} {idea.description}"
            )
            results.append({
                "id": idea.id,
                "title": idea.title,
                "actual_stage": idea.stage.value,
                "extracted_keywords": [k["keyword"] for k in keywords],
                "predicted_stage": stage_pred["predicted_stage"],
                "stage_confidence": stage_pred["confidence"],
                "stage_match": stage_pred["predicted_stage"] == idea.stage.value,
                "entities": entities,
            })
        return results
