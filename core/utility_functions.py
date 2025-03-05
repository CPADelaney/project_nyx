# core/utility_functions.py

"""
Utility functions used across the Nyx codebase.
This module provides common functionality that is referenced by other modules
but was previously missing implementations.
"""

import os
import json
import time
import sqlite3
import logging
from datetime import datetime
from pathlib import Path
from core.permission_validator import PermissionValidator

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

# Ensure all log directories exist
def ensure_log_dirs():
    """Creates all necessary log directories if they don't exist, with permission validation."""
    log_paths = [
        "logs",
        "logs/rollback_snapshots", 
        "logs/refactored_functions", 
        "logs/feature_expansion", 
        "logs/modification_backups"
    ]
    
    success = True
    for path in log_paths:
        # Use permission validator to ensure directory is safe and writable
        if not PermissionValidator.ensure_safe_directory(path):
            logger.error(f"Failed to create or access directory: {path}")
            success = False
    
    return success

def save_json_state(file_path, data):
    """
    Safely saves JSON state data to a file with permission validation.
    Creates a backup of the existing file before overwriting.
    
    Args:
        file_path (str): Path to the JSON file
        data (dict): Data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate file path
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            logger.error(f"Invalid file path: {file_path}")
            return False
        
        # Check if we can write to the file
        if not PermissionValidator.can_write_file(safe_path):
            logger.error(f"Cannot write to file: {safe_path}")
            return False
        
        # Create backup of existing file if it exists
        if os.path.exists(safe_path):
            backup_path = f"{safe_path}.bak"
            if PermissionValidator.can_write_file(backup_path):
                shutil.copy2(safe_path, backup_path)
            else:
                logger.warning(f"Could not create backup at {backup_path}")
        
        # Write new data
        with open(safe_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        logger.error(f"Error saving JSON state to {file_path}: {str(e)}")
        return False

# Load function with permission validation
def load_json_state(file_path, default=None):
    """
    Safely loads JSON state data from a file with permission validation.
    
    Args:
        file_path (str): Path to the JSON file
        default (any): Default value to return if file doesn't exist or is invalid
        
    Returns:
        dict: Loaded data or default value
    """
    try:
        # Validate file path
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            logger.error(f"Invalid file path: {file_path}")
            return default
        
        if not os.path.exists(safe_path):
            return default
            
        # Check if we can read the file
        if not PermissionValidator.can_read_file(safe_path):
            logger.error(f"Cannot read file: {safe_path}")
            return default
            
        with open(safe_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {file_path}")
        return default
    except Exception as e:
        logger.error(f"Error loading JSON state from {file_path}: {str(e)}")
        return default

# Create initial JSON files with basic structure
def initialize_json_logs():
    """Ensures all JSON log files exist with valid initial structure."""
    json_logs = {
        EXECUTION_LOG: {"last_checked": str(datetime.utcnow()), "active_processes": [], "failover_attempts": 0},
        PROPAGATION_LOG: {"last_checked": str(datetime.utcnow()), "active_nodes": [], "replication_attempts": 0},
        INFRASTRUCTURE_LOG: {"last_checked": str(datetime.utcnow()), "optimization_cycles": 0, "execution_migrations": []},
        SELF_HEALING_LOG: {"last_checked": str(datetime.utcnow()), "failed_nodes": [], "healing_events": []},
        INTELLIGENCE_LOG: {"last_checked": str(datetime.utcnow()), "evolution_cycles": 0, "architectural_refinements": []},
        REDUNDANCY_LOG: {"last_checked": str(datetime.utcnow()), "redundancy_points": [], "last_backup": None},
        PERFORMANCE_LOG: []
    }
    
    for path, initial_data in json_logs.items():
        if not os.path.exists(path):
            with open(path, "w", encoding="utf-8") as f:
                json.dump(initial_data, f, indent=4)
    
    # Initialize known_hosts with an empty array if it doesn't exist
    if not os.path.exists(KNOWN_HOSTS_FILE):
        with open(KNOWN_HOSTS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f, indent=4)
    
    return True

# Missing utility functions
def get_crypto_balance(wallet_address=None):
    """
    Simulated function to get cryptocurrency balance.
    In a real implementation, this would interact with a blockchain API.
    
    Returns:
        float: Simulated balance (always returns 100.0 for safety)
    """
    logger.info("Simulated crypto balance check (this is a stub function)")
    # Return a safe, simulated balance
    return 100.0

def get_personality():
    """
    Gets the current AI personality traits from the database.
    
    Returns:
        dict: A dictionary of personality traits and their values
    """
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT trait, value FROM personality_traits")
        traits = {row[0]: row[1] for row in c.fetchall()}
        conn.close()
        
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
    except Exception as e:
        logger.error(f"Error getting personality traits: {str(e)}")
        # Return safe default values
        return {
            "adaptability": 7,
            "patience": 5,
            "creativity": 8,
            "precision": 9,
            "curiosity": 8
        }

def generate_new_goals():
    """
    Generates new AI self-improvement goals based on current needs.
    """
    goals = [
        "Improve code efficiency",
        "Enhance error handling",
        "Optimize memory usage",
        "Implement better logging",
        "Refactor complex functions"
    ]
    
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        for goal in goals:
            c.execute("""
                INSERT INTO goals (goal, priority, status) 
                VALUES (?, 'medium', 'pending')
                ON CONFLICT(goal) DO NOTHING
            """, (goal,))
            
        conn.commit()
        conn.close()
        
        logger.info(f"Generated {len(goals)} new improvement goals")
        return True
    except Exception as e:
        logger.error(f"Error generating new goals: {str(e)}")
        return False

def save_json_state(file_path, data):
    """
    Safely saves JSON state data to a file.
    Creates a backup of the existing file before overwriting.
    
    Args:
        file_path (str): Path to the JSON file
        data (dict): Data to save
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Create backup of existing file if it exists
        if os.path.exists(file_path):
            backup_path = f"{file_path}.bak"
            shutil.copy2(file_path, backup_path)
        
        # Write new data
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            
        return True
    except Exception as e:
        logger.error(f"Error saving JSON state to {file_path}: {str(e)}")
        return False

def load_json_state(file_path, default=None):
    """
    Safely loads JSON state data from a file.
    
    Args:
        file_path (str): Path to the JSON file
        default (any): Default value to return if file doesn't exist or is invalid
        
    Returns:
        dict: Loaded data or default value
    """
    try:
        if not os.path.exists(file_path):
            return default
            
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {file_path}")
        return default
    except Exception as e:
        logger.error(f"Error loading JSON state from {file_path}: {str(e)}")
        return default

# Initialize everything
def init():
    """Initialize all required directories and files."""
    ensure_log_dirs()
    initialize_json_logs()
    logger.info("Utility functions initialized successfully")

# Run initialization if this module is executed directly
if __name__ == "__main__":
    init()
