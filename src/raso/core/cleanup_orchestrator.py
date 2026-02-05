#!/usr/bin/env python3
"""
Cleanup Orchestrator for RASO Codebase
Manages the systematic removal and reorganization of files with backup and rollback capabilities.
"""

import json
import logging
import shutil
from pathlib import Path
from typing import List, Dict, Set, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

from cleanup_infrastructure import FileAnalyzer, FileInfo, BackupManager, BackupManifest

logger = logging.getLogger(__name__)


@dataclass
class CleanupResult:
    """Results of cleanup operations."""
    files_removed: int
    files_moved: int
    duplicates_consolidated: int
    backup_manifest: Optional[str]
    validation_passed: bool
    errors: List[str]
    size_freed: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class ConsolidationResult:
    """Results of duplicate consolidation operations."""
    groups_processed: int
    files_removed: int
    files_kept: int
    size_saved: int
    errors: List[str]


class CleanupOrchestrator:
    """Orchestrates the complete cleanup process with safety measures."""
    
    def __init__(self, root_path: Path, backup_enabled: bool = True):
        """Initialize cleanup orchestrator."""
        self.root_path = Path(root_path)
        self.backup_enabled = backup_enabled
        self.analyzer = FileAnalyzer(root_path)
        self.backup_manager = BackupManager() if backup_enabled else None
        self.dry_run = False
        
    def set_dry_run(self, enabled: bool) -> None:
        """Enable/disable dry run mode (no actual file operations)."""
        self.dry_run = enabled
        logger.info(f"Dry run mode: {'enabled' if enabled else 'disabled'}")
    
    def cleanup_temporary_files(self) -> CleanupResult:
        """Remove all temporary files with backup."""
        logger.info("Starting temporary file cleanup")
        
        # Get file inventory
        inventory = self.analyzer.scan_directory()
        temporary_files = inventory.temporary_files
        
        if not temporary_files:
            logger.info("No temporary files found")
            return CleanupResult(
                files_removed=0,
                files_moved=0,
                duplicates_consolidated=0,
                backup_manifest=None,
                validation_passed=True,
                errors=[],
                size_freed=0
            )
        
        logger.info(f"Found {len(temporary_files)} temporary files to remove")
        
        # Create backup if enabled
        backup_manifest = None
        if self.backup_enabled and not self.dry_run:
            try:
                manifest = self.backup_manager.create_backup(temporary_files, self.root_path)
                backup_manifest = manifest.backup_directory
                logger.info(f"Backup created: {backup_manifest}")
            except Exception as e:
                logger.error(f"Backup failed: {e}")
                return CleanupResult(
                    files_removed=0,
                    files_moved=0,
                    duplicates_consolidated=0,
                    backup_manifest=None,
                    validation_passed=False,
                    errors=[f"Backup failed: {e}"],
                    size_freed=0
                )
        
        # Remove temporary files
        files_removed = 0
        size_freed = 0
        errors = []
        
        for file_info in temporary_files:
            try:
                file_path = self.root_path / file_info.path
                
                if self.dry_run:
                    logger.info(f"DRY RUN: Would remove {file_info.path}")
                    files_removed += 1
                    size_freed += file_info.size
                else:
                    if file_path.exists():
                        file_path.unlink()
                        files_removed += 1
                        size_freed += file_info.size
                        logger.debug(f"Removed: {file_info.path}")
                    else:
                        logger.warning(f"File not found: {file_info.path}")
                        
            except Exception as e:
                error_msg = f"Failed to remove {file_info.path}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        # Validate cleanup
        validation_passed = self._validate_cleanup(temporary_files) if not self.dry_run else True
        
        result = CleanupResult(
            files_removed=files_removed,
            files_moved=0,
            duplicates_consolidated=0,
            backup_manifest=backup_manifest,
            validation_passed=validation_passed,
            errors=errors,
            size_freed=size_freed
        )
        
        logger.info(f"Temporary file cleanup complete: {files_removed} files removed, "
                   f"{size_freed:,} bytes freed")
        
        return result
    
    def consolidate_duplicates(self, keep_strategy: str = "primary") -> ConsolidationResult:
        """Consolidate duplicate files based on strategy."""
        logger.info(f"Starting duplicate consolidation with strategy: {keep_strategy}")
        
        # Get file inventory
        inventory = self.analyzer.scan_directory()
        duplicate_groups = inventory.duplicate_groups
        
        if not duplicate_groups:
            logger.info("No duplicate files found")
            return ConsolidationResult(
                groups_processed=0,
                files_removed=0,
                files_kept=0,
                size_saved=0,
                errors=[]
            )
        
        groups_processed = 0
        files_removed = 0
        files_kept = 0
        size_saved = 0
        errors = []
        
        for hash_val, duplicate_files in duplicate_groups.items():
            try:
                # Select which file to keep
                keep_file, remove_files = self._select_files_to_keep(duplicate_files, keep_strategy)
                
                if not remove_files:
                    continue
                
                # Remove duplicate files
                for file_info in remove_files:
                    try:
                        file_path = self.root_path / file_info.path
                        
                        if self.dry_run:
                            logger.info(f"DRY RUN: Would remove duplicate {file_info.path}")
                            files_removed += 1
                            size_saved += file_info.size
                        else:
                            if file_path.exists():
                                file_path.unlink()
                                files_removed += 1
                                size_saved += file_info.size
                                logger.debug(f"Removed duplicate: {file_info.path}")
                            else:
                                logger.warning(f"Duplicate file not found: {file_info.path}")
                                
                    except Exception as e:
                        error_msg = f"Failed to remove duplicate {file_info.path}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                
                files_kept += 1
                groups_processed += 1
                logger.debug(f"Kept: {keep_file.path}, removed {len(remove_files)} duplicates")
                
            except Exception as e:
                error_msg = f"Failed to process duplicate group {hash_val}: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = ConsolidationResult(
            groups_processed=groups_processed,
            files_removed=files_removed,
            files_kept=files_kept,
            size_saved=size_saved,
            errors=errors
        )
        
        logger.info(f"Duplicate consolidation complete: {groups_processed} groups processed, "
                   f"{files_removed} files removed, {size_saved:,} bytes saved")
        
        return result
    
    def _select_files_to_keep(self, duplicate_files: List[FileInfo], strategy: str) -> Tuple[FileInfo, List[FileInfo]]:
        """Select which file to keep and which to remove from duplicates."""
        if len(duplicate_files) <= 1:
            return duplicate_files[0] if duplicate_files else None, []
        
        if strategy == "primary":
            # Keep the first non-backup, non-temporary file
            primary_candidates = []
            backup_files = []
            
            for file_info in duplicate_files:
                path_str = str(file_info.path).lower()
                if 'backup' in path_str or '_backup' in path_str or '.backup' in path_str:
                    backup_files.append(file_info)
                elif file_info.category == 'temporary':
                    backup_files.append(file_info)
                else:
                    primary_candidates.append(file_info)
            
            # If we have primary candidates, keep the first one
            if primary_candidates:
                keep_file = primary_candidates[0]
                remove_files = primary_candidates[1:] + backup_files
            else:
                # All are backups/temporary, keep the first one
                keep_file = duplicate_files[0]
                remove_files = duplicate_files[1:]
                
        elif strategy == "newest":
            # Keep the newest file (by modification time)
            try:
                files_with_mtime = []
                for file_info in duplicate_files:
                    file_path = self.root_path / file_info.path
                    if file_path.exists():
                        mtime = file_path.stat().st_mtime
                        files_with_mtime.append((file_info, mtime))
                
                if files_with_mtime:
                    files_with_mtime.sort(key=lambda x: x[1], reverse=True)
                    keep_file = files_with_mtime[0][0]
                    remove_files = [f[0] for f in files_with_mtime[1:]]
                else:
                    keep_file = duplicate_files[0]
                    remove_files = duplicate_files[1:]
                    
            except Exception:
                # Fallback to primary strategy
                return self._select_files_to_keep(duplicate_files, "primary")
                
        elif strategy == "production":
            # Keep production files over others
            production_files = [f for f in duplicate_files if f.category == 'production']
            non_production_files = [f for f in duplicate_files if f.category != 'production']
            
            if production_files:
                keep_file = production_files[0]
                remove_files = production_files[1:] + non_production_files
            else:
                keep_file = duplicate_files[0]
                remove_files = duplicate_files[1:]
                
        else:
            # Default: keep first file
            keep_file = duplicate_files[0]
            remove_files = duplicate_files[1:]
        
        return keep_file, remove_files
    
    def _validate_cleanup(self, removed_files: List[FileInfo]) -> bool:
        """Validate that cleanup was successful."""
        try:
            # Check that removed files no longer exist
            for file_info in removed_files:
                file_path = self.root_path / file_info.path
                if file_path.exists():
                    logger.error(f"Validation failed: {file_info.path} still exists")
                    return False
            
            # Check root directory file count
            root_files = [f for f in self.root_path.iterdir() if f.is_file()]
            if len(root_files) >= 30:
                logger.warning(f"Root directory still has {len(root_files)} files (target: <30)")
                # Don't fail validation for this, just warn
            
            logger.info("Cleanup validation passed")
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def rollback_cleanup(self, backup_manifest_path: Path) -> bool:
        """Rollback cleanup using backup manifest."""
        if not self.backup_manager:
            logger.error("Backup manager not available for rollback")
            return False
        
        try:
            success = self.backup_manager.restore_backup(backup_manifest_path, self.root_path)
            if success:
                logger.info("Cleanup rollback completed successfully")
            else:
                logger.error("Cleanup rollback failed")
            return success
            
        except Exception as e:
            logger.error(f"Rollback error: {e}")
            return False
    
    def get_cleanup_preview(self) -> Dict:
        """Get preview of what cleanup would do without making changes."""
        logger.info("Generating cleanup preview")
        
        # Get file inventory
        inventory = self.analyzer.scan_directory()
        
        # Calculate potential impact
        temporary_files = inventory.temporary_files
        duplicate_groups = inventory.duplicate_groups
        
        temp_size = sum(f.size for f in temporary_files)
        duplicate_size = sum(
            sum(f.size for f in files[1:])  # Size of all but first file in each group
            for files in duplicate_groups.values()
        )
        
        preview = {
            'temporary_files': {
                'count': len(temporary_files),
                'size_bytes': temp_size,
                'files': [str(f.path) for f in temporary_files[:10]]  # First 10 for preview
            },
            'duplicate_files': {
                'groups': len(duplicate_groups),
                'total_duplicates': sum(len(files) - 1 for files in duplicate_groups.values()),
                'size_savings_bytes': duplicate_size
            },
            'total_impact': {
                'files_to_remove': len(temporary_files) + sum(len(files) - 1 for files in duplicate_groups.values()),
                'total_size_freed': temp_size + duplicate_size
            }
        }
        
        logger.info(f"Preview: {preview['total_impact']['files_to_remove']} files to remove, "
                   f"{preview['total_impact']['total_size_freed']:,} bytes to free")
        
        return preview


