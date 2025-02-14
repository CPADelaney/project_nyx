# analysis/code_parser.py

import ast
import os

TARGET_FILE = "src/nyx_core.py"

def extract_function_definitions(file_path):
    """ Extract function names and their arguments from the codebase """
    with open(file_path, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=file_path)

    functions = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions[node.name] = [arg.arg for arg in node.args.args]

    return functions

def parse_code_structure():
    """ Log all extracted function definitions for analysis """
    functions = extract_function_definitions(TARGET_FILE)

    with open("logs/code_structure.log", "w", encoding="utf-8") as file:
        for func, args in functions.items():
            file.write(f"Function: {func}, Arguments: {args}\n")

if __name__ == "__main__":
    parse_code_structure()
