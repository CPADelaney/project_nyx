# core/database_performance.py

"""
Database performance optimizations for SQLite databases.
Implements query optimization, proper indexing, and performance monitoring.
"""

import os
import sqlite3
import time
import logging
from typing import List, Dict, Any, Tuple, Optional, Union
import threading
from functools import wraps

# Configure logging
logger = logging.getLogger("NYX-DatabasePerformance")

class QueryCache:
    """
    Simple in-memory cache for query results.
    Caches frequently executed queries to reduce database load.
    """
    
    def __init__(self, max_size: int = 100, ttl: int = 60):
        """
        Initialize the query cache.
        
        Args:
            max_size: Maximum number of cached queries
            ttl: Time-to-live in seconds for cached results
        """
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl
        self.lock = threading.RLock()
    
    def get(self, query: str, params: Tuple = None) -> Optional[Any]:
        """
        Get a cached query result.
        
        Args:
            query: The SQL query
            params: Query parameters
            
        Returns:
            Any: Cached result or None if not in cache
        """
        with self.lock:
            key = self._make_key(query, params)
            if key in self.cache:
                timestamp, result = self.cache[key]
                # Check if the result is still valid
                if time.time() - timestamp <= self.ttl:
                    return result
                # Remove expired result
                del self.cache[key]
        return None
    
    def set(self, query: str, params: Tuple = None, result: Any = None) -> None:
        """
        Cache a query result.
        
        Args:
            query: The SQL query
            params: Query parameters
            result: Query result
        """
        with self.lock:
            # Check if cache is full
            if len(self.cache) >= self.max_size:
                # Remove oldest entry
                oldest_key = min(self.cache.items(), key=lambda x: x[1][0])[0]
                del self.cache[oldest_key]
            
            key = self._make_key(query, params)
            self.cache[key] = (time.time(), result)
    
    def invalidate(self, table_name: str = None) -> None:
        """
        Invalidate cache entries for a specific table or all tables.
        
        Args:
            table_name: Name of the table to invalidate (None for all)
        """
        with self.lock:
            if table_name is None:
                self.cache.clear()
            else:
                # Remove entries that involve the specified table
                keys_to_remove = []
                for key in self.cache:
                    if table_name.lower() in key.lower():
                        keys_to_remove.append(key)
                
                for key in keys_to_remove:
                    del self.cache[key]
    
    def _make_key(self, query: str, params: Tuple = None) -> str:
        """
        Create a cache key from a query and parameters.
        
        Args:
            query: The SQL query
            params: Query parameters
            
        Returns:
            str: Cache key
        """
        return f"{query}:{str(params)}"

