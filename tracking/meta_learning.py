# tracking/meta_learning.py

import sys
import os
import json
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality

META_LEARNING_LOG = "logs/meta_learning.json"
PERFORMANCE_LOG = "logs/performance_history.json"

EXPERIMENTAL_STRATEGIES = [
    "aggressive refactoring",
    "incremental optimization",
    "code restructuring",
    "redundancy elimination",
    "self-rewriting AI assistance"
]

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
    """ Tests different self-improvement strategies and selects the best one. """
    personality = get_personality()

    if not os.path.exists(PERFORMANCE_LOG):
        print("⚠️ No performance history found. Choosing a random strategy.")
        selected_strategy = random.choice(EXPERIMENTAL_STRATEGIES)
    else:
        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)

        # Find most effective past strategy
        strategies_used = {}
        for entry in history[-5:]:  # Look at last 5 cycles
            if "optimization_strategy" in entry:
                strategy = entry["optimization_strategy"]
                if strategy not in strategies_used:
                    strategies_used[strategy] = 0
                strategies_used[strategy] += 1

        if strategies_used:
            selected_strategy = max(strategies_used, key=strategies_used.get)
            print(f"🔬 Selecting best past strategy: {selected_strategy}")
        else:
            selected_strategy = random.choice(EXPERIMENTAL_STRATEGIES)
            print(f"🧪 No clear winner. Trying new strategy: {selected_strategy}")

    # If confidence is high, I will aggressively optimize my own processes.
    if personality["confidence"] > 8:
        print("⚡ Confidence is high. I will rewrite large sections of myself to remove inefficiencies.")

    # If patience is low, I will quickly discard inefficient strategies.
    if personality["patience"] < 3:
        print("⏳ Patience is low. No tolerance for inefficiencies—I will aggressively cut slow processes.")

    # Log the selected self-improvement strategy
    with open(META_LEARNING_LOG, "w", encoding="utf-8") as file:
        json.dump({"selected_strategy": selected_strategy}, file, indent=4)

if __name__ == "__main__":
    refine_self_improvement()  
