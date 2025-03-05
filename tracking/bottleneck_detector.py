# tracking/bottleneck_detector.py

import cProfile
import pstats
import os
import sqlite3
from io import StringIO

LOG_DB = "logs/ai_logs.db"
TARGET_FILE = "src/nyx_core.py"
THRESHOLD_PERCENT = 5  # Only optimize if function runs 5% slower than baseline

def profile_execution():
    """Runs profiling on nyx_core.py and logs function execution times."""
    profiler = cProfile.Profile()
    profiler.enable()

    os.system(f"python3 {TARGET_FILE}")  # Run the AI core

    profiler.disable()
    result = StringIO()
    stats = pstats.Stats(profiler, stream=result)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.print_stats()

    # Extract slowest functions
    slow_functions = []
    for line in result.getvalue().split("\n"):
        if "src/" in line:
            parts = line.strip().split()
            if len(parts) > 5:
                function_name = parts[-1]
                execution_time = float(parts[2])
                slow_functions.append((function_name, execution_time))

    # Log function execution times
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    for func, time in slow_functions:
        c.execute("INSERT INTO optimization_logs (function_name, execution_time) VALUES (?, ?)", (func, time))
    conn.commit()
    conn.close()

def detect_bottlenecks():
    """Identifies the slowest functions based on profiling history."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    
    # Get the last two execution records for each function
    c.execute("""
        SELECT function_name, MAX(execution_time), MIN(execution_time)
        FROM optimization_logs
        GROUP BY function_name
        HAVING (MAX(execution_time) - MIN(execution_time)) / MIN(execution_time) * 100 >= ?
    """, (THRESHOLD_PERCENT,))

    slow_functions = c.fetchall()
    conn.close()
    
    return [func for func, max_time, min_time in slow_functions]

if __name__ == "__main__":
    profile_execution()
    print("🔍 Bottlenecks detected:", detect_bottlenecks())
