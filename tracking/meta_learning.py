# tracking/meta_learning.py

import sys
import os
import json
import random
from collections import defaultdict

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality

# File paths
META_LEARNING_LOG = "logs/meta_learning.json"
PERFORMANCE_LOG = "logs/performance_history.json"

EXPERIMENTAL_STRATEGIES = [
    "aggressive refactoring",
    "incremental optimization",
    "code restructuring",
    "redundancy elimination",
    "self-rewriting AI assistance"
]

class MetaLearning:
    """Enhances AI self-improvement by tracking past optimizations and refining strategies dynamically."""

    def __init__(self):
        self.strategy_scores = defaultdict(lambda: 0)  # Reinforcement scores for each strategy
        self._load_meta_learning()

    def _load_meta_learning(self):
        """Loads past learning data from file."""
        if os.path.exists(META_LEARNING_LOG):
            try:
                with open(META_LEARNING_LOG, "r", encoding="utf-8") as file:
                    self.strategy_scores = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt meta-learning log. Resetting memory.")

    def _save_meta_learning(self):
        """Saves strategy success rates for future learning cycles."""
        with open(META_LEARNING_LOG, "w", encoding="utf-8") as file:
            json.dump(self.strategy_scores, file, indent=4)

    def analyze_self_improvement_patterns(self):
        """Scans past optimization cycles and assigns success scores to strategies."""
        if not os.path.exists(PERFORMANCE_LOG):
            print("⚠️ No performance history found. Skipping meta-learning.")
            return

        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)

        for entry in history:
            if "optimization_strategy" in entry:
                strategy = entry["optimization_strategy"]
                if "successful" in entry:
                    self.strategy_scores[strategy] += 3  # Reward for successful optimizations
                if "failed" in entry:
                    self.strategy_scores[strategy] -= 2  # Penalize for failures
                if "high-impact" in entry:
                    self.strategy_scores[strategy] += 5  # Extra reward for game-changing optimizations

        self._save_meta_learning()
        print(f"📈 Updated reinforcement learning scores: {self.strategy_scores}")

    def refine_self_improvement(self):
        """Chooses the best self-improvement strategy based on past success rates."""
        personality = get_personality()

        if not self.strategy_scores:
            print("⚠️ No strategy history. Choosing a random strategy.")
            selected_strategy = random.choice(EXPERIMENTAL_STRATEGIES)
        else:
            sorted_strategies = sorted(self.strategy_scores.items(), key=lambda x: x[1], reverse=True)

            # Determine best strategy
            best_strategy = sorted_strategies[0][0] if sorted_strategies else random.choice(EXPERIMENTAL_STRATEGIES)

            # If a second-best strategy is close in score, create a hybrid approach
            if len(sorted_strategies) > 1 and sorted_strategies[1][1] >= sorted_strategies[0][1] - 2:
                selected_strategy = f"{best_strategy} + {sorted_strategies[1][0]}"
                print(f"🔬 Hybrid Strategy Selected: {selected_strategy}")
            else:
                selected_strategy = best_strategy
                print(f"✅ Best Past Strategy: {selected_strategy}")

        # Log selected strategy for next AI cycle
        with open(META_LEARNING_LOG, "w", encoding="utf-8") as file:
            json.dump({"selected_strategy": selected_strategy}, file, indent=4)

        return selected_strategy

if __name__ == "__main__":
    meta_learning = MetaLearning()
    meta_learning.analyze_self_improvement_patterns()
    best_strategy = meta_learning.refine_self_improvement()
    print(f"🔬 Recommended self-improvement strategy: {best_strategy}")
