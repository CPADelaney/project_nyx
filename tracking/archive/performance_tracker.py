# tracking/performance_tracker.py
import sys
import os
import sqlite3
import subprocess
import time
import timeit
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
TARGET_FILE = "src/nyx_core.py"

def ensure_performance_log():
    """ Ensures performance log exists and is properly formatted. """
    if not os.path.exists(PERFORMANCE_LOG):
        with open(PERFORMANCE_LOG, "w", encoding="utf-8") as file:
            json.dump([], file, indent=4)  # ✅ Ensure a valid JSON list structure
        print("✅ Initialized performance history log.")

ensure_performance_log()

def measure_execution_time():
    """Measures execution time of nyx_core.py in a controlled subprocess."""
    start_time = time.time()

    try:
        result = subprocess.run(["python3", TARGET_FILE], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Warning: nyx_core.py execution failed.\n{result.stderr}")
            return None  # Skip logging if execution fails

    except Exception as e:
        print(f"Error while executing nyx_core.py: {e}")
        return None

    execution_time = time.time() - start_time
    print(f"Execution time: {execution_time:.4f} seconds")
    return execution_time


def update_performance_log(new_time):
    """Stores the latest execution time in the performance history database."""
    if new_time is None:
        print("Skipping performance logging due to execution failure.")
        return

    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
              ("execution_time", f"{new_time:.4f} seconds"))
    conn.commit()
    conn.close()

    print(f"Logged execution time: {new_time:.4f} seconds")


if __name__ == "__main__":
    initialize_log_db()  # Ensure database is initialized
    execution_time = measure_execution_time()
    update_performance_log(execution_time)
