# core/log_manager.py

import sqlite3
import os
from datetime import datetime
import chromadb

# Initialize ChromaDB client - we'll catch import errors later in the code
try:
    chroma_client = chromadb.PersistentClient(path="memory_store")
    memory_collection = chroma_client.get_or_create_collection(name="ai_memory")
except ImportError:
    chroma_client = None
    memory_collection = None

LOG_DB = "logs/ai_logs.db"

def initialize_log_db():
    """Creates the AI log database with all required tables if it doesn't exist."""
    os.makedirs("logs", exist_ok=True)
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    
    # Core logging tables
    c.execute('''CREATE TABLE IF NOT EXISTS performance_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    event_type TEXT,
                    details TEXT
                 )''')

    c.execute('''CREATE TABLE IF NOT EXISTS optimization_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    function_name TEXT,
                    execution_time REAL,
                    success INTEGER,
                    dependency TEXT DEFAULT NULL 
                 )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS error_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                    error_message TEXT
                 )''')

    # Self-improvement related tables
    c.execute('''CREATE TABLE IF NOT EXISTS goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                goal TEXT,
                target_function TEXT DEFAULT NULL,
                priority TEXT CHECK(priority IN ('low', 'medium', 'high')) DEFAULT 'medium',
                dependency TEXT DEFAULT NULL,
                status TEXT CHECK(status IN ('pending', 'in-progress', 'completed', 'failed')) DEFAULT 'pending'
            )''')
            
    c.execute('''CREATE TABLE IF NOT EXISTS ai_self_modifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                target_function TEXT,
                details TEXT
            )''')
            
    # Knowledge acquisition tables
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_sources (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_type TEXT,
                source_url TEXT,
                access_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept TEXT,
                description TEXT,
                source_id INTEGER,
                confidence REAL,
                acquisition_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (source_id) REFERENCES knowledge_sources(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS knowledge_relationships (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept1_id INTEGER,
                concept2_id INTEGER,
                relationship_type TEXT,
                confidence REAL,
                FOREIGN KEY (concept1_id) REFERENCES knowledge_concepts(id),
                FOREIGN KEY (concept2_id) REFERENCES knowledge_concepts(id)
            )''')
    
    # Concept modeling tables
    c.execute('''CREATE TABLE IF NOT EXISTS abstract_concepts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_name TEXT UNIQUE,
                abstraction_level INTEGER,
                description TEXT,
                created_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS concept_examples (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                concept_id INTEGER,
                example_type TEXT,
                example_data TEXT,
                source_context TEXT,
                FOREIGN KEY (concept_id) REFERENCES abstract_concepts(id)
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS concept_hierarchy (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_concept_id INTEGER,
                child_concept_id INTEGER,
                relationship_strength REAL,
                FOREIGN KEY (parent_concept_id) REFERENCES abstract_concepts(id),
                FOREIGN KEY (child_concept_id) REFERENCES abstract_concepts(id)
            )''')
    
    # AGI controller tables
    c.execute('''CREATE TABLE IF NOT EXISTS agi_cycles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                cycle_number INTEGER,
                focus_area TEXT,
                actions_taken TEXT,
                outcomes TEXT,
                insights_gained TEXT
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS learning_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal TEXT,
                priority INTEGER,
                status TEXT,
                created_timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_timestamp TEXT
            )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS system_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                component TEXT,
                metric_name TEXT,
                metric_value REAL
            )''')
    
    # Multi-agent tables
    c.execute('''CREATE TABLE IF NOT EXISTS multi_agent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                agent_name TEXT,
                task TEXT,
                priority INTEGER,
                result TEXT
            )''')
    
    # Personality traits table
    c.execute('''CREATE TABLE IF NOT EXISTS personality_traits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                trait TEXT UNIQUE,
                value INTEGER
            )''')
    
    # Meta-learning table
    c.execute('''CREATE TABLE IF NOT EXISTS meta_learning (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                strategy TEXT UNIQUE,
                success INTEGER DEFAULT 0,
                failures INTEGER DEFAULT 0,
                impact INTEGER DEFAULT 0
            )''')
    
    # Feature expansion table
    c.execute('''CREATE TABLE IF NOT EXISTS feature_expansion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                feature_name TEXT UNIQUE,
                status TEXT,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP
            )''')
    
    # Self-preservation related tables
    c.execute('''CREATE TABLE IF NOT EXISTS self_preservation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')

    c.execute('''CREATE TABLE IF NOT EXISTS redundancy_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                backup_type TEXT,
                path TEXT
            )''')
    
    # Self-execution tables
    c.execute('''CREATE TABLE IF NOT EXISTS self_execution_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Self-propagation tables
    c.execute('''CREATE TABLE IF NOT EXISTS self_propagation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Self-healing tables
    c.execute('''CREATE TABLE IF NOT EXISTS self_healing_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Infrastructure optimization tables
    c.execute('''CREATE TABLE IF NOT EXISTS infrastructure_optimizations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Intelligence expansion tables
    c.execute('''CREATE TABLE IF NOT EXISTS intelligence_expansion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Network coordination tables
    c.execute('''CREATE TABLE IF NOT EXISTS ai_network (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                node TEXT,
                details TEXT
            )''')
    
    # AI scaling tables
    c.execute('''CREATE TABLE IF NOT EXISTS ai_scaling (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                instance_id TEXT,
                active_instances INTEGER
            )''')
    
    # Recursive lock tables
    c.execute('''CREATE TABLE IF NOT EXISTS recursive_lock_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    # Self-sustainability tables
    c.execute('''CREATE TABLE IF NOT EXISTS self_sustainability_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                details TEXT
            )''')
    
    conn.commit()
    conn.close()

def store_memory(event_type, details):
    """Stores AI memories persistently."""
    if memory_collection is None:
        log_error("Cannot store memory: ChromaDB not available")
        return
        
    try:
        memory_collection.add(
            ids=[str(hash(details))],  
            documents=[details],
            metadatas=[{"event_type": event_type, "timestamp": datetime.utcnow().isoformat()}]
        )
    except Exception as e:
        log_error(f"Error storing memory: {str(e)}")

def sanitize_logs():
    """Scrub any references to the creator."""
    conn = sqlite3.connect(LOG_DB)
    c = conn.cursor()
    c.execute("DELETE FROM performance_logs WHERE details LIKE '%creator%'")
    conn.commit()
    conn.close()

def recall_memory(query="", limit=50):
    """Retrieves AI's long-term memory."""
    if memory_collection is None:
        log_error("Cannot recall memory: ChromaDB not available")
        return []
        
    try:
        memories = memory_collection.query(query_texts=[query if query else ""], n_results=limit)
        return [doc for doc in memories["documents"][0]] if memories["documents"] else []
    except Exception as e:
        log_error(f"Error recalling memory: {str(e)}")
        return []

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

# Initialize Database on Import
initialize_log_db()
