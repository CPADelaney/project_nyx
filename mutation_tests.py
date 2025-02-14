# mutation_tests.py

import subprocess
import difflib
import os

ORIGINAL_FILE = "src/nyx_core.py"
MODIFIED_FILE = "logs/nyx_core_modified.py"
MODIFIED_FUNCTIONS = [f"logs/refactored_function_{i}.py" for i in range(10)]  # Adjust range as needed

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
    """ Benchmarks AI-modified functions against original ones """
    for modified_function in MODIFIED_FUNCTIONS:
        if not os.path.exists(modified_function):
            continue

        with open(modified_function, "r", encoding="utf-8") as file:
            function_code = file.read()

        # Execute AI-modified function and measure execution time
        exec_globals = {}
        exec(function_code, exec_globals)

        test_function = [name for name in exec_globals if name.startswith("test_")]
        if test_function:
            function_name = test_function[0]
            execution_time = timeit.timeit(f"{function_name}()", globals=exec_globals, number=100)
            print(f"Execution time for {modified_function}: {execution_time} seconds")

if __name__ == "__main__":
    compare_versions()
    if test_modified_code():
        subprocess.run(["mv", MODIFIED_FILE, ORIGINAL_FILE]) 
    test_function_performance()
