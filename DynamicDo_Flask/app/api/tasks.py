from flask import Blueprint, request

from ..services.task_service import TaskService


tasks_bp = Blueprint("tasks", __name__)


@tasks_bp.get("/")
def list_tasks() -> dict:
    # Placeholder response
    tasks = TaskService().list_tasks()
    return {"tasks": tasks}


@tasks_bp.post("/")
def create_task() -> tuple[dict, int]:
    data = request.get_json(silent=True) or {}
    created = TaskService().create_task(data)
    return created, 201


@tasks_bp.post("/suggest")
def suggest_tasks() -> dict:
    payload = request.get_json(silent=True) or {}
    suggestions = TaskService().suggest_tasks_from_text(payload.get("text", ""))
    return {"suggestions": suggestions}


@tasks_bp.post("/rank")
def rank_tasks() -> dict:
    payload = request.get_json(silent=True) or {}
    tasks = payload.get("tasks", [])
    context = payload.get("context", "")

    if not tasks:
        return {"error": "No tasks provided"}, 400

    ranked = TaskService().rank_tasks(tasks, context)
    return {"ranked_tasks": ranked}


