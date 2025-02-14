# analysis/change_tracker.py

import os
import difflib
import sqlite3
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"

def get_previous_log():
    """Fetches the last logged analysis from SQLite."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("SELECT details FROM performance_logs WHERE event_type='code_analysis' ORDER BY id DESC LIMIT 1")
    result = c.fetchone()
    conn.close()
    return result[0].splitlines() if result else []

def get_current_log():
    """Reads the latest code analysis log file."""
    if os.path.exists("logs/code_analysis.log"):
        with open("logs/code_analysis.log", "r", encoding="utf-8") as file:
            return file.readlines()
    return []

def track_changes():
    """Tracks changes in the code analysis log and logs differences to SQLite."""
    previous_log = get_previous_log()
    current_log = get_current_log()

    diff = list(difflib.unified_diff(previous_log, current_log, lineterm=''))
    diff_text = "\n".join(diff)

    if diff_text.strip():
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("code_analysis_diff", diff_text))
        conn.commit()
        conn.close()
        print("Change tracking completed. Differences logged in SQLite.")

    # Store the latest analysis in SQLite for future comparisons
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
              ("code_analysis", "\n".join(current_log)))
    conn.commit()
    conn.close()

if __name__ == "__main__":
    initialize_log_db()  # Ensure database is initialized
    track_changes()
