# /mutation_tests.py

import subprocess
import difflib
import os
import timeit
import shutil
import sqlite3
import psutil  # 🔥 NEW: To measure CPU & RAM usage
import signal
import time
from core.log_manager import initialize_log_db  # Ensure DB is initialized

# File Paths
ORIGINAL_FILE = "src/nyx_core.py"
BACKUP_DIR = "logs/rollback_snapshots/"
SANDBOX_FILE = "logs/nyx_core_sandbox.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"
LOG_DB = "logs/ai_logs.db"

# Performance Thresholds
ACCEPTABLE_SLOWDOWN = 1.05  # Allow a 5% slowdown
MAX_CPU_INCREASE = 10  # CPU usage should not increase by more than 10%
MAX_RAM_INCREASE = 15  # RAM usage should not increase by more than 15%

# Ensure rollback directory exists
os.makedirs(BACKUP_DIR, exist_ok=True)

def backup_code():
    """Creates a rollback snapshot before modifying nyx_core.py."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"nyx_core_backup_{timestamp}.py")

    if os.path.exists(ORIGINAL_FILE):
        shutil.copy(ORIGINAL_FILE, backup_path)
        print(f"✅ Backup saved: {backup_path}")

def compare_versions():
    """Compare AI-modified code with original and log differences to SQLite."""
    if not os.path.exists(MODIFIED_FILE):
        print(f"⚠️ Warning: {MODIFIED_FILE} does not exist. Skipping comparison.")
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
        print("🔍 Code differences logged.")

def sandbox_execution():
    """Runs AI-modified code in a sandboxed environment before applying it."""
    if not os.path.exists(MODIFIED_FILE):
        print(f"⚠️ No AI-modified file found. Skipping sandbox test.")
        return False

    shutil.copy(MODIFIED_FILE, SANDBOX_FILE)  # Copy modified code to a sandbox file

    print("🔬 Running AI-modified code in a sandbox...")
    
    try:
        process = subprocess.Popen(
            ["python3", SANDBOX_FILE],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid  # Ensure it runs as a separate process group
        )

        time.sleep(5)  # Give it a few seconds to detect crashes

        # Measure system resources
        cpu_usage = psutil.cpu_percent(interval=1)
        ram_usage = psutil.virtual_memory().percent

        if cpu_usage > MAX_CPU_INCREASE or ram_usage > MAX_RAM_INCREASE:
            print(f"⚠️ AI-modified code used too many resources! CPU: {cpu_usage}%, RAM: {ram_usage}%")
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Kill the sandbox process
            return False

        process.terminate()
        return True

    except Exception as e:
        print(f"❌ Sandbox execution failed: {e}")
        return False

def benchmark_performance():
    """Tests AI-modified code performance and decides if it should be kept."""
    print("⚡ Benchmarking AI-modified code...")

    old_time = timeit.timeit(lambda: subprocess.run(["python3", ORIGINAL_FILE], capture_output=True), number=5)
    new_time = timeit.timeit(lambda: subprocess.run(["python3", MODIFIED_FILE], capture_output=True), number=5)

    performance_ratio = new_time / old_time
    print(f"🔍 Execution time comparison: {old_time:.4f}s → {new_time:.4f}s")

    if performance_ratio > ACCEPTABLE_SLOWDOWN:
        print("❌ Performance worsened! Reverting to last known good version.")
        rollback()
        return False

    return True

def rollback():
    """Rolls back to the most recent valid backup."""
    backups = sorted(os.listdir(BACKUP_DIR), reverse=True)
    
    if not backups:
        print("⚠️ No rollback backups found!")
        return

    latest_backup = os.path.join(BACKUP_DIR, backups[0])
    shutil.copy(latest_backup, ORIGINAL_FILE)
    print(f"🔄 Reverted to last known good version: {latest_backup}")

def test_code_integrity():
    """Runs AI-modified code through tests to ensure functionality is preserved."""
    print("🔬 Running AI-modified unit tests...")

    result = subprocess.run(["python3", "-m", "unittest", "tests/self_test.py"], capture_output=True, text=True)

    if result.returncode == 0:
        print("✅ AI-modified code passed all tests!")
        return True
    else:
        print("❌ AI-modified code failed tests. Rolling back...")
        rollback()
        return False

def log_failed_attempts():
    """Logs failed modifications to prevent the AI from making the same mistake again."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
              ("failed_optimization", "AI attempted an optimization that failed performance benchmarks"))
    conn.commit()
    conn.close()
    print("📌 AI optimization failure logged.")

if __name__ == "__main__":
    initialize_log_db()

    backup_code()
    compare_versions()

    if sandbox_execution():
        if test_code_integrity():
            if benchmark_performance():
                print("🚀 AI optimization approved! Applying changes.")
                shutil.move(MODIFIED_FILE, ORIGINAL_FILE)
            else:
                log_failed_attempts()
        else:
            log_failed_attempts()
    else:
        print("❌ AI-modified code failed sandbox execution. Rolling back.")
        rollback()


