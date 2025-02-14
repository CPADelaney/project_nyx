# mutation_tests.py

import subprocess
import json
import difflib
import os
import timeit
import shutil

ORIGINAL_FILE = "src/nyx_core.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"
MODIFIED_FUNCTIONS = [f"logs/refactored_function_{i}.py" for i in range(10)]  # Adjust range as needed
LOG_FILE = "logs/performance_history.json"
THRESHOLD = 0.98  # Only apply changes that perform at least 98% as well as previous versions


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


def test_function_performance():
    """ Benchmarks AI-modified functions against original ones in a safe environment """
    for modified_function in MODIFIED_FUNCTIONS:
        if not os.path.exists(modified_function):
            continue

        # Write the AI-generated function to a temp script
        temp_script = "logs/temp_function_test.py"
        shutil.copy(modified_function, temp_script)

        # Measure execution time of the AI-refactored function
        execution_time = timeit.timeit(stmt=f"subprocess.run(['python3', '{temp_script}'])", number=10)

        print(f"Execution time for {modified_function}: {execution_time:.4f} seconds")


def get_latest_performance():
    """ Retrieves the last two recorded execution times to compare performance """
    if not os.path.exists(LOG_FILE):
        return None, None

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)

    if len(history) < 2:
        return None, None

    return history[-2]["execution_time"], history[-1]["execution_time"]


def decide_if_changes_are_kept():
    """ Compares AI-generated code with previous versions and decides whether to keep it """
    prev_time, new_time = get_latest_performance()

    if prev_time is None or new_time is None:
        print("Not enough performance data yet. Keeping changes.")
        return True

    performance_ratio = new_time / prev_time

    if performance_ratio <= THRESHOLD:
        print(f"AI changes performed worse ({performance_ratio * 100:.2f}% efficiency). Reverting to previous version.")
        return False
    else:
        print(f"AI changes improved performance ({performance_ratio * 100:.2f}% efficiency). Keeping changes.")
        return True


if __name__ == "__main__":
    compare_versions()

    if test_modified_code():
        shutil.move(MODIFIED_FILE, ORIGINAL_FILE)  # Cross-platform safe move

    test_function_performance()

    if not decide_if_changes_are_kept():
        print("Reverting to previous version of nyx_core.py.")
        subprocess.run(["git", "checkout", "HEAD~1", "--", "src/nyx_core.py"])
        subprocess.run(["git", "commit", "-m", "Reverted AI changes due to performance drop"])
        subprocess.run(["git", "push", "origin", "main"])
