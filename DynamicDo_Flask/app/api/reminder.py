from flask import Blueprint, request, jsonify
from app.services.reminder_service import ReminderService
from app.services.user_service import UserService
from app.services.ai_client import AiClient

reminder_bp = Blueprint("reminders", __name__)
reminder_service = ReminderService()
user_service = UserService()
ai_client = AiClient.from_env()


def error_response(message: str, status_code: int):
    """Create a standardized error response with both error and detail fields."""
    return jsonify({"error": message, "detail": message}), status_code


@reminder_bp.post("/")
def create_reminder():
    """Create a new reminder for the authenticated user."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get reminder data from request
    data = request.get_json(silent=True) or {}

    try:
        reminder = reminder_service.create_reminder(user_id, data)
        return jsonify(reminder), 201
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.get("/")
def list_reminders():
    """Get all reminders for the authenticated user."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

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
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get reminder data from request
    data = request.get_json(silent=True) or {}

    try:
        reminder = reminder_service.delete_reminders(user_id, data)
        return jsonify(reminder), 201
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.route("/<reminder_id>", methods=["PATCH"])
def update_reminder(reminder_id):
    """Update an existing reminder."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get update data from request
    data = request.get_json(silent=True) or {}

    try:
        reminder = reminder_service.update_reminder(user_id, reminder_id, data)
        return jsonify(reminder), 200
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.post("/complete")
def complete_reminders():
    """Mark reminders as completed (batch operation, cap 10)."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get reminder IDs from request body
    data = request.get_json(silent=True) or {}

    try:
        result = reminder_service.toggle_reminder_completion(user_id, data, True)
        return jsonify(result), 200
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.post("/uncomplete")
def uncomplete_reminders():
    """Mark reminders as not completed (batch operation, cap 10)."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get reminder IDs from request body
    data = request.get_json(silent=True) or {}

    try:
        result = reminder_service.toggle_reminder_completion(user_id, data, False)
        return jsonify(result), 200
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.get("/<reminder_id>")
def get_reminder(reminder_id):
    """Get a single reminder by ID."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    try:
        reminder = reminder_service.get_reminder_by_id(user_id, reminder_id)
        return jsonify(reminder), 200
    except ValueError as e:
        return error_response(str(e), 400)


@reminder_bp.post("/rank")
def rank_reminders():
    """Use AI to rank and prioritize user's uncompleted reminders based on urgency and importance."""
    # Extract token from Authorization header
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")

    # Verify token and get user_id
    decoded = user_service.verify_token(token)
    if not decoded:
        return error_response("Invalid or expired token", 401)

    user_id = decoded["user_id"]

    # Get optional parameters from request body
    data = request.get_json(silent=True) or {}
    context = data.get("context", "")
    debug = data.get("debug", False)  # Include reasoning if debug=True

    try:
        # Get only uncompleted reminders (more efficient - MongoDB query filters directly)
        uncompleted_reminders = reminder_service.list_uncompleted_reminders(user_id)

        if not uncompleted_reminders:
            return jsonify({
                "reminders": [],
                "count": 0,
                "message": "No uncompleted reminders to rank"
            }), 200

        # Use AI to rank uncompleted reminders
        # debug=True includes reasoning (uses more tokens), debug=False saves tokens
        ranked_reminders = ai_client.rank_tasks(uncompleted_reminders, context, debug)

        # Save ranking results to database for persistence
        save_result = reminder_service.save_ranking_results(user_id, ranked_reminders)

        return jsonify({
            "reminders": ranked_reminders,
            "count": len(ranked_reminders),
            "saved": save_result["updated"]
        }), 200

    except Exception as e:
        return error_response(f"Failed to rank reminders: {str(e)}", 500)