#!/usr/bin/env python3
"""
RASO Codebase Cleanup Infrastructure
Provides file analysis, categorization, and backup utilities for systematic cleanup.
"""

import os
import re
import json
import shutil
import logging
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('cleanup.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


@dataclass
class FileInfo:
    """Information about a file for cleanup analysis."""
    path: Path
    size: int
    category: str
    is_duplicate: bool = False
    duplicate_group: Optional[str] = None
    content_hash: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'path': str(self.path),
            'size': self.size,
            'category': self.category,
            'is_duplicate': self.is_duplicate,
            'duplicate_group': self.duplicate_group,
            'content_hash': self.content_hash
        }


@dataclass
class FileInventory:
    """Complete inventory of files categorized for cleanup."""
    total_files: int
    temporary_files: List[FileInfo]
    production_files: List[FileInfo]
    test_files: List[FileInfo]
    config_files: List[FileInfo]
    documentation_files: List[FileInfo]
    duplicate_groups: Dict[str, List[FileInfo]]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            'total_files': self.total_files,
            'temporary_files': [f.to_dict() for f in self.temporary_files],
            'production_files': [f.to_dict() for f in self.production_files],
            'test_files': [f.to_dict() for f in self.test_files],
            'config_files': [f.to_dict() for f in self.config_files],
            'documentation_files': [f.to_dict() for f in self.documentation_files],
            'duplicate_groups': {k: [f.to_dict() for f in v] for k, v in self.duplicate_groups.items()}
        }


@dataclass
class BackupManifest:
    """Manifest of files backed up during cleanup."""
    timestamp: str
    backup_directory: str
    files_backed_up: List[Dict]
    total_size: int
    
    def save(self, path: Path) -> None:
        """Save manifest to JSON file."""
        with open(path, 'w') as f:
            json.dump(asdict(self), f, indent=2)
    
    @classmethod
    def load(cls, path: Path) -> 'BackupManifest':
        """Load manifest from JSON file."""
        with open(path, 'r') as f:
            data = json.load(f)
        return cls(**data)


