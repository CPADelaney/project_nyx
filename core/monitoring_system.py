# core/monitoring_system.py

"""
Comprehensive monitoring system for Project Nyx.
Tracks system resources, component health, and performance metrics.
"""

import os
import time
import json
import logging
import threading
import sqlite3
import psutil
import platform
from datetime import datetime, timedelta
import traceback

# Import core modules
from core.log_manager import LOG_DB
from core.error_handler import safe_execute, safe_db_execute
from core.config_manager import get_config
from core.utility_functions import save_json_state, load_json_state

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/monitoring_system.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-Monitoring")

# Constants
MONITOR_INTERVAL = 60  # Default interval in seconds
METRICS_FILE = "logs/system_metrics.json"
ALERTS_FILE = "logs/system_alerts.json"
HEALTH_FILE = "logs/system_health.json"

class ResourceMonitor:
    """Monitors system resource usage."""
    
    def __init__(self):
        """Initialize the resource monitor."""
        self.config = get_config()
        self.metrics = {
            "cpu": [],
            "memory": [],
            "disk": [],
            "network": [],
            "process": []
        }
        self.thresholds = self._load_thresholds()
        self.alerts = []
        self.interval = self.config.get("monitoring", "interval", MONITOR_INTERVAL)
        
        # Load previous metrics if they exist
        self._load_metrics()
    
    def _load_thresholds(self):
        """Load resource thresholds from configuration."""
        return {
            "cpu": self.config.get("resources", "max_cpu_percent", 80),
            "memory": self.config.get("resources", "max_memory_percent", 80),
            "disk": self.config.get("resources", "max_disk_usage_gb", 10),
            "process_count": self.config.get("resources", "max_process_count", 10)
        }
    
    def _load_metrics(self):
        """Load metrics from file if it exists."""
        metrics = load_json_state(METRICS_FILE, default=None)
        if metrics:
            self.metrics = metrics
    
    def _save_metrics(self):
        """Save metrics to file."""
        # Trim metrics to keep only the last 1000
        for key in self.metrics:
            if len(self.metrics[key]) > 1000:
                self.metrics[key] = self.metrics[key][-1000:]
        
        save_json_state(METRICS_FILE, self.metrics)
    
    @safe_execute
    def collect_cpu_metrics(self):
        """Collect CPU usage metrics."""
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        cpu_freq = psutil.cpu_freq()
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "percent": cpu_percent,
            "count": cpu_count,
            "freq": cpu_freq._asdict() if cpu_freq else None
        }
        
        self.metrics["cpu"].append(metric)
        
        # Check threshold
        if cpu_percent > self.thresholds["cpu"]:
            self._create_alert("cpu", f"CPU usage is {cpu_percent}%, above threshold of {self.thresholds['cpu']}%")
        
        return metric
    
    @safe_execute
    def collect_memory_metrics(self):
        """Collect memory usage metrics."""
        memory = psutil.virtual_memory()
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "total": memory.total,
            "available": memory.available,
            "percent": memory.percent,
            "used": memory.used,
            "free": memory.free
        }
        
        self.metrics["memory"].append(metric)
        
        # Check threshold
        if memory.percent > self.thresholds["memory"]:
            self._create_alert("memory", f"Memory usage is {memory.percent}%, above threshold of {self.thresholds['memory']}%")
        
        return metric
    
    @safe_execute
    def collect_disk_metrics(self):
        """Collect disk usage metrics."""
        disk = psutil.disk_usage('/')
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }
        
        self.metrics["disk"].append(metric)
        
        # Check threshold (convert bytes to GB)
        disk_usage_gb = disk.used / (1024 * 1024 * 1024)
        if disk_usage_gb > self.thresholds["disk"]:
            self._create_alert("disk", f"Disk usage is {disk_usage_gb:.2f} GB, above threshold of {self.thresholds['disk']} GB")
        
        return metric
    
    @safe_execute
    def collect_network_metrics(self):
        """Collect network usage metrics."""
        network = psutil.net_io_counters()
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "bytes_sent": network.bytes_sent,
            "bytes_recv": network.bytes_recv,
            "packets_sent": network.packets_sent,
            "packets_recv": network.packets_recv,
            "errin": network.errin,
            "errout": network.errout
        }
        
        self.metrics["network"].append(metric)
        return metric
    
    @safe_execute
    def collect_process_metrics(self):
        """Collect process metrics."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'username', 'memory_percent', 'cpu_percent']):
            try:
                # Get process info
                process_info = proc.info
                
                # Add to list if it's related to Nyx
                if "nyx" in process_info["name"].lower():
                    processes.append(process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        metric = {
            "timestamp": datetime.now().isoformat(),
            "count": len(processes),
            "processes": processes
        }
        
        self.metrics["process"].append(metric)
        
        # Check threshold
        if len(processes) > self.thresholds["process_count"]:
            self._create_alert("process", f"Process count is {len(processes)}, above threshold of {self.thresholds['process_count']}")
        
        return metric
    
    def _create_alert(self, alert_type, message):
        """Create an alert."""
        alert = {
            "timestamp": datetime.now().isoformat(),
            "type": alert_type,
            "message": message,
            "severity": "warning",
            "status": "active"
        }
        
        self.alerts.append(alert)
        
        # Save alerts to file
        alerts = load_json_state(ALERTS_FILE, default=[])
        alerts.append(alert)
        save_json_state(ALERTS_FILE, alerts)
        
        logger.warning(f"ALERT: {message}")
        
        return alert
    
    @safe_execute
    def collect_all_metrics(self):
        """Collect all metrics."""
        self.collect_cpu_metrics()
        self.collect_memory_metrics()
        self.collect_disk_metrics()
        self.collect_network_metrics()
        self.collect_process_metrics()
        
        # Save metrics
        self._save_metrics()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "cpu": self.metrics["cpu"][-1] if self.metrics["cpu"] else None,
            "memory": self.metrics["memory"][-1] if self.metrics["memory"] else None,
            "disk": self.metrics["disk"][-1] if self.metrics["disk"] else None,
            "network": self.metrics["network"][-1] if self.metrics["network"] else None,
            "process": self.metrics["process"][-1] if self.metrics["process"] else None
        }
    
    def start_monitoring(self, interval=None):
        """Start continuous monitoring in a background thread."""
        if interval:
            self.interval = interval
        
        def monitor_thread():
            while True:
                try:
                    self.collect_all_metrics()
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error in monitoring thread: {str(e)}")
                    time.sleep(self.interval * 2)  # Sleep longer on error
        
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info(f"Resource monitoring started with interval {self.interval} seconds")

class ComponentMonitor:
    """Monitors Nyx component health."""
    
    def __init__(self):
        """Initialize the component monitor."""
        self.config = get_config()
        self.components = {
            "nyx_core": {"status": "unknown", "last_check": None, "errors": 0},
            "self_analysis": {"status": "unknown", "last_check": None, "errors": 0},
            "optimization_engine": {"status": "unknown", "last_check": None, "errors": 0},
            "self_writer": {"status": "unknown", "last_check": None, "errors": 0},
            "log_manager": {"status": "unknown", "last_check": None, "errors": 0}
        }
        self.interval = self.config.get("monitoring", "component_interval", MONITOR_INTERVAL)
        
        # Load previous health data if it exists
        self._load_health()
    
    def _load_health(self):
        """Load health data from file if it exists."""
        health = load_json_state(HEALTH_FILE, default=None)
        if health:
            self.components = health
    
    def _save_health(self):
        """Save health data to file."""
        save_json_state(HEALTH_FILE, self.components)
    
    @safe_execute
    def check_component(self, component_name, check_function=None):
        """Check the health of a component."""
        component = self.components.get(component_name)
        if not component:
            component = {"status": "unknown", "last_check": None, "errors": 0}
            self.components[component_name] = component
        
        component["last_check"] = datetime.now().isoformat()
        
        try:
            if check_function:
                # Call the provided check function
                result = check_function()
                component["status"] = "healthy" if result else "unhealthy"
            else:
                # Default check - just see if the file exists
                file_path = f"src/{component_name}.py"
                if not os.path.exists(file_path):
                    file_path = f"{component_name}.py"
                
                if os.path.exists(file_path):
                    # Try to import it
                    try:
                        # Don't actually import, just check syntax
                        with open(file_path, 'r') as f:
                            compile(f.read(), file_path, 'exec')
                        component["status"] = "healthy"
                    except Exception as e:
                        component["status"] = "unhealthy"
                        component["errors"] += 1
                        component["last_error"] = str(e)
                else:
                    component["status"] = "missing"
        except Exception as e:
            component["status"] = "error"
            component["errors"] += 1
            component["last_error"] = str(e)
        
        # Save health data
        self._save_health()
        
        return component
    
    @safe_execute
    def check_all_components(self):
        """Check the health of all components."""
        for component_name in list(self.components.keys()):
            self.check_component(component_name)
        
        return self.components
    
    @safe_db_execute
    def check_database(self, conn=None):
        """Check the health of the database."""
        try:
            c = conn.cursor()
            
            # Check tables
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            
            # Check for required tables
            required_tables = [
                "performance_logs",
                "error_logs",
                "optimization_logs"
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            component = {
                "status": "healthy" if not missing_tables else "unhealthy",
                "last_check": datetime.now().isoformat(),
                "tables": tables,
                "missing_tables": missing_tables,
                "errors": len(missing_tables)
            }
            
            self.components["database"] = component
            
            # Save health data
            self._save_health()
            
            return component
        except Exception as e:
            component = {
                "status": "error",
                "last_check": datetime.now().isoformat(),
                "errors": 1,
                "last_error": str(e)
            }
            
            self.components["database"] = component
            
            # Save health data
            self._save_health()
            
            return component
    
    def start_monitoring(self, interval=None):
        """Start continuous monitoring in a background thread."""
        if interval:
            self.interval = interval
        
        def monitor_thread():
            while True:
                try:
                    self.check_all_components()
                    self.check_database()
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error in component monitoring thread: {str(e)}")
                    time.sleep(self.interval * 2)  # Sleep longer on error
        
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info(f"Component monitoring started with interval {self.interval} seconds")

class PerformanceMonitor:
    """Monitors Nyx performance metrics."""
    
    def __init__(self):
        """Initialize the performance monitor."""
        self.config = get_config()
        self.metrics = {
            "function_execution_times": {},
            "optimization_success_rate": 0,
            "error_rate": 0
        }
        self.interval = self.config.get("monitoring", "performance_interval", MONITOR_INTERVAL * 5)
    
    @safe_db_execute
    def collect_execution_times(self, conn=None):
        """Collect function execution times."""
        c = conn.cursor()
        
        # Get average execution time for each function
        c.execute("""
            SELECT function_name, AVG(execution_time) as avg_time
            FROM optimization_logs
            GROUP BY function_name
        """)
        
        execution_times = {row[0]: row[1] for row in c.fetchall()}
        self.metrics["function_execution_times"] = execution_times
        
        return execution_times
    
    @safe_db_execute
    def collect_optimization_metrics(self, conn=None):
        """Collect optimization metrics."""
        c = conn.cursor()
        
        # Get success rate of optimizations
        c.execute("""
            SELECT COUNT(*) as total,
                   SUM(CASE WHEN success = 1 THEN 1 ELSE 0 END) as successes
            FROM optimization_logs
        """)
        
        row = c.fetchone()
        if row and row[0] > 0:
            success_rate = (row[1] / row[0]) * 100
        else:
            success_rate = 0
        
        self.metrics["optimization_success_rate"] = success_rate
        
        return success_rate
    
    @safe_db_execute
    def collect_error_metrics(self, conn=None):
        """Collect error metrics."""
        c = conn.cursor()
        
        # Get error rate (errors per day)
        c.execute("""
            SELECT COUNT(*) as error_count
            FROM error_logs
            WHERE timestamp > datetime('now', '-1 day')
        """)
        
        row = c.fetchone()
        error_count = row[0] if row else 0
        
        self.metrics["error_rate"] = error_count
        
        return error_count
    
    @safe_execute
    def collect_all_metrics(self):
        """Collect all performance metrics."""
        self.collect_execution_times()
        self.collect_optimization_metrics()
        self.collect_error_metrics()
        
        return self.metrics
    
    def start_monitoring(self, interval=None):
        """Start continuous monitoring in a background thread."""
        if interval:
            self.interval = interval
        
        def monitor_thread():
            while True:
                try:
                    self.collect_all_metrics()
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error in performance monitoring thread: {str(e)}")
                    time.sleep(self.interval * 2)  # Sleep longer on error
        
        threading.Thread(target=monitor_thread, daemon=True).start()
        logger.info(f"Performance monitoring started with interval {self.interval} seconds")

class MonitoringSystem:
    """Main monitoring system that combines all monitors."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern to ensure only one instance exists."""
        if cls._instance is None:
            cls._instance = super(MonitoringSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the monitoring system."""
        if self._initialized:
            return
            
        self.config = get_config()
        self.resource_monitor = ResourceMonitor()
        self.component_monitor = ComponentMonitor()
        self.performance_monitor = PerformanceMonitor()
        self.running = False
        self._initialized = True
    
    def start(self):
        """Start all monitoring systems."""
        if self.running:
            logger.warning("Monitoring system is already running")
            return False
        
        # Get intervals from config
        resource_interval = self.config.get("monitoring", "resource_interval", MONITOR_INTERVAL)
        component_interval = self.config.get("monitoring", "component_interval", MONITOR_INTERVAL * 2)
        performance_interval = self.config.get("monitoring", "performance_interval", MONITOR_INTERVAL * 5)
        
        # Start all monitors
        self.resource_monitor.start_monitoring(resource_interval)
        self.component_monitor.start_monitoring(component_interval)
        self.performance_monitor.start_monitoring(performance_interval)
        
        self.running = True
        logger.info("Monitoring system started")
        return True
    
    def get_system_status(self):
        """Get the current system status."""
        status = {
            "timestamp": datetime.now().isoformat(),
            "system": platform.system(),
            "release": platform.release(),
            "resources": {
                "cpu": self.resource_monitor.metrics["cpu"][-1] if self.resource_monitor.metrics["cpu"] else None,
                "memory": self.resource_monitor.metrics["memory"][-1] if self.resource_monitor.metrics["memory"] else None,
                "disk": self.resource_monitor.metrics["disk"][-1] if self.resource_monitor.metrics["disk"] else None
            },
            "components": self.component_monitor.components,
            "performance": self.performance_monitor.metrics,
            "alerts": self.resource_monitor.alerts
        }
        
        return status

# Global instance
monitoring_system = MonitoringSystem()

def get_monitoring_system():
    """Get the global monitoring system instance."""
    return monitoring_system

if __name__ == "__main__":
    # Command-line interface for the monitoring system
    import argparse
    
    parser = argparse.ArgumentParser(description="Nyx Monitoring System")
    parser.add_argument("command", choices=["start", "status", "resources", "components", "performance"],
                        help="Command to execute")
    
    args = parser.parse_args()
    
    if args.command == "start":
        monitoring_system.start()
        print("Monitoring system started")
    
    elif args.command == "status":
        status = monitoring_system.get_system_status()
        print(json.dumps(status, indent=4, default=str))
    
    elif args.command == "resources":
        resources = monitoring_system.resource_monitor.collect_all_metrics()
        print(json.dumps(resources, indent=4, default=str))
    
    elif args.command == "components":
        components = monitoring_system.component_monitor.check_all_components()
        print(json.dumps(components, indent=4, default=str))
    
    elif args.command == "performance":
        performance = monitoring_system.performance_monitor.collect_all_metrics()
        print(json.dumps(performance, indent=4, default=str))
