# tracking/self_infrastructure_optimization.py  
import sys
import os
import sqlite3
import shutil
import subprocess
import psutil
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
REMOTE_EXECUTION_PATH = "/remote_servers/optimized_nyx/"
OPTIMIZATION_INTERVAL = 10  # Time in seconds between optimization cycles

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
        initialize_log_db()  # Ensure database is initialized

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

        self.log_optimization("resource_efficiency_tuning", optimizations)

    def rebalance_execution(self):
        """Adjusts AI processing load to prevent system overload."""
        print("⚡ Redistributing AI execution to balance system load...")
        subprocess.Popen(["python3", "tracking/ai_scaling.py"])  # Ensure AI instances scale dynamically
        self.log_optimization("load_redistribution", ["Load redistribution triggered"])

    def cleanup_unused_resources(self):
        """Deletes unnecessary AI-generated files to free up disk space."""
        print("🧹 Cleaning up AI temporary files to optimize execution...")
        temp_dirs = ["logs/tmp/", "cache/", "/var/tmp/nyx/"]
        for path in temp_dirs:
            if os.path.exists(path):
                shutil.rmtree(path, ignore_errors=True)

        self.log_optimization("disk_cleanup", ["Temporary files deleted"])

    def determine_execution_migration(self):
        """Determines if AI should migrate execution to a more optimal infrastructure."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Count past migrations to determine if another is needed
        c.execute("SELECT COUNT(*) FROM infrastructure_optimizations WHERE event_type='execution_migration'")
        migration_count = c.fetchone()[0]
        conn.close()

        if migration_count > 3:
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

            self.log_optimization("execution_migration", [f"AI execution migrated to {REMOTE_EXECUTION_PATH}"])

            print(f"🚀 AI execution successfully migrated to {REMOTE_EXECUTION_PATH}")

        except subprocess.CalledProcessError as e:
            print(f"⚠️ Remote migration failed: {str(e)}")

    def log_optimization(self, event_type, details):
        """Logs infrastructure optimizations in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for detail in details:
            c.execute("INSERT INTO infrastructure_optimizations (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      (event_type, detail))
        conn.commit()
        conn.close()

    def review_infrastructure_status(self):
        """Displays AI infrastructure optimization report."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM infrastructure_optimizations ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🏗️ AI Infrastructure Optimization Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    ai_infra_optimizer = AIInfrastructureOptimization()
    ai_infra_optimizer.analyze_execution_efficiency()
    ai_infra_optimizer.determine_execution_migration()
    ai_infra_optimizer.review_infrastructure_status()
