# core/async_operations.py

"""
Asynchronous operations framework for I/O-bound and CPU-bound tasks.
Provides a consistent interface for executing operations asynchronously.
"""

import os
import asyncio
import threading
import concurrent.futures
import logging
import time
import functools
import inspect
from typing import Dict, Any, Optional, Callable, List, Union, Tuple, TypeVar, Awaitable

# Configure logging
logger = logging.getLogger("NYX-AsyncOperations")

# Type variables for generics
T = TypeVar('T')
R = TypeVar('R')

class AsyncOperationError(Exception):
    """Exception raised for errors in asynchronous operations."""
    pass

class AsyncOperationCancelled(AsyncOperationError):
    """Exception raised when an asynchronous operation is cancelled."""
    pass

class AsyncOperationTimeout(AsyncOperationError):
    """Exception raised when an asynchronous operation times out."""
    pass

class AsyncResult:
    """
    Result of an asynchronous operation.
    Provides a way to check if the operation is complete and get its result.
    """
    
    def __init__(self, future: concurrent.futures.Future = None,
                task: asyncio.Task = None, operation_id: str = None):
        """
        Initialize async result.
        
        Args:
            future: Concurrent future (for ThreadPoolExecutor)
            task: Asyncio task (for asyncio-based operations)
            operation_id: Unique ID for the operation
        """
        self.future = future
        self.task = task
        self.operation_id = operation_id
        self.start_time = time.time()
        self._callbacks = []
    
    def done(self) -> bool:
        """
        Check if the operation is complete.
        
        Returns:
            bool: True if the operation is complete, False otherwise
        """
        if self.future is not None:
            return self.future.done()
        if self.task is not None:
            return self.task.done()
        return False
    
    def cancel(self) -> bool:
        """
        Cancel the operation.
        
        Returns:
            bool: True if the operation was cancelled, False otherwise
        """
        if self.future is not None:
            return self.future.cancel()
        if self.task is not None:
            self.task.cancel()
            return True
        return False
    
    def result(self, timeout: Optional[float] = None) -> Any:
        """
        Get the result of the operation.
        
        Args:
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            Any: Result of the operation
            
        Raises:
            AsyncOperationCancelled: If the operation was cancelled
            AsyncOperationTimeout: If the operation timed out
            AsyncOperationError: If the operation failed
        """
        try:
            if self.future is not None:
                return self.future.result(timeout)
            if self.task is not None:
                if not self.task.done():
                    if timeout is not None:
                        try:
                            return asyncio.wait_for(self.task, timeout)
                        except asyncio.TimeoutError:
                            raise AsyncOperationTimeout(f"Operation timed out after {timeout} seconds")
                    else:
                        # This will block until the task is complete
                        loop = asyncio.get_event_loop()
                        return loop.run_until_complete(self.task)
                else:
                    # Task is already done
                    exception = self.task.exception()
                    if exception is not None:
                        raise AsyncOperationError(f"Operation failed: {str(exception)}") from exception
                    return self.task.result()
        except concurrent.futures.CancelledError:
            raise AsyncOperationCancelled("Operation was cancelled")
        except concurrent.futures.TimeoutError:
            raise AsyncOperationTimeout(f"Operation timed out after {timeout} seconds")
    
    def add_done_callback(self, callback: Callable[['AsyncResult'], None]) -> None:
        """
        Add a callback to be executed when the operation completes.
        
        Args:
            callback: Callback function to execute
        """
        self._callbacks.append(callback)
        
        def future_callback(future):
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in callback: {str(e)}")
        
        def task_callback(task):
            try:
                callback(self)
            except Exception as e:
                logger.error(f"Error in callback: {str(e)}")
        
        if self.future is not None:
            self.future.add_done_callback(future_callback)
        if self.task is not None:
            self.task.add_done_callback(task_callback)
    
    def elapsed_time(self) -> float:
        """
        Get the elapsed time since the operation started.
        
        Returns:
            float: Elapsed time in seconds
        """
        return time.time() - self.start_time
    
    def __str__(self) -> str:
        status = "done" if self.done() else "running"
        elapsed = self.elapsed_time()
        return f"AsyncResult(id={self.operation_id}, status={status}, elapsed={elapsed:.2f}s)"

