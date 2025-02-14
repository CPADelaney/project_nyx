# tracking/performance_tracker.py

import os
import json
import timeit

LOG_FILE = "logs/performance_history.json"
TARGET_FILE = "src/nyx_core.py"

def measure_execution_time():
    """ Measures the execution time of nyx_core.py to track improvements over time. """
    execution_time = timeit.timeit("exec(open(TARGET_FILE).read())", globals=globals(), number=10)
    
    return execution_time

def update_performance_log(new_time):
    """ Stores the latest execution time in a performance history log. """
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding="utf-8") as file:
            history = json.load(file)
    else:
        history = []

    history.append({"timestamp": time.time(), "execution_time": new_time})

    with open(LOG_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4)

    print(f"Logged execution time: {new_time} seconds")

if __name__ == "__main__":
    execution_time = measure_execution_time()
    update_performance_log(execution_time)
