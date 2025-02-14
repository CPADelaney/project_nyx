# tracking/goal_generator.py

import os
import json
from collections import Counter
from datetime import datetime, timedelta

PERFORMANCE_LOG = "logs/performance_history.json"
BOTTLENECK_LOG = "logs/bottleneck_functions.json"
GOAL_LOG = "logs/autonomous_goals.json"

class GoalGenerator:
    """Manages AI’s evolving self-improvement roadmap based on performance trends."""

    def __init__(self):
        self.goals = []
        self._load_existing_goals()

    def _load_existing_goals(self):
        """Loads previous self-improvement goals to maintain long-term tracking."""
        if os.path.exists(GOAL_LOG):
            try:
                with open(GOAL_LOG, "r", encoding="utf-8") as file:
                    self.goals = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt goal log detected. Resetting.")

    def analyze_trends(self):
        """Identifies recurring inefficiencies and prioritizes high-impact improvements."""
        if not os.path.exists(PERFORMANCE_LOG):
            print("⚠️ No performance history found. Skipping trend analysis.")
            return []

        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)

        slow_functions = []
        dependencies = {}  # Track which functions depend on others
        for entry in history:
            if "slowest_functions" in entry:
                slow_functions.extend(entry["slowest_functions"])
            if "dependency_links" in entry:
                dependencies.update(entry["dependency_links"])

        counter = Counter(slow_functions)
        recurring_issues = [func for func, count in counter.items() if count > 3]  # More than 3 slowdowns

        # Prioritize by impact (functions that slowed down critical operations)
        prioritized_issues = sorted(recurring_issues, key=lambda func: counter[func], reverse=True)

        return prioritized_issues, dependencies

    def generate_new_goals(self):
        """Creates evolving self-improvement goals based on recurring inefficiencies."""
        recurring_issues, dependencies = self.analyze_trends()

        if not recurring_issues:
            print("✅ No recurring inefficiencies detected. No new goals generated.")
            return

        new_goals = []
        for func in recurring_issues:
            goal = {
                "goal": f"Redesign {func} to improve execution efficiency",
                "target_function": func,
                "priority": "high" if func in dependencies else "medium",
                "dependency": dependencies.get(func, None),
                "last_updated": str(datetime.utcnow())
            }
            new_goals.append(goal)

        # Merge with existing goals to prevent redundant tasks
        self._update_existing_goals(new_goals)

        with open(GOAL_LOG, "w", encoding="utf-8") as file:
            json.dump(self.goals, file, indent=4)

        print(f"📌 Generated {len(new_goals)} long-term self-improvement goals.")

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

    def review_goals(self):
        """Displays all currently active self-improvement goals."""
        print("\n📖 AI Self-Improvement Roadmap:")
        for goal in self.goals:
            print(f"🔹 {goal['goal']} (Priority: {goal['priority']}, Last Updated: {goal['last_updated']})")

if __name__ == "__main__":
    goal_generator = GoalGenerator()
    goal_generator.generate_new_goals()
    goal_generator.review_goals()
