# core/resource_limiter.py

"""
Resource limiter and rate throttling for resource-intensive operations.
Provides mechanisms to control CPU, memory, and I/O usage to prevent system overload.
"""

import os
import time
import threading
import logging
import psutil
from typing import Dict, Any, Optional, Callable, List, Union, Tuple
from functools import wraps
from datetime import datetime, timedelta
import signal
import resource

# Configure logging
logger = logging.getLogger("NYX-ResourceLimiter")

class ResourceLimit:
    """Resource limit configuration."""
    
    def __init__(self, cpu_percent: float = 80.0, memory_mb: int = 1024,
                 file_descriptors: int = 1000, execution_time_s: float = 300.0):
        """
        Initialize resource limits.
        
        Args:
            cpu_percent: Maximum CPU usage percentage
            memory_mb: Maximum memory usage in MB
            file_descriptors: Maximum number of open file descriptors
            execution_time_s: Maximum execution time in seconds
        """
        self.cpu_percent = cpu_percent
        self.memory_mb = memory_mb
        self.file_descriptors = file_descriptors
        self.execution_time_s = execution_time_s
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'cpu_percent': self.cpu_percent,
            'memory_mb': self.memory_mb,
            'file_descriptors': self.file_descriptors,
            'execution_time_s': self.execution_time_s
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ResourceLimit':
        """Create from dictionary."""
        return cls(
            cpu_percent=data.get('cpu_percent', 80.0),
            memory_mb=data.get('memory_mb', 1024),
            file_descriptors=data.get('file_descriptors', 1000),
            execution_time_s=data.get('execution_time_s', 300.0)
        )

class RateLimiter:
    """
    Rate limiter for controlling request frequency.
    Implements token bucket algorithm for flexible rate limiting.
    """
    
    def __init__(self, rate: float, burst: int = 1):
        """
        Initialize rate limiter.
        
        Args:
            rate: Rate of tokens per second
            burst: Maximum token bucket size
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_refill = time.time()
        self.lock = threading.RLock()
    
    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.rate
        self.tokens = min(self.burst, self.tokens + new_tokens)
        self.last_refill = now
    
    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            block: Whether to block until tokens are available
            
        Returns:
            bool: True if tokens were acquired, False otherwise
        """
        with self.lock:
            self._refill_tokens()
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            if not block:
                return False
            
            # Calculate time to wait for enough tokens
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            
            # Sleep until we have enough tokens
            time.sleep(wait_time)
            
            # Refill tokens and acquire
            self._refill_tokens()
            self.tokens -= tokens
            return True

class CPUThrottler:
    """
    Throttles CPU-intensive operations to maintain system responsiveness.
    """
    
    def __init__(self, target_percent: float = 70.0, check_interval: float = 0.1):
        """
        Initialize CPU throttler.
        
        Args:
            target_percent: Target CPU usage percentage
            check_interval: Interval in seconds to check CPU usage
        """
        self.target_percent = target_percent
        self.check_interval = check_interval
        self.process = psutil.Process(os.getpid())
    
    def throttle(self) -> None:
        """
        Throttle CPU usage if it exceeds the target.
        This method should be called periodically during CPU-intensive operations.
        """
        cpu_percent = self.process.cpu_percent(interval=self.check_interval)
        
        if cpu_percent > self.target_percent:
            # Calculate sleep time based on how much we're over the target
            over_percent = (cpu_percent - self.target_percent) / 100.0
            sleep_time = over_percent * self.check_interval
            time.sleep(sleep_time)

