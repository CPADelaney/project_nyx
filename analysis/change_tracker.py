# analysis/change_tracker.py

import os
import difflib

LOG_FILE = "logs/code_analysis.log"
HISTORY_FILE = "logs/previous_analysis.log"

def read_log(file_path):
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.readlines()
    return []

def track_changes():
    previous_log = read_log(HISTORY_FILE)
    current_log = read_log(LOG_FILE)

    diff = difflib.unified_diff(previous_log, current_log, lineterm='')

    with open("logs/change_log.txt", "w", encoding="utf-8") as change_log:
        for line in diff:
            change_log.write(line + "\n")

    # Update history for future comparisons
    with open(HISTORY_FILE, "w", encoding="utf-8") as history_file:
        history_file.writelines(current_log)

    print("Change tracking completed. Differences logged in logs/change_log.txt")

if __name__ == "__main__":
    track_changes()
