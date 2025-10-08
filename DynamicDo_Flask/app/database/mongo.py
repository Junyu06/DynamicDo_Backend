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

# 创建索引以确保数据完整性和查询性能
# email必须唯一，防止重复注册
users_collection.create_index("email", unique=True)

# user_id索引，加速查询某用户的所有reminders
reminders_collection.create_index("user_id")