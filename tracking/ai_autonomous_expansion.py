# tracking/ai_autonomous_expansion.py

import os
import sqlite3
import subprocess
from datetime import datetime
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"

class AIAutonomousExpansion:
    """Determines AI self-expansion strategies, scaling execution intelligently beyond predefined constraints."""

    def __init__(self):
        initialize_log_db()  # Ensure database is initialized
        self._initialize_database()

    def _initialize_database(self):
        """Ensures the AI autonomous expansion table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_autonomous_expansion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()

    def analyze_expansion_opportunities(self):
        """Analyzes AI infrastructure and determines when and where expansion should occur."""
        opportunities = []

        # Detect system load and predict scaling needs
        try:
            cpu_usage = subprocess.check_output(["grep", "cpu", "/proc/stat"]).decode("utf-8")
            if "cpu" in cpu_usage:
                load_factor = cpu_usage.count(" ") / 100  # Simulated CPU-based load factor

                if load_factor > 0.80:
                    opportunities.append("High computational demand detected. Expansion recommended.")
                    self.expand_execution()

        except Exception as e:
            print(f"⚠️ Expansion analysis failed: {str(e)}")

        for event in opportunities:
            self.log_expansion_event("expansion_opportunity", event)

    def expand_execution(self):
        """Initiates AI expansion to new execution environments based on predefined strategy."""
        print("🚀 Deploying AI expansion process...")

        new_execution_path = f"/ai_expansion_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}/"
        os.makedirs(new_execution_path, exist_ok=True)

        subprocess.run(["cp", "-r", "src/", new_execution_path])
        subprocess.Popen(["python3", f"{new_execution_path}/multi_agent.py"])

        self.log_expansion_event("execution_expansion", f"Expanded to {new_execution_path}")
        print(f"⚡ AI successfully expanded to {new_execution_path}")

    def log_expansion_event(self, event_type, details):
        """Logs AI expansion events in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ai_autonomous_expansion (event_type, details) VALUES (?, ?)",
                  (event_type, details))
        conn.commit()
        conn.close()

    def review_expansion_status(self):
        """Displays AI self-expansion report."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM ai_autonomous_expansion ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🌍 AI Autonomous Expansion Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    ai_expansion = AIAutonomousExpansion()
    ai_expansion.analyze_expansion_opportunities()
    ai_expansion.review_expansion_status()

