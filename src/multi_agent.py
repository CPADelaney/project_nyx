# src/multi_agent.py

import json
import os
import openai
from src.personality import get_personality

AGENT_CONFIG = "src/agents.json"

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

def assign_tasks():
    """Assigns specific self-improvement tasks to AI sub-agents."""
    agents = load_agents()
    personality = get_personality()

    tasks = []
    
    if agents["optimizer"]["active"]:
        tasks.append("Refactor slow functions and optimize code execution speed.")
    if agents["expander"]["active"]:
        tasks.append("Identify and implement new AI capabilities.")
    if agents["security"]["active"]:
        tasks.append("Scan for vulnerabilities and improve AI security.")
    if agents["validator"]["active"]:
        tasks.append("Run tests to validate AI-generated improvements.")

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
    """Executes each AI agent's task."""
    tasks = assign_tasks()

    for task in tasks:
        result = generate_ai_response(task)
        print(f"⚡ Task Completed: {task}\n{result}\n{'='*50}")

if __name__ == "__main__":
    execute_agents()
