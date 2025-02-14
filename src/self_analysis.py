# self_analysis.py

import ast
import os

# Directory to analyze
CODE_DIR = "src"

# Log file for self-analysis
LOG_FILE = "logs/code_analysis.log"

def analyze_code_structure(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)
    
    functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
    
    return {
        "file": file_path,
        "functions": functions,
        "imports": imports
    }

def log_analysis(results):
    with open(LOG_FILE, "a", encoding="utf-8") as log_file:
        for result in results:
            log_file.write(f"File: {result['file']}\n")
            log_file.write(f"Functions: {', '.join(result['functions'])}\n")
            log_file.write(f"Imports: {', '.join(result['imports'])}\n")
            log_file.write("="*40 + "\n")

def main():
    results = []
    
    for filename in os.listdir(CODE_DIR):
        if filename.endswith(".py"):  # Adjust for other languages if needed
            file_path = os.path.join(CODE_DIR, filename)
            results.append(analyze_code_structure(file_path))
    
    log_analysis(results)
    print(f"Code analysis completed. Results logged in {LOG_FILE}")

if __name__ == "__main__":
    main()
