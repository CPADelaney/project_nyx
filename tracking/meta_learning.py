# tracking/meta_learning.py
import sys
import os
import random
import json
from collections import defaultdict
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.database_manager import get_log_db_manager
from core.utility_functions import get_personality
from core.error_framework import safe_execute, safe_db_execute

# Get database manager
db_manager = get_log_db_manager()

# File paths
META_LEARNING_FILE = "logs/meta_learning.json"

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
        # Initialize strategy tracking
        self.strategy_scores = defaultdict(lambda: {"success": 0, "failures": 0, "impact": 0})
        
        # Ensure database table exists
        self._initialize_database()
        
        # Load existing strategy scores
        self._load_strategy_scores()

    def _initialize_database(self):
        """Ensures the meta_learning table exists in the database."""
        db_manager.execute_script('''
            CREATE TABLE IF NOT EXISTS meta_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                strategy TEXT UNIQUE,
                success INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                impact INTEGER DEFAULT 0
            )
        ''')

    def _load_strategy_scores(self):
        """Loads strategy scores from the database."""
        strategies = db_manager.execute(
            "SELECT strategy, success, failures, impact FROM meta_learning"
        )
        
        for strategy in strategies:
            self.strategy_scores[strategy['strategy']] = {
                "success": strategy['success'],
                "failures": strategy['failures'],
                "impact": strategy['impact']
            }
    
    @safe_execute
    def analyze_self_improvement_patterns(self):
        """Scans past optimization cycles and assigns weighted success scores to strategies."""
        # Retrieve past optimizations
        history = db_manager.execute("""
            SELECT event_type, target_function, details 
            FROM ai_self_modifications 
            ORDER BY timestamp DESC
            LIMIT 100
        """)

        if not history:
            print("⚠️ No performance history found. Skipping meta-learning.")
            return {"success": False, "message": "No performance history found"}

        # Process each historical record
        for record in history:
            event_type = record['event_type']
            target_function = record['target_function']
            details = record['details']
            
            # Extract strategy from details (simplified)
            strategy = None
            for exp_strategy in EXPERIMENTAL_STRATEGIES:
                if exp_strategy.lower() in details.lower():
                    strategy = exp_strategy
                    break
                    
            if not strategy:
                # If no matching strategy found, use a generic one
                strategy = "general optimization"
                
            # Determine success and impact based on event_type
            if "success" in event_type.lower():
                self.strategy_scores[strategy]["success"] += 1
                self.strategy_scores[strategy]["impact"] += 1
            elif "failure" in event_type.lower():
                self.strategy_scores[strategy]["failures"] += 1
            
        # Save scores back to database
        for strategy, scores in self.strategy_scores.items():
            db_manager.execute_update("""
                INSERT INTO meta_learning (strategy, success, failures, impact)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(strategy) DO UPDATE SET
                    success = ?,
                    failures = ?,
                    impact = ?
            """, (
                strategy, scores["success"], scores["failures"], scores["impact"],
                scores["success"], scores["failures"], scores["impact"]
            ))
        
        # Save to JSON file
        try:
            with open(META_LEARNING_FILE, "w") as f:
                json.dump(
                    {
                        "strategies": {
                            k: v for k, v in self.strategy_scores.items()
                        }
                    }, 
                    f, 
                    indent=4
                )
        except Exception as e:
            print(f"Error saving meta-learning data to JSON: {e}")

        print(f"📈 Updated reinforcement learning scores for {len(self.strategy_scores)} strategies")
        return {"success": True, "strategies": self.strategy_scores}

    @safe_execute
    def weighted_decision_matrix(self):
        """Evaluates multiple strategies simultaneously using weighted scoring."""
        if not self.strategy_scores:
            return []

        scored_strategies = {}
        for strategy, scores in self.strategy_scores.items():
            success_score = scores["success"] * 1.5  # Prioritize successful strategies
            failure_penalty = scores["failures"] * -2  # Penalize failed attempts
            impact_bonus = scores["impact"] * 2  # Prioritize high-impact changes

            total_score = success_score + failure_penalty + impact_bonus
            scored_strategies[strategy] = total_score

        # Sort by score in descending order
        sorted_strategies = sorted(scored_strategies.items(), key=lambda x: x[1], reverse=True)
        return sorted_strategies

    @safe_execute
    def refine_self_improvement(self):
        """Chooses the best self-improvement strategy based on multi-variable weighted decision-making."""
        try:
            personality = get_personality()
        except Exception:
            # Fallback personality traits if function fails
            personality = {"adaptability": 7, "curiosity": 8}
            
        scored_strategies = self.weighted_decision_matrix()

        if not scored_strategies:
            print("⚠️ No strategy history. Choosing a random strategy.")
            selected_strategy = random.choice(EXPERIMENTAL_STRATEGIES)
        else:
            # Select top-ranked strategy
            best_strategy = scored_strategies[0][0]

            # If another strategy is close in score, consider merging them for a hybrid approach
            # but only if the AI has high adaptability
            if len(scored_strategies) > 1 and abs(scored_strategies[0][1] - scored_strategies[1][1]) < 2:
                # Check personality - if adaptable, try a hybrid approach
                if personality.get("adaptability", 5) > 6:
                    selected_strategy = f"{best_strategy} + {scored_strategies[1][0]}"
                    print(f"🔬 Hybrid Strategy Selected: {selected_strategy}")
                else:
                    selected_strategy = best_strategy
                    print(f"✅ Best Strategy Selected: {selected_strategy}")
            else:
                selected_strategy = best_strategy
                print(f"✅ Best Strategy Selected: {selected_strategy}")

        # Store the selected strategy in SQLite
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO meta_learning (strategy, success, failures, impact) 
            VALUES (?, ?, ?, ?) 
            ON CONFLICT(strategy) DO UPDATE SET success = success + 1
        """, (selected_strategy, 1, 0, 1))
        conn.commit()
        conn.close()

        return {
            "success": True,
            "strategy": selected_strategy,
            "explanation": f"Strategy '{selected_strategy}' selected based on past performance metrics"
        }

# Fix duplicate __init__ issue
if __name__ == "__main__":
    meta_learning = MetaLearning()
    meta_learning.analyze_self_improvement_patterns()
    best_strategy = meta_learning.refine_self_improvement()
    print(f"Selected strategy: {best_strategy}")
