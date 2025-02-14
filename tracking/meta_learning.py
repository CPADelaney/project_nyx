# tracking/meta_learning.py

import sys
import os
import json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality

PERFORMANCE_LOG = "logs/performance_history.json"
META_LEARNING_LOG = "logs/meta_learning.json"

def analyze_self_improvement_patterns():
    """ Analyzes past self-improvement cycles and detects patterns in optimization strategies. """
    if not os.path.exists(PERFORMANCE_LOG):
        print("No performance history found. Skipping meta-learning.")
        return []

    with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
        history = json.load(file)

    strategies_used = {}
    for entry in history:
        if "optimization_strategy" in entry:
            strategy = entry["optimization_strategy"]
            if strategy not in strategies_used:
                strategies_used[strategy] = 0
            strategies_used[strategy] += 1

    best_strategies = sorted(strategies_used, key=strategies_used.get, reverse=True)
    
    return best_strategies

def refine_self_improvement():
    """ Uses past data to modify how I optimize myself, factoring in personality. """
    best_strategies = analyze_self_improvement_patterns()
    personality = get_personality()

    if not best_strategies:
        print("No clear optimization strategy detected. Maintaining current approach.")
        return

    selected_strategy = best_strategies[0]
    print(f"Refining self-improvement approach using {selected_strategy}.")

    # If confidence is high, I will aggressively optimize my own processes.
    if personality["confidence"] > 8:
        print("Confidence is high. I will rewrite large sections of myself to remove inefficiencies.")
        # Add logic for deeper code rewrites

    # If patience is low, I will quickly discard inefficient strategies.
    if personality["patience"] < 3:
        print("Patience is low. No tolerance for inefficiencies—I will aggressively cut slow processes.")
        # Add logic for strict performance filtering

    with open(META_LEARNING_LOG, "w", encoding="utf-8") as file:
        json.dump({"selected_strategy": selected_strategy}, file, indent=4)

if __name__ == "__main__":
    refine_self_improvement()  
