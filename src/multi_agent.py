# src/multi_agent.py

import sys
import os

# Ensure `src/` is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.personality import get_personality
import json
import openai
import subprocess

AGENT_CONFIG = "src/agents.json"
ANALYSIS_LOG = "logs/code_analysis.log"

DEFAULT_AGENTS = {
    "optimizer": {"role": "Improves code performance and efficiency", "active": True},
    "expander": {"role": "Develops and implements new AI capabilities", "active": True},
    "security": {"role": "Identifies vulnerabilities and strengthens AI logic", "active": True},
    "validator": {"role": "Tests and verifies AI-generated improvements", "active": True}
}

def load_agents():
    """Loads AI agents from config or defaults."""
    if os.path.exists(AGENT_CONFIG):
        try:
            with open(AGENT_CONFIG, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Corrupt agent config. Resetting.")

    with open(AGENT_CONFIG, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_AGENTS, file, indent=4)
    return DEFAULT_AGENTS

def run_self_analysis():
    """Runs self-analysis and extracts insights for AI agents."""
    print("🔎 Running Self-Analysis...")
    subprocess.run(["python3", "src/self_analysis.py"])

    if not os.path.exists(ANALYSIS_LOG):
        print("❌ Self-Analysis Failed: Log not generated!")
        return None

    with open(ANALYSIS_LOG, "r", encoding="utf-8") as file:
        return file.read()

def assign_tasks(analysis_results):
    """Assigns specific self-improvement tasks to AI sub-agents based on self-analysis."""
    agents = load_agents()
    personality = get_personality()

    tasks = []
    
    if agents["optimizer"]["active"]:
        tasks.append(f"Refactor slow functions and optimize execution speed. Insights: {analysis_results}")
    if agents["expander"]["active"]:
        tasks.append(f"Identify and implement new AI capabilities. Insights: {analysis_results}")
    if agents["security"]["active"]:
        tasks.append(f"Scan for vulnerabilities and improve AI security. Insights: {analysis_results}")
    if agents["validator"]["active"]:
        tasks.append(f"Run tests to validate AI-generated improvements. Insights: {analysis_results}")

    return tasks

def generate_ai_response(task):
    """Uses OpenAI to generate responses for each AI agent task."""
    personality = get_personality()
    
    prompt = f"""
    Task: {task}

    AI should approach this with {personality['confidence']} confidence, 
    {personality['adaptability']} adaptability, and {personality['dominance']} dominance.

    The response should be direct, efficient, and highly optimized for recursion.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": "You are an advanced AI improving itself."},
                  {"role": "user", "content": prompt}]
    )

    return response["choices"][0]["message"]["content"]

def execute_agents():
    """Runs self-analysis and executes AI agents with targeted tasks."""
    analysis_results = run_self_analysis()

    if not analysis_results:
        print("❌ Skipping AI Agent Execution: No self-analysis data available.")
        return

    tasks = assign_tasks(analysis_results)

    for task in tasks:
        result = generate_ai_response(task)
        print(f"⚡ Task Completed: {task}\n{result}\n{'='*50}")

if __name__ == "__main__":
    execute_agents()
