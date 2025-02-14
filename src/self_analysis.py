# src/self_analysis/py

import ast
import os

# Directory to analyze
CODE_DIR = "src"

# Log file for self-analysis
LOG_FILE = "logs/code_analysis.log"

def analyze_code_structure(file_path):
    """Analyzes the structure of a Python file and extracts functions and imports."""
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()

            if not content:
                print(f"⚠️ Skipping {file_path}: Empty or invalid file.")
                return {"file": file_path, "functions": [], "imports": [], "unused_imports": [], "long_functions": []}

            tree = ast.parse(content, filename=file_path)
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        
        # Detect unused imports
        unused_imports = [imp for imp in imports if imp not in functions]

        # Detect long functions (excessive complexity)
        long_functions = [node.name for node in ast.walk(tree) 
                          if isinstance(node, ast.FunctionDef) and len(node.body) > 20]  # Threshold: 20 lines

        return {
            "file": file_path,
            "functions": functions,
            "imports": imports,
            "unused_imports": unused_imports,
            "long_functions": long_functions
        }
    
    except SyntaxError as e:
        print(f"❌ Skipping {file_path}: SyntaxError detected. {e}")
        return {"file": file_path, "functions": [], "imports": [], "unused_imports": [], "long_functions": []}


def log_analysis(results):
    """Logs analysis results, ensuring the log file is never empty."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)  # Ensure log directory exists

    with open(LOG_FILE, "w", encoding="utf-8") as log_file:
        if not results:
            log_file.write("⚠️ No Python files found for analysis.\n")
            print("⚠️ Warning: No Python files detected. Log will be minimal.")
            return

        for result in results:
            log_file.write(f"File: {result['file']}\n")
            log_file.write(f"Functions: {', '.join(result['functions'])}\n")
            log_file.write(f"Imports: {', '.join(result['imports'])}\n")
            log_file.write(f"Unused Imports: {', '.join(result['unused_imports'])}\n")
            log_file.write(f"Complex Functions: {', '.join(result['long_functions'])}\n")
            log_file.write("="*40 + "\n")

def main():
    """ Runs code analysis and ensures logs exist. """
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)  # Ensure log directory exists

    results = []
    
    for filename in os.listdir(CODE_DIR):
        if filename.endswith(".py"):  # Adjust for other languages if needed
            file_path = os.path.join(CODE_DIR, filename)
            results.append(analyze_code_structure(file_path))

    log_analysis(results)

    # If no results were written, ensure log file still has meaningful output
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        log_file.write("✅ Code analysis completed.\n")

    print(f"✅ Code analysis completed. Results logged in {LOG_FILE}")

if __name__ == "__main__":
    main()
