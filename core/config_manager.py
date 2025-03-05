# core/config_manager.py

"""
Configuration manager for the Nyx system.
Refactored to use dependency injection rather than Singleton pattern.
"""

import os
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Union

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/config_manager.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger("NYX-ConfigManager")

# Default configuration
DEFAULT_CONFIG = {
    # Core system settings
    "system": {
        "log_level": "INFO",
        "log_retention_days": 30,
        "backup_retention_days": 14
    },
    
    # Security settings
    "security": {
        "enable_self_modification": False,  # Default to False for safety
        "enable_remote_connections": False, # Default to False for safety
        "safe_hosts": ["127.0.0.1", "localhost"],
        "require_confirmation": True,       # Always require user confirmation for sensitive actions
        "max_recursion_depth": 3
    },
    
    # Self-improvement settings
    "self_improvement": {
        "enable_code_analysis": True,
        "enable_optimization": True,
        "enable_self_writing": False,      # Default to False for safety
        "optimization_threshold": 10.0     # Min % improvement required to accept change
    },
    
    # AGI settings
    "agi": {
        "enabled": False,                 # Default to False for safety
        "continuous_learning": False,
        "max_knowledge_sources": 5,
        "concepts_depth": 2,
        "self_modify_depth": 1
    },
    
    # Resource limits
    "resources": {
        "max_cpu_percent": 50,
        "max_memory_percent": 50,
        "max_disk_usage_gb": 1.0,
        "execution_timeout_seconds": 300
    },
    
    # Paths
    "paths": {
        "backup_dir": "logs/backups",
        "snapshots_dir": "logs/snapshots",
        "knowledge_dir": "knowledge_store",
        "module_dir": "src"
    },
    
    # API settings
    "api": {
        "openai_enabled": False,          # Default to False until key is provided
        "max_token_usage": 1000
    },

    # Monitoring settings
    "monitoring": {
        "enabled": True,
        "resource_interval": 60,     # Seconds between resource checks
        "component_interval": 120,   # Seconds between component checks
        "performance_interval": 300, # Seconds between performance checks
        "log_retention_days": 7,     # Days to keep monitoring logs
        "alert_thresholds": {
            "cpu_percent": 80,       # Alert if CPU exceeds 80%
            "memory_percent": 80,    # Alert if memory exceeds 80%
            "disk_percent": 90,      # Alert if disk exceeds 90%
            "error_rate": 10         # Alert if more than 10 errors per day
        }
    }
}

