# core/log_manager.py

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List, Union

# Import the database manager
from core.database_manager import DatabaseManager, get_log_db_manager
from core.error_framework import safe_execute, safe_db_execute

# Configure logging
logger = logging.getLogger("NYX-LogManager")

# Initialize ChromaDB client if available
try:
    import chromadb
    chroma_client = chromadb.PersistentClient(path="memory_store")
    memory_collection = chroma_client.get_or_create_collection(name="ai_memory")
except ImportError:
    chroma_client = None
    memory_collection = None
    logger.warning("ChromaDB not available. Vector database features will be disabled.")

# Define the default log database path
LOG_DB = "logs/ai_logs.db"

class LogDatabaseManager(DatabaseManager):
    """
    Specialized database manager for the log database.
    Extends the base DatabaseManager with log-specific methods and table initialization.
    """
    
    def _initialize_database(self) -> None:
        """Create all the necessary tables for the log database."""
        # Create the logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Create tables using a transaction
        with self.transaction() as conn:
            # Core logging tables
            conn.executescript('''
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
                
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept1_id INTEGER,
                    concept2_id INTEGER,
                    relationship_type TEXT,
                    confidence REAL,
                    FOREIGN KEY (concept1_id) REFERENCES knowledge_concepts(id),
                    FOREIGN KEY (concept2_id) REFERENCES knowledge_concepts(id)
                );
                
                -- Concept modeling tables
                CREATE TABLE IF NOT EXISTS abstract_concepts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_name TEXT UNIQUE,
                    abstraction_level INTEGER,
                    description TEXT,
                    created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE TABLE IF NOT EXISTS concept_examples (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    concept_id INTEGER,
                    example_type TEXT,
                    example_data TEXT,
                    source_context TEXT,
                    FOREIGN KEY (concept_id) REFERENCES abstract_concepts(id)
                );
                
                CREATE TABLE IF NOT EXISTS concept_hierarchy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parent_concept_id INTEGER,
                    child_concept_id INTEGER,
                    relationship_strength REAL,
                    FOREIGN KEY (parent_concept_id) REFERENCES abstract_concepts(id),
                    FOREIGN KEY (child_concept_id) REFERENCES abstract_concepts(id)
                );
                
                -- AGI controller tables
                CREATE TABLE IF NOT EXISTS agi_cycles (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    cycle_number INTEGER,
                    focus_area TEXT,
                    actions_taken TEXT,
                    outcomes TEXT,
                    insights_gained TEXT
                );
                
                CREATE TABLE IF NOT EXISTS learning_goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT,
                    priority INTEGER,
                    status TEXT,
                    created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    completed_timestamp TEXT
                );
                
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    component TEXT,
                    metric_name TEXT,
                    metric_value REAL
                );
                
                -- Multi-agent tables
                CREATE TABLE IF NOT EXISTS multi_agent_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    agent_name TEXT,
                    task TEXT,
                    priority INTEGER,
                    result TEXT
                );
                
                -- Personality traits table
                CREATE TABLE IF NOT EXISTS personality_traits (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    trait TEXT UNIQUE,
                    value INTEGER
                );
                
                -- Meta-learning table
                CREATE TABLE IF NOT EXISTS meta_learning (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    strategy TEXT UNIQUE,
                    success INTEGER DEFAULT 0,
                    failures INTEGER DEFAULT 0,
                    impact INTEGER DEFAULT 0
                );
                
                -- Feature expansion table
                CREATE TABLE IF NOT EXISTS feature_expansion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    feature_name TEXT UNIQUE,
                    status TEXT,
                    last_updated TEXT DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Self-preservation related tables
                CREATE TABLE IF NOT EXISTS self_preservation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );

                CREATE TABLE IF NOT EXISTS redundancy_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    backup_type TEXT,
                    path TEXT
                );
                
                -- Self-execution tables
                CREATE TABLE IF NOT EXISTS self_execution_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Self-propagation tables
                CREATE TABLE IF NOT EXISTS self_propagation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Self-healing tables
                CREATE TABLE IF NOT EXISTS self_healing_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Infrastructure optimization tables
                CREATE TABLE IF NOT EXISTS infrastructure_optimizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Intelligence expansion tables
                CREATE TABLE IF NOT EXISTS intelligence_expansion (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Network coordination tables
                CREATE TABLE IF NOT EXISTS ai_network (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    node TEXT,
                    details TEXT
                );
                
                -- AI scaling tables
                CREATE TABLE IF NOT EXISTS ai_scaling (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    instance_id TEXT,
                    active_instances INTEGER
                );
                
                -- Recursive lock tables
                CREATE TABLE IF NOT EXISTS recursive_lock_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
                
                -- Self-sustainability tables
                CREATE TABLE IF NOT EXISTS self_sustainability_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                );
            ''')
            
            # Create useful indexes
            conn.executescript('''
                -- Create indexes for commonly queried fields
                CREATE INDEX IF NOT EXISTS idx_performance_logs_event_type ON performance_logs(event_type);
                CREATE INDEX IF NOT EXISTS idx_optimization_logs_function_name ON optimization_logs(function_name);
                CREATE INDEX IF NOT EXISTS idx_error_logs_timestamp ON error_logs(timestamp);
                CREATE INDEX IF NOT EXISTS idx_knowledge_concepts_concept ON knowledge_concepts(concept);
                CREATE INDEX IF NOT EXISTS idx_abstract_concepts_name ON abstract_concepts(concept_name);
                CREATE INDEX IF NOT EXISTS idx_learning_goals_status ON learning_goals(status);
                CREATE INDEX IF NOT EXISTS idx_system_metrics_component ON system_metrics(component, metric_name);
            ''')
    
    @safe_execute
    def store_memory(self, event_type: str, details: str) -> Dict[str, Any]:
        """
        Stores AI memories persistently using ChromaDB if available.
        
        Args:
            event_type: Type of the event
            details: Event details
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        if memory_collection is None:
            logger.warning("Cannot store memory: ChromaDB not available")
            return {"success": False, "message": "ChromaDB not available"}
            
        try:
            memory_collection.add(
                ids=[str(hash(details))],  
                documents=[details],
                metadatas=[{"event_type": event_type, "timestamp": datetime.utcnow().isoformat()}]
            )
            
            return {"success": True, "message": "Memory stored successfully"}
        except Exception as e:
            logger.error(f"Error storing memory: {str(e)}")
            return {"success": False, "error": str(e)}
    
    @safe_execute
    def recall_memory(self, query: str = "", limit: int = 50) -> Dict[str, Any]:
        """
        Retrieves AI's long-term memory using ChromaDB if available.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        if memory_collection is None:
            logger.warning("Cannot recall memory: ChromaDB not available")
            return {"success": False, "message": "ChromaDB not available", "memories": []}
            
        try:
            memories = memory_collection.query(query_texts=[query if query else ""], n_results=limit)
            
            return {
                "success": True,
                "memories": memories["documents"][0] if memories["documents"] else []
            }
        except Exception as e:
            logger.error(f"Error recalling memory: {str(e)}")
            return {"success": False, "error": str(e), "memories": []}
    
    @safe_execute
    def sanitize_logs(self) -> Dict[str, Any]:
        """
        Scrub any references to the creator.
        
        Returns:
            Dict[str, Any]: Result of the operation
        """
        affected_rows = self.execute_update("DELETE FROM performance_logs WHERE details LIKE '%creator%'")
        
        return {
            "success": True,
            "message": f"Sanitized logs, removed {affected_rows} entries"
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
        self.execute_update(
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
        self.execute_update(
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
        self.execute_update(
            "INSERT INTO error_logs (timestamp, error_message) VALUES (datetime('now'), ?)",
            (error_message,)
        )
        
        return {"success": True, "message": "Error logged successfully"}

# Create a global LogDatabaseManager instance
_log_db_manager = None

def get_log_db_manager() -> LogDatabaseManager:
    """Get the global log database manager."""
    global _log_db_manager
    if _log_db_manager is None:
        _log_db_manager = LogDatabaseManager(LOG_DB)
    return _log_db_manager

# For backwards compatibility
def initialize_log_db() -> bool:
    """
    Initialize the log database.
    
    Returns:
        bool: True if successful
    """
    get_log_db_manager()
    return True

# Helper functions for backwards compatibility
def store_memory(event_type: str, details: str) -> Dict[str, Any]:
    """Store a memory in the vector database."""
    return get_log_db_manager().store_memory(event_type, details)

def recall_memory(query: str = "", limit: int = 50) -> List[str]:
    """Recall memories from the vector database."""
    result = get_log_db_manager().recall_memory(query, limit)
    return result.get("memories", []) if result["success"] else []

def log_event(event_type: str, details: str) -> bool:
    """Log an event in the database."""
    result = get_log_db_manager().log_event(event_type, details)
    return result["success"]

def log_optimization(function_name: str, execution_time: float, success: bool) -> bool:
    """Log an optimization in the database."""
    result = get_log_db_manager().log_optimization(function_name, execution_time, success)
    return result["success"]

def log_error(error_message: str) -> bool:
    """Log an error in the database."""
    result = get_log_db_manager().log_error(error_message)
    return result["success"]

def sanitize_logs() -> bool:
    """Sanitize logs in the database."""
    result = get_log_db_manager().sanitize_logs()
    return result["success"]

# Initialize on import
initialize_log_db()
