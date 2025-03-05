# src/self_analysis.py

import ast
import os
import logging
from typing import Dict, List, Any, Optional
from core.error_framework import safe_execute, fail_gracefully, ValidationError, FileSystemError

# Configure logging
logger = logging.getLogger("NYX-SelfAnalysis")

# Directory to analyze
CODE_DIR = "src"

# Log file for self-analysis
LOG_FILE = "logs/code_analysis.log"

class CodeAnalyzer:
    """Analyzes Python code structure and provides insights about the codebase."""
    
    def __init__(self, code_dir: str = CODE_DIR, log_file: str = LOG_FILE):
        """
        Initialize the code analyzer.
        
        Args:
            code_dir: Directory containing code to analyze
            log_file: Path to the log file
        """
        self.code_dir = code_dir
        self.log_file = log_file
    
    @safe_execute
    def analyze_code_structure(self, file_path: str) -> Dict[str, Any]:
        """
        Analyzes the structure of a Python file and extracts functions and imports.
        
        Args:
            file_path: Path to the Python file to analyze
            
        Returns:
            Dict[str, Any]: Analysis results
            
        Raises:
            FileSystemError: If the file cannot be read
            ValidationError: If the file is empty or invalid
            SyntaxError: If the file contains syntax errors
        """
        # Validate file path
        if not os.path.exists(file_path):
            raise FileSystemError(f"File does not exist: {file_path}", path=file_path, operation="read")
        
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                content = file.read().strip()

                if not content:
                    raise ValidationError(f"Empty or invalid file: {file_path}", field="file_content")

                tree = ast.parse(content, filename=file_path)
        except SyntaxError as e:
            logger.warning(f"Syntax error in {file_path}: {str(e)}")
            raise ValidationError(f"Syntax error in file: {str(e)}", field="file_content", cause=e)
        except Exception as e:
            raise FileSystemError(f"Could not read file: {str(e)}", path=file_path, operation="read", cause=e)
        
        functions = [node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
        imports = [node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)]
        
        # Detect unused imports
        unused_imports = [imp for imp in imports if imp not in functions]

        # Detect long functions (excessive complexity)
        long_functions = [node.name for node in ast.walk(tree) 
                         if isinstance(node, ast.FunctionDef) and len(node.body) > 20]  # Threshold: 20 lines

        return {
            "file": file_path,
            "functions": functions,
            "imports": imports,
            "unused_imports": unused_imports,
            "long_functions": long_functions
        }
    
    @safe_execute
    def log_analysis(self, results: List[Dict[str, Any]]) -> bool:
        """
        Logs analysis results, ensuring the log file is never empty.
        
        Args:
            results: List of analysis results
            
        Returns:
            bool: True if successful
            
        Raises:
            FileSystemError: If the log file cannot be written
        """
        # Create the log directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)

        try:
            with open(self.log_file, "w", encoding="utf-8") as log_file:
                if not results:
                    log_file.write("⚠️ No Python files found for analysis.\n")
                    logger.warning("No Python files detected. Log will be minimal.")
                    return True

                for result in results:
                    log_file.write(f"File: {result['file']}\n")
                    log_file.write(f"Functions: {', '.join(result['functions'])}\n")
                    log_file.write(f"Imports: {', '.join(result['imports'])}\n")
                    log_file.write(f"Unused Imports: {', '.join(result['unused_imports'])}\n")
                    log_file.write(f"Complex Functions: {', '.join(result['long_functions'])}\n")
                    log_file.write("="*40 + "\n")
                    
                # Ensure the log file has a completion message
                log_file.write("✅ Code analysis completed.\n")
                
                return True
        except Exception as e:
            raise FileSystemError(f"Could not write to log file: {str(e)}", 
                                 path=self.log_file, operation="write", cause=e)
    
    @fail_gracefully(default_return=[])
    def analyze_all_files(self) -> List[Dict[str, Any]]:
        """
        Analyze all Python files in the code directory.
        
        Returns:
            List[Dict[str, Any]]: List of analysis results
        """
        results = []
        
        if not os.path.exists(self.code_dir):
            logger.error(f"Code directory does not exist: {self.code_dir}")
            return results
        
        for filename in os.listdir(self.code_dir):
            if filename.endswith(".py"):  # Adjust for other languages if needed
                file_path = os.path.join(self.code_dir, filename)
                try:
                    analysis = self.analyze_code_structure(file_path)
                    if analysis["success"] is False:  # Handle the case where safe_execute returned an error
                        logger.warning(f"Analysis failed for {file_path}: {analysis.get('error', {}).get('message')}")
                        continue
                    results.append(analysis)
                except Exception as e:
                    logger.error(f"Unexpected error analyzing {file_path}: {str(e)}")
        
        return results

@safe_execute
def main() -> Dict[str, Any]:
    """
    Run code analysis and ensure logs exist.
    
    Returns:
        Dict[str, Any]: Result of the analysis
    """
    analyzer = CodeAnalyzer(CODE_DIR, LOG_FILE)
    
    # Analyze all Python files
    results = analyzer.analyze_all_files()
    
    # Log the results
    log_success = analyzer.log_analysis(results)
    
    logger.info(f"✅ Code analysis completed. Results logged in {LOG_FILE}")
    
    return {
        "success": True,
        "message": f"Code analysis completed. Results logged in {LOG_FILE}",
        "file_count": len(results)
    }

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    result = main()
    if result["success"] is False:
        print(f"❌ Analysis failed: {result.get('error', {}).get('message', 'Unknown error')}")
        exit(1)
    else:
        print(f"✅ Analysis completed: {result['message']}")
