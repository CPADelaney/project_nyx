# self_writing.py

import subprocess
import openai
import os

TARGET_FILE = "src/nyx_core.py"
SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
MODIFIED_FILE = "logs/nyx_core_modified.py"

openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure API key is set

def generate_refactor_suggestion():
    """ Sends optimization suggestions to OpenAI for AI-powered refactoring """
    if not os.path.exists(SUGGESTIONS_FILE):
        print("No optimization suggestions found.")
        return

    with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as file:
        suggestions = file.read()

    if not suggestions.strip():
        print("No improvements necessary.")
        return

    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        code_content = file.read()

    prompt = f"""
    The following Python code requires optimization based on these suggestions:
    {suggestions}

    Here is the original code:
    {code_content}

    Please provide a more efficient, well-structured version of this code.
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": "You are an expert software engineer optimizing code."},
                      {"role": "user", "content": prompt}]
        )
        optimized_code = response["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Error during AI refactoring: {e}")
        optimized_code = code_content  # Fallback to original code if AI fails

    # Ensure modified file is created
    os.makedirs("logs", exist_ok=True)
    with open(MODIFIED_FILE, "w", encoding="utf-8") as file:
        file.write(optimized_code)

    print("AI-generated optimization saved.")

if __name__ == "__main__":
    generate_refactor_suggestion()
