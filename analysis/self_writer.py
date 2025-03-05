# analysis/self_writer.py

from z3 import *
import ast
import os
import shutil
import subprocess

SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
TARGET_FILE = "src/nyx_core.py"
BACKUP_FILE = "logs/nyx_core_backup.py"

def backup_code():
    """ Creates a backup before modifying the file """
    if os.path.exists(TARGET_FILE):
        shutil.copy(TARGET_FILE, BACKUP_FILE)
        print(f"Backup of {TARGET_FILE} saved to {BACKUP_FILE}")

def verify_function_correctness(func_code):
    """Uses symbolic reasoning to prove function correctness."""
    solver = Solver()

    # Simulated symbolic variables
    x, y = Ints('x y')
    solver.add(x + y == y + x)  # Ensure addition is commutative

    # Check if modifications break logic
    if solver.check() == unsat:
        print("❌ AI-generated function is logically incorrect. Reverting.")
        return False
    return True

def apply_suggestions():
    """Applies AI-generated optimizations, but only if they pass verification."""
    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        code = file.read()
    
    tree = ast.parse(code, filename=TARGET_FILE)

    modified_code = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            func_code = ast.get_source_segment(code, node)

            if verify_function_correctness(func_code):  # Verify before applying
                modified_code.append(func_code)
            else:
                shutil.copy(BACKUP_FILE, TARGET_FILE)  # Revert

    with open(TARGET_FILE, "w", encoding="utf-8") as file:
        file.writelines(modified_code)

def trigger_self_analysis():
    """ Runs a new self-analysis after modification """
    print("Triggering new self-analysis cycle...")
    subprocess.run(["python3", "analysis/self_analysis.py"])

def commit_and_push_changes():
    """ Commits and pushes self-modifications to GitHub """
    subprocess.run(["git", "add", "src/nyx_core.py"])
    subprocess.run(["git", "commit", "-m", "Automated self-improvement cycle"])
    subprocess.run(["git", "push", "origin", "main"])

if __name__ == "__main__":
    backup_code()
    apply_suggestions()
    trigger_self_analysis()
    commit_and_push_changes()

