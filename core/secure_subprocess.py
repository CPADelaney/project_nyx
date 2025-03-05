# core/secure_subprocess.py

import os
import sys
import re
import shlex
import subprocess
import logging
from typing import List, Dict, Any, Optional, Union, Tuple

logger = logging.getLogger("NYX-SecureSubprocess")

# Define a whitelist of allowed executable paths
ALLOWED_EXECUTABLES = {
    "python": sys.executable,
    "python3": sys.executable,
    "bash": "/bin/bash",
    "sh": "/bin/sh",
    "grep": "/usr/bin/grep",
    "ps": "/usr/bin/ps",
    # Add other executables as needed
}

# Define a whitelist of allowed commands (command + arguments patterns)
ALLOWED_COMMANDS = [
    # Python scripts
    (sys.executable, r"^src/.*\.py$"),
    (sys.executable, r"^tracking/.*\.py$"),
    (sys.executable, r"^core/.*\.py$"),
    (sys.executable, r"^tests/.*\.py$"),
    
    # System commands
    ("/usr/bin/grep", r"^cpu /proc/stat$"),
    ("/usr/bin/ps", r"^aux$"),
    
    # Python modules
    (sys.executable, r"^-m unittest discover -s tests$"),
    (sys.executable, r"^-m py_compile src/.*\.py$"),
]

class CommandValidationError(Exception):
    """Exception raised when a command fails validation."""
    pass

def validate_command(command: List[str]) -> List[str]:
    """
    Validates a command against security rules.
    
    Args:
        command (List[str]): The command and its arguments as a list
        
    Returns:
        List[str]: The validated command with full paths
        
    Raises:
        CommandValidationError: If the command fails validation
    """
    if not command:
        raise CommandValidationError("Empty command")
    
    # Normalize the executable name
    exec_name = command[0]
    
    # Check if the executable is in our whitelist
    if exec_name in ALLOWED_EXECUTABLES:
        # Replace with the full path
        exec_path = ALLOWED_EXECUTABLES[exec_name]
    elif os.path.isabs(exec_name) and os.path.exists(exec_name) and os.access(exec_name, os.X_OK):
        # It's already a full path and exists
        exec_path = exec_name
        # Check if this full path is in our values
        if exec_path not in ALLOWED_EXECUTABLES.values():
            raise CommandValidationError(f"Executable not in whitelist: {exec_path}")
    else:
        raise CommandValidationError(f"Executable not allowed: {exec_name}")
    
    # Reconstruct the command with the full path
    validated_command = [exec_path] + command[1:]
    
    # Join arguments for pattern matching
    args_str = " ".join(command[1:]) if len(command) > 1 else ""
    
    # Check against allowed command patterns
    allowed = False
    for allowed_exec, allowed_args_pattern in ALLOWED_COMMANDS:
        if exec_path == allowed_exec and re.match(allowed_args_pattern, args_str):
            allowed = True
            break
    
    if not allowed:
        raise CommandValidationError(f"Command pattern not allowed: {exec_path} {args_str}")
    
    return validated_command

