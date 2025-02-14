# analysis/self_optimizer.py

import os
import re

LOG_FILE = "logs/code_analysis.log"
OPTIMIZATION_SUGGESTIONS = "logs/optimization_suggestions.txt"

def suggest_improvements():
    with open(LOG_FILE, "r", encoding="utf-8") as log_file:
        analysis = log_file.readlines()

    suggestions = []

    for line in analysis:
        # Detect long functions (complexity issue)
        if "Complex Functions:" in line and line.strip() != "Complex Functions:":
            suggestions.append("⚠ Consider refactoring long functions to improve readability and maintainability.\n")

        # Detect unused imports
        if "Unused Imports:" in line and line.strip() != "Unused Imports:":
            suggestions.append("⚠ Remove unused imports to streamline code execution.\n")

    # Write suggestions to file
    with open(OPTIMIZATION_SUGGESTIONS, "w", encoding="utf-8") as suggestion_file:
        suggestion_file.writelines(suggestions)

    print(f"Optimization suggestions generated: {len(suggestions)} issues found.")

if __name__ == "__main__":
    suggest_improvements()
