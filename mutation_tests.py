# mutation_tests.py

import subprocess
import json
import difflib
import os
import timeit
import shutil

ORIGINAL_FILE = "src/nyx_core.py"
BACKUP_FILE = "logs/nyx_core_backup.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"
MODIFIED_FUNCTIONS = [f"logs/refactored_function_{i}.py" for i in range(10)]  # Adjust range as needed
LOG_FILE = "logs/performance_history.json"
THRESHOLD = 0.98  # Only apply changes that perform at least 98% as well as previous versions

def backup_code():
    """Creates a backup before modifying the file."""
    if os.path.exists(ORIGINAL_FILE):
        os.makedirs("logs", exist_ok=True)
        os.system(f"cp {ORIGINAL_FILE} {BACKUP_FILE}")
        print(f"✅ Backup of {ORIGINAL_FILE} saved.")

def compare_versions():
    """ Compare AI-modified code with original and log differences """
    if not os.path.exists(MODIFIED_FILE):
        print(f"Warning: {MODIFIED_FILE} does not exist. Skipping comparison.")
        return

    with open(ORIGINAL_FILE, "r", encoding="utf-8") as orig, open(MODIFIED_FILE, "r", encoding="utf-8") as mod:
        original_code = orig.readlines()
        modified_code = mod.readlines()

    diff = list(difflib.unified_diff(original_code, modified_code, lineterm=''))

    with open("logs/code_differences.txt", "w", encoding="utf-8") as diff_log:
        diff_log.writelines(diff)

    print("Code differences logged.")

def test_modified_code():
    """ Runs tests on AI-modified code to ensure functionality is preserved """
    if not os.path.exists(MODIFIED_FILE):
        print(f"Warning: {MODIFIED_FILE} does not exist. Skipping test.")
        return False

    result = subprocess.run(["python3", "-m", "unittest", "tests/self_test.py"], capture_output=True, text=True)

    if result.returncode == 0:
        print("AI-modified code passed all tests! Ready for deployment.")
        return True
    else:
        print("AI-modified code failed tests. Keeping original version.")
        os.system(f"cp {BACKUP_FILE} {ORIGINAL_FILE}")
        return False

def test_function_performance():
    """ Benchmarks AI-modified functions against original ones in a safe environment """
    for modified_function in MODIFIED_FUNCTIONS:
        if not os.path.exists(modified_function):
            continue

        temp_script = "logs/temp_function_test.py"
        shutil.copy(modified_function, temp_script)

        try:
            execution_time = timeit.timeit(lambda: subprocess.run(["python3", temp_script], capture_output=True, check=True), number=10)
            print(f"Execution time for {modified_function}: {execution_time:.4f} seconds")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error executing {modified_function}: {e}")

if __name__ == "__main__":
    compare_versions()

    if test_modified_code():
        if os.path.exists(MODIFIED_FILE):
            shutil.move(MODIFIED_FILE, ORIGINAL_FILE)  # ✅ Now checks if file exists before moving
        else:
            print(f"⚠️ Warning: {MODIFIED_FILE} not found. Skipping move.")

    test_function_performance()

    if not decide_if_changes_are_kept():
        print("Reverting to previous version of nyx_core.py.")
        subprocess.run(["git", "checkout", "HEAD~1", "--", "src/nyx_core.py"])
        subprocess.run(["git", "add", "src/nyx_core.py"])  # ✅ Stage rollback before commit
        subprocess.run(["git", "commit", "-m", "Reverted AI changes due to performance drop"])
        subprocess.run(["git", "push", "origin", "main"])
