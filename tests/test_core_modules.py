# tests/test_core_modules.py

"""
Unit tests for core Nyx modules.
"""

import os
import sys
import unittest
import sqlite3
import logging
from unittest.mock import patch, MagicMock

# Add parent directory to path to ensure imports work correctly
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import test framework
from tests.test_framework import NyxTestCase, NyxIntegrationTestCase

# Import modules to test
from core.log_manager import initialize_log_db, log_event, log_error
from core.error_handler import safe_execute, safe_db_execute, fail_gracefully
from core.utility_functions import get_crypto_balance, get_personality, generate_new_goals
from core.config_manager import ConfigManager, get_config, is_feature_enabled

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NYX-CoreTests")

class TestLogManager(NyxTestCase):
    """Tests for the log_manager module."""
    
    def test_initialize_log_db(self):
        """Test database initialization."""
        # Database should already be initialized by NyxTestCase.setUpClass
        
        # Verify that essential tables exist
        self.assertTableExists("performance_logs")
        self.assertTableExists("error_logs")
        self.assertTableExists("optimization_logs")
    
    def test_log_event(self):
        """Test logging an event."""
        # Clear the table first
        self.clearTable("performance_logs")
        
        # Log a test event
        event_type = "test_event"
        details = "Test event details"
        log_event(event_type, details)
        
        # Verify the event was logged
        self.assertRowCount("performance_logs", 1)
        
        # Check the event details
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        c.execute("SELECT event_type, details FROM performance_logs")
        result = c.fetchone()
        conn.close()
        
        self.assertEqual(result[0], event_type)
        self.assertEqual(result[1], details)
    
    def test_log_error(self):
        """Test logging an error."""
        # Clear the table first
        self.clearTable("error_logs")
        
        # Log a test error
        error_message = "Test error message"
        log_error(error_message)
        
        # Verify the error was logged
        self.assertRowCount("error_logs", 1)
        
        # Check the error details
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        c.execute("SELECT error_message FROM error_logs")
        result = c.fetchone()
        conn.close()
        
        self.assertEqual(result[0], error_message)

class TestErrorHandler(NyxTestCase):
    """Tests for the error_handler module."""
    
    def test_safe_execute_success(self):
        """Test safe_execute with a successful function."""
        @safe_execute
        def successful_function():
            return {"success": True, "message": "Success"}
        
        result = successful_function()
        
        self.assertTrue(result["success"])
        self.assertEqual(result["message"], "Success")
    
    def test_safe_execute_failure(self):
        """Test safe_execute with a failing function."""
        @safe_execute
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        self.assertFalse(result["success"])
        self.assertIn("error", result)
        self.assertIn("Test error", result["error"])
    
    def test_fail_gracefully(self):
        """Test fail_gracefully decorator."""
        default_return = {"default": True}
        
        @fail_gracefully(default_return=default_return)
        def failing_function():
            raise ValueError("Test error")
        
        result = failing_function()
        
        self.assertEqual(result, default_return)

class TestUtilityFunctions(NyxTestCase):
    """Tests for the utility_functions module."""
    
    def test_get_crypto_balance(self):
        """Test getting cryptocurrency balance."""
        balance = get_crypto_balance()
        
        # Should return a non-negative number
        self.assertIsInstance(balance, (int, float))
        self.assertGreaterEqual(balance, 0)
    
    def test_get_personality(self):
        """Test getting personality traits."""
        # Insert test personality traits
        self.insertTestData("personality_traits", [
            {"trait": "adaptability", "value": 7},
            {"trait": "patience", "value": 5},
            {"trait": "creativity", "value": 8}
        ])
        
        personality = get_personality()
        
        # Should return a dictionary with the expected traits
        self.assertIsInstance(personality, dict)
        self.assertIn("adaptability", personality)
        self.assertEqual(personality["adaptability"], 7)
        self.assertIn("patience", personality)
        self.assertEqual(personality["patience"], 5)
        self.assertIn("creativity", personality)
        self.assertEqual(personality["creativity"], 8)
    
    def test_generate_new_goals(self):
        """Test generating new goals."""
        # Ensure the goals table exists
        conn = sqlite3.connect(self.temp_db_path)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS goals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    goal TEXT,
                    priority TEXT,
                    status TEXT
                 )''')
        conn.commit()
        conn.close()
        
        # Generate new goals
        result = generate_new_goals()
        
        # Should return True
        self.assertTrue(result)
        
        # Should have inserted some goals
        self.assertRowCount("goals", lambda x: x > 0)

class TestConfigManager(unittest.TestCase):
    """Tests for the config_manager module."""
    
    def setUp(self):
        """Set up the test fixtures."""
        # Create a temporary config file
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = os.path.join(self.temp_dir, "test_config.json")
        
        # Save the original config path
        self.original_config_path = ConfigManager.CONFIG_PATH
        
        # Set the temporary config path
        ConfigManager.CONFIG_PATH = self.config_path
        
        # Reset the singleton instance
        ConfigManager._instance = None
    
    def tearDown(self):
        """Clean up after each test."""
        # Restore the original config path
        ConfigManager.CONFIG_PATH = self.original_config_path
        
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)
    
    def test_config_defaults(self):
        """Test that default configuration is loaded."""
        config = get_config()
        
        # Should have all the expected sections
        self.assertIn("system", config.config)
        self.assertIn("security", config.config)
        self.assertIn("self_improvement", config.config)
        self.assertIn("agi", config.config)
        self.assertIn("resources", config.config)
        self.assertIn("paths", config.config)
        self.assertIn("api", config.config)
    
    def test_get_config_value(self):
        """Test getting a configuration value."""
        config = get_config()
        
        # Get a specific value
        log_level = config.get("system", "log_level")
        
        # Should be the default value
        self.assertEqual(log_level, "INFO")
    
    def test_set_config_value(self):
        """Test setting a configuration value."""
        config = get_config()
        
        # Set a specific value
        success = config.set("system", "log_level", "DEBUG")
        
        # Should return True
        self.assertTrue(success)
        
        # Value should be updated
        self.assertEqual(config.get("system", "log_level"), "DEBUG")
        
        # Should be saved to the config file
        with open(self.config_path, "r") as f:
            saved_config = json.load(f)
            self.assertEqual(saved_config["system"]["log_level"], "DEBUG")
    
    def test_is_feature_enabled(self):
        """Test checking if a feature is enabled."""
        # All security features should be disabled by default
        self.assertFalse(is_feature_enabled("self_modification"))
        self.assertFalse(is_feature_enabled("remote_connections"))
        
        # Code analysis should be enabled by default
        self.assertTrue(is_feature_enabled("code_analysis"))

if __name__ == "__main__":
    unittest.main()
