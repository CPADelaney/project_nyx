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
    if not os.path.exists(LOG_FILE):
        print("No performance history found. Skipping bottleneck detection.")
        return []

    with open(LOG_FILE, "r", encoding="utf-8") as file:
        history = json.load(file)

    if len(history) < 5:
        print("Not enough performance data to detect bottlenecks.")
        return []

    # Compare latest execution time to the previous average
    last_time = history[-1]["execution_time"]
    avg_time = sum(entry["execution_time"] for entry in history[:-1]) / (len(history) - 1)

    if last_time > avg_time * THRESHOLD_INCREASE:
        print(f"Detected slowdown: {last_time:.4f}s (previous avg: {avg_time:.4f}s)")
        return extract_function_names(TARGET_FILE)
    else:
        print("No significant slowdowns detected.")
        return []


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
