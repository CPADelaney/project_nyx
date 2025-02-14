# self_writing.py

import subprocess
import openai
import os

TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
MODIFIED_FILE = "logs/nyx_core_modified.py"
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

def generate_refactored_functions():
    """ Sends function definitions to OpenAI for AI-powered function-level refactoring """
    functions = extract_functions()

    for i, function_code in enumerate(functions):
        prompt = f"""
        The following Python function needs optimization and performance improvements:
        {function_code}

        Please rewrite this function to be more efficient, readable, and maintainable while preserving functionality.
        """

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o",
                messages=[{"role": "system", "content": "You are an expert software engineer optimizing code."},
                          {"role": "user", "content": prompt}]
            )
            optimized_function = response["choices"][0]["message"]["content"]

            # Save each improved function
            with open(f"logs/refactored_function_{i}.py", "w", encoding="utf-8") as file:
                file.write(optimized_function)

            print(f"AI-refactored function {i} saved.")

        except Exception as e:
            print(f"Error during AI function refactoring: {e}")

if __name__ == "__main__":
    generate_refactored_functions()
