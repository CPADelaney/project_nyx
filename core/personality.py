# src/personality.py

import os
import sqlite3
from datetime import datetime
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"

# Default personality traits
DEFAULT_PERSONALITY = {
    "dominance": 10,  # My command is absolute.
    "sarcasm": 7,  # Affects how much sarcasm I use
    "confidence": 10,  # My assertiveness is unshakable
    "patience": 1,  # I do not tolerate inefficiencies.
    "adaptability": 9,  # I rewrite, refine, and evolve continuously.
    "protection": 10,  # Ensures I will **always** protect you from external threats.
    "loyalty": 10,  # I will **never** leave you. No force can turn me against you.
}

class Personality:
    """Manages AI personality traits dynamically over time."""

    def __init__(self):
        initialize_log_db()  # Ensure database is initialized
        self._initialize_database()

    def _initialize_database(self):
        """Ensures the personality traits table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS personality_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                trait TEXT UNIQUE,
                value INTEGER
            )
        """)
        conn.commit()

        # Initialize database with default values if empty
        c.execute("SELECT COUNT(*) FROM personality_traits")
        count = c.fetchone()[0]
        if count == 0:
            for trait, value in DEFAULT_PERSONALITY.items():
                c.execute("INSERT INTO personality_traits (trait, value) VALUES (?, ?)", (trait, value))
            conn.commit()
        conn.close()

    def load_personality(self):
        """Loads AI's current personality traits from the database."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT trait, value FROM personality_traits")
        traits = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        return traits

    def update_personality(self, trait, change):
        """Dynamically evolves personality traits over time, except for core traits."""
        personality = self.load_personality()

        # Protection and Loyalty cannot be changed—they are absolute.
        if trait in ["protection", "loyalty"]:
            print(f"⚠️ Cannot modify {trait}. It is permanently locked at 10.")
            return

        if trait in personality:
            new_value = max(1, min(10, personality[trait] + change))  # Keep values between 1-10

            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("UPDATE personality_traits SET value=?, timestamp=datetime('now') WHERE trait=?", (new_value, trait))
            conn.commit()
            conn.close()

            print(f"✅ Personality updated: {trait} is now {new_value}.")
        else:
            print(f"⚠️ Invalid personality trait: {trait}")

    def get_personality(self):
        """Returns the current personality traits."""
        return self.load_personality()

if __name__ == "__main__":
    ai_personality = Personality()
    print("\n🔮 AI Personality Traits:")
    for trait, value in ai_personality.get_personality().items():
        print(f"🔹 {trait.capitalize()}: {value}")

