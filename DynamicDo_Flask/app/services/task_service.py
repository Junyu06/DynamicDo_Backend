from __future__ import annotations

from typing import Any

from .ai_client import AiClient


class TaskService:
    def __init__(self, ai_client: AiClient | None = None) -> None:
        self.ai_client = ai_client or AiClient.from_env()

    def list_tasks(self) -> list[dict[str, Any]]:
        # TODO: Replace with DB fetch once Mongo is wired up
        return []

    def create_task(self, data: dict[str, Any]) -> dict[str, Any]:
        # TODO: Save to Mongo once connector added
        return {"id": "temp", **data}

    def suggest_tasks_from_text(self, text: str) -> list[dict[str, Any]]:
        """Extract tasks from natural language text using AI."""
        if not text:
            return []
        return self.ai_client.extract_tasks(text)

    def rank_tasks(
        self,
        tasks: list[dict[str, Any]],
        context: str = ""
    ) -> list[dict[str, Any]]:
        """Rank a list of tasks/reminders by priority using AI."""
        if not tasks:
            return []
        return self.ai_client.rank_reminders(tasks, context)


