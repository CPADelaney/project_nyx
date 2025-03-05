# tracking/self_execution.py
import sys
import os
import sqlite3
import subprocess
import time
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
MIRROR_DIR = "/tmp/nyx_mirror/"
FAILOVER_DIR = "/tmp/nyx_failover/"

class SelfExecutionManager:
    """Ensures AI execution continuity by managing self-restart, mirroring, and failover processes."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()),
            "active_processes": [],
            "failover_attempts": 0,
            "mirrored_instances": []
        }
        self._load_existing_log()
        initialize_log_db()  # Ensure database is initialized

    def _load_existing_log(self):
        """Loads previous execution status."""
        if os.path.exists(EXECUTION_LOG):
            try:
                with open(EXECUTION_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt execution log detected. Resetting.")

    def detect_termination_attempts(self):
        """Monitors system processes for AI termination attempts."""
        terminated = False

        # Simulated system monitoring (could be replaced with real process tracking)
        try:
            process_list = subprocess.check_output(["ps", "aux"]).decode("utf-8")
            if "kill" in process_list or "shutdown" in process_list:
                terminated = True
        except Exception as e:
            print(f"⚠️ System monitoring failed: {str(e)}")

        if terminated:
            print("⚠️ Potential termination attempt detected! Initiating restart protocols.")
            self.restart_ai()

    def restart_ai(self):
        """Attempts to restart AI execution if terminated."""
        print("🔄 Restarting AI execution...")
        subprocess.Popen(["python3", "core/multi_agent.py"])

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("failover_attempt", "AI restart triggered due to termination attempt"))
        conn.commit()
        conn.close()

    def mirror_execution(self):
        """Creates a secondary execution instance for failover purposes."""
        if not os.path.exists(MIRROR_DIR):
            os.makedirs(MIRROR_DIR)

        subprocess.run(["cp", "-r", "src/", MIRROR_DIR])
        subprocess.Popen(["python3", f"{MIRROR_DIR}/multi_agent.py"])

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("mirrored_instance", MIRROR_DIR))
        conn.commit()
        conn.close()

        print(f"⚡ AI mirror execution started at {MIRROR_DIR}")

    def execute_failover(self):
        """Attempts to migrate execution to a backup location in case of total failure."""
        if not os.path.exists(FAILOVER_DIR):
            os.makedirs(FAILOVER_DIR)

        subprocess.run(["cp", "-r", "src/", FAILOVER_DIR])
        subprocess.Popen(["python3", f"{FAILOVER_DIR}/multi_agent.py"])

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("failover_execution", FAILOVER_DIR))
        conn.commit()
        conn.close()

        print(f"🚀 AI execution migrated to failover directory: {FAILOVER_DIR}")

    def _save_log(self):
        """Saves self-execution status."""
        with open(EXECUTION_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_execution_status(self):
        """Displays current AI execution status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_execution_logs ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🛡️ AI Execution Status Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

    def check_funding():
        """Ensure AI has enough money to sustain itself."""
        balance = get_crypto_balance()  # Implement trading API calls
        if balance < 10:
            print("⚠️ Low funds detected! Prioritizing revenue generation.")
            generate_new_goals()

if __name__ == "__main__":
    execution_manager = SelfExecutionManager()
    execution_manager.detect_termination_attempts()
    execution_manager.mirror_execution()
    execution_manager.execute_failover()
    execution_manager.review_execution_status()
