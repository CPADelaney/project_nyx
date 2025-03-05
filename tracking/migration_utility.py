# tracking/migration_utility.py

"""
Migration utility to help transition from the old tracking modules to the new consolidated system.
"""

import os
import sys
import sqlite3
import json
import logging
import shutil
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/migration.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-Migration")

# Database path
LOG_DB = "logs/ai_logs.db"

# Old tracking modules and their table names
OLD_MODULES = {
    "ai_autonomous_expansion.py": "ai_autonomous_expansion",
    "ai_network_coordinator.py": "ai_network",
    "ai_scaling.py": "ai_scaling",
    "bottleneck_detector.py": "optimization_logs",
    "feature_expansion.py": "feature_expansion",
    "goal_generator.py": "goals",
    "intelligence_expansion.py": "intelligence_expansion",
    "meta_learning.py": "meta_learning",
    "performance_tracker.py": "performance_logs",
    "redundancy_manager.py": "redundancy_logs",
    "self_execution.py": "self_execution_logs",
    "self_healing.py": "self_healing_logs",
    "self_infrastructure_optimization.py": "infrastructure_optimizations",
    "self_preservation.py": "self_preservation_logs",
    "self_propagation.py": "self_propagation_logs",
    "self_sustainability.py": "self_sustainability_logs"
}

# JSON state files
JSON_FILES = [
    "logs/execution_status.json",
    "logs/propagation_status.json",
    "logs/infrastructure_status.json",
    "logs/self_healing_status.json",
    "logs/intelligence_expansion.json",
    "logs/redundancy_status.json",
    "logs/performance_history.json"
]

