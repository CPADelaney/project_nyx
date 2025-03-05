# tracking/components/scaling.py

"""
Scaling component that consolidates resource allocation and workload management
functionality from various tracking modules.
"""

import os
import logging
import psutil
import socket
import time
import subprocess
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from core.error_framework import safe_execute, ValidationError
from core.secure_subprocess import run
from core.permission_validator import PermissionValidator

# Configure logging
logger = logging.getLogger("NYX-Scaling")

class ScalingComponent:
    """
    Manages resource allocation, workload distribution, and instance scaling.
    Consolidates functionality from:
    - ai_scaling.py
    - ai_network_coordinator.py
    - self_infrastructure_optimization.py
    """
    
    def __init__(self, tracking_system):
        """
        Initialize the scaling component.
        
        Args:
            tracking_system: The parent tracking system
        """
        self.tracking_system = tracking_system
        self.db_manager = tracking_system.db_manager
        
        # Scaling configuration
        self.instance_count = 1  # Start with one instance
        self.max_instances = 3  # Maximum number of instances
        self.scale_up_threshold = 75  # CPU usage percentage to trigger scale up
        self.scale_down_threshold = 25  # CPU usage percentage to trigger scale down
        
        # Networking configuration
        self.local_ip = self._get_local_ip()
        self.port = 5555  # Port for instance communication
        
        # State tracking
        self.active_nodes = []
        self.load_balanced = False
        
        logger.info("Scaling component initialized")
    
    def _get_local_ip(self) -> str:
        """Get the local machine's IP address."""
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception as e:
            logger.error(f"Error getting local IP: {str(e)}")
            return "127.0.0.1"
    
    @safe_execute
    def monitor_workload(self) -> Dict[str, Any]:
        """
        Monitor system workload and scale as needed.
        
        Returns:
            Dict: Monitoring results
        """
        # Get current CPU usage
        cpu_usage = psutil.cpu_percent(interval=1)
        
        # Check if we need to scale up or down
        scale_action = None
        
        if cpu_usage > self.scale_up_threshold and self.instance_count < self.max_instances:
            # Need to scale up
            scale_result = self.scale_up()
            scale_action = "up"
        elif cpu_usage < self.scale_down_threshold and self.instance_count > 1:
            # Need to scale down
            scale_result = self.scale_down()
            scale_action = "down"
        
        # Log current status
        self.tracking_system.log_event(
            "scaling", 
            "workload_monitored", 
            f"CPU: {cpu_usage}%, Instances: {self.instance_count}, Action: {scale_action or 'none'}"
        )
        
        # Check if load needs to be balanced
        if cpu_usage > 50 and self.instance_count > 1 and not self.load_balanced:
            self.balance_load()
        
        return {
            "cpu_usage": cpu_usage,
            "instance_count": self.instance_count,
            "scale_action": scale_action
        }
    
    @safe_execute
    def scale_up(self) -> Dict[str, Any]:
        """
        Increase the number of instances.
        
        Returns:
            Dict: Scale-up result
        """
        if self.instance_count >= self.max_instances:
            return {"success": False, "message": "Already at maximum instances"}
        
        try:
            # Create a new instance ID
            self.instance_count += 1
            instance_id = f"instance_{self.instance_count}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Create instance directory in a safe location
            instance_dir = f"logs/instances/{instance_id}"
            
            # Create directory
            if PermissionValidator.ensure_safe_directory(instance_dir, create=True):
                # Copy necessary files to instance directory
                essential_files = [
                    "src/nyx_core.py",
                    "core/log_manager.py"
                ]
                
                for file_path in essential_files:
                    if os.path.exists(file_path):
                        target_dir = os.path.join(instance_dir, os.path.dirname(file_path))
                        if PermissionValidator.ensure_safe_directory(target_dir, create=True):
                            # Use secure copy method
                            if PermissionValidator.can_read_file(file_path):
                                target_path = os.path.join(instance_dir, file_path)
                                run(["cp", file_path, target_path], check=True)
                
                # Launch the new instance
                process = run(
                    ["python3", os.path.join(instance_dir, "src/nyx_core.py")],
                    capture_output=True,
                    text=True
                )
                
                # Check if the process started successfully
                if process.returncode != 0:
                    logger.error(f"Failed to start instance: {process.stderr}")
                    self.instance_count -= 1  # Revert count
                    return {"success": False, "message": "Failed to start instance"}
                
                # Record the new instance
                self.db_manager.execute_update(
                    "INSERT INTO tracking_events (component, event_type, details) VALUES (?, ?, ?)",
                    ("scaling", "instance_created", instance_id)
                )
                
                # Add to active nodes
                self.active_nodes.append({
                    "id": instance_id,
                    "path": instance_dir,
                    "created_at": datetime.now().isoformat()
                })
                
                self.tracking_system.log_event(
                    "scaling", 
                    "scaled_up", 
                    f"Created new instance: {instance_id}, total instances: {self.instance_count}"
                )
                
                return {
                    "success": True,
                    "instance_id": instance_id,
                    "instance_count": self.instance_count
                }
            else:
                logger.error(f"Failed to create instance directory: {instance_dir}")
                self.instance_count -= 1  # Revert count
                return {"success": False, "message": "Failed to create instance directory"}
                
        except Exception as e:
            logger.error(f"Error scaling up: {str(e)}")
            self.instance_count -= 1  # Revert count
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def scale_down(self) -> Dict[str, Any]:
        """
        Decrease the number of instances.
        
        Returns:
            Dict: Scale-down result
        """
        if self.instance_count <= 1:
            return {"success": False, "message": "Already at minimum instances"}
        
        try:
            # Get the most recent instance to remove
            if not self.active_nodes:
                logger.warning("No active nodes found for scale down")
                return {"success": False, "message": "No active nodes found"}
            
            # Remove the most recent instance
            instance = self.active_nodes.pop()
            instance_id = instance["id"]
            instance_dir = instance["path"]
            
            # Terminate the instance processes
            try:
                # Find and kill the process
                process_name = f"python3 {instance_dir}/src/nyx_core.py"
                result = run(
                    ["pkill", "-f", process_name],
                    capture_output=True,
                    text=True
                )
            except Exception as e:
                logger.warning(f"Error terminating instance process: {str(e)}")
                # Continue with cleanup even if process termination fails
            
            # Clean up instance directory
            if os.path.exists(instance_dir) and PermissionValidator.safe_path(instance_dir):
                run(["rm", "-rf", instance_dir], check=True)
            
            # Decrement instance count
            self.instance_count -= 1
            
            # Record the scale down
            self.db_manager.execute_update(
                "INSERT INTO tracking_events (component, event_type, details) VALUES (?, ?, ?)",
                ("scaling", "instance_removed", instance_id)
            )
            
            self.tracking_system.log_event(
                "scaling", 
                "scaled_down", 
                f"Removed instance: {instance_id}, total instances: {self.instance_count}"
            )
            
            return {
                "success": True,
                "instance_id": instance_id,
                "instance_count": self.instance_count
            }
        except Exception as e:
            logger.error(f"Error scaling down: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def balance_load(self) -> Dict[str, Any]:
        """
        Balance load across instances.
        
        Returns:
            Dict: Load balancing result
        """
        if self.instance_count <= 1:
            return {"success": False, "message": "Need multiple instances for load balancing"}
        
        try:
            # Set balanced flag
            self.load_balanced = True
            
            # In a real implementation, this would configure load distribution
            # For this example, we just log the action
            self.tracking_system.log_event(
                "scaling", 
                "load_balanced", 
                f"Balanced load across {self.instance_count} instances"
            )
            
            return {
                "success": True,
                "instance_count": self.instance_count,
                "balanced": True
            }
        except Exception as e:
            logger.error(f"Error balancing load: {str(e)}")
            self.load_balanced = False
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def discover_nodes(self) -> Dict[str, Any]:
        """
        Discover other nodes on the local network.
        
        Returns:
            Dict: Discovery result
        """
        discovered_nodes = []
        
        try:
            # For security, only scan the local system
            node_ip = "127.0.0.1"
            
            # Check if our port is open
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.1)
            result = s.connect_ex((node_ip, self.port))
            if result == 0:
                discovered_nodes.append(node_ip)
            s.close()
            
            if discovered_nodes:
                self.tracking_system.log_event(
                    "scaling", 
                    "nodes_discovered", 
                    f"Discovered {len(discovered_nodes)} nodes"
                )
                
            return {
                "success": True,
                "discovered_nodes": discovered_nodes
            }
        except Exception as e:
            logger.error(f"Error discovering nodes: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def optimize_resources(self) -> Dict[str, Any]:
        """
        Optimize resource usage.
        
        Returns:
            Dict: Optimization result
        """
        optimizations = []
        
        # Check system resources
        try:
            cpu_usage = psutil.cpu_percent(interval=1)
            ram_usage = psutil.virtual_memory().percent
            disk_usage = psutil.disk_usage('/').percent
            
            if cpu_usage > 80:
                optimizations.append("CPU usage high")
                # In a real implementation, we might adjust process priority
            
            if ram_usage > 80:
                optimizations.append("RAM usage high")
                # In a real implementation, we might clear caches
            
            if disk_usage > 80:
                optimizations.append("Disk usage high")
                # In a real implementation, we might clean up temp files
                
            if optimizations:
                self.tracking_system.log_event(
                    "scaling", 
                    "resources_optimized", 
                    f"Applied optimizations: {', '.join(optimizations)}"
                )
                
            return {
                "success": True,
                "optimizations": optimizations,
                "resource_usage": {
                    "cpu": cpu_usage,
                    "ram": ram_usage,
                    "disk": disk_usage
                }
            }
        except Exception as e:
            logger.error(f"Error optimizing resources: {str(e)}")
            return {"success": False, "message": f"Error: {str(e)}"}
    
    @safe_execute
    def get_instance_info(self) -> Dict[str, Any]:
        """
        Get information about instances.
        
        Returns:
            Dict: Instance information
        """
        return {
            "instance_count": self.instance_count,
            "active_nodes": self.active_nodes,
            "load_balanced": self.load_balanced
        }
    
    @safe_execute
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the scaling component.
        
        Returns:
            Dict: Current status
        """
        return {
            "instances": self.instance_count,
            "max_instances": self.max_instances,
            "balanced": self.load_balanced,
            "active_nodes": len(self.active_nodes)
        }
