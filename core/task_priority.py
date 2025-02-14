# core/task_priority.py

import sys
import os
import json
import time
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

TASK_PRIORITY_LOG = "logs/task_priority.json"
PERFORMANCE_LOG = "logs/performance_history.json"

DEFAULT_PRIORITIES = {
    "optimizer": 5,   # Scale: 1-10 (Higher means more priority)
    "expander": 5,
    "security": 5,
    "validator": 5
}

class TaskPriorityManager:
    """Manages AI agent task priorities with real-time attention scaling."""

    def __init__(self):
        self.task_priorities = self.load_task_priorities()
        self.lock = threading.Lock()  # Ensure safe concurrent updates

    def load_task_priorities(self):
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

    def ensure_performance_log(self):
        """Ensures the performance history file is always properly initialized."""
        if not os.path.exists(PERFORMANCE_LOG) or os.stat(PERFORMANCE_LOG).st_size == 0:
            with open(PERFORMANCE_LOG, "w", encoding="utf-8") as file:
                json.dump([], file, indent=4)  # ✅ Ensure a valid JSON list structure
            print("✅ Initialized performance history log.")

    def adjust_task_priorities(self):
        """Dynamically adjusts AI agent execution priorities based on recent performance history."""
        self.ensure_performance_log()

        try:
            with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
                history = json.load(file)
                if not history:
                    print("⚠️ Performance history is empty. Keeping current priorities.")
                    return self.task_priorities
        except json.JSONDecodeError:
            print("❌ Error: Performance history file is corrupt. Resetting to defaults.")
            self.ensure_performance_log()
            return self.task_priorities

        # Adjust priorities based on last 3 performance cycles
        for entry in history[-3:]:
            if "slowest_functions" in entry:
                self.task_priorities["optimizer"] += 1
            if "security_alerts" in entry:
                self.task_priorities["security"] += 2
            if "new_feature_requests" in entry:
                self.task_priorities["expander"] += 1

        # Normalize priority values (keep between 1-10)
        for agent in self.task_priorities:
            self.task_priorities[agent] = max(1, min(10, self.task_priorities[agent]))

        self.save_task_priorities()

        print(f"✅ Updated AI task priorities: {self.task_priorities}")

    def save_task_priorities(self):
        """Saves task priorities to the log file."""
        with open(TASK_PRIORITY_LOG, "w", encoding="utf-8") as file:
            json.dump(self.task_priorities, file, indent=4)

    def real_time_priority_adjustment(self, task, impact_score):
        """Dynamically adjusts priority in real-time based on task execution impact."""
        with self.lock:
            if task in self.task_priorities:
                adjustment = impact_score // 2  # Scale impact influence
                self.task_priorities[task] = max(1, min(10, self.task_priorities[task] + adjustment))
                self.save_task_priorities()
                print(f"⚡ Real-Time Priority Update: {task} → {self.task_priorities[task]}")

    def redistribute_resources(self):
        """Reallocates AI processing power dynamically based on active task loads."""
        with self.lock:
            highest_priority = max(self.task_priorities, key=self.task_priorities.get)
            lowest_priority = min(self.task_priorities, key=self.task_priorities.get)

            # Shift resources from lowest priority to highest priority
            if self.task_priorities[highest_priority] > self.task_priorities[lowest_priority] + 2:
                print(f"🔄 Redistributing resources: Boosting {highest_priority}, reducing {lowest_priority}")
                self.task_priorities[highest_priority] = min(10, self.task_priorities[highest_priority] + 1)
                self.task_priorities[lowest_priority] = max(1, self.task_priorities[lowest_priority] - 1)

            self.save_task_priorities()

    def continuous_monitoring(self):
        """Runs a background thread that continuously optimizes AI task allocation in real-time."""
        def monitor():
            while True:
                time.sleep(10)  # Adjust interval for real-time responsiveness
                self.redistribute_resources()

        threading.Thread(target=monitor, daemon=True).start()

if __name__ == "__main__":
    priority_manager = TaskPriorityManager()
    priority_manager.adjust_task_priorities()
    priority_manager.continuous_monitoring()
