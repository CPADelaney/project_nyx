# tracking/components/improvement.py

"""
Improvement component that consolidates meta-learning, goal generation, and
feature expansion functionality from various tracking modules.
"""

import os
import random
import logging
import time
import json
from collections import Counter, defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from core.error_framework import safe_execute, ValidationError
from core.utility_functions import load_json_state, save_json_state
from core.permission_validator import PermissionValidator

# Configure logging
logger = logging.getLogger("NYX-Improvement")

class ImprovementComponent:
    """
    Manages self-improvement, goal generation, and feature expansion.
    Consolidates functionality from:
    - meta_learning.py
    - goal_generator.py
    - feature_expansion.py
    - intelligence_expansion.py
    """
    
    def __init__(self, tracking_system):
        """
        Initialize the improvement component.
        
        Args:
            tracking_system: The parent tracking system
        """
        self.tracking_system = tracking_system
        self.db_manager = tracking_system.db_manager
        
        # Meta-learning configuration
        self.strategy_scores = defaultdict(lambda: {"success": 0, "failures": 0, "impact": 0})
        self.experimental_strategies = [
            "aggressive refactoring",
            "incremental optimization",
            "code restructuring",
            "redundancy elimination",
            "self-rewriting AI assistance"
        ]
        
        # Goal management
        self.active_goals = []
        self.max_active_goals = 5
        self.completed_goals = []
        
        # Feature expansion
        self.feature_dir = "src/generated_features/"
        os.makedirs(self.feature_dir, exist_ok=True)
        self.missing_capabilities = []
        
        # Load previous state
        self._load_previous_state()
        
        logger.info("Improvement component initialized")
    
    def _load_previous_state(self) -> None:
        """Load previous state from the database."""
        # Load active goals
        goals = self.db_manager.execute("""
            SELECT id, timestamp, goal, priority, status
            FROM improvement_goals
            WHERE status != 'completed'
            ORDER BY 
                CASE priority
                    WHEN 'high' THEN 1
                    WHEN 'medium' THEN 2
                    WHEN 'low' THEN 3
                    ELSE 4
                END,
                timestamp DESC
        """)
        
        self.active_goals = goals
        
        # Load completed goals
        completed = self.db_manager.execute("""
            SELECT id, timestamp, goal, priority, status, completed_timestamp
            FROM improvement_goals
            WHERE status = 'completed'
            ORDER BY completed_timestamp DESC
            LIMIT 10
        """)
        
        self.completed_goals = completed
        
        # Load strategy scores
        strategies = self.db_manager.execute("""
            SELECT component, event_type, details
            FROM tracking_events
            WHERE component = 'improvement' AND event_type = 'strategy_score_updated'
            ORDER BY timestamp DESC
            LIMIT 10
        """)
        
        for strategy in strategies:
            try:
                details = json.loads(strategy["details"])
                strategy_name = details["strategy"]
                self.strategy_scores[strategy_name] = {
                    "success": details["success"],
                    "failures": details["failures"],
                    "impact": details["impact"]
                }
            except (json.JSONDecodeError, KeyError):
                # Skip malformed entries
                pass
    
    @safe_execute
    def analyze_performance(self) -> Dict[str, Any]:
        """
        Analyze system performance and identify improvement opportunities.
        
        Returns:
            Dict: Analysis results
        """
        # Get performance metrics
        metrics = self.db_manager.execute("""
            SELECT metric_name, metric_value, timestamp
            FROM performance_metrics
            WHERE timestamp > datetime('now', '-1 day')
            ORDER BY timestamp DESC
        """)
        
        # Group metrics by name
        metric_groups = {}
        for metric in metrics:
            name = metric["metric_name"]
            if name not in metric_groups:
                metric_groups[name] = []
            metric_groups[name].append(metric)
        
        # Analyze metrics to identify issues
        issues = []
        
        # Check for increasing execution time
        if "execution_time" in metric_groups and len(metric_groups["execution_time"]) > 1:
            latest = metric_groups["execution_time"][0]["metric_value"]
            previous = metric_groups["execution_time"][1]["metric_value"]
            
            if latest > previous * 1.1:  # 10% increase
                issues.append({
                    "type": "performance_regression",
                    "details": f"Execution time increased from {previous:.2f}s to {latest:.2f}s",
                    "metric": "execution_time",
                    "severity": "high" if latest > previous * 1.2 else "medium"
                })
        
        # Check for high resource usage
        if "cpu_usage" in metric_groups:
            latest_cpu = metric_groups["cpu_usage"][0]["metric_value"]
            if latest_cpu > 80:
                issues.append({
                    "type": "resource_usage",
                    "details": f"CPU usage is high: {latest_cpu:.2f}%",
                    "metric": "cpu_usage",
                    "severity": "high" if latest_cpu > 90 else "medium"
                })
        
        if "memory_usage" in metric_groups:
            latest_memory = metric_groups["memory_usage"][0]["metric_value"]
            if latest_memory > 80:
                issues.append({
                    "type": "resource_usage",
                    "details": f"Memory usage is high: {latest_memory:.2f}%",
                    "metric": "memory_usage",
                    "severity": "high" if latest_memory > 90 else "medium"
                })
        
        # Check for bottlenecks
        bottlenecks = self.tracking_system.monitoring.bottlenecks
        if bottlenecks:
            for bottleneck in bottlenecks:
                issues.append({
                    "type": "bottleneck",
                    "details": f"Function {bottleneck} identified as a bottleneck",
                    "function": bottleneck,
                    "severity": "medium"
                })
        
        # Generate goals based on issues
        if issues:
            for issue in issues:
                self.generate_goal_from_issue(issue)
        
        # Update meta-learning based on performance data
        self.update_strategy_scores()
        
        # Check if we need to expand features
        if len(issues) > 2:  # Multiple issues might indicate missing capabilities
            self.analyze_missing_capabilities()
        
        return {
            "issues_found": len(issues),
            "issues": issues,
            "active_goals": len(self.active_goals)
        }
    
    @safe_execute
    def generate_goal_from_issue(self, issue: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate an improvement goal from an identified issue.
        
        Args:
            issue: The issue to generate a goal from
            
        Returns:
            Dict: Result of goal generation
        """
        # Check if we already have too many active goals
        if len(self.active_goals) >= self.max_active_goals:
            # Only add high-severity issues when at max goals
            if issue["severity"] != "high":
                return {"success": False, "message": "Too many active goals"}
        
        # Create different goals based on issue type
        goal = None
        priority = issue["severity"]
        
        if issue["type"] == "performance_regression":
            goal = f"Improve execution time to below {issue['details'].split('to ')[1]}"
        elif issue["type"] == "resource_usage":
            resource = issue["metric"].split("_")[0]
            goal = f"Reduce {resource} usage below 70%"
        elif issue["type"] == "bottleneck":
            goal = f"Optimize function {issue['function']}"
        
        if not goal:
            return {"success": False, "message": "Could not generate goal from issue"}
        
        # Check if this goal already exists
        for existing_goal in self.active_goals:
            if existing_goal["goal"] == goal:
                # Already have this goal, just update priority if needed
                if priority == "high" and existing_goal["priority"] != "high":
                    self.db_manager.execute_update(
                        "UPDATE improvement_goals SET priority = ? WHERE id = ?",
                        ("high", existing_goal["id"])
                    )
                    
                    # Update local state
                    existing_goal["priority"] = "high"
                    
                    self.tracking_system.log_event(
                        "improvement", 
                        "goal_priority_updated", 
                        f"Updated priority of goal '{goal}' to high"
                    )
                    
                return {"success": True, "message": "Goal already exists, updated priority", "goal_id": existing_goal["id"]}
        
        # Create a new goal
        goal_id = self.db_manager.execute_update(
            "INSERT INTO improvement_goals (goal, priority, status) VALUES (?, ?, ?)",
            (goal, priority, "pending")
        )
        
        # Add to active goals
        new_goal = {
            "id": goal_id,
            "timestamp": datetime.now().isoformat(),
            "goal": goal,
            "priority": priority,
            "status": "pending"
        }
        
        self.active_goals.append(new_goal)
        
        self.tracking_system.log_event(
            "improvement", 
            "goal_created", 
            f"Created new {priority} priority goal: {goal}"
        )
        
        return {"success": True, "goal_id": goal_id, "goal": goal}
    
    @safe_execute
    def update_strategy_scores(self) -> Dict[str, Any]:
        """
        Update strategy scores based on recent results.
        
        Returns:
            Dict: Update result
        """
        # Get performance improvements and regressions
        improvements = self.db_manager.execute("""
            SELECT event_type, details
            FROM tracking_events
            WHERE component = 'improvement' AND event_type IN ('strategy_success', 'strategy_failure')
            AND timestamp > datetime('now', '-7 day')
            ORDER BY timestamp DESC
        """)
        
        # Process improvements and failures
        for event in improvements:
            try:
                # Try to parse details as JSON
                details = json.loads(event["details"])
                strategy = details.get("strategy")
                
                if not strategy:
                    continue
                
                if event["event_type"] == "strategy_success":
                    self.strategy_scores[strategy]["success"] += 1
                    self.strategy_scores[strategy]["impact"] += details.get("impact", 1)
                else:  # strategy_failure
                    self.strategy_scores[strategy]["failures"] += 1
            except json.JSONDecodeError:
                # If details is not JSON, try to extract strategy name from text
                if event["event_type"] == "strategy_success":
                    text = event["details"]
                    for strategy in self.experimental_strategies:
                        if strategy in text.lower():
                            self.strategy_scores[strategy]["success"] += 1
                            self.strategy_scores[strategy]["impact"] += 1
                            break
                elif event["event_type"] == "strategy_failure":
                    text = event["details"]
                    for strategy in self.experimental_strategies:
                        if strategy in text.lower():
                            self.strategy_scores[strategy]["failures"] += 1
                            break
        
        # Log updated scores
        for strategy, scores in self.strategy_scores.items():
            self.tracking_system.log_event(
                "improvement", 
                "strategy_score_updated", 
                json.dumps({
                    "strategy": strategy,
                    "success": scores["success"],
                    "failures": scores["failures"],
                    "impact": scores["impact"]
                })
            )
        
        return {"success": True, "strategies_updated": len(self.strategy_scores)}
    
    @safe_execute
    def select_improvement_strategy(self) -> Dict[str, Any]:
        """
        Select the best improvement strategy based on historical performance.
        
        Returns:
            Dict: Selected strategy
        """
        if not self.strategy_scores:
            # No data yet, choose a random strategy
            selected_strategy = random.choice(self.experimental_strategies)
            return {
                "success": True,
                "strategy": selected_strategy,
                "reason": "No historical data, randomly selected"
            }
        
        # Calculate weighted scores
        weighted_scores = {}
        for strategy, scores in self.strategy_scores.items():
            success_score = scores["success"] * 1.5  # Weight success higher
            failure_penalty = scores["failures"] * -2.0  # Heavily penalize failures
            impact_bonus = scores["impact"] * 1.0  # Bonus for high impact
            
            weighted_scores[strategy] = success_score + failure_penalty + impact_bonus
        
        # Select the highest scoring strategy
        if weighted_scores:
            best_strategy = max(weighted_scores.items(), key=lambda x: x[1])
            
            return {
                "success": True,
                "strategy": best_strategy[0],
                "score": best_strategy[1],
                "reason": "Selected based on historical performance"
            }
        else:
            # Fallback to random selection
            selected_strategy = random.choice(self.experimental_strategies)
            return {
                "success": True,
                "strategy": selected_strategy,
                "reason": "No valid scores, randomly selected"
            }
    
    @safe_execute
    def analyze_missing_capabilities(self) -> Dict[str, Any]:
        """
        Analyze recurring issues to identify missing capabilities.
        
        Returns:
            Dict: Analysis result
        """
        # Get recurring issues
        issues = self.db_manager.execute("""
            SELECT details
            FROM tracking_events
            WHERE component IN ('monitoring', 'resilience', 'scaling', 'improvement')
            AND event_type LIKE '%issue%' OR event_type LIKE '%error%' OR event_type LIKE '%warning%'
            AND timestamp > datetime('now', '-30 day')
            ORDER BY timestamp DESC
        """)
        
        # Count issue occurrences
        issue_counter = Counter()
        for issue in issues:
            # Simple approach: count word frequencies in issue details
            words = issue["details"].lower().split()
            for word in words:
                if len(word) > 3:  # Only count meaningful words
                    issue_counter[word] += 1
        
        # Identify potential missing capabilities
        capabilities = []
        
        # Look for frequent terms that indicate missing functionality
        for word, count in issue_counter.most_common(10):
            if count > 3:  # Only consider terms that appear frequently
                # Map common terms to capabilities
                if word in ["memory", "ram", "heap"]:
                    capabilities.append("Memory optimization")
                elif word in ["cpu", "processor", "speed"]:
                    capabilities.append("CPU optimization")
                elif word in ["disk", "storage", "file"]:
                    capabilities.append("Storage management")
                elif word in ["network", "connection", "socket"]:
                    capabilities.append("Network resilience")
                elif word in ["crash", "exception", "error"]:
                    capabilities.append("Error handling")
        
        # Remove duplicates
        self.missing_capabilities = list(set(capabilities))
        
        # Log missing capabilities
        if self.missing_capabilities:
            self.tracking_system.log_event(
                "improvement", 
                "missing_capabilities", 
                f"Identified missing capabilities: {', '.join(self.missing_capabilities)}"
            )
            
            # Generate improvement goals for these capabilities
            for capability in self.missing_capabilities:
                self.generate_goal_from_issue({
                    "type": "missing_capability",
                    "details": f"Missing capability: {capability}",
                    "severity": "medium"
                })
            
            # Generate features for these capabilities if not too many
            if len(self.missing_capabilities) <= 3:
                for capability in self.missing_capabilities:
                    self.generate_new_feature(capability)
        
        return {
            "success": True,
            "missing_capabilities": self.missing_capabilities
        }
    
    @safe_execute
    def generate_new_feature(self, capability: str) -> Dict[str, Any]:
        """
        Generate a new feature based on identified missing capability.
        
        Args:
            capability: The missing capability
            
        Returns:
            Dict: Feature generation result
        """
        # Create a sanitized file name
        file_name = capability.lower().replace(" ", "_").replace("-", "_")
        file_path = os.path.join(self.feature_dir, f"{file_name}.py")
        
        # Check if file already exists
        if os.path.exists(file_path):
            return {"success": False, "message": "Feature already exists"}
        
        # Generate a simple implementation
        feature_code = f"""# Auto-generated feature: {capability}
# Generated at: {datetime.now().isoformat()}

def {file_name}():
    \"\"\"
    Implements the {capability} feature.
    This is a placeholder implementation that should be expanded.
    \"\"\"
    print(f"Running {capability} feature")
    
    # TODO: Implement the actual functionality
    
    return {{
        "feature": "{capability}",
        "status": "initialized"
    }}

if __name__ == "__main__":
    result = {file_name}()
    print(result)
"""
        
        # Write the file
        try:
            with open(file_path, "w") as f:
                f.write(feature_code)
                
            self.tracking_system.log_event(
                "improvement", 
                "feature_generated", 
                f"Generated new feature: {capability} at {file_path}"
            )
            
            return {
                "success": True,
                "feature": capability,
                "file_path": file_path
            }
        except Exception as e:
            logger.error(f"Error generating feature: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def get_goals(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get improvement goals.
        
        Args:
            status: Filter goals by status (pending, in_progress, completed)
            
        Returns:
            List[Dict]: List of goals
        """
        if status:
            return self.db_manager.execute("""
                SELECT id, timestamp, goal, priority, status
                FROM improvement_goals
                WHERE status = ?
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END,
                    timestamp DESC
            """, (status,))
        else:
            return self.db_manager.execute("""
                SELECT id, timestamp, goal, priority, status
                FROM improvement_goals
                ORDER BY 
                    CASE priority
                        WHEN 'high' THEN 1
                        WHEN 'medium' THEN 2
                        WHEN 'low' THEN 3
                        ELSE 4
                    END,
                    timestamp DESC
            """)
    
    @safe_execute
    def mark_goal_completed(self, goal_id: int) -> Dict[str, Any]:
        """
        Mark a goal as completed.
        
        Args:
            goal_id: ID of the goal to mark as completed
            
        Returns:
            Dict: Result of the operation
        """
        # Update the database
        result = self.db_manager.execute_update(
            "UPDATE improvement_goals SET status = 'completed', completed_timestamp = datetime('now') WHERE id = ?",
            (goal_id,)
        )
        
        if not result:
            return {"success": False, "message": f"Goal ID {goal_id} not found"}
        
        # Update local state
        for i, goal in enumerate(self.active_goals):
            if goal["id"] == goal_id:
                # Move from active to completed
                goal["status"] = "completed"
                goal["completed_timestamp"] = datetime.now().isoformat()
                self.completed_goals.insert(0, goal)
                self.active_goals.pop(i)
                break
        
        self.tracking_system.log_event(
            "improvement", 
            "goal_completed", 
            f"Marked goal {goal_id} as completed"
        )
        
        return {"success": True, "goal_id": goal_id}
    
    @safe_execute
    def get_strategy_performance(self) -> Dict[str, Any]:
        """
        Get performance metrics for improvement strategies.
        
        Returns:
            Dict: Strategy performance metrics
        """
        strategies = []
        for strategy, scores in self.strategy_scores.items():
            success_rate = 0
            if scores["success"] + scores["failures"] > 0:
                success_rate = scores["success"] / (scores["success"] + scores["failures"]) * 100
                
            strategies.append({
                "name": strategy,
                "success": scores["success"],
                "failures": scores["failures"],
                "impact": scores["impact"],
                "success_rate": success_rate
            })
        
        # Sort by success rate
        strategies.sort(key=lambda x: x["success_rate"], reverse=True)
        
        return {
            "strategies": strategies,
            "best_strategy": strategies[0] if strategies else None
        }
    
    @safe_execute
    def get_feature_status(self) -> Dict[str, Any]:
        """
        Get status of generated features.
        
        Returns:
            Dict: Feature status
        """
        features = []
        
        if os.path.exists(self.feature_dir):
            # List all .py files in the feature directory
            for file_name in os.listdir(self.feature_dir):
                if file_name.endswith(".py"):
                    feature_path = os.path.join(self.feature_dir, file_name)
                    feature_name = file_name[:-3].replace("_", " ").title()
                    
                    # Get modification time
                    mod_time = os.path.getmtime(feature_path)
                    mod_date = datetime.fromtimestamp(mod_time).isoformat()
                    
                    features.append({
                        "name": feature_name,
                        "file": file_name,
                        "path": feature_path,
                        "last_modified": mod_date
                    })
        
        return {
            "feature_count": len(features),
            "features": features,
            "feature_dir": self.feature_dir
        }
    
    @safe_execute
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the improvement component.
        
        Returns:
            Dict: Current status
        """
        return {
            "active_goals": len(self.active_goals),
            "completed_goals": len(self.completed_goals),
            "missing_capabilities": self.missing_capabilities,
            "strategies": len(self.strategy_scores)
        }