class QueryProfiler:
    """
    Profiles SQLite queries to identify slow queries and optimization opportunities.
    """
    
    def __init__(self, threshold_ms: float = 100.0):
        """
        Initialize the query profiler.
        
        Args:
            threshold_ms: Threshold in milliseconds for slow queries
        """
        self.query_stats = {}
        self.threshold_ms = threshold_ms
        self.lock = threading.RLock()
    
    def start_query(self, query: str, params: Tuple = None) -> int:
        """
        Start timing a query.
        
        Args:
            query: The SQL query
            params: Query parameters
            
        Returns:
            int: Query ID for stopping the timer
        """
        query_id = id(query) + id(str(params))
        with self.lock:
            self.query_stats[query_id] = {
                'query': query,
                'params': params,
                'start_time': time.time(),
                'end_time': None,
                'duration_ms': None
            }
        return query_id
    
    def stop_query(self, query_id: int) -> float:
        """
        Stop timing a query and record its duration.
        
        Args:
            query_id: Query ID from start_query
            
        Returns:
            float: Query duration in milliseconds
        """
        with self.lock:
            if query_id in self.query_stats:
                stats = self.query_stats[query_id]
                stats['end_time'] = time.time()
                stats['duration_ms'] = (stats['end_time'] - stats['start_time']) * 1000
                
                # Log slow queries
                if stats['duration_ms'] > self.threshold_ms:
                    logger.warning(f"Slow query detected ({stats['duration_ms']:.2f}ms): {stats['query']}")
                    
                return stats['duration_ms']
        return 0.0
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Get a list of slow queries.
        
        Returns:
            List[Dict[str, Any]]: List of slow query stats
        """
        with self.lock:
            return [
                stats for stats in self.query_stats.values()
                if stats['duration_ms'] is not None and stats['duration_ms'] > self.threshold_ms
            ]
    
    def get_query_stats(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """
        Get statistics for the slowest queries.
        
        Args:
            top_n: Number of queries to return
            
        Returns:
            List[Dict[str, Any]]: List of query stats
        """
        with self.lock:
            # Filter completed queries
            completed = [
                stats for stats in self.query_stats.values()
                if stats['duration_ms'] is not None
            ]
            
            # Sort by duration (slowest first)
            sorted_stats = sorted(completed, key=lambda x: x['duration_ms'], reverse=True)
            
            return sorted_stats[:top_n]
    
    def clear_stats(self) -> None:
        """Clear all query statistics."""
        with self.lock:
            self.query_stats.clear()

def profile_query(func):
    """
    Decorator to profile a database query function.
    
    Args:
        func: Function to decorate
        
    Returns:
        wrapper: Decorated function
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Extract query and params from args/kwargs
        query = args[1] if len(args) > 1 else kwargs.get('query')
        params = args[2] if len(args) > 2 else kwargs.get('params')
        
        profiler = args[0].profiler if hasattr(args[0], 'profiler') else None
        query_id = None
        
        if profiler is not None and query is not None:
            query_id = profiler.start_query(query, params)
            
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            if profiler is not None and query_id is not None:
                profiler.stop_query(query_id)
    
    return wrapper

