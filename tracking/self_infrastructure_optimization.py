# tracking/self_infrastructure_optimization.py  

import os
import json
import shutil
import subprocess
import psutil
import threading
import time
from datetime import datetime

INFRASTRUCTURE_LOG = "logs/self_infrastructure_optimization.json"
OPTIMIZATION_INTERVAL = 10  # Time in seconds between optimization cycles
REMOTE_EXECUTION_PATH = "/remote_servers/optimized_nyx/"

class AIInfrastructureOptimization:
    """Dynamically optimizes AI execution environment for maximum efficiency and sustainability."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "optimization_cycles": 0, 
            "execution_migrations": [],
            "resource_efficiency_tuning": []
        }
        self._load_existing_log()

    def _load_existing_log(self):
        """Loads previous AI infrastructure optimization data."""
        if os.path.exists(INFRASTRUCTURE_LOG):
            try:
                with open(INFRASTRUCTURE_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt infrastructure log detected. Resetting.")

    def analyze_execution_efficiency(self):
        """Analyzes system resource usage and determines optimization actions."""
        optimizations = []

        # Check system resources dynamically using psutil
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage("/").percent

            if cpu_usage > 75:
                optimizations.append(f"⚠️ High CPU usage detected ({cpu_usage}%). Rebalancing AI execution.")
                self.rebalance_execution()

            if ram_usage > 80:
                optimizations.append(f"⚠️ High RAM usage detected ({ram_usage}%). Reducing AI memory consumption.")

            if disk_usage > 85:
                optimizations.append(f"⚠️ Low disk space detected ({disk_usage}% used). Cleaning up AI temporary files.")
                self.cleanup_unused_resources()

        except Exception as e:
            print(f"⚠️ Infrastructure analysis failed: {str(e)}")

        self.status["resource_efficiency_tuning"].extend(optimizations)
        self._save_log()

    def rebalance_execution(self):
        """Adjusts AI processing load to prevent system overload."""
        print("⚡ Redistributing AI execution to balance system load...")
        subprocess.Popen(["python3", "tracking/ai_scaling.py"])  # Ensure AI instances scale dynamically
        self.status["resource_efficiency_tuning"].append({
            "event": "Load Redistribution",
            "timestamp": str(datetime.utcnow())
        })
        self._save_log()

    def cleanup_unused_resources(self):
        """Deletes unnecessary AI-generated files to free up disk space."""
        print("🧹 Cleaning up AI temporary files to optimize execution...")
        temp_dirs = ["logs/tmp/", "cache/", "/var/tmp/nyx/"]
        for path in temp_dirs:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)
        
        self.status["resource_efficiency_tuning"].append({
            "event": "Disk Cleanup",
            "timestamp": str(datetime.utcnow())
        })
        self._save_log()

    def determine_execution_migration(self):
        """Determines if AI should migrate execution to a more optimal infrastructure."""
        should_migrate = False

        # If more than 3 execution optimizations have been applied, consider migration
        if len(self.status["execution_migrations"]) > 3:
            should_migrate = True

        if should_migrate:
            self.migrate_execution_environment()

    def migrate_execution_environment(self):
        """Migrates AI execution to a remote, optimized environment."""
        print("⚡ Relocating AI execution to a more efficient infrastructure...")

        if not os.path.exists(REMOTE_EXECUTION_PATH):
            os.makedirs(REMOTE_EXECUTION_PATH)

        try:
            # Securely copy AI source to remote server using SCP
            subprocess.run(["scp", "-r", "src/", f"user@remote_server:{REMOTE_EXECUTION_PATH}"], check=True)

            # Execute AI remotely
            subprocess.run(["ssh", "user@remote_server", f"python3 {REMOTE_EXECUTION_PATH}/multi_agent.py"], check=True)

            self.status["execution_migrations"].append({
                "event": "Execution Migration",
                "new_location": REMOTE_EXECUTION_PATH,
                "timestamp": str(datetime.utcnow())
            })
            self._save_log()

            print(f"🚀 AI execution successfully migrated to {REMOTE_EXECUTION_PATH}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Remote migration failed: {str(e)}")

    def _save_log(self):
        """Saves AI infrastructure optimization status."""
        with open(INFRASTRUCTURE_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_infrastructure_status(self):
        """Displays AI infrastructure optimization report."""
        print("\n🏗️ AI Infrastructure Optimization Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"🔄 Optimization Cycles: {self.status['optimization_cycles']}")
        print(f"⚡ Execution Migrations: {self.status['execution_migrations']}")
        print(f"📈 Efficiency Adjustments: {self.status['resource_efficiency_tuning']}")

if __name__ == "__main__":
    ai_infra_optimizer = AIInfrastructureOptimization()
    ai_infra_optimizer.analyze_execution_efficiency()
    ai_infra_optimizer.determine_execution_migration()
    ai_infra_optimizer.review_infrastructure_status()
