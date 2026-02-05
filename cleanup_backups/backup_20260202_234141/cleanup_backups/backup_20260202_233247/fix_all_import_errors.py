#!/usr/bin/env python3
"""
Fix all import errors in the RASO codebase.
Specifically fix incorrect 'from backend.models' imports to 'from config.backend.models'.
"""

import os
import re
from pathlib import Path


def fix_imports_in_file(file_path: Path) -> tuple[bool, list[str]]:
    """
    Fix import statements in a single file.
    
    Returns:
        tuple of (was_modified, list_of_changes)
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        changes = []
        
        # Pattern 1: from backend.models import ...
        pattern1 = r'from backend\.models'
        replacement1 = 'from config.backend.models'
        
        if re.search(pattern1, content):
            content = re.sub(pattern1, replacement1, content)
            count = len(re.findall(pattern1, original_content))
            changes.append(f"Fixed {count} 'from backend.models' imports")
        
        # Pattern 2: from backend.services import ...
        pattern2 = r'from backend\.services'
        replacement2 = 'from config.backend.services'
        
        if re.search(pattern2, content):
            content = re.sub(pattern2, replacement2, content)
            count = len(re.findall(pattern2, original_content))
            changes.append(f"Fixed {count} 'from backend.services' imports")
        
        # Pattern 3: import backend.models
        pattern3 = r'import backend\.models'
        replacement3 = 'import config.backend.models'
        
        if re.search(pattern3, content):
            content = re.sub(pattern3, replacement3, content)
            count = len(re.findall(pattern3, original_content))
            changes.append(f"Fixed {count} 'import backend.models' imports")
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True, changes
        
        return False, []
        
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False, []


def scan_and_fix_directory(directory: Path) -> dict:
    """
    Scan directory recursively and fix import errors.
    
    Returns:
        dict with statistics
    """
    stats = {
        'files_scanned': 0,
        'files_modified': 0,
        'total_changes': 0,
        'errors': 0
    }
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', '.venv', 'node_modules', '.pytest_cache', 
                 '.hypothesis', '.vscode', 'dist', 'build', '.egg-info'}
    
    # Scan all Python files
    for file_path in directory.rglob('*.py'):
        # Skip excluded directories
        if any(skip in file_path.parts for skip in skip_dirs):
            continue
        
        stats['files_scanned'] += 1
        
        try:
            was_modified, changes = fix_imports_in_file(file_path)
            
            if was_modified:
                stats['files_modified'] += 1
                stats['total_changes'] += len(changes)
                print(f"✅ Fixed: {file_path}")
                for change in changes:
                    print(f"   - {change}")
        
        except Exception as e:
            stats['errors'] += 1
            print(f"❌ Error: {file_path}: {e}")
    
    return stats


def main():
    """Main function to fix all imports."""
    print("🔧 RASO Import Error Fixer")
    print("=" * 60)
    print()
    
    # Get project root
    project_root = Path(__file__).parent
    
    print(f"📁 Scanning: {project_root}")
    print()
    
    # Scan and fix
    stats = scan_and_fix_directory(project_root)
    
    # Print summary
    print()
    print("=" * 60)
    print("📊 Summary")
    print("=" * 60)
    print(f"Files scanned:  {stats['files_scanned']}")
    print(f"Files modified: {stats['files_modified']}")
    print(f"Total changes:  {stats['total_changes']}")
    print(f"Errors:         {stats['errors']}")
    
    if stats['files_modified'] > 0:
        print()
        print("✨ Import errors fixed successfully!")
        print("🔄 Please restart your application for changes to take effect.")
    else:
        print()
        print("✅ No import errors found!")


if __name__ == "__main__":
    main()
