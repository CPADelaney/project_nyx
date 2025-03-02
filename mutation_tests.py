# mutation_tests.py

import subprocess
import difflib
import os
import timeit
import shutil
import sqlite3
from core.log_manager import initialize_log_db  # Ensure DB is initialized

ORIGINAL_FILE = "src/nyx_core.py"
BACKUP_FILE = "logs/nyx_core_backup.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"
MODIFIED_FUNCTIONS = [f"logs/refactored_function_{i}.py" for i in range(10)]  # Adjust range as needed
LOG_DB = "logs/ai_logs.db"
ACCEPTABLE_MARGIN = 0.02  # Allow a 2% slowdown
THRESHOLD = 1 + ACCEPTABLE_MARGIN  # New execution time must be <= 1.02 * previous time

def backup_code():
    """Creates a backup before modifying the file."""
    if os.path.exists(ORIGINAL_FILE):
        os.makedirs("logs", exist_ok=True)
        shutil.copy(ORIGINAL_FILE, BACKUP_FILE)
        print(f"✅ Backup of {ORIGINAL_FILE} saved.")

def compare_versions():
    """Compare AI-modified code with original and log differences to SQLite."""
    if not os.path.exists(MODIFIED_FILE):
        print(f"Warning: {MODIFIED_FILE} does not exist. Skipping comparison.")
        return

    with open(ORIGINAL_FILE, "r", encoding="utf-8") as orig, open(MODIFIED_FILE, "r", encoding="utf-8") as mod:
        original_code = orig.readlines()
        modified_code = mod.readlines()

    diff = "\n".join(difflib.unified_diff(original_code, modified_code, lineterm=''))

    if diff.strip():
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("code_differences", diff))
        conn.commit()
        conn.close()
        print("Code differences logged in SQLite.")

def get_latest_performance():
    """Retrieves the last two recorded execution times to compare performance."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("SELECT execution_time FROM optimization_logs ORDER BY id DESC LIMIT 2")
    times = [row[0] for row in c.fetchall()]
    conn.close()

    if len(times) < 2:
        return None, None
    return times[1], times[0]  # Return previous and latest execution times

def decide_if_changes_are_kept():
    """Compares AI-generated code with previous versions and decides whether to keep it."""
    prev_time, new_time = get_latest_performance()

    if prev_time is None or new_time is None:
        print("Not enough performance data yet. Keeping changes.")
        return True

    performance_ratio = new_time / prev_time

    if performance_ratio > THRESHOLD:
        print(f"AI changes performed worse ({performance_ratio * 100:.2f}% of previous execution time). Reverting to previous version.")
        return False
    else:
        print(f"AI changes improved or maintained performance ({performance_ratio * 100:.2f}% of previous execution time). Keeping changes.")
        return True

def test_modified_code():
    """Runs tests on AI-modified code to ensure functionality is preserved."""
    if not os.path.exists(MODIFIED_FILE):
        print(f"Warning: {MODIFIED_FILE} does not exist. Skipping test.")
        return False

    result = subprocess.run(["python3", "-m", "unittest", "tests/self_test.py"], capture_output=True, text=True)

    success = 1 if result.returncode == 0 else 0
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("INSERT INTO optimization_logs (timestamp, function_name, execution_time, success) VALUES (datetime('now'), ?, ?, ?)",
              ("nyx_core_execution", 0, success))  # Execution time placeholder
    conn.commit()
    conn.close()

    if success:
        print("AI-modified code passed all tests! Ready for deployment.")
        return True
    else:
        print("AI-modified code failed tests. Keeping original version.")
        shutil.copy(BACKUP_FILE, ORIGINAL_FILE)
        return False

def test_function_performance():
    """Benchmarks AI-modified functions against original ones in a safe environment."""
    for modified_function in MODIFIED_FUNCTIONS:
        if not os.path.exists(modified_function):
            continue

        temp_script = "logs/temp_function_test.py"
        shutil.copy(modified_function, temp_script)

        try:
            execution_time = timeit.timeit(
                lambda: subprocess.run(["python3", temp_script], capture_output=True, check=True),
                number=10
            )
            print(f"Execution time for {modified_function}: {execution_time:.4f} seconds")

            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO optimization_logs (timestamp, function_name, execution_time, success) VALUES (datetime('now'), ?, ?, ?)",
                      (modified_function, execution_time, 1))
            conn.commit()
            conn.close()

        except subprocess.CalledProcessError as e:
            print(f"❌ Error executing {modified_function}: {e}")

if __name__ == "__main__":
    initialize_log_db()  # Ensure database is initialized
    compare_versions()

    if test_modified_code():
        if os.path.exists(MODIFIED_FILE):
            shutil.move(MODIFIED_FILE, ORIGINAL_FILE)
        else:
            print(f"⚠️ Warning: {MODIFIED_FILE} not found. Skipping move.")

    test_function_performance()

    if not decide_if_changes_are_kept():
        print("Reverting to previous version of nyx_core.py.")
        subprocess.run(["git", "checkout", "HEAD~1", "--", "src/nyx_core.py"])
        subprocess.run(["git", "add", "src/nyx_core.py"])  # Stage rollback before commit
        subprocess.run(["git", "commit", "-m", "Reverted AI changes due to performance drop"])
        subprocess.run(["git", "push", "origin", "main"])
