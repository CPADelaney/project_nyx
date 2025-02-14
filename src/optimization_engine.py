# src/optimization_engine.py

import ast
import os
import shutil
import subprocess

TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
ROLLBACK_DIR = "logs/rollback_snapshots/"

class OptimizationEngine:
    """Enhances AI-driven code optimization and architecture modifications."""

    def __init__(self):
        self.issues = []

    def create_rollback_snapshot(self):
        """Creates a rollback snapshot before making modifications."""
        if not os.path.exists(ROLLBACK_DIR):
            os.makedirs(ROLLBACK_DIR)

        snapshot_path = os.path.join(ROLLBACK_DIR, "nyx_core_backup.py")
        shutil.copy2(TARGET_FILE, snapshot_path)
        print(f"📂 Rollback snapshot created: {snapshot_path}")

    def detect_inefficiencies(self, file_path):
        """Identifies code inefficiencies and structural improvement opportunities."""
        with open(file_path, "r", encoding="utf-8") as file:
            tree = ast.parse(file.read(), filename=file_path)

        self.issues = []

        # Detect unused imports
        imported_names = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        defined_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        unused_imports = [imp for imp in imported_names if imp not in defined_functions]

        if unused_imports:
            self.issues.append(f"Remove unused imports: {', '.join(unused_imports)}")

        # Detect inefficient loops
        for node in ast.walk(tree):
            if isinstance(node, (ast.For, ast.While)) and len(node.body) > 10:
                self.issues.append(f"Refactor long loop at line {node.lineno}")

        # Detect complex functions
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and len(node.body) > 20:
                self.issues.append(f"Refactor overly complex function `{node.name}` (line {node.lineno})")

        return self.issues

    def propose_modifications(self):
        """Generates AI-driven refactoring suggestions."""
        inefficiencies = self.detect_inefficiencies(TARGET_FILE)

        if not inefficiencies:
            print("✅ No major inefficiencies detected.")
            return []

        suggestions = []
        for issue in inefficiencies:
            if "Remove unused imports" in issue:
                suggestions.append("Optimize import statements to remove unused dependencies.")
            elif "Refactor long loop" in issue:
                suggestions.append("Rewrite loops using list comprehensions or generator functions.")
            elif "Refactor overly complex function" in issue:
                suggestions.append("Break down large functions into modular sub-functions.")

        with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as file:
            file.writelines(f"{s}\n" for s in suggestions)

        print(f"📌 {len(suggestions)} AI-driven refactoring suggestions generated.")
        return suggestions

    def apply_modifications(self):
        """Applies the proposed modifications using AI-driven self-rewriting."""
        self.create_rollback_snapshot()
        suggestions = self.propose_modifications()

        if not suggestions:
            print("✅ No modifications required.")
            return

        print("⚙️ Applying AI-driven optimizations...")
        for suggestion in suggestions:
            subprocess.run(["python3", "self_writing.py", "--execute-modification", suggestion])

        print("🚀 Code optimizations applied successfully.")

if __name__ == "__main__":
    optimizer = OptimizationEngine()
    optimizer.apply_modifications()
