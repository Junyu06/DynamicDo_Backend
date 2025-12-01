# user verification api

from flask import Blueprint, request, jsonify
from app.services.user_service import UserService

users_bp = Blueprint("users", __name__)
service = UserService()

@users_bp.post("/register")
def register():
    data = request.get_json() or {}
    try:
        user = service.register_user(data["email"], data["password"])
        return jsonify(user), 201
    except ValueError as e:
        return jsonify({"error": str(e), "detail": str(e)}), 400

@users_bp.post("/login")
def login():
    data = request.get_json() or {}
    try:
        token = service.login_user(data["email"], data["password"])
        return jsonify({"token": token, "access_token": token, "token_type": "bearer"})
    except ValueError as e:
        return jsonify({"error": str(e), "detail": str(e)}), 401

@users_bp.get("/me")
def me():
    auth = request.headers.get("Authorization", "")
    token = auth.replace("Bearer ", "")
    decoded = service.verify_token(token)
    if not decoded:
        return jsonify({"error": "Invalid or expired token", "detail": "Invalid or expired token"}), 401
    return jsonify({"user_id": decoded["user_id"], "email": decoded["email"]})