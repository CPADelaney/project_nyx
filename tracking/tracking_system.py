# tracking/tracking_system.py

"""
Unified tracking system that consolidates monitoring, resilience, scaling, and improvement
functionality from the various tracking modules.
"""

import os
import logging
import threading
import time
from typing import Dict, Any, List, Optional, Union, Type

# Import core utilities
from core.database_manager import get_log_db_manager
from core.error_framework import safe_execute, ValidationError
from core.utility_functions import load_json_state, save_json_state
from core.resource_limiter import get_resource_monitor

# Import component implementations
from tracking.components.monitoring import MonitoringComponent
from tracking.components.resilience import ResilienceComponent
from tracking.components.scaling import ScalingComponent
from tracking.components.improvement import ImprovementComponent

# Configure logging
logger = logging.getLogger("NYX-TrackingSystem")

class TrackingSystem:
    """
    Unified tracking system that consolidates monitoring, resilience, scaling, and 
    improvement functionality from the various tracking modules.
    """
    
    _instance = None
    
    def __new__(cls):
        """Implements the Singleton pattern for the tracking system."""
        if cls._instance is None:
            cls._instance = super(TrackingSystem, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize the tracking system if not already initialized."""
        if self._initialized:
            return
            
        # Set up database
        self.db_manager = get_log_db_manager()
        self._initialize_database()
        
        # System state
        self.running = False
        self.pause_requested = False
        self.check_interval = 60  # Default check interval in seconds
        self.system_thread = None
        
        # Core components
        self.monitoring = MonitoringComponent(self)
        self.resilience = ResilienceComponent(self)
        self.scaling = ScalingComponent(self)
        self.improvement = ImprovementComponent(self)
        
        # Initialize resource monitoring
        self.resource_monitor = get_resource_monitor()
        
        self._initialized = True
        logger.info("Tracking system initialized")
    
    def _initialize_database(self) -> None:
        """Create necessary database tables if they don't exist."""
        # Create a single unified tracking_events table
        self.db_manager.execute_script('''
            CREATE TABLE IF NOT EXISTS tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                component TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                severity TEXT DEFAULT 'info'
            );
            
            CREATE INDEX IF NOT EXISTS idx_tracking_events_component 
            ON tracking_events(component);
            
            CREATE INDEX IF NOT EXISTS idx_tracking_events_type 
            ON tracking_events(event_type);
        ''')
        
        # Create component-specific tables that need specific schemas
        self.db_manager.execute_script('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                units TEXT
            );
            
            CREATE TABLE IF NOT EXISTS system_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                backup_type TEXT NOT NULL,
                path TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            );
            
            CREATE TABLE IF NOT EXISTS improvement_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                goal TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                completed_timestamp TEXT
            );
        ''')
    
    @safe_execute
    def log_event(self, component: str, event_type: str, details: str = None, 
                 severity: str = "info") -> Dict[str, Any]:
        """
        Log a tracking event to the database.
        
        Args:
            component: The component that generated the event
            event_type: The type of event
            details: Event details
            severity: Event severity (info, warning, error, critical)
            
        Returns:
            Dict: Result of the operation
        """
        self.db_manager.execute_update(
            "INSERT INTO tracking_events (component, event_type, details, severity) VALUES (?, ?, ?, ?)",
            (component, event_type, details, severity)
        )
        
        # Also log to the console for certain severity levels
        if severity == "warning":
            logger.warning(f"{component}: {event_type} - {details}")
        elif severity == "error" or severity == "critical":
            logger.error(f"{component}: {event_type} - {details}")
        else:
            logger.info(f"{component}: {event_type} - {details}")
            
        return {"success": True, "component": component, "event_type": event_type}
    
    @safe_execute
    def get_recent_events(self, component: Optional[str] = None, 
                         limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get recent tracking events.
        
        Args:
            component: Optional component filter
            limit: Maximum number of events to return
            
        Returns:
            List[Dict]: List of recent events
        """
        if component:
            events = self.db_manager.execute(
                "SELECT * FROM tracking_events WHERE component = ? ORDER BY timestamp DESC LIMIT ?",
                (component, limit)
            )
        else:
            events = self.db_manager.execute(
                "SELECT * FROM tracking_events ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            )
            
        return events
    
    @safe_execute
    def start(self) -> Dict[str, Any]:
        """
        Start the tracking system.
        
        Returns:
            Dict: Result of the operation
        """
        if self.running:
            return {"success": False, "message": "Tracking system already running"}
            
        self.running = True
        self.pause_requested = False
        
        # Start the resource monitor
        self.resource_monitor.start()
        
        # Create a thread for periodic checks
        def system_thread():
            while self.running:
                if not self.pause_requested:
                    try:
                        # Run monitoring checks
                        self.monitoring.monitor()
                        
                        # Run resilience checks
                        self.resilience.check_system()
                        
                        # Run scaling checks
                        self.scaling.monitor_workload()
                        
                        # Run improvement checks
                        self.improvement.analyze_performance()
                    except Exception as e:
                        logger.error(f"Error in tracking system thread: {str(e)}")
                
                # Sleep until next check
                time.sleep(self.check_interval)
        
        self.system_thread = threading.Thread(target=system_thread, daemon=True)
        self.system_thread.start()
        
        self.log_event("tracking_system", "system_started", "Tracking system started")
        logger.info("Tracking system started")
        return {"success": True, "message": "Tracking system started"}
    
    @safe_execute
    def stop(self) -> Dict[str, Any]:
        """
        Stop the tracking system.
        
        Returns:
            Dict: Result of the operation
        """
        if not self.running:
            return {"success": False, "message": "Tracking system not running"}
            
        self.running = False
        
        if self.system_thread:
            self.system_thread.join(timeout=30)
            
        # Stop the resource monitor
        self.resource_monitor.stop()
        
        self.log_event("tracking_system", "system_stopped", "Tracking system stopped")
        logger.info("Tracking system stopped")
        return {"success": True, "message": "Tracking system stopped"}
    
    @safe_execute
    def pause(self) -> Dict[str, Any]:
        """
        Pause the tracking system.
        
        Returns:
            Dict: Result of the operation
        """
        if not self.running:
            return {"success": False, "message": "Tracking system not running"}
            
        self.pause_requested = True
        
        self.log_event("tracking_system", "system_paused", "Tracking system paused")
        logger.info("Tracking system paused")
        return {"success": True, "message": "Tracking system paused"}
    
    @safe_execute
    def resume(self) -> Dict[str, Any]:
        """
        Resume the tracking system after pausing.
        
        Returns:
            Dict: Result of the operation
        """
        if not self.running:
            return {"success": False, "message": "Tracking system not running"}
            
        if not self.pause_requested:
            return {"success": False, "message": "Tracking system not paused"}
            
        self.pause_requested = False
        
        self.log_event("tracking_system", "system_resumed", "Tracking system resumed")
        logger.info("Tracking system resumed")
        return {"success": True, "message": "Tracking system resumed"}
    
    @safe_execute
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the tracking system.
        
        Returns:
            Dict: Current status
        """
        status = {
            "running": self.running,
            "paused": self.pause_requested,
            "check_interval": self.check_interval,
            "components": {
                "monitoring": self.monitoring.get_status(),
                "resilience": self.resilience.get_status(),
                "scaling": self.scaling.get_status(),
                "improvement": self.improvement.get_status()
            },
            "recent_events": self.get_recent_events(limit=10)
        }
        
        return status

# Create a global instance
_tracking_system = None

def get_tracking_system() -> TrackingSystem:
    """
    Get the global tracking system instance.
    
    Returns:
        TrackingSystem: The global tracking system instance
    """
    global _tracking_system
    if _tracking_system is None:
        _tracking_system = TrackingSystem()
    return _tracking_system
