# core/agi_controller_interface.py

"""
Interface for the AGI Controller functionality.
This breaks circular dependencies between modules that need AGI controller functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional

class AGIControllerInterface(ABC):
    """
    Interface for AGI Controller functionality.
    Abstracts the AGI controller to break circular dependencies.
    """
    
    @abstractmethod
    def start(self) -> bool:
        """
        Starts the AGI controller in a separate thread.
        
        Returns:
            bool: True if started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stops the AGI controller.
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def pause(self) -> bool:
        """
        Pauses the AGI controller.
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def resume(self) -> bool:
        """
        Resumes the AGI controller if paused.
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Returns the current status of the AGI controller.
        
        Returns:
            Dict[str, Any]: Status information
        """
        pass
    
    @abstractmethod
    def execute_cycle(self) -> Dict[str, Any]:
        """
        Executes a single AGI improvement cycle.
        
        Returns:
            Dict[str, Any]: Results of the cycle
        """
        pass
    
    @abstractmethod
    def load_learning_goals(self) -> None:
        """
        Loads learning goals from the database.
        """
        pass
    
    @abstractmethod
    def add_learning_goal(self, goal: str, priority: int = 3) -> int:
        """
        Adds a new learning goal.
        
        Args:
            goal: The learning goal to add
            priority: Priority of the goal (1-5)
            
        Returns:
            int: ID of the added goal
        """
        pass
    
    @abstractmethod
    def complete_learning_goal(self, goal_id: int) -> None:
        """
        Marks a learning goal as completed.
        
        Args:
            goal_id: ID of the goal to complete
        """
        pass
    
    @abstractmethod
    def execute_knowledge_acquisition_cycle(self) -> Dict[str, Any]:
        """
        Executes a knowledge acquisition cycle.
        
        Returns:
            Dict[str, Any]: Results of the cycle
        """
        pass
    
    @abstractmethod
    def execute_concept_formation_cycle(self) -> Dict[str, Any]:
        """
        Executes a concept formation cycle.
        
        Returns:
            Dict[str, Any]: Results of the cycle
        """
        pass
    
    @abstractmethod
    def execute_self_modification_cycle(self) -> Dict[str, Any]:
        """
        Executes a self-modification cycle.
        
        Returns:
            Dict[str, Any]: Results of the cycle
        """
        pass
    
    @abstractmethod
    def get_recent_activities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Returns the most recent AGI cycles.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List[Dict[str, Any]]: Recent activities
        """
        pass

# Factory function to get an AGI controller implementation
def get_agi_controller() -> Optional[AGIControllerInterface]:
    """
    Factory function to get an AGI controller implementation.
    This prevents circular imports by dynamically importing the implementation
    only when needed.
    
    Returns:
        AGIControllerInterface or None: An instance of the AGI controller, or None if not available
    """
    try:
        # Import the implementation only when needed
        from core.agi_controller_impl import AGIControllerImpl
        return AGIControllerImpl()
    except ImportError:
        import logging
        logging.getLogger("NYX-AGI").warning("AGI controller implementation not available")
        return None
