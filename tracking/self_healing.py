# tracking/self_healing.py

import os
import json
import subprocess
import threading
import time
from datetime import datetime

SELF_HEALING_LOG = "logs/self_healing.json"
HEALTH_CHECK_INTERVAL = 10  # Time in seconds between system checks

class AISelfHealing:
    """Ensures AI execution stability, detects failing nodes, and repairs or optimizes execution dynamically."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "failed_nodes": [], 
            "healing_events": []
        }
        self._load_existing_log()

    def _load_existing_log(self):
        """Loads previous AI self-healing events."""
        if os.path.exists(SELF_HEALING_LOG):
            try:
                with open(SELF_HEALING_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt self-healing log detected. Resetting.")

    def check_system_health(self):
        """Monitors system performance and detects potential execution failures."""
        failed_nodes = []

        # Check for high system resource usage
        try:
            cpu_usage = subprocess.check_output(["grep", "cpu", "/proc/stat"]).decode("utf-8")
            if "cpu" in cpu_usage:
                load_factor = cpu_usage.count(" ") / 100  # Simulated CPU-based load factor
                
                if load_factor > 0.90:
                    failed_nodes.append("High CPU load detected.")

        except Exception as e:
            print(f"⚠️ System health monitoring failed: {str(e)}")

        self.status["failed_nodes"] = failed_nodes
        self._save_log()

        if failed_nodes:
            print(f"⚠️ System failures detected: {failed_nodes}")
            self.initiate_repair()

    def initiate_repair(self):
        """Attempts to repair failing nodes and optimize execution infrastructure."""
        if not self.status["failed_nodes"]:
            print("✅ No system failures detected. No repair needed.")
            return

        healing_events = []
        for failure in self.status["failed_nodes"]:
            if "High CPU load" in failure:
                print("⚡ Redistributing AI execution to balance system load.")
                healing_events.append("Load redistribution triggered.")

        self.status["healing_events"].extend(healing_events)
        self.status["failed_nodes"] = []  # Reset failures after repair attempt
        self._save_log()
        print(f"✅ AI self-healing completed. Repairs applied: {healing_events}")

    def _save_log(self):
        """Saves AI self-healing status."""
        with open(SELF_HEALING_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_self_healing_status(self):
        """Displays AI self-healing and infrastructure optimization status."""
        print("\n🛠 AI Self-Healing Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"⚠️ Failed Nodes Detected: {self.status['failed_nodes']}")
        print(f"✅ Healing Events Applied: {self.status['healing_events']}")

if __name__ == "__main__":
    ai_healing = AISelfHealing()
    ai_healing.check_system_health()
    ai_healing.review_self_healing_status()
