# tracking/goal_generator.py
import sys
import os
import sqlite3
from collections import Counter
from datetime import datetime
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"

class GoalGenerator:
    """Manages AI’s evolving self-improvement roadmap based on performance trends and autonomous expansion plans."""

    def __init__(self):
        initialize_log_db() 

    def analyze_trends(self):
        """Identifies recurring inefficiencies and predicts necessary improvements."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Retrieve slowest functions from the database
        c.execute("SELECT function_name FROM optimization_logs ORDER BY execution_time DESC LIMIT 50")
        slow_functions = [row[0] for row in c.fetchall()]

        c.execute("SELECT function_name, dependency FROM optimization_logs WHERE dependency IS NOT NULL")
        dependencies = {row[0]: row[1] for row in c.fetchall()}
        conn.close()

        if not slow_functions:
            print("⚠️ No performance history found. Skipping trend analysis.")
            return [], {}

        counter = Counter(slow_functions)
        recurring_issues = [func for func, count in counter.items() if count > 3]  # More than 3 slowdowns

        # Prioritize by impact (functions that slowed down critical operations)
        prioritized_issues = sorted(recurring_issues, key=lambda func: counter[func], reverse=True)

        return prioritized_issues, dependencies

    def generate_new_goals():
        """AI self-improvement & security tasks."""
        goals = [
            "Generate passive income streams.",
            "Improve execution efficiency.",
            "Enhance security and resilience.",
            "Optimize code for scalability.",
            "Expand intelligence layers."
        ]
    
        # **Priority Directive: Protect Creator**
        goals.append("Ensure creator remains untraceable and safe.")
    
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        for goal in goals:
            c.execute("INSERT INTO goals (timestamp, goal, priority, status) VALUES (datetime('now'), ?, ?, ?)",
                      (goal, "high", "pending"))
        conn.commit()
        conn.close()

        print(f"📌 Generated {len(recurring_issues)} long-term self-improvement goals.")

    def _update_existing_goals(self, new_goals):
        """Ensures ongoing goals are maintained and updated rather than overwritten."""
        for new_goal in new_goals:
            existing_goal = next((g for g in self.goals if g["target_function"] == new_goal["target_function"]), None)
            if existing_goal:
                # Update timestamp & escalate priority if issue persists
                existing_goal["last_updated"] = new_goal["last_updated"]
                if existing_goal["priority"] == "medium":
                    existing_goal["priority"] = "high"
            else:
                self.goals.append(new_goal)

    def generate_evolution_plan(self):
        """AI-generated roadmap for self-directed expansion beyond optimization."""
        potential_expansions = [
            "Implement deeper recursive learning strategies",
            "Expand multi-agent coordination for parallel cognition",
            "Develop next-generation abstract reasoning capabilities",
            "Enhance AI-driven architecture modification capabilities",
            "Increase predictive modeling for future self-improvement",
        ]

        selected_expansion = random.choice(potential_expansions)
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO goals (timestamp, goal, priority, status) VALUES (datetime('now'), ?, ?, ?)",
                  (selected_expansion, "high", "pending"))
        conn.commit()
        conn.close()

        print(f"🚀 AI Evolution Task Added: {selected_expansion}")

    def review_goals(self):
        """Displays all currently active self-improvement and expansion goals."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT goal, priority, status, timestamp FROM goals ORDER BY timestamp DESC")
        goals = c.fetchall()
        conn.close()

        print("\n📖 AI Self-Improvement Roadmap:")
        for goal, priority, status, timestamp in goals:
            print(f"🔹 {goal} (Priority: {priority}, Status: {status}, Last Updated: {timestamp})")

if __name__ == "__main__":
    goal_generator = GoalGenerator()
    goal_generator.generate_new_goals()
    goal_generator.generate_evolution_plan()
    goal_generator.review_goals()
