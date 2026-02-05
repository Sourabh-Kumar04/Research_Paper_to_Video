"""
Content Versioning and History Manager

This module provides comprehensive content versioning capabilities,
tracking all generated content versions, generation parameters,
and providing diff functionality and rollback capabilities.
"""

import os
import json
import hashlib
import shutil
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
import logging
import difflib

logger = logging.getLogger(__name__)

@dataclass
class GenerationParameters:
    """Parameters used for content generation"""
    model_name: str
    model_version: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    prompt_template: Optional[str] = None
    quality_preset: Optional[str] = None
    custom_params: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.custom_params is None:
            self.custom_params = {}

@dataclass
class ContentVersion:
    """Represents a version of generated content"""
    version_id: str
    content_type: str  # "video", "audio", "script", "animation", etc.
    file_path: str
    created_at: str
    generation_params: GenerationParameters
    file_hash: str
    file_size: int
    metadata: Dict[str, Any] = None
    parent_version: Optional[str] = None
    tags: List[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.tags is None:
            self.tags = []

@dataclass
class ContentDiff:
    """Represents differences between content versions"""
    from_version: str
    to_version: str
    diff_type: str  # "text", "binary", "metadata"
    changes: List[str]
    similarity_score: float
    created_at: str

class ContentVersionManager:
    """
    Manages content versioning and history tracking
    """
    
    def __init__(self, base_path: str = "content_versions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Version storage
        self.versions_dir = self.base_path / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # Metadata storage
        self.metadata_file = self.base_path / "version_metadata.json"
        self.versions_metadata = self._load_versions_metadata()
        
        # Diff cache
        self.diff_cache_dir = self.base_path / "diffs"
        self.diff_cache_dir.mkdir(exist_ok=True)
        
    def _load_versions_metadata(self) -> Dict[str, Dict]:
        """Load version metadata from disk"""
        if self.metadata_file.exists():
            try:
                with open(self.metadata_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load version metadata: {e}")
        return {}
    
    def _save_versions_metadata(self):
        """Save version metadata to disk"""
        try:
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(self.versions_metadata, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save version metadata: {e}")
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of a file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate hash for {file_path}: {e}")
            return ""
    
    def _generate_version_id(self, content_type: str, file_path: str) -> str:
        """Generate unique version ID"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        content_hash = hashlib.md5(f"{content_type}_{file_path}_{timestamp}".encode()).hexdigest()[:8]
        return f"{content_type}_{timestamp}_{content_hash}"
    
    def create_version(self, 
                      content_type: str,
                      file_path: str,
                      generation_params: GenerationParameters,
                      metadata: Optional[Dict[str, Any]] = None,
                      parent_version: Optional[str] = None,
                      tags: Optional[List[str]] = None) -> ContentVersion:
        """
        Create a new content version
        
        Args:
            content_type: Type of content (video, audio, script, etc.)
            file_path: Path to the content file
            generation_params: Parameters used for generation
            metadata: Additional metadata
            parent_version: ID of parent version (for tracking lineage)
            tags: Tags for categorization
            
        Returns:
            ContentVersion object
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Content file not found: {file_path}")
        
        # Generate version ID
        version_id = self._generate_version_id(content_type, str(file_path))
        
        # Calculate file properties
        file_hash = self._calculate_file_hash(file_path)
        file_size = file_path.stat().st_size
        
        # Create version directory
        version_dir = self.versions_dir / version_id
        version_dir.mkdir(exist_ok=True)
        
        # Copy content file to version storage
        stored_file_path = version_dir / file_path.name
        shutil.copy2(file_path, stored_file_path)
        
        # Create version object
        version = ContentVersion(
            version_id=version_id,
            content_type=content_type,
            file_path=str(stored_file_path),
            created_at=datetime.now().isoformat(),
            generation_params=generation_params,
            file_hash=file_hash,
            file_size=file_size,
            metadata=metadata or {},
            parent_version=parent_version,
            tags=tags or []
        )
        
        # Store version metadata
        self.versions_metadata[version_id] = asdict(version)
        self._save_versions_metadata()
        
        # Save generation parameters separately for easy access
        params_file = version_dir / "generation_params.json"
        with open(params_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(generation_params), f, indent=2)
        
        logger.info(f"Created content version: {version_id}")
        return version
    
    def get_version(self, version_id: str) -> Optional[ContentVersion]:
        """
        Get a specific content version
        
        Args:
            version_id: Version identifier
            
        Returns:
            ContentVersion object or None if not found
        """
        if version_id not in self.versions_metadata:
            return None
        
        version_data = self.versions_metadata[version_id]
        
        # Reconstruct GenerationParameters
        params_data = version_data['generation_params']
        generation_params = GenerationParameters(**params_data)
        
        # Create ContentVersion object
        version = ContentVersion(
            version_id=version_data['version_id'],
            content_type=version_data['content_type'],
            file_path=version_data['file_path'],
            created_at=version_data['created_at'],
            generation_params=generation_params,
            file_hash=version_data['file_hash'],
            file_size=version_data['file_size'],
            metadata=version_data.get('metadata', {}),
            parent_version=version_data.get('parent_version'),
            tags=version_data.get('tags', [])
        )
        
        return version
    
    def list_versions(self, 
                     content_type: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     limit: Optional[int] = None) -> List[ContentVersion]:
        """
        List content versions with optional filtering
        
        Args:
            content_type: Filter by content type
            tags: Filter by tags (must have all specified tags)
            limit: Maximum number of versions to return
            
        Returns:
            List of ContentVersion objects
        """
        versions = []
        
        for version_id, version_data in self.versions_metadata.items():
            # Apply filters
            if content_type and version_data['content_type'] != content_type:
                continue
            
            if tags:
                version_tags = set(version_data.get('tags', []))
                if not set(tags).issubset(version_tags):
                    continue
            
            version = self.get_version(version_id)
            if version:
                versions.append(version)
        
        # Sort by creation time (newest first)
        versions.sort(key=lambda v: v.created_at, reverse=True)
        
        if limit:
            versions = versions[:limit]
        
        return versions
    
    def get_version_history(self, version_id: str) -> List[ContentVersion]:
        """
        Get the complete history chain for a version
        
        Args:
            version_id: Starting version ID
            
        Returns:
            List of versions in chronological order (oldest first)
        """
        history = []
        current_version = self.get_version(version_id)
        
        # Build history chain by following parent versions
        while current_version:
            history.insert(0, current_version)  # Insert at beginning for chronological order
            
            if current_version.parent_version:
                current_version = self.get_version(current_version.parent_version)
            else:
                break
        
        return history
    
    def compare_versions(self, version1_id: str, version2_id: str) -> Optional[ContentDiff]:
        """
        Compare two content versions
        
        Args:
            version1_id: First version ID
            version2_id: Second version ID
            
        Returns:
            ContentDiff object or None if comparison fails
        """
        version1 = self.get_version(version1_id)
        version2 = self.get_version(version2_id)
        
        if not version1 or not version2:
            logger.error(f"One or both versions not found: {version1_id}, {version2_id}")
            return None
        
        # Check if diff is cached
        diff_cache_file = self.diff_cache_dir / f"{version1_id}_{version2_id}.json"
        if diff_cache_file.exists():
            try:
                with open(diff_cache_file, 'r', encoding='utf-8') as f:
                    diff_data = json.load(f)
                    return ContentDiff(**diff_data)
            except Exception as e:
                logger.warning(f"Failed to load cached diff: {e}")
        
        # Determine diff type and perform comparison
        if version1.content_type != version2.content_type:
            logger.warning(f"Comparing different content types: {version1.content_type} vs {version2.content_type}")
        
        changes = []
        similarity_score = 0.0
        diff_type = "binary"
        
        try:
            file1_path = Path(version1.file_path)
            file2_path = Path(version2.file_path)
            
            # Try text comparison for certain file types
            text_extensions = {'.txt', '.py', '.js', '.html', '.css', '.json', '.md', '.yml', '.yaml'}
            if file1_path.suffix.lower() in text_extensions and file2_path.suffix.lower() in text_extensions:
                diff_type = "text"
                
                with open(file1_path, 'r', encoding='utf-8') as f1, open(file2_path, 'r', encoding='utf-8') as f2:
                    lines1 = f1.readlines()
                    lines2 = f2.readlines()
                
                # Generate unified diff
                diff = list(difflib.unified_diff(
                    lines1, lines2,
                    fromfile=f"Version {version1_id}",
                    tofile=f"Version {version2_id}",
                    lineterm=''
                ))
                
                changes = diff
                
                # Calculate similarity score
                matcher = difflib.SequenceMatcher(None, ''.join(lines1), ''.join(lines2))
                similarity_score = matcher.ratio()
            
            else:
                # Binary comparison
                if version1.file_hash == version2.file_hash:
                    similarity_score = 1.0
                    changes = ["Files are identical"]
                else:
                    similarity_score = 0.0 if version1.file_size != version2.file_size else 0.5
                    changes = [
                        f"File size: {version1.file_size} -> {version2.file_size}",
                        f"Hash: {version1.file_hash[:16]}... -> {version2.file_hash[:16]}..."
                    ]
        
        except Exception as e:
            logger.error(f"Failed to compare versions: {e}")
            changes = [f"Comparison failed: {str(e)}"]
        
        # Create diff object
        content_diff = ContentDiff(
            from_version=version1_id,
            to_version=version2_id,
            diff_type=diff_type,
            changes=changes,
            similarity_score=similarity_score,
            created_at=datetime.now().isoformat()
        )
        
        # Cache the diff
        try:
            with open(diff_cache_file, 'w', encoding='utf-8') as f:
                json.dump(asdict(content_diff), f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to cache diff: {e}")
        
        return content_diff
    
    def rollback_to_version(self, version_id: str, target_path: str) -> bool:
        """
        Rollback content to a specific version
        
        Args:
            version_id: Version to rollback to
            target_path: Path where to restore the content
            
        Returns:
            True if rollback successful, False otherwise
        """
        version = self.get_version(version_id)
        if not version:
            logger.error(f"Version not found: {version_id}")
            return False
        
        try:
            source_path = Path(version.file_path)
            target_path = Path(target_path)
            
            if not source_path.exists():
                logger.error(f"Version file not found: {source_path}")
                return False
            
            # Create target directory if needed
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy version file to target location
            shutil.copy2(source_path, target_path)
            
            logger.info(f"Successfully rolled back to version {version_id} at {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to rollback to version {version_id}: {e}")
            return False
    
    def delete_version(self, version_id: str, keep_file: bool = False) -> bool:
        """
        Delete a content version
        
        Args:
            version_id: Version to delete
            keep_file: Whether to keep the actual file
            
        Returns:
            True if deletion successful, False otherwise
        """
        if version_id not in self.versions_metadata:
            logger.warning(f"Version not found: {version_id}")
            return False
        
        try:
            # Remove version directory if not keeping file
            if not keep_file:
                version_dir = self.versions_dir / version_id
                if version_dir.exists():
                    shutil.rmtree(version_dir)
            
            # Remove from metadata
            del self.versions_metadata[version_id]
            self._save_versions_metadata()
            
            # Clean up diff cache
            for diff_file in self.diff_cache_dir.glob(f"*{version_id}*"):
                diff_file.unlink()
            
            logger.info(f"Deleted version: {version_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete version {version_id}: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get versioning statistics
        
        Returns:
            Dictionary with version statistics
        """
        stats = {
            'total_versions': len(self.versions_metadata),
            'content_types': {},
            'total_size_mb': 0,
            'versions_by_date': {},
            'most_recent_versions': [],
            'generation_models': {}
        }
        
        for version_data in self.versions_metadata.values():
            # Count by content type
            content_type = version_data['content_type']
            stats['content_types'][content_type] = stats['content_types'].get(content_type, 0) + 1
            
            # Calculate total size
            stats['total_size_mb'] += version_data['file_size'] / (1024 * 1024)
            
            # Count by date
            date = version_data['created_at'][:10]  # Extract date part
            stats['versions_by_date'][date] = stats['versions_by_date'].get(date, 0) + 1
            
            # Track generation models
            model_name = version_data['generation_params']['model_name']
            stats['generation_models'][model_name] = stats['generation_models'].get(model_name, 0) + 1
        
        # Get most recent versions
        recent_versions = sorted(
            self.versions_metadata.items(),
            key=lambda x: x[1]['created_at'],
            reverse=True
        )[:10]
        
        stats['most_recent_versions'] = [
            {
                'version_id': vid,
                'content_type': vdata['content_type'],
                'created_at': vdata['created_at']
            }
            for vid, vdata in recent_versions
        ]
        
        return stats

# Example usage and testing
if __name__ == "__main__":
    # Example usage
    manager = ContentVersionManager()
    
    # Create test generation parameters
    params = GenerationParameters(
        model_name="gpt-4",
        model_version="2024-01",
        temperature=0.7,
        max_tokens=1000,
        quality_preset="high"
    )
    
    # Create a test file
    test_file = Path("test_content.txt")
    test_file.write_text("This is test content for versioning.")
    
    try:
        # Create version
        version = manager.create_version(
            content_type="script",
            file_path=str(test_file),
            generation_params=params,
            metadata={"purpose": "testing"},
            tags=["test", "script"]
        )
        
        print(f"Created version: {version.version_id}")
        
        # List versions
        versions = manager.list_versions(content_type="script")
        print(f"Found {len(versions)} script versions")
        
        # Get statistics
        stats = manager.get_statistics()
        print(f"Statistics: {stats}")
        
    finally:
        # Cleanup
        if test_file.exists():
            test_file.unlink()