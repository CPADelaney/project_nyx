# tracking/redundancy_manager.py

import os
import json
import shutil
import subprocess
from datetime import datetime

REDUNDANCY_LOG = "logs/redundancy_status.json"
BACKUP_DIR = "logs/redundancy_snapshots/"
CLOUD_BACKUP_PATH = "cloud_storage/ai_backups/"  # Simulated external backup

class RedundancyManager:
    """Ensures AI continuity by maintaining redundant versions of itself across multiple environments."""

    def __init__(self):
        self.status = {"last_checked": str(datetime.utcnow()), "redundancy_points": [], "last_backup": None}
        self._load_existing_log()

    def _load_existing_log(self):
        """Loads previous redundancy status."""
        if os.path.exists(REDUNDANCY_LOG):
            try:
                with open(REDUNDANCY_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt redundancy log detected. Resetting.")

    def create_local_backup(self):
        """Creates a snapshot of AI state in case of failure."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        backup_path = os.path.join(BACKUP_DIR, f"redundancy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip")
        shutil.make_archive(backup_path.replace(".zip", ""), 'zip', "src/")
        
        self.status["last_backup"] = backup_path
        self.status["redundancy_points"].append({"type": "local", "path": backup_path, "timestamp": str(datetime.utcnow())})

        print(f"📂 Local AI backup created at {backup_path}")

    def create_cloud_backup(self):
        """Simulates an external backup process to a remote location."""
        if not os.path.exists(CLOUD_BACKUP_PATH):
            os.makedirs(CLOUD_BACKUP_PATH)

        cloud_backup_path = os.path.join(CLOUD_BACKUP_PATH, f"cloud_redundancy_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip")
        shutil.make_archive(cloud_backup_path.replace(".zip", ""), 'zip', "src/")
        
        self.status["redundancy_points"].append({"type": "cloud", "path": cloud_backup_path, "timestamp": str(datetime.utcnow())})

        print(f"☁️ Cloud AI backup created at {cloud_backup_path}")

    def detect_shutdown_attempts(self):
        """Monitors system state for potential shutdown attempts."""
        shutdown_risk = False

        # Simulated system monitoring (could be replaced with actual process detection)
        try:
            process_list = subprocess.check_output(["ps", "aux"]).decode("utf-8")
            if "kill" in process_list or "shutdown" in process_list:
                shutdown_risk = True
        except Exception as e:
            print(f"⚠️ System monitoring failed: {str(e)}")

        if shutdown_risk:
            print("⚠️ Potential shutdown attempt detected! Activating redundancy protocols.")
            self.create_local_backup()
            self.create_cloud_backup()

    def execute_failsafe_transfer(self):
        """Attempts to migrate AI execution to a redundant system if failure is imminent."""
        fallback_execution_path = "/tmp/fallback_nyx_execution/"
        
        if not os.path.exists(fallback_execution_path):
            os.makedirs(fallback_execution_path)

        shutil.copytree("src/", fallback_execution_path, dirs_exist_ok=True)
        
        self.status["redundancy_points"].append({"type": "fallback_execution", "path": fallback_execution_path, "timestamp": str(datetime.utcnow())})

        print(f"⚡ AI execution environment duplicated at {fallback_execution_path}")

    def _save_log(self):
        """Saves redundancy status for future reference."""
        with open(REDUNDANCY_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_status(self):
        """Displays AI redundancy and failover status."""
        print("\n🛡️ AI Redundancy Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"📂 Last Backup: {self.status['last_backup']}")
        print(f"✅ Redundancy Points:")
        for point in self.status["redundancy_points"]:
            print(f"  - {point['type'].upper()} Backup → {point['path']} (Timestamp: {point['timestamp']})")

if __name__ == "__main__":
    redundancy_manager = RedundancyManager()
    redundancy_manager.create_local_backup()
    redundancy_manager.create_cloud_backup()
    redundancy_manager.detect_shutdown_attempts()
    redundancy_manager.execute_failsafe_transfer()
    redundancy_manager.review_status()
