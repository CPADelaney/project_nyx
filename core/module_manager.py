# core/module_manager.py

"""
Module manager for safely handling optional dependencies.
This module provides wrapper functions to safely import optional modules
and fallback functionality when they are not available.
"""

import importlib
import sys
import logging
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/module_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-ModuleManager")

# Dictionary of module states
module_states = {}

def import_optional_module(module_name, as_name=None, fallback=None):
    """
    Safely import an optional module.
    
    Args:
        module_name (str): Name of module to import
        as_name (str, optional): Name to import the module as
        fallback (object, optional): Fallback object if import fails
        
    Returns:
        module or fallback: The imported module or fallback object
    """
    if as_name is None:
        as_name = module_name
        
    # Check if we've already tried to import this module
    if module_name in module_states:
        if module_states[module_name]["available"]:
            return module_states[module_name]["module"]
        return fallback
        
    try:
        module = importlib.import_module(module_name)
        module_states[module_name] = {
            "available": True,
            "module": module
        }
        
        # Set in the caller's global namespace if as_name is provided
        if as_name:
            caller_globals = sys._getframe(1).f_globals
            caller_globals[as_name] = module
            
        logger.info(f"Successfully imported optional module: {module_name}")
        return module
    except ImportError as e:
        module_states[module_name] = {
            "available": False,
            "error": str(e)
        }
        logger.warning(f"Optional module {module_name} not available: {e}")
        
        if fallback is not None:
            # Set fallback in the caller's global namespace
            if as_name:
                caller_globals = sys._getframe(1).f_globals
                caller_globals[as_name] = fallback
                
        return fallback

def is_module_available(module_name):
    """
    Check if a module is available without attempting to import it again.
    
    Args:
        module_name (str): Name of module to check
        
    Returns:
        bool: True if the module is available, False otherwise
    """
    if module_name in module_states:
        return module_states[module_name]["available"]
        
    # Try importing it
    try:
        importlib.import_module(module_name)
        module_states[module_name] = {
            "available": True
        }
        return True
    except ImportError:
        module_states[module_name] = {
            "available": False
        }
        return False

def get_module_error(module_name):
    """
    Get the error message from attempting to import a module.
    
    Args:
        module_name (str): Name of module to check
        
    Returns:
        str: Error message or None if no error or import not attempted
    """
    if module_name in module_states and not module_states[module_name]["available"]:
        return module_states[module_name].get("error")
    return None

def get_available_modules():
    """
    Get the list of available optional modules.
    
    Returns:
        list: List of available module names
    """
    return [name for name, state in module_states.items() if state["available"]]

def get_unavailable_modules():
    """
    Get the list of unavailable optional modules.
    
    Returns:
        list: List of unavailable module names
    """
    return [name for name, state in module_states.items() if not state["available"]]

# Import typical optional modules used in the project
def import_common_modules():
    """Pre-import commonly used optional modules to detect availability early."""
    # AI and ML
    import_optional_module("torch")
    import_optional_module("networkx")
    import_optional_module("sklearn")
    import_optional_module("chromadb")
    import_optional_module("z3")
    
    # Web and data
    import_optional_module("requests")
    import_optional_module("bs4", "BeautifulSoup")
    import_optional_module("paramiko")
    
    # Others
    import_optional_module("openai")
    
    # Log results
    available = get_available_modules()
    unavailable = get_unavailable_modules()
    
    logger.info(f"Available optional modules: {', '.join(available)}")
    if unavailable:
        logger.warning(f"Unavailable optional modules: {', '.join(unavailable)}")
    
# Mock modules for fallbacks
class MockZ3Solver:
    """Mock Z3 solver for when z3 is not available."""
    
    def __init__(self):
        self.constraints = []
    
    def add(self, constraint):
        self.constraints.append(constraint)
        
    def check(self):
        return "sat"  # Always return satisfiable for safety
        
    def model(self):
        return {}  # Empty model

class MockOpenAI:
    """Mock OpenAI for when openai module is not available."""
    
    class ChatCompletion:
        @staticmethod
        def create(**kwargs):
            return MockOpenAIResponse(
                "I'm sorry, but the OpenAI module is not available. "
                "This is a mock response."
            )
    
class MockOpenAIResponse:
    """Mock response from OpenAI API."""
    
    def __init__(self, content):
        self.choices = [MockOpenAIChoice(content)]
        
class MockOpenAIChoice:
    """Mock choice from OpenAI API response."""
    
    def __init__(self, content):
        self.message = {"content": content}

# Initialize at module import time
if __name__ != "__main__":
    import_common_modules()
    
# Test the module if run directly
if __name__ == "__main__":
    import_common_modules()
    print(f"Available modules: {get_available_modules()}")
    print(f"Unavailable modules: {get_unavailable_modules()}")
