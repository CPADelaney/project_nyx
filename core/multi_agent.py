# core/multi_agent.py

import sys
import os
import json
import openai
import subprocess
import asyncio
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


# Load Agents
def load_agents():
    """Loads AI agents from config or sets defaults."""
    if os.path.exists(AGENT_CONFIG):
        with open(AGENT_CONFIG, "r", encoding="utf-8") as file:
            return json.load(file)
    return {
        "optimizer": {"role": "Improve efficiency", "priority": 5, "active": True},
        "expander": {"role": "Develop new features", "priority": 5, "active": True},
        "security": {"role": "Detect threats", "priority": 5, "active": True},
        "validator": {"role": "Test optimizations", "priority": 5, "active": True},
    }

task_queue = asyncio.PriorityQueue()

### 🔹 **Parallel Thought Execution with Dynamic Prioritization**
async def process_thought(agent_name, task, priority):
    """Processes a given AI task asynchronously with real-time priority."""
    execution_time = random.uniform(0.5, 2.5) / (priority / 5)  # Scale speed by priority
    print(f"⚡ [{agent_name}] Running task: '{task}' at priority {priority} ({execution_time:.2f}s)...")
    
    await asyncio.sleep(execution_time)  # Simulate async execution
    return f"✅ [{agent_name}] Task '{task}' completed."

async def agent_task_runner():
    """Continuously fetches and executes tasks from the priority queue."""
    while True:
        priority, agent_name, task = await task_queue.get()
        result = await process_thought(agent_name, task, priority)
        print(result)
        task_queue.task_done()

async def execute_parallel_thoughts():
    """Loads tasks dynamically based on agent priority and runs them in parallel."""
    agents = load_agents()
    
    # Populate Task Queue
    for agent_name, agent in agents.items():
        if agent["active"]:
            priority = agent.get("priority", 5)
            task = f"{agent_name.upper()} Task"
            await task_queue.put((10 - priority, agent_name, task))  # Lower number = higher priority

    # Spawn async workers
    workers = [asyncio.create_task(agent_task_runner()) for _ in range(4)]  # Adjust worker count as needed
    await task_queue.join()  # Wait until all tasks are done

    # Cancel workers after execution
    for worker in workers:
        worker.cancel()

# **Main Async Execution**
if __name__ == "__main__":
    asyncio.run(execute_parallel_thoughts())

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
