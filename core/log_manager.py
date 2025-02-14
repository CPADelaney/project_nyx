# core/log_manager.py

import sqlite3
import os
from datetime import datetime

LOG_DB = "logs/ai_logs.db"

def initialize_log_db():
    """Creates the AI log database if it doesn't exist."""
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    
    # **Create tables if they don’t exist**
    c.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    event_type TEXT,
                    details TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS optimization_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    function_name TEXT,
                    execution_time REAL,
                    success INTEGER
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    error_message TEXT
                 )''')

    conn.commit()
    conn.close()

def log_event(event_type, details):
    """Logs a general AI event."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    c.execute("INSERT INTO performance_logs (timestamp, event_type, details) VALUES (?, ?, ?)", 
              (timestamp, event_type, details))
    conn.commit()
    conn.close()

def log_optimization(function_name, execution_time, success):
    """Logs function execution time and optimization success."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    c.execute("INSERT INTO optimization_logs (timestamp, function_name, execution_time, success) VALUES (?, ?, ?, ?)",
              (timestamp, function_name, execution_time, success))
    conn.commit()
    conn.close()

def log_error(error_message):
    """Logs errors encountered during execution."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    timestamp = datetime.utcnow().isoformat()
    c.execute("INSERT INTO error_logs (timestamp, error_message) VALUES (?, ?)", 
              (timestamp, error_message))
    conn.commit()
    conn.close()

# **Initialize Database on Import**
initialize_log_db()
