from flask import Blueprint, request, jsonify
from app.services.reminder_service import ReminderService
from app.services.user_service import UserService

reminder_bp = Blueprint("reminders", __name__)
reminder_service = ReminderService()
user_service = UserService()


@reminder_bp.post("/")
def create_reminder():
    """Create a new reminder for the authenticated user."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return jsonify({"error": "Invalid or expired token"}), 401

    user_id = decoded["user_id"]

    # Get reminder data from request
    data = request.get_json(silent=True) or {}

    try:
        reminder = reminder_service.create_reminder(user_id, data)
        return jsonify(reminder), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@reminder_bp.get("/")
def list_reminders():
    """Get all reminders for the authenticated user."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return jsonify({"error": "Invalid or expired token"}), 401

    user_id = decoded["user_id"]

    # Get reminders for the user
    reminders = reminder_service.list_reminders(user_id)
    return jsonify({"reminders": reminders})

@reminder_bp.post("/delete")
def delete_reminder():
    """delete reminder."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return jsonify({"error": "Invalid or expired token"}), 401

    user_id = decoded["user_id"]

    # Get reminder data from request
    data = request.get_json(silent=True) or {}

    try:
        reminder = reminder_service.delete_reminders(user_id, data)
        return jsonify(reminder), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 400