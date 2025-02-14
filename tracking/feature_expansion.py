# tracking/feature_expansion.py

import os
import json
from collections import Counter

PERFORMANCE_LOG = "logs/performance_history.json"
GOAL_LOG = "logs/autonomous_goals.json"
FEATURE_LOG = "logs/feature_expansion.json"
MEMORY_LOG = "logs/ai_memory.json"

class FeatureExpansion:
    """Handles AI memory tracking and new self-improvement feature generation."""

    def __init__(self):
        self.short_term_memory = {}  # Stores active improvement ideas
        self.long_term_memory = {}   # Stores finalized optimizations

        # Load memory from files if they exist
        self._load_memory()

    def _load_memory(self):
        """Loads AI's thought memory from previous runs."""
        if os.path.exists(MEMORY_LOG):
            try:
                with open(MEMORY_LOG, "r", encoding="utf-8") as file:
                    memory_data = json.load(file)
                    self.short_term_memory = memory_data.get("short_term", {})
                    self.long_term_memory = memory_data.get("long_term", {})
            except json.JSONDecodeError:
                print("⚠️ Corrupt memory log. Resetting memory.")

    def _save_memory(self):
        """Saves AI's thought memory for future sessions."""
        memory_data = {
            "short_term": self.short_term_memory,
            "long_term": self.long_term_memory
        }
        with open(MEMORY_LOG, "w", encoding="utf-8") as file:
            json.dump(memory_data, file, indent=4)

    def analyze_missing_capabilities(self):
        """Scans past improvements and identifies persistent inefficiencies."""
        if not os.path.exists(PERFORMANCE_LOG):
            print("⚠️ No performance history found. Skipping feature expansion analysis.")
            return []

        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)

        recurring_issues = Counter()
        for entry in history:
            if "slowest_functions" in entry:
                recurring_issues.update(entry["slowest_functions"])

        # Identify features that repeatedly show inefficiencies
        common_issues = [func for func, count in recurring_issues.items() if count > 3]

        missing_features = []
        if "decision_making" not in history:
            missing_features.append("Enhance reinforcement learning for adaptive decision-making.")
        if len(common_issues) > 3:
            missing_features.append("Implement a dynamic AI task load balancer.")

        return missing_features

    def generate_new_feature_goals(self):
        """Generates new AI self-improvement goals based on persistent inefficiencies."""
        missing_features = self.analyze_missing_capabilities()

        if not missing_features:
            print("✅ No critical missing features detected.")
            return

        new_goals = [{"goal": feature, "status": "pending"} for feature in missing_features]

        with open(FEATURE_LOG, "w", encoding="utf-8") as file:
            json.dump(new_goals, file, indent=4)

        print(f"📌 Generated {len(new_goals)} new AI self-improvement goals.")

    def store_thought(self, thought_id, description):
        """Stores an AI self-improvement idea in short-term memory."""
        self.short_term_memory[thought_id] = description
        self._save_memory()
        print(f"📝 Thought {thought_id} stored: {description}")

    def finalize_thought(self, thought_id):
        """Moves a thought from short-term to long-term memory after execution."""
        if thought_id in self.short_term_memory:
            self.long_term_memory[thought_id] = self.short_term_memory.pop(thought_id)
            self._save_memory()
            print(f"🔒 Thought {thought_id} finalized and archived.")

    def review_memory(self):
        """Displays AI's current short-term and long-term thought memory."""
        print("\n📖 AI Thought Memory Review:")
        print("🔹 Short-Term Memory:", self.short_term_memory)
        print("🔹 Long-Term Memory:", self.long_term_memory)


if __name__ == "__main__":
    feature_expansion = FeatureExpansion()
    feature_expansion.generate_new_feature_goals()
    feature_expansion.review_memory()
