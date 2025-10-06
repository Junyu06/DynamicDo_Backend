from __future__ import annotations
from typing import Any
from datetime import datetime
from app.database.mongo import reminders_collection


class ReminderService:
    def create_reminder(self, user_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Create a new reminder for a user.

        Args:
            user_id: ID of the user creating the reminder
            data: Reminder data containing title (required) and optional fields

        Returns:
            Created reminder with id (MongoDB _id converted to string)

        Raises:
            ValueError: If title is missing or empty
        """
        title = data.get("title", "").strip()
        if not title:
            raise ValueError("Reminder title is required")

        reminder = {
            "title": title,
            "notes": data.get("notes"),
            "url": data.get("url"),
            "date": data.get("date"),
            "time": data.get("time"),
            "priority": data.get("priority"),
            "list": data.get("list"),
            "tag": data.get("tag"),
            "user_id": user_id,
            "created_at": datetime.utcnow()
        }

        result = reminders_collection.insert_one(reminder)
        reminder["id"] = str(result.inserted_id)
        del reminder["_id"]  # Remove ObjectId, use string id instead

        return reminder

    def list_reminders(self, user_id: str) -> list[dict[str, Any]]:
        """Get all reminders for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of reminders for the user (with id field)
        """
        reminders = list(reminders_collection.find({"user_id": user_id}))

        # Convert ObjectId to string id field for JSON serialization
        for reminder in reminders:
            reminder["id"] = str(reminder["_id"])
            del reminder["_id"]

        return reminders