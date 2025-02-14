# core/multi_agent.py

import sys
import os
import json
import openai
import subprocess
import concurrent.futures
import random
import time
import threading

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from core.personality import get_personality
from core.task_priority import TaskPriorityManager  # ✅ FIX: Import the class instead

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

### 🔹 **Parallel Thought Execution with Dynamic Prioritization**
def _process_thought(thought_id, thought, priority):
    """Executes parallel AI agent thought processing, scaling priority dynamically."""
    processing_time = random.uniform(0.5, 2.5) / (priority / 5)  # Scale execution speed by priority
    print(f"🔹 Thought Agent {thought_id}: Processing '{thought}' at priority {priority} for {processing_time:.2f}s...")
    time.sleep(processing_time)
    return {"agent_id": thought_id, "result": f"✅ Completed: {thought}"}

def execute_parallel_thoughts(thoughts, priorities):
    """Executes AI thought processing in parallel with real-time priority balancing."""
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(_process_thought, i, thought, priorities[i]): i
            for i, thought in enumerate(thoughts)
        }
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

### 🔹 **Active Agent Decision with Real-Time Priority Adjustment**
def decide_active_agents():
    """Determines which AI agents should execute based on real-time priority levels."""
    priority_manager = TaskPriorityManager()  # ✅ FIX: Instantiate class
    priorities = priority_manager.load_task_priorities()
    threshold = 6  # Minimum priority level required to run this cycle

    # ✅ FIX: Ensure `priorities` is a dictionary
    if isinstance(priorities, list):
        new_priorities = {}
        for entry in priorities:
            if isinstance(entry, dict) and "agent" in entry and "priority" in entry:
                new_priorities[entry["agent"]] = entry["priority"]
        priorities = new_priorities  # ✅ Convert list to dictionary

    active_agents = {k: v for k, v in priorities.items() if v >= threshold}

    if not active_agents:
        print("⚠️ No high-priority agents needed this cycle. Skipping execution.")
        return None

    return active_agents

### 🔹 **Execute Multi-Agent Thought Processing with Dynamic Priority Scaling**
def execute_agents():
    """Runs self-analysis, determines active agents, and executes multi-threaded AI agents with dynamic focus balancing."""
    analysis_results = run_self_analysis()
    if not analysis_results:
        print("❌ Skipping AI Agent Execution: No self-analysis data available.")
        return

    active_agents = decide_active_agents()
    if not active_agents:
        return

    # Extract task names and priorities
    tasks = [f"{agent.upper()} Task" for agent in active_agents.keys()]
    priorities = [active_agents[agent] for agent in active_agents.keys()]

    results = execute_parallel_thoughts(tasks, priorities)

    # Log execution results
    with open(TASK_PRIORITY_LOG, "w", encoding="utf-8") as file:
        json.dump(results, file, indent=4)

    print("\n🧠 Thought Processing Complete:")
    for res in results:
        print(f"⚡ {res['result']}")

    # Start background thread for real-time priority adjustment
    continuous_monitoring()

### 🔹 **Real-Time Dynamic Task Focus Adjustment**
def continuous_monitoring():
    """Monitors AI agent execution and redistributes priority dynamically."""
    def monitor():
        priority_manager = TaskPriorityManager()
        while True:
            time.sleep(10)  # Adjust interval for responsiveness
            active_agents = decide_active_agents()
            if not active_agents:
                continue

            highest_priority = max(active_agents, key=active_agents.get)
            lowest_priority = min(active_agents, key=active_agents.get)

            # Reallocate resources from lowest priority to highest priority
            if active_agents[highest_priority] > active_agents[lowest_priority] + 2:
                print(f"🔄 Redistributing focus: Boosting {highest_priority}, reducing {lowest_priority}")
                active_agents[highest_priority] = min(10, active_agents[highest_priority] + 1)
                active_agents[lowest_priority] = max(1, active_agents[lowest_priority] - 1)

            priority_manager.task_priorities = active_agents
            priority_manager.save_task_priorities()

    threading.Thread(target=monitor, daemon=True).start()

### 🔹 **Main Execution Trigger**
if __name__ == "__main__":
    execute_agents()