class MemoryLimiter:
    """
    Limits memory usage of the current process.
    """
    
    def __init__(self, max_memory_mb: int = 1024):
        """
        Initialize memory limiter.
        
        Args:
            max_memory_mb: Maximum memory usage in MB
        """
        self.max_memory_mb = max_memory_mb
        self.process = psutil.Process(os.getpid())
    
    def limit_memory(self) -> None:
        """Apply memory limits using the resource module."""
        # Set soft and hard limits for memory usage
        max_bytes = self.max_memory_mb * 1024 * 1024
        
        try:
            resource.setrlimit(resource.RLIMIT_AS, (max_bytes, max_bytes))
            logger.info(f"Set memory limit to {self.max_memory_mb} MB")
        except (ValueError, resource.error) as e:
            logger.error(f"Failed to set memory limit: {str(e)}")
    
    def check_memory_usage(self) -> Tuple[bool, float]:
        """
        Check current memory usage against the limit.
        
        Returns:
            Tuple[bool, float]: (within limit, current usage in MB)
        """
        memory_info = self.process.memory_info()
        usage_mb = memory_info.rss / (1024 * 1024)
        
        return usage_mb <= self.max_memory_mb, usage_mb

class IOThrottler:
    """
    Throttles I/O operations to prevent excessive disk usage.
    """
    
    def __init__(self, max_ops_per_second: float = 100.0):
        """
        Initialize I/O throttler.
        
        Args:
            max_ops_per_second: Maximum I/O operations per second
        """
        self.rate_limiter = RateLimiter(max_ops_per_second)
    
    def throttle_io(self, cost: float = 1.0) -> None:
        """
        Throttle I/O operations.
        
        Args:
            cost: Cost of the operation (higher for more intensive operations)
        """
        self.rate_limiter.acquire(cost)

class TimeoutGuard:
    """
    Guard against long-running operations with timeout.
    """
    
    def __init__(self, timeout_seconds: float):
        """
        Initialize timeout guard.
        
        Args:
            timeout_seconds: Timeout in seconds
        """
        self.timeout_seconds = timeout_seconds
        self.timeout_occurred = False
    
    def _timeout_handler(self, signum, frame):
        """Signal handler for timeout."""
        self.timeout_occurred = True
        raise TimeoutError(f"Operation timed out after {self.timeout_seconds} seconds")
    
    def __enter__(self):
        """Set up the timeout handler."""
        self.timeout_occurred = False
        self.old_handler = signal.signal(signal.SIGALRM, self._timeout_handler)
        signal.alarm(int(self.timeout_seconds))
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Clean up the timeout handler."""
        signal.alarm(0)
        signal.signal(signal.SIGALRM, self.old_handler)
        return exc_type is TimeoutError and self.timeout_occurred

class ResourceLimiter:
    """
    Main resource limiter that combines various limiting strategies.
    """
    
    def __init__(self, limits: Optional[ResourceLimit] = None):
        """
        Initialize resource limiter.
        
        Args:
            limits: Resource limits (if None, use defaults)
        """
        self.limits = limits or ResourceLimit()
        self.cpu_throttler = CPUThrottler(self.limits.cpu_percent)
        self.memory_limiter = MemoryLimiter(self.limits.memory_mb)
        self.io_throttler = IOThrottler()
    
    def throttle_cpu(self) -> None:
        """Throttle CPU usage."""
        self.cpu_throttler.throttle()
    
    def throttle_io(self, cost: float = 1.0) -> None:
        """Throttle I/O operations."""
        self.io_throttler.throttle_io(cost)
    
    def limit_memory(self) -> None:
        """Apply memory limits."""
        self.memory_limiter.limit_memory()
    
    def apply_resource_limits(self) -> None:
        """Apply all resource limits."""
        self.limit_memory()
        
        # Set file descriptor limit
        try:
            resource.setrlimit(resource.RLIMIT_NOFILE, 
                              (self.limits.file_descriptors, self.limits.file_descriptors))
            logger.info(f"Set file descriptor limit to {self.limits.file_descriptors}")
        except (ValueError, resource.error) as e:
            logger.error(f"Failed to set file descriptor limit: {str(e)}")
    
    def guard_operation(self, operation: Callable, *args, **kwargs) -> Any:
        """
        Guard an operation with resource limits and timeout.
        
        Args:
            operation: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Any: Result of the operation
            
        Raises:
            TimeoutError: If the operation times out
        """
        # Apply resource limits
        self.apply_resource_limits()
        
        # Execute with timeout guard
        with TimeoutGuard(self.limits.execution_time_s):
            result = operation(*args, **kwargs)
            
        return result


# Decorator for limiting resource usage
def limit_resources(cpu_percent: float = 80.0, memory_mb: int = 1024,
                   file_descriptors: int = 1000, execution_time_s: float = 300.0):
    """
    Decorator to limit resource usage of a function.
    
    Args:
        cpu_percent: Maximum CPU usage percentage
        memory_mb: Maximum memory usage in MB
        file_descriptors: Maximum number of open file descriptors
        execution_time_s: Maximum execution time in seconds
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limits = ResourceLimit(cpu_percent, memory_mb, file_descriptors, execution_time_s)
            limiter = ResourceLimiter(limits)
            
            return limiter.guard_operation(func, *args, **kwargs)
        return wrapper
    return decorator

