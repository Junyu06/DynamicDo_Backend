from __future__ import annotations

import os
import json
from typing import Any
from openai import OpenAI


class AiClient:
    """Client for AI-powered reminder ranking using OpenAI's ChatGPT API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("CHATGPT_TOKEN", "")

        if not self.api_key:
            raise ValueError("CHATGPT_TOKEN environment variable is not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Cost-effective model for ranking

    @classmethod
    def from_env(cls) -> "AiClient":
        """Create an AiClient instance using environment variables."""
        return cls()

    def rank_reminders(
        self,
        reminders: list[dict[str, Any]],
        context: str = ""
    ) -> list[dict[str, Any]]:
        """
        Rank a list of reminders by priority using AI.

        Args:
            reminders: List of reminder objects with at least a 'title' or 'content' field
            context: Optional context about the user's current goals or situation

        Returns:
            List of reminders with added 'rank', 'priority', and 'reasoning' fields,
            sorted by importance (highest rank first)
        """
        if not reminders:
            return []

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            # Prepare the prompt
            reminders_text = json.dumps(reminders, indent=2, ensure_ascii=False)

            system_prompt = """You are an AI assistant that helps prioritize reminders and tasks.
Analyze the given reminders and rank them based on:
1. Urgency (time-sensitive tasks)
2. Importance (impact on goals)
3. Dependencies (tasks that block others)
4. Effort required (quick wins vs. long tasks)

Return a JSON array with each reminder enhanced with:
- rank: float from 0.0 to 1.0 (1.0 = highest priority)
- priority: "high", "medium", or "low"
- reasoning: brief explanation of the ranking

Sort the results from highest to lowest rank."""

            user_prompt = f"""Here are the reminders to rank:

{reminders_text}"""

            if context:
                user_prompt += f"\n\nUser context: {context}"

            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,  # Lower temperature for more consistent ranking
                response_format={"type": "json_object"}
            )

            # Parse response
            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from OpenAI")

            result = json.loads(result_text)

            # Handle both array and object responses
            ranked_reminders = result if isinstance(result, list) else result.get("reminders", [])

            return ranked_reminders

        except Exception as e:
            # Log error and return original reminders with default ranking
            print(f"Error ranking reminders with AI: {e}")
            # Fallback: return reminders with default rank
            return [
                {**reminder, "rank": 0.5, "priority": "medium", "reasoning": "AI ranking unavailable"}
                for reminder in reminders
            ]

    def extract_tasks(self, text: str) -> list[dict[str, Any]]:
        """
        Extract tasks from natural language text using AI.

        Args:
            text: Natural language text containing potential tasks

        Returns:
            List of extracted task objects
        """
        if not text.strip():
            return []

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        try:
            system_prompt = """You are an AI assistant that extracts actionable tasks from text.
Extract all tasks, reminders, or action items from the given text.

Return a JSON array where each task has:
- title: concise task description
- priority: "high", "medium", or "low"
- due_date: null or suggested date (ISO format) if mentioned
- rank: float from 0.0 to 1.0 based on implied urgency"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            if not result_text:
                raise ValueError("Empty response from OpenAI")

            result = json.loads(result_text)
            tasks = result if isinstance(result, list) else result.get("tasks", [])

            return tasks

        except Exception as e:
            print(f"Error extracting tasks with AI: {e}")
            # Fallback: simple sentence splitting
            sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
            return [
                {
                    "title": sentence[:100],
                    "priority": "medium",
                    "due_date": None,
                    "rank": 0.5,
                }
                for sentence in sentences[:10]  # Limit to 10 tasks
            ]
