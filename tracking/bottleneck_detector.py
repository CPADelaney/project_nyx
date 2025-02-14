# tracking/bottleneck_detector.py

import os
import sqlite3
import ast
from collections import Counter
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
TARGET_FILE = "src/nyx_core.py"
THRESHOLD_INCREASE = 1.10  # 10% increase in execution time triggers refactoring

def get_worst_performing_functions():
    """Identifies the slowest functions based on past execution times."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()

    # Retrieve slowest functions from the database
    c.execute("SELECT function_name FROM optimization_logs WHERE execution_time > 0 ORDER BY execution_time DESC LIMIT 50")
    slow_functions = [row[0] for row in c.fetchall()]
    conn.close()

    if not slow_functions:
        print("⚠️ No performance history found. Skipping bottleneck detection.")
        return []

    counter = Counter(slow_functions)
    recurring_issues = [func for func, count in counter.items() if count > 3]  # More than 3 slowdowns

    # Store results in SQLite for future reference
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    for func in recurring_issues:
        c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("bottleneck_function", func))
    conn.commit()
    conn.close()

    print(f"✅ Logged bottleneck functions for optimization: {recurring_issues}")
    return recurring_issues

def extract_function_names(file_path):
    """Parses function names from the source code for targeted optimization."""
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    
    # Store extracted function names in SQLite
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    for func in functions:
        c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("function_detected", func))
    conn.commit()
    conn.close()

    print(f"✅ Logged bottleneck functions for optimization: {functions}")
    return functions

if __name__ == "__main__":
    initialize_log_db()  # Ensure database is initialized
    get_worst_performing_functions()
