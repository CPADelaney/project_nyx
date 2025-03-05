# core/error_framework.py

"""
Unified error handling framework for the Nyx codebase.
Provides consistent error handling, logging, and recovery mechanisms.
"""

import sys
import os
import traceback
import logging
import sqlite3
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable, TypeVar, Type, Union, List
from functools import wraps

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NYX-ErrorFramework")

# Database connection
LOG_DB = "logs/ai_logs.db"

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')

class ErrorSeverity:
    """Enumeration of error severity levels."""
    DEBUG = 10
    INFO = 20
    WARNING = 30
    ERROR = 40
    CRITICAL = 50

class NyxError(Exception):
    """Base class for all Nyx-specific exceptions."""
    
    def __init__(self, message: str, severity: int = ErrorSeverity.ERROR, 
                 details: Optional[Dict[str, Any]] = None, 
                 cause: Optional[Exception] = None):
        """
        Initialize a new NyxError.
        
        Args:
            message: The error message
            severity: The error severity (from ErrorSeverity class)
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        self.message = message
        self.severity = severity
        self.details = details or {}
        self.cause = cause
        self.timestamp = datetime.now()
        self.traceback = traceback.format_exc()
        
        # Call the parent constructor
        super().__init__(message)

class ValidationError(NyxError):
    """Exception raised for input validation errors."""
    def __init__(self, message: str, field: Optional[str] = None, 
                 value: Optional[Any] = None, **kwargs):
        details = kwargs.pop('details', {})
        details.update({
            'field': field,
            'value': value
        })
        super().__init__(message, ErrorSeverity.WARNING, details, **kwargs)

class SecurityError(NyxError):
    """Exception raised for security-related errors."""
    def __init__(self, message: str, security_context: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        details.update({
            'security_context': security_context
        })
        super().__init__(message, ErrorSeverity.CRITICAL, details, **kwargs)

class DatabaseError(NyxError):
    """Exception raised for database-related errors."""
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        details.update({
            'query': query
        })
        super().__init__(message, ErrorSeverity.ERROR, details, **kwargs)

class APIError(NyxError):
    """Exception raised for API-related errors."""
    def __init__(self, message: str, status_code: int = 500, 
                 endpoint: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        details.update({
            'status_code': status_code,
            'endpoint': endpoint
        })
        super().__init__(message, ErrorSeverity.ERROR, details, **kwargs)

class FileSystemError(NyxError):
    """Exception raised for file system-related errors."""
    def __init__(self, message: str, path: Optional[str] = None, 
                 operation: Optional[str] = None, **kwargs):
        details = kwargs.pop('details', {})
        details.update({
            'path': path,
            'operation': operation
        })
        super().__init__(message, ErrorSeverity.ERROR, details, **kwargs)

class ErrorHandler:
    """
    Handles errors in a consistent way across the codebase.
    Provides logging, reporting, and recovery mechanisms.
    """
    
    def __init__(self, db_path: str = LOG_DB):
        """
        Initialize the error handler.
        
        Args:
            db_path: Path to the SQLite database for error logging
        """
        self.db_path = db_path
        self._initialize_database()
        
        # Recovery strategies keyed by error type
        self.recovery_strategies: Dict[Type[Exception], Callable] = {}
    
    def _initialize_database(self) -> None:
        """Initialize the error logging database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Create error_logs table if it doesn't exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                )
            ''')
            
            # Create detailed_error_logs table if it doesn't exist
            c.execute('''
                CREATE TABLE IF NOT EXISTS detailed_error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    error_type TEXT,
                    error_message TEXT,
                    severity INTEGER,
                    module_name TEXT,
                    function_name TEXT,
                    details TEXT,
                    traceback TEXT
                )
            ''')
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to initialize error database: {str(e)}")
    
    def handle(self, error: Exception, module_name: str, function_name: str) -> Dict[str, Any]:
        """
        Handle an exception with standardized logging.
        
        Args:
            error: The exception that was raised
            module_name: Name of the module where the error occurred
            function_name: Name of the function where the error occurred
            
        Returns:
            Dict[str, Any]: Error information for user feedback
        """
        error_type = type(error).__name__
        
        # Extract additional information if it's a NyxError
        if isinstance(error, NyxError):
            error_message = error.message
            severity = error.severity
            details = error.details
            traceback_str = error.traceback
        else:
            error_message = str(error)
            severity = ErrorSeverity.ERROR
            details = {}
            traceback_str = traceback.format_exc()
        
        # Log to file
        log_level = logging.ERROR
        if severity == ErrorSeverity.DEBUG:
            log_level = logging.DEBUG
        elif severity == ErrorSeverity.INFO:
            log_level = logging.INFO
        elif severity == ErrorSeverity.WARNING:
            log_level = logging.WARNING
        elif severity == ErrorSeverity.CRITICAL:
            log_level = logging.CRITICAL
            
        logger.log(log_level, f"{error_type} in {module_name}.{function_name}: {error_message}\n{traceback_str}")
        
        # Log to database
        self._log_to_database(error_type, error_message, severity, module_name, function_name, details, traceback_str)
        
        # Attempt recovery if a strategy exists
        recovery_result = None
        for error_class, strategy in self.recovery_strategies.items():
            if isinstance(error, error_class):
                try:
                    recovery_result = strategy(error)
                except Exception as recovery_error:
                    logger.error(f"Recovery strategy failed: {str(recovery_error)}")
        
        # Return a standardized error response
        return {
            "success": False,
            "error": {
                "type": error_type,
                "message": error_message,
                "module": module_name,
                "function": function_name,
                "timestamp": datetime.now().isoformat(),
                "recovery_attempted": recovery_result is not None,
                "recovery_result": recovery_result
            }
        }
    
    def _log_to_database(self, error_type: str, error_message: str, severity: int,
                        module_name: str, function_name: str, details: Dict[str, Any], 
                        traceback_str: str) -> None:
        """Log error details to the database."""
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            
            # Insert into detailed_error_logs
            c.execute("""
                INSERT INTO detailed_error_logs 
                (timestamp, error_type, error_message, severity, module_name, 
                 function_name, details, traceback)
                VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?)
            """, (
                error_type, 
                error_message, 
                severity, 
                module_name, 
                function_name, 
                json.dumps(details), 
                traceback_str
            ))
            
            # Also insert into simple error_logs for backward compatibility
            c.execute("""
                INSERT INTO error_logs (timestamp, error_message)
                VALUES (datetime('now'), ?)
            """, (f"{error_type} in {module_name}.{function_name}: {error_message}",))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Failed to log error to database: {str(e)}")
    
    def register_recovery_strategy(self, error_class: Type[Exception], 
                                  strategy: Callable[[Exception], Any]) -> None:
        """
        Register a recovery strategy for a specific error type.
        
        Args:
            error_class: The exception class to register the strategy for
            strategy: A function that takes an exception and returns a recovery result
        """
        self.recovery_strategies[error_class] = strategy
    
    def get_error_summary(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get a summary of recent errors from the database.
        
        Args:
            limit: Maximum number of errors to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of error summaries
        """
        try:
            conn = sqlite3.connect(self.db_path)
            c = conn.cursor()
            c.execute("""
                SELECT timestamp, error_type, error_message, severity, module_name, function_name 
                FROM detailed_error_logs 
                ORDER BY timestamp DESC
                LIMIT ?
            """, (limit,))
            
            errors = [
                {
                    "timestamp": row[0],
                    "error_type": row[1],
                    "error_message": row[2],
                    "severity": row[3],
                    "module_name": row[4],
                    "function_name": row[5]
                }
                for row in c.fetchall()
            ]
            
            conn.close()
            return errors
        except Exception as e:
            logger.error(f"Failed to get error summary: {str(e)}")
            return []
    
    def get_most_common_errors(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get the most common errors from the database.
        
        Args:
            limit: Maximum number of error types to retrieve
            
        Returns:
            List[Dict[str, Any]]: List of error types with count
        """
        try:
            conn = sqlite3.connect(self.db_path)
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

# Create decorator functions for standardized error handling

def safe_execute(f):
    """
    Decorator to safely execute a function with comprehensive error handling.
    
    Args:
        f: The function to decorate
        
    Returns:
        Callable: Decorated function with error handling
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Get module and function names
            module_name = f.__module__ if hasattr(f, "__module__") else "unknown_module"
            function_name = f.__name__ if hasattr(f, "__name__") else "unknown_function"
            
            # Create an error handler and handle the error
            handler = ErrorHandler()
            return handler.handle(e, module_name, function_name)
    return wrapper

def safe_db_execute(f):
    """
    Decorator to safely execute a function that uses SQLite with comprehensive error handling.
    
    Args:
        f: The function to decorate
        
    Returns:
        Callable: Decorated function with database and error handling
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        conn = None
        try:
            conn = sqlite3.connect(LOG_DB)
            kwargs['conn'] = conn
            result = f(*args, **kwargs)
            if conn:
                conn.commit()
            return result
        except Exception as e:
            if conn:
                conn.rollback()
                
            # Get module and function names
            module_name = f.__module__ if hasattr(f, "__module__") else "unknown_module"
            function_name = f.__name__ if hasattr(f, "__name__") else "unknown_function"
            
            # Create a more specific error if it's a database error
            if isinstance(e, sqlite3.Error):
                # Extract the SQL query if it's in the args or kwargs
                query = None
                if 'query' in kwargs:
                    query = kwargs['query']
                elif len(args) > 1 and isinstance(args[1], str):
                    query = args[1]
                    
                db_error = DatabaseError(str(e), query=query, cause=e)
                
                # Create an error handler and handle the error
                handler = ErrorHandler()
                return handler.handle(db_error, module_name, function_name)
            else:
                # Create an error handler and handle the error
                handler = ErrorHandler()
                return handler.handle(e, module_name, function_name)
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
        Callable: Decorator function
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except Exception as e:
                # Get module and function names
                module_name = f.__module__ if hasattr(f, "__module__") else "unknown_module"
                function_name = f.__name__ if hasattr(f, "__name__") else "unknown_function"
                
                # Create an error handler and handle the error (just for logging)
                handler = ErrorHandler()
                handler.handle(e, module_name, function_name)
                
                # Return the default value
                return default_return
        return wrapper
    return decorator

# Create a global error handler instance
error_handler = ErrorHandler()

def handle_error(e, module_name, function_name):
    """Global function to handle an error with the global error handler."""
    return error_handler.handle(e, module_name, function_name)

def register_recovery_strategy(error_class, strategy):
    """Global function to register a recovery strategy with the global error handler."""
    error_handler.register_recovery_strategy(error_class, strategy)

def get_error_summary(limit=10):
    """Global function to get an error summary from the global error handler."""
    return error_handler.get_error_summary(limit)

def get_most_common_errors(limit=5):
    """Global function to get the most common errors from the global error handler."""
    return error_handler.get_most_common_errors(limit)

# Example usage
if __name__ == "__main__":
    # Example function with error handling
    @safe_execute
    def divide(a, b):
        return a / b
    
    # Example database function with error handling
    @safe_db_execute
    def get_user(user_id, conn=None):
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        return c.fetchone()
    
    # Example function with graceful failure
    @fail_gracefully(default_return=[])
    def get_data():
        raise ValueError("Simulated error")
    
    # Register a recovery strategy for ValueError
    def value_error_recovery(e):
        return {"recovered": True, "original_error": str(e)}
    
    register_recovery_strategy(ValueError, value_error_recovery)
    
    # Test the error handling
    result = divide(10, 0)
    print(f"Division result: {result}")
    
    # Test graceful failure
    data = get_data()
    print(f"Data result: {data}")
    
    # Print error summary
    errors = get_error_summary()
    print(f"Error summary: {errors}")
