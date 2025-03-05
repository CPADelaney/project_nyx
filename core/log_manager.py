# core/log_manager.py

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import the database manager
from core.database_manager import get_log_db_manager

# Configure logging
logger = logging.getLogger("NYX-LogManager")

# Define the default log database path (for reference only)
LOG_DB = "logs/ai_logs.db"

class LogDatabaseManager:
    """
    Specialized database manager for the log database.
    Uses the core database manager for all operations.
    """
    
    def __init__(self):
        """Initialize the log database manager."""
        # Get the global database manager instance
        self.db_manager = get_log_db_manager()
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Create all the necessary tables for the log database."""
        # Create tables using the database manager's transaction
        self.db_manager.execute_script('''
            CREATE TABLE IF NOT EXISTS performance_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            );

            CREATE TABLE IF NOT EXISTS optimization_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                function_name TEXT,
                execution_time REAL,
                success INTEGER,
                dependency TEXT DEFAULT NULL 
            );
            
            CREATE TABLE IF NOT EXISTS error_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                error_message TEXT
            );
            
            -- All other tables follow...
        ''')
        
        logger.info("Log database tables initialized")
    
    def store_memory(self, event_type: str, details: str) -> Dict[str, Any]:
        """
        Stores AI memories persistently.
        
        Args:
            event_type: Type of the event
            details: Event details
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            # Use the database manager to execute the query
            self.db_manager.execute_update(
                "INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                (event_type, details)
            )
            
            return {"success": True, "message": "Memory stored successfully"}
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def log_event(self, event_type: str, details: str) -> Dict[str, Any]:
        """
        Logs a general AI event.
        
        Args:
            event_type: Type of the event
            details: Event details
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            self.db_manager.execute_update(
                "INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                (event_type, details)
            )
            
            return {"success": True, "message": "Event logged successfully"}
        except Exception as e:
            logger.error(f"Error logging event: {str(e)}")
            return {"success": False, "error": str(e)}
    
    # Continue with other methods...

# Create a global LogDatabaseManager instance
_log_db_manager = None

def get_log_db_manager() -> LogDatabaseManager:
    """Get the global log database manager."""
    global _log_db_manager
    if _log_db_manager is None:
        _log_db_manager = LogDatabaseManager()
    return _log_db_manager

# Helper functions for backwards compatibility
def initialize_log_db() -> bool:
    """
    Initialize the log database.
    
    Returns:
        bool: True if successful
    """
    get_log_db_manager()
    return True

def log_event(event_type: str, details: str) -> bool:
    """Log an event in the database."""
    result = get_log_db_manager().log_event(event_type, details)
    return result["success"]

# Other helper functions follow...

# Initialize on import
initialize_log_db()