class OptimizedDatabaseManager:
    """
    Enhanced database manager with performance optimizations.
    Extends the base DatabaseManager with query caching and profiling.
    """
    
    def __init__(self, db_path: str, cache_enabled: bool = True, profile_enabled: bool = True,
                 max_cache_size: int = 200, cache_ttl: int = 300):
        """
        Initialize the optimized database manager.
        
        Args:
            db_path: Path to the SQLite database
            cache_enabled: Whether to enable query caching
            profile_enabled: Whether to enable query profiling
            max_cache_size: Maximum size of the query cache
            cache_ttl: Time-to-live for cached results in seconds
        """
        # Initialize from parent class
        self.db_path = db_path
        
        # Create cache and profiler if enabled
        self.cache = QueryCache(max_cache_size, cache_ttl) if cache_enabled else None
        self.profiler = QueryProfiler() if profile_enabled else None
        
        # Initialize database
        conn = self._get_connection()
        
        # Enable WAL mode for better concurrency
        conn.execute("PRAGMA journal_mode=WAL")
        
        # Enable foreign keys
        conn.execute("PRAGMA foreign_keys=ON")
        
        # Set reasonable timeouts and cache size
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA cache_size=-10000")  # Negative means size in KB, not pages
        
        # Close connection
        conn.close()
    
    def _get_connection(self) -> sqlite3.Connection:
        """
        Get a database connection.
        
        Returns:
            sqlite3.Connection: Database connection
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def analyze_database(self) -> Dict[str, Any]:
        """
        Analyze the database for optimization opportunities.
        
        Returns:
            Dict[str, Any]: Analysis results
        """
        conn = self._get_connection()
        try:
            results = {
                'tables': {},
                'indexes': [],
                'potential_indexes': [],
                'stats': {}
            }
            
            # Get table list
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            # Get statistics for each table
            for table in tables:
                # Number of rows
                cursor = conn.execute(f"SELECT COUNT(*) FROM '{table}'")
                row_count = cursor.fetchone()[0]
                
                # Table info
                cursor = conn.execute(f"PRAGMA table_info('{table}')")
                columns = [
                    {
                        'name': row[1],
                        'type': row[2],
                        'notnull': row[3],
                        'pk': row[4]
                    }
                    for row in cursor.fetchall()
                ]
                
                # Index list
                cursor = conn.execute(f"PRAGMA index_list('{table}')")
                indexes = [
                    {
                        'name': row[1],
                        'unique': row[2]
                    }
                    for row in cursor.fetchall()
                ]
                
                for idx in indexes:
                    cursor = conn.execute(f"PRAGMA index_info('{idx['name']}')")
                    idx_info = cursor.fetchall()
                    idx['columns'] = [row[2] for row in idx_info]
                    results['indexes'].append(idx)
                
                # Store table info
                results['tables'][table] = {
                    'row_count': row_count,
                    'columns': columns,
                    'indexes': indexes
                }
                
                # Identify potential missing indexes
                # For columns used in WHERE clauses, but not indexed
                if row_count > 1000:  # Only suggest indexes for larger tables
                    query = f"""
                        SELECT 0 AS dummy
                        FROM sqlite_master
                        WHERE type='trigger'
                        AND sql LIKE '%FROM {table} WHERE%'
                    """
                    cursor = conn.execute(query)
                    if cursor.fetchone():
                        # Has triggers that filter on this table
                        for col in columns:
                            # Check if column is indexed
                            is_indexed = False
                            for idx in indexes:
                                if col['name'] in idx['columns']:
                                    is_indexed = True
                                    break
                            
                            # Suggest index if not already indexed and not the primary key
                            if not is_indexed and not col['pk']:
                                results['potential_indexes'].append({
                                    'table': table,
                                    'column': col['name'],
                                    'reason': 'Used in WHERE clauses'
                                })
            
            # Get database stats
            cursor = conn.execute("PRAGMA database_list")
            db_info = cursor.fetchall()
            results['stats']['database_files'] = [
                {
                    'seq': row[0],
                    'name': row[1],
                    'file': row[2]
                }
                for row in db_info
            ]
            
            cursor = conn.execute("PRAGMA journal_mode")
            results['stats']['journal_mode'] = cursor.fetchone()[0]
            
            cursor = conn.execute("PRAGMA cache_size")
            results['stats']['cache_size'] = cursor.fetchone()[0]
            
            return results
        finally:
            conn.close()
    
    def optimize_database(self) -> Dict[str, Any]:
        """
        Optimize the database based on analysis results.
        
        Returns:
            Dict[str, Any]: Optimization results
        """
        conn = self._get_connection()
        try:
            results = {
                'vacuum': False,
                'analyze': False,
                'indexes_added': [],
                'error': None
            }
            
            # Run analysis
            analysis = self.analyze_database()
            
            # Create suggested indexes
            for idx_suggestion in analysis['potential_indexes']:
                table = idx_suggestion['table']
                column = idx_suggestion['column']
                idx_name = f"idx_{table}_{column}"
                
                try:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table}({column})")
                    results['indexes_added'].append(idx_name)
                except sqlite3.Error as e:
                    logger.error(f"Error creating index {idx_name}: {str(e)}")
            
            # Run ANALYZE to gather statistics
            try:
                conn.execute("ANALYZE")
                results['analyze'] = True
            except sqlite3.Error as e:
                logger.error(f"Error running ANALYZE: {str(e)}")
            
            # Run VACUUM to defragment the database
            try:
                conn.execute("VACUUM")
                results['vacuum'] = True
            except sqlite3.Error as e:
                logger.error(f"Error running VACUUM: {str(e)}")
            
            conn.commit()
            return results
        except sqlite3.Error as e:
            conn.rollback()
            results['error'] = str(e)
            return results
        finally:
            conn.close()
    
    @profile_query
    def execute_query(self, query: str, params: Union[Tuple, Dict] = ()) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query with caching.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List[Dict[str, Any]]: Query results
        """
        # Check if the query is a SELECT query
        is_select = query.strip().upper().startswith("SELECT")
        
        # Try to get from cache for SELECT queries
        if is_select and self.cache is not None:
            cached_result = self.cache.get(query, params)
            if cached_result is not None:
                return cached_result
        
        # Execute the query
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            if cursor.description:
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
                # Cache the result for SELECT queries
                if is_select and self.cache is not None:
                    self.cache.set(query, params, results)
                
                return results
            return []
        finally:
            conn.close()
    
    @profile_query
    def execute_update(self, query: str, params: Union[Tuple, Dict] = ()) -> int:
        """
        Execute an UPDATE/INSERT/DELETE query.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            int: Number of affected rows
        """
        conn = self._get_connection()
        try:
            cursor = conn.execute(query, params)
            conn.commit()
            
            # Invalidate cache based on affected table
            if self.cache is not None:
                # Extract table name from query
                words = query.strip().split()
                if len(words) > 1:
                    table_name = words[1] if words[0].upper() in ("UPDATE", "INSERT", "DELETE") else None
                    if table_name:
                        self.cache.invalidate(table_name)
            
            return cursor.rowcount
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    @profile_query
    def execute_batch(self, query: str, params_list: List[Union[Tuple, Dict]]) -> int:
        """
        Execute a batch of queries.
        
        Args:
            query: SQL query
            params_list: List of query parameters
            
        Returns:
            int: Number of affected rows
        """
        conn = self._get_connection()
        try:
            total_rows = 0
            cursor = conn.cursor()
            
            # Use executemany for better performance
            cursor.executemany(query, params_list)
            total_rows = cursor.rowcount
            
            conn.commit()
            
            # Invalidate cache based on affected table
            if self.cache is not None:
                # Extract table name from query
                words = query.strip().split()
                if len(words) > 1:
                    table_name = words[1] if words[0].upper() in ("UPDATE", "INSERT", "DELETE") else None
                    if table_name:
                        self.cache.invalidate(table_name)
            
            return total_rows
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def create_indexes(self, table_name: str, columns: List[str]) -> List[str]:
        """
        Create indexes for a table.
        
        Args:
            table_name: Name of the table
            columns: List of columns to index
            
        Returns:
            List[str]: List of created index names
        """
        conn = self._get_connection()
        try:
            created_indexes = []
            
            for column in columns:
                index_name = f"idx_{table_name}_{column}"
                
                try:
                    conn.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column})")
                    created_indexes.append(index_name)
                except sqlite3.Error as e:
                    logger.error(f"Error creating index {index_name}: {str(e)}")
            
            conn.commit()
            return created_indexes
        except sqlite3.Error:
            conn.rollback()
            raise
        finally:
            conn.close()
    
    def get_profiling_stats(self) -> List[Dict[str, Any]]:
        """
        Get query profiling statistics.
        
        Returns:
            List[Dict[str, Any]]: Query statistics
        """
        if self.profiler is not None:
            return self.profiler.get_query_stats()
        return []
    
    def get_slow_queries(self) -> List[Dict[str, Any]]:
        """
        Get slow queries.
        
        Returns:
            List[Dict[str, Any]]: Slow query statistics
        """
        if self.profiler is not None:
            return self.profiler.get_slow_queries()
        return []
    
    def clear_cache(self) -> None:
        """Clear the query cache."""
        if self.cache is not None:
            self.cache.invalidate()
    
    def clear_stats(self) -> None:
        """Clear query statistics."""
        if self.profiler is not None:
            self.profiler.clear_stats()

# Example usage
if __name__ == "__main__":
    db_path = "example.db"
    
    # Create an optimized database manager
    db_manager = OptimizedDatabaseManager(db_path)
    
    # Analyze the database
    analysis = db_manager.analyze_database()
    print(f"Tables: {list(analysis['tables'].keys())}")
    print(f"Indexes: {analysis['indexes']}")
    print(f"Potential indexes: {analysis['potential_indexes']}")
    
    # Optimize the database
    result = db_manager.optimize_database()
    print(f"Optimization result: {result}")
    
    # Execute a query
    users = db_manager.execute_query("SELECT * FROM users WHERE name LIKE ?", ("%John%",))
    print(f"Users: {users}")
    
    # Get query stats
    stats = db_manager.get_profiling_stats()
    print(f"Query stats: {stats}")
