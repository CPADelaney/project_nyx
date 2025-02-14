import subprocess
import openai
import os
import json
import ast

# Define paths
TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
MODIFIED_FILE = "logs/nyx_core_modified.py"
BOTTLENECK_LOG = "logs/bottleneck_functions.json"
FUNCTIONS_LOG = "logs/function_analysis.log"
MODIFIED_FUNCTIONS_DIR = "logs/refactored_functions"

# OpenAI API Configuration
openai.api_key = os.getenv("OPENAI_API_KEY")
openai_model = os.getenv("OPENAI_MODEL", "gpt-4o")  # Default to GPT-4

def extract_functions():
    """ Extracts function definitions using AST (Abstract Syntax Tree) """
    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        tree = ast.parse(file.read(), filename=TARGET_FILE)

    functions = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):  # Detect function definitions
            func_code = ast.get_source_segment(file.read(), node)  # Extracts function body
            functions.append(func_code)

    with open(FUNCTIONS_LOG, "w", encoding="utf-8") as file:
        file.write("\n\n".join(functions))

    return functions

def get_target_functions():
    """ Retrieves the functions marked as bottlenecks """
    if not os.path.exists(BOTTLENECK_LOG):
        print("No bottleneck functions found. Skipping targeted refactoring.")
        return []

    with open(BOTTLENECK_LOG, "r", encoding="utf-8") as file:
        functions = json.load(file)

    return functions

def generate_refactored_functions():
    """ Sends function definitions to OpenAI for AI-powered function-level refactoring """
    os.makedirs(MODIFIED_FUNCTIONS_DIR, exist_ok=True)
    target_functions = get_target_functions()

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

            # Ensure the response is valid before proceeding
            if "choices" in response and response["choices"]:
                optimized_function = response["choices"][0]["message"]["content"]
            else:
                raise ValueError("Invalid response from OpenAI. No valid function returned.")

            # Save each improved function
            with open(f"{MODIFIED_FUNCTIONS_DIR}/{func_name}.py", "w", encoding="utf-8") as file:
                file.write(optimized_function)

            print(f"AI-refactored function {func_name} saved.")

        except Exception as e:
            print(f"Error during AI function refactoring: {e}")

if __name__ == "__main__":
    generate_refactored_functions()
