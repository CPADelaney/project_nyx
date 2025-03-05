# core/file_operations.py

"""
Asynchronous file operations for the Nyx system.
Provides efficient file I/O without blocking the main thread.
"""

import os
import json
import logging
import shutil
import asyncio
import aiofiles
from typing import Dict, Any, Optional, List, Union, BinaryIO
from pathlib import Path

from core.error_framework import safe_execute, ValidationError, FileSystemError
from core.permission_validator import PermissionValidator
from core.async_operations import async_io_operation, run_async

# Configure logging
logger = logging.getLogger("NYX-FileOperations")

class FileOperations:
    """
    Provides high-level file operations with both synchronous and asynchronous APIs.
    Uses PermissionValidator to ensure safe file access.
    """
    
    @staticmethod
    @safe_execute
    def ensure_directory(directory_path: str) -> Dict[str, Any]:
        """
        Ensure a directory exists with permissions validation.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        if not PermissionValidator.ensure_safe_directory(directory_path, create=True):
            raise FileSystemError(f"Cannot create or access directory: {directory_path}", 
                                path=directory_path, operation="create")
            
        return {"success": True, "message": f"Directory {directory_path} created or verified"}
    
    @staticmethod
    @async_io_operation
    async def ensure_directory_async(directory_path: str) -> Dict[str, Any]:
        """
        Async version of ensure_directory.
        
        Args:
            directory_path: Path to the directory
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Use the synchronous version but run it in a separate thread
        return FileOperations.ensure_directory(directory_path)
    
    @staticmethod
    @safe_execute
    def read_file(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Read a file with permissions validation.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation with file content
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="read")
            
        if not PermissionValidator.can_read_file(safe_path):
            raise FileSystemError(f"Cannot read file: {safe_path}", 
                                path=safe_path, operation="read")
            
        try:
            with open(safe_path, 'r', encoding=encoding) as f:
                content = f.read()
                
            return {"success": True, "content": content}
        except Exception as e:
            raise FileSystemError(f"Error reading file {safe_path}: {str(e)}", 
                                path=safe_path, operation="read", cause=e)
    
    @staticmethod
    @async_io_operation
    async def read_file_async(file_path: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Async version of read_file.
        
        Args:
            file_path: Path to the file
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation with file content
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="read")
            
        if not PermissionValidator.can_read_file(safe_path):
            raise FileSystemError(f"Cannot read file: {safe_path}", 
                                path=safe_path, operation="read")
            
        try:
            async with aiofiles.open(safe_path, 'r', encoding=encoding) as f:
                content = await f.read()
                
            return {"success": True, "content": content}
        except Exception as e:
            raise FileSystemError(f"Error reading file {safe_path}: {str(e)}", 
                                path=safe_path, operation="read", cause=e)
    
    @staticmethod
    @safe_execute
    def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Write to a file with permissions validation.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="write")
            
        # Ensure the directory exists
        directory = os.path.dirname(os.path.abspath(safe_path))
        if not os.path.exists(directory):
            if not PermissionValidator.ensure_safe_directory(directory, create=True):
                raise FileSystemError(f"Cannot create directory: {directory}", 
                                    path=directory, operation="create")
            
        if not PermissionValidator.can_write_file(safe_path):
            raise FileSystemError(f"Cannot write to file: {safe_path}", 
                                path=safe_path, operation="write")
            
        try:
            with open(safe_path, 'w', encoding=encoding) as f:
                f.write(content)
                
            return {"success": True, "message": f"Successfully wrote to {safe_path}"}
        except Exception as e:
            raise FileSystemError(f"Error writing to file {safe_path}: {str(e)}", 
                                path=safe_path, operation="write", cause=e)
    
    @staticmethod
    @async_io_operation
    async def write_file_async(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Async version of write_file.
        
        Args:
            file_path: Path to the file
            content: Content to write
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="write")
            
        # Ensure the directory exists
        directory = os.path.dirname(os.path.abspath(safe_path))
        if not os.path.exists(directory):
            # Use sync version for directory creation since it's a rare operation
            if not PermissionValidator.ensure_safe_directory(directory, create=True):
                raise FileSystemError(f"Cannot create directory: {directory}", 
                                    path=directory, operation="create")
            
        if not PermissionValidator.can_write_file(safe_path):
            raise FileSystemError(f"Cannot write to file: {safe_path}", 
                                path=safe_path, operation="write")
            
        try:
            async with aiofiles.open(safe_path, 'w', encoding=encoding) as f:
                await f.write(content)
                
            return {"success": True, "message": f"Successfully wrote to {safe_path}"}
        except Exception as e:
            raise FileSystemError(f"Error writing to file {safe_path}: {str(e)}", 
                                path=safe_path, operation="write", cause=e)
    
    @staticmethod
    @safe_execute
    def append_file(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Append to a file with permissions validation.
        
        Args:
            file_path: Path to the file
            content: Content to append
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="append")
            
        # Ensure the directory exists
        directory = os.path.dirname(os.path.abspath(safe_path))
        if not os.path.exists(directory):
            if not PermissionValidator.ensure_safe_directory(directory, create=True):
                raise FileSystemError(f"Cannot create directory: {directory}", 
                                    path=directory, operation="create")
            
        if not PermissionValidator.can_write_file(safe_path):
            raise FileSystemError(f"Cannot write to file: {safe_path}", 
                                path=safe_path, operation="append")
            
        try:
            with open(safe_path, 'a', encoding=encoding) as f:
                f.write(content)
                
            return {"success": True, "message": f"Successfully appended to {safe_path}"}
        except Exception as e:
            raise FileSystemError(f"Error appending to file {safe_path}: {str(e)}", 
                                path=safe_path, operation="append", cause=e)
    
    @staticmethod
    @async_io_operation
    async def append_file_async(file_path: str, content: str, encoding: str = 'utf-8') -> Dict[str, Any]:
        """
        Async version of append_file.
        
        Args:
            file_path: Path to the file
            content: Content to append
            encoding: File encoding
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="append")
            
        # Ensure the directory exists
        directory = os.path.dirname(os.path.abspath(safe_path))
        if not os.path.exists(directory):
            # Use sync version for directory creation since it's a rare operation
            if not PermissionValidator.ensure_safe_directory(directory, create=True):
                raise FileSystemError(f"Cannot create directory: {directory}", 
                                    path=directory, operation="create")
            
        if not PermissionValidator.can_write_file(safe_path):
            raise FileSystemError(f"Cannot write to file: {safe_path}", 
                                path=safe_path, operation="append")
            
        try:
            async with aiofiles.open(safe_path, 'a', encoding=encoding) as f:
                await f.write(content)
                
            return {"success": True, "message": f"Successfully appended to {safe_path}"}
        except Exception as e:
            raise FileSystemError(f"Error appending to file {safe_path}: {str(e)}", 
                                path=safe_path, operation="append", cause=e)
    
    @staticmethod
    @safe_execute
    def delete_file(file_path: str) -> Dict[str, Any]:
        """
        Delete a file with permissions validation.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_path = PermissionValidator.safe_path(file_path)
        if not safe_path:
            raise FileSystemError(f"Invalid file path: {file_path}", 
                                path=file_path, operation="delete")
            
        try:
            if os.path.exists(safe_path):
                os.remove(safe_path)
                return {"success": True, "message": f"Successfully deleted {safe_path}"}
            else:
                return {"success": True, "message": f"File {safe_path} does not exist"}
        except Exception as e:
            raise FileSystemError(f"Error deleting file {safe_path}: {str(e)}", 
                                path=safe_path, operation="delete", cause=e)
    
    @staticmethod
    @async_io_operation
    async def delete_file_async(file_path: str) -> Dict[str, Any]:
        """
        Async version of delete_file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Use the synchronous version but run it in a separate thread
        return FileOperations.delete_file(file_path)
    
    @staticmethod
    @safe_execute
    def copy_file(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        Copy a file with permissions validation.
        
        Args:
            source_path: Path to the source file
            dest_path: Path to the destination file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_source = PermissionValidator.safe_path(source_path)
        if not safe_source:
            raise FileSystemError(f"Invalid source path: {source_path}", 
                                path=source_path, operation="copy")
            
        safe_dest = PermissionValidator.safe_path(dest_path)
        if not safe_dest:
            raise FileSystemError(f"Invalid destination path: {dest_path}", 
                                path=dest_path, operation="copy")
            
        if not PermissionValidator.can_read_file(safe_source):
            raise FileSystemError(f"Cannot read source file: {safe_source}", 
                                path=safe_source, operation="read")
            
        # Ensure the destination directory exists
        dest_dir = os.path.dirname(os.path.abspath(safe_dest))
        if not os.path.exists(dest_dir):
            if not PermissionValidator.ensure_safe_directory(dest_dir, create=True):
                raise FileSystemError(f"Cannot create destination directory: {dest_dir}", 
                                    path=dest_dir, operation="create")
            
        if not PermissionValidator.can_write_file(safe_dest):
            raise FileSystemError(f"Cannot write to destination file: {safe_dest}", 
                                path=safe_dest, operation="write")
            
        try:
            shutil.copy2(safe_source, safe_dest)
            return {"success": True, "message": f"Successfully copied {safe_source} to {safe_dest}"}
        except Exception as e:
            raise FileSystemError(f"Error copying file: {str(e)}", 
                                path=f"{safe_source} -> {safe_dest}", operation="copy", cause=e)
    
    @staticmethod
    @async_io_operation
    async def copy_file_async(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        Async version of copy_file.
        
        Args:
            source_path: Path to the source file
            dest_path: Path to the destination file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Use the synchronous version but run it in a separate thread
        return FileOperations.copy_file(source_path, dest_path)
    
    @staticmethod
    @safe_execute
    def move_file(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        Move a file with permissions validation.
        
        Args:
            source_path: Path to the source file
            dest_path: Path to the destination file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        safe_source = PermissionValidator.safe_path(source_path)
        if not safe_source:
            raise FileSystemError(f"Invalid source path: {source_path}", 
                                path=source_path, operation="move")
            
        safe_dest = PermissionValidator.safe_path(dest_path)
        if not safe_dest:
            raise FileSystemError(f"Invalid destination path: {dest_path}", 
                                path=dest_path, operation="move")
            
        if not PermissionValidator.can_read_file(safe_source):
            raise FileSystemError(f"Cannot read source file: {safe_source}", 
                                path=safe_source, operation="read")
            
        # Ensure the destination directory exists
        dest_dir = os.path.dirname(os.path.abspath(safe_dest))
        if not os.path.exists(dest_dir):
            if not PermissionValidator.ensure_safe_directory(dest_dir, create=True):
                raise FileSystemError(f"Cannot create destination directory: {dest_dir}", 
                                    path=dest_dir, operation="create")
            
        if not PermissionValidator.can_write_file(safe_dest):
            raise FileSystemError(f"Cannot write to destination file: {safe_dest}", 
                                path=safe_dest, operation="write")
            
        try:
            shutil.move(safe_source, safe_dest)
            return {"success": True, "message": f"Successfully moved {safe_source} to {safe_dest}"}
        except Exception as e:
            raise FileSystemError(f"Error moving file: {str(e)}", 
                                path=f"{safe_source} -> {safe_dest}", operation="move", cause=e)
    
    @staticmethod
    @async_io_operation
    async def move_file_async(source_path: str, dest_path: str) -> Dict[str, Any]:
        """
        Async version of move_file.
        
        Args:
            source_path: Path to the source file
            dest_path: Path to the destination file
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        # Use the synchronous version but run it in a separate thread
        return FileOperations.move_file(source_path, dest_path)
    
    @staticmethod
    @safe_execute
    def load_json(file_path: str, default: Any = None) -> Dict[str, Any]:
        """
        Load JSON data from a file with permissions validation.
        
        Args:
            file_path: Path to the JSON file
            default: Default value if the file doesn't exist or is invalid
            
        Returns:
            Dict[str, Any]: Result of the operation with loaded data
        """
        result = FileOperations.read_file(file_path)
        if not result["success"]:
            return {"success": False, "error": result.get("error")}
            
        try:
            data = json.loads(result["content"])
            return {"success": True, "data": data}
        except json.JSONDecodeError as e:
            if default is not None:
                return {"success": True, "data": default, "warning": f"Invalid JSON, using default: {str(e)}"}
            else:
                raise FileSystemError(f"Error parsing JSON: {str(e)}", 
                                    path=file_path, operation="parse", cause=e)
    
    @staticmethod
    @async_io_operation
    async def load_json_async(file_path: str, default: Any = None) -> Dict[str, Any]:
        """
        Async version of load_json.
        
        Args:
            file_path: Path to the JSON file
            default: Default value if the file doesn't exist or is invalid
            
        Returns:
            Dict[str, Any]: Result of the operation with loaded data
        """
        result = await FileOperations.read_file_async(file_path)
        if not result["success"]:
            return {"success": False, "error": result.get("error")}
            
        try:
            data = json.loads(result["content"])
            return {"success": True, "data": data}
        except json.JSONDecodeError as e:
            if default is not None:
                return {"success": True, "data": default, "warning": f"Invalid JSON, using default: {str(e)}"}
            else:
                raise FileSystemError(f"Error parsing JSON: {str(e)}", 
                                    path=file_path, operation="parse", cause=e)
    
    @staticmethod
    @safe_execute
    def save_json(file_path: str, data: Any, indent: int = 4) -> Dict[str, Any]:
        """
        Save data as JSON to a file with permissions validation.
        
        Args:
            file_path: Path to the JSON file
            data: Data to save
            indent: JSON indentation
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            json_str = json.dumps(data, indent=indent)
            return FileOperations.write_file(file_path, json_str)
        except Exception as e:
            raise FileSystemError(f"Error saving JSON: {str(e)}", 
                                path=file_path, operation="write", cause=e)
    
    @staticmethod
    @async_io_operation
    async def save_json_async(file_path: str, data: Any, indent: int = 4) -> Dict[str, Any]:
        """
        Async version of save_json.
        
        Args:
            file_path: Path to the JSON file
            data: Data to save
            indent: JSON indentation
            
        Returns:
            Dict[str, Any]: Result of the operation
        """
        try:
            json_str = json.dumps(data, indent=indent)
            return await FileOperations.write_file_async(file_path, json_str)
        except Exception as e:
            raise FileSystemError(f"Error saving JSON: {str(e)}", 
                                path=file_path, operation="write", cause=e)
    
    @staticmethod
    @safe_execute
    def list_files(directory_path: str, pattern: str = "*") -> Dict[str, Any]:
        """
        List files in a directory with permissions validation.
        
        Args:
            directory_path: Path to the directory
            pattern: Glob pattern for file matching
            
        Returns:
            Dict[str, Any]: Result of the operation with list of files
        """
        safe_path = PermissionValidator.safe_path(directory_path)
        if not safe_path:
            raise FileSystemError(f"Invalid directory path: {directory_path}", 
                                path=directory_path, operation="list")
            
        if not os.path.exists(safe_path):
            return {"success": True, "files": [], "message": f"Directory {safe_path} does not exist"}
            
        if not os.path.isdir(safe_path):
            raise FileSystemError(f"Not a directory: {safe_path}", 
                                path=safe_path, operation="list")
            
        try:
            # Use Path.glob for safer pattern matching
            path = Path(safe_path)
            files = list(map(str, path.glob(pattern)))
            return {"success": True, "files": files}
        except Exception as e:
            raise FileSystemError(f"Error listing files: {str(e)}", 
                                path=safe_path, operation="list", cause=e)
    
    @staticmethod
    @async_io_operation
    async def list_files_async(directory_path: str, pattern: str = "*") -> Dict[str, Any]:
        """
        Async version of list_files.
        
        Args:
            directory_path: Path to the directory
            pattern: Glob pattern for file matching
            
        Returns:
            Dict[str, Any]: Result of the operation with list of files
        """
        # Use the synchronous version but run it in a separate thread
        return FileOperations.list_files(directory_path, pattern)

# Aliases for backward compatibility
async_read_file = FileOperations.read_file_async
async_write_file = FileOperations.write_file_async
async_append_file = FileOperations.append_file_async
async_load_json = FileOperations.load_json_async
async_save_json = FileOperations.save_json_async

# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Example: Write a file asynchronously
    async def example():
        # Write a file
        result = await FileOperations.write_file_async("example.txt", "Hello, world!")
        print(f"Write result: {result}")
        
        # Read the file
        result = await FileOperations.read_file_async("example.txt")
        print(f"Read result: {result}")
        
        # Save JSON data
        data = {"name": "Example", "values": [1, 2, 3]}
        result = await FileOperations.save_json_async("example.json", data)
        print(f"Save JSON result: {result}")
        
        # Load JSON data
        result = await FileOperations.load_json_async("example.json")
        print(f"Load JSON result: {result}")
        
        # Clean up
        await FileOperations.delete_file_async("example.txt")
        await FileOperations.delete_file_async("example.json")
    
    # Run the example
    run_async(example())
