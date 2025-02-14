# tracking/performance_tracker.py

import os
import json
import subprocess
import time
import timeit

LOG_FILE = "logs/performance_history.json"
TARGET_FILE = "src/nyx_core.py"

def measure_execution_time():
    """ Measures execution time of nyx_core.py in a controlled subprocess """
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
    """ Stores the latest execution time in a performance history log. """
    if new_time is None:
        print("Skipping performance logging due to execution failure.")
        return

    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
    else:
        history = []

    history.append({"timestamp": time.time(), "execution_time": new_time})

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

    print(f"Logged execution time: {new_time:.4f} seconds")

if __name__ == "__main__":
    execution_time = measure_execution_time()
    update_performance_log(execution_time)
