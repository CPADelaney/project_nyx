# self_writing.py

import os
import sqlite3
import subprocess
import ast
import openai
from datetime import datetime
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
TARGET_FILE = "src/nyx_core.py"
MODIFIED_FUNCTIONS_DIR = "logs/refactored_functions"

# OpenAI API Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to GPT-4

class SelfWriting:
    """Handles AI-driven self-improvement by modifying its own code."""

    def __init__(self):
        initialize_log_db()  # Ensure database is initialized
        self._initialize_database()

    def _initialize_database(self):
        """Ensures the AI self-modification table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_self_modifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                target_function TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()

    def extract_functions(self):
        """Extracts function definitions using AST (Abstract Syntax Tree)."""
        with open(TARGET_FILE, "r", encoding="utf-8") as file:
            source_code = file.read()

        tree = ast.parse(source_code, filename=TARGET_FILE)

        functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_code = ast.get_source_segment(source_code, node)
                functions.append(func_code)

        return functions

    def get_target_functions(self):
        """Retrieves the functions marked as bottlenecks from SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT details FROM performance_logs WHERE event_type='bottleneck_function'")
        functions = [row[0] for row in c.fetchall()]
        conn.close()

        if not functions:
            print("No bottleneck functions found. Skipping targeted refactoring.")
        return functions

    def generate_refactored_functions(self):
        """Sends function definitions to OpenAI for AI-powered function-level refactoring."""
        os.makedirs(MODIFIED_FUNCTIONS_DIR, exist_ok=True)
        target_functions = self.get_target_functions()

        for func_name in target_functions:
            prompt = f"""
            The following function in `nyx_core.py` is running slower than expected:
            Function name: {func_name}

            Please rewrite this function to be more efficient while maintaining functionality.
            """

            try:
                response = openai.ChatCompletion.create(
                    model=openai_model,
                    messages=[{"role": "system", "content": "You are an expert software engineer optimizing code."},
                              {"role": "user", "content": prompt}]
                )

                if "choices" in response and response["choices"]:
                    optimized_function = response["choices"][0]["message"]["content"]
                else:
                    raise ValueError("Invalid response from OpenAI. No valid function returned.")

                # Save each improved function
                with open(f"{MODIFIED_FUNCTIONS_DIR}/{func_name}.py", "w", encoding="utf-8") as file:
                    file.write(optimized_function)

                self.log_self_modification("function_refactor", func_name, "AI-optimized function generated")

                print(f"AI-refactored function {func_name} saved.")

            except Exception as e:
                print(f"Error during AI function refactoring: {e}")

    def log_self_modification(self, event_type, target_function, details):
        """Logs AI-driven self-improvements in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ai_self_modifications (event_type, target_function, details) VALUES (?, ?, ?)",
                  (event_type, target_function, details))
        conn.commit()
        conn.close()

    def review_self_modifications(self):
        """Displays AI self-modification report."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, target_function, details FROM ai_self_modifications ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🤖 AI Self-Modification Report:")
        for timestamp, event_type, target_function, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} | Function: `{target_function}` | Details: {details}")

if __name__ == "__main__":
    self_writer = SelfWriting()
    self_writer.generate_refactored_functions()
    self_writer.review_self_modifications()
