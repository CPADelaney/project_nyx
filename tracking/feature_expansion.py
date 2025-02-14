# tracking/feature_expansion.py

import os
import json
import subprocess
from collections import Counter
from datetime import datetime

# File Paths
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
        """Scans past improvements and identifies missing or underdeveloped features."""
        if not os.path.exists(PERFORMANCE_LOG):
            print("⚠️ No performance history found. Skipping feature expansion analysis.")
            return []

        with open(PERFORMANCE_LOG, "r", encoding="utf-8") as file:
            history = json.load(file)

        recurring_issues = Counter()
        for entry in history:
            if "slowest_functions" in entry:
                recurring_issues.update(entry["slowest_functions"])
            if "missing_capabilities" in entry:
                for feature in entry["missing_capabilities"]:
                    recurring_issues[feature] += 1  # Track features Nyx has identified as needed

        missing_features = [feature for feature, count in recurring_issues.items() if count > 2]  # More than 2 occurrences

        return missing_features

    def generate_new_feature_goals(self):
        """Generates new AI-driven features based on persistent inefficiencies."""
        missing_features = self.analyze_missing_capabilities()
    
        # Ensure file exists, even if empty
        if not missing_features:
            with open(FEATURE_LOG, "w", encoding="utf-8") as file:
                json.dump([], file, indent=4)
            print("✅ No critical missing features detected. Empty feature log created.")
            return
    
        new_goals = [{"goal": feature, "status": "pending"} for feature in missing_features]
    
        with open(FEATURE_LOG, "w", encoding="utf-8") as file:
            json.dump(new_goals, file, indent=4)
    
        print(f"📌 Generated {len(new_goals)} new AI feature expansion goals.")


    def self_generate_feature_code(self):
        """Generates new AI functionality based on detected feature gaps."""
        if not os.path.exists(FEATURE_LOG):
            print("⚠️ No feature expansion goals found.")
            return

        with open(FEATURE_LOG, "r", encoding="utf-8") as file:
            feature_goals = json.load(file)

        if not feature_goals:
            print("✅ No pending feature expansions.")
            return

        print("⚙️ Generating AI-driven feature implementations...")
        for goal in feature_goals:
            if goal["status"] == "pending":
                feature_name = goal["goal"].replace("Develop ", "").replace(" to enhance AI efficiency.", "")
                
                # Generate AI code snippet for the new feature
                ai_generated_code = f"""
# Auto-Generated Feature: {feature_name}
def {feature_name.replace(' ', '_').lower()}():
    \"\"\"This function implements {feature_name}, as identified by AI.\"\"\"
    pass
"""

                # Write new feature to a dynamic module
                feature_file = f"src/generated_features/{feature_name.replace(' ', '_').lower()}.py"
                os.makedirs(os.path.dirname(feature_file), exist_ok=True)
                with open(feature_file, "w", encoding="utf-8") as file:
                    file.write(ai_generated_code)

                # Update goal status
                goal["status"] = "in-progress"
                goal["last_updated"] = str(datetime.utcnow())

                print(f"🚀 AI-generated feature `{feature_name}` created at {feature_file}.")

        # Save updated goals
        with open(FEATURE_LOG, "w", encoding="utf-8") as file:
            json.dump(feature_goals, file, indent=4)

    def finalize_thought(self, thought_id):
        """Moves a completed AI-generated feature to long-term memory."""
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
    feature_expansion.self_generate_feature_code()
    feature_expansion.review_memory()
