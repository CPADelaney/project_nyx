import os
import shutil
import subprocess

SUGGESTIONS_FILE = "logs/optimization_suggestions.txt"
TARGET_FILE = "src/nyx_core.py"
BACKUP_FILE = "logs/nyx_core_backup.py"

def backup_code():
    """ Creates a backup before modifying the file """
    if os.path.exists(TARGET_FILE):
        shutil.copy(TARGET_FILE, BACKUP_FILE)
        print(f"Backup of {TARGET_FILE} saved to {BACKUP_FILE}")

def apply_suggestions():
    """ Reads optimization suggestions and applies simple fixes """
    if not os.path.exists(SUGGESTIONS_FILE):
        print("No suggestions found. Skipping self-writing process.")
        return

    with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as file:
        suggestions = file.readlines()

    if not suggestions:
        print("No optimizations needed.")
        return

    with open(TARGET_FILE, "r", encoding="utf-8") as file:
        code_lines = file.readlines()

    modified_code = []
    for line in code_lines:
        if "import " in line and any("Remove unused imports" in s for s in suggestions):
            continue  # Automatically remove unused imports

        modified_code.append(line)

    with open(TARGET_FILE, "w", encoding="utf-8") as file:
        file.writelines(modified_code)

    print("Applied optimizations to nyx_core.py.")

def trigger_self_analysis():
    """ Runs a new self-analysis after modification """
    print("Triggering new self-analysis cycle...")
    subprocess.run(["python3", "analysis/self_analysis.py"])

if __name__ == "__main__":
    backup_code()
    apply_suggestions()
    trigger_self_analysis()
