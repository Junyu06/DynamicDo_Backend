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

        now = datetime.utcnow()
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
            "completed": False,
            "created_at": now,
            "updated_at": now
        }

        result = reminders_collection.insert_one(reminder)
        reminder["id"] = str(result.inserted_id)
        del reminder["_id"]  # Remove ObjectId, use string id instead

        return reminder

    def list_reminders(self, user_id: str) -> list[dict[str, Any]]:
        """Get all reminders for a user, sorted by rank and completion status.

        Args:
            user_id: ID of the user

        Returns:
            List of reminders for the user (with id field), sorted by:
            1. Completed status (uncompleted first)
            2. Rank (highest first, if present)
        """
        reminders = list(reminders_collection.find({"user_id": user_id}))

        # Convert ObjectId to string id field for JSON serialization
        for reminder in reminders:
            reminder["id"] = str(reminder["_id"])
            del reminder["_id"]

        # Sort reminders: uncompleted first, then by rank (highest first)
        reminders.sort(key=lambda r: (
            r.get("completed", False),  # False (uncompleted) comes before True
            -r.get("rank", -1)  # Higher ranks first, items without rank go to end
        ))

        return reminders

    def list_uncompleted_reminders(self, user_id: str) -> list[dict[str, Any]]:
        """Get only uncompleted reminders for a user (more efficient for AI ranking).

        Args:
            user_id: ID of the user

        Returns:
            List of uncompleted reminders (completed=False) with id field
        """
        # Query MongoDB directly for uncompleted reminders only
        reminders = list(reminders_collection.find({
            "user_id": user_id,
            "completed": False
        }))

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

    def update_reminder(self, user_id: str, reminder_id: str, data: dict[str, Any]) -> dict[str, Any]:
        """Update an existing reminder.

        Args:
            user_id: ID of the user who owns the reminder
            reminder_id: ID of the reminder to update
            data: Fields to update (title, notes, url, date, time, priority, list, tag)

        Returns:
            Updated reminder with id field

        Raises:
            ValueError: If reminder_id is invalid or reminder not found
        """
        # Convert reminder_id to ObjectId
        try:
            obj_id = ObjectId(reminder_id)
        except Exception:
            raise ValueError("Invalid reminder ID")

        # Build update document with only provided fields
        update_fields = {}
        allowed_fields = ["title", "notes", "url", "date", "time", "priority", "list", "tag"]

        for field in allowed_fields:
            if field in data:
                if field == "title":
                    # Validate title is not empty
                    title = data["title"].strip() if data["title"] else ""
                    if not title:
                        raise ValueError("Reminder title cannot be empty")
                    update_fields["title"] = title
                else:
                    update_fields[field] = data[field]

        if not update_fields:
            raise ValueError("No valid fields to update")

        # Always update the updated_at timestamp
        update_fields["updated_at"] = datetime.utcnow()

        # Update the reminder
        result = reminders_collection.find_one_and_update(
            {"_id": obj_id, "user_id": user_id},
            {"$set": update_fields},
            return_document=True
        )

        if not result:
            raise ValueError("Reminder not found or does not belong to user")

        # Convert ObjectId to string id for response
        result["id"] = str(result["_id"])
        del result["_id"]

        return result

    def toggle_reminder_completion(self, user_id: str, data: list[str], completed: bool) -> dict[str, Any]:
        """Toggle the completion status of reminders, cap for 10 first.

        Args:
            user_id: ID of the user who owns the reminders
            data: list of reminder IDs to toggle
            completed: True to mark as completed, False to mark as not completed

        Returns:
            Dictionary with updated, not_found, and ignored reminder IDs

        Raises:
            ValueError: If reminder list is empty
        """
        if not data:
            raise ValueError("No Reminder IDs provided")

        ignored = data[10:]  # cap
        ids_to_process = data[:10]

        # Convert to ObjectId
        valid_ids, invalid_ids = [], []
        for rid in ids_to_process:
            try:
                valid_ids.append(ObjectId(rid))
            except Exception:
                invalid_ids.append(rid)

        # Find reminders that belong to user
        existing = list(reminders_collection.find(
            {"_id": {"$in": valid_ids}, "user_id": user_id},
            {"_id": 1}
        ))
        found_ids = [str(r["_id"]) for r in existing]

        # Update completion status for all found reminders
        if existing:
            reminders_collection.update_many(
                {"_id": {"$in": [r["_id"] for r in existing]}},
                {"$set": {"completed": completed, "updated_at": datetime.utcnow()}}
            )

        not_found = [rid for rid in ids_to_process if rid not in found_ids]

        return {
            "updated": found_ids,
            "not_found": not_found + invalid_ids,
            "ignored": ignored
        }

    def get_reminder_by_id(self, user_id: str, reminder_id: str) -> dict[str, Any]:
        """Get a single reminder by ID.

        Args:
            user_id: ID of the user who owns the reminder
            reminder_id: ID of the reminder to retrieve

        Returns:
            Reminder with id field

        Raises:
            ValueError: If reminder_id is invalid or reminder not found
        """
        # Convert reminder_id to ObjectId
        try:
            obj_id = ObjectId(reminder_id)
        except Exception:
            raise ValueError("Invalid reminder ID")

        # Find the reminder
        reminder = reminders_collection.find_one(
            {"_id": obj_id, "user_id": user_id}
        )

        if not reminder:
            raise ValueError("Reminder not found or does not belong to user")

        # Convert ObjectId to string id for response
        reminder["id"] = str(reminder["_id"])
        del reminder["_id"]

        return reminder

    def save_ranking_results(self, user_id: str, ranked_reminders: list[dict[str, Any]]) -> dict[str, Any]:
        """Save AI ranking results to database in bulk.

        Args:
            user_id: ID of the user who owns the reminders
            ranked_reminders: List of reminders with rank and ai_priority fields

        Returns:
            Dictionary with count of updated reminders

        Raises:
            ValueError: If ranked_reminders is empty or invalid
        """
        if not ranked_reminders:
            raise ValueError("No ranked reminders to save")

        updated_count = 0
        errors = []

        for reminder in ranked_reminders:
            try:
                reminder_id = reminder.get("id")
                rank = reminder.get("rank")
                ai_priority = reminder.get("ai_priority")

                if not reminder_id or rank is None:
                    continue

                obj_id = ObjectId(reminder_id)

                # Update rank and ai_priority fields
                result = reminders_collection.update_one(
                    {"_id": obj_id, "user_id": user_id},
                    {
                        "$set": {
                            "rank": rank,
                            "ai_priority": ai_priority,
                            "updated_at": datetime.utcnow()
                        }
                    }
                )

                if result.modified_count > 0:
                    updated_count += 1

            except Exception as e:
                errors.append({"id": reminder.get("id"), "error": str(e)})

        return {
            "updated": updated_count,
            "errors": errors
        }

