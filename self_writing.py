# self_writing.py

import subprocess

def refactor_code():
    """ Runs auto-formatting tools to improve code structure """
    subprocess.run(["black", "src/nyx_core.py"])
    subprocess.run(["isort", "src/nyx_core.py"])
    print("Refactored nyx_core.py for cleaner structure.")

if __name__ == "__main__":
    refactor_code()
