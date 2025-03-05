# core/error_handler.py

"""
Error handling utilities for the Nyx codebase.
This module provides functions to standardize error handling across the codebase.
"""

import sys
import os
import traceback
import logging
import sqlite3
from functools import wraps
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/errors.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-ErrorHandler")

# SQLite database for error logging
LOG_DB = "logs/ai_logs.db"

def log_error_to_db(error_type, error_message, module_name, function_name, traceback_str):
    """
    Log an error to the SQLite database.
    
    Args:
        error_type (str): Type of the error
        error_message (str): Error message
        module_name (str): Name of the module where the error occurred
        function_name (str): Name of the function where the error occurred
        traceback_str (str): Full traceback string
    """
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        
        # Ensure the table exists
        c.execute('''CREATE TABLE IF NOT EXISTS detailed_error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT,
                    error_message TEXT,
                    module_name TEXT,
                    function_name TEXT,
                    traceback TEXT
                 )''')
        
        c.execute("""
            INSERT INTO detailed_error_logs 
            (timestamp, error_type, error_message, module_name, function_name, traceback)
            VALUES (datetime('now'), ?, ?, ?, ?, ?)
        """, (error_type, error_message, module_name, function_name, traceback_str))
        
        # Also add to simple error_logs table for backward compatibility
        c.execute("""
            INSERT INTO error_logs (timestamp, error_message)
            VALUES (datetime('now'), ?)
        """, (f"{error_type} in {module_name}.{function_name}: {error_message}",))
        
        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"Failed to log error to database: {str(e)}")
        # Don't raise an exception here to avoid infinite recursion

def handle_error(e, module_name, function_name):
    """
    Handle an exception with standardized logging.
    
    Args:
        e (Exception): The exception that was raised
        module_name (str): Name of the module where the error occurred
        function_name (str): Name of the function where the error occurred
        
    Returns:
        str: Error message for user feedback
    """
    error_type = type(e).__name__
    error_message = str(e)
    traceback_str = traceback.format_exc()
    
    # Log to file
    logger.error(f"{error_type} in {module_name}.{function_name}: {error_message}\n{traceback_str}")
    
    # Log to database
    log_error_to_db(error_type, error_message, module_name, function_name, traceback_str)
    
    # Return a friendly message for user feedback
    return f"An error occurred in {function_name}: {error_message}"

def safe_execute(func):
    """
    Decorator to safely execute a function with error handling.
    
    Args:
        func: The function to decorate
        
    Returns:
        function: Decorated function with error handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            module_name = func.__module__ if hasattr(func, "__module__") else "unknown_module"
            function_name = func.__name__ if hasattr(func, "__name__") else "unknown_function"
            error_msg = handle_error(e, module_name, function_name)
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
    return wrapper

def safe_db_execute(func):
    """
    Decorator to safely execute a function that uses SQLite with connection handling.
    
    Args:
        func: The function to decorate
        
    Returns:
        function: Decorated function with database connection handling
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect(LOG_DB)
            kwargs['conn'] = conn
            result = func(*args, **kwargs)
            if conn:
                conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
            module_name = func.__module__ if hasattr(func, "__module__") else "unknown_module"
            function_name = func.__name__ if hasattr(func, "__name__") else "unknown_function"
            error_msg = handle_error(e, module_name, function_name)
            logger.error(error_msg)
            return {"success": False, "error": error_msg}
        finally:
            if conn:
                conn.close()
    return wrapper

def fail_gracefully(default_return=None):
    """
    Decorator to gracefully handle failures by returning a default value.
    
    Args:
        default_return: The default value to return on failure
        
    Returns:
        function: Decorator function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                module_name = func.__module__ if hasattr(func, "__module__") else "unknown_module"
                function_name = func.__name__ if hasattr(func, "__name__") else "unknown_function"
                handle_error(e, module_name, function_name)
                return default_return
        return wrapper
    return decorator

def get_error_summary(limit=10):
    """
    Get a summary of recent errors from the database.
    
    Args:
        limit (int): Maximum number of errors to retrieve
        
    Returns:
        list: List of error dictionaries
    """
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, error_type, error_message, module_name, function_name 
            FROM detailed_error_logs 
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
        
        errors = [
            {
                "timestamp": row[0],
                "error_type": row[1],
                "error_message": row[2],
                "module_name": row[3],
                "function_name": row[4]
            }
            for row in c.fetchall()
        ]
        
        conn.close()
        return errors
    except Exception as e:
        logger.error(f"Failed to get error summary: {str(e)}")
        return []

def get_most_common_errors(limit=5):
    """
    Get the most common errors from the database.
    
    Args:
        limit (int): Maximum number of error types to retrieve
        
    Returns:
        list: List of error dictionaries with count
    """
    try:
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            SELECT error_type, COUNT(*) as count
            FROM detailed_error_logs 
            GROUP BY error_type
            ORDER BY count DESC
            LIMIT ?
        """, (limit,))
        
        errors = [
            {
                "error_type": row[0],
                "count": row[1]
            }
            for row in c.fetchall()
        ]
        
        conn.close()
        return errors
    except Exception as e:
        logger.error(f"Failed to get most common errors: {str(e)}")
        return []