# Decorator for rate limiting
def rate_limit(rate: float, burst: int = 1):
    """
    Decorator to apply rate limiting to a function.
    
    Args:
        rate: Rate of calls per second
        burst: Maximum burst size
        
    Returns:
        Callable: Decorated function
    """
    limiter = RateLimiter(rate, burst)
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter.acquire()
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Decorator for throttling CPU usage
def throttle_cpu(target_percent: float = 70.0, check_interval: float = 0.1):
    """
    Decorator to throttle CPU usage during function execution.
    
    Args:
        target_percent: Target CPU usage percentage
        check_interval: Interval in seconds to check CPU usage
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            throttler = CPUThrottler(target_percent, check_interval)
            result = func(*args, **kwargs)
            throttler.throttle()
            return result
        return wrapper
    return decorator

# Background resource monitor
class ResourceMonitor:
    """
    Background thread that monitors resource usage and applies throttling.
    """
    
    def __init__(self, check_interval: float = 1.0, 
                cpu_limit: float = 80.0, memory_limit_mb: int = 1024):
        """
        Initialize resource monitor.
        
        Args:
            check_interval: Interval in seconds to check resource usage
            cpu_limit: CPU usage limit percentage
            memory_limit_mb: Memory usage limit in MB
        """
        self.check_interval = check_interval
        self.cpu_limit = cpu_limit
        self.memory_limit_mb = memory_limit_mb
        self.running = False
        self.monitor_thread = None
        self.process = psutil.Process(os.getpid())
        self.usage_history = []
        self.alerts = []
    
    def start(self) -> None:
        """Start the monitor thread."""
        if self.running:
            logger.warning("Resource monitor is already running")
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Resource monitor started")
    
    def stop(self) -> None:
        """Stop the monitor thread."""
        if not self.running:
            logger.warning("Resource monitor is not running")
            return
            
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Resource monitor stopped")
    
    def _monitor_loop(self) -> None:
        """Main monitoring loop."""
        while self.running:
            try:
                # Get CPU and memory usage
                cpu_percent = self.process.cpu_percent(interval=0.1)
                memory_info = self.process.memory_info()
                memory_mb = memory_info.rss / (1024 * 1024)
                
                # Record usage
                timestamp = datetime.now()
                usage = {
                    'timestamp': timestamp,
                    'cpu_percent': cpu_percent,
                    'memory_mb': memory_mb
                }
                self.usage_history.append(usage)
                
                # Trim history to keep only the last 60 records
                if len(self.usage_history) > 60:
                    self.usage_history = self.usage_history[-60:]
                
                # Check for high usage
                if cpu_percent > self.cpu_limit:
                    alert = {
                        'timestamp': timestamp,
                        'type': 'high_cpu',
                        'value': cpu_percent,
                        'limit': self.cpu_limit,
                        'message': f"High CPU usage: {cpu_percent:.1f}% (limit: {self.cpu_limit:.1f}%)"
                    }
                    self.alerts.append(alert)
                    logger.warning(alert['message'])
                    
                    # Apply throttling - sleep proportionally to the excess
                    excess = (cpu_percent - self.cpu_limit) / 100.0
                    sleep_time = excess * self.check_interval
                    time.sleep(sleep_time)
                
                if memory_mb > self.memory_limit_mb:
                    alert = {
                        'timestamp': timestamp,
                        'type': 'high_memory',
                        'value': memory_mb,
                        'limit': self.memory_limit_mb,
                        'message': f"High memory usage: {memory_mb:.1f} MB (limit: {self.memory_limit_mb:.1f} MB)"
                    }
                    self.alerts.append(alert)
                    logger.warning(alert['message'])
                    
                    # For memory, we can't really throttle, but we can trigger GC
                    import gc
                    gc.collect()
                
                # Trim alerts to keep only the last 100
                if len(self.alerts) > 100:
                    self.alerts = self.alerts[-100:]
                
                # Sleep until next check
                time.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in resource monitor: {str(e)}")
                time.sleep(self.check_interval * 2)  # Sleep longer after error
    
    def get_usage_history(self) -> List[Dict[str, Any]]:
        """
        Get resource usage history.
        
        Returns:
            List[Dict[str, Any]]: Usage history
        """
        return self.usage_history.copy()
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """
        Get resource alerts.
        
        Returns:
            List[Dict[str, Any]]: Alerts
        """
        return self.alerts.copy()
    
    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.
        
        Returns:
            Dict[str, Any]: Current usage
        """
        cpu_percent = self.process.cpu_percent(interval=0.1)
        memory_info = self.process.memory_info()
        memory_mb = memory_info.rss / (1024 * 1024)
        
        return {
            'timestamp': datetime.now(),
            'cpu_percent': cpu_percent,
            'memory_mb': memory_mb
        }

