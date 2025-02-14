# core/task_priority.py

import json
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality

PERFORMANCE_LOG = "logs/performance_history.json"
TASK_PRIORITY_LOG = "logs/task_priority.json"

DEFAULT_PRIORITIES = {
    "optimizer": 5,   # Scale: 1-10 (Higher means more priority)
    "expander": 5,
    "security": 5,
    "validator": 5
}

def load_task_priorities():
    """Loads or initializes AI agent task priorities."""
    if os.path.exists(TASK_PRIORITY_LOG):
        try:
            with open(TASK_PRIORITY_LOG, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Corrupt task priority config. Resetting.")

    with open(TASK_PRIORITY_LOG, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_PRIORITIES, file, indent=4)
    return DEFAULT_PRIORITIES

def adjust_task_priorities():
    """Adjusts agent execution priorities based on performance trends."""
    if not os.path.exists(PERFORMANCE_LOG):
        print("⚠️ No performance history found. Keeping current priorities.")
        return load_task_priorities()

    with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
        history = json.load(file)

    task_priorities = load_task_priorities()

    # Analyze slowdowns & adjust priorities dynamically
    for entry in history[-3:]:  # Look at last 3 performance cycles
        if "slowest_functions" in entry:
            task_priorities["optimizer"] += 1  # Increase optimization priority if slowdowns detected
        if "security_alerts" in entry:
            task_priorities["security"] += 2  # Increase security checks if vulnerabilities detected
        if "new_feature_requests" in entry:
            task_priorities["expander"] += 1  # Increase feature expansion priority

    # Normalize priorities (keep values between 1-10)
    for agent in task_priorities:
        task_priorities[agent] = max(1, min(10, task_priorities[agent]))

    with open(TASK_PRIORITY_LOG, "w", encoding="utf-8") as file:
        json.dump(task_priorities, file, indent=4)

    print(f"✅ Updated AI task priorities: {task_priorities}")

if __name__ == "__main__":
    adjust_task_priorities()
