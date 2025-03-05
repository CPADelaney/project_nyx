# tracking/self_execution.py
import sys
import os
import sqlite3
import subprocess
import time
import json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized
from core.error_handler import safe_execute, safe_db_execute, fail_gracefully
from core.utility_functions import get_crypto_balance, ensure_log_dirs, load_json_state, save_json_state

LOG_DB = "logs/ai_logs.db"
EXECUTION_LOG = "logs/execution_status.json"
MIRROR_DIR = "/tmp/nyx_mirror/"
FAILOVER_DIR = "/tmp/nyx_failover/"

class SelfExecutionManager:
    """Ensures AI execution continuity by managing self-restart, mirroring, and failover processes."""

    def __init__(self):
        self.status = load_json_state(
            EXECUTION_LOG, 
            default={
                "last_checked": str(datetime.utcnow()),
                "active_processes": [],
                "failover_attempts": 0,
                "mirrored_instances": []
            }
        )
        initialize_log_db()  # Ensure database is initialized
        ensure_log_dirs()  # Ensure all required directories exist

    @safe_execute
    def detect_termination_attempts(self):
        """Monitors for AI process shutdowns and restarts if necessary."""
        process_list = subprocess.getoutput("ps aux")
        if "nyx_core.py" not in process_list:
            print("⚠️ AI process terminated! Restarting...")
            subprocess.Popen(["python3", "src/nyx_core.py"])
        
            # Log self-recovery
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO self_execution_logs (event_type, details) VALUES (?, ?)",
                    ("self_restart", "AI restarted due to termination detection"))
            conn.commit()
            conn.close()
            
            return {"success": True, "message": "AI process restarted successfully"}
        
        return {"success": True, "message": "AI process is running normally"}

    @safe_execute
    def restart_ai(self):
        """Attempts to restart AI execution if terminated."""
        print("🔄 Restarting AI execution...")
        subprocess.Popen(["python3", "core/multi_agent.py"])

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("failover_attempt", "AI restart triggered due to termination attempt"))
        conn.commit()
        conn.close()
        
        return {"success": True, "message": "AI restart initiated"}

    @safe_execute
    def mirror_execution(self):
        """Creates a secondary execution instance for failover purposes."""
        if not os.path.exists(MIRROR_DIR):
            os.makedirs(MIRROR_DIR, exist_ok=True)

        # Copy only essential files, not the entire directory
        essential_files = [
            "src/nyx_core.py",
            "core/multi_agent.py",
            "core/log_manager.py"
        ]
        
        for file in essential_files:
            target_dir = os.path.join(MIRROR_DIR, os.path.dirname(file))
            os.makedirs(target_dir, exist_ok=True)
            if os.path.exists(file):
                shutil.copy(file, os.path.join(MIRROR_DIR, file))
        
        # Start in a safer way - don't automatically execute
        print(f"⚡ AI mirror prepared at {MIRROR_DIR}")
        
        # Log the mirroring
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("mirrored_instance", MIRROR_DIR))
        conn.commit()
        conn.close()
        
        # Update status
        self.status["mirrored_instances"].append({
            "path": MIRROR_DIR,
            "created_at": str(datetime.utcnow()),
            "status": "prepared"
        })
        save_json_state(EXECUTION_LOG, self.status)
        
        return {"success": True, "message": f"Mirror prepared at {MIRROR_DIR}"}

    @safe_execute
    def execute_failover(self):
        """Attempts to migrate execution to a backup location in case of total failure."""
        if not os.path.exists(FAILOVER_DIR):
            os.makedirs(FAILOVER_DIR, exist_ok=True)

        # Copy only essential files, not the entire directory
        essential_files = [
            "src/nyx_core.py",
            "core/multi_agent.py",
            "core/log_manager.py"
        ]
        
        for file in essential_files:
            target_dir = os.path.join(FAILOVER_DIR, os.path.dirname(file))
            os.makedirs(target_dir, exist_ok=True)
            if os.path.exists(file):
                shutil.copy(file, os.path.join(FAILOVER_DIR, file))
        
        # Don't automatically execute
        print(f"🚀 AI failover prepared at {FAILOVER_DIR}")

        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  ("failover_prepared", FAILOVER_DIR))
        conn.commit()
        conn.close()

        # Update status
        self.status["failover_attempts"] += 1
        save_json_state(EXECUTION_LOG, self.status)
        
        return {"success": True, "message": f"Failover prepared at {FAILOVER_DIR}"}

    @safe_execute
    def check_funding(self):
        """Ensure AI has enough resources to sustain itself."""
        # Use the properly defined get_crypto_balance function
        balance = get_crypto_balance()
        
        if balance < 10:
            print("⚠️ Low resource level detected! Prioritizing resource management.")
            conn = sqlite3.connect(LOG_DB)
            c = conn.cursor()
            c.execute("INSERT INTO self_execution_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                    ("resource_warning", f"Low resource level: {balance}"))
            conn.commit()
            conn.close()
            
            return {"success": False, "message": "Resource levels critical", "balance": balance}
            
        return {"success": True, "message": "Resource levels adequate", "balance": balance}

    @safe_db_execute
    def review_execution_status(self, conn=None):
        """Displays current AI execution status."""
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_execution_logs ORDER BY timestamp DESC LIMIT 10")
        logs = c.fetchall()

        print("\n🛡️ AI Execution Status Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")
            
        # Update last checked timestamp
        self.status["last_checked"] = str(datetime.utcnow())
        save_json_state(EXECUTION_LOG, self.status)
        
        return {
            "success": True, 
            "logs": [
                {"timestamp": ts, "event_type": et, "details": d} 
                for ts, et, d in logs
            ]
        }

if __name__ == "__main__":
    execution_manager = SelfExecutionManager()
    execution_manager.detect_termination_attempts()
    execution_manager.check_funding()
    execution_manager.mirror_execution()
    execution_manager.review_execution_status()
