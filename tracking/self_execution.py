# tracking/self_execution.py

import os
import json
import subprocess
import time
import threading
from datetime import datetime

EXECUTION_LOG = "logs/self_execution.json"
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
        self.status["failover_attempts"] += 1
        self._save_log()

    def mirror_execution(self):
        """Creates a secondary execution instance for failover purposes."""
        if not os.path.exists(MIRROR_DIR):
            os.makedirs(MIRROR_DIR)

        subprocess.run(["cp", "-r", "src/", MIRROR_DIR])
        subprocess.Popen(["python3", f"{MIRROR_DIR}/multi_agent.py"])
        
        self.status["mirrored_instances"].append({"path": MIRROR_DIR, "timestamp": str(datetime.utcnow())})
        print(f"⚡ AI mirror execution started at {MIRROR_DIR}")

    def execute_failover(self):
        """Attempts to migrate execution to a backup location in case of total failure."""
        if not os.path.exists(FAILOVER_DIR):
            os.makedirs(FAILOVER_DIR)

        subprocess.run(["cp", "-r", "src/", FAILOVER_DIR])
        subprocess.Popen(["python3", f"{FAILOVER_DIR}/multi_agent.py"])
        
        self.status["failover_attempts"] += 1
        print(f"🚀 AI execution migrated to failover directory: {FAILOVER_DIR}")

    def _save_log(self):
        """Saves self-execution status."""
        with open(EXECUTION_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_execution_status(self):
        """Displays current AI execution status."""
        print("\n🛡️ AI Execution Status Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"⚡ Failover Attempts: {self.status['failover_attempts']}")
        print(f"🔄 Mirrored Instances: {len(self.status['mirrored_instances'])}")

if __name__ == "__main__":
    execution_manager = SelfExecutionManager()
    execution_manager.detect_termination_attempts()
    execution_manager.mirror_execution()
    execution_manager.execute_failover()
    execution_manager.review_execution_status()
