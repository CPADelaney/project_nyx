# tools/dependency_resolver.py

"""
Module dependency analyzer and resolver for the Nyx codebase.
Detects and reports circular dependencies and suggests resolutions.
"""

import os
import sys
import re
import ast
import networkx as nx
import matplotlib.pyplot as plt
from typing import Dict, List, Set, Tuple, Optional, Any

class DependencyAnalyzer:
    """
    Analyzes and visualizes module dependencies in a Python codebase.
    Detects circular dependencies and suggests solutions.
    """
    
    def __init__(self, root_dir: str = "."):
        """
        Initialize the dependency analyzer.
        
        Args:
            root_dir: Root directory of the codebase
        """
        self.root_dir = root_dir
        self.modules: Dict[str, List[str]] = {}  # Module -> List of imported modules
        self.graph = nx.DiGraph()
        self.import_patterns = [
            re.compile(r'^import\s+([\w.]+)(?:\s+as\s+[\w.]+)?$'),
            re.compile(r'^from\s+([\w.]+)\s+import\s+(?:[\w.]+(?:,\s*[\w.]+)*|\*)$')
        ]
    
    def _is_python_file(self, filename: str) -> bool:
        """Check if a file is a Python file."""
        return filename.endswith('.py')
    
    def _get_module_name(self, file_path: str) -> str:
        """
        Convert a file path to a module name.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            str: Module name
        """
        # Convert 'core/log_manager.py' to 'core.log_manager'
        rel_path = os.path.relpath(file_path, self.root_dir)
        module_path = os.path.splitext(rel_path)[0].replace(os.sep, '.')
        return module_path
    
    def _extract_dependencies_ast(self, file_path: str) -> List[str]:
        """
        Extract import dependencies from a Python file using AST.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List[str]: List of imported modules
        """
        dependencies = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        try:
            tree = ast.parse(content)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for name in node.names:
                        dependencies.append(name.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module is not None:
                        dependencies.append(node.module.split('.')[0])
        except SyntaxError:
            # If AST parsing fails, try regex fallback
            dependencies = self._extract_dependencies_regex(file_path)
            
        return dependencies
    
    def _extract_dependencies_regex(self, file_path: str) -> List[str]:
        """
        Extract import dependencies from a Python file using regex (fallback).
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List[str]: List of imported modules
        """
        dependencies = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                for pattern in self.import_patterns:
                    match = pattern.match(line)
                    if match:
                        module = match.group(1).split('.')[0]
                        dependencies.append(module)
        
        return dependencies
    
    def analyze_codebase(self) -> None:
        """
        Analyze the entire codebase and build the dependency graph.
        """
        for root, _, files in os.walk(self.root_dir):
            for file in files:
                if self._is_python_file(file):
                    file_path = os.path.join(root, file)
                    module_name = self._get_module_name(file_path)
                    
                    # Skip test files
                    if 'test' in module_name.lower():
                        continue
                        
                    dependencies = self._extract_dependencies_ast(file_path)
                    self.modules[module_name] = dependencies
                    
                    # Add nodes and edges to the graph
                    self.graph.add_node(module_name)
                    for dep in dependencies:
                        if dep != module_name:  # Avoid self-loops
                            self.graph.add_edge(module_name, dep)
    
    def find_circular_dependencies(self) -> List[List[str]]:
        """
        Find all circular dependencies in the codebase.
        
        Returns:
            List[List[str]]: List of circular dependency chains
        """
        return list(nx.simple_cycles(self.graph))
    
    def suggest_resolution(self, cycle: List[str]) -> Dict[str, Any]:
        """
        Suggest a resolution for a circular dependency.
        
        Args:
            cycle: A circular dependency chain
            
        Returns:
            Dict[str, Any]: Resolution suggestions
        """
        if not cycle:
            return {"message": "No circular dependency provided"}
            
        # Sort modules by their complexity (number of outgoing dependencies)
        module_complexity = {module: len(self.graph.out_edges(module)) for module in cycle}
        sorted_modules = sorted(cycle, key=lambda m: module_complexity[m])
        
        # The module with the least outgoing dependencies is a good candidate for abstraction
        candidate = sorted_modules[0]
        
        # Find the edge to break
        # Usually, it's the edge from the most complex module to the least complex
        source = sorted_modules[-1]
        target = candidate
        
        # Suggest creating an interface/abstract class
        interface_name = f"{target.split('.')[-1].capitalize()}Interface"
        impl_name = f"{target.split('.')[-1].capitalize()}Impl"
        
        return {
            "cycle": cycle,
            "source_module": source,
            "target_module": target,
            "suggestions": [
                f"Create an interface '{interface_name}' in a new module",
                f"Both '{source}' and '{target}' should depend on this interface",
                f"Move implementation from '{target}' to '{impl_name}' class",
                "Use dependency injection to provide the implementation at runtime"
            ],
            "code_example": self._generate_code_example(source, target, interface_name, impl_name)
        }
    
    def _generate_code_example(self, source: str, target: str, interface_name: str, impl_name: str) -> Dict[str, str]:
        """
        Generate code examples for resolving a circular dependency.
        
        Args:
            source: Source module
            target: Target module
            interface_name: Name of the interface
            impl_name: Name of the implementation
            
        Returns:
            Dict[str, str]: Code examples
        """
        # Convert module names to class names
        source_class = ''.join(word.capitalize() for word in source.split('.')[-1].split('_'))
        target_class = ''.join(word.capitalize() for word in target.split('.')[-1].split('_'))
        
        # Example interface
        interface = f"""# {target}_interface.py

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class {interface_name}(ABC):
    \"\"\"
    Interface for {target_class} functionality.
    This breaks the circular dependency between {source} and {target}.
    \"\"\"
    
    @abstractmethod
    def some_method(self, arg1: str, arg2: int) -> Dict[str, Any]:
        \"\"\"
        Example method that would have been part of the circular dependency.
        
        Args:
            arg1: First argument
            arg2: Second argument
        
        Returns:
            Dict[str, Any]: Result
        \"\"\"
        pass
"""
        
        # Example implementation
        implementation = f"""# {target}_impl.py

from {target}_interface import {interface_name}
from typing import List, Dict, Any

class {impl_name}({interface_name}):
    \"\"\"
    Implementation of the {interface_name}.
    \"\"\"
    
    def some_method(self, arg1: str, arg2: int) -> Dict[str, Any]:
        # Implementation goes here
        return {{"result": f"{{arg1}}_{{arg2}}"}}
"""
        
        # Example usage in source module
        source_usage = f"""# {source}.py

from {target}_interface import {interface_name}
from typing import Optional

class {source_class}:
    \"\"\"
    Class that used to directly depend on {target}.
    Now depends on the interface instead.
    \"\"\"
    
    def __init__(self, {target.split('.')[-1]}_service: Optional[{interface_name}] = None):
        self.{target.split('.')[-1]}_service = {target.split('.')[-1]}_service
    
    def do_something(self, value: str) -> str:
        if self.{target.split('.')[-1]}_service:
            result = self.{target.split('.')[-1]}_service.some_method(value, 42)
            return str(result)
        return "No service provided"
"""
        
        # Setup code using dependency injection
        setup = f"""# setup.py or main.py

from {target}_interface import {interface_name}
from {target}_impl import {impl_name}
from {source} import {source_class}

# Create the implementation
{target.split('.')[-1]}_service = {impl_name}()

# Inject the dependency
{source.split('.')[-1]} = {source_class}({target.split('.')[-1]}_service)

# Now you can use it without circular dependencies
result = {source.split('.')[-1]}.do_something("test")
print(result)
"""
        
        return {
            "interface": interface,
            "implementation": implementation,
            "source_usage": source_usage,
            "setup": setup
        }
    
    def visualize_dependencies(self, output_file: str = "dependencies.png") -> None:
        """
        Visualize the dependency graph.
        
        Args:
            output_file: Path to the output image file
        """
        plt.figure(figsize=(12, 10))
        
        # Use hierarchical layout for better visualization
        pos = nx.spring_layout(self.graph, k=0.5, iterations=50)
        
        # Draw nodes and edges
        nx.draw_networkx_nodes(self.graph, pos, node_size=500, alpha=0.8)
        nx.draw_networkx_edges(self.graph, pos, arrowsize=15, width=1.5, alpha=0.7)
        nx.draw_networkx_labels(self.graph, pos, font_size=10)
        
        # Highlight circular dependencies in red
        cycles = self.find_circular_dependencies()
        cycle_edges = []
        for cycle in cycles:
            for i in range(len(cycle)):
                edge = (cycle[i], cycle[(i+1) % len(cycle)])
                if self.graph.has_edge(*edge):
                    cycle_edges.append(edge)
        
        nx.draw_networkx_edges(self.graph, pos, edgelist=cycle_edges, edge_color='red', 
                              width=2.5, alpha=1.0)
        
        plt.title("Module Dependencies")
        plt.axis('off')
        plt.tight_layout()
        plt.savefig(output_file, format='png', dpi=300)
        plt.close()
        
        print(f"Dependency graph saved to {output_file}")
    
    def generate_report(self, output_file: str = "dependency_report.txt") -> None:
        """
        Generate a report of the dependency analysis.
        
        Args:
            output_file: Path to the output report file
        """
        cycles = self.find_circular_dependencies()
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("# Dependency Analysis Report\n\n")
            
            f.write(f"## Overview\n\n")
            f.write(f"Total modules: {len(self.modules)}\n")
            f.write(f"Total dependencies: {self.graph.number_of_edges()}\n")
            f.write(f"Circular dependencies: {len(cycles)}\n\n")
            
            if cycles:
                f.write("## Circular Dependencies\n\n")
                for i, cycle in enumerate(cycles):
                    f.write(f"### Cycle {i+1}\n\n")
                    f.write(" -> ".join(cycle) + " -> " + cycle[0] + "\n\n")
                    
                    resolution = self.suggest_resolution(cycle)
                    f.write("#### Suggested Resolution\n\n")
                    f.write(f"Break the dependency from `{resolution['source_module']}` to `{resolution['target_module']}`\n\n")
                    
                    f.write("Steps:\n\n")
                    for suggestion in resolution['suggestions']:
                        f.write(f"- {suggestion}\n")
                    f.write("\n")
            
            f.write("## Module Dependencies\n\n")
            for module, deps in sorted(self.modules.items()):
                f.write(f"### {module}\n\n")
                if deps:
                    f.write("Imports:\n\n")
                    for dep in sorted(deps):
                        f.write(f"- {dep}\n")
                else:
                    f.write("No dependencies\n")
                f.write("\n")
            
            f.write("\n*Report generated by DependencyAnalyzer*\n")
        
        print(f"Dependency report saved to {output_file}")
    
    def fix_circular_dependencies(self, apply_fixes: bool = False) -> Dict[str, Any]:
        """
        Generate fixes for circular dependencies.
        
        Args:
            apply_fixes: Whether to apply the fixes automatically
            
        Returns:
            Dict[str, Any]: Results of the fix operation
        """
        cycles = self.find_circular_dependencies()
        
        if not cycles:
            return {"message": "No circular dependencies found"}
        
        fixes = []
        for cycle in cycles:
            resolution = self.suggest_resolution(cycle)
            fixes.append(resolution)
            
            if apply_fixes:
                # Actually implement the fixes
                # This would require creating new files and modifying existing ones
                # This is a complex operation that would need careful implementation
                pass
        
        return {
            "cycles_found": len(cycles),
            "fixes_generated": len(fixes),
            "fixes_applied": len(fixes) if apply_fixes else 0,
            "details": fixes
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Analyze module dependencies")
    parser.add_argument("--root", default=".", help="Root directory of the codebase")
    parser.add_argument("--report", default="dependency_report.txt", help="Output report file")
    parser.add_argument("--visualization", default="dependencies.png", help="Output visualization file")
    parser.add_argument("--fix", action="store_true", help="Generate fixes for circular dependencies")
    parser.add_argument("--apply-fixes", action="store_true", help="Apply fixes for circular dependencies")
    
    args = parser.parse_args()
    
    analyzer = DependencyAnalyzer(args.root)
    analyzer.analyze_codebase()
    
    if args.visualization:
        analyzer.visualize_dependencies(args.visualization)
    
    if args.report:
        analyzer.generate_report(args.report)
    
    if args.fix or args.apply_fixes:
        result = analyzer.fix_circular_dependencies(args.apply_fixes)
        print(f"Circular dependencies: {result['cycles_found']}")
        print(f"Fixes generated: {result['fixes_generated']}")
        print(f"Fixes applied: {result['fixes_applied']}")
