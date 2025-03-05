# core/database_manager.py

"""
Database connection manager for the Nyx codebase.
Provides connection pooling, context management, and transaction support for SQLite.
"""

import os
import sqlite3
import threading
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union, Callable
from contextlib import contextmanager

logger = logging.getLogger("NYX-DatabaseManager")

class DatabaseManager:
    """
    Manages database connections with connection pooling.
    Provides a simple API for database operations with proper connection handling.
    """
    
    def __init__(self, db_path: str, pool_size: int = 5, timeout: float = 30.0):
        """
        Initialize the database manager.
        
        Args:
            db_path: Path to the SQLite database
            pool_size: Maximum number of connections in the pool
            timeout: Timeout in seconds for connection acquisition
        """
        self.db_path = db_path
        self.pool_size = pool_size
        self.timeout = timeout
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        # Initialize connection pool
        self._pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.RLock()
        self._in_use: Dict[int, bool] = {}
        
        # Thread-local storage for connection caching
        self._local = threading.local()
        
        # Initialize the database
        self._initialize_database()
        
        logger.info(f"Initialized database manager for {db_path} with pool size {pool_size}")
    
    def _initialize_database(self) -> None:
        """Create any necessary tables and indexes."""
        # This method should be overridden by subclasses to create
        # specific tables for their needs. The base class just ensures
        # the database file exists.
        if not os.path.exists(self.db_path):
            # Create an empty database file
            conn = sqlite3.connect(self.db_path)
            conn.close()
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create a new database connection."""
        conn = sqlite3.connect(self.db_path)
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys = ON")
        
        # Set connection properties
        conn.row_factory = sqlite3.Row
        
        return conn
    
    def _get_connection(self) -> Tuple[sqlite3.Connection, int]:
        """
        Get a connection from the pool or create a new one.
        
        Returns:
            Tuple[sqlite3.Connection, int]: The connection and its pool index
        """
        # Check if the current thread already has a connection
        if hasattr(self._local, 'connection') and hasattr(self._local, 'index'):
            return self._local.connection, self._local.index
        
        # Try to get a connection from the pool
        with self._pool_lock:
            # First, try to find an unused connection
            for i, conn in enumerate(self._pool):
                if not self._in_use.get(i, False):
                    self._in_use[i] = True
                    self._local.connection = conn
                    self._local.index = i
                    return conn, i
            
            # If no unused connection and pool is not full, create a new one
            if len(self._pool) < self.pool_size:
                conn = self._create_connection()
                index = len(self._pool)
                self._pool.append(conn)
                self._in_use[index] = True
                self._local.connection = conn
                self._local.index = index
                return conn, index
        
        # If we reach here, the pool is full and all connections are in use
        # Wait for a connection to become available
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            with self._pool_lock:
                for i, conn in enumerate(self._pool):
                    if not self._in_use.get(i, False):
                        self._in_use[i] = True
                        self._local.connection = conn
                        self._local.index = i
                        return conn, i
            
            # Wait a bit before trying again
            time.sleep(0.1)
        
        # If we reach here, we've timed out waiting for a connection
        raise TimeoutError(f"Timed out waiting for a database connection after {self.timeout} seconds")
    
    def _release_connection(self, index: int) -> None:
        """
        Release a connection back to the pool.
        
        Args:
            index: The index of the connection in the pool
        """
        with self._pool_lock:
            self._in_use[index] = False
        
        # Clear thread-local storage
        if hasattr(self._local, 'connection'):
            delattr(self._local, 'connection')
        if hasattr(self._local, 'index'):
            delattr(self._local, 'index')
    
    @contextmanager
    def connection(self):
        """
        Get a database connection from the pool using a context manager.
        
        Yields:
            sqlite3.Connection: A database connection
        """
        conn, index = self._get_connection()
        try:
            yield conn
        finally:
            self._release_connection(index)
    
    @contextmanager
    def transaction(self):
        """
        Execute a database transaction with automatic commit/rollback.
        
        Yields:
            sqlite3.Connection: A database connection with an active transaction
        """
        conn, index = self._get_connection()
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            logger.error(f"Transaction rolled back: {str(e)}")
            raise
        finally:
            self._release_connection(index)
    
    def execute(self, query: str, parameters: Union[Tuple, Dict] = ()) -> List[Dict[str, Any]]:
        """
        Execute a SQL query and return the results as a list of dictionaries.
        
        Args:
            query: SQL query to execute
            parameters: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        with self.connection() as conn:
            cursor = conn.execute(query, parameters)
            columns = [col[0] for col in cursor.description] if cursor.description else []
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def execute_update(self, query: str, parameters: Union[Tuple, Dict] = ()) -> int:
        """
        Execute a SQL update/insert/delete and return the number of affected rows.
        
        Args:
            query: SQL query to execute
            parameters: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        with self.transaction() as conn:
            cursor = conn.execute(query, parameters)
            return cursor.rowcount
    
    def execute_script(self, script: str) -> None:
        """
        Execute a SQL script.
        
        Args:
            script: SQL script to execute
        """
        with self.transaction() as conn:
            conn.executescript(script)
    
    def execute_batch(self, query: str, parameter_list: List[Union[Tuple, Dict]]) -> int:
        """
        Execute a batch of SQL queries with different parameters.
        
        Args:
            query: SQL query to execute
            parameter_list: List of query parameters
            
        Returns:
            int: Total number of affected rows
        """
        total_rowcount = 0
        with self.transaction() as conn:
            for parameters in parameter_list:
                cursor = conn.execute(query, parameters)
                total_rowcount += cursor.rowcount
        return total_rowcount
    
    def close_all(self) -> None:
        """Close all database connections in the pool."""
        with self._pool_lock:
            for conn in self._pool:
                try:
                    conn.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {str(e)}")
            self._pool = []
            self._in_use = {}
    
    def __del__(self) -> None:
        """Close all connections when the object is deleted."""
        self.close_all()

# Create a default database manager for the main log database
_log_db_manager = None

def get_log_db_manager() -> DatabaseManager:
    """Get the global log database manager instance."""
    global _log_db_manager
    if _log_db_manager is None:
        log_db_path = os.environ.get("NYX_LOG_DB", "logs/ai_logs.db")
        _log_db_manager = DatabaseManager(log_db_path)
    return _log_db_manager

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create a database manager
    db_manager = DatabaseManager("example.db")
    
    # Create a table
    db_manager.execute_script("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    """)
    
    # Insert data
    db_manager.execute_update(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        ("John Doe", "john@example.com")
    )
    
    # Query data
    users = db_manager.execute("SELECT * FROM users")
    for user in users:
        print(f"User: {user['name']}, Email: {user['email']}")
    
    # Use a transaction
    with db_manager.transaction() as conn:
        conn.execute("INSERT INTO users (name, email) VALUES (?, ?)", ("Jane Doe", "jane@example.com"))
        # This will be automatically committed if no exception occurs
    
    # Batch insert
    batch_data = [
        ("Alice Smith", "alice@example.com"),
        ("Bob Johnson", "bob@example.com"),
        ("Carol Williams", "carol@example.com")
    ]
    db_manager.execute_batch(
        "INSERT INTO users (name, email) VALUES (?, ?)",
        batch_data
    )
    
    # Clean up
    db_manager.close_all()