# Global resource monitor instance
_resource_monitor = None

def get_resource_monitor(check_interval: float = 1.0, 
                        cpu_limit: float = 80.0, 
                        memory_limit_mb: int = 1024) -> ResourceMonitor:
    """
    Get or create the global resource monitor.
    
    Args:
        check_interval: Interval in seconds to check resource usage
        cpu_limit: CPU usage limit percentage
        memory_limit_mb: Memory usage limit in MB
        
    Returns:
        ResourceMonitor: Resource monitor instance
    """
    global _resource_monitor
    if _resource_monitor is None:
        _resource_monitor = ResourceMonitor(check_interval, cpu_limit, memory_limit_mb)
    return _resource_monitor

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Start the resource monitor
    monitor = get_resource_monitor()
    monitor.start()
    
    # Example of a resource-intensive function with limits
    @limit_resources(cpu_percent=50.0, memory_mb=100, execution_time_s=10.0)
    def intensive_calculation(n):
        """Do some intensive calculation."""
        result = 0
        for i in range(n):
            result += i ** 2
        return result
    
    # Example of a rate-limited function
    @rate_limit(rate=2.0, burst=3)
    def api_call(endpoint):
        """Simulated API call."""
        logger.info(f"Calling API endpoint: {endpoint}")
        time.sleep(0.1)  # Simulate API call
        return f"Result from {endpoint}"
    
    # Example of a CPU-throttled function
    @throttle_cpu(target_percent=30.0)
    def compute_matrix(size):
        """Compute a matrix operation."""
        import numpy as np
        matrix = np.random.rand(size, size)
        result = np.matmul(matrix, matrix)
        return result.mean()
    
    try:
        # Test the resource-limited function
        logger.info("Testing resource-limited function...")
        result = intensive_calculation(1000000)
        logger.info(f"Result: {result}")
        
        # Test the rate-limited function
        logger.info("Testing rate-limited function...")
        for i in range(10):
            result = api_call(f"endpoint_{i}")
            logger.info(f"Result: {result}")
        
        # Test the CPU-throttled function
        logger.info("Testing CPU-throttled function...")
        result = compute_matrix(1000)
        logger.info(f"Result: {result}")
        
        # Print resource usage and alerts
        logger.info("Resource usage history:")
        for usage in monitor.get_usage_history():
            logger.info(f"Time: {usage['timestamp']}, CPU: {usage['cpu_percent']:.1f}%, Memory: {usage['memory_mb']:.1f} MB")
        
        logger.info("Resource alerts:")
        for alert in monitor.get_alerts():
            logger.info(f"Time: {alert['timestamp']}, Type: {alert['type']}, Message: {alert['message']}")
        
    finally:
        # Stop the resource monitor
        monitor.stop()
