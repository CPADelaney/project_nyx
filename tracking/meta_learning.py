# tracking/meta_learning.py
import sys
import os
import sqlite3
import random
from collections import defaultdict
from core.log_manager import initialize_log_db  # Ensure DB is initialized
from core.personality import get_personality

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality

# File paths
LOG_DB = "logs/ai_logs.db"

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
        self.strategy_scores = defaultdict(lambda: {"success": 0, "failures": 0, "impact": 0})  # Multi-variable tracking
        self._load_meta_learning()
        initialize_log_db()  # Ensure the database is initialized

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
        """Scans past optimization cycles and assigns weighted success scores to strategies."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Retrieve past optimizations
        c.execute("SELECT strategy, success, failures, impact FROM meta_learning")
        history = c.fetchall()
        conn.close()

        if not history:
            print("⚠️ No performance history found. Skipping meta-learning.")
            return

        # Convert history into a dictionary of scores
        strategy_scores = defaultdict(lambda: {"success": 0, "failures": 0, "impact": 0})
        for strategy, success, failures, impact in history:
            strategy_scores[strategy]["success"] += success
            strategy_scores[strategy]["failures"] += failures
            strategy_scores[strategy]["impact"] += impact

        # Store updated scores back into SQLite
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for strategy, scores in strategy_scores.items():
            c.execute("""
                INSERT INTO meta_learning (strategy, success, failures, impact) 
                VALUES (?, ?, ?, ?)
                ON CONFLICT(strategy) DO UPDATE SET 
                success = excluded.success,
                failures = excluded.failures,
                impact = excluded.impact
            """, (strategy, scores["success"], scores["failures"], scores["impact"]))
        conn.commit()
        conn.close()

        print(f"📈 Updated reinforcement learning scores: {strategy_scores}")

    def weighted_decision_matrix(self):
        """Evaluates multiple strategies simultaneously using weighted scoring."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT strategy, success, failures, impact FROM meta_learning")
        history = c.fetchall()
        conn.close()

        if not history:
            return []

        scored_strategies = {}
        for strategy, success, failures, impact in history:
            success_score = success * 1.5  # Prioritize successful strategies
            failure_penalty = failures * -2  # Penalize failed attempts
            impact_bonus = impact * 2  # Prioritize high-impact changes

            total_score = success_score + failure_penalty + impact_bonus
            scored_strategies[strategy] = total_score

        return sorted(scored_strategies.items(), key=lambda x: x[1], reverse=True)

    def refine_self_improvement(self):
        """Chooses the best self-improvement strategy based on multi-variable weighted decision-making."""
        personality = get_personality()
        scored_strategies = self.weighted_decision_matrix()

        if not scored_strategies:
            print("⚠️ No strategy history. Choosing a random strategy.")
            selected_strategy = random.choice(EXPERIMENTAL_STRATEGIES)
        else:
            # Select top-ranked strategy
            best_strategy = scored_strategies[0][0]

            # If another strategy is close in score, merge them for a hybrid approach
            if len(scored_strategies) > 1 and abs(scored_strategies[0][1] - scored_strategies[1][1]) < 2:
                selected_strategy = f"{best_strategy} + {scored_strategies[1][0]}"
                print(f"🔬 Hybrid Strategy Selected: {selected_strategy}")
            else:
                selected_strategy = best_strategy
                print(f"✅ Best Strategy Selected: {selected_strategy}")

        # Store the selected strategy in SQLite
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO meta_learning (strategy, success, failures, impact) VALUES (?, ?, ?, ?) ON CONFLICT(strategy) DO UPDATE SET success = success + 1",
                  (selected_strategy, 1, 0, 1))
        conn.commit()
        conn.close()

        return selected_strategy

if __name__ == "__main__":
    meta_learning = MetaLearning()
    meta_learning.analyze_self_improvement_patterns()
    best_strategy = meta_learning.refine_self_improvement()
    print(f"🔬 Recommended self-improvement strategy: {best_strategy}")
