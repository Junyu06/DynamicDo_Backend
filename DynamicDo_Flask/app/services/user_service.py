import os
import bcrypt
import jwt
from datetime import datetime, timedelta
from typing import Optional
from app.database.mongo import users_collection

# Require JWT_SECRET to be set - fail fast if missing
JWT_SECRET = os.getenv("JWT_SECRET")
if not JWT_SECRET:
    raise ValueError("JWT_SECRET environment variable must be set")

JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

class UserService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash password using bcrypt with automatic salt generation."""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    def register_user(self, email: str, password: str) -> dict:
        if users_collection.find_one({"email": email}):
            raise ValueError("User already exists")

        hashed = self.hash_password(password)
        result = users_collection.insert_one({
            "email": email,
            "password": hashed,
            "created_at": datetime.utcnow()
        })

        user_id = str(result.inserted_id)
        return {"user_id": user_id, "email": email}

    def login_user(self, email: str, password: str) -> str:
        user = users_collection.find_one({"email": email})
        if not user:
            raise ValueError("Invalid email or password")

        # Verify password using bcrypt
        if not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
            raise ValueError("Invalid email or password")

        payload = {
            "user_id": str(user["_id"]),
            "email": email,
            "exp": datetime.utcnow() + timedelta(hours=1)  # 1小时过期
        }
        token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
        return token

    def verify_token(self, token: str) -> Optional[dict]:
        try:
            decoded = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            return decoded  # { "user_id": ..., "email": ..., "exp": ... }
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None