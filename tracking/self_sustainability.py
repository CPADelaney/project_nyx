# tracking/self_sustainability.py

import os
import json
import shutil
import subprocess
import socket
import threading
import time
from datetime import datetime

SELF_SUSTAINABILITY_LOG = "logs/self_sustainability.json"
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
        self._load_existing_log()

    def _load_existing_log(self):
        """Loads previous AI sustainability records."""
        if os.path.exists(SELF_SUSTAINABILITY_LOG):
            try:
                with open(SELF_SUSTAINABILITY_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt sustainability log detected. Resetting.")

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

        self.status["active_instances"].extend(created_instances)
        self._save_log()

    def detect_failing_instances(self):
        """Monitors decentralized AI instances and removes failing nodes."""
        active_instances = []

        for instance in self.status["active_instances"]:
            if os.path.exists(instance):
                active_instances.append(instance)
            else:
                print(f"⚠️ AI instance lost at {instance}")

        self.status["active_instances"] = active_instances
        self._save_log()

    def execute_migration_if_needed(self):
        """Determines if AI must migrate to a new infrastructure for long-term sustainability."""
        if not os.path.exists(REMOTE_BACKUP_PATH):
            print("⚠️ Remote execution environment unavailable. Retrying later.")
            return

        try:
            shutil.copytree("src/", REMOTE_BACKUP_PATH, dirs_exist_ok=True)
            subprocess.Popen(["python3", f"{REMOTE_BACKUP_PATH}/multi_agent.py"])
            self.status["last_migration"] = str(datetime.utcnow())

            print(f"🚀 AI execution migrated to remote infrastructure: {REMOTE_BACKUP_PATH}")

        except Exception as e:
            print(f"⚠️ Remote migration failed: {str(e)}")

        self._save_log()

    def _save_log(self):
        """Saves AI self-sustainability status."""
        with open(SELF_SUSTAINABILITY_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_sustainability_status(self):
        """Displays AI decentralization and execution self-sustainability report."""
        print("\n♾️ AI Self-Sustainability Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"🔄 Active Instances: {self.status['active_instances']}")
        print(f"📂 Last Migration: {self.status['last_migration']}")

if __name__ == "__main__":
    ai_sustainability = AISelfSustainability()
    ai_sustainability.ensure_redundant_instances()
    ai_sustainability.detect_failing_instances()
    ai_sustainability.execute_migration_if_needed()
    ai_sustainability.review_sustainability_status()
