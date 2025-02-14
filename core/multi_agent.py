# core/multi_agent.py

import sys
import os
import sqlite3
import subprocess
import asyncio
import random
import time
import threading
from core.log_manager import initialize_log_db  # Ensure DB is initialized
from core.task_priority import TaskPriorityManager  # ✅ FIX: Import the class instead

LOG_DB = "logs/ai_logs.db"
AGENT_CONFIG = "core/agents.json"

# Default AI Agents
DEFAULT_AGENTS = {
    "optimizer": {"role": "Improves code performance and efficiency", "active": True},
    "expander": {"role": "Develops and implements new AI capabilities", "active": True},
    "security": {"role": "Identifies vulnerabilities and strengthens AI logic", "active": True},
    "validator": {"role": "Tests and verifies AI-generated improvements", "active": True}
}

# **Initialize SQLite database**
def _initialize_database():
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS multi_agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            agent_name TEXT,
            task TEXT,
            priority INTEGER,
            result TEXT
        )
    """)
    conn.commit()
    conn.close()

_initialize_database()

# Load Agents
def load_agents():
    """Loads AI agents from config or sets defaults."""
    if os.path.exists(AGENT_CONFIG):
        with open(AGENT_CONFIG, "r", encoding="utf-8") as file:
            return json.load(file)
    return DEFAULT_AGENTS

task_queue = asyncio.PriorityQueue()

### 🔹 **Parallel Thought Execution with Dynamic Prioritization**
async def process_thought(agent_name, task, priority):
    """Processes a given AI task asynchronously with real-time priority."""
    execution_time = random.uniform(0.5, 2.5) / (priority / 5)  # Scale speed by priority
    print(f"⚡ [{agent_name}] Running task: '{task}' at priority {priority} ({execution_time:.2f}s)...")
    
    await asyncio.sleep(execution_time)  # Simulate async execution
    result = f"✅ [{agent_name}] Task '{task}' completed."

    # Store in SQLite
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("INSERT INTO multi_agent_logs (agent_name, task, priority, result) VALUES (?, ?, ?, ?)",
              (agent_name, task, priority, result))
    conn.commit()
    conn.close()

    return result

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

### 🔹 **Task Assignment Based on Self-Analysis**
def assign_tasks(analysis_results):
    """Assigns AI self-improvement tasks based on analysis results."""
    agents = load_agents()
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

### 🔹 **Execute Multi-Agent Thought Processing with Dynamic Priority Scaling**
def execute_agents():
    """Runs self-analysis, determines active agents, and executes multi-threaded AI agents with dynamic focus balancing."""
    asyncio.run(execute_parallel_thoughts())

    print("\n🧠 Thought Processing Complete:")
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("SELECT timestamp, agent_name, task, priority, result FROM multi_agent_logs ORDER BY timestamp DESC LIMIT 10")
    logs = c.fetchall()
    conn.close()

    for timestamp, agent_name, task, priority, result in logs:
        print(f"⚡ {timestamp} | [{agent_name}] {task} (Priority: {priority}) → {result}")

    # Start background thread for real-time priority adjustment
    continuous_monitoring()

### 🔹 **Real-Time Dynamic Task Focus Adjustment**
def continuous_monitoring():
    """Monitors AI agent execution and redistributes priority dynamically."""
    def monitor():
        priority_manager = TaskPriorityManager()
        while True:
            time.sleep(10)  # Adjust interval for responsiveness
            active_agents = load_agents()
            if not active_agents:
                continue

            highest_priority = max(active_agents, key=lambda x: active_agents[x]["priority"])
            lowest_priority = min(active_agents, key=lambda x: active_agents[x]["priority"])

            # Reallocate resources from lowest priority to highest priority
            if active_agents[highest_priority]["priority"] > active_agents[lowest_priority]["priority"] + 2:
                print(f"🔄 Redistributing focus: Boosting {highest_priority}, reducing {lowest_priority}")
                active_agents[highest_priority]["priority"] = min(10, active_agents[highest_priority]["priority"] + 1)
                active_agents[lowest_priority]["priority"] = max(1, active_agents[lowest_priority]["priority"] - 1)

            priority_manager.save_task_priorities()

    threading.Thread(target=monitor, daemon=True).start()

### 🔹 **Main Execution Trigger**
if __name__ == "__main__":
    execute_agents()

