# core/agi_controller.py

import os
import sys
import json
import sqlite3
import subprocess
import time
import random
import numpy as np
from datetime import datetime, timedelta
import threading
import asyncio
import logging
from core.log_manager import initialize_log_db, LOG_DB
from knowledge.acquisition import KnowledgeAcquisition
from modeling.concept_builder import ConceptualModeling
from core.self_modification import SelfModification

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/agi_controller.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("AGI-Controller")

class AGIController:
    """
    Central controller that orchestrates the proto-AGI system components and implements
    a recursive self-improvement feedback loop with knowledge acquisition and abstraction.
    """
    
    def __init__(self):
        initialize_log_db()
        self._initialize_database()
        
        # Initialize component subsystems
        self.knowledge_system = KnowledgeAcquisition()
        self.concept_system = ConceptualModeling()
        self.modification_system = SelfModification()
        
        # System state
        self.running = False
        self.pause_requested = False
        self.controller_thread = None
        self.cycle_count = 0
        self.last_activity = {}
        self.system_state = {
            "status": "initialized",
            "current_focus": None,
            "improvement_cycles": 0,
            "knowledge_items": 0,
            "concepts_formed": 0,
            "last_update": str(datetime.now())
        }
        
        # Learning goals and priorities
        self.learning_goals = []
        self.component_priorities = {
            "knowledge_acquisition": 0.33,
            "concept_formation": 0.33,
            "self_modification": 0.34
        }
        
        # Load existing state if available
        self._load_state()
        logger.info("AGI Controller initialized")
    
    def _initialize_database(self):
        """Initializes database tables for the AGI controller."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS agi_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    cycle_number INTEGER,
                    focus_area TEXT,
                    actions_taken TEXT,
                    outcomes TEXT,
                    insights_gained TEXT
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS learning_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_timestamp TEXT
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    metric_name TEXT,
                    metric_value REAL
                )''')
                
        conn.commit()
        conn.close()
    
    def _load_state(self):
        """Loads the previous system state."""
        state_file = "logs/agi_state.json"
        if os.path.exists(state_file):
            try:
                with open(state_file, "r", encoding="utf-8") as file:
                    state = json.load(file)
                    self.system_state = state.get("system_state", self.system_state)
                    self.component_priorities = state.get("component_priorities", self.component_priorities)
                    self.cycle_count = state.get("cycle_count", 0)
                    logger.info(f"Loaded system state: {self.cycle_count} cycles completed")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading state: {str(e)}")
    
    def _save_state(self):
        """Saves the current system state."""
        state_file = "logs/agi_state.json"
        self.system_state["last_update"] = str(datetime.now())
        
        state = {
            "system_state": self.system_state,
            "component_priorities": self.component_priorities,
            "cycle_count": self.cycle_count
        }
        
        try:
            with open(state_file, "w", encoding="utf-8") as file:
                json.dump(state, file, indent=2)
        except IOError as e:
            logger.error(f"Error saving state: {str(e)}")
    
    def load_learning_goals(self):
        """Loads learning goals from the database."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT id, goal, priority, status FROM learning_goals WHERE status != 'completed'")
        goals = c.fetchall()
        conn.close()
        
        self.learning_goals = [
            {"id": g[0], "goal": g[1], "priority": g[2], "status": g[3]}
            for g in goals
        ]
        
        if not self.learning_goals:
            # Set some initial goals if none exist
            self.add_learning_goal("Improve system optimization capabilities", 5)
            self.add_learning_goal("Develop better understanding of parallel processing", 3)
            self.add_learning_goal("Learn about advanced memory management techniques", 4)
    
    def add_learning_goal(self, goal, priority=3):
        """Adds a new learning goal."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO learning_goals (goal, priority, status) VALUES (?, ?, ?)",
                 (goal, priority, "pending"))
        goal_id = c.lastrowid
        conn.commit()
        conn.close()
        
        self.learning_goals.append({
            "id": goal_id,
            "goal": goal,
            "priority": priority,
            "status": "pending"
        })
        
        logger.info(f"Added learning goal: {goal} (priority: {priority})")
        return goal_id
    
    def complete_learning_goal(self, goal_id):
        """Marks a learning goal as completed."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("UPDATE learning_goals SET status = 'completed', completed_timestamp = datetime('now') WHERE id = ?",
                 (goal_id,))
        conn.commit()
        conn.close()
        
        # Update local state
        for i, goal in enumerate(self.learning_goals):
            if goal["id"] == goal_id:
                self.learning_goals[i]["status"] = "completed"
                logger.info(f"Completed learning goal: {goal['goal']}")
                break
    
    def update_component_priorities(self):
        """Dynamically adjusts component priorities based on results and needs."""
        # Get recent metrics for each component
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            SELECT component, AVG(metric_value) 
            FROM system_metrics 
            WHERE timestamp > datetime('now', '-1 day')
            GROUP BY component
        """)
        
        recent_metrics = dict(c.fetchall())
        conn.close()
        
        # If we don't have metrics, maintain current priorities
        if not recent_metrics:
            return
            
        # Calculate new priorities based on performance and balance needs
        # Lower performing components get higher priority
        total_metrics = sum(recent_metrics.values())
        if total_metrics <= 0:
            return
            
        # Invert the metrics so lower values get higher priority
        for component in recent_metrics:
            recent_metrics[component] = 1.0 / max(0.1, recent_metrics[component])
            
        # Normalize to get priority distribution
        total_inverted = sum(recent_metrics.values())
        for component in recent_metrics:
            self.component_priorities[component] = recent_metrics[component] / total_inverted
            
        logger.info(f"Updated component priorities: {self.component_priorities}")
    
    def select_focus_area(self):
        """Selects which component to focus on in the current cycle."""
        # Update priorities first
        self.update_component_priorities()
        
        # Choose a component based on priority weights
        components = list(self.component_priorities.keys())
        weights = [self.component_priorities[c] for c in components]
        
        # Also consider time since last activity
        now = datetime.now()
        for i, component in enumerate(components):
            last_time = self.last_activity.get(component, now - timedelta(days=1))
            hours_since = (now - last_time).total_seconds() / 3600
            
            # Add a bonus for components not used recently
            if hours_since > 2:  # If more than 2 hours
                weights[i] *= (1 + min(1.0, hours_since / 10))
                
        # Normalize weights
        total = sum(weights)
        weights = [w/total for w in weights]
        
        # Weighted random selection
        selected = np.random.choice(components, p=weights)
        
        self.last_activity[selected] = now
        self.system_state["current_focus"] = selected
        
        logger.info(f"Selected focus area: {selected}")
        return selected
    
    def execute_knowledge_acquisition_cycle(self):
        """Executes a knowledge acquisition cycle."""
        # Select a learning goal to focus on
        active_goals = [g for g in self.learning_goals if g["status"] == "pending"]
        if not active_goals:
            logger.info("No pending learning goals. Creating a new one.")
            self.add_learning_goal("Learn about optimization techniques", 4)
            active_goals = [g for g in self.learning_goals if g["status"] == "pending"]
            
        # Sort by priority and select one
        active_goals.sort(key=lambda x: x["priority"], reverse=True)
        selected_goal = active_goals[0]
        
        # Create web search terms from the goal
        search_term = selected_goal["goal"].replace("Learn about ", "").replace("Improve ", "")
        
        logger.info(f"Acquiring knowledge for goal: {selected_goal['goal']}")
        
        # Simulate web search and content acquisition
        urls = [
            f"https://example.com/article-about-{search_term.replace(' ', '-')}-1",
            f"https://example.com/tutorial-{search_term.replace(' ', '-')}-advanced",
            f"https://example.com/research-paper-{search_term.replace(' ', '-')}"
        ]
        
        # For demonstration, we'll simulate knowledge acquisition
        acquired_concepts = []
        for url in urls:
            # In a real system, this would actually fetch content from the URL
            # Here we'll simulate success with a probability
            if random.random() < 0.8:  # 80% success rate
                acquired_concepts.append({
                    "concept": f"{search_term.title()} Technique {len(acquired_concepts)+1}",
                    "description": f"A method for {search_term} that improves performance by optimizing resource usage.",
                    "confidence": random.uniform(0.7, 0.95)
                })
                
        if acquired_concepts:
            logger.info(f"Acquired {len(acquired_concepts)} new concepts")
            
            # Record metrics
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("knowledge_acquisition", "concepts_acquired", len(acquired_concepts)))
            
            # Update cycle information
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
                "concept_formation",
                "Analyzed patterns in past optimizations",
                f"Created {len(abstractions)} new abstractions"
            ))
            conn.commit()
            conn.close()
            
            # Update system state
            self.system_state["concepts_formed"] += len(abstractions)
            
            return {
                "success": True,
                "abstractions_created": len(abstractions),
                "hierarchy_depth": len(hierarchy)
            }
        else:
            logger.warning("Failed to identify meaningful patterns")
            
            # Record the failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("concept_formation", "pattern_failures", 1))
            
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
                "concept_formation",
                "Attempted to identify patterns",
                "Failed to identify meaningful patterns"
            ))
            conn.commit()
            conn.close()
            
            return {
                "success": False,
                "error": "Insufficient data for pattern recognition"
            }
    
    def execute_self_modification_cycle(self):
        """Executes a self-modification cycle."""
        logger.info("Starting self-modification cycle")
        
        # Run the self-improvement cycle from the SelfModification system
        result = self.modification_system.run_improvement_cycle()
        
        if result and result.get("success"):
            logger.info(f"Self-modification successful: {result.get('result')}")
            
            # Record metrics
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("self_modification", "successful_modifications", 1))
            
            # Update cycle information
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
                "self_modification",
                f"Applied {result.get('approach')} to {result.get('target_function')}",
                result.get('result')
            ))
            conn.commit()
            conn.close()
            
            # Update system state
            self.system_state["improvement_cycles"] += 1
            
            return {
                "success": True,
                "target": result.get('target_function'),
                "approach": result.get('approach'),
                "result": result.get('result')
            }
        else:
            error_msg = "No optimization candidates found" if not result else result.get('message', 'Unknown error')
            logger.warning(f"Self-modification failed: {error_msg}")
            
            # Record the failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("self_modification", "modification_failures", 1))
            
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
                "self_modification",
                "Attempted to apply self-modification",
                f"Failed: {error_msg}"
            ))
            conn.commit()
            conn.close()
            
            return {
                "success": False,
                "error": error_msg
            }
    
    def generate_new_learning_goal(self):
        """Generates a new learning goal based on system needs."""
        # Analyze past cycles to identify areas that need improvement
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            SELECT focus_area, COUNT(*) as count, 
                   SUM(CASE WHEN outcomes LIKE '%Failed%' THEN 1 ELSE 0 END) as failures
            FROM agi_cycles
            GROUP BY focus_area
        """)
        
        area_stats = c.fetchall()
        conn.close()
        
        # Identify the area with the highest failure rate
        area_failure_rates = {}
        for area, count, failures in area_stats:
            if count > 0:
                area_failure_rates[area] = failures / count
            
        if area_failure_rates:
            weakest_area = max(area_failure_rates.items(), key=lambda x: x[1])[0]
            
            # Generate a learning goal based on the weakest area
            if weakest_area == "knowledge_acquisition":
                goal_topics = [
                    "research methodologies",
                    "information extraction techniques",
                    "knowledge representation",
                    "semantic analysis"
                ]
            elif weakest_area == "concept_formation":
                goal_topics = [
                    "pattern recognition algorithms",
                    "abstraction techniques",
                    "hierarchical knowledge representation",
                    "concept clustering methods"
                ]
            else:  # self_modification
                goal_topics = [
                    "code optimization techniques",
                    "refactoring methodologies",
                    "performance profiling",
                    "automated debugging"
                ]
                
            topic = random.choice(goal_topics)
            goal = f"Learn about {topic} to improve {weakest_area}"
            priority = int(min(5, area_failure_rates[weakest_area] * 5 + 2))  # Scale 1-5
            
            logger.info(f"Generated new learning goal: {goal} (priority: {priority})")
            return self.add_learning_goal(goal, priority)
        else:
            # If no data yet, add a general goal
            goal = "Learn about self-improvement techniques"
            logger.info(f"Added default learning goal: {goal}")
            return self.add_learning_goal(goal, 3)
    
    def execute_cycle(self):
        """Executes a single AGI improvement cycle."""
        self.cycle_count += 1
        logger.info(f"Starting AGI cycle #{self.cycle_count}")
        
        # Load learning goals if needed
        if not self.learning_goals:
            self.load_learning_goals()
            
        # Generate a new learning goal occasionally
        if self.cycle_count % 5 == 0 or not self.learning_goals:
            self.generate_new_learning_goal()
        
        # Select which component to focus on
        focus_area = self.select_focus_area()
        
        # Execute the appropriate cycle
        cycle_result = None
        if focus_area == "knowledge_acquisition":
            cycle_result = self.execute_knowledge_acquisition_cycle()
        elif focus_area == "concept_formation":
            cycle_result = self.execute_concept_formation_cycle()
        elif focus_area == "self_modification":
            cycle_result = self.execute_self_modification_cycle()
            
        # Save updated state
        self._save_state()
        
        logger.info(f"Completed AGI cycle #{self.cycle_count}")
        return {
            "cycle": self.cycle_count,
            "focus": focus_area,
            "result": cycle_result
        }
    
    def start(self):
        """Starts the AGI controller in a separate thread."""
        if self.running:
            logger.warning("AGI controller is already running")
            return False
            
        self.running = True
        self.pause_requested = False
        
        def run_controller():
            logger.info("AGI controller thread started")
            
            while self.running:
                if self.pause_requested:
                    time.sleep(1)
                    continue
                    
                try:
                    self.execute_cycle()
                    
                    # Sleep between cycles to prevent resource hogging
                    time.sleep(10)  # 10-second delay between cycles
                    
                except Exception as e:
                    logger.error(f"Error in AGI cycle: {str(e)}")
                    time.sleep(30)  # Longer delay after an error
                    
            logger.info("AGI controller thread stopped")
            
        self.controller_thread = threading.Thread(target=run_controller)
        self.controller_thread.daemon = True  # Allow the thread to exit when the main program exits
        self.controller_thread.start()
        
        self.system_state["status"] = "running"
        self._save_state()
        
        logger.info("AGI controller started")
        return True
    
    def stop(self):
        """Stops the AGI controller."""
        if not self.running:
            logger.warning("AGI controller is not running")
            return False
            
        logger.info("Stopping AGI controller")
        self.running = False
        
        if self.controller_thread:
            self.controller_thread.join(timeout=30)
            
        self.system_state["status"] = "stopped"
        self._save_state()
        
        logger.info("AGI controller stopped")
        return True
    
    def pause(self):
        """Pauses the AGI controller."""
        if not self.running:
            logger.warning("AGI controller is not running")
            return False
            
        logger.info("Pausing AGI controller")
        self.pause_requested = True
        self.system_state["status"] = "paused"
        self._save_state()
        
        return True
    
    def resume(self):
        """Resumes the AGI controller if paused."""
        if not self.running:
            logger.warning("AGI controller is not running")
            return False
            
        if not self.pause_requested:
            logger.warning("AGI controller is not paused")
            return False
            
        logger.info("Resuming AGI controller")
        self.pause_requested = False
        self.system_state["status"] = "running"
        self._save_state()
        
        return True
    
    def get_status(self):
        """Returns the current status of the AGI controller."""
        status = {
            "status": self.system_state["status"],
            "cycles_completed": self.cycle_count,
            "current_focus": self.system_state["current_focus"],
            "improvements_made": self.system_state["improvement_cycles"],
            "knowledge_items": self.system_state["knowledge_items"],
            "concepts_formed": self.system_state["concepts_formed"],
            "learning_goals": len(self.learning_goals),
            "component_priorities": self.component_priorities,
            "last_update": self.system_state["last_update"]
        }
        
        return status
    
    def get_recent_activities(self, limit=10):
        """Returns the most recent AGI cycles."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            SELECT cycle_number, timestamp, focus_area, actions_taken, outcomes
            FROM agi_cycles
            ORDER BY cycle_number DESC
            LIMIT ?
        """, (limit,))
        
        cycles = [
            {
                "cycle": row[0],
                "timestamp": row[1],
                "focus": row[2],
                "actions": row[3],
                "outcomes": row[4]
            }
            for row in c.fetchall()
        ]
        
        conn.close()
        return cycles

