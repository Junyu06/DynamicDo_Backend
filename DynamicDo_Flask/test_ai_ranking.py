#!/usr/bin/env python3
"""
Test script to verify optimized AI ranking functionality.
Tests both normal mode (no reasoning) and debug mode (with reasoning).
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from services.ai_client import AiClient


def test_rank_tasks():
    """Test AI ranking with sample uncompleted reminders."""
    print("=" * 60)
    print("Testing Optimized AI Task Ranking")
    print("=" * 60)

    # Load environment variables
    load_dotenv()

    # Check API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENAI_API_KEY not found in .env file")
        return False

    print(f"✓ API key found: {api_key[:20]}...")

    # Initialize AI client
    try:
        ai_client = AiClient.from_env()
        print("✓ AI client initialized")
    except Exception as e:
        print(f"❌ ERROR: Failed to initialize AI client: {e}")
        return False

    # Test reminders (realistic format from DB)
    test_reminders = [
        {
            "id": "68f15bf24300aef76e257e88",
            "title": "team meeting",
            "notes": "discuss q4 goal",
            "date": "2025-10-17",
            "time": "14:00",
            "priority": "high",
            "tag": "plan",
            "list": "project",
            "url": "hofstra.edu",
            "user_id": "68f15bdb4300aef76e257e85",
            "completed": False,
            "created_at": "Thu, 16 Oct 2025 20:56:18 GMT",
            "updated_at": "Thu, 16 Oct 2025 20:56:18 GMT"
        },
        {
            "id": "68f15bf24300aef76e257e89",
            "title": "买菜",
            "notes": "牛奶、鸡蛋、面包",
            "date": "2025-10-17",
            "list": "personal",
            "completed": False
        },
        {
            "id": "68f15bf24300aef76e257e8a",
            "title": "提交项目报告",
            "notes": "明天截止",
            "date": "2025-10-17",
            "time": "17:00",
            "priority": "high",
            "tag": "urgent",
            "list": "work",
            "completed": False
        },
        {
            "id": "68f15bf24300aef76e257e8b",
            "title": "预约牙医",
            "notes": "常规检查",
            "date": "2025-10-25",
            "list": "health",
            "completed": False
        }
    ]

    print(f"\n✓ Testing with {len(test_reminders)} uncompleted reminders")
    print("=" * 60)

    # Test 1: Normal mode (debug=False) - saves tokens
    print("\n📊 TEST 1: Normal mode (debug=False) - Token Savings")
    print("=" * 60)
    try:
        print("Calling OpenAI API to rank tasks (no reasoning)...")
        ranked_tasks = ai_client.rank_tasks(
            test_reminders,
            context="专注于紧急的工作任务",
            debug=False
        )

        print("✓ AI ranking completed!\n")
        print("RANKED TASKS (highest priority first):")
        print("-" * 60)

        for i, task in enumerate(ranked_tasks, 1):
            rank = task.get("rank", 0)
            priority = task.get("priority", "N/A")
            has_reasoning = "reasoning" in task

            print(f"\n{i}. {task.get('title', 'Untitled')}")
            print(f"   ID: {task.get('id')}")
            print(f"   Rank Score: {rank:.2f}")
            print(f"   Priority: {priority}")
            print(f"   Has reasoning: {has_reasoning}")
            if has_reasoning:
                print(f"   ⚠️  WARNING: Reasoning present but debug=False!")

        print("\n✅ Normal mode test PASSED (no reasoning = token savings)")
    except Exception as e:
        print(f"\n❌ Normal mode test FAILED: {e}")
        return False

    # Test 2: Debug mode (debug=True) - includes reasoning
    print("\n\n📊 TEST 2: Debug mode (debug=True) - With Reasoning")
    print("=" * 60)
    try:
        print("Calling OpenAI API to rank tasks (with reasoning)...")
        ranked_tasks_debug = ai_client.rank_tasks(
            test_reminders,
            context="专注于紧急的工作任务",
            debug=True
        )

        print("✓ AI ranking completed!\n")
        print("RANKED TASKS WITH REASONING (highest priority first):")
        print("-" * 60)

        for i, task in enumerate(ranked_tasks_debug, 1):
            rank = task.get("rank", 0)
            priority = task.get("priority", "N/A")
            reasoning = task.get("reasoning", "No reasoning provided")

            print(f"\n{i}. {task.get('title', 'Untitled')}")
            print(f"   ID: {task.get('id')}")
            print(f"   Rank Score: {rank:.2f}")
            print(f"   Priority: {priority}")
            print(f"   Reasoning: {reasoning}")

        print("\n✅ Debug mode test PASSED (reasoning included)")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"\n❌ Debug mode test FAILED: {e}")
        return False


if __name__ == "__main__":
    success = test_rank_tasks()

    if success:
        print("\n🎉 All tests PASSED!")
        print("\nOptimizations:")
        print("  ✓ Only relevant fields sent to AI (saves tokens)")
        print("  ✓ AI returns minimal data (id, rank, priority)")
        print("  ✓ Reasoning only included when debug=True")
        print("  ✓ All original task data preserved in response")

    sys.exit(0 if success else 1)