class MigrationUtility:
    """
    Utility for migrating from old tracking modules to the new consolidated system.
    """
    
    def __init__(self):
        """Initialize the migration utility."""
        self.conn = sqlite3.connect(LOG_DB)
        self.conn.row_factory = sqlite3.Row
        
        # Create backup of database before migration
        self._backup_database()
        
        # Create the new tables if they don't exist
        self._create_new_tables()
        
        logger.info("Migration utility initialized")
    
    def _backup_database(self) -> None:
        """Create a backup of the database before migration."""
        backup_dir = "logs/backups"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(backup_dir, f"ai_logs_before_migration_{timestamp}.db")
        
        # Close the connection to copy the file
        self.conn.close()
        
        # Copy the database file
        if os.path.exists(LOG_DB):
            shutil.copy2(LOG_DB, backup_path)
            logger.info(f"Database backed up to {backup_path}")
        
        # Reconnect
        self.conn = sqlite3.connect(LOG_DB)
        self.conn.row_factory = sqlite3.Row
    
    def _create_new_tables(self) -> None:
        """Create the new tables for the consolidated tracking system."""
        c = self.conn.cursor()
        
        # Create tracking_events table
        c.execute('''
            CREATE TABLE IF NOT EXISTS tracking_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                component TEXT NOT NULL,
                event_type TEXT NOT NULL,
                details TEXT,
                severity TEXT DEFAULT 'info'
            )
        ''')
        
        # Create indexes
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_tracking_events_component 
            ON tracking_events(component)
        ''')
        
        c.execute('''
            CREATE INDEX IF NOT EXISTS idx_tracking_events_type 
            ON tracking_events(event_type)
        ''')
        
        # Create performance_metrics table
        c.execute('''
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                metric_name TEXT NOT NULL,
                metric_value REAL,
                units TEXT
            )
        ''')
        
        # Create system_backups table
        c.execute('''
            CREATE TABLE IF NOT EXISTS system_backups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                backup_type TEXT NOT NULL,
                path TEXT NOT NULL,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Create improvement_goals table
        c.execute('''
            CREATE TABLE IF NOT EXISTS improvement_goals (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                goal TEXT NOT NULL,
                priority TEXT DEFAULT 'medium',
                status TEXT DEFAULT 'pending',
                completed_timestamp TEXT
            )
        ''')
        
        self.conn.commit()
        logger.info("New tables created")
    
    def migrate_data(self) -> Dict[str, Any]:
        """
        Migrate data from old tables to new tables.
        
        Returns:
            Dict: Migration results
        """
        results = {
            "tables_migrated": 0,
            "rows_migrated": 0,
            "errors": 0
        }
        
        try:
            # Check which old tables exist
            c = self.conn.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            existing_tables = [row["name"] for row in c.fetchall()]
            
            # Migrate data from each existing old table
            for old_module, old_table in OLD_MODULES.items():
                if old_table in existing_tables:
                    try:
                        rows = self._migrate_table(old_table)
                        results["tables_migrated"] += 1
                        results["rows_migrated"] += rows
                        logger.info(f"Migrated {rows} rows from {old_table}")
                    except Exception as e:
                        logger.error(f"Error migrating table {old_table}: {str(e)}")
                        results["errors"] += 1
            
            # Migrate JSON state files
            for json_file in JSON_FILES:
                if os.path.exists(json_file):
                    try:
                        self._migrate_json_file(json_file)
                        logger.info(f"Migrated JSON file {json_file}")
                    except Exception as e:
                        logger.error(f"Error migrating JSON file {json_file}: {str(e)}")
                        results["errors"] += 1
            
            logger.info(f"Migration completed: {results['tables_migrated']} tables, {results['rows_migrated']} rows")
            return results
            
        except Exception as e:
            logger.error(f"Error during migration: {str(e)}")
            return {
                "tables_migrated": results["tables_migrated"],
                "rows_migrated": results["rows_migrated"],
                "errors": results["errors"] + 1,
                "error_message": str(e)
            }
    
    def _migrate_table(self, old_table: str) -> int:
        """
        Migrate data from an old table to the new tables.
        
        Args:
            old_table: Name of the old table
            
        Returns:
            int: Number of rows migrated
        """
        c = self.conn.cursor()
        
        # Get data from the old table
        try:
            c.execute(f"SELECT * FROM {old_table}")
            rows = c.fetchall()
        except sqlite3.OperationalError:
            logger.warning(f"Table {old_table} does not exist or has no rows")
            return 0
        
        # Map to appropriate new table based on old table name
        rows_migrated = 0
        
        # Process each row
        for row in rows:
            # Convert row to dictionary
            row_dict = {key: row[key] for key in row.keys()}
            
            # Determine which component the data belongs to
            if old_table in ["optimization_logs", "performance_logs"]:
                # Performance metrics
                self._migrate_performance_metric(row_dict, old_table)
                rows_migrated += 1
            elif old_table in ["redundancy_logs", "self_healing_logs", "self_execution_logs", "self_preservation_logs"]:
                # Resilience events
                self._migrate_resilience_event(row_dict, old_table)
                rows_migrated += 1
            elif old_table in ["ai_scaling", "ai_network", "infrastructure_optimizations", "self_propagation_logs", "self_sustainability_logs"]:
                # Scaling events
                self._migrate_scaling_event(row_dict, old_table)
                rows_migrated += 1
            elif old_table in ["feature_expansion", "goals", "intelligence_expansion", "meta_learning"]:
                # Improvement events
                self._migrate_improvement_event(row_dict, old_table)
                rows_migrated += 1
            else:
                # Generic events
                self._migrate_generic_event(row_dict, old_table)
                rows_migrated += 1
        
        return rows_migrated
    
    def _migrate_performance_metric(self, row: Dict[str, Any], old_table: str) -> None:
        """
        Migrate a performance metric.
        
        Args:
            row: The row to migrate
            old_table: Name of the old table
        """
        c = self.conn.cursor()
        
        if old_table == "performance_logs":
            # Extract data
            timestamp = row.get("timestamp")
            event_type = row.get("event_type")
            details = row.get("details")
            
            if event_type == "execution_time":
                # Extract execution time from details
                try:
                    time_value = float(details.replace(" seconds", ""))
                    
                    # Insert into performance_metrics
                    c.execute("""
                        INSERT INTO performance_metrics 
                        (timestamp, metric_name, metric_value, units) 
                        VALUES (?, ?, ?, ?)
                    """, (timestamp, "execution_time", time_value, "seconds"))
                    
                    # Also log as event
                    c.execute("""
                        INSERT INTO tracking_events 
                        (timestamp, component, event_type, details, severity) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (timestamp, "monitoring", "execution_time_measured", details, "info"))
                except (ValueError, TypeError):
                    # If can't parse as float, just log as event
                    c.execute("""
                        INSERT INTO tracking_events 
                        (timestamp, component, event_type, details, severity) 
                        VALUES (?, ?, ?, ?, ?)
                    """, (timestamp, "monitoring", event_type, details, "info"))
            else:
                # Generic performance event
                c.execute("""
                    INSERT INTO tracking_events 
                    (timestamp, component, event_type, details, severity) 
                    VALUES (?, ?, ?, ?, ?)
                """, (timestamp, "monitoring", event_type, details, "info"))
                
        elif old_table == "optimization_logs":
            # Extract data
            timestamp = row.get("timestamp")
            function_name = row.get("function_name")
            execution_time = row.get("execution_time")
            
            if function_name and execution_time:
                # Insert into performance_metrics
                c.execute("""
                    INSERT INTO performance_metrics 
                    (timestamp, metric_name, metric_value, units) 
                    VALUES (?, ?, ?, ?)
                """, (timestamp, f"function_{function_name}", execution_time, "seconds"))
        
        self.conn.commit()
    
    def _migrate_resilience_event(self, row: Dict[str, Any], old_table: str) -> None:
        """
        Migrate a resilience event.
        
        Args:
            row: The row to migrate
            old_table: Name of the old table
        """
        c = self.conn.cursor()
        
        # Extract common fields
        timestamp = row.get("timestamp")
        event_type = row.get("event_type", "unknown")
        details = row.get("details", "")
        
        # Map event types to new format
        if old_table == "redundancy_logs":
            backup_type = row.get("backup_type")
            path = row.get("path")
            
            if backup_type == "local" or backup_type == "cloud":
                # This is a backup event, insert into system_backups
                c.execute("""
                    INSERT INTO system_backups 
                    (timestamp, backup_type, path, status) 
                    VALUES (?, ?, ?, ?)
                """, (timestamp, backup_type, path, "active"))
            
            # Also log as tracking event
            severity = "info"
            if "failed" in event_type or "error" in event_type:
                severity = "error"
            elif "warning" in event_type:
                severity = "warning"
                
            c.execute("""
                INSERT INTO tracking_events 
                (timestamp, component, event_type, details, severity) 
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, "resilience", event_type, details, severity))
            
        elif old_table in ["self_healing_logs", "self_execution_logs", "self_preservation_logs"]:
            # Generic resilience events
            severity = "info"
            if "failed" in event_type or "error" in event_type:
                severity = "error"
            elif "warning" in event_type:
                severity = "warning"
                
            c.execute("""
                INSERT INTO tracking_events 
                (timestamp, component, event_type, details, severity) 
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, "resilience", event_type, details, severity))
        
        self.conn.commit()
    
    def _migrate_scaling_event(self, row: Dict[str, Any], old_table: str) -> None:
        """
        Migrate a scaling event.
        
        Args:
            row: The row to migrate
            old_table: Name of the old table
        """
        c = self.conn.cursor()
        
        # Extract common fields
        timestamp = row.get("timestamp")
        event_type = row.get("event_type", "unknown")
        details = row.get("details", "")
        
        severity = "info"
        if "failed" in event_type or "error" in event_type:
            severity = "error"
        elif "warning" in event_type:
            severity = "warning"
            
        c.execute("""
            INSERT INTO tracking_events 
            (timestamp, component, event_type, details, severity) 
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, "scaling", event_type, details, severity))
        
        self.conn.commit()
    
    def _migrate_improvement_event(self, row: Dict[str, Any], old_table: str) -> None:
        """
        Migrate an improvement event.
        
        Args:
            row: The row to migrate
            old_table: Name of the old table
        """
        c = self.conn.cursor()
        
        # Extract common fields
        timestamp = row.get("timestamp")
        
        if old_table == "goals":
            # Migrate goals to improvement_goals
            goal = row.get("goal")
            priority = row.get("priority", "medium")
            status = row.get("status", "pending")
            
            if goal:
                c.execute("""
                    INSERT INTO improvement_goals 
                    (timestamp, goal, priority, status) 
                    VALUES (?, ?, ?, ?)
                """, (timestamp, goal, priority, status))
        else:
            # Generic improvement events
            event_type = row.get("event_type", "unknown")
            details = row.get("details", "")
            
            severity = "info"
            if "failed" in event_type or "error" in event_type:
                severity = "error"
            elif "warning" in event_type:
                severity = "warning"
                
            c.execute("""
                INSERT INTO tracking_events 
                (timestamp, component, event_type, details, severity) 
                VALUES (?, ?, ?, ?, ?)
            """, (timestamp, "improvement", event_type, details, severity))
        
        self.conn.commit()
    
    def _migrate_generic_event(self, row: Dict[str, Any], old_table: str) -> None:
        """
        Migrate a generic event.
        
        Args:
            row: The row to migrate
            old_table: Name of the old table
        """
        c = self.conn.cursor()
        
        # Extract common fields
        timestamp = row.get("timestamp")
        event_type = row.get("event_type", "unknown")
        details = row.get("details", "")
        
        # Determine component based on table name
        component = "tracking_system"  # Default
        
        # Map table names to components
        if "ai_autonomous" in old_table:
            component = "scaling"
        elif "network" in old_table:
            component = "scaling"
        elif "feature" in old_table or "intelligence" in old_table:
            component = "improvement"
        
        severity = "info"
        if "failed" in event_type or "error" in event_type:
            severity = "error"
        elif "warning" in event_type:
            severity = "warning"
            
        c.execute("""
            INSERT INTO tracking_events 
            (timestamp, component, event_type, details, severity) 
            VALUES (?, ?, ?, ?, ?)
        """, (timestamp, component, event_type, details, severity))
        
        self.conn.commit()
    
    def _migrate_json_file(self, json_file: str) -> None:
        """
        Migrate a JSON state file.
        
        Args:
            json_file: Path to the JSON file
        """
        try:
            # Read the JSON file
            with open(json_file, "r") as f:
                data = json.load(f)
            
            # Create backup
            backup_dir = "logs/backups"
            os.makedirs(backup_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"{os.path.basename(json_file)}_{timestamp}.json")
            
            with open(backup_file, "w") as f:
                json.dump(data, f, indent=4)
                
            # Determine component from file name
            component = "tracking_system"  # Default
            if "execution" in json_file:
                component = "resilience"
            elif "propagation" in json_file:
                component = "scaling"
            elif "infrastructure" in json_file:
                component = "scaling"
            elif "healing" in json_file:
                component = "resilience"
            elif "intelligence" in json_file:
                component = "improvement"
            elif "redundancy" in json_file:
                component = "resilience"
            elif "performance" in json_file:
                component = "monitoring"
            
            # Log state data as events
            c = self.conn.cursor()
            
            # Log the overall state
            c.execute("""
                INSERT INTO tracking_events 
                (timestamp, component, event_type, details, severity) 
                VALUES (datetime('now'), ?, ?, ?, ?)
            """, (component, "state_migrated", f"Migrated state from {json_file}", "info"))
            
            self.conn.commit()
            
        except json.JSONDecodeError:
            logger.warning(f"Could not parse JSON file {json_file}")
        except Exception as e:
            logger.error(f"Error migrating JSON file {json_file}: {str(e)}")
            raise
    
    def backup_old_modules(self) -> Dict[str, Any]:
        """
        Create backups of old tracking modules.
        
        Returns:
            Dict: Backup results
        """
        results = {
            "modules_backed_up": 0,
            "errors": 0
        }
        
        backup_dir = "logs/old_tracking_modules"
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        for old_module in OLD_MODULES.keys():
            old_path = os.path.join("tracking", old_module)
            if os.path.exists(old_path):
                try:
                    # Create backup
                    backup_path = os.path.join(backup_dir, f"{old_module}_{timestamp}")
                    shutil.copy2(old_path, backup_path)
                    results["modules_backed_up"] += 1
                    logger.info(f"Backed up {old_path} to {backup_path}")
                except Exception as e:
                    logger.error(f"Error backing up {old_path}: {str(e)}")
                    results["errors"] += 1
        
        return results
    
    def create_migration_report(self) -> Dict[str, Any]:
        """
        Create a migration report.
        
        Returns:
            Dict: Migration report
        """
        c = self.conn.cursor()
        
        # Get counts from new tables
        c.execute("SELECT COUNT(*) FROM tracking_events")
        tracking_events_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM performance_metrics")
        performance_metrics_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM system_backups")
        system_backups_count = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM improvement_goals")
        improvement_goals_count = c.fetchone()[0]
        
        # Summarize by component
        c.execute("SELECT component, COUNT(*) FROM tracking_events GROUP BY component")
        component_counts = {row[0]: row[1] for row in c.fetchall()}
        
        # Summarize by severity
        c.execute("SELECT severity, COUNT(*) FROM tracking_events GROUP BY severity")
        severity_counts = {row[0]: row[1] for row in c.fetchall()}
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "tracking_events": tracking_events_count,
            "performance_metrics": performance_metrics_count,
            "system_backups": system_backups_count,
            "improvement_goals": improvement_goals_count,
            "components": component_counts,
            "severities": severity_counts
        }
        
        # Save report to file
        report_file = "logs/migration_report.json"
        with open(report_file, "w") as f:
            json.dump(report, f, indent=4)
            
        logger.info(f"Migration report saved to {report_file}")
        
        return report
    
    def close(self) -> None:
        """Close database connection."""
        if self.conn:
            self.conn.close()

