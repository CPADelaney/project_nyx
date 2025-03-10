#!/usr/bin/env python3
"""
Script to scan for old tracking module imports and optionally update them.
This can be run directly or as part of a GitHub Action.
"""

import os
import re
import argparse
import json
from typing import Dict, List, Tuple, Any

# Mapping of old imports to new components
IMPORT_MAPPING = {
    # AI modules
    "tracking.ai_autonomous_expansion": "scaling",
    "tracking.ai_scaling": "scaling",
    "tracking.ai_network_coordinator": "scaling",
    
    # Performance modules
    "tracking.performance_tracker": "monitoring",
    "tracking.bottleneck_detector": "monitoring",
    
    # Redundancy and healing modules
    "tracking.redundancy_manager": "resilience", 
    "tracking.self_healing": "resilience",
    "tracking.self_infrastructure_optimization": "scaling",
    "tracking.self_preservation": "resilience",
    "tracking.self_execution": "resilience",
    "tracking.self_propagation": "resilience",
    "tracking.self_sustainability": "scaling",
    
    # Improvement modules
    "tracking.goal_generator": "improvement",
    "tracking.feature_expansion": "improvement",
    "tracking.meta_learning": "improvement",
    "tracking.intelligence_expansion": "improvement",
    "tracking.final_recursive_lock": "improvement"
}

# Class mappings for import from x import Y
CLASS_MAPPINGS = {
    "AIAutonomousExpansion": "scaling",
    "AIScalingManager": "scaling",
    "AINetworkCoordinator": "scaling",
    "AIEvolution": "improvement",
    "AISelfHealing": "resilience",
    "AIInfrastructureOptimization": "scaling",
    "AIFinalRecursiveLock": "improvement",
    "FeatureExpansion": "improvement",
    "GoalGenerator": "improvement",
    "MetaLearning": "improvement",
    "RedundancyManager": "resilience",
    "SelfPreservation": "resilience",
    "SelfExecutionManager": "resilience",
    "SelfPropagation": "resilience"
}

# Function mappings
FUNCTION_MAPPINGS = {
    "measure_execution_time": "monitoring.measure_execution_time",
    "profile_execution": "monitoring.profile_execution",
    "detect_bottlenecks": "monitoring.detect_bottlenecks"
}


def find_python_files(base_dir: str, exclude_dirs: List[str] = None) -> List[str]:
    """Find all Python files in the repository, excluding specified directories."""
    exclude_dirs = exclude_dirs or []
    python_files = []
    
    for root, dirs, files in os.walk(base_dir):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files


