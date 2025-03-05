# src/nyx_core.py

"""
Nyx Core Module - Main entry point for the Nyx self-improvement system
This module has been refactored to improve stability, error handling, and dependency management.
"""

import os
import sys
import json
import time
import logging
import traceback
from datetime import datetime
from typing import Dict, Any, Optional

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

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

# Set up dependency injection container
from core.dependency_injection import container, register, register_class, resolve

# Import core functionality with error handling
try:
    from src.self_analysis import main as analyze
except ImportError as e:
    logger.error(f"Failed to import self_analysis: {str(e)}")
    def analyze():
        logger.error("analyze() function not available")
        return {"success": False, "error": "Self-analysis module not available"}

try:
    from src.optimization_engine import generate_optimization_suggestions
except ImportError as e:
    logger.error(f"Failed to import optimization_engine: {str(e)}")
    def generate_optimization_suggestions():
        logger.error("generate_optimization_suggestions() function not available")
        return {"success": False, "error": "Optimization engine not available"}

try:
    from analysis.self_writer import apply_suggestions
except ImportError as e:
    logger.error(f"Failed to import self_writer: {str(e)}")
    def apply_suggestions():
        logger.error("apply_suggestions() function not available")
        return {"success": False, "error": "Self-writer not available"}

# Import core error framework 
from core.error_framework import safe_execute, ValidationError, APIError

# Import configuration manager
from core.config_manager import create_config_manager

# Import AGI controller interface - breaking circular dependency
from core.agi_controller_interface import AGIControllerInterface, get_agi_controller

# Import monitoring system
from core.monitoring_system import get_monitoring_system

# Set up configuration
config_manager = create_config_manager()

# Register services in dependency injection container
register("config_manager", instance=config_manager)
register("agi_controller", factory=get_agi_controller, singleton=True)

class NyxCore:
    """
    Main class for the Nyx self-improvement system.
    Implements core functionality and coordinates components.
    """
    
    def __init__(self, config_manager, agi_controller: Optional[AGIControllerInterface] = None):
        """
        Initialize the Nyx core system.
        
        Args:
            config_manager: Configuration manager instance
            agi_controller: AGI controller instance (optional)
        """
        self.config_manager = config_manager
        self.agi_controller = agi_controller
        self.agi_available = self.agi_controller is not None
        
        logger.info("Nyx Core initialized")
        if self.agi_available:
            logger.info("AGI functionality is available")
        else:
            logger.info("AGI functionality is not available")
    
    @safe_execute
    def nyx_core_loop(self) -> Dict[str, Any]:
        """
        Executes the original core loop for basic self-improvement functionality.
        
        Returns:
            Dict[str, Any]: Results of the operation
        """
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
    def enhanced_nyx_core_loop(self) -> Dict[str, Any]:
        """
        Executes the enhanced core loop with AGI capabilities if available.
        
        Returns:
            Dict[str, Any]: Results of the operation
        """
        logger.info("Beginning enhanced self-improvement cycle...")
        
        # Run basic self-improvement
        core_result = self.nyx_core_loop()
        
        # Run AGI functionality if available
        agi_result = None
        if self.agi_available:
            try:
                cycle_result = self.agi_controller.execute_cycle()
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
    def start_continuous_improvement(self) -> Dict[str, Any]:
        """
        Starts continuous AGI-driven improvement if available.
        
        Returns:
            Dict[str, Any]: Results of the operation
        """
        if not self.agi_available:
            logger.warning("AGI functionality not available for continuous improvement.")
            return {"success": False, "message": "AGI functionality not available"}
        
        # Start the AGI controller in background mode
        success = self.agi_controller.start()
        
        if success:
            logger.info("Continuous AGI improvement started.")
            return {"success": True, "message": "Continuous AGI improvement started"}
        else:
            logger.error("Failed to start continuous improvement.")
            return {"success": False, "message": "Failed to start continuous improvement"}
    
    @safe_execute
    def stop_continuous_improvement(self) -> Dict[str, Any]:
        """
        Stops continuous AGI-driven improvement if running.
        
        Returns:
            Dict[str, Any]: Results of the operation
        """
        if not self.agi_available:
            logger.warning("AGI controller not initialized or available.")
            return {"success": False, "message": "AGI controller not initialized"}
        
        success = self.agi_controller.stop()
        
        if success:
            logger.info("Continuous AGI improvement stopped.")
            return {"success": True, "message": "Continuous AGI improvement stopped"}
        else:
            logger.error("Failed to stop continuous improvement.")
            return {"success": False, "message": "Failed to stop continuous improvement"}
    
    @safe_execute
    def get_system_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the system.
        
        Returns:
            Dict[str, Any]: Status information
        """
        status = {
            "time": str(datetime.now()),
            "agi_available": self.agi_available,
            "agi_initialized": self.agi_controller is not None
        }
        
        if self.agi_controller:
            agi_status = self.agi_controller.get_status()
            status["agi_status"] = agi_status
        
        return {"success": True, "status": status}

# Register the NyxCore class with dependency injection
register_class(NyxCore, singleton=True)

@safe_execute
def main() -> int:
    """
    Main entry point for command-line usage.
    
    Returns:
        int: Exit code
    """
    # Resolve the Nyx core instance from the container
    nyx_core = resolve("NyxCore")
    
    # Start monitoring system if enabled
    if config_manager.get("monitoring", "enabled", True):
        monitoring_system = get_monitoring_system()
        monitoring_system.start()
        logger.info("Monitoring system started")
    
    # Parse command line arguments
    command = sys.argv[1].lower() if len(sys.argv) > 1 else "run"
    
    if command == "run":
        result = nyx_core.enhanced_nyx_core_loop()
        if result["success"]:
            print("✅ Nyx core executed successfully")
        else:
            print(f"❌ Execution failed: {result.get('error', 'Unknown error')}")
    elif command == "start":
        result = nyx_core.start_continuous_improvement()
        if result["success"]:
            print("✅ Continuous improvement started")
        else:
            print(f"❌ Failed to start: {result.get('error', result.get('message', 'Unknown error'))}")
    elif command == "stop":
        result = nyx_core.stop_continuous_improvement()
        if result["success"]:
            print("✅ Continuous improvement stopped")
        else:
            print(f"❌ Failed to stop: {result.get('error', result.get('message', 'Unknown error'))}")
    elif command == "status":
        result = nyx_core.get_system_status()
        if result["success"]:
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
