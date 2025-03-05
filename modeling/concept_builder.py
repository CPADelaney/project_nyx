# modeling/concept_builder.py

import os
import json
import numpy as np
import sqlite3
from datetime import datetime
import networkx as nx
from sklearn.cluster import DBSCAN
from core.log_manager import initialize_log_db, LOG_DB

class ConceptualModeling:
    """Builds higher-level abstractions from observed patterns and experiences."""
    
    def __init__(self):
        initialize_log_db()
        self._initialize_database()
        self.concept_graph = nx.DiGraph()
        self._load_concept_graph()
        
    def _initialize_database(self):
        """Creates tables for concept modeling."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE IF NOT EXISTS abstract_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_name TEXT UNIQUE,
                    abstraction_level INTEGER,
                    description TEXT,
                    created_timestamp TIMESTAMP
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS concept_examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_id INTEGER,
                    example_type TEXT,
                    example_data TEXT,
                    source_context TEXT,
                    FOREIGN KEY (concept_id) REFERENCES abstract_concepts(id)
                )''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS concept_hierarchy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_concept_id INTEGER,
                    child_concept_id INTEGER,
                    relationship_strength REAL,
                    FOREIGN KEY (parent_concept_id) REFERENCES abstract_concepts(id),
                    FOREIGN KEY (child_concept_id) REFERENCES abstract_concepts(id)
                )''')
                
        conn.commit()
        conn.close()
    
    def _load_concept_graph(self):
        """Loads the concept hierarchy into a NetworkX graph."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Load all concepts as nodes
        c.execute("SELECT id, concept_name, abstraction_level, description FROM abstract_concepts")
        for concept_id, name, level, description in c.fetchall():
            self.concept_graph.add_node(concept_id, name=name, level=level, description=description)
        
        # Load all relationships as edges
        c.execute("SELECT parent_concept_id, child_concept_id, relationship_strength FROM concept_hierarchy")
        for parent_id, child_id, strength in c.fetchall():
            self.concept_graph.add_edge(parent_id, child_id, weight=strength)
            
        conn.close()
    
    def identify_patterns_in_optimizations(self):
        """Identifies recurring patterns in successful code optimizations."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Get successful optimizations
        c.execute("""
            SELECT o.function_name, o.execution_time, m.details 
            FROM optimization_logs o
            JOIN ai_self_modifications m ON o.function_name = m.target_function
            WHERE o.success = 1
            ORDER BY o.execution_time
        """)
        
        optimizations = c.fetchall()
        conn.close()
        
        if not optimizations:
            print("No successful optimizations found for pattern analysis")
            return []
            
        # Group similar optimizations (simplified)
        optimization_types = {}
        
        for func_name, exec_time, details in optimizations:
            # Identify the type of optimization from the details
            opt_type = self._categorize_optimization(details)
            
            if opt_type not in optimization_types:
                optimization_types[opt_type] = []
                
            optimization_types[opt_type].append({
                "function": func_name,
                "execution_time": exec_time,
                "details": details
            })
            
        # For each group, identify common patterns and abstract
        abstractions = []
        for opt_type, examples in optimization_types.items():
            if len(examples) >= 3:  # Require at least 3 examples to form an abstraction
                abstraction = self._create_abstraction_from_examples(opt_type, examples)
                abstractions.append(abstraction)
                
        return abstractions
    
    def _categorize_optimization(self, details):
        """Categorizes an optimization based on its description."""
        categories = {
            "loop_optimization": ["loop", "iteration", "for each"],
            "memory_efficiency": ["memory", "allocation", "buffer"],
            "algorithm_improvement": ["algorithm", "complexity", "approach"],
            "parallelization": ["parallel", "concurrent", "thread"],
            "code_structure": ["refactor", "structure", "organization"]
        }
        
        details_lower = details.lower()
        
        for category, keywords in categories.items():
            if any(keyword in details_lower for keyword in keywords):
                return category
                
        return "general_optimization"
    
    def _create_abstraction_from_examples(self, opt_type, examples):
        """Creates a higher-level abstraction from examples."""
        # Generate a description of the abstraction
        example_count = len(examples)
        avg_improvement = np.mean([ex.get("execution_time", 0) for ex in examples])
        
        description = f"A pattern of {opt_type} identified across {example_count} functions, "
        description += f"providing an average execution improvement of {avg_improvement:.2f}."
        
        # Save the abstraction to the database
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Check if a similar abstraction already exists
        c.execute("SELECT id FROM abstract_concepts WHERE concept_name LIKE ?", (f"%{opt_type}%",))
        existing = c.fetchone()
        
        if existing:
            concept_id = existing[0]
            # Update the existing concept
            c.execute("UPDATE abstract_concepts SET description = ? WHERE id = ?", 
                     (description, concept_id))
        else:
            # Create a new concept
            c.execute("""
                INSERT INTO abstract_concepts 
                (concept_name, abstraction_level, description, created_timestamp) 
                VALUES (?, ?, ?, datetime('now'))
            """, (f"{opt_type}_pattern", 1, description))
            
            concept_id = c.lastrowid
            
        # Add the examples to the concept
        for example in examples:
            c.execute("""
                INSERT INTO concept_examples
                (concept_id, example_type, example_data, source_context)
                VALUES (?, ?, ?, ?)
            """, (concept_id, "optimization", json.dumps(example), example["function"]))
            
        conn.commit()
        conn.close()
        
        # Update the concept graph
        if concept_id not in self.concept_graph:
            self.concept_graph.add_node(concept_id, name=f"{opt_type}_pattern", 
                                       level=1, description=description)
        
        return {
            "concept_id": concept_id,
            "concept_name": f"{opt_type}_pattern",
            "description": description,
            "examples": examples
        }
    
    def generalize_concepts(self):
        """Creates higher-level abstractions by grouping related lower-level concepts."""
        # Get all concepts at level 1 (direct abstractions)
        level_1_concepts = [n for n, d in self.concept_graph.nodes(data=True) if d.get('level') == 1]
        
        if len(level_1_concepts) < 3:
            print("Not enough level 1 concepts to form higher-level abstractions")
            return
            
        # For simplicity, manually create some higher-level concepts
        # In a real system, this would use clustering or other ML techniques
        concept_groups = {
            "efficiency_patterns": ["loop_optimization_pattern", "memory_efficiency_pattern"],
            "architecture_patterns": ["code_structure_pattern", "algorithm_improvement_pattern"],
            "resource_optimization": ["parallelization_pattern", "memory_efficiency_pattern"]
        }
        
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        for higher_concept, related_patterns in concept_groups.items():
            # Get IDs of the related patterns
            c.execute("SELECT id FROM abstract_concepts WHERE " + 
                     " OR ".join(["concept_name = ?" for _ in related_patterns]), 
                     related_patterns)
            
            related_ids = [row[0] for row in c.fetchall()]
            
            if len(related_ids) < 2:
                continue
                
            # Create the higher-level concept
            description = f"A higher-level pattern combining {', '.join(related_patterns)}"
            
            c.execute("""
                INSERT INTO abstract_concepts 
                (concept_name, abstraction_level, description, created_timestamp) 
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(concept_name) DO UPDATE SET description = ?
            """, (higher_concept, 2, description, description))
            
            higher_concept_id = c.lastrowid if c.lastrowid else c.execute(
                "SELECT id FROM abstract_concepts WHERE concept_name = ?", 
                (higher_concept,)).fetchone()[0]
            
            # Create relationships to the lower-level concepts
            for related_id in related_ids:
                c.execute("""
                    INSERT INTO concept_hierarchy
                    (parent_concept_id, child_concept_id, relationship_strength)
                    VALUES (?, ?, ?)
                    ON CONFLICT(parent_concept_id, child_concept_id) DO UPDATE SET relationship_strength = ?
                """, (higher_concept_id, related_id, 0.8, 0.8))
                
                # Update the concept graph
                if higher_concept_id not in self.concept_graph:
                    self.concept_graph.add_node(higher_concept_id, name=higher_concept, 
                                             level=2, description=description)
                                             
                self.concept_graph.add_edge(higher_concept_id, related_id, weight=0.8)
                
        conn.commit()
        conn.close()
    
    def get_concept_hierarchy(self):
        """Returns the full concept hierarchy as a nested dictionary."""
        # Find all root concepts (level 2 or higher with no parents)
        roots = [n for n, d in self.concept_graph.nodes(data=True) 
                if d.get('level', 0) >= 2 and self.concept_graph.in_degree(n) == 0]
                
        hierarchy = {}
        
        for root in roots:
            hierarchy[self.concept_graph.nodes[root]['name']] = self._get_subtree(root)
            
        return hierarchy
    
    def _get_subtree(self, node_id):
        """Recursively builds a subtree of the concept hierarchy."""
        children = list(self.concept_graph.successors(node_id))
        
        if not children:
            return {
                "description": self.concept_graph.nodes[node_id].get('description', ''),
                "children": []
            }
            
        return {
            "description": self.concept_graph.nodes[node_id].get('description', ''),
            "children": [
                {self.concept_graph.nodes[child]['name']: self._get_subtree(child)}
                for child in children
            ]
        }
        
    def apply_concept_to_new_problem(self, problem_description, target_function=None):
        """Applies learned abstract concepts to a new optimization problem."""
        # This would use a similarity search to find the most relevant concept
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Get all concepts with their descriptions
        c.execute("SELECT id, concept_name, description FROM abstract_concepts")
        concepts = c.fetchall()
        
        # Find the most relevant concept (simplified)
        most_relevant = None
        highest_relevance = 0
        
        for concept_id, name, description in concepts:
            relevance = self._calculate_relevance(problem_description, description)
            
            if relevance > highest_relevance:
                most_relevant = (concept_id, name, description)
                highest_relevance = relevance
                
        if not most_relevant or highest_relevance < 0.3:
            conn.close()
            return {"success": False, "message": "No relevant concepts found"}
            
        # Get examples of this concept
        c.execute("SELECT example_data FROM concept_examples WHERE concept_id = ?", (most_relevant[0],))
        examples = [json.loads(row[0]) for row in c.fetchall()]
        
        # Generate a solution approach based on the concept and examples
        solution_approach = self._generate_solution_approach(most_relevant, examples, problem_description)
        
        conn.close()
        
        return {
            "success": True,
            "concept": most_relevant[1],
            "description": most_relevant[2],
            "approach": solution_approach,
            "confidence": highest_relevance
        }
    
    def _calculate_relevance(self, problem, concept_description):
        """Calculates the relevance of a concept to a problem (simplified)."""
        # In a real system, this would use embeddings and semantic similarity
        problem_words = set(problem.lower().split())
        concept_words = set(concept_description.lower().split())
        
        intersection = problem_words.intersection(concept_words)
        
        if not intersection:
            return 0
            
        return len(intersection) / (len(problem_words) + len(concept_words) - len(intersection))
    
    def _generate_solution_approach(self, concept, examples, problem):
        """Generates a solution approach based on a concept and its examples."""
        # In a real system, this would use more sophisticated generation
        concept_name, description = concept[1], concept[2]
        
        approach = f"Based on the '{concept_name}' pattern:\n\n"
        approach += f"{description}\n\n"
        approach += "Suggested approach:\n"
        
        if "loop_optimization" in concept_name:
            approach += "1. Examine loop structures for redundant operations\n"
            approach += "2. Consider replacing loops with list comprehensions\n"
            approach += "3. Move invariant calculations outside of loops\n"
        elif "memory_efficiency" in concept_name:
            approach += "1. Review memory allocation patterns\n"
            approach += "2. Consider using generators instead of storing all data\n"
            approach += "3. Implement lazy loading where appropriate\n"
        elif "algorithm_improvement" in concept_name:
            approach += "1. Analyze the algorithmic complexity\n"
            approach += "2. Look for more efficient algorithms for the specific task\n"
            approach += "3. Consider space-time tradeoffs\n"
        else:
            approach += "1. Study the successful examples of this pattern\n"
            approach += "2. Identify common elements that can be applied\n"
            approach += "3. Adapt the pattern to the specific context\n"
            
        # Add an example if available
        if examples:
            approach += f"\nReference example:\n{examples[0].get('function', 'Unknown')} - {examples[0].get('details', 'No details')}\n"
            
        return approach

# Usage example 
if __name__ == "__main__":
    modeling = ConceptualModeling()
    
    # Identify patterns in past optimizations
    abstractions = modeling.identify_patterns_in_optimizations()
    
    # Create higher-level concepts
    modeling.generalize_concepts()
    
    # Get the full concept hierarchy
    hierarchy = modeling.get_concept_hierarchy()
    print(json.dumps(hierarchy, indent=2))
    
    # Apply a concept to a new problem
    solution = modeling.apply_concept_to_new_problem(
        "Function has nested loops with redundant calculations"
    )
    print(solution["approach"] if solution["success"] else solution["message"])