class AsyncOperationManager:
    """
    Manager for asynchronous operations.
    Provides thread pools and task queues for executing operations asynchronously.
    """
    
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(AsyncOperationManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, max_workers: int = None, max_io_workers: int = None):
        """
        Initialize async operation manager.
        
        Args:
            max_workers: Maximum number of worker threads for CPU-bound tasks
            max_io_workers: Maximum number of worker threads for I/O-bound tasks
        """
        if self._initialized:
            return
            
        # Use number of processors for CPU-bound tasks
        if max_workers is None:
            max_workers = min(32, (os.cpu_count() or 1) + 4)
            
        # Use higher number for I/O-bound tasks
        if max_io_workers is None:
            max_io_workers = min(64, (os.cpu_count() or 1) * 4)
            
        # Create thread pools
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)
        self.io_executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_io_workers)
        
        # Track active operations
        self.operations = {}
        self.operation_counter = 0
        self.lock = threading.RLock()
        
        # Create asyncio event loop if needed
        self._event_loop = None
        
        self._initialized = True
        logger.info(f"AsyncOperationManager initialized with {max_workers} workers, {max_io_workers} I/O workers")
    
    def _get_operation_id(self) -> str:
        """
        Get a unique operation ID.
        
        Returns:
            str: Unique operation ID
        """
        with self.lock:
            self.operation_counter += 1
            return f"op-{self.operation_counter:08d}"
    
    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """
        Get or create an asyncio event loop.
        
        Returns:
            asyncio.AbstractEventLoop: Event loop
        """
        if self._event_loop is None:
            try:
                self._event_loop = asyncio.get_event_loop()
            except RuntimeError:
                # No event loop in this thread, create a new one
                self._event_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._event_loop)
        return self._event_loop
    
    def submit(self, func: Callable[..., T], *args, **kwargs) -> AsyncResult:
        """
        Submit a function for execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            AsyncResult: Async result for the operation
        """
        operation_id = self._get_operation_id()
        
        # If the function is a coroutine function, use asyncio
        if asyncio.iscoroutinefunction(func):
            loop = self._get_event_loop()
            coro = func(*args, **kwargs)
            task = loop.create_task(coro)
            result = AsyncResult(task=task, operation_id=operation_id)
        else:
            future = self.executor.submit(func, *args, **kwargs)
            result = AsyncResult(future=future, operation_id=operation_id)
        
        # Track the operation
        with self.lock:
            self.operations[operation_id] = result
            
        # Clean up when done
        def cleanup(result):
            with self.lock:
                if operation_id in self.operations:
                    del self.operations[operation_id]
        
        result.add_done_callback(cleanup)
        
        return result
    
    def submit_io(self, func: Callable[..., T], *args, **kwargs) -> AsyncResult:
        """
        Submit an I/O-bound function for execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            AsyncResult: Async result for the operation
        """
        operation_id = self._get_operation_id()
        
        # If the function is a coroutine function, use asyncio
        if asyncio.iscoroutinefunction(func):
            loop = self._get_event_loop()
            coro = func(*args, **kwargs)
            task = loop.create_task(coro)
            result = AsyncResult(task=task, operation_id=operation_id)
        else:
            future = self.io_executor.submit(func, *args, **kwargs)
            result = AsyncResult(future=future, operation_id=operation_id)
        
        # Track the operation
        with self.lock:
            self.operations[operation_id] = result
            
        # Clean up when done
        def cleanup(result):
            with self.lock:
                if operation_id in self.operations:
                    del self.operations[operation_id]
        
        result.add_done_callback(cleanup)
        
        return result
    
    def map(self, func: Callable[[T], R], items: List[T], 
           max_workers: Optional[int] = None) -> List[R]:
        """
        Map a function over a list of items.
        
        Args:
            func: Function to apply
            items: Items to process
            max_workers: Maximum number of worker threads (None for auto)
            
        Returns:
            List[R]: Results
        """
        if not items:
            return []
            
        if max_workers is None:
            max_workers = min(len(items), self.executor._max_workers)
            
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            return list(executor.map(func, items))
    
    def wait_for_operations(self, timeout: Optional[float] = None) -> Dict[str, AsyncResult]:
        """
        Wait for all operations to complete.
        
        Args:
            timeout: Timeout in seconds (None for no timeout)
            
        Returns:
            Dict[str, AsyncResult]: Completed operations
        """
        start_time = time.time()
        
        with self.lock:
            operations = list(self.operations.values())
            
        remaining = operations
        
        while remaining and (timeout is None or time.time() - start_time < timeout):
            remaining = [op for op in remaining if not op.done()]
            if remaining:
                time.sleep(0.1)
        
        with self.lock:
            return {op_id: op for op_id, op in self.operations.items() if op.done()}
    
    def cancel_all_operations(self) -> int:
        """
        Cancel all active operations.
        
        Returns:
            int: Number of operations cancelled
        """
        with self.lock:
            operations = list(self.operations.values())
            
        cancelled = 0
        for op in operations:
            if op.cancel():
                cancelled += 1
                
        return cancelled
    
    def get_active_count(self) -> int:
        """
        Get the number of active operations.
        
        Returns:
            int: Number of active operations
        """
        with self.lock:
            return len(self.operations)
    
    def shutdown(self, wait: bool = True) -> None:
        """
        Shut down the operation manager.
        
        Args:
            wait: Whether to wait for operations to complete
        """
        if wait:
            self.wait_for_operations()
        else:
            self.cancel_all_operations()
            
        self.executor.shutdown(wait=wait)
        self.io_executor.shutdown(wait=wait)
        
        if self._event_loop is not None and self._event_loop.is_running():
            self._event_loop.stop()

