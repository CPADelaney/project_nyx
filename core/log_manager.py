# core/log_manager.py

import os
import logging
import json
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Import the database manager
from core.database_manager import DatabaseManager, get_log_db_manager
from core.error_framework import safe_execute, safe_db_execute, ValidationError, FileSystemError

# Configure logging
logger = logging.getLogger("NYX-LogManager")

# Define the default log database path
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

            -- Self-improvement related tables
            CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                goal TEXT,
                target_function TEXT DEFAULT NULL,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                dependency TEXT DEFAULT NULL,
                status TEXT CHECK(status IN ('pending', 'in-progress', 'completed', 'failed')) DEFAULT 'pending'
            );
            
            CREATE TABLE IF NOT EXISTS ai_self_modifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                target_function TEXT,
                details TEXT
            );
            
            -- Knowledge acquisition tables
            CREATE TABLE IF NOT EXISTS knowledge_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_url TEXT,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            );
            
            CREATE TABLE IF NOT EXISTS knowledge_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT,
                description TEXT,
                source_id INTEGER,
                confidence REAL,
                acquisition_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES knowledge_sources(id)
            );
            
            -- More tables follow...
        ''')
        
        logger.info("Log database tables initialized")
    
    @safe_execute
    def store_memory(self, event_type: str, details: str) -> Dict[str, Any]:
        """
        Stores AI memories persistently.
        
        Args:
            event_type: Type of the event
            details: Event details
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        self.db_manager.execute_update(
            "INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
            (event_type, details)
        )
        
        return {"success": True, "message": "Memory stored successfully"}
    
    @safe_execute
    def recall_memory(self, query: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        Retrieves AI's long-term memory.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # This would use more sophisticated vector search in a real implementation
        memories = self.db_manager.execute(
            "SELECT details FROM performance_logs WHERE details LIKE ? ORDER BY timestamp DESC LIMIT ?",
            (f"%{query}%", limit)
        )
        
        return {
            "success": True,
            "memories": [memory['details'] for memory in memories]
        }
    
    @safe_execute
    def log_event(self, event_type: str, details: str) -> Dict[str, Any]:
        """
        Logs a general AI event.
        
        Args:
            event_type: Type of the event
            details: Event details
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        self.db_manager.execute_update(
            "INSERT INTO performance_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
            (event_type, details)
        )
        
        return {"success": True, "message": "Event logged successfully"}
    
    @safe_execute
    def log_optimization(self, function_name: str, execution_time: float, success: bool) -> Dict[str, Any]:
        """
        Logs function execution time and optimization success.
        
        Args:
            function_name: Name of the function
            execution_time: Execution time in seconds
            success: Whether the optimization was successful
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        self.db_manager.execute_update(
            "INSERT INTO optimization_logs (timestamp, function_name, execution_time, success) VALUES (datetime('now'), ?, ?, ?)",
            (function_name, execution_time, 1 if success else 0)
        )
        
        return {"success": True, "message": "Optimization logged successfully"}
    
    @safe_execute
    def log_error(self, error_message: str) -> Dict[str, Any]:
        """
        Logs errors encountered during execution.
        
        Args:
            error_message: Error message
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        self.db_manager.execute_update(
            "INSERT INTO error_logs (timestamp, error_message) VALUES (datetime('now'), ?)",
            (error_message,)
        )
        
        return {"success": True, "message": "Error logged successfully"}

# Global instance
_log_db_manager = None

def get_log_manager() -> LogDatabaseManager:
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
    get_log_manager()
    return True

def store_memory(event_type: str, details: str) -> Dict[str, Any]:
    """Store a memory in the database."""
    return get_log_manager().store_memory(event_type, details)

def recall_memory(query: str = "", limit: int = 50) -> List[str]:
    """Recall memories from the database."""
    result = get_log_manager().recall_memory(query, limit)
    return result.get("memories", []) if result["success"] else []

def log_event(event_type: str, details: str) -> bool:
    """Log an event in the database."""
    result = get_log_manager().log_event(event_type, details)
    return result["success"]

def log_optimization(function_name: str, execution_time: float, success: bool) -> bool:
    """Log an optimization in the database."""
    result = get_log_manager().log_optimization(function_name, execution_time, success)
    return result["success"]

def log_error(error_message: str) -> bool:
    """Log an error in the database."""
    result = get_log_manager().log_error(error_message)
    return result["success"]

# Initialize on import
initialize_log_db()