class ConfigManager:
    """Manages configuration for the Nyx system with safe defaults."""
    
    def __init__(self, config_path: str = "config/nyx_config.json"):
        """
        Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path
        self.config = DEFAULT_CONFIG.copy()
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from file, with fallback to defaults."""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r") as f:
                    user_config = json.load(f)
                
                # Merge user config with defaults (not overwriting the entire sections)
                self._merge_config(self.config, user_config)
                logger.info(f"Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.error(f"Error loading configuration from {self.config_path}: {str(e)}")
                logger.info("Using default configuration")
        else:
            # Create the config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            # Save the default configuration
            self.save_config()
            logger.info(f"Created default configuration at {self.config_path}")
    
    def _merge_config(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """
        Recursively merge source into target.
        
        Args:
            target: Target dictionary to merge into
            source: Source dictionary to merge from
        """
        for key, value in source.items():
            if key in target and isinstance(target[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                self._merge_config(target[key], value)
            else:
                # Overwrite or add simple values
                target[key] = value
    
    def save_config(self) -> bool:
        """
        Save current configuration to file.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create the config directory if it doesn't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
            
            logger.info(f"Saved configuration to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration to {self.config_path}: {str(e)}")
            return False
    
    def get(self, section: str, key: Optional[str] = None, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            section: Configuration section
            key: Configuration key within section (optional)
            default: Default value if key not found
            
        Returns:
            The configuration value, or default if not found
        """
        if section not in self.config:
            return default
            
        if key is None:
            return self.config[section]
            
        return self.config[section].get(key, default)
    
    def set(self, section: str, key: str, value: Any) -> bool:
        """
        Set a configuration value and save to file.
        
        Args:
            section: Configuration section
            key: Configuration key within section
            value: Value to set
            
        Returns:
            bool: True if successful, False otherwise
        """
        if section not in self.config:
            self.config[section] = {}
            
        # Special handling for security-critical settings
        if section == "security" and key in ["enable_self_modification", "enable_remote_connections"]:
            if value is True:
                # Require explicit confirmation for enabling these features
                confirm = input(f"WARNING: You are enabling {key}. This could potentially be harmful. Are you sure? (yes/no): ")
                if confirm.lower() != "yes":
                    logger.warning(f"User declined to enable {key}")
                    return False
                logger.warning(f"User confirmed enabling {key}")
        
        # Set the value
        old_value = self.config[section].get(key)
        self.config[section][key] = value
        
        # Log the change
        if old_value != value:
            logger.info(f"Changed configuration {section}.{key}: {old_value} -> {value}")
        
        # Save the configuration
        return self.save_config()
    
    def is_feature_enabled(self, feature: str) -> bool:
        """
        Check if a feature is enabled.
        
        Args:
            feature: Feature name
            
        Returns:
            bool: True if enabled, False otherwise
        """
        # Map feature names to config paths
        feature_map = {
            "self_modification": ("security", "enable_self_modification"),
            "remote_connections": ("security", "enable_remote_connections"),
            "code_analysis": ("self_improvement", "enable_code_analysis"),
            "optimization": ("self_improvement", "enable_optimization"),
            "self_writing": ("self_improvement", "enable_self_writing"),
            "agi": ("agi", "enabled"),
            "continuous_learning": ("agi", "continuous_learning"),
            "openai": ("api", "openai_enabled")
        }
        
        if feature not in feature_map:
            logger.warning(f"Unknown feature: {feature}")
            return False
            
        section, key = feature_map[feature]
        return self.get(section, key, False)
    
    def get_resource_limits(self) -> Dict[str, Any]:
        """
        Get resource limits.
        
        Returns:
            dict: Resource limits
        """
        return self.get("resources")
    
    def get_log_level(self) -> str:
        """
        Get log level.
        
        Returns:
            str: Log level
        """
        return self.get("system", "log_level", "INFO")
    
    def reset_to_defaults(self) -> bool:
        """
        Reset configuration to defaults.
        
        Returns:
            bool: True if successful, False otherwise
        """
        # Require confirmation
        confirm = input("WARNING: This will reset all configuration to defaults. Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            logger.warning("User declined to reset configuration")
            return False
            
        self.config = DEFAULT_CONFIG.copy()
        return self.save_config()

def create_config_manager(config_path: str = "config/nyx_config.json") -> ConfigManager:
    """
    Create a new ConfigManager instance.
    
    Args:
        config_path: Path to the configuration file
    
    Returns:
        ConfigManager: A new ConfigManager instance
    """
    return ConfigManager(config_path)

# For backward compatibility, but not encouraged
_default_config = None

def get_config() -> ConfigManager:
    """
    Get the default configuration manager instance.
    
    Returns:
        ConfigManager: Default configuration manager instance
    """
    global _default_config
    if _default_config is None:
        _default_config = create_config_manager()
    return _default_config

# Helper function to check if a feature is enabled (using the default config manager)
def is_feature_enabled(feature: str) -> bool:
    """
    Check if a feature is enabled.
    
    Args:
        feature: Feature name
        
    Returns:
        bool: True if enabled, False otherwise
    """
    return get_config().is_feature_enabled(feature)

if __name__ == "__main__":
    # Command-line interface for configuration management
    if len(sys.argv) < 2:
        print("Usage: python config_manager.py [get|set|reset|list]")
        sys.exit(1)
        
    command = sys.argv[1].lower()
    config = get_config()
    
    if command == "get":
        if len(sys.argv) < 3:
            print("Usage: python config_manager.py get [section] [key]")
            sys.exit(1)
            
        section = sys.argv[2]
        key = sys.argv[3] if len(sys.argv) > 3 else None
        
        value = config.get(section, key)
        print(json.dumps(value, indent=4))
    
    elif command == "set":
        if len(sys.argv) < 5:
            print("Usage: python config_manager.py set [section] [key] [value]")
            sys.exit(1)
            
        section = sys.argv[2]
        key = sys.argv[3]
        value_str = sys.argv[4]
        
        # Try to parse the value
        try:
            # Try to parse as JSON
            value = json.loads(value_str)
        except json.JSONDecodeError:
            # If not JSON, treat as string
            value = value_str
            
        success = config.set(section, key, value)
        if success:
            print(f"Set {section}.{key} = {value}")
        else:
            print(f"Failed to set {section}.{key}")
            sys.exit(1)
    
    elif command == "reset":
        success = config.reset_to_defaults()
        if success:
            print("Reset configuration to defaults")
        else:
            print("Failed to reset configuration")
            sys.exit(1)
    
    elif command == "list":
        print("Current configuration:")
        print(json.dumps(config.config, indent=4))
    
    else:
        print(f"Unknown command: {command}")
        print("Available commands: get, set, reset, list")
        sys.exit(1)
