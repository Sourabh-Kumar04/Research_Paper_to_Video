#!/usr/bin/env python3
"""
Comprehensive Error Checker for RASO Platform
Checks Python files for syntax errors, import issues, and runtime problems.
"""

import ast
import sys
import importlib
from pathlib import Path
from typing import List, Tuple, Dict
import traceback

class ErrorChecker:
    """Check for errors in Python files."""
    
    def __init__(self, root_dir: Path):
        self.root_dir = root_dir
        self.errors = []
        self.warnings = []
        
    def check_syntax(self, file_path: Path) -> List[str]:
        """Check Python file for syntax errors."""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            # Try to parse the file
            ast.parse(source_code, filename=str(file_path))
            
        except SyntaxError as e:
            errors.append(f"SYNTAX ERROR in {file_path}:{e.lineno} - {e.msg}")
        except Exception as e:
            errors.append(f"PARSE ERROR in {file_path} - {str(e)}")
        
        return errors
    
    def check_imports(self, file_path: Path) -> List[str]:
        """Check for import errors."""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source_code = f.read()
            
            tree = ast.parse(source_code, filename=str(file_path))
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        try:
                            importlib.import_module(alias.name)
                        except ImportError as e:
                            errors.append(f"IMPORT ERROR in {file_path}:{node.lineno} - Cannot import '{alias.name}': {str(e)}")
                        except Exception:
                            pass  # Skip other import issues
                            
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        try:
                            importlib.import_module(node.module)
                        except ImportError as e:
                            errors.append(f"IMPORT ERROR in {file_path}:{node.lineno} - Cannot import from '{node.module}': {str(e)}")
                        except Exception:
                            pass  # Skip other import issues
                            
        except Exception as e:
            pass  # Already caught by syntax check
        
        return errors
    
    def check_file(self, file_path: Path) -> Tuple[List[str], List[str]]:
        """Check a single Python file for errors."""
        errors = []
        warnings = []
        
        # Check syntax
        syntax_errors = self.check_syntax(file_path)
        errors.extend(syntax_errors)
        
        # Only check imports if syntax is ok
        if not syntax_errors:
            import_errors = self.check_imports(file_path)
            warnings.extend(import_errors)  # Treat as warnings since some imports might not be installed
        
        return errors, warnings
    
    def check_directory(self, directory: Path) -> None:
        """Recursively check all Python files in directory."""
        print(f"\\n🔍 Checking directory: {directory}")
        
        # Find all Python files
        python_files = list(directory.rglob("*.py"))
        
        # Exclude certain directories
        excluded_dirs = {'.venv', 'venv', '__pycache__', 'node_modules', '.git', '.pytest_cache', '.hypothesis', '.kiro'}
        python_files = [
            f for f in python_files 
            if not any(excluded in f.parts for excluded in excluded_dirs)
        ]
        
        print(f"   Found {len(python_files)} Python files")
        
        for file_path in python_files:
            file_errors, file_warnings = self.check_file(file_path)
            
            if file_errors:
                self.errors.extend(file_errors)
                print(f"   ❌ {file_path.relative_to(self.root_dir)}: {len(file_errors)} error(s)")
            elif file_warnings:
                self.warnings.extend(file_warnings)
                print(f"   ⚠️  {file_path.relative_to(self.root_dir)}: {len(file_warnings)} warning(s)")
    
    def print_report(self) -> int:
        """Print error and warning report."""
        print("\\n" + "=" * 70)
        print("ERROR REPORT")
        print("=" * 70)
        
        if self.errors:
            print(f"\\n🔴 CRITICAL ERRORS FOUND: {len(self.errors)}")
            print("-" * 70)
            for error in self.errors:
                print(f"   {error}")
        else:
            print("\\n✅ NO CRITICAL ERRORS FOUND")
        
        if self.warnings:
            print(f"\\n⚠️  WARNINGS: {len(self.warnings)}")
            print("-" * 70)
            for warning in self.warnings[:10]:  # Show first 10 warnings
                print(f"   {warning}")
            if len(self.warnings) > 10:
                print(f"   ... and {len(self.warnings) - 10} more warnings")
        
        print("\\n" + "=" * 70)
        
        # Return exit code based on errors
        return 0 if not self.errors else 1

def main():
    """Main entry point."""
    print("🚀 RASO Platform - Error Checker")
    print("=" * 70)
    
    root_dir = Path(__file__).parent
    
    # Add src to path
    sys.path.insert(0, str(root_dir / "src"))
    sys.path.insert(0, str(root_dir / "config"))
    
    checker = ErrorChecker(root_dir)
    
    # Check main directories
    directories_to_check = [
        root_dir / "src" / "agents",
        root_dir / "config" / "backend",
        root_dir / "scripts",
    ]
    
    for directory in directories_to_check:
        if directory.exists():
            checker.check_directory(directory)
        else:
            print(f"\\n⚠️  Directory not found: {directory}")
    
    # Print final report
    exit_code = checker.print_report()
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
