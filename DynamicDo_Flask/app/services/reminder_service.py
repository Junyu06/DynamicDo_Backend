from __future__ import annotations
from typing import Any
from datetime import datetime
from app.database.mongo import reminders_collection
from bson import ObjectId


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
    
    def delete_reminders(self, user_id: str, data: list[str]) -> dict[str, Any]:
        """Delete reminder from the users, cap for 10 first

        Args:
            user_id: ID of the user creating the reminder
            data: list of reminder id that is going to delete

        Returns:
            the id of delete reminder, and unable delete reminder

        Raises:
            ValueError: If reminder is missing 
        """
        if not data:
            raise ValueError("No Reminder IDs provided for deletion")
        
        ignored = data[10:] # cap
        ids_to_process = data[:10]

        #mongo db need convert to objectid can be find the id
        #convert to objectid
        valid_ids, invalid_ids = [], []
        for rid in ids_to_process:
            try:
                valid_ids.append(ObjectId(rid))
            except Exception:
                invalid_ids.append(rid)
        
        #find out the reminder that below to user
        existing = list(reminders_collection.find(
            {"_id": {"$in": valid_ids}, "user_id": user_id},# find the all valid in db
            {"_id": 1} #only want the id to return 
        ))
        found_ids = [str(r["_id"]) for r in existing] # have to convert from objectid to str

        #delete reminder
        reminders_collection.delete_many({"_id": {"$in": [r["_id"] for r in existing]}})
        not_found = [rid for rid in ids_to_process if rid not in found_ids]

        return{
            "deleted": found_ids,
            "not_found": not_found + invalid_ids,
            "ignored": ignored
        }