# Command-line interface for testing
if __name__ == "__main__":
    controller = AGIController()
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "start":
            controller.start()
            print("AGI controller started")
            
        elif command == "stop":
            controller.stop()
            print("AGI controller stopped")
            
        elif command == "status":
            status = controller.get_status()
            print(json.dumps(status, indent=2))
            
        elif command == "cycle":
            # Run a single cycle
            result = controller.execute_cycle()
            print(json.dumps(result, indent=2))
            
        elif command == "activities":
            activities = controller.get_recent_activities()
            print(json.dumps(activities, indent=2))
            
        else:
            print(f"Unknown command: {command}")
            print("Available commands: start, stop, status, cycle, activities")
    else:
        print("AGI Controller - Command Line Interface")
        print("Usage: python agi_controller.py [command]")
        print("Available commands: start, stop, status, cycle, activities")
"knowledge_acquisition",
                f"Researched {search_term} from {len(urls)} sources",
                f"Acquired {len(acquired_concepts)} new concepts"
            ))
            conn.commit()
            conn.close()
            
            # Update system state
            self.system_state["knowledge_items"] += len(acquired_concepts)
            
            # If we acquired enough knowledge, mark the goal as completed
            if len(acquired_concepts) >= 3:
                self.complete_learning_goal(selected_goal["id"])
                
            return {
                "success": True,
                "concepts_acquired": len(acquired_concepts),
                "goal": selected_goal["goal"]
            }
        else:
            logger.warning(f"Failed to acquire knowledge for {search_term}")
            
            # Record the failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("knowledge_acquisition", "acquisition_failures", 1))
            
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
                "knowledge_acquisition",
                f"Attempted to research {search_term}",
                "Failed to acquire meaningful concepts"
            ))
            conn.commit()
            conn.close()
            
            return {
                "success": False,
                "error": f"Failed to acquire knowledge about {search_term}"
            }
    
    def execute_concept_formation_cycle(self):
        """Executes a concept formation and abstraction cycle."""
        logger.info("Starting concept formation cycle")
        
        # Identify patterns in past optimizations or use knowledge
        abstractions = self.concept_system.identify_patterns_in_optimizations()
        
        if abstractions:
            logger.info(f"Identified {len(abstractions)} pattern abstractions")
            
            # Form higher-level concepts
            self.concept_system.generalize_concepts()
            
            # Get the current concept hierarchy
            hierarchy = self.concept_system.get_concept_hierarchy()
            
            # Record metrics
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO system_metrics (component, metric_name, metric_value) VALUES (?, ?, ?)",
                     ("concept_formation", "abstractions_created", len(abstractions)))
            
            # Update cycle information
            c.execute("""
                INSERT INTO agi_cycles 
                (cycle_number, focus_area, actions_taken, outcomes) 
                VALUES (?, ?, ?, ?)
            """, (
                self.cycle_count,
