# src/nyx_core.py

"""
Nyx Core Module - Main entry point for the Nyx self-improvement system
This module has been refactored to improve stability, error handling, and safety
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from core.monitoring_system import get_monitoring_system

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/nyx_core.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-Core")

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import core functionality with error handling
try:
    from src.self_analysis import main as analyze
except ImportError as e:
    logger.error(f"Failed to import self_analysis: {str(e)}")
    def analyze():
        logger.error("analyze() function not available")
        return False

try:
    from src.optimization_engine import generate_optimization_suggestions
except ImportError as e:
    logger.error(f"Failed to import optimization_engine: {str(e)}")
    def generate_optimization_suggestions():
        logger.error("generate_optimization_suggestions() function not available")
        return False

try:
    from analysis.self_writer import apply_suggestions
except ImportError as e:
    logger.error(f"Failed to import self_writer: {str(e)}")
    def apply_suggestions():
        logger.error("apply_suggestions() function not available")
        return False

# Import core error handling
try:
    from core.error_handler import safe_execute
except ImportError as e:
    logger.error(f"Failed to import error_handler: {str(e)}")
    # Define a simple safe_execute decorator as fallback
    def safe_execute(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {str(e)}\n{traceback.format_exc()}")
                return {"success": False, "error": str(e)}
        return wrapper

# Try to import AGI controller if available
try:
    from core.agi_controller import AGIController
    agi_available = True
except ImportError:
    logger.warning("AGI controller not available, running in basic mode")
    agi_available = False
    
# Global AGI controller instance
agi_controller = None

@safe_execute
def initialize_agi():
    """Initializes the AGI components if available."""
    global agi_controller
    
    if not agi_available:
        logger.warning("AGI functionality not available.")
        return {"success": False, "message": "AGI functionality not available"}
    
    logger.info("Initializing AGI components...")
    agi_controller = AGIController()
    
    # Load existing state and prepare the system
    try:
        agi_controller.load_learning_goals()
        logger.info("AGI components initialized successfully.")
        return {"success": True, "message": "AGI components initialized successfully"}
    except Exception as e:
        logger.error(f"Error initializing AGI: {str(e)}")
        return {"success": False, "error": str(e)}

@safe_execute
def nyx_core_loop():
    """Original core loop for basic self-improvement functionality."""
    logger.info("Beginning self-improvement cycle...")
    
    # Analyze code structure
    analyze_result = analyze()
    
    # Generate optimization suggestions
    suggestions_result = generate_optimization_suggestions()
    
    # Apply the suggestions
    apply_result = apply_suggestions()
    
    logger.info("Self-improvement cycle complete.")
    
    return {
        "success": True,
        "analyze_result": analyze_result,
        "suggestions_result": suggestions_result,
        "apply_result": apply_result
    }

@safe_execute
def enhanced_nyx_core_loop():
    """Enhanced core loop with AGI capabilities if available."""
    global agi_controller
    
    logger.info("Beginning enhanced self-improvement cycle...")
    
    # Run basic self-improvement
    core_result = nyx_core_loop()
    
    # Run AGI functionality if available
    agi_result = None
    if agi_available:
        if not agi_controller:
            init_result = initialize_agi()
            if not init_result.get("success", False):
                logger.warning("Failed to initialize AGI controller")
                
        if agi_controller:
            try:
                cycle_result = agi_controller.execute_cycle()
                logger.info(f"Executed AGI cycle #{cycle_result['cycle']} focusing on {cycle_result['focus']}")
                agi_result = cycle_result
            except Exception as e:
                logger.error(f"Error in AGI cycle: {str(e)}")
                agi_result = {"success": False, "error": str(e)}
    
    logger.info("Enhanced self-improvement cycle complete.")
    
    return {
        "success": True,
        "core_result": core_result,
        "agi_result": agi_result
    }

@safe_execute
def start_continuous_improvement():
    """Starts continuous AGI-driven improvement if available."""
    global agi_controller
    
    if not agi_available:
        logger.warning("AGI functionality not available for continuous improvement.")
        return {"success": False, "message": "AGI functionality not available"}
    
    if not agi_controller:
        init_result = initialize_agi()
        if not init_result.get("success", False):
            logger.warning("Failed to initialize AGI controller")
            return init_result
    
    # Start the AGI controller in background mode
    try:
        success = agi_controller.start()
        
        if success:
            logger.info("Continuous AGI improvement started.")
            return {"success": True, "message": "Continuous AGI improvement started"}
        else:
            logger.error("Failed to start continuous improvement.")
            return {"success": False, "message": "Failed to start continuous improvement"}
    except Exception as e:
        logger.error(f"Error starting continuous improvement: {str(e)}")
        return {"success": False, "error": str(e)}

@safe_execute
def stop_continuous_improvement():
    """Stops continuous AGI-driven improvement if running."""
    global agi_controller
    
    if not agi_available or not agi_controller:
        logger.warning("AGI controller not initialized or available.")
        return {"success": False, "message": "AGI controller not initialized"}
    
    try:
        success = agi_controller.stop()
        
        if success:
            logger.info("Continuous AGI improvement stopped.")
            return {"success": True, "message": "Continuous AGI improvement stopped"}
        else:
            logger.error("Failed to stop continuous improvement.")
            return {"success": False, "message": "Failed to stop continuous improvement"}
    except Exception as e:
        logger.error(f"Error stopping continuous improvement: {str(e)}")
        return {"success": False, "error": str(e)}

@safe_execute
def get_system_status():
    """Returns the current status of the system."""
    global agi_controller
    
    status = {
        "time": str(datetime.now()),
        "agi_available": agi_available,
        "agi_initialized": agi_controller is not None
    }
    
    if agi_controller:
        try:
            agi_status = agi_controller.get_status()
            status["agi_status"] = agi_status
        except Exception as e:
            logger.error(f"Error getting AGI status: {str(e)}")
            status["agi_status_error"] = str(e)
    
    return {"success": True, "status": status}

def main():
    """Main entry point for command-line usage."""
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
    if get_config().get("monitoring", "enabled", True):
        monitoring_system = get_monitoring_system()
        monitoring_system.start()
        logger.info("Monitoring system started")    
    if command == "run":
        result = enhanced_nyx_core_loop()
        if result.get("success", False):
            print("✅ Nyx core executed successfully")
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
    elif command == "start":
        result = start_continuous_improvement()
        if result.get("success", False):
            print("✅ Continuous improvement started")
        else:
            print(f"❌ Failed to start: {result.get('error', result.get('message', 'Unknown error'))}")
    elif command == "stop":
        result = stop_continuous_improvement()
        if result.get("success", False):
            print("✅ Continuous improvement stopped")
        else:
            print(f"❌ Failed to stop: {result.get('error', result.get('message', 'Unknown error'))}")
    elif command == "status":
        result = get_system_status()
        if result.get("success", False):
            print(json.dumps(result["status"], indent=2))
        else:
            print(f"❌ Failed to get status: {result.get('error', 'Unknown error')}")
    else:
        print(f"Unknown command: {command}")
        print("Available commands: run, start, stop, status")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except Exception as e:
        logger.critical(f"Unhandled exception in main: {str(e)}\n{traceback.format_exc()}")
        print(f"Critical error: {str(e)}")
        sys.exit(1)
