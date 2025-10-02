from flask import Blueprint


health_bp = Blueprint("health", __name__)


@health_bp.get("/")
def health() -> dict:
    return {"ok": True}


