# core/self_modification.py

import os
import sqlite3
import subprocess
import ast
import json
import openai
import torch
import numpy as np
from datetime import datetime
from core.log_manager import initialize_log_db, LOG_DB
from modeling.concept_builder import ConceptualModeling
from core.secrets_manager import get_secret

class SelfModification:
    """Implements a more sophisticated self-modification system that leverages learned patterns."""
    
    def __init__(self):
        initialize_log_db()
        self._initialize_database()
        self.concept_model = ConceptualModeling()
        self.target_file = "src/nyx_core.py"
        self.backup_dir = "logs/modification_backups"
        self.modification_history = []
        
        # Securely get the OpenAI API key
        self.openai_api_key = get_secret("OPENAI_API_KEY")
        if self.openai_api_key:
            openai.api_key = self.openai_api_key
        else:
            logger.warning("OpenAI API key not found. Some features will be unavailable.")
            
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _initialize_database(self):
        """Initializes database tables for tracking modifications."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS modification_experiments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    target_component TEXT,
                    approach_used TEXT,
                    hypothesis TEXT,
                    result_success INTEGER,
                    performance_change REAL,
                    insights_gained TEXT
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS modification_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE,
                    description TEXT,
                    pattern TEXT,
                    success_rate REAL,
                    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP
                )''')
                
        conn.commit()
        conn.close()
    
    def create_backup(self):
        """Creates a backup of the target file before modification."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"nyx_core_{timestamp}.py")
        
        try:
            shutil.copy(self.target_file, backup_path)
            print(f"Created backup at {backup_path}")
            return backup_path
        except Exception as e:
            print(f"Error creating backup: {str(e)}")
            return None
    
    def analyze_codebase(self):
        """Analyzes the codebase to identify components and relationships."""
        if not os.path.exists(self.target_file):
            print(f"Target file {self.target_file} not found")
            return None
            
        with open(self.target_file, "r", encoding="utf-8") as file:
            source_code = file.read()
            
        try:
            tree = ast.parse(source_code)
            
            # Extract functions and their relationships
            functions = {}
            function_calls = {}
            imports = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions[node.name] = {
                        "name": node.name,
                        "line_number": node.lineno,
                        "args": [arg.arg for arg in node.args.args],
                        "docstring": ast.get_docstring(node),
                        "complexity": self._calculate_complexity(node)
                    }
                    
                    # Track function calls within this function
                    function_calls[node.name] = []
                    
                    for subnode in ast.walk(node):
                        if isinstance(subnode, ast.Call) and isinstance(subnode.func, ast.Name):
                            called_func = subnode.func.id
                            function_calls[node.name].append(called_func)
                
                elif isinstance(node, ast.Import) or isinstance(node, ast.ImportFrom):
                    if isinstance(node, ast.Import):
                        for name in node.names:
                            imports.append(name.name)
                    else:  # ImportFrom
                        for name in node.names:
                            imports.append(f"{node.module}.{name.name}")
            
            # Calculate function dependencies
            dependencies = {}
            for func, calls in function_calls.items():
                dependencies[func] = [call for call in calls if call in functions]
            
            return {
                "functions": functions,
                "dependencies": dependencies,
                "imports": imports
            }
            
        except SyntaxError as e:
            print(f"Syntax error in {self.target_file}: {str(e)}")
            return None
    
    def _calculate_complexity(self, node):
        """Calculates the cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for subnode in ast.walk(node):
            if isinstance(subnode, (ast.If, ast.While, ast.For)):
                complexity += 1
            elif isinstance(subnode, ast.BoolOp) and isinstance(subnode.op, ast.And):
                complexity += len(subnode.values) - 1
        
        return complexity
    
    def identify_optimization_candidates(self):
        """Identifies functions that are candidates for optimization."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Get execution times from performance logs
        c.execute("""
            SELECT function_name, AVG(execution_time) as avg_time
            FROM optimization_logs
            GROUP BY function_name
            ORDER BY avg_time DESC
        """)
        
        slow_functions = c.fetchall()
        
        # Get code analysis for complexity
        codebase = self.analyze_codebase()
        
        if not codebase or not codebase["functions"]:
            conn.close()
            return []
            
        # Combine execution time with complexity metrics
        candidates = []
        
        for func_name, avg_time in slow_functions:
            if func_name in codebase["functions"]:
                complexity = codebase["functions"][func_name]["complexity"]
                dependency_count = len(codebase["dependencies"].get(func_name, []))
                
                # Calculate an optimization priority score
                priority = (avg_time * 0.6) + (complexity * 0.3) + (dependency_count * 0.1)
                
                candidates.append({
                    "function": func_name,
                    "avg_execution_time": avg_time,
                    "complexity": complexity,
                    "dependencies": dependency_count,
                    "priority_score": priority
                })
        
        conn.close()
        
        # Sort by priority score
        candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return candidates
    
    def design_modification_experiment(self, target_function):
        """Designs an experiment to optimize a function based on learned concepts."""
        # Get function details
        codebase = self.analyze_codebase()
        if not codebase or target_function not in codebase["functions"]:
            return None
            
        function_details = codebase["functions"][target_function]
        
        # Get the actual function code
        with open(self.target_file, "r", encoding="utf-8") as file:
            source_code = file.read()
            
        tree = ast.parse(source_code)
        function_code = None
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == target_function:
                function_code = ast.get_source_segment(source_code, node)
                break
                
        if not function_code:
            return None
        
        # Create a problem description
        problem_description = f"Function '{target_function}' with complexity {function_details['complexity']} "
        
        if function_details["complexity"] > 5:
            problem_description += "has high cyclomatic complexity. "
        
        if len(function_details["args"]) > 5:
            problem_description += "has many parameters. "
            
        # Check for common inefficiency patterns
        if "for" in function_code and "for" in function_code.split("for")[1]:
            problem_description += "contains nested loops. "
            
        if function_code.count("if") > 3:
            problem_description += "has multiple conditional branches. "
            
        # Apply conceptual knowledge to the problem
        solution = self.concept_model.apply_concept_to_new_problem(problem_description, target_function)
        
        if not solution["success"]:
            # Fall back to a general approach
            approach = "Apply standard optimization techniques such as reducing complexity and redundant operations."
            hypothesis = "Reducing the function's complexity will improve its performance."
            concept = "general_optimization"
        else:
            approach = solution["approach"]
            hypothesis = f"Applying the {solution['concept']} pattern will improve performance."
            concept = solution["concept"]
            
        experiment = {
            "target_function": target_function,
            "function_code": function_code,
            "problem_description": problem_description,
            "approach": approach,
            "hypothesis": hypothesis,
            "concept_applied": concept
        }
        
        # Store the experiment design in the database
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            INSERT INTO modification_experiments
            (target_component, approach_used, hypothesis, result_success)
            VALUES (?, ?, ?, 0)
        """, (target_function, concept, hypothesis))
        experiment_id = c.lastrowid
        conn.commit()
        conn.close()
        
        experiment["id"] = experiment_id
        return experiment
    
    def execute_modification(self, experiment):
        """Executes the designed modification experiment."""
        if not experiment or not self.openai_api_key:
            return {"success": False, "message": "Invalid experiment or missing API key"}
            
        # Create a backup before modification
        backup_path = self.create_backup()
        if not backup_path:
            return {"success": False, "message": "Failed to create backup"}
            
        # Generate improved code using LLM
        function_code = experiment["function_code"]
        problem = experiment["problem_description"]
        approach = experiment["approach"]
        
        prompt = f"""
        Optimize the following Python function based on the approach provided:
        
        FUNCTION CODE:
        {function_code}
        
        PROBLEM DESCRIPTION:
        {problem}
        
        OPTIMIZATION APPROACH:
        {approach}
        
        Provide only the improved function code with no additional explanation.
        """
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert programmer focused on performance optimization."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            improved_code = response.choices[0].message.content.strip()
            
            # Verify the generated code is valid Python
            try:
                ast.parse(improved_code)
            except SyntaxError:
                return {
                    "success": False, 
                    "message": "Generated code has syntax errors",
                    "original_code": function_code,
                    "generated_code": improved_code
                }
                
            # Apply the modification to the file
            with open(self.target_file, "r", encoding="utf-8") as file:
                original_content = file.read()
                
            # Replace the function in the file
            modified_content = original_content.replace(function_code, improved_code)
            
            with open(self.target_file, "w", encoding="utf-8") as file:
                file.write(modified_content)
                
            return {
                "success": True,
                "message": "Modification applied successfully",
                "original_code": function_code,
                "improved_code": improved_code,
                "backup_path": backup_path
            }
            
        except Exception as e:
            # Restore from backup if anything goes wrong
            if backup_path and os.path.exists(backup_path):
                shutil.copy(backup_path, self.target_file)
                
            return {"success": False, "message": f"Error during modification: {str(e)}"}
    
    def evaluate_modification(self, experiment_id, modification_result):
        """Evaluates the performance impact of a modification."""
        if not modification_result["success"]:
            # Update the experiment with failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("""
                UPDATE modification_experiments
                SET result_success = 0, insights_gained = ?
                WHERE id = ?
            """, (modification_result["message"], experiment_id))
            conn.commit()
            conn.close()
            
            return {"success": False, "message": modification_result["message"]}
            
        # Measure performance before and after
        # In a real system, this would use more sophisticated benchmarking
        try:
            # Run tests to ensure functionality
            subprocess.run(["python3", "-m", "unittest", "tests/self_test.py"], check=True)
            
            # Measure performance
            start_time = datetime.now()
            subprocess.run(["python3", self.target_file], check=True)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            # Get previous execution time
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("""
                SELECT AVG(execution_time) 
                FROM optimization_logs 
                WHERE function_name = (
                    SELECT target_component 
                    FROM modification_experiments 
                    WHERE id = ?
                )
            """, (experiment_id,))
            
            previous_time = c.fetchone()[0]
            
            if not previous_time:
                previous_time = execution_time * 1.2  # Assume 20% worse if no previous data
                
            performance_change = (previous_time - execution_time) / previous_time * 100
            
            # Record the result
            target_function = c.execute("SELECT target_component FROM modification_experiments WHERE id = ?", 
                                      (experiment_id,)).fetchone()[0]
            
            c.execute("""
                UPDATE modification_experiments
                SET result_success = ?, performance_change = ?, insights_gained = ?
                WHERE id = ?
            """, (
                1 if performance_change > 0 else 0,
                performance_change,
                f"Performance changed by {performance_change:.2f}%",
                experiment_id
            ))
            
            # Update function performance logs
            c.execute("""
                INSERT INTO optimization_logs
                (function_name, execution_time, success)
                VALUES (?, ?, ?)
            """, (target_function, execution_time, 1 if performance_change > 0 else 0))
            
            conn.commit()
            
            # If performance worsened, revert the change
            if performance_change <= 0:
                backup_path = modification_result["backup_path"]
                if backup_path and os.path.exists(backup_path):
                    shutil.copy(backup_path, self.target_file)
                    
                    c.execute("""
                        UPDATE modification_experiments
                        SET insights_gained = ?
                        WHERE id = ?
                    """, (f"Performance worsened by {-performance_change:.2f}%. Change reverted.", experiment_id))
                    
                    conn.commit()
                    
                    result = {
                        "success": False,
                        "message": f"Performance worsened by {-performance_change:.2f}%. Change reverted.",
                        "original_code": modification_result["original_code"],
                        "improved_code": modification_result["improved_code"],
                        "performance_change": performance_change
                    }
            else:
                result = {
                    "success": True,
                    "message": f"Performance improved by {performance_change:.2f}%",
                    "original_code": modification_result["original_code"],
                    "improved_code": modification_result["improved_code"],
                    "performance_change": performance_change
                }
                
            conn.close()
            return result
            
        except subprocess.CalledProcessError as e:
            # Functionality is broken, revert the change
            backup_path = modification_result["backup_path"]
            if backup_path and os.path.exists(backup_path):
                shutil.copy(backup_path, self.target_file)
                
            # Record the failure
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("""
                UPDATE modification_experiments
                SET result_success = 0, insights_gained = ?
                WHERE id = ?
            """, (f"Modification broke functionality: {str(e)}", experiment_id))
            conn.commit()
            conn.close()
            
            return {
                "success": False,
                "message": f"Modification broke functionality: {str(e)}",
                "original_code": modification_result["original_code"],
                "improved_code": modification_result["improved_code"]
            }
    
    def extract_insights(self, experiment_id, evaluation_result):
        """Extracts insights from the modification experiment to improve future modifications."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        c.execute("""
            SELECT target_component, approach_used, result_success, performance_change
            FROM modification_experiments
            WHERE id = ?
        """, (experiment_id,))
        
        experiment = c.fetchone()
        if not experiment:
            conn.close()
            return
            
        target_function, approach_used, success, performance_change = experiment
        
        # Update success rate for the approach
        c.execute("""
            SELECT success_rate 
            FROM modification_templates 
            WHERE name = ?
        """, (approach_used,))
        
        template = c.fetchone()
        
        if template:
            # Update existing template
            c.execute("""
                UPDATE modification_templates
                SET success_rate = (success_rate + ?) / 2
                WHERE name = ?
            """, (1.0 if success else 0.0, approach_used))
        else:
            # Create new template
            pattern_description = "Automatically generated pattern based on experimental results"
            
            if evaluation_result["success"]:
                pattern = evaluation_result["improved_code"]
            else:
                pattern = evaluation_result["original_code"]
                
            c.execute("""
                INSERT INTO modification_templates
                (name, description, pattern, success_rate)
                VALUES (?, ?, ?, ?)
            """, (approach_used, pattern_description, pattern, 1.0 if success else 0.0))
            
        conn.commit()
        conn.close()
        
        # Integrate with concept model
        if evaluation_result["success"]:
            # Feed successful experiment back into concept model
            self.concept_model.identify_patterns_in_optimizations()
            self.concept_model.generalize_concepts()
    
    def run_improvement_cycle(self):
        """Runs a complete self-improvement cycle."""
        print("Starting self-improvement cycle...")
        
        # Identify optimization candidates
        candidates = self.identify_optimization_candidates()
        if not candidates:
            print("No optimization candidates found")
            return
            
        print(f"Identified {len(candidates)} optimization candidates")
        
        # Select top candidate
        target_function = candidates[0]["function"]
        print(f"Selected {target_function} for optimization (priority score: {candidates[0]['priority_score']:.2f})")
        
        # Design the modification experiment
        experiment = self.design_modification_experiment(target_function)
        if not experiment:
            print(f"Failed to design experiment for {target_function}")
            return
            
        print(f"Designed experiment using {experiment['concept_applied']} approach")
        
        # Execute the modification
        modification_result = self.execute_modification(experiment)
        if not modification_result["success"]:
            print(f"Modification failed: {modification_result['message']}")
            return
            
        print("Modification applied successfully")
        
        # Evaluate the modification
        evaluation = self.evaluate_modification(experiment["id"], modification_result)
        
        if evaluation["success"]:
            print(f"Optimization successful: {evaluation['message']}")
        else:
            print(f"Optimization unsuccessful: {evaluation['message']}")
            
        # Extract insights
        self.extract_insights(experiment["id"], evaluation)
        print("Insights extracted and integrated into knowledge base")
        
        return {
            "target_function": target_function,
            "approach": experiment["concept_applied"],
            "result": evaluation["message"],
            "success": evaluation["success"]
        }

# Usage example
if __name__ == "__main__":
    modifier = SelfModification()
    result = modifier.run_improvement_cycle()
    print(json.dumps(result, indent=2) if result else "No improvement made")
