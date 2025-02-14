# tracking/feature_expansion.py

import os
import sqlite3
import subprocess
from collections import Counter
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
FEATURE_DIR = "src/generated_features/"

class FeatureExpansion:
    """Handles AI memory tracking and new self-improvement feature generation."""

    def __init__(self):
        initialize_log_db()  # Ensure database is initialized
        self._initialize_database()

    def _initialize_database(self):
        """Ensures the feature expansion table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS feature_expansion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                feature_name TEXT UNIQUE,
                status TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def analyze_missing_capabilities(self):
        """Scans past improvements and identifies missing or underdeveloped features."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Retrieve slowest functions and missing capabilities
        c.execute("SELECT details FROM performance_logs WHERE event_type='slow_function'")
        slow_functions = [row[0] for row in c.fetchall()]

        c.execute("SELECT details FROM performance_logs WHERE event_type='missing_capability'")
        missing_capabilities = [row[0] for row in c.fetchall()]
        conn.close()

        if not slow_functions and not missing_capabilities:
            print("⚠️ No performance history found. Skipping feature expansion analysis.")
            return []

        # Identify frequently occurring inefficiencies
        recurring_issues = Counter(slow_functions + missing_capabilities)
        missing_features = [feature for feature, count in recurring_issues.items() if count > 2]  # More than 2 occurrences

        return missing_features

    def generate_new_feature_goals(self):
        """Generates new AI-driven features based on persistent inefficiencies."""
        missing_features = self.analyze_missing_capabilities()

        if not missing_features:
            print("✅ No critical missing features detected. No feature expansion needed.")
            return

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for feature in missing_features:
            c.execute("""
                INSERT INTO feature_expansion (feature_name, status) 
                VALUES (?, 'pending') 
                ON CONFLICT(feature_name) DO NOTHING
            """, (feature,))
        conn.commit()
        conn.close()

        print(f"📌 Generated {len(missing_features)} new AI feature expansion goals.")

    def self_generate_feature_code(self):
        """Generates new AI functionality based on detected feature gaps."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT feature_name FROM feature_expansion WHERE status='pending'")
        feature_goals = c.fetchall()
        conn.close()

        if not feature_goals:
            print("✅ No pending feature expansions.")
            return

        print("⚙️ Generating AI-driven feature implementations...")
        os.makedirs(FEATURE_DIR, exist_ok=True)

        for feature in feature_goals:
            feature_name = feature[0].replace("Develop ", "").replace(" to enhance AI efficiency.", "")
            feature_func = feature_name.replace(" ", "_").lower()

            ai_generated_code = f"""
# Auto-Generated Feature: {feature_name}
def {feature_func}():
    \"\"\"This function implements {feature_name}, as identified by AI.\"\"\"  
    pass
"""

            # Write new feature to a dynamic module
            feature_file = f"{FEATURE_DIR}{feature_func}.py"
            with open(feature_file, "w", encoding="utf-8") as file:
                file.write(ai_generated_code)

            # Update feature status in the database
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("UPDATE feature_expansion SET status='in-progress', last_updated=datetime('now') WHERE feature_name=?", (feature[0],))
            conn.commit()
            conn.close()

            print(f"🚀 AI-generated feature `{feature_name}` created at {feature_file}.")

    def finalize_thought(self, thought_id):
        """Marks a completed AI-generated feature as finalized."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("UPDATE feature_expansion SET status='completed', last_updated=datetime('now') WHERE feature_name=?", (thought_id,))
        conn.commit()
        conn.close()
        print(f"🔒 Thought `{thought_id}` finalized and archived.")

    def review_memory(self):
        """Displays AI's current feature expansion status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, feature_name, status FROM feature_expansion ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n📖 AI Thought Memory Review:")
        for timestamp, feature_name, status in logs:
            print(f"🔹 {timestamp} | Feature: `{feature_name}` | Status: {status}")

if __name__ == "__main__":
    feature_expansion = FeatureExpansion()
    feature_expansion.generate_new_feature_goals()
    feature_expansion.self_generate_feature_code()
    feature_expansion.review_memory()