def run_migration() -> None:
    """Run the migration process."""
    logger.info("Starting migration from old tracking modules to consolidated system")
    
    try:
        # Create migration utility
        migration = MigrationUtility()
        
        # Backup old modules
        backup_results = migration.backup_old_modules()
        logger.info(f"Backed up {backup_results['modules_backed_up']} old modules")
        
        # Migrate data
        migration_results = migration.migrate_data()
        logger.info(f"Migrated {migration_results['tables_migrated']} tables, {migration_results['rows_migrated']} rows")
        
        # Create migration report
        report = migration.create_migration_report()
        logger.info("Migration report created")
        
        # Clean up
        migration.close()
        
        logger.info("Migration completed successfully")
        
        # Print summary
        print("\n=== Migration Summary ===")
        print(f"Backed up {backup_results['modules_backed_up']} old modules")
        print(f"Migrated {migration_results['tables_migrated']} tables, {migration_results['rows_migrated']} rows")
        print(f"Created {report['tracking_events']} tracking events")
        print(f"Created {report['performance_metrics']} performance metrics")
        print(f"Created {report['system_backups']} system backups")
        print(f"Created {report['improvement_goals']} improvement goals")
        print("\nMigration report saved to logs/migration_report.json")
        
    except Exception as e:
        logger.error(f"Migration failed: {str(e)}")
        print(f"\nERROR: Migration failed: {str(e)}")
        print("See logs/migration.log for details")

if __name__ == "__main__":
    run_migration()
