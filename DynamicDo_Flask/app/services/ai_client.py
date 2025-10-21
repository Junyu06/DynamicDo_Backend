from __future__ import annotations

import os
import json
from typing import Any
from openai import OpenAI
from datetime import datetime

class AiClient:
    """Client for AI-powered reminder ranking using OpenAI's ChatGPT API."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")

        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        self.client = OpenAI(api_key=self.api_key)
        self.model = "gpt-4o-mini"  # Cost-effective model for ranking

    @classmethod
    def from_env(cls) -> "AiClient":
        """Create an AiClient instance using environment variables."""
        return cls()

    def rank_tasks(
        self,
        tasks: list[dict[str, Any]],
        context: str = "",
        debug: bool = False
    ) -> list[dict[str, Any]]:
        """
        Rank tasks using AI based on urgency, importance, dependencies, and effort.

        Args:
            tasks: List of task/reminder objects to rank
            context: Optional user context (e.g., "Focus on work tasks", "Preparing for vacation")
            debug: If True, include reasoning in response (uses more tokens)

        Returns:
            List of tasks sorted by priority (highest first), with added fields:
            - rank: float from 0.0 to 1.0 (1.0 = highest priority)
            - priority: "high", "medium", or "low"
            - reasoning: (only if debug=True) brief explanation of the ranking
        """
        if not tasks:
            return []

        if not self.client:
            raise RuntimeError("OpenAI client not initialized")

        # Extract only relevant fields for AI (save tokens)
        # Send: id, title, date, time, priority, tag, list, notes
        simplified_tasks = []
        for task in tasks:
            simplified = {
                "id": task.get("id"),
                "title": task.get("title"),
                "date": task.get("date"),
                "time": task.get("time"),
                "priority": task.get("priority"),
                "tag": task.get("tag"),
                "list": task.get("list"),
                "notes": task.get("notes")
            }
            # Remove None values to save tokens
            simplified = {k: v for k, v in simplified.items() if v is not None}
            simplified_tasks.append(simplified)

        # Build system prompt based on debug mode
        reasoning_instruction = """- reasoning: brief explanation (1-2 sentences)""" if debug else ""
        reasoning_example = """, "reasoning": "brief explanation" """ if debug else ""

        system_prompt = f"""You are an AI assistant that helps prioritize tasks and reminders.
Analyze the given tasks and rank them based on:
1. Urgency (date/time - approaching deadlines are more urgent)
2. Importance (priority field, tag, list context)
3. Impact on goals
4. Effort vs value

Return a JSON object with this exact structure:
{{
  "tasks": [
    {{
      "id": "task_id",
      "rank": 0.95,
      "priority": "high"{reasoning_example}
    }}
  ]
}}

Requirements:
- rank: float from 0.0 to 1.0 (1.0 = highest priority)
- priority: must be "high", "medium", or "low"
{reasoning_instruction}
- Sort tasks from highest to lowest rank
- ONLY return id, rank, priority{', reasoning' if debug else ''} fields (save tokens)"""
        nowtime = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        ##user_prompt = f"Here are the tasks to rank:\n\n{json.dumps(simplified_tasks, indent=2, ensure_ascii=False)}"
        user_prompt = f"""
The current date and time is {nowtime}.
Rank the following tasks accordingly.
If a task's date/time is in the past relative to now, consider it overdue or lower priority unless critical.
Tasks:
{json.dumps(simplified_tasks, indent=2, ensure_ascii=False)}
"""
        
        if context:
            user_prompt += f"\n\nUser context: {context}"

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.3  # Lower temperature for more consistent ranking
            )

            content = response.choices[0].message.content

            if not content:
                raise ValueError("Empty response from OpenAI")

            # Parse JSON response
            result = json.loads(content)

            # Handle both formats: {"tasks": [...]} or direct array
            ai_ranked = result.get("tasks", result if isinstance(result, list) else [])

            # Merge AI results back with original task data
            # Create a lookup map by id
            ai_map = {item["id"]: item for item in ai_ranked if "id" in item}

            # Build final result maintaining original task data + AI fields
            final_tasks = []
            for task in tasks:
                task_id = task.get("id")
                if task_id in ai_map:
                    ai_data = ai_map[task_id]
                    final_task = {
                        **task,  # All original fields
                        "rank": ai_data.get("rank", 0.5),
                        "priority": ai_data.get("priority", "medium")
                    }
                    if debug and "reasoning" in ai_data:
                        final_task["reasoning"] = ai_data["reasoning"]
                    final_tasks.append(final_task)
                else:
                    # Task not in AI response, add default
                    final_tasks.append({
                        **task,
                        "rank": 0.5,
                        "priority": "medium"
                    })

            # Sort by rank descending
            final_tasks.sort(key=lambda x: x.get("rank", 0), reverse=True)

            return final_tasks

        except Exception as e:
            # Fallback: return original tasks with default ranking
            print(f"Error ranking tasks with AI: {e}")
            fallback = [
                {**task, "rank": 0.5, "priority": "medium"}
                for task in tasks
            ]
            if debug:
                for task in fallback:
                    task["reasoning"] = "AI ranking unavailable"
            return fallback
