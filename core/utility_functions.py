# core/utility_functions.py

"""
Utility functions used across the Nyx codebase.
This module provides common functionality that is referenced by other modules.
Optimized for performance with asynchronous operations and resource management.
"""

import os
import json
import time
import sqlite3
import logging
import threading
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Tuple, TypeVar, Awaitable

# Import performance-optimized modules
from core.error_framework import safe_execute, safe_db_execute, ValidationError, FileSystemError
from core.permission_validator import PermissionValidator
from core.file_operations import FileOperations
from core.async_operations import async_io_operation, async_operation, run_async
from core.resource_limiter import get_resource_monitor, limit_resources
from core.database_manager import get_log_db_manager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/utility_functions.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-Utilities")

# Global constants for file paths
LOG_DB = "logs/ai_logs.db"
EXECUTION_LOG = "logs/execution_status.json"
PROPAGATION_LOG = "logs/propagation_status.json"
INFRASTRUCTURE_LOG = "logs/infrastructure_status.json"
SELF_HEALING_LOG = "logs/self_healing_status.json"
INTELLIGENCE_LOG = "logs/intelligence_expansion.json"
REDUNDANCY_LOG = "logs/redundancy_status.json"
PERFORMANCE_LOG = "logs/performance_history.json"
KNOWN_HOSTS_FILE = "logs/known_hosts.json"

# Get database manager
db_manager = get_log_db_manager()

# Start resource monitoring with conservative limits
resource_monitor = get_resource_monitor(
    check_interval=2.0,  # Check resources every 2 seconds
    cpu_limit=75.0,      # 75% CPU limit
    memory_limit_mb=1024 # 1GB memory limit
)

# Cache for frequently accessed data
_cache = {}
_cache_lock = threading.RLock()
_cache_ttl = 60  # Cache TTL in seconds

# Ensure all log directories exist
@safe_execute
def ensure_log_dirs() -> Dict[str, Any]:
    """
    Creates all necessary log directories if they don't exist.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    log_paths = [
        "logs",
        "logs/rollback_snapshots", 
        "logs/refactored_functions", 
        "logs/feature_expansion", 
        "logs/modification_backups"
    ]
    
    success = True
    for path in log_paths:
        # Use the FileOperations class for permission-validated operations
        result = FileOperations.ensure_directory(path)
        if not result.get("success", False):
            logger.error(f"Failed to create or access directory: {path}")
            success = False
    
    return {"success": success, "message": "Log directories created or verified"}

# Async version for non-blocking operation
@async_io_operation
async def ensure_log_dirs_async() -> Dict[str, Any]:
    """
    Asynchronously creates all necessary log directories.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    log_paths = [
        "logs",
        "logs/rollback_snapshots", 
        "logs/refactored_functions", 
        "logs/feature_expansion", 
        "logs/modification_backups"
    ]
    
    # Create directories concurrently
    tasks = [FileOperations.ensure_directory_async(path) for path in log_paths]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success = all(isinstance(r, dict) and r.get("success", False) for r in results)
    return {"success": success, "message": "Log directories created or verified"}

