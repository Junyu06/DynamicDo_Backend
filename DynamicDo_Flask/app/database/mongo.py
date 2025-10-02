from __future__ import annotations
import os
from pymongo import MongoClient

# 直接在 import 时连接
MONGO_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGODB_DB", "dynamicdo")

client = MongoClient(MONGO_URI)  # 启动时立刻连接
db = client[DB_NAME]

# 定义常用的 collection
users_collection = db["users"]
tokens_collection = db["tokens"]
tasks_collection = db["tasks"]
reminders_collection = db["reminders"]