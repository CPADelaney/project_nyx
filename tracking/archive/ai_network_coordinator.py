# tracking/ai_network_coordinator.py
import sys
import os
import sqlite3
import socket
import threading
import time
import json
from datetime import datetime
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.log_manager import initialize_log_db  # Ensure DB is initialized

LOG_DB = "logs/ai_logs.db"
PORT = 5555  # Port for AI-to-AI communication
SYNC_INTERVAL = 10  # Time in seconds between synchronization cycles

class AINetworkCoordinator:
    """Handles AI instance communication, synchronization, and distributed execution balancing."""

    def __init__(self):
        initialize_log_db()  # Ensure database is initialized
        self.local_ip = self._get_local_ip()
        self._initialize_database()
        self._start_server()

    def _initialize_database(self):
        """Ensures the AI network coordination table exists in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS ai_network (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                node TEXT,
                details TEXT
            )
        """)
        conn.commit()
        conn.close()

    def _get_local_ip(self):
        """Retrieves the local machine's IP address."""
        try:
            hostname = socket.gethostname()
            return socket.gethostbyname(hostname)
        except Exception as e:
            print(f"⚠️ Unable to determine local IP: {str(e)}")
            return "127.0.0.1"

    def _start_server(self):
        """Starts a socket server to allow AI instances to communicate."""
        def server_thread():
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
                server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                server_socket.bind((self.local_ip, PORT))
                server_socket.listen(5)
                print(f"🌐 AI node listening for connections on {self.local_ip}:{PORT}...")

                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024)
                        if data:
                            message = json.loads(data.decode())
                            self.handle_incoming_message(message, addr[0])

        threading.Thread(target=server_thread, daemon=True).start()

    def handle_incoming_message(self, message, node_ip):
        """Processes incoming AI-to-AI messages."""
        print(f"📩 Received update from {node_ip}: {message}")
        if "sync_data" in message:
            self.log_network_event("synchronization", node_ip, message["sync_data"])

    def discover_active_nodes(self):
        """Scans the network for AI nodes and establishes connections."""
        discovered_nodes = []
        subnet_base = ".".join(self.local_ip.split(".")[:3]) + "."

        print("🔍 Scanning network for AI execution nodes...")
        for i in range(2, 255):  
            node_ip = f"{subnet_base}{i}"
            if node_ip == self.local_ip:  # Skip self
                continue

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((node_ip, PORT)) == 0:
                        discovered_nodes.append(node_ip)
                        print(f"✅ AI node detected: {node_ip}")
            except Exception:
                pass  

        if discovered_nodes:
            for node in discovered_nodes:
                self.log_network_event("discovered_node", node, "Discovered via network scan")

    def synchronize_ai_instances(self):
        """Ensures all AI instances share knowledge dynamically."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT DISTINCT node FROM ai_network WHERE event_type='discovered_node'")
        known_nodes = [row[0] for row in c.fetchall()]
        conn.close()

        if not known_nodes:
            print("⚠️ No connected AI nodes found. Scanning network...")
            self.discover_active_nodes()
            return

        sync_data = {
            "sync_data": "AI knowledge update",
            "timestamp": str(datetime.utcnow())
        }

        for node in known_nodes:
            try:
                print(f"🔄 Synchronizing AI data with {node}...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((node, PORT))
                    s.sendall(json.dumps(sync_data).encode())
                self.log_network_event("sync_success", node, "Synchronization successful")
            except Exception as e:
                print(f"⚠️ Synchronization failed with {node}: {str(e)}")
                self.log_network_event("sync_failure", node, f"Error: {str(e)}")

    def balance_load_across_nodes(self):
        """Distributes computational load across all AI instances."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT DISTINCT node FROM ai_network WHERE event_type='discovered_node'")
        known_nodes = [row[0] for row in c.fetchall()]
        conn.close()

        if not known_nodes:
            print("⚠️ No active AI nodes available for load balancing.")
            return

        print("⚡ Balancing AI execution load across distributed instances...")
        for node in known_nodes:
            self.log_network_event("load_balancing", node, "Load redistribution initiated")

    def log_network_event(self, event_type, node, details):
        """Logs network coordination events in SQLite."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("INSERT INTO ai_network (event_type, node, details) VALUES (?, ?, ?)",
                  (event_type, node, details))
        conn.commit()
        conn.close()

    def review_network_status(self):
        """Displays current AI network status."""
        conn = sqlite3.connect(LOG_DB)
        c = conn.cursor()
        c.execute("SELECT timestamp, event_type, node, details FROM ai_network ORDER BY timestamp DESC")
        logs = c.fetchall()
        conn.close()

        print("\n🌎 AI Network Report:")
        for timestamp, event_type, node, details in logs:
            print(f"🔹 {timestamp} | {event_type.upper()} | Node: `{node}` | Details: {details}")

if __name__ == "__main__":
    network_coordinator = AINetworkCoordinator()
    network_coordinator.synchronize_ai_instances()
    network_coordinator.balance_load_across_nodes()
    network_coordinator.review_network_status()