class FileAnalyzer:
    """Analyzes and categorizes files for cleanup operations."""
    
    # File patterns for categorization
    TEMPORARY_PATTERNS = [
        r'^fix_.*\.py$',
        r'^debug_.*\.py$',
        r'^test_.*\.py$',  # Only in root directory
        r'.*_COMPLETE\.md$',
        r'.*_FIXED\.md$',
        r'.*_STATUS\.md$',
        r'^enhance_.*\.py$',
        r'^implement_.*\.py$',
        r'^upgrade_.*\.py$',
        r'^check_.*\.py$',
        r'^enable_.*\.py$',
        r'^force_.*\.py$',
        r'^list_.*\.py$',
        r'^inspect_.*\.py$',
        r'^verify_.*\.py$',
        r'^diagnose_.*\.py$',
        r'^simple_.*\.py$',
        r'^comprehensive_.*\.py$',
        r'.*\.backup$',
        r'.*\.backup\.py$',
        r'.*\.bat$',
        r'.*\.ps1$'
    ]
    
    PRODUCTION_PATTERNS = [
        r'^src/.*\.py$',
        r'^config/.*\.py$',
        r'^main\.py$',
        r'^requirements\.txt$',
        r'^pyproject\.toml$',
        r'^Dockerfile$',
        r'^docker-compose.*\.yml$',
        r'^Makefile$',
        r'^README\.md$'
    ]
    
    TEST_PATTERNS = [
        r'^tests/.*\.py$',
        r'^.*_test\.py$',
        r'^test_.*\.py$'  # When in tests/ directory
    ]
    
    CONFIG_PATTERNS = [
        r'^\.env.*$',
        r'^.*\.json$',
        r'^.*\.yaml$',
        r'^.*\.yml$',
        r'^.*\.toml$',
        r'^.*\.ini$'
    ]
    
    DOCUMENTATION_PATTERNS = [
        r'^.*\.md$',
        r'^docs/.*$',
        r'^LICENSE$',
        r'^CHANGELOG$'
    ]
    
    def __init__(self, root_path: Path):
        """Initialize analyzer with project root path."""
        self.root_path = Path(root_path)
        self.exclude_dirs = {'.git', '.venv', '__pycache__', 'node_modules', '.hypothesis'}
        
    def scan_directory(self) -> FileInventory:
        """Scan directory and categorize all files."""
        logger.info(f"Starting directory scan of {self.root_path}")
        
        all_files = []
        for file_path in self._get_all_files():
            try:
                file_info = self._analyze_file(file_path)
                all_files.append(file_info)
            except Exception as e:
                logger.warning(f"Error analyzing {file_path}: {e}")
        
        # Categorize files
        temporary_files = [f for f in all_files if f.category == 'temporary']
        production_files = [f for f in all_files if f.category == 'production']
        test_files = [f for f in all_files if f.category == 'test']
        config_files = [f for f in all_files if f.category == 'config']
        documentation_files = [f for f in all_files if f.category == 'documentation']
        
        # Find duplicates
        duplicate_groups = self._find_duplicates(all_files)
        
        inventory = FileInventory(
            total_files=len(all_files),
            temporary_files=temporary_files,
            production_files=production_files,
            test_files=test_files,
            config_files=config_files,
            documentation_files=documentation_files,
            duplicate_groups=duplicate_groups
        )
        
        logger.info(f"Scan complete: {len(all_files)} files analyzed")
        logger.info(f"Categories: {len(temporary_files)} temporary, {len(production_files)} production, "
                   f"{len(test_files)} test, {len(config_files)} config, {len(documentation_files)} docs")
        
        return inventory
    
    def _get_all_files(self) -> List[Path]:
        """Get all files in the directory, excluding certain directories."""
        files = []
        for root, dirs, filenames in os.walk(self.root_path):
            # Remove excluded directories from dirs list to prevent traversal
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for filename in filenames:
                file_path = Path(root) / filename
                files.append(file_path)
        
        return files
    
    def _analyze_file(self, file_path: Path) -> FileInfo:
        """Analyze a single file and determine its category."""
        relative_path = file_path.relative_to(self.root_path)
        relative_str = str(relative_path).replace('\\', '/')
        
        # Get file size
        try:
            size = file_path.stat().st_size
        except OSError:
            size = 0
        
        # Calculate content hash for duplicate detection
        content_hash = self._calculate_hash(file_path)
        
        # Determine category
        category = self._categorize_file(relative_str, file_path)
        
        return FileInfo(
            path=relative_path,
            size=size,
            category=category,
            content_hash=content_hash
        )
    
    def _categorize_file(self, relative_path: str, file_path: Path) -> str:
        """Categorize a file based on its path and patterns."""
        # Check if it's a temporary file (highest priority)
        for pattern in self.TEMPORARY_PATTERNS:
            if re.match(pattern, relative_path) or re.match(pattern, file_path.name):
                # Special case: test files in root are temporary, in tests/ are production
                if file_path.name.startswith('test_') and 'tests/' in relative_path:
                    return 'test'
                return 'temporary'
        
        # Check production patterns
        for pattern in self.PRODUCTION_PATTERNS:
            if re.match(pattern, relative_path):
                return 'production'
        
        # Check test patterns
        for pattern in self.TEST_PATTERNS:
            if re.match(pattern, relative_path):
                return 'test'
        
        # Check config patterns
        for pattern in self.CONFIG_PATTERNS:
            if re.match(pattern, relative_path):
                return 'config'
        
        # Check documentation patterns
        for pattern in self.DOCUMENTATION_PATTERNS:
            if re.match(pattern, relative_path):
                return 'documentation'
        
        # Default to production if no pattern matches
        return 'production'
    
    def _calculate_hash(self, file_path: Path) -> Optional[str]:
        """Calculate SHA-256 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.sha256(content).hexdigest()
        except Exception:
            return None
    
    def _find_duplicates(self, files: List[FileInfo]) -> Dict[str, List[FileInfo]]:
        """Find duplicate files based on content hash."""
        hash_groups = {}
        
        for file_info in files:
            if file_info.content_hash:
                if file_info.content_hash not in hash_groups:
                    hash_groups[file_info.content_hash] = []
                hash_groups[file_info.content_hash].append(file_info)
        
        # Only keep groups with more than one file
        duplicate_groups = {
            hash_val: files_list 
            for hash_val, files_list in hash_groups.items() 
            if len(files_list) > 1
        }
        
        # Mark files as duplicates
        for group_files in duplicate_groups.values():
            for file_info in group_files:
                file_info.is_duplicate = True
                file_info.duplicate_group = file_info.content_hash
        
        return duplicate_groups


class BackupManager:
    """Manages backup operations for cleanup process."""
    
    def __init__(self, backup_root: Path = Path("cleanup_backups")):
        """Initialize backup manager."""
        self.backup_root = backup_root
        self.backup_root.mkdir(exist_ok=True)
    
    def create_backup(self, files: List[FileInfo], root_path: Path) -> BackupManifest:
        """Create backup of specified files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = self.backup_root / f"backup_{timestamp}"
        backup_dir.mkdir(exist_ok=True)
        
        backed_up_files = []
        total_size = 0
        
        logger.info(f"Creating backup in {backup_dir}")
        
        for file_info in files:
            try:
                source_path = root_path / file_info.path
                backup_path = backup_dir / file_info.path
                
                # Create parent directories
                backup_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file
                shutil.copy2(source_path, backup_path)
                
                backed_up_files.append(file_info.to_dict())
                total_size += file_info.size
                
                logger.debug(f"Backed up: {file_info.path}")
                
            except Exception as e:
                logger.error(f"Failed to backup {file_info.path}: {e}")
        
        manifest = BackupManifest(
            timestamp=timestamp,
            backup_directory=str(backup_dir),
            files_backed_up=backed_up_files,
            total_size=total_size
        )
        
        # Save manifest
        manifest_path = backup_dir / "manifest.json"
        manifest.save(manifest_path)
        
        logger.info(f"Backup complete: {len(backed_up_files)} files, {total_size} bytes")
        return manifest
    
    def restore_backup(self, manifest_path: Path, root_path: Path) -> bool:
        """Restore files from backup using manifest."""
        try:
            manifest = BackupManifest.load(manifest_path)
            backup_dir = Path(manifest.backup_directory)
            
            logger.info(f"Restoring backup from {backup_dir}")
            
            for file_dict in manifest.files_backed_up:
                backup_file = backup_dir / file_dict['path']
                restore_path = root_path / file_dict['path']
                
                # Create parent directories
                restore_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file back
                shutil.copy2(backup_file, restore_path)
                logger.debug(f"Restored: {file_dict['path']}")
            
            logger.info("Backup restoration complete")
            return True
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False


def main():
    """Main function for testing the infrastructure."""
    root_path = Path(".")
    
    # Initialize analyzer
    analyzer = FileAnalyzer(root_path)
    
    # Scan directory
    inventory = analyzer.scan_directory()
    
    # Save inventory to file
    inventory_path = Path("file_inventory.json")
    with open(inventory_path, 'w') as f:
        json.dump(inventory.to_dict(), f, indent=2)
    
    print(f"File inventory saved to {inventory_path}")
    print(f"Found {inventory.total_files} total files:")
    print(f"  - {len(inventory.temporary_files)} temporary files")
    print(f"  - {len(inventory.production_files)} production files")
    print(f"  - {len(inventory.test_files)} test files")
    print(f"  - {len(inventory.config_files)} config files")
    print(f"  - {len(inventory.documentation_files)} documentation files")
    print(f"  - {len(inventory.duplicate_groups)} duplicate groups")


if __name__ == "__main__":
    main()