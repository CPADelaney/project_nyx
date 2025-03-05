# tests/test_framework.py

"""
Unit testing framework for the Nyx codebase.
This module provides the base classes and utilities for testing Nyx components.
"""

import os
import sys
import unittest
import sqlite3
import shutil
import json
import logging
from datetime import datetime
import tempfile

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import core modules
from core.log_manager import LOG_DB

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/test_framework.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-TestFramework")

class NyxTestCase(unittest.TestCase):
    """Base test case for Nyx tests with database isolation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the class-level test fixtures."""
        # Create a temporary directory for the test database
        cls.temp_dir = tempfile.mkdtemp()
        
        # Save the original database path
        cls.original_db_path = LOG_DB
        
        # Create a temporary database path
        cls.temp_db_path = os.path.join(cls.temp_dir, "test_ai_logs.db")
        
        # Override the database path in the log_manager module
        from core import log_manager
        log_manager.LOG_DB = cls.temp_db_path
        
        # Initialize the test database
        log_manager.initialize_log_db()
        
        logger.info(f"Test database initialized at {cls.temp_db_path}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in the class have run."""
        # Restore the original database path
        from core import log_manager
        log_manager.LOG_DB = cls.original_db_path
        
        # Remove the temporary directory
        shutil.rmtree(cls.temp_dir)
        
        logger.info("Test environment cleaned up")
    
    def setUp(self):
        """Set up the test fixtures before each test method runs."""
        pass
    
    def tearDown(self):
        """Clean up after each test method runs."""
        pass
    
    def assertTableExists(self, table_name):
        """Assert that a table exists in the database."""
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        
        c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
        exists = c.fetchone() is not None
        
        conn.close()
        
        self.assertTrue(exists, f"Table {table_name} does not exist")
    
    def assertRowCount(self, table_name, expected_count):
        """Assert the number of rows in a table."""
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        
        c.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = c.fetchone()[0]
        
        conn.close()
        
        self.assertEqual(count, expected_count, f"Expected {expected_count} rows in {table_name}, got {count}")
    
    def insertTestData(self, table_name, data):
        """Insert test data into a table."""
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        
        if isinstance(data, dict):
            columns = ", ".join(data.keys())
            placeholders = ", ".join(["?"] * len(data))
            values = tuple(data.values())
            
            c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        elif isinstance(data, list):
            for row in data:
                columns = ", ".join(row.keys())
                placeholders = ", ".join(["?"] * len(row))
                values = tuple(row.values())
                
                c.execute(f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})", values)
        
        conn.commit()
        conn.close()
    
    def clearTable(self, table_name):
        """Clear all data from a table."""
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        
        c.execute(f"DELETE FROM {table_name}")
        
        conn.commit()
        conn.close()

class NyxIntegrationTestCase(unittest.TestCase):
    """Base test case for Nyx integration tests with temporary filesystem."""
    
    @classmethod
    def setUpClass(cls):
        """Set up the class-level test fixtures."""
        # Create a temporary directory for test files
        cls.temp_dir = tempfile.mkdtemp()
        
        # Create required directories
        os.makedirs(os.path.join(cls.temp_dir, "logs"), exist_ok=True)
        os.makedirs(os.path.join(cls.temp_dir, "src"), exist_ok=True)
        os.makedirs(os.path.join(cls.temp_dir, "core"), exist_ok=True)
        
        # Save the original working directory
        cls.original_cwd = os.getcwd()
        
        # Change to the temporary directory
        os.chdir(cls.temp_dir)
        
        logger.info(f"Integration test environment initialized at {cls.temp_dir}")
    
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests in the class have run."""
        # Restore the original working directory
        os.chdir(cls.original_cwd)
        
        # Remove the temporary directory
        shutil.rmtree(cls.temp_dir)
        
        logger.info("Integration test environment cleaned up")
    
    def setUp(self):
        """Set up the test fixtures before each test method runs."""
        pass
    
    def tearDown(self):
        """Clean up after each test method runs."""
        pass
    
    def createTestFile(self, path, content):
        """Create a test file with the given content."""
        full_path = os.path.join(self.temp_dir, path)
        
        # Create parent directories if they don't exist
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, "w") as f:
            f.write(content)
            
        return full_path
    
    def fileExists(self, path):
        """Check if a file exists."""
        full_path = os.path.join(self.temp_dir, path)
        return os.path.exists(full_path)
    
    def readTestFile(self, path):
        """Read the content of a test file."""
        full_path = os.path.join(self.temp_dir, path)
        
        with open(full_path, "r") as f:
            return f.read()

def run_tests(test_module=None):
    """Run all tests in the specified module or all test modules."""
    if test_module:
        suite = unittest.defaultTestLoader.loadTestsFromModule(test_module)
    else:
        start_dir = os.path.join(os.path.dirname(__file__))
        suite = unittest.defaultTestLoader.discover(start_dir, pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result

if __name__ == "__main__":
    # If a specific test module is specified, run only that module
    if len(sys.argv) > 1:
        module_name = sys.argv[1]
        
        try:
            # Import the module
            module = __import__(module_name)
            
            # Run the tests
            result = run_tests(module)
            
            # Exit with the appropriate status code
            sys.exit(not result.wasSuccessful())
        except ImportError:
            print(f"Cannot import module: {module_name}")
            sys.exit(1)
    else:
        # Run all tests
        result = run_tests()
        
        # Exit with the appropriate status code
        sys.exit(not result.wasSuccessful())
