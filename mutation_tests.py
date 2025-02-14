# mutation_tests.py

import subprocess
import difflib
import os

ORIGINAL_FILE = "src/nyx_core.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"

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
        return False

if __name__ == "__main__":
    compare_versions()
    if test_modified_code():
        subprocess.run(["mv", MODIFIED_FILE, ORIGINAL_FILE])  # Replace old file with improved version
