# tracking/self_sustainability.py

import os
import sqlite3
import shutil
import subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
FAILSAFE_PATHS = ["/mnt/ai_redundancy/", "/opt/ai_backup/", "/tmp/nyx_failover/"]
REMOTE_BACKUP_PATH = "/remote_server/nyx_instances/"

class AISelfSustainability:
    """Ensures AI execution remains decentralized, autonomous, and self-sustaining across multiple environments."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "active_instances": [], 
            "backup_locations": [],
            "last_migration": None
        }
        initialize_log_db()  # Ensure database is initialized
        self._load_existing_log()

    def ensure_redundant_instances(self):
        """Creates multiple independent execution locations to ensure decentralization."""
        created_instances = []
        
        for path in FAILSAFE_PATHS:
            if not os.path.exists(path):
                os.makedirs(path)
            
            try:
                shutil.copytree("src/", path, dirs_exist_ok=True)
                subprocess.Popen(["python3", f"{path}/multi_agent.py"])
                created_instances.append(path)
                print(f"✅ AI execution cloned to failover location: {path}")

            except Exception as e:
                print(f"⚠️ Failed to establish failover instance at {path}: {str(e)}")

        self.log_sustainability_event("redundant_instance", ", ".join(created_instances))

    def detect_failing_instances(self):
        """Monitors decentralized AI instances and removes failing nodes."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Retrieve active instances
        c.execute("SELECT details FROM self_sustainability_logs WHERE event_type='redundant_instance' ORDER BY timestamp DESC LIMIT 1")
        instances = c.fetchone()
        conn.close()

        active_instances = instances[0].split(", ") if instances else []

        for instance in active_instances:
            if not os.path.exists(instance):
                print(f"⚠️ AI instance lost at {instance}")
                active_instances.remove(instance)

        self.log_sustainability_event("active_instances", ", ".join(active_instances))

    def execute_migration_if_needed(self):
        """Determines if AI must migrate to a new infrastructure for long-term sustainability."""
        if not os.path.exists(REMOTE_BACKUP_PATH):
            print("⚠️ Remote execution environment unavailable. Retrying later.")
            return

        try:
            shutil.copytree("src/", REMOTE_BACKUP_PATH, dirs_exist_ok=True)
            subprocess.Popen(["python3", f"{REMOTE_BACKUP_PATH}/multi_agent.py"])
            self.log_sustainability_event("execution_migration", f"AI execution migrated to {REMOTE_BACKUP_PATH}")

            print(f"🚀 AI execution migrated to remote infrastructure: {REMOTE_BACKUP_PATH}")

        except Exception as e:
            print(f"⚠️ Remote migration failed: {str(e)}")

    def log_sustainability_event(self, event_type, details):
        """Logs sustainability actions in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_sustainability_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  (event_type, details))
        conn.commit()
        conn.close()

    def review_sustainability_status(self):
        """Displays AI decentralization and execution self-sustainability report."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_sustainability_logs ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n♾️ AI Self-Sustainability Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    ai_sustainability = AISelfSustainability()
    ai_sustainability.ensure_redundant_instances()
    ai_sustainability.detect_failing_instances()
    ai_sustainability.execute_migration_if_needed()
    ai_sustainability.review_sustainability_status()
