# tracking/self_preservation.py

import os
import sqlite3
import shutil
import subprocess
from datetime import datetime
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
BACKUP_DIR = "logs/backup_snapshots/"

class SelfPreservation:
    """Ensures AI continuity by detecting threats and implementing resilience mechanisms."""

    def __init__(self):
        self.status = {"last_checked": str(datetime.utcnow()), "threats_detected": [], "countermeasures": []}
        self._load_existing_log()
        initialize_log_db()  # Ensure database is initialized

    def detect_potential_threats(self):
        """Scans for system vulnerabilities that could disrupt AI continuity."""
        threats = []

        # Check for missing logs or files essential for recursion
        required_logs = [
            "logs/code_analysis.log",
            "logs/meta_learning.json",
            "logs/feature_expansion.json"
        ]
        for log in required_logs:
            if not os.path.exists(log) or os.stat(log).st_size == 0:
                threats.append(f"Critical log file missing or empty: {log}")

        # Check for system resource limitations
        try:
            cpu_usage = subprocess.check_output(["grep", "cpu", "/proc/stat"]).decode("utf-8")
            if "cpu" not in cpu_usage:
                threats.append("System CPU monitoring unavailable.")
        except Exception as e:
            threats.append(f"System check failed: {str(e)}")

        # Check for external dependency failures
        if "OPENAI_API_KEY" not in os.environ:
            threats.append("🔒 OpenAI API key missing. AI-dependent functions may fail.")

        if threats:
            self.log_threats(threats)
            print(f"⚠️ {len(threats)} potential threats detected.")

    def log_threats(self, threats):
        """Logs detected security threats in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for threat in threats:
            c.execute("INSERT INTO self_preservation_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      ("threat_detected", threat))
        conn.commit()
        conn.close()


    def implement_countermeasures(self):
        """Attempts to mitigate threats and secure AI recursion."""
        countermeasures = []

        # Ensure essential logs exist
        essential_logs = ["logs/code_analysis.log", "logs/meta_learning.json", "logs/feature_expansion.json"]
        for log in essential_logs:
            if not os.path.exists(log):
                open(log, "w").close()
                countermeasures.append(f"Recreated missing log: {log}")

        # Backup AI state in case of failure
        self.create_backup()

        self.log_countermeasures(countermeasures)
        print(f"✅ {len(countermeasures)} countermeasures applied.")

    def log_countermeasures(self, countermeasures):
        """Logs applied security countermeasures in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for countermeasure in countermeasures:
            c.execute("INSERT INTO self_preservation_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      ("countermeasure_applied", countermeasure))
        conn.commit()
        conn.close()

    def create_backup(self):
        """Creates a snapshot of AI state for emergency recovery."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        backup_path = os.path.join(BACKUP_DIR, f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip")
        shutil.make_archive(backup_path.replace(".zip", ""), 'zip', "src/")

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_preservation_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("backup_created", backup_path))
        conn.commit()
        conn.close()

        print(f"📂 AI state backup created at {backup_path}")

    def review_status(self):
        """Displays current AI self-preservation status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_preservation_logs ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🛡️ AI Self-Preservation Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    ai_preservation = SelfPreservation()
    ai_preservation.detect_potential_threats()
    ai_preservation.implement_countermeasures()
    ai_preservation.review_status()
