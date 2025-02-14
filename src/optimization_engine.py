# src/optimization_engine.py

import ast
import os

TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"

def detect_inefficiencies(file_path):
    """ Identify unused imports, inefficient loops, and overly complex functions. """
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    issues = []

    # Detect unused imports
    imported_names = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    defined_functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    unused_imports = [imp for imp in imported_names if imp not in defined_functions]

    if unused_imports:
        issues.append(f"⚠ Remove unused imports: {', '.join(unused_imports)}\n")

    # Detect inefficient loops
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)) and len(node.body) > 10:
            issues.append(f"⚠ Consider refactoring a long loop at line {node.lineno}\n")

    # Detect long functions (excessive complexity)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and len(node.body) > 20:
            issues.append(f"⚠ Function `{node.name}` may be too complex (line {node.lineno})\n")

    return issues

def generate_optimization_suggestions():
    """ Run all optimization checks and store suggestions in a log file. """
    issues = detect_inefficiencies(TARGET_FILE)

    with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as file:
        for issue in issues:
            file.write(issue)

    print(f"Optimization suggestions generated: {len(issues)} issues found.")

if __name__ == "__main__":
    generate_optimization_suggestions()
