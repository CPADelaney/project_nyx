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
    except Exception
