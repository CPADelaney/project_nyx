# tracking/components/resilience.py

"""
Resilience component that consolidates backup, recovery, and self-healing functionality
from various tracking modules.
"""

import os
import shutil
import logging
import time
import subprocess
import socket
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

from core.error_framework import safe_execute, ValidationError
from core.secure_subprocess import run
from core.permission_validator import PermissionValidator

# Configure logging
logger = logging.getLogger("NYX-Resilience")

class ResilienceComponent:
    """
    Ensures system resilience through backups, health checks, and recovery mechanisms.
    Consolidates functionality from:
    - redundancy_manager.py
    - self_healing.py
    - self_preservation.py
    - self_execution.py
    """
    
    def __init__(self, tracking_system):
        """
        Initialize the resilience component.
        
        Args:
            tracking_system: The parent tracking system
        """
        self.tracking_system = tracking_system
        self.db_manager = tracking_system.db_manager
        
        # Backup configuration
        self.backup_dir = "logs/backups"
        self.backup_retention_days = 7
        self.failover_dir = "logs/failover"
        self.max_backups = 10
        
        # Ensure backup directories exist
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(self.failover_dir, exist_ok=True)
        
        # State tracking
        self.active_backups = []
        self.last_backup = None
        self.healing_events = []
        
        # Load existing backups
        self._load_existing_backups()
        
        logger.info("Resilience component initialized")
    
    def _load_existing_backups(self) -> None:
        """Load information about existing backups from the database."""
        backups = self.db_manager.execute("""
            SELECT id, timestamp, backup_type, path, status
            FROM system_backups
            WHERE status = 'active'
            ORDER BY timestamp DESC
        """)
        
        self.active_backups = backups
        if backups:
            self.last_backup = backups[0]
    
    @safe_execute
    def check_system(self) -> Dict[str, Any]:
        """
        Run all resilience checks.
        
        Returns:
            Dict: Results of the resilience checks
        """
        results = {
            "system_health": self.check_system_health(),
            "backup_status": self.check_backup_status(),
            "process_status": self.check_process_status()
        }
        
        self.tracking_system.log_event(
            "resilience", 
            "check_executed", 
            f"Health check complete: {len(self.healing_events)} healing events"
        )
        
        return results
    
    @safe_execute
    def check_system_health(self) -> Dict[str, Any]:
        """
        Check overall system health.
        
        Returns:
            Dict: Health check results
        """
        issues = []
        
        # Check for required directories
        required_dirs = [
            "logs",
            "src",
            "core"
        ]
        
        for directory in required_dirs:
            if not os.path.exists(directory) or not os.path.isdir(directory):
                issues.append(f"Required directory missing: {directory}")
                
                # Create the directory if possible
                try:
                    os.makedirs(directory, exist_ok=True)
                    self.tracking_system.log_event(
                        "resilience", 
                        "dir_created", 
                        f"Created missing directory: {directory}"
                    )
                except Exception as e:
                    self.tracking_system.log_event(
                        "resilience", 
                        "dir_creation_failed", 
                        f"Failed to create directory {directory}: {str(e)}", 
                        "error"
                    )
        
        # Check for required files
        required_files = [
            "src/nyx_core.py",
            "core/log_manager.py"
        ]
        
        for file_path in required_files:
            if not os.path.exists(file_path) or not os.path.isfile(file_path):
                issues.append(f"Required file missing: {file_path}")
                
                # Try to restore from backup
                if self.last_backup:
                    try:
                        self.restore_file(file_path)
                        self.tracking_system.log_event(
                            "resilience", 
                            "file_restored", 
                            f"Restored missing file: {file_path}"
                        )
                    except Exception as e:
                        self.tracking_system.log_event(
                            "resilience", 
                            "file_restore_failed", 
                            f"Failed to restore file {file_path}: {str(e)}", 
                            "error"
                        )
        
        # Check system resources
        resource_usage = self.tracking_system.monitoring.get_resource_usage()
        if resource_usage["cpu"] > 90:
            issues.append(f"Critical CPU usage: {resource_usage['cpu']}%")
        if resource_usage["memory"] > 90:
            issues.append(f"Critical memory usage: {resource_usage['memory']}%")
        if resource_usage["disk"] > 90:
            issues.append(f"Critical disk usage: {resource_usage['disk']}%")
        
        # Record healing events if issues were found
        if issues:
            for issue in issues:
                self.tracking_system.log_event(
                    "resilience", 
                    "system_issue", 
                    issue, 
                    "warning"
                )
                
                # Add to healing events
                self.healing_events.append({
                    "timestamp": datetime.now().isoformat(),
                    "issue": issue,
                    "status": "detected"
                })
        
        return {
            "healthy": len(issues) == 0,
            "issues": issues
        }
    
    @safe_execute
    def check_backup_status(self) -> Dict[str, Any]:
        """
        Check backup status and create new backups if needed.
        
        Returns:
            Dict: Backup status
        """
        # Check when the last backup was created
        if not self.last_backup:
            # No backups exist, create one
            self.create_backup()
            return {"status": "new_backup_created"}
        
        # Check if the last backup is older than a day
        last_backup_time = datetime.fromisoformat(self.last_backup["timestamp"])
        time_since_backup = (datetime.now() - last_backup_time).total_seconds() / 3600  # Hours
        
        if time_since_backup > 24:
            # Backup is more than a day old, create a new one
            self.create_backup()
            return {"status": "new_backup_created", "hours_since_last": time_since_backup}
        
        # Check if all backups are valid
        invalid_backups = []
        for backup in self.active_backups:
            if not os.path.exists(backup["path"]):
                invalid_backups.append(backup)
                
                # Mark as inactive in database
                self.db_manager.execute_update(
                    "UPDATE system_backups SET status = 'missing' WHERE id = ?",
                    (backup["id"],)
                )
        
        if invalid_backups:
            # Some backups are missing, create a new one
            self.create_backup()
            return {"status": "missing_backups_replaced", "missing_count": len(invalid_backups)}
        
        return {"status": "backups_valid", "hours_since_last": time_since_backup}
    
    @safe_execute
    def check_process_status(self) -> Dict[str, Any]:
        """
        Check if critical processes are running.
        
        Returns:
            Dict: Process status
        """
        critical_processes = [
            "nyx_core.py"  # Add other critical processes as needed
        ]
        
        missing_processes = []
        
        # Check if processes are running
        try:
            # Get the list of running processes securely
            result = run(["ps", "aux"], capture_output=True, text=True)
            process_list = result.stdout
            
            for process in critical_processes:
                if process not in process_list:
                    missing_processes.append(process)
                    
                    self.tracking_system.log_event(
                        "resilience", 
                        "process_missing", 
                        f"Critical process not running: {process}", 
                        "warning"
                    )
        except Exception as e:
            self.tracking_system.log_event(
                "resilience", 
                "process_check_failed", 
                f"Failed to check processes: {str(e)}", 
                "error"
            )
            return {"success": False, "error": str(e)}
        
        # Try to restart missing processes
        restarted_processes = []
        for process in missing_processes:
            if process == "nyx_core.py":
                try:
                    run(["python3", "src/nyx_core.py"], capture_output=True, text=True)
                    restarted_processes.append(process)
                    
                    self.tracking_system.log_event(
                        "resilience", 
                        "process_restarted", 
                        f"Restarted process: {process}"
                    )
                except Exception as e:
                    self.tracking_system.log_event(
                        "resilience", 
                        "process_restart_failed", 
                        f"Failed to restart {process}: {str(e)}", 
                        "error"
                    )
        
        return {
            "all_running": len(missing_processes) == 0,
            "missing_processes": missing_processes,
            "restarted_processes": restarted_processes
        }
    
    @safe_execute
    def create_backup(self, backup_type: str = "full") -> Dict[str, Any]:
        """
        Create a system backup.
        
        Args:
            backup_type: Type of backup (full, incremental)
            
        Returns:
            Dict: Backup result
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(self.backup_dir, f"system_backup_{timestamp}")
        
        # Create directory if it doesn't exist
        os.makedirs(backup_path, exist_ok=True)
        
        # Directories to backup
        backup_dirs = [
            "src",
            "core"
        ]
        
        # Create backup
        try:
            for directory in backup_dirs:
                if os.path.exists(directory) and os.path.isdir(directory):
                    # Use permission validator for safe path operations
                    target_dir = os.path.join(backup_path, directory)
                    if PermissionValidator.ensure_safe_directory(target_dir, create=True):
                        # Copy directory contents
                        shutil.copytree(directory, target_dir, dirs_exist_ok=True)
            
            # Record backup in database
            backup_id = self.db_manager.execute_update(
                "INSERT INTO system_backups (backup_type, path) VALUES (?, ?)",
                (backup_type, backup_path)
            )
            
            # Update state
            backup_record = {
                "id": backup_id,
                "timestamp": datetime.now().isoformat(),
                "backup_type": backup_type,
                "path": backup_path,
                "status": "active"
            }
            
            self.active_backups.insert(0, backup_record)
            self.last_backup = backup_record
            
            self.tracking_system.log_event(
                "resilience", 
                "backup_created", 
                f"Created {backup_type} backup at {backup_path}"
            )
            
            # Clean up old backups
            self._clean_old_backups()
            
            return {
                "success": True,
                "backup_id": backup_id,
                "path": backup_path
            }
        except Exception as e:
            self.tracking_system.log_event(
                "resilience", 
                "backup_failed", 
                f"Failed to create backup: {str(e)}", 
                "error"
            )
            return {"success": False, "error": str(e)}
    
    def _clean_old_backups(self) -> None:
        """Clean up old backups based on retention policy."""
        # First, remove any backups beyond the max count
        if len(self.active_backups) > self.max_backups:
            # Get the oldest backups
            backups_to_remove = self.active_backups[self.max_backups:]
            self.active_backups = self.active_backups[:self.max_backups]
            
            # Remove them
            for backup in backups_to_remove:
                try:
                    # Delete the backup directory
                    if os.path.exists(backup["path"]):
                        shutil.rmtree(backup["path"])
                    
                    # Update the database
                    self.db_manager.execute_update(
                        "UPDATE system_backups SET status = 'deleted' WHERE id = ?",
                        (backup["id"],)
                    )
                    
                    self.tracking_system.log_event(
                        "resilience", 
                        "backup_deleted", 
                        f"Deleted old backup: {backup['path']}"
                    )
                except Exception as e:
                    self.tracking_system.log_event(
                        "resilience", 
                        "backup_deletion_failed", 
                        f"Failed to delete backup {backup['path']}: {str(e)}", 
                        "warning"
                    )
        
        # Next, remove backups older than retention days
        retention_time = datetime.now().timestamp() - (self.backup_retention_days * 24 * 3600)
        backups_to_remove = []
        
        for backup in self.active_backups:
            backup_time = datetime.fromisoformat(backup["timestamp"]).timestamp()
            if backup_time < retention_time:
                backups_to_remove.append(backup)
        
        # Remove backups outside retention period
        for backup in backups_to_remove:
            try:
                # Delete the backup directory
                if os.path.exists(backup["path"]):
                    shutil.rmtree(backup["path"])
                
                # Update the database
                self.db_manager.execute_update(
                    "UPDATE system_backups SET status = 'expired' WHERE id = ?",
                    (backup["id"],)
                )
                
                # Remove from active backups
                self.active_backups.remove(backup)
                
                self.tracking_system.log_event(
                    "resilience", 
                    "backup_expired", 
                    f"Removed expired backup: {backup['path']}"
                )
            except Exception as e:
                self.tracking_system.log_event(
                    "resilience", 
                    "backup_expiration_failed", 
                    f"Failed to remove expired backup {backup['path']}: {str(e)}", 
                    "warning"
                )
    
    @safe_execute
    def restore_system(self, backup_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Restore the system from a backup.
        
        Args:
            backup_id: ID of the backup to restore (None for latest)
            
        Returns:
            Dict: Restore result
        """
        # If no backup ID specified, use the latest
        if backup_id is None:
            if not self.active_backups:
                return {"success": False, "message": "No active backups available"}
            
            backup = self.active_backups[0]
        else:
            # Find the specified backup
            matching_backups = [b for b in self.active_backups if b["id"] == backup_id]
            if not matching_backups:
                return {"success": False, "message": f"Backup ID {backup_id} not found"}
            
            backup = matching_backups[0]
        
        # Check if the backup exists
        if not os.path.exists(backup["path"]):
            self.tracking_system.log_event(
                "resilience", 
                "restore_failed", 
                f"Backup path not found: {backup['path']}", 
                "error"
            )
            return {"success": False, "message": "Backup path not found"}
        
        # Create a backup of the current state before restoring
        pre_restore_backup = self.create_backup(backup_type="pre_restore")
        
        # Restore from backup
        try:
            # Get list of directories in the backup
            backup_dirs = [d for d in os.listdir(backup["path"]) 
                          if os.path.isdir(os.path.join(backup["path"], d))]
            
            # Restore each directory
            for directory in backup_dirs:
                source_dir = os.path.join(backup["path"], directory)
                
                # Make sure the target directory exists
                if not os.path.exists(directory):
                    os.makedirs(directory, exist_ok=True)
                
                # Copy files from backup to target
                shutil.copytree(source_dir, directory, dirs_exist_ok=True)
            
            self.tracking_system.log_event(
                "resilience", 
                "system_restored", 
                f"Restored system from backup ID {backup['id']} at {backup['path']}"
            )
            
            return {
                "success": True,
                "message": "System restored successfully",
                "backup_id": backup["id"],
                "pre_restore_backup": pre_restore_backup.get("backup_id") if pre_restore_backup["success"] else None
            }
        except Exception as e:
            self.tracking_system.log_event(
                "resilience", 
                "restore_failed", 
                f"Failed to restore from backup: {str(e)}", 
                "error"
            )
            return {"success": False, "message": f"Restore failed: {str(e)}"}
    
    @safe_execute
    def restore_file(self, file_path: str, backup_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Restore a specific file from a backup.
        
        Args:
            file_path: Path to the file to restore
            backup_id: ID of the backup to restore from (None for latest)
            
        Returns:
            Dict: Restore result
        """
        # Verify file path is valid
        if not PermissionValidator.safe_path(file_path):
            return {"success": False, "message": "Invalid file path"}
        
        # If no backup ID specified, use the latest
        if backup_id is None:
            if not self.active_backups:
                return {"success": False, "message": "No active backups available"}
            
            backup = self.active_backups[0]
        else:
            # Find the specified backup
            matching_backups = [b for b in self.active_backups if b["id"] == backup_id]
            if not matching_backups:
                return {"success": False, "message": f"Backup ID {backup_id} not found"}
            
            backup = matching_backups[0]
        
        # Check if the backup exists
        if not os.path.exists(backup["path"]):
            self.tracking_system.log_event(
                "resilience", 
                "file_restore_failed", 
                f"Backup path not found: {backup['path']}", 
                "error"
            )
            return {"success": False, "message": "Backup path not found"}
        
        # Build the path to the file in the backup
        backup_file_path = os.path.join(backup["path"], file_path)
        
        # Check if the file exists in the backup
        if not os.path.exists(backup_file_path) or not os.path.isfile(backup_file_path):
            return {"success": False, "message": f"File {file_path} not found in backup"}
        
        try:
            # Create parent directory if it doesn't exist
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Copy the file from backup to target
            shutil.copy2(backup_file_path, file_path)
            
            self.tracking_system.log_event(
                "resilience", 
                "file_restored", 
                f"Restored file {file_path} from backup ID {backup['id']}"
            )
            
            return {
                "success": True,
                "message": f"File {file_path} restored successfully",
                "backup_id": backup["id"]
            }
        except Exception as e:
            self.tracking_system.log_event(
                "resilience", 
                "file_restore_failed", 
                f"Failed to restore file {file_path}: {str(e)}", 
                "error"
            )
            return {"success": False, "message": f"File restore failed: {str(e)}"}
    
    @safe_execute
    def get_backup_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get backup history.
        
        Args:
            limit: Maximum number of backups to return
            
        Returns:
            List[Dict]: Backup history
        """
        return self.db_manager.execute("""
            SELECT id, timestamp, backup_type, path, status
            FROM system_backups
            ORDER BY timestamp DESC
            LIMIT ?
        """, (limit,))
    
    @safe_execute
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the resilience component.
        
        Returns:
            Dict: Current status
        """
        return {
            "active_backups": len(self.active_backups),
            "last_backup": self.last_backup,
            "healing_events": len(self.healing_events)
        }
