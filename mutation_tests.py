# mutation_tests.py

import random
import subprocess

TARGET_FILE = "src/nyx_core.py"

def introduce_random_bug():
    """ Introduce a small syntax error randomly for self-testing """
    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        lines = file.readlines()

    if len(lines) > 5:
        corrupt_line = random.randint(0, len(lines) - 1)
        lines[corrupt_line] = lines[corrupt_line].replace(" ", "# ", 1)  # Breaks indentation

    with open(TARGET_FILE, "w", encoding="utf-8") as file:
        file.writelines(lines)

    print("Introduced a random bug for mutation testing.")

if __name__ == "__main__":
    introduce_random_bug()
    subprocess.run(["python3", "tests/self_test.py"])

