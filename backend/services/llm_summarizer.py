"""
LLM-Powered Idea Summarizer using OpenAI API.

Generates rich scholarly descriptions for ideas based on their
title, category, stage, and keywords using OpenAI GPT models.
"""

import os
import requests as http_requests
from typing import Dict, Any, Optional

from backend.models import EvolutionStage
from backend.services.data_store import DataStore


# Stage descriptions for prompt context
_STAGE_DESCRIPTIONS = {
    EvolutionStage.PHILOSOPHY: "an early philosophical or theoretical concept",
    EvolutionStage.SCIENTIFIC_VALIDATION: "a scientifically validated theory with experimental evidence",
    EvolutionStage.ENGINEERING_APPLICATION: "an engineering application with practical implementations",
    EvolutionStage.MODERN_TECHNOLOGY: "a modern technology in active use today",
}


class LLMSummarizerService:
    """
    Service that uses the OpenAI API to generate rich, scholarly
    descriptions for ideas based on their metadata.

    Requires the OPENAI_API_KEY environment variable to be set.
    """

    def __init__(self, store: DataStore, model: str = "gpt-3.5-turbo"):
        self._store = store
        self._model = model

    def _call_openai(self, prompt: str) -> str:
        """Call OpenAI chat completions API and return the response text."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY environment variable is not set."
            )

        response = http_requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.7,
                "max_tokens": 500,
            },
            timeout=30,
        )

        if response.status_code != 200:
            raise RuntimeError(
                f"OpenAI API error {response.status_code}: {response.text[:200]}"
            )

        return response.json()["choices"][0]["message"]["content"].strip()

    def _build_prompt(self, title: str, category: str, stage: EvolutionStage,
                      keywords: list, start_year: int) -> str:
        """Build a structured prompt for OpenAI."""
        stage_desc = _STAGE_DESCRIPTIONS.get(stage, "a concept in development")
        keywords_str = ", ".join(keywords) if keywords else "not specified"

        return f"""You are a scholarly research assistant. Generate a concise, informative description 
(3-5 sentences) for the following academic/scientific idea. The description should explain what 
the idea is, its significance, and its impact on the field.

Title: {title}
Category: {category}
Evolution Stage: {stage_desc}
Year: {start_year}
Keywords: {keywords_str}

Requirements:
- Write in an academic but accessible tone
- Mention the historical context and significance
- Reference the key contributors or field if relevant
- Keep it between 50-120 words
- Do NOT use markdown formatting, just plain text

Description:"""

    def summarize_idea(self, idea_id: str) -> Dict[str, Any]:
        """
        Generate an AI description for a single idea, update it in the
        DataStore, and return the result.

        Args:
            idea_id: The ID of the idea to summarize

        Returns:
            Dict with id, title, description (generated), and model info
        """
        idea = self._store.get_idea(idea_id)
        if idea is None:
            raise ValueError(f"Idea '{idea_id}' not found")

        prompt = self._build_prompt(
            title=idea.title,
            category=idea.category,
            stage=idea.stage,
            keywords=idea.keywords,
            start_year=idea.start_year,
        )

        try:
            generated_text = self._call_openai(prompt)
        except Exception as exc:
            raise RuntimeError(f"OpenAI API error: {exc}") from exc

        # Update the idea's description in the store
        idea.description = generated_text
        from datetime import datetime
        idea.updated_at = datetime.now()
        self._store._ideas[idea.id] = idea
        self._store._save_data()

        return {
            "id": idea.id,
            "title": idea.title,
            "description": generated_text,
            "model": self._model,
            "status": "generated",
        }

    def summarize_batch(self, idea_ids: list, max_count: int = 10) -> Dict[str, Any]:
        """
        Generate AI descriptions for multiple ideas.

        Args:
            idea_ids: List of idea IDs to summarize (max 10)
            max_count: Maximum number of ideas to process

        Returns:
            Dict with results list and summary stats
        """
        ids_to_process = idea_ids[:max_count]
        results = []
        errors = []

        for idea_id in ids_to_process:
            try:
                result = self.summarize_idea(idea_id)
                results.append(result)
            except Exception as exc:
                errors.append({"id": idea_id, "error": str(exc)})

        return {
            "processed": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors,
        }

    def is_configured(self) -> bool:
        """Check if the OpenAI API key is configured."""
        return bool(os.environ.get("OPENAI_API_KEY"))