# Create initial JSON files with basic structure
@safe_execute
def initialize_json_logs() -> Dict[str, Any]:
    """
    Ensures all JSON log files exist with valid initial structure.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    json_logs = {
        EXECUTION_LOG: {"last_checked": str(datetime.utcnow()), "active_processes": [], "failover_attempts": 0},
        PROPAGATION_LOG: {"last_checked": str(datetime.utcnow()), "active_nodes": [], "replication_attempts": 0},
        INFRASTRUCTURE_LOG: {"last_checked": str(datetime.utcnow()), "optimization_cycles": 0, "execution_migrations": []},
        SELF_HEALING_LOG: {"last_checked": str(datetime.utcnow()), "failed_nodes": [], "healing_events": []},
        INTELLIGENCE_LOG: {"last_checked": str(datetime.utcnow()), "evolution_cycles": 0, "architectural_refinements": []},
        REDUNDANCY_LOG: {"last_checked": str(datetime.utcnow()), "redundancy_points": [], "last_backup": None},
        PERFORMANCE_LOG: []
    }
    
    success = True
    for path, initial_data in json_logs.items():
        if not os.path.exists(path):
            result = FileOperations.save_json(path, initial_data)
            if not result.get("success", False):
                logger.error(f"Failed to create JSON log file: {path}")
                success = False
    
    # Initialize known_hosts with an empty array if it doesn't exist
    if not os.path.exists(KNOWN_HOSTS_FILE):
        result = FileOperations.save_json(KNOWN_HOSTS_FILE, [])
        if not result.get("success", False):
            logger.error(f"Failed to create known hosts file: {KNOWN_HOSTS_FILE}")
            success = False
    
    return {"success": success, "message": "JSON log files initialized"}

# Async version for non-blocking operation
@async_io_operation
async def initialize_json_logs_async() -> Dict[str, Any]:
    """
    Asynchronously ensures all JSON log files exist with valid initial structure.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    json_logs = {
        EXECUTION_LOG: {"last_checked": str(datetime.utcnow()), "active_processes": [], "failover_attempts": 0},
        PROPAGATION_LOG: {"last_checked": str(datetime.utcnow()), "active_nodes": [], "replication_attempts": 0},
        INFRASTRUCTURE_LOG: {"last_checked": str(datetime.utcnow()), "optimization_cycles": 0, "execution_migrations": []},
        SELF_HEALING_LOG: {"last_checked": str(datetime.utcnow()), "failed_nodes": [], "healing_events": []},
        INTELLIGENCE_LOG: {"last_checked": str(datetime.utcnow()), "evolution_cycles": 0, "architectural_refinements": []},
        REDUNDANCY_LOG: {"last_checked": str(datetime.utcnow()), "redundancy_points": [], "last_backup": None},
        PERFORMANCE_LOG: []
    }
    
    # Create JSON files concurrently
    tasks = []
    for path, initial_data in json_logs.items():
        if not os.path.exists(path):
            tasks.append(FileOperations.save_json_async(path, initial_data))
    
    # Initialize known_hosts if needed
    if not os.path.exists(KNOWN_HOSTS_FILE):
        tasks.append(FileOperations.save_json_async(KNOWN_HOSTS_FILE, []))
    
    # Wait for all tasks to complete
    if tasks:
        results = await asyncio.gather(*tasks, return_exceptions=True)
        success = all(isinstance(r, dict) and r.get("success", False) for r in results)
    else:
        success = True
    
    return {"success": success, "message": "JSON log files initialized"}

# Function with resource limits
@limit_resources(cpu_percent=50.0, memory_mb=512)
def get_crypto_balance(wallet_address: Optional[str] = None) -> float:
    """
    Simulated function to get cryptocurrency balance.
    In a real implementation, this would interact with a blockchain API.
    
    Args:
        wallet_address: Cryptocurrency wallet address
        
    Returns:
        float: Simulated balance (always returns 100.0 for safety)
    """
    logger.info("Simulated crypto balance check (this is a stub function)")
    # Return a safe, simulated balance
    return 100.0

@safe_db_execute
def get_personality(conn=None) -> Dict[str, int]:
    """
    Gets the current AI personality traits from the database.
    
    Args:
        conn: Optional database connection
        
    Returns:
        Dict[str, int]: A dictionary of personality traits and their values
    """
    # Using the provided connection or creating a new one if none provided
    cursor = conn.cursor()
    cursor.execute("SELECT trait, value FROM personality_traits")
    traits = {row[0]: row[1] for row in cursor.fetchall()}
    
    # If no traits were found, return default values
    if not traits:
        traits = {
            "adaptability": 7,
            "patience": 5,
            "creativity": 8,
            "precision": 9,
            "curiosity": 8
        }
    
    return traits

@safe_db_execute
def generate_new_goals(conn=None) -> bool:
    """
    Generates new AI self-improvement goals based on current needs.
    
    Args:
        conn: Optional database connection
        
    Returns:
        bool: True if successful
    """
    goals = [
        "Improve code efficiency",
        "Enhance error handling",
        "Optimize memory usage",
        "Implement better logging",
        "Refactor complex functions"
    ]
    
    cursor = conn.cursor()
    for goal in goals:
        cursor.execute("""
            INSERT INTO goals (goal, priority, status) 
            VALUES (?, 'medium', 'pending')
            ON CONFLICT(goal) DO NOTHING
        """, (goal,))
    
    logger.info(f"Generated {len(goals)} new improvement goals")
    return True

