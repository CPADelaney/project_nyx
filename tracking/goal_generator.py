# tracking/goal_generator.py

import os
import json
from collections import Counter

PERFORMANCE_LOG = "logs/performance_history.json"
BOTTLENECK_LOG = "logs/bottleneck_functions.json"
GOAL_LOG = "logs/autonomous_goals.json"

def analyze_trends():
    """ Analyzes past optimizations to identify recurring inefficiencies """
    if not os.path.exists(PERFORMANCE_LOG):
        print("No performance history found. Skipping trend analysis.")
        return []

    with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
        history = json.load(file)

    slow_functions = []
    for entry in history:
        if "slowest_functions" in entry:
            slow_functions.extend(entry["slowest_functions"])

    counter = Counter(slow_functions)
    recurring_issues = [func for func, count in counter.items() if count > 3]  # More than 3 slowdowns

    return recurring_issues

def generate_new_goals():
    """ Generates self-improvement goals based on recurring inefficiencies """
    recurring_issues = analyze_trends()
    
    if not recurring_issues:
        print("No recurring inefficiencies detected. No new goals generated.")
        return

    new_goals = []
    for func in recurring_issues:
        new_goals.append({
            "goal": f"Redesign {func} to reduce execution time by 20%",
            "target_function": func
        })

    with open(GOAL_LOG, "w", encoding="utf-8") as file:
        json.dump(new_goals, file, indent=4)

    print(f"Generated {len(new_goals)} new self-improvement goals.")

if __name__ == "__main__":
    generate_new_goals()
