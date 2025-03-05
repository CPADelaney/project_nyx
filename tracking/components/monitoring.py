# tracking/components/monitoring.py

"""
Monitoring component that consolidates performance tracking and bottleneck detection
functionality from various tracking modules.
"""

import os
import time
import psutil
import logging
import subprocess
import cProfile
import pstats
from io import StringIO
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from core.error_framework import safe_execute, ValidationError
from core.secure_subprocess import run

# Configure logging
logger = logging.getLogger("NYX-Monitoring")

class MonitoringComponent:
    """
    Monitors system performance, detects bottlenecks, and tracks resource usage.
    Consolidates functionality from:
    - performance_tracker.py
    - bottleneck_detector.py
    """
    
    def __init__(self, tracking_system):
        """
        Initialize the monitoring component.
        
        Args:
            tracking_system: The parent tracking system
        """
        self.tracking_system = tracking_system
        self.db_manager = tracking_system.db_manager
        self.threshold_percent = 5  # Only optimize if function runs 5% slower than baseline
        self.target_file = "src/nyx_core.py"  # Default target file
        self.metrics = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "execution_time": []
        }
        self.bottlenecks = []
        
        logger.info("Monitoring component initialized")
    
    @safe_execute
    def monitor(self) -> Dict[str, Any]:
        """
        Run all monitoring checks.
        
        Returns:
            Dict: Results of the monitoring checks
        """
        results = {
            "resource_metrics": self.collect_resource_metrics(),
            "execution_time": self.measure_execution_time(),
            "bottlenecks": self.detect_bottlenecks()
        }
        
        self.tracking_system.log_event(
            "monitoring", 
            "monitor_executed", 
            f"Run complete: {len(self.bottlenecks)} bottlenecks detected"
        )
        
        return results
    
    @safe_execute
    def collect_resource_metrics(self) -> Dict[str, Any]:
        """
        Collect system resource metrics.
        
        Returns:
            Dict: Resource metrics
        """
        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        
        # Get memory usage
        memory = psutil.virtual_memory()
        
        # Get disk usage
        disk = psutil.disk_usage('/')
        
        # Record metrics
        timestamp = datetime.now().isoformat()
        
        cpu_metric = {
            "timestamp": timestamp,
            "value": cpu_percent,
            "units": "percent"
        }
        
        memory_metric = {
            "timestamp": timestamp,
            "value": memory.percent,
            "used_bytes": memory.used,
            "total_bytes": memory.total,
            "units": "percent"
        }
        
        disk_metric = {
            "timestamp": timestamp,
            "value": disk.percent,
            "used_bytes": disk.used,
            "total_bytes": disk.total,
            "units": "percent"
        }
        
        # Store in metrics history
        self.metrics["cpu"].append(cpu_metric)
        self.metrics["memory"].append(memory_metric)
        self.metrics["disk"].append(disk_metric)
        
        # Trim metrics history (keep only the last 100 entries)
        for key in self.metrics:
            if len(self.metrics[key]) > 100:
                self.metrics[key] = self.metrics[key][-100:]
        
        # Log metrics to database
        self.db_manager.execute_update(
            "INSERT INTO performance_metrics (metric_name, metric_value, units) VALUES (?, ?, ?)",
            ("cpu_usage", cpu_percent, "percent")
        )
        
        self.db_manager.execute_update(
            "INSERT INTO performance_metrics (metric_name, metric_value, units) VALUES (?, ?, ?)",
            ("memory_usage", memory.percent, "percent")
        )
        
        self.db_manager.execute_update(
            "INSERT INTO performance_metrics (metric_name, metric_value, units) VALUES (?, ?, ?)",
            ("disk_usage", disk.percent, "percent")
        )
        
        # Log event if resource usage is high
        if cpu_percent > 80:
            self.tracking_system.log_event(
                "monitoring", 
                "high_cpu_usage", 
                f"CPU usage is {cpu_percent}%", 
                "warning"
            )
            
        if memory.percent > 80:
            self.tracking_system.log_event(
                "monitoring", 
                "high_memory_usage", 
                f"Memory usage is {memory.percent}%", 
                "warning"
            )
            
        if disk.percent > 85:
            self.tracking_system.log_event(
                "monitoring", 
                "high_disk_usage", 
                f"Disk usage is {disk.percent}%", 
                "warning"
            )
        
        return {
            "cpu": cpu_metric,
            "memory": memory_metric,
            "disk": disk_metric
        }
    
    @safe_execute
    def measure_execution_time(self) -> Dict[str, Any]:
        """
        Measure execution time of the target file.
        
        Returns:
            Dict: Execution time results
        """
        if not os.path.exists(self.target_file):
            return {"success": False, "message": f"Target file {self.target_file} not found"}
            
        start_time = time.time()
        
        try:
            # Use secure subprocess to run the target file
            result = run(["python3", self.target_file], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Target file execution failed: {result.stderr}")
                return {"success": False, "message": "Execution failed", "stderr": result.stderr}
        except Exception as e:
            logger.error(f"Error executing target file: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
        
        execution_time = time.time() - start_time
        
        # Record execution time
        timestamp = datetime.now().isoformat()
        time_metric = {
            "timestamp": timestamp,
            "value": execution_time,
            "units": "seconds"
        }
        
        self.metrics["execution_time"].append(time_metric)
        
        # Trim execution time history
        if len(self.metrics["execution_time"]) > 100:
            self.metrics["execution_time"] = self.metrics["execution_time"][-100:]
        
        # Log execution time to database
        self.db_manager.execute_update(
            "INSERT INTO performance_metrics (metric_name, metric_value, units) VALUES (?, ?, ?)",
            ("execution_time", execution_time, "seconds")
        )
        
        # Log event for slow execution
        if len(self.metrics["execution_time"]) > 1:
            prev_time = self.metrics["execution_time"][-2]["value"]
            if execution_time > prev_time * 1.2:  # 20% slower
                self.tracking_system.log_event(
                    "monitoring", 
                    "slow_execution", 
                    f"Execution time increased from {prev_time:.2f}s to {execution_time:.2f}s", 
                    "warning"
                )
        
        return {
            "success": True,
            "execution_time": execution_time,
            "metric": time_metric
        }
    
    @safe_execute
    def profile_execution(self) -> Dict[str, Any]:
        """
        Run profiling on the target file and log function execution times.
        
        Returns:
            Dict: Profiling results
        """
        if not os.path.exists(self.target_file):
            return {"success": False, "message": f"Target file {self.target_file} not found"}
            
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            # Use secure subprocess to run the target file
            result = run(["python3", self.target_file], capture_output=True, text=True)
            if result.returncode != 0:
                logger.warning(f"Target file execution failed: {result.stderr}")
                return {"success": False, "message": "Execution failed"}
        except Exception as e:
            logger.error(f"Error executing target file: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
        
        profiler.disable()
        result_stream = StringIO()
        stats = pstats.Stats(profiler, stream=result_stream)
        stats.sort_stats(pstats.SortKey.TIME)
        stats.print_stats()
        
        # Extract slowest functions
        slow_functions = []
        for line in result_stream.getvalue().split("\n"):
            if "src/" in line:
                parts = line.strip().split()
                if len(parts) > 5:
                    function_name = parts[-1]
                    execution_time = float(parts[2])
                    slow_functions.append((function_name, execution_time))
        
        # Log function execution times
        for func, time_value in slow_functions:
            self.db_manager.execute_update(
                "INSERT INTO performance_metrics (metric_name, metric_value, units) VALUES (?, ?, ?)",
                (f"function_{func}", time_value, "seconds")
            )
        
        return {
            "success": True,
            "slow_functions": slow_functions
        }
    
    @safe_execute
    def detect_bottlenecks(self) -> List[str]:
        """
        Identify the slowest functions based on profiling history.
        
        Returns:
            List[str]: List of bottleneck functions
        """
        # Get the last two execution records for each function
        function_metrics = self.db_manager.execute("""
            SELECT metric_name, metric_value
            FROM performance_metrics
            WHERE metric_name LIKE 'function_%'
            ORDER BY timestamp DESC
            LIMIT 100
        """)
        
        # Group by function name
        function_times = {}
        for metric in function_metrics:
            func_name = metric["metric_name"].replace("function_", "")
            if func_name not in function_times:
                function_times[func_name] = []
            function_times[func_name].append(metric["metric_value"])
        
        # Find functions with increasing execution time
        self.bottlenecks = []
        for func, times in function_times.items():
            if len(times) >= 2:
                # Compare latest to previous
                latest = times[0]
                previous = times[1]
                
                # Check if execution time increased significantly
                if latest > previous * (1 + self.threshold_percent / 100):
                    self.bottlenecks.append(func)
                    
                    # Log the bottleneck
                    self.tracking_system.log_event(
                        "monitoring", 
                        "bottleneck_detected", 
                        f"Function {func} execution time increased from {previous:.4f}s to {latest:.4f}s", 
                        "warning"
                    )
        
        return self.bottlenecks
    
    @safe_execute
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.
        
        Returns:
            Dict: Current resource usage
        """
        return {
            "cpu": psutil.cpu_percent(),
            "memory": psutil.virtual_memory().percent,
            "disk": psutil.disk_usage('/').percent
        }
    
    @safe_execute
    def get_performance_history(self, metric: str = "execution_time", 
                              limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get performance history for a specific metric.
        
        Args:
            metric: Metric name
            limit: Maximum number of records to return
            
        Returns:
            List[Dict]: Performance history
        """
        return self.db_manager.execute("""
            SELECT timestamp, metric_value, units
            FROM performance_metrics
            WHERE metric_name = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """, (metric, limit))
    
    @safe_execute
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the monitoring component.
        
        Returns:
            Dict: Current status
        """
        return {
            "resource_usage": self.get_resource_usage(),
            "bottlenecks": self.bottlenecks,
            "last_execution_time": self.metrics["execution_time"][-1] if self.metrics["execution_time"] else None
        }
