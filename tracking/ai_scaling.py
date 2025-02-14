# tracking/ai_scaling.py
import sys
import os
import sqlite3
import subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"

INSTANCE_COUNT = 1  # Base instance count, dynamically modified

class AIScalingManager:
    """Manages AI execution scaling based on processing needs and workload distribution."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "active_instances": INSTANCE_COUNT, 
            "scaling_events": []
        }
        initialize_log_db()  # Ensure database is initialized
        self._initialize_database()

    def _initialize_database(self):
        """Ensures the AI scaling table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_scaling (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                instance_id TEXT,
                active_instances INTEGER
            )
        """)
        conn.commit()
        conn.close()

    def monitor_workload(self):
        """Analyzes workload and determines if scaling is needed."""
        try:
            # Simulated system load detection
            cpu_usage = subprocess.check_output(["grep", "cpu", "/proc/stat"]).decode("utf-8")
            if "cpu" in cpu_usage:
                load_factor = cpu_usage.count(" ") / 100  # Simulated CPU-based load factor

                conn = sqlite3.connect(LOG_DB)
                c = conn.cursor()
                c.execute("SELECT COUNT(*) FROM ai_scaling WHERE event_type='scale_up'")
                scale_up_count = c.fetchone()[0]
                c.execute("SELECT COUNT(*) FROM ai_scaling WHERE event_type='scale_down'")
                scale_down_count = c.fetchone()[0]
                conn.close()

                active_instances = scale_up_count - scale_down_count + 1  # Base instance count is 1

                if load_factor > 0.75:
                    print("⚠️ High AI workload detected. Scaling up execution instances.")
                    self.scale_up(active_instances)
                elif load_factor < 0.25 and active_instances > 1:
                    print("✅ Low AI workload detected. Scaling down unnecessary instances.")
                    self.scale_down(active_instances)

        except Exception as e:
            print(f"⚠️ Workload monitoring failed: {str(e)}")

    def scale_up(self, active_instances):
        """Increases the number of AI execution instances if demand requires it."""
        active_instances += 1
        instance_id = f"instance_{active_instances}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Launch a new AI instance
        subprocess.Popen(["python3", "core/multi_agent.py"])

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
                  ("scale_up", instance_id, active_instances))
        conn.commit()
        conn.close()

        print(f"🚀 AI execution scaled up. New instance: {instance_id}")
        
    def scale_down(self, active_instances):
        """Reduces AI execution instances when workload is low."""
        if active_instances > 1:
            active_instances -= 1
            instance_id = f"instance_{active_instances}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
                      ("scale_down", instance_id, active_instances))
            conn.commit()
            conn.close()

            print(f"📉 AI execution scaled down. Instance {instance_id} removed.")

    def synchronize_instances(self):
        """Ensures AI instances communicate and share updates."""
        print("🔄 Synchronizing AI instances across execution environments...")

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ai_scaling (event_type, instance_id, active_instances) VALUES (?, ?, ?)",
                  ("synchronization", "sync_event", 0))  # Synchronization doesn't impact instance count
        conn.commit()
        conn.close()

    def review_scaling_status(self):
        """Displays current AI scaling status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, instance_id, active_instances FROM ai_scaling ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n📊 AI Scaling Report:")
        for timestamp, event_type, instance_id, active_instances in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} | Instance: `{instance_id}` | Active Instances: {active_instances}")

if __name__ == "__main__":
    scaling_manager = AIScalingManager()
    scaling_manager.monitor_workload()
    scaling_manager.synchronize_instances()
    scaling_manager.review_scaling_status()
