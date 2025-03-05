# core/permission_validator.py

import os
import stat
import logging
import tempfile
from pathlib import Path

logger = logging.getLogger("NYX-PermissionValidator")

class PermissionValidator:
    """
    Validates file system permissions to ensure operations can be performed safely.
    This prevents permission-related errors and potential security issues.
    """
    
    @staticmethod
    def can_write_to_directory(directory_path):
        """
        Checks if the current process has permission to write to the specified directory.
        
        Args:
            directory_path (str): Path to the directory to check
            
        Returns:
            bool: True if the directory exists and is writable, False otherwise
        """
        path = Path(directory_path)
        
        # Check if directory exists
        if not path.exists():
            try:
                # Try to create it
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {directory_path}")
                return True
            except (PermissionError, OSError) as e:
                logger.error(f"Cannot create directory {directory_path}: {str(e)}")
                return False
        
        # Check if it's actually a directory
        if not path.is_dir():
            logger.error(f"{directory_path} exists but is not a directory")
            return False
        
        # Check write permission by attempting to create a temporary file
        try:
            test_file = path / f".permission_test_{os.getpid()}"
            test_file.touch()
            test_file.unlink()  # Remove the test file
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot write to directory {directory_path}: {str(e)}")
            return False
    
    @staticmethod
    def can_read_file(file_path):
        """
        Checks if the current process has permission to read the specified file.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if the file exists and is readable, False otherwise
        """
        path = Path(file_path)
        
        # Check if file exists
        if not path.exists():
            logger.error(f"File does not exist: {file_path}")
            return False
        
        # Check if it's a file
        if not path.is_file():
            logger.error(f"{file_path} exists but is not a file")
            return False
        
        # Check read permission
        try:
            with open(file_path, 'r') as _:
                pass
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot read file {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def can_write_file(file_path):
        """
        Checks if the current process has permission to write to the specified file.
        If the file doesn't exist, checks if it can be created.
        
        Args:
            file_path (str): Path to the file to check
            
        Returns:
            bool: True if the file can be written to, False otherwise
        """
        path = Path(file_path)
        
        # Check if the directory exists
        parent_dir = path.parent
        if not PermissionValidator.can_write_to_directory(parent_dir):
            return False
        
        # If file exists, check if we can write to it
        if path.exists():
            if not path.is_file():
                logger.error(f"{file_path} exists but is not a file")
                return False
            
            try:
                # Open the file in append mode to test write permission without modifying content
                with open(file_path, 'a') as _:
                    pass
                return True
            except (PermissionError, OSError) as e:
                logger.error(f"Cannot write to file {file_path}: {str(e)}")
                return False
        
        # File doesn't exist, check if we can create it
        try:
            path.touch()
            path.unlink()  # Remove the test file
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Cannot create file {file_path}: {str(e)}")
            return False
    
    @staticmethod
    def safe_path(path_str):
        """
        Ensures a path is safe by resolving and validating it.
        Prevents directory traversal attacks.
        
        Args:
            path_str (str): Path to validate
            
        Returns:
            str: Absolute, resolved path if safe, None otherwise
        """
        try:
            base_dir = os.getcwd()
            requested_path = os.path.abspath(path_str)
            
            # Check for directory traversal attempts
            if not requested_path.startswith(base_dir) and not requested_path.startswith('/tmp/'):
                logger.error(f"Path traversal attempt detected: {path_str}")
                return None
                
            return requested_path
        except Exception as e:
            logger.error(f"Error validating path {path_str}: {str(e)}")
            return None
    
    @staticmethod
    def ensure_safe_directory(directory_path, create=True):
        """
        Ensures a directory exists, is writable, and has appropriate permissions.
        
        Args:
            directory_path (str): Path to the directory
            create (bool): Whether to create the directory if it doesn't exist
            
        Returns:
            bool: True if the directory is safe to use, False otherwise
        """
        # Validate and resolve the path
        safe_dir = PermissionValidator.safe_path(directory_path)
        if not safe_dir:
            return False
            
        path = Path(safe_dir)
        
        # Check if directory exists
        if not path.exists():
            if not create:
                logger.error(f"Directory does not exist: {safe_dir}")
                return False
                
            try:
                # Create with secure permissions (0o755 = rwxr-xr-x)
                path.mkdir(parents=True, exist_ok=True)
                os.chmod(safe_dir, 0o755)
                logger.info(f"Created directory with secure permissions: {safe_dir}")
            except (PermissionError, OSError) as e:
                logger.error(f"Cannot create directory {safe_dir}: {str(e)}")
                return False
        
        # Check if it's a directory and has appropriate permissions
        if not path.is_dir():
            logger.error(f"{safe_dir} exists but is not a directory")
            return False
            
        # Check write permission
        if not PermissionValidator.can_write_to_directory(safe_dir):
            return False
            
        return True

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Check if we can write to logs directory
    if PermissionValidator.ensure_safe_directory("logs"):
        print("Logs directory is safe to use")
    else:
        print("Cannot use logs directory")
        
    # Check if we can write to a file
    if PermissionValidator.can_write_file("logs/test.log"):
        print("Can write to logs/test.log")
    else:
        print("Cannot write to logs/test.log")