# Global operation manager instance
_operation_manager = None

def get_operation_manager(max_workers: int = None, max_io_workers: int = None) -> AsyncOperationManager:
    """
    Get the global operation manager.
    
    Args:
        max_workers: Maximum number of worker threads for CPU-bound tasks
        max_io_workers: Maximum number of worker threads for I/O-bound tasks
        
    Returns:
        AsyncOperationManager: Operation manager instance
    """
    global _operation_manager
    if _operation_manager is None:
        _operation_manager = AsyncOperationManager(max_workers, max_io_workers)
    return _operation_manager

def async_operation(func: Callable[..., T]) -> Callable[..., AsyncResult]:
    """
    Decorator to execute a function asynchronously.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_operation_manager()
        return manager.submit(func, *args, **kwargs)
    return wrapper

def async_io_operation(func: Callable[..., T]) -> Callable[..., AsyncResult]:
    """
    Decorator to execute an I/O-bound function asynchronously.
    
    Args:
        func: Function to decorate
        
    Returns:
        Callable: Decorated function
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        manager = get_operation_manager()
        return manager.submit_io(func, *args, **kwargs)
    return wrapper

def run_async(coroutine_or_future: Union[Awaitable[T], concurrent.futures.Future]) -> T:
    """
    Run a coroutine or future synchronously.
    
    Args:
        coroutine_or_future: Coroutine or future to run
        
    Returns:
        T: Result of the coroutine or future
    """
    if isinstance(coroutine_or_future, concurrent.futures.Future):
        return coroutine_or_future.result()
    
    if asyncio.iscoroutine(coroutine_or_future):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(coroutine_or_future)
        
    raise ValueError("Expected a coroutine or future")

async def async_map(func: Callable[[T], R], items: List[T], 
                  chunk_size: int = 100) -> List[R]:
    """
    Map a function over a list of items asynchronously.
    
    Args:
        func: Function to apply
        items: Items to process
        chunk_size: Size of chunks to process in parallel
        
    Returns:
        List[R]: Results
    """
    if not items:
        return []
        
    loop = asyncio.get_event_loop()
    
    # Process in chunks to avoid creating too many tasks
    chunks = [items[i:i+chunk_size] for i in range(0, len(items), chunk_size)]
    all_results = []
    
    for chunk in chunks:
        # Create tasks for the chunk
        tasks = [loop.run_in_executor(None, func, item) for item in chunk]
        # Wait for all tasks to complete
        results = await asyncio.gather(*tasks)
        all_results.extend(results)
        
    return all_results

# Example async file operations
async def async_read_file(file_path: str, encoding: str = 'utf-8') -> str:
    """
    Read a file asynchronously.
    
    Args:
        file_path: Path to the file
        encoding: File encoding
        
    Returns:
        str: File contents
    """
    loop = asyncio.get_event_loop()
    
    def _read_file():
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    
    return await loop.run_in_executor(None, _read_file)

async def async_write_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Write to a file asynchronously.
    
    Args:
        file_path: Path to the file
        content: Content to write
        encoding: File encoding
    """
    loop = asyncio.get_event_loop()
    
    def _write_file():
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
    
    await loop.run_in_executor(None, _write_file)

async def async_append_file(file_path: str, content: str, encoding: str = 'utf-8') -> None:
    """
    Append to a file asynchronously.
    
    Args:
        file_path: Path to the file
        content: Content to append
        encoding: File encoding
    """
    loop = asyncio.get_event_loop()
    
    def _append_file():
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, 'a', encoding=encoding) as f:
            f.write(content)
    
    await loop.run_in_executor(None, _append_file)

# Thread-safe lazy property
def lazy_property(fn):
    """
    Decorator for thread-safe lazy properties.
    
    Args:
        fn: Property getter function
        
    Returns:
        property: Lazy property
    """
    attr_name = '_lazy_' + fn.__name__
    
    @property
    def _lazy_property(self):
        if not hasattr(self, attr_name):
            with threading.RLock():
                if not hasattr(self, attr_name):
                    setattr(self, attr_name, fn(self))
        return getattr(self, attr_name)
