from __future__ import annotations

import os
from typing import Any


class AiClient:
    """Abstracts AI provider selection (OpenAI, local LLM, etc.)."""

    def __init__(self, provider: str | None = None, api_key: str | None = None) -> None:
        self.provider = provider or os.getenv("AI_PROVIDER", "local")
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

    @classmethod
    def from_env(cls) -> "AiClient":
        return cls()

    def extract_tasks(self, text: str) -> list[dict[str, Any]]:
        # Placeholder heuristic; replace with real provider calls
        sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
        suggestions: list[dict[str, Any]] = []
        for idx, sentence in enumerate(sentences):
            suggestions.append(
                {
                    "title": sentence[:80],
                    "priority": "medium",
                    "due_date": None,
                    "source": self.provider,
                    "rank": 0.5,
                    "id": f"sugg-{idx}",
                }
            )
        return suggestions


