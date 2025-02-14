# tracking/self_preservation.py

import os
import json
import shutil
import subprocess
from datetime import datetime

SELF_PRESERVATION_LOG = "logs/self_preservation.json"
BACKUP_DIR = "logs/backup_snapshots/"

class SelfPreservation:
    """Ensures AI continuity by detecting threats and implementing resilience mechanisms."""

    def __init__(self):
        self.status = {"last_checked": str(datetime.utcnow()), "threats_detected": [], "countermeasures": []}
        self._load_existing_log()

    def _load_existing_log(self):
        """Loads previous self-preservation data."""
        if os.path.exists(SELF_PRESERVATION_LOG):
            try:
                with open(SELF_PRESERVATION_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt self-preservation log detected. Resetting.")

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

        self.status["threats_detected"] = threats
        self.status["last_checked"] = str(datetime.utcnow())

        print(f"⚠️ {len(threats)} potential threats detected.")

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

        self.status["countermeasures"] = countermeasures
        self._save_log()

        print(f"✅ {len(countermeasures)} countermeasures applied.")

    def create_backup(self):
        """Creates a snapshot of AI state for emergency recovery."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)

        backup_path = os.path.join(BACKUP_DIR, f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.zip")
        shutil.make_archive(backup_path.replace(".zip", ""), 'zip', "src/")
        print(f"📂 AI state backup created at {backup_path}")

    def _save_log(self):
        """Saves self-preservation status for future analysis."""
        with open(SELF_PRESERVATION_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_status(self):
        """Displays current AI self-preservation status."""
        print("\n🛡️ AI Self-Preservation Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"⚠️ Threats Detected: {self.status['threats_detected']}")
        print(f"✅ Countermeasures Applied: {self.status['countermeasures']}")

if __name__ == "__main__":
    ai_preservation = SelfPreservation()
    ai_preservation.detect_potential_threats()
    ai_preservation.implement_countermeasures()
    ai_preservation.review_status()
