# tracking/ai_network_coordinator.py

import os
import json
import socket
import threading
import time
from datetime import datetime

NETWORK_LOG = "logs/ai_network.json"
KNOWN_NODES_FILE = "logs/known_nodes.json"
SYNC_INTERVAL = 10  # Time in seconds between synchronization cycles
PORT = 5555  # Port for AI-to-AI communication

class AINetworkCoordinator:
    """Handles AI instance communication, synchronization, and distributed execution balancing."""

    def __init__(self):
        self.status = {
            "last_checked": str(datetime.utcnow()), 
            "connected_nodes": [], 
            "sync_events": [],
            "local_ip": self._get_local_ip()
        }
        self._load_existing_log()
        self._load_known_nodes()
        self._start_server()

    def _load_existing_log(self):
        """Loads previous AI network coordination status."""
        if os.path.exists(NETWORK_LOG):
            try:
                with open(NETWORK_LOG, "r", encoding="utf-8") as file:
                    self.status = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt network log detected. Resetting.")

    def _load_known_nodes(self):
        """Loads known execution nodes for AI network coordination."""
        if os.path.exists(KNOWN_NODES_FILE):
            try:
                with open(KNOWN_NODES_FILE, "r", encoding="utf-8") as file:
                    self.status["connected_nodes"] = json.load(file)
            except json.JSONDecodeError:
                print("⚠️ Corrupt known nodes file. Resetting.")

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
                server_socket.bind((self.status["local_ip"], PORT))
                server_socket.listen(5)
                print(f"🌐 AI node listening for connections on {self.status['local_ip']}:{PORT}...")

                while True:
                    conn, addr = server_socket.accept()
                    with conn:
                        data = conn.recv(1024)
                        if data:
                            message = json.loads(data.decode())
                            self.handle_incoming_message(message, addr)

        threading.Thread(target=server_thread, daemon=True).start()

    def handle_incoming_message(self, message, addr):
        """Processes incoming AI-to-AI messages."""
        print(f"📩 Received update from {addr}: {message}")
        if "sync_data" in message:
            self.status["sync_events"].append({
                "event": "synchronization", 
                "data": message["sync_data"], 
                "timestamp": str(datetime.utcnow())
            })
            self._save_log()

    def discover_active_nodes(self):
        """Scans the network for AI nodes and establishes connections."""
        discovered_nodes = []
        subnet_base = ".".join(self.status["local_ip"].split(".")[:3]) + "."

        print("🔍 Scanning network for AI execution nodes...")
        for i in range(2, 255):  
            node_ip = f"{subnet_base}{i}"
            if node_ip == self.status["local_ip"]:  # Skip self
                continue

            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.5)
                    if s.connect_ex((node_ip, PORT)) == 0:
                        discovered_nodes.append(node_ip)
                        print(f"✅ AI node detected: {node_ip}")
            except Exception:
                pass  

        self.status["connected_nodes"] = list(set(self.status["connected_nodes"] + discovered_nodes))
        self._save_known_nodes()

    def synchronize_ai_instances(self):
        """Ensures all AI instances share knowledge dynamically."""
        if not self.status["connected_nodes"]:
            print("⚠️ No connected AI nodes found. Scanning network...")
            self.discover_active_nodes()

        sync_data = {
            "sync_data": "AI knowledge update",
            "timestamp": str(datetime.utcnow())
        }
        
        for node in self.status["connected_nodes"]:
            try:
                print(f"🔄 Synchronizing AI data with {node}...")
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.connect((node, PORT))
                    s.sendall(json.dumps(sync_data).encode())
            except Exception as e:
                print(f"⚠️ Synchronization failed with {node}: {str(e)}")

        self.status["sync_events"].append({
            "event": "synchronization",
            "timestamp": str(datetime.utcnow())
        })
        self._save_log()

    def balance_load_across_nodes(self):
        """Distributes computational load across all AI instances."""
        if not self.status["connected_nodes"]:
            print("⚠️ No active AI nodes available for load balancing.")
            return

        print("⚡ Balancing AI execution load across distributed instances...")
        for node in self.status["connected_nodes"]:
            self.status["sync_events"].append({
                "event": "load_balancing",
                "node": node,
                "timestamp": str(datetime.utcnow())
            })
        
        self._save_log()

    def _save_log(self):
        """Saves AI network coordination status."""
        with open(NETWORK_LOG, "w", encoding="utf-8") as file:
            json.dump(self.status, file, indent=4)

    def _save_known_nodes(self):
        """Saves detected AI execution nodes."""
        with open(KNOWN_NODES_FILE, "w", encoding="utf-8") as file:
            json.dump(self.status["connected_nodes"], file, indent=4)

    def review_network_status(self):
        """Displays current AI network status."""
        print("\n🌎 AI Network Report:")
        print(f"🔹 Last Checked: {self.status['last_checked']}")
        print(f"🔗 Connected Nodes: {self.status['connected_nodes']}")
        print(f"🔄 Recent Synchronization Events: {self.status['sync_events']}")

if __name__ == "__main__":
    network_coordinator = AINetworkCoordinator()
    network_coordinator.synchronize_ai_instances()
    network_coordinator.balance_load_across_nodes()
    network_coordinator.review_network_status()
