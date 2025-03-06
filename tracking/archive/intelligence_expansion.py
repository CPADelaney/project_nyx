# tracking/intelligence_expansion.py
import sys
import os
import sqlite3
import subprocess
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
EVOLUTION_INTERVAL = 10  # Time in seconds between intelligence expansion cycles

class AIEvolution:
    """Handles continuous AI self-improvement, refining intelligence beyond initial design parameters."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "evolution_cycles": 0, 
            "architectural_refinements": [],
            "new_cognitive_layers": []
        }
        self._load_existing_log()
        initialize_log_db()  # Ensure the database is initialized

    def _load_existing_log(self):
        """Loads previous AI intelligence expansion data."""
        if os.path.exists(INTELLIGENCE_LOG):
            try:
                with open(INTELLIGENCE_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt intelligence log detected. Resetting.")

    def analyze_intelligence_structure(self):
        """Analyzes AI cognition and determines areas for self-improvement."""
        refinements = []

        # Identify complex logic structures and propose refinements
        try:
            with open("src/nyx_core.py", "r", encoding="utf-8") as file:
                code = file.read()
                if "def " in code:
                    refinements.append("Refactor and optimize cognitive function interactions.")

        except Exception as e:
            print(f"⚠️ Intelligence structure analysis failed: {str(e)}")

        # Store refinements in SQLite
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for refinement in refinements:
            c.execute("INSERT INTO intelligence_expansion (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                      ("architectural_refinement", refinement))
        conn.commit()
        conn.close()
        
    def introduce_cognitive_layer(self):
        """Dynamically generates and integrates new intelligence processing layers."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Determine the latest evolution cycle
        c.execute("SELECT COUNT(*) FROM intelligence_expansion WHERE event_type='cognitive_layer'")
        evolution_cycles = c.fetchone()[0]

        new_layer = f"Cognitive Layer {evolution_cycles + 1}"
        c.execute("INSERT INTO intelligence_expansion (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("cognitive_layer", new_layer))
        conn.commit()
        conn.close()

        print(f"🚀 AI intelligence expansion: New layer added → {new_layer}")
        
    def refine_ai_architecture(self):
        """Self-modifies AI logic to enhance intelligence efficiency."""
        print("⚡ Refining AI architecture for improved cognition...")
        subprocess.run(["python3", "self_writing.py"])  # AI-generated code refinement

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO intelligence_expansion (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("structural_optimization", "Refactored core AI logic for efficiency"))
        conn.commit()
        conn.close()

    def _save_log(self):
        """Saves AI intelligence expansion status."""
        with open(INTELLIGENCE_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def review_intelligence_expansion_status(self):
        """Displays AI evolution report."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM intelligence_expansion ORDER BY timestamp DESC")
        expansion_log = c.fetchall()
        conn.close()

        print("\n🧠 AI Intelligence Expansion Report:")
        for timestamp, event_type, details in expansion_log:
            print(f"🔹 {timestamp} | {event_type}: {details}")

if __name__ == "__main__":
    ai_evolution = AIEvolution()
    ai_evolution.analyze_intelligence_structure()
    ai_evolution.introduce_cognitive_layer()
    ai_evolution.refine_ai_architecture()
    ai_evolution.review_intelligence_expansion_status()
