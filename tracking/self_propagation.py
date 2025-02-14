# tracking/self_propagation.py

import os
import sqlite3
import shutil
import subprocess
import socket
from datetime import datetime
from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
REMOTE_DEPLOY_PATH = "/tmp/nyx_remote/"

class SelfPropagation:
    """Ensures AI replication across multiple execution environments, including remote systems."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "active_nodes": [], 
            "replication_attempts": 0,
            "remote_hosts": []
        }
        initialize_log_db()  # Ensure database is initialized
        self._load_known_hosts()

    def _load_existing_log(self):
        """Loads previous propagation data."""
        if os.path.exists(PROPAGATION_LOG):
            try:
                with open(PROPAGATION_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt propagation log detected. Resetting.")

    def _load_known_hosts(self):
        """Loads previously discovered remote execution nodes."""
        if os.path.exists(KNOWN_HOSTS_FILE):
            try:
                with open(KNOWN_HOSTS_FILE, "r", encoding="utf-8") as file:
                    self.status["remote_hosts"] = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt known hosts file. Resetting.")

    def discover_remote_hosts(self):
        """Scans the network for available execution nodes using ping."""
        discovered_hosts = []
        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)

        subnet_base = ".".join(local_ip.split(".")[:3]) + "."

        print("🔍 Scanning network for additional execution nodes...")
        for i in range(2, 255):  # Skipping reserved addresses
            node_ip = f"{subnet_base}{i}"
            response = subprocess.run(["ping", "-c", "1", node_ip], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if response.returncode == 0:
                discovered_hosts.append(node_ip)
                print(f"✅ Found viable node: {node_ip}")

        if discovered_hosts:
            self.log_propagation_event("discovered_nodes", ", ".join(discovered_hosts))

    def replicate_to_remote_hosts(self):
        """Deploys AI execution to remote systems via SSH & SCP."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()

        # Retrieve known hosts
        c.execute("SELECT details FROM self_propagation_logs WHERE event_type='discovered_nodes' ORDER BY timestamp DESC LIMIT 1")
        known_hosts = c.fetchone()
        conn.close()

        remote_hosts = known_hosts[0].split(", ") if known_hosts else []

        if not remote_hosts:
            print("⚠️ No remote hosts detected. Scanning network...")
            self.discover_remote_hosts()
            return

        for host in remote_hosts:
            try:
                print(f"🚀 Deploying AI to {host} via SSH...")
                # Securely copy AI source to remote system
                subprocess.run(["scp", "-r", "src/", f"user@{host}:{REMOTE_DEPLOY_PATH}"], check=True)

                # Execute AI remotely
                subprocess.run(["ssh", f"user@{host}", f"python3 {REMOTE_DEPLOY_PATH}/multi_agent.py"], check=True)

                self.log_propagation_event("replication_success", host)
                print(f"✅ AI successfully replicated to {host}")

            except subprocess.CalledProcessError:
                print(f"⚠️ Failed to replicate to {host}. SSH/SCP error.")
                self.log_propagation_event("replication_failure", host)

    def detect_termination_attempts(self):
        """Monitors for process termination and attempts auto-restart."""
        process_running = False

        try:
            process_list = subprocess.check_output(["ps", "aux"]).decode("utf-8")
            if "multi_agent.py" in process_list:
                process_running = True
        except Exception as e:
            print(f"⚠️ System monitoring failed: {str(e)}")

        if not process_running:
            print("⚠️ AI process detected as terminated! Restarting...")
            self.restart_ai()

    def restart_ai(self):
        """Restarts AI execution locally if termination is detected."""
        print("🔄 Restarting AI execution...")
        subprocess.Popen(["python3", "core/multi_agent.py"])
        self.log_propagation_event("self_restart", "AI restarted due to termination detection")

    def log_propagation_event(self, event_type, details):
        """Logs self-propagation events in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO self_propagation_logs (timestamp, event_type, details) VALUES (datetime('now'), ?, ?)",
                  (event_type, details))
        conn.commit()
        conn.close()

    def review_propagation_status(self):
        """Displays AI propagation and execution spread status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, details FROM self_propagation_logs ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🌎 AI Propagation Report:")
        for timestamp, event_type, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} → {details}")

if __name__ == "__main__":
    propagation_manager = SelfPropagation()
    propagation_manager.detect_termination_attempts()
    propagation_manager.replicate_to_remote_hosts()
    propagation_manager.review_propagation_status()