def scan_file_for_imports(file_path: str) -> List[Dict[str, Any]]:
    """Scan a Python file for old tracking module imports."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    imports_found = []
    
    # Pattern for "from tracking.X import Y"
    from_import_pattern = r'from\s+(tracking\.[a-zA-Z_]+)\s+import\s+([a-zA-Z_, ]+)'
    
    # Pattern for "import tracking.X"
    import_pattern = r'import\s+(tracking\.[a-zA-Z_]+)'
    
    # Find "from tracking.X import Y" patterns
    for match in re.finditer(from_import_pattern, content):
        module = match.group(1)
        classes = [c.strip() for c in match.group(2).split(',')]
        
        # Check if this is an old module
        if module in IMPORT_MAPPING:
            imports_found.append({
                'type': 'from_import',
                'module': module,
                'classes': classes,
                'line': content[:match.start()].count('\n') + 1,
                'match': match.group(0)
            })
    
    # Find "import tracking.X" patterns
    for match in re.finditer(import_pattern, content):
        module = match.group(1)
        
        # Check if this is an old module
        if module in IMPORT_MAPPING:
            imports_found.append({
                'type': 'import',
                'module': module,
                'line': content[:match.start()].count('\n') + 1,
                'match': match.group(0)
            })
    
    return imports_found


def generate_replacement(import_info: Dict[str, Any]) -> Tuple[str, str]:
    """Generate replacement code for old imports."""
    old_import = import_info['match']
    
    if import_info['type'] == 'from_import':
        # Handle "from tracking.X import Y" pattern
        return old_import, "from tracking.tracking_system import get_tracking_system"
    else:
        # Handle "import tracking.X" pattern
        return old_import, "from tracking.tracking_system import get_tracking_system"


def update_file(file_path: str, imports_found: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Update imports in a file and return a report."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    replacements = []
    updated_content = content
    
    # Generate and apply replacements
    for import_info in imports_found:
        old_code, new_code = generate_replacement(import_info)
        updated_content = updated_content.replace(old_code, new_code)
        replacements.append({
            'old': old_code,
            'new': new_code,
            'line': import_info['line']
        })
    
    # Only write to file if content changed
    if updated_content != content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)
    
    return {
        'file': file_path,
        'replacements': replacements,
        'updated': updated_content != content
    }


def generate_usage_update_guide(file_path: str, imports_found: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate a guide for updating usage of old modules."""
    usage_updates = []
    component_mapping = {}
    
    for import_info in imports_found:
        if import_info['type'] == 'from_import':
            for class_name in import_info['classes']:
                class_name = class_name.strip()
                if class_name in CLASS_MAPPINGS:
                    component = CLASS_MAPPINGS[class_name]
                    component_mapping[class_name] = f"tracking_system.{component}"
                elif class_name in FUNCTION_MAPPINGS:
                    component_mapping[class_name] = f"tracking_system.{FUNCTION_MAPPINGS[class_name]}"
        
        module = import_info['module']
        if module in IMPORT_MAPPING:
            component = IMPORT_MAPPING[module]
            module_name = module.split('.')[-1]
            component_mapping[module_name] = f"tracking_system.{component}"
    
    # Now search for usage of these classes/variables in the file
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    for old_name, new_path in component_mapping.items():
        # Look for variable initialization
        var_pattern = rf'(\w+)\s*=\s*{old_name}\(\)'
        for match in re.finditer(var_pattern, content):
            var_name = match.group(1)
            usage_updates.append({
                'type': 'initialization',
                'old': f"{var_name} = {old_name}()",
                'new': f"tracking_system = get_tracking_system()",
                'line': content[:match.start()].count('\n') + 1
            })
            
            # Now find method calls on this variable
            method_pattern = rf'{var_name}\.(\w+)\('
            for method_match in re.finditer(method_pattern, content):
                method_name = method_match.group(1)
                line_num = content[:method_match.start()].count('\n') + 1
                # Find where this method usage ends (at the closing parenthesis)
                method_call = content[method_match.start():].split(')', 1)[0] + ')'
                
                usage_updates.append({
                    'type': 'method_call',
                    'old': method_call,
                    'new': f"{new_path}.{method_name}(",
                    'line': line_num
                })
    
    return usage_updates


def scan_repository(base_dir: str, update: bool = False) -> Dict[str, Any]:
    """Scan the repository for old tracking module imports and generate a report."""
    python_files = find_python_files(base_dir, exclude_dirs=['venv', 'env', '.venv', '.git', 'node_modules', 'logs', 'tracking/components'])
    
    files_with_imports = []
    total_imports_found = 0
    files_updated = 0
    
    for file_path in python_files:
        imports_found = scan_file_for_imports(file_path)
        
        if imports_found:
            total_imports_found += len(imports_found)
            usage_updates = generate_usage_update_guide(file_path, imports_found)
            
            file_report = {
                'file': file_path,
                'imports_found': imports_found,
                'usage_updates': usage_updates
            }
            
            if update:
                update_result = update_file(file_path, imports_found)
                file_report['update_result'] = update_result
                if update_result['updated']:
                    files_updated += 1
            
            files_with_imports.append(file_report)
    
    return {
        'total_files_scanned': len(python_files),
        'files_with_old_imports': len(files_with_imports),
        'total_imports_found': total_imports_found,
        'files_updated': files_updated if update else 0,
        'files': files_with_imports
    }


def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Scan and update tracking module imports')
    parser.add_argument('--base-dir', default='.', help='Base directory to scan')
    parser.add_argument('--update', action='store_true', help='Update imports in place')
    parser.add_argument('--output', default='import_scan_report.json', help='Output report file')
    parser.add_argument('--github-output', action='store_true', help='Generate GitHub Actions output')
    
    args = parser.parse_args()
    
    report = scan_repository(args.base_dir, args.update)
    
    # Save report to file
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    # Print summary
    print(f"Scanned {report['total_files_scanned']} Python files")
    print(f"Found {report['files_with_old_imports']} files with old tracking imports")
    print(f"Total of {report['total_imports_found']} old imports found")
    
    if args.update:
        print(f"Updated {report['files_updated']} files")
    
    # Generate GitHub Actions output if requested
    if args.github_output:
        with open(os.environ.get('GITHUB_OUTPUT', 'github_output.txt'), 'a') as f:
            f.write(f"files_with_imports={report['files_with_old_imports']}\n")
            f.write(f"total_imports={report['total_imports_found']}\n")
            f.write(f"files_updated={report['files_updated']}\n")
    
    return 0


if __name__ == '__main__':
    main()