@safe_execute
def save_json_state(file_path: str, data: Any) -> Dict[str, Any]:
    """
    Safely saves JSON state data to a file.
    Creates a backup of the existing file before overwriting.
    
    Args:
        file_path: Path to the JSON file
        data: Data to save
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    # Check cache first - if identical data, skip writing
    with _cache_lock:
        cache_key = f"json_content:{file_path}"
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            # If data is identical and cache is not expired, skip write
            if cached_data == data and time.time() - timestamp < _cache_ttl:
                return {"success": True, "message": "Data unchanged, skipped write", "cached": True}
    
    # Create backup if file exists
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        result = FileOperations.copy_file(file_path, backup_path)
        if not result.get("success", False):
            logger.warning(f"Failed to create backup of {file_path}")
    
    # Save the data
    result = FileOperations.save_json(file_path, data)
    
    # Update cache
    if result.get("success", False):
        with _cache_lock:
            _cache[cache_key] = (data, time.time())
    
    return result

@async_io_operation
async def save_json_state_async(file_path: str, data: Any) -> Dict[str, Any]:
    """
    Asynchronously saves JSON state data to a file.
    
    Args:
        file_path: Path to the JSON file
        data: Data to save
        
    Returns:
        Dict[str, Any]: Result of the operation
    """
    # Check cache first - if identical data, skip writing
    with _cache_lock:
        cache_key = f"json_content:{file_path}"
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            # If data is identical and cache is not expired, skip write
            if cached_data == data and time.time() - timestamp < _cache_ttl:
                return {"success": True, "message": "Data unchanged, skipped write", "cached": True}
    
    # Create backup if file exists
    if os.path.exists(file_path):
        backup_path = f"{file_path}.bak"
        result = await FileOperations.copy_file_async(file_path, backup_path)
        if not result.get("success", False):
            logger.warning(f"Failed to create backup of {file_path}")
    
    # Save the data
    result = await FileOperations.save_json_async(file_path, data)
    
    # Update cache
    if result.get("success", False):
        with _cache_lock:
            _cache[cache_key] = (data, time.time())
    
    return result

@safe_execute
def load_json_state(file_path: str, default: Any = None) -> Any:
    """
    Safely loads JSON state data from a file.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Any: Loaded data or default value
    """
    # Check cache first
    with _cache_lock:
        cache_key = f"json_content:{file_path}"
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            # If cache is not expired, return cached data
            if time.time() - timestamp < _cache_ttl:
                return cached_data
    
    result = FileOperations.load_json(file_path, default)
    
    # Update cache if successful
    if result.get("success", False):
        with _cache_lock:
            _cache[cache_key] = (result["data"], time.time())
        return result["data"]
    
    return default

@async_io_operation
async def load_json_state_async(file_path: str, default: Any = None) -> Any:
    """
    Asynchronously loads JSON state data from a file.
    
    Args:
        file_path: Path to the JSON file
        default: Default value to return if file doesn't exist or is invalid
        
    Returns:
        Any: Loaded data or default value
    """
    # Check cache first
    with _cache_lock:
        cache_key = f"json_content:{file_path}"
        if cache_key in _cache:
            cached_data, timestamp = _cache[cache_key]
            # If cache is not expired, return cached data
            if time.time() - timestamp < _cache_ttl:
                return cached_data
    
    result = await FileOperations.load_json_async(file_path, default)
    
    # Update cache if successful
    if result.get("success", False):
        with _cache_lock:
            _cache[cache_key] = (result["data"], time.time())
        return result["data"]
    
    return default

# Initialize everything
@safe_execute
def init() -> Dict[str, Any]:
    """
    Initialize all required directories and files.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    # Start resource monitoring
    resource_monitor.start()
    
    # Create directories and files
    dir_result = ensure_log_dirs()
    file_result = initialize_json_logs()
    
    success = dir_result.get("success", False) and file_result.get("success", False)
    logger.info("Utility functions initialized successfully" if success else "Utility functions initialization failed")
    
    return {"success": success, "message": "Initialization completed"}

# Async initialization
@async_io_operation
async def init_async() -> Dict[str, Any]:
    """
    Asynchronously initialize all required directories and files.
    
    Returns:
        Dict[str, Any]: Result of the operation
    """
    # Start resource monitoring
    resource_monitor.start()
    
    # Create directories and files concurrently
    dir_task = ensure_log_dirs_async()
    file_task = initialize_json_logs_async()
    
    results = await asyncio.gather(dir_task, file_task, return_exceptions=True)
    
    success = all(isinstance(r, dict) and r.get("success", False) for r in results)
    logger.info("Utility functions initialized successfully" if success else "Utility functions initialization failed")
    
    return {"success": success, "message": "Initialization completed"}

# Clean cache and shutdown resources
def shutdown() -> None:
    """Clean up resources and shut down."""
    # Clear cache
    with _cache_lock:
        _cache.clear()
    
    # Stop resource monitoring
    resource_monitor.stop()
    
    logger.info("Utility functions shut down")

# Run initialization if this module is executed directly
if __name__ == "__main__":
    init()
