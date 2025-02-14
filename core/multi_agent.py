# core/multi_agent.py

import sys
import os
import json
import openai
import subprocess
import concurrent.futures
import random
import time

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality
from core.task_priority import load_task_priorities

# File paths
AGENT_CONFIG = "core/agents.json"
ANALYSIS_LOG = "logs/code_analysis.log"
TASK_PRIORITY_LOG = "logs/task_priority.json"

# Default AI Agents
DEFAULT_AGENTS = {
    "optimizer": {"role": "Improves code performance and efficiency", "active": True},
    "expander": {"role": "Develops and implements new AI capabilities", "active": True},
    "security": {"role": "Identifies vulnerabilities and strengthens AI logic", "active": True},
    "validator": {"role": "Tests and verifies AI-generated improvements", "active": True}
}

### 🔹 **Load Agents Configuration**
def load_agents():
    """Loads AI agents from config or sets defaults."""
    if os.path.exists(AGENT_CONFIG):
        try:
            with open(AGENT_CONFIG, "r", encoding="utf-8") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("⚠️ Corrupt agent config. Resetting.")

    with open(AGENT_CONFIG, "w", encoding="utf-8") as file:
        json.dump(DEFAULT_AGENTS, file, indent=4)
    return DEFAULT_AGENTS

### 🔹 **Parallel Thought Execution**
def _process_thought(thought_id, thought):
    """Simulates parallel AI agent thought execution."""
    processing_time = random.uniform(0.5, 2.5)
    print(f"🔹 Thought Agent {thought_id}: Processing '{thought}' for {processing_time:.2f}s...")
    time.sleep(processing_time)
    return {"agent_id": thought_id, "result": f"✅ Completed: {thought}"}

def execute_parallel_thoughts(thoughts):
    """Executes all AI thought processes in parallel."""
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(_process_thought, i, thought): i for i, thought in enumerate(thoughts)}
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())

    return results

### 🔹 **Self-Analysis Execution**
def run_self_analysis():
    """Runs self-analysis and extracts insights for AI agents."""
    print("🔎 Running Self-Analysis...")
    subprocess.run(["python3", "src/self_analysis.py"])

    if not os.path.exists(ANALYSIS_LOG):
        print("❌ Self-Analysis Failed: Log not generated!")
        return None

    with open(ANALYSIS_LOG, "r", encoding="utf-8") as file:
        return file.read()

### 🔹 **Task Assignment Based on Self-Analysis**
def assign_tasks(analysis_results):
    """Assigns AI self-improvement tasks based on analysis results."""
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

### 🔹 **Active Agent Decision**
def decide_active_agents():
    """Determines which AI agents should execute based on priority levels."""
    priorities = load_task_priorities()
    threshold = 6  # Minimum priority level required to run this cycle

    # If priorities is a list, convert it into a dict.
    # Expected list format: [{"agent": "optimizer", "priority": 7}, ...]
    if isinstance(priorities, list):
        new_priorities = {}
        for entry in priorities:
            if isinstance(entry, dict) and "agent" in entry and "priority" in entry:
                new_priorities[entry["agent"]] = entry["priority"]
        priorities = new_priorities

    active_agents = {k: v for k, v in priorities.items() if v >= threshold}

    if not active_agents:
        print("⚠️ No high-priority agents needed this cycle. Skipping execution.")
        return None

    return active_agents

### 🔹 **OpenAI API Integration**
def get_openai_client():
    """Returns an OpenAI client instance."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not found in environment")
    
    return openai.OpenAI(api_key=api_key)

def generate_ai_response(task):
    """Uses OpenAI API to generate responses for each AI agent task."""
    personality = get_personality()
    client = get_openai_client()

    prompt = f"""
    Task: {task}

    AI should approach this with {personality['confidence']} confidence, 
    {personality['adaptability']} adaptability, and {personality['dominance']} dominance.

    The response should be direct, efficient, and highly optimized for recursion.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are an advanced AI improving itself."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=300
        )
        return response.choices[0].message.content

    except openai.OpenAIError as e:
        print(f"❌ OpenAI API error: {e}")
        return "Error generating AI response."

### 🔹 **Execute Multi-Agent Thought Processing**
def execute_agents():
    """Runs self-analysis, determines active agents, and executes multi-threaded AI agents."""
    analysis_results = run_self_analysis()
    if not analysis_results:
        print("❌ Skipping AI Agent Execution: No self-analysis data available.")
        return

    active_agents = decide_active_agents()
    if not active_agents:
        return

    tasks = [f"{agent.upper()} Task" for agent in active_agents.keys()]
    results = execute_parallel_thoughts(tasks)

    # Log execution results
    with open(TASK_PRIORITY_LOG, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print("\n🧠 Thought Processing Complete:")
    for res in results:
        print(f"⚡ {res['result']}")

### 🔹 **Main Execution Trigger**
if __name__ == "__main__":
    execute_agents()