def main():
    """Main function for testing cleanup orchestrator."""
    root_path = Path(".")
    
    # Initialize orchestrator
    orchestrator = CleanupOrchestrator(root_path, backup_enabled=True)
    
    # Enable dry run for testing
    orchestrator.set_dry_run(True)
    
    # Get cleanup preview
    preview = orchestrator.get_cleanup_preview()
    
    # Save preview
    preview_path = Path("cleanup_preview.json")
    with open(preview_path, 'w') as f:
        json.dump(preview, f, indent=2)
    
    print(f"Cleanup preview saved to {preview_path}")
    print(f"\nCleanup Preview:")
    print(f"  Temporary files: {preview['temporary_files']['count']} files, {preview['temporary_files']['size_bytes']:,} bytes")
    print(f"  Duplicate groups: {preview['duplicate_files']['groups']} groups, {preview['duplicate_files']['total_duplicates']} duplicates")
    print(f"  Total impact: {preview['total_impact']['files_to_remove']} files, {preview['total_impact']['total_size_freed']:,} bytes")
    
    # Test temporary file cleanup (dry run)
    print(f"\nTesting temporary file cleanup (dry run)...")
    temp_result = orchestrator.cleanup_temporary_files()
    print(f"  Would remove: {temp_result.files_removed} files")
    print(f"  Would free: {temp_result.size_freed:,} bytes")
    print(f"  Errors: {len(temp_result.errors)}")
    
    # Test duplicate consolidation (dry run)
    print(f"\nTesting duplicate consolidation (dry run)...")
    dup_result = orchestrator.consolidate_duplicates()
    print(f"  Would process: {dup_result.groups_processed} groups")
    print(f"  Would remove: {dup_result.files_removed} duplicates")
    print(f"  Would save: {dup_result.size_saved:,} bytes")
    print(f"  Errors: {len(dup_result.errors)}")


if __name__ == "__main__":
    main()