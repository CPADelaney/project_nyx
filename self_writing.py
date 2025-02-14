# self_writing.py

import subprocess
import openai
import os
import json

TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
MODIFIED_FILE = "logs/nyx_core_modified.py"
BOTTLENECK_LOG = "logs/bottleneck_functions.json"
FUNCTIONS_LOG = "logs/function_analysis.log"

openai.api_key = os.getenv("OPENAI_API_KEY") 

def extract_functions():
    """ Extracts function definitions from the codebase for AI-guided improvement """
    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    functions = []
    inside_function = False
    function_body = []

    for line in lines:
        if line.startswith("def "):  # Start of a function
            if function_body:
                functions.append("\n".join(function_body))
                function_body = []
            inside_function = True

        if inside_function:
            function_body.append(line)

        if line.strip() == "":  # End of function
            inside_function = False

    if function_body:
        functions.append("\n".join(function_body))

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
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are an expert software engineer optimizing code."},
                          {"role": "user", "content": prompt}]
            )
            optimized_function = response["choices"][0]["message"]["content"]

            # Save each improved function
            with open(f"{MODIFIED_FUNCTIONS_DIR}/{func_name}.py", "w", encoding="utf-8") as file:
                file.write(optimized_function)

            print(f"AI-refactored function {func_name} saved.")

        except Exception as e:
            print(f"Error during AI function refactoring: {e}")

if __name__ == "__main__":
    generate_refactored_functions()