def sanitize_env(env: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Sanitizes the environment variables for subprocess execution.
    
    Args:
        env (Dict[str, str], optional): Environment variables to use
        
    Returns:
        Dict[str, str]: Sanitized environment variables
    """
    # Start with a minimal set of necessary environment variables
    base_env = {
        "PATH": "/usr/bin:/bin",
        "PYTHONPATH": os.getcwd(),
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
    }
    
    # If env is provided, validate and merge with base_env
    if env:
        # Filter out potentially dangerous variables
        dangerous_vars = ["LD_PRELOAD", "LD_LIBRARY_PATH", "PYTHONPATH"]
        for var in dangerous_vars:
            if var in env:
                logger.warning(f"Removing potentially dangerous environment variable: {var}")
                del env[var]
        
        # Merge with base_env (env takes precedence)
        sanitized_env = {**base_env, **env}
    else:
        sanitized_env = base_env
    
    return sanitized_env

def run(
    command: List[str],
    shell: bool = False,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = 60,
    check: bool = False,
    **kwargs
) -> subprocess.CompletedProcess:
    """
    Securely runs a subprocess command.
    
    Args:
        command (List[str]): The command and its arguments as a list
        shell (bool): Whether to run the command through the shell (always set to False for security)
        cwd (str, optional): Working directory for the command
        env (Dict[str, str], optional): Environment variables
        timeout (float, optional): Timeout in seconds (default: 60)
        check (bool): Whether to raise an exception if the return code is non-zero
        **kwargs: Additional arguments to pass to subprocess.run
        
    Returns:
        subprocess.CompletedProcess: The completed process
        
    Raises:
        CommandValidationError: If the command fails validation
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If check is True and the command returns a non-zero exit code
    """
    # Always force shell to False for security
    if shell:
        logger.warning("Shell execution requested but disabled for security reasons")
    shell = False
    
    # Validate the command
    try:
        validated_command = validate_command(command)
    except CommandValidationError as e:
        logger.error(f"Command validation failed: {e}")
        raise
    
    # Sanitize environment variables
    sanitized_env = sanitize_env(env)
    
    # Log the command being executed
    logger.info(f"Executing command: {' '.join(validated_command)}")
    
    # Run the command
    return subprocess.run(
        validated_command,
        shell=False,
        cwd=cwd,
        env=sanitized_env,
        timeout=timeout,
        check=check,
        **kwargs
    )

def Popen(
    command: List[str],
    shell: bool = False,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    **kwargs
) -> subprocess.Popen:
    """
    Securely creates a subprocess with Popen.
    
    Args:
        command (List[str]): The command and its arguments as a list
        shell (bool): Whether to run the command through the shell (always set to False for security)
        cwd (str, optional): Working directory for the command
        env (Dict[str, str], optional): Environment variables
        **kwargs: Additional arguments to pass to subprocess.Popen
        
    Returns:
        subprocess.Popen: The Popen object
        
    Raises:
        CommandValidationError: If the command fails validation
    """
    # Always force shell to False for security
    if shell:
        logger.warning("Shell execution requested but disabled for security reasons")
    shell = False
    
    # Validate the command
    try:
        validated_command = validate_command(command)
    except CommandValidationError as e:
        logger.error(f"Command validation failed: {e}")
        raise
    
    # Sanitize environment variables
    sanitized_env = sanitize_env(env)
    
    # Log the command being executed
    logger.info(f"Starting process: {' '.join(validated_command)}")
    
    # Create the process
    return subprocess.Popen(
        validated_command,
        shell=False,
        cwd=cwd,
        env=sanitized_env,
        **kwargs
    )

def check_output(
    command: List[str],
    shell: bool = False,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: Optional[float] = 60,
    **kwargs
) -> bytes:
    """
    Securely runs a command and returns its output.
    
    Args:
        command (List[str]): The command and its arguments as a list
        shell (bool): Whether to run the command through the shell (always set to False for security)
        cwd (str, optional): Working directory for the command
        env (Dict[str, str], optional): Environment variables
        timeout (float, optional): Timeout in seconds (default: 60)
        **kwargs: Additional arguments to pass to subprocess.check_output
        
    Returns:
        bytes: The command's output
        
    Raises:
        CommandValidationError: If the command fails validation
        subprocess.TimeoutExpired: If the command times out
        subprocess.CalledProcessError: If the command returns a non-zero exit code
    """
    # Always force shell to False for security
    if shell:
        logger.warning("Shell execution requested but disabled for security reasons")
    shell = False
    
    # Validate the command
    try:
        validated_command = validate_command(command)
    except CommandValidationError as e:
        logger.error(f"Command validation failed: {e}")
        raise
    
    # Sanitize environment variables
    sanitized_env = sanitize_env(env)
    
    # Log the command being executed
    logger.info(f"Executing command for output: {' '.join(validated_command)}")
    
    # Run the command and return its output
    return subprocess.check_output(
        validated_command,
        shell=False,
        cwd=cwd,
        env=sanitized_env,
        timeout=timeout,
        **kwargs
    )

# Helper function for parsing shell commands safely
def parse_shell_command(cmd_str: str) -> List[str]:
    """
    Safely parses a shell command string into a list of arguments.
    
    Args:
        cmd_str (str): The command string to parse
        
    Returns:
        List[str]: The parsed command as a list
    """
    try:
        return shlex.split(cmd_str)
    except ValueError as e:
        logger.error(f"Error parsing shell command: {e}")
        raise CommandValidationError(f"Invalid shell command: {cmd_str}")

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Example of running a safe command
        result = run(["python3", "src/nyx_core.py"])
        print(f"Command executed with return code: {result.returncode}")
        
        # Example of running a command that should fail validation
        result = run(["rm", "-rf", "/"])
    except CommandValidationError as e:
        print(f"Validation error: {e}")
    except Exception as e:
        print(f"Execution error: {e}")
