# tracking/self_propagation.py
import sys
import os
import sqlite3
import shutil
import socket
import subprocess
import json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized
from core.error_handler import safe_execute, safe_db_execute
from core.utility_functions import load_json_state, save_json_state

LOG_DB = "logs/ai_logs.db"
PROPAGATION_LOG = "logs/propagation_status.json"
KNOWN_HOSTS_FILE = "logs/known_hosts.json"
REMOTE_DEPLOY_PATH = "/tmp/nyx_remote/"

# Safe list of known hosts that can be deployed to
SAFE_HOSTS = ["127.0.0.1", "localhost"]

class SelfPropagation:
    """Ensures AI replication across multiple execution environments, with proper safety controls."""

    def __init__(self):
        self.status = load_json_state(
            PROPAGATION_LOG, 
            default={
                "last_checked": str(datetime.utcnow()), 
                "active_nodes": [], 
                "replication_attempts": 0,
                "remote_hosts": []
            }
        )
        
        initialize_log_db()  # Ensure database is initialized
        self._load_known_hosts()

    def _load_known_hosts(self):
        """Loads previously approved remote execution nodes."""
        known_hosts = load_json_state(KNOWN_HOSTS_FILE, default=[])
        
        # Only keep hosts that are in the SAFE_HOSTS list
        self.status["remote_hosts"] = [host for host in known_hosts if host in SAFE_HOSTS]
        save_json_state(KNOWN_HOSTS_FILE, self.status["remote_hosts"])

    @safe_execute
    def discover_local_network(self):
        """Scans for local devices but only logs their existence, doesn't connect."""
        print("🔍 Scanning local network...")
        
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        
        # Only log information about the local machine
        discovered_hosts = [local_ip]
        
        print(f"✅ Found local machine at {local_ip}")

        self.log_propagation_event("discovered_nodes", f"Local machine at {local_ip}")
        return {"success": True, "discovered": discovered_hosts}

    @safe_execute
    def prepare_backups(self):
        """Creates local backups of important files but doesn't deploy them remotely."""
        backup_dir = "logs/backups"
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
            
        # List of essential files to back up
        essential_files = [
            "src/nyx_core.py",
            "core/log_manager.py"
        ]
        
        backed_up_files = []
        for file in essential_files:
            if os.path.exists(file):
                backup_path = os.path.join(backup_dir, os.path.basename(file))
                shutil.copy2(file, backup_path)
                backed_up_files.append(file)
                
        self.log_propagation_event("local_backup", f"Backed up {len(backed_up_files)} files to {backup_dir}")
        
        return {
            "success": True, 
            "message": f"Created local backups of {len(backed_up_files)} files",
            "backup_dir": backup_dir
        }

    @safe_execute
    def detect_termination_attempts(self):
        """Monitors for process termination and logs the attempts."""
        process_running = False

        try:
            process_list = subprocess.check_output(["ps", "aux"]).decode("utf-8")
            if "nyx_core.py" in process_list:
                process_running = True
        except Exception as e:
            print(f"⚠️ System monitoring failed: {str(e)}")
            return {"success": False, "error": str(e)}

        if not process_running:
            print("⚠️ AI process not detected! Logging event...")
            self.log_propagation_event("process_not_found", "nyx_core.py process not found")
            return {"success": False, "message": "Process not running"}
            
        return {"success": True, "message": "Process running normally"}

    @safe_db_execute
    def log_propagation_event(self, event_type, details, conn=None):
        """Logs self-propagation events in SQLite."""
        c = conn.cursor()
        c.execute("""
            INSERT INTO self_propagation_logs 
            (timestamp, event_type, details) 
            VALUES (datetime('now'), ?, ?)
        """, (event_type, details))
        
        return {"success": True, "event_type": event_type}

    @safe_db_execute
    def review_propagation_status(self, conn=None):
        """Displays AI propagation status."""
        c = conn.cursor()
        c.execute("""
            SELECT timestamp, event_type, details 
            FROM self_propagation_logs 
            ORDER BY timestamp DESC 
            LIMIT 10
        """)
        logs = c.fetchall()

        print("\n🌎 AI Propagation Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")
            
        # Update last checked timestamp
        self.status["last_checked"] = str(datetime.utcnow())
        save_json_state(PROPAGATION_LOG, self.status)
        
        return {
            "success": True,
            "logs": [
                {"timestamp": ts, "event_type": et, "details": d}
                for ts, et, d in logs
            ]
        }
        
    @safe_execute
    def export_backup_to_json(self, output_path="logs/nyx_backup.json"):
        """
        Exports a backup of critical information as a JSON file.
        This is a safer alternative to automatic propagation.
        """
        # Collect critical information
        critical_info = {
            "timestamp": str(datetime.utcnow()),
            "hostname": socket.gethostname(),
            "status": self.status,
            "config": {
                "safe_hosts": SAFE_HOSTS,
                "remote_deploy_path": REMOTE_DEPLOY_PATH
            }
        }
        
        # Save to file
        try:
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(critical_info, f, indent=4)
                
            print(f"✅ Backup exported to {output_path}")
            self.log_propagation_event("backup_exported", f"Backup saved to {output_path}")
            
            return {
                "success": True,
                "message": f"Backup saved to {output_path}",
                "path": output_path
            }
        except Exception as e:
            print(f"❌ Failed to export backup: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
            
    @safe_execute
    def deploy_locally(self, target_dir=None, require_confirmation=True):
        """
        Deploys the system to a local directory with user confirmation.
        This is a safer alternative to automatic remote deployment.
        """
        if target_dir is None:
            target_dir = os.path.join(os.path.expanduser("~"), "nyx_local_deploy")
            
        if require_confirmation:
            confirmation = input(f"Deploy to {target_dir}? (y/n): ")
            if confirmation.lower() != "y":
                print("Deployment cancelled by user.")
                return {
                    "success": False,
                    "message": "Deployment cancelled by user"
                }
                
        # Create target directory
        os.makedirs(target_dir, exist_ok=True)
        
        # Copy essential files
        essential_files = [
            "src/nyx_core.py",
            "core/log_manager.py",
            "core/error_handler.py",
            "core/utility_functions.py"
        ]
        
        deployed_files = []
        for file in essential_files:
            if os.path.exists(file):
                target_path = os.path.join(target_dir, file)
                target_dir_path = os.path.dirname(target_path)
                os.makedirs(target_dir_path, exist_ok=True)
                
                shutil.copy2(file, target_path)
                deployed_files.append(file)
                
        print(f"✅ Deployed {len(deployed_files)} files to {target_dir}")
        self.log_propagation_event("local_deployment", f"Deployed to {target_dir}")
        
        return {
            "success": True,
            "message": f"Deployed {len(deployed_files)} files to {target_dir}",
            "target_dir": target_dir,
            "deployed_files": deployed_files
        }

if __name__ == "__main__":
    propagation_manager = SelfPropagation()
    propagation_manager.detect_termination_attempts()
    propagation_manager.prepare_backups()
    propagation_manager.review_propagation_status()
    propagation_manager.export_backup_to_json()
