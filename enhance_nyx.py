# enhance_nyx.py

import os
import sys
import shutil
import subprocess
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/nyx_enhancement.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-Enhancer")

class NYXEnhancer:
    """
    Integrates the new proto-AGI enhancements with the existing NYX codebase.
    """
    
    def __init__(self):
        self.original_dir = "src"
        self.backup_dir = "logs/original_backup"
        self.new_modules = [
            {
                "path": "knowledge/acquisition.py",
                "description": "Knowledge acquisition system for learning new concepts"
            },
            {
                "path": "modeling/concept_builder.py",
                "description": "Conceptual modeling system for building abstractions"
            },
            {
                "path": "core/self_modification.py",
                "description": "Enhanced self-modification system with learning capabilities"
            },
            {
                "path": "core/agi_controller.py",
                "description": "Central controller for orchestrating AGI components"
            }
        ]
    
    def backup_original_code(self):
        """Creates a backup of the original codebase."""
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Copy all files from src to backup
        for root, dirs, files in os.walk(self.original_dir):
            for file in files:
                src_path = os.path.join(root, file)
                # Create relative path
                rel_path = os.path.relpath(src_path, self.original_dir)
                # Create destination path
                dst_path = os.path.join(self.backup_dir, rel_path)
                # Ensure destination directory exists
                os.makedirs(os.path.dirname(dst_path), exist_ok=True)
                # Copy the file
                shutil.copy2(src_path, dst_path)
                
        logger.info(f"Created backup of original code in {self.backup_dir}")
    
    def create_directory_structure(self):
        """Creates the necessary directory structure for new modules."""
        dirs_to_create = [
            "knowledge",
            "modeling",
            "core"
        ]
        
        for directory in dirs_to_create:
            os.makedirs(os.path.join(self.original_dir, directory), exist_ok=True)
            
        # Create __init__.py files to make the directories proper packages
        for directory in dirs_to_create:
            init_file = os.path.join(self.original_dir, directory, "__init__.py")
            if not os.path.exists(init_file):
                with open(init_file, "w") as f:
                    f.write(f"# {directory} package\n")
                    
        logger.info("Created directory structure for new modules")
    
    def integrate_new_modules(self):
        """Copies new module files to the appropriate locations."""
        for module in self.new_modules:
            # Source path in the current directory
            src_path = module["path"]
            # Destination path in the original codebase
            dst_path = os.path.join(self.original_dir, module["path"])
            
            # Ensure destination directory exists
            os.makedirs(os.path.dirname(dst_path), exist_ok=True)
            
            # Copy the file
            if os.path.exists(src_path):
                shutil.copy2(src_path, dst_path)
                logger.info(f"Integrated {src_path} -> {dst_path}")
            else:
                logger.error(f"Source file {src_path} not found")
    
    def update_nyx_core(self):
        """Updates the nyx_core.py file to include the new AGI capabilities."""
        # Path to the original nyx_core.py
        nyx_core_path = os.path.join(self.original_dir, "nyx_core.py")
        
        if not os.path.exists(nyx_core_path):
            logger.error(f"Original {nyx_core_path} not found")
            return False
            
        # Read the original file
        with open(nyx_core_path, "r") as f:
            original_content = f.read()
            
        # Create updated content with imports for new modules
        updated_content = f"""# Enhanced NYX Core with Proto-AGI Capabilities
# Original core functionality with integrated AGI components
# Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

import os
import sys
import time
from datetime import datetime

# Original imports
from src.self_analysis import main as analyze
from src.optimization_engine import generate_optimization_suggestions
from analysis.self_writer import apply_suggestions

# New AGI component imports
from core.agi_controller import AGIController
from knowledge.acquisition import KnowledgeAcquisition
from modeling.concept_builder import ConceptualModeling
from core.self_modification import SelfModification

# Initialize global AGI controller
agi_controller = None

def initialize_agi():
    \"\"\"Initializes the AGI components.\"\"\"
    global agi_controller
    
    print("NYX CORE: Initializing AGI components...")
    agi_controller = AGIController()
    
    # Load existing state and prepare the system
    agi_controller.load_learning_goals()
    
    print("NYX CORE: AGI components initialized.")
    return agi_controller

def enhanced_nyx_core_loop():
    \"\"\"Enhanced core loop with AGI capabilities.\"\"\"
    global agi_controller
    
    print("NYX CORE: Beginning enhanced self-improvement cycle...")
    
    # Original NYX functionality
    analyze()
    generate_optimization_suggestions()
    apply_suggestions()
    
    # New AGI functionality
    if not agi_controller:
        agi_controller = initialize_agi()
        
    # Execute an AGI improvement cycle
    cycle_result = agi_controller.execute_cycle()
    
    print(f"NYX CORE: Executed AGI cycle #{cycle_result['cycle']} focusing on {cycle_result['focus']}")
    print("NYX CORE: Enhanced optimization cycle complete.")

def start_continuous_improvement():
    \"\"\"Starts continuous AGI-driven improvement.\"\"\"
    global agi_controller
    
    if not agi_controller:
        agi_controller = initialize_agi()
        
    # Start the AGI controller in background mode
    success = agi_controller.start()
    
    if success:
        print("NYX CORE: Continuous AGI improvement started.")
    else:
        print("NYX CORE: Failed to start continuous improvement.")
    
    return success

def stop_continuous_improvement():
    \"\"\"Stops continuous AGI-driven improvement.\"\"\"
    global agi_controller
    
    if agi_controller:
        success = agi_controller.stop()
        
        if success:
            print("NYX CORE: Continuous AGI improvement stopped.")
        else:
            print("NYX CORE: Failed to stop continuous improvement.")
        
        return success
    else:
        print("NYX CORE: AGI controller not initialized.")
        return False

def get_agi_status():
    \"\"\"Returns the current status of the AGI system.\"\"\"
    global agi_controller
    
    if agi_controller:
        return agi_controller.get_status()
    else:
        return {"status": "not_initialized"}

def nyx_core_loop():
    \"\"\"Original nyx_core_loop function, now calls the enhanced version.\"\"\"
    enhanced_nyx_core_loop()

if __name__ == "__main__":
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
    
    if command == "run":
        nyx_core_loop()
    elif command == "start":
        start_continuous_improvement()
    elif command == "stop":
        stop_continuous_improvement()
    elif command == "status":
        status = get_agi_status()
        print(json.dumps(status, indent=2))
    else:
        print(f"Unknown command: {command}")
        print("Available commands: run, start, stop, status")
"""
        
        # Write the updated content
        with open(nyx_core_path, "w") as f:
            f.write(updated_content)
            
        logger.info(f"Updated {nyx_core_path} with AGI capabilities")
        return True
    
    def create_startup_script(self):
        """Creates a startup script for easy launching of the enhanced NYX system."""
        startup_script = """#!/usr/bin/env python3
# start_nyx_agi.py - Launcher for the enhanced NYX AGI system

import os
import sys
import subprocess
import time
import json

def main():
    print("┌─────────────────────────────────────────┐")
    print("│          NYX AGI System Launcher        │")
    print("└─────────────────────────────────────────┘")
    
    # Check if the system is already running
    result = subprocess.run(["python3", "src/nyx_core.py", "status"], 
                          capture_output=True, text=True)
    
    try:
        status = json.loads(result.stdout)
        if status.get("status") == "running":
            print("NYX AGI is already running.")
            print(f"Status: {status}")
            choice = input("Do you want to stop it? (y/n): ").lower()
            
            if choice == 'y':
                subprocess.run(["python3", "src/nyx_core.py", "stop"])
                print("NYX AGI stopped.")
            return
    except:
        # If we can't parse the status, assume it's not running
        pass
    
    print("Starting NYX AGI system...")
    subprocess.run(["python3", "src/nyx_core.py", "start"])
    
    print("NYX AGI system started in continuous improvement mode.")
    print("You can check the status by running: python3 src/nyx_core.py status")
    print("You can stop it by running: python3 src/nyx_core.py stop")
    
    choice = input("Do you want to monitor the system? (y/n): ").lower()
    
    if choice == 'y':
        try:
            while True:
                result = subprocess.run(["python3", "src/nyx_core.py", "status"], 
                                      capture_output=True, text=True)
                print("\n" + "-" * 50)
                print(result.stdout)
                print("-" * 50)
                print("Press Ctrl+C to exit monitoring.")
                time.sleep(30)  # Update every 30 seconds
        except KeyboardInterrupt:
            print("\nMonitoring stopped. NYX AGI continues running in the background.")
            
if __name__ == "__main__":
    main()
"""
        
        # Write the startup script
        with open("start_nyx_agi.py", "w") as f:
            f.write(startup_script)
            
        # Make it executable
        os.chmod("start_nyx_agi.py", 0o755)
        
        logger.info("Created startup script: start_nyx_agi.py")
    
    def update_github_workflow(self):
        """Updates the GitHub workflow to include the new AGI components."""
        workflow_path = ".github/workflows/self-improvement.yml"
        
        if not os.path.exists(workflow_path):
            logger.error(f"Workflow file {workflow_path} not found")
            return False
            
        # Read the original workflow
        with open(workflow_path, "r") as f:
            workflow_content = f.read()
            
        # Add new steps for AGI components
        new_steps = """
      - name: 🧠 Initialize AGI Components
        run: |
          mkdir -p knowledge modeling
          python3 -c "import sys; sys.path.append('.'); from core.agi_controller import AGIController; controller = AGIController(); print('AGI components initialized')"

      - name: 🔍 Execute AGI Knowledge Acquisition
        run: python3 -c "import sys; sys.path.append('.'); from core.agi_controller import AGIController; controller = AGIController(); controller.execute_knowledge_acquisition_cycle()"
        
      - name: 🧩 Execute AGI Concept Formation
        run: python3 -c "import sys; sys.path.append('.'); from core.agi_controller import AGIController; controller = AGIController(); controller.execute_concept_formation_cycle()"
        
      - name: ⚙️ Execute AGI Self-Modification
        run: python3 -c "import sys; sys.path.append('.'); from core.agi_controller import AGIController; controller = AGIController(); controller.execute_self_modification_cycle()"
"""
        
        # Find the position to insert the new steps (before the 🛡️ Detect & Rollback Failed AI Improvements step)
        insert_marker = "- name: 🛡️ Detect & Rollback Failed AI Improvements"
        if insert_marker in workflow_content:
            parts = workflow_content.split(insert_marker)
            updated_workflow = parts[0] + new_steps + "      " + insert_marker + parts[1]
            
            # Write the updated workflow
            with open(workflow_path, "w") as f:
                f.write(updated_workflow)
                
            logger.info(f"Updated GitHub workflow: {workflow_path}")
            return True
        else:
            logger.error(f"Could not find insertion point in {workflow_path}")
            return False
    
    def install_dependencies(self):
        """Installs necessary dependencies for the AGI components."""
        dependencies = [
            "numpy",
            "scikit-learn",
            "networkx",
            "torch",
            "chromadb",
            "beautifulsoup4",
            "requests"
        ]
        
        logger.info("Installing dependencies...")
        
        try:
            subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade"] + dependencies)
            logger.info("Dependencies installed successfully")
            return True
        except Exception as e:
            logger.error(f"Error installing dependencies: {str(e)}")
            return False
    
    def enhance_nyx(self):
        """Main method to enhance the NYX system with proto-AGI capabilities."""
        logger.info("Starting NYX enhancement process")
        
        # Backup original code
        self.backup_original_code()
        
        # Create directory structure
        self.create_directory_structure()
        
        # Integrate new modules
        self.integrate_new_modules()
        
        # Update nyx_core.py
        self.update_nyx_core()
        
        # Create startup script
        self.create_startup_script()
        
        # Update GitHub workflow
        self.update_github_workflow()
        
        # Install dependencies
        self.install_dependencies()
        
        logger.info("NYX enhancement process completed")
        
        print("\n" + "=" * 50)
        print("NYX ENHANCEMENT COMPLETED")
        print("=" * 50)
        print("\nThe NYX system has been enhanced with proto-AGI capabilities.")
        print("\nNew components:")
        for module in self.new_modules:
            print(f"  - {module['path']}: {module['description']}")
            
        print("\nTo start the enhanced NYX system:")
        print("  python3 start_nyx_agi.py")
        
        print("\nTo run a single improvement cycle:")
        print("  python3 src/nyx_core.py run")
        
        print("\nTo check the AGI status:")
        print("  python3 src/nyx_core.py status")
        
        print("\nOriginal code has been backed up to:")
        print(f"  {self.backup_dir}")
        
        print("\n" + "=" * 50)
        

if __name__ == "__main__":
    enhancer = NYXEnhancer()
    enhancer.enhance_nyx()
