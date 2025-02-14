# tracking/bottleneck_detector.py

import os
import json
import ast

LOG_FILE = "logs/performance_history.json"
TARGET_FILE = "src/nyx_core.py"
BOTTLENECK_LOG = "logs/bottleneck_functions.json"
THRESHOLD_INCREASE = 1.10  # 10% increase in execution time triggers refactoring


def get_worst_performing_functions():
    """ Identifies the slowest functions based on past execution times """
    if not os.path.exists(PERFORMANCE_LOG):
        print("⚠️ No performance history found. Skipping bottleneck detection.")
        return []

    try:
        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)
            if not history:  # ✅ Fix: Check if JSON is empty
                print("⚠️ Performance history is empty. Skipping bottleneck detection.")
                return []
    except json.JSONDecodeError:
        print("❌ Error: Performance history file is corrupt. Skipping bottleneck detection.")
        return []

    slow_functions = []
    for entry in history:
        if "slowest_functions" in entry:
            slow_functions.extend(entry["slowest_functions"])

    counter = Counter(slow_functions)
    recurring_issues = [func for func, count in counter.items() if count > 3]  # More than 3 slowdowns

    with open(BOTTLENECK_LOG, "w", encoding="utf-8") as file:
        json.dump(recurring_issues, file, indent=4)

    print(f"✅ Logged bottleneck functions for optimization: {recurring_issues}")
    return recurring_issues

def extract_function_names(file_path):
    """ Parses function names from the source code for targeted optimization """
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    with open(BOTTLENECK_LOG, "w", encoding="utf-8") as file:
        json.dump(functions, file, indent=4)

    print(f"Logged bottleneck functions for optimization: {functions}")
    return functions


if __name__ == "__main__":
    get_worst_performing_functions()
