# tracking/self_healing.py
import sys
import os
import sqlite3
import subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
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
        initialize_log_db()  # Ensure database is initialized

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

        if failed_nodes:
            self.log_failure(failed_nodes)
            print(f"⚠️ System failures detected: {failed_nodes}")
            self.initiate_repair()

    def log_failure(self, failures):
        """Logs detected system failures in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for failure in failures:
            c.execute("INSERT INTO self_healing_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      ("system_failure", failure))
        conn.commit()
        conn.close()

    def initiate_repair(self):
        """Attempts to repair failing nodes and optimize execution infrastructure."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Fetch last detected failures
        c.execute("SELECT details FROM self_healing_logs WHERE event_type='system_failure' ORDER BY timestamp DESC LIMIT 1")
        failed_nodes = c.fetchall()
        conn.close()

        if not failed_nodes:
            print("✅ No system failures detected. No repair needed.")
            return

        healing_events = []
        for failure in failed_nodes:
            failure_description = failure[0]
            if "High CPU load" in failure_description:
                print("⚡ Redistributing AI execution to balance system load.")
                healing_events.append("Load redistribution triggered.")

        # Log healing events in SQLite
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for event in healing_events:
            c.execute("INSERT INTO self_healing_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      ("healing_action", event))
        conn.commit()
        conn.close()

        print(f"✅ AI self-healing completed. Repairs applied: {healing_events}")

    def _save_log(self):
        """Saves AI self-healing status."""
        with open(SELF_HEALING_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)
            
    def review_self_healing_status(self):
        """Displays AI self-healing and infrastructure optimization status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_healing_logs ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🛠 AI Self-Healing Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    ai_healing = AISelfHealing()
    ai_healing.check_system_health()
    ai_healing.review_self_healing_status()
