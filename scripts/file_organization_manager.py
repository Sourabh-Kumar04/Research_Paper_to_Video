"""
Intelligent file organization system for production video generation.
Implements industry-standard folder structure and asset management.
"""

import os
import re
import hashlib
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import json

logger = logging.getLogger(__name__)


class FileOrganizationManager:
    """Manages intelligent file organization and asset storage."""
    
    def __init__(self, base_path: str = "data"):
        """Initialize file organization manager."""
        self.base_path = Path(base_path)
        self.setup_directory_structure()
    
    def setup_directory_structure(self):
        """Create the standard directory structure."""
        directories = [
            # Main paper storage
            "papers",
            
            # Video assets
            "videos/final",
            "videos/scenes", 
            "videos/drafts",
            "videos/thumbnails",
            
            # Audio assets
            "audio/narration",
            "audio/music",
            "audio/effects",
            "audio/raw",
            
            # Visual assets
            "visuals/animations",
            "visuals/slides",
            "visuals/diagrams",
            "visuals/3d_models",
            "visuals/charts",
            
            # Generated code
            "code/manim",
            "code/motion_canvas",
            "code/remotion",
            "code/blender",
            
            # Metadata and configs
            "metadata",
            "configs",
            "templates",
            
            # Temporary and cache
            "temp",
            "cache",
            
            # Backups
            "backups/daily",
            "backups/weekly",
            "backups/monthly"
        ]
        
        for directory in directories:
            dir_path = self.base_path / directory
            dir_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Directory structure created at: {self.base_path}")
    
    def sanitize_filename(self, filename: str, max_length: int = 100) -> str:
        """Sanitize filename for filesystem compatibility."""
        # Remove or replace problematic characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        
        # Replace multiple spaces with single space
        sanitized = re.sub(r'\s+', ' ', sanitized)
        
        # Remove leading/trailing spaces and dots
        sanitized = sanitized.strip(' .')
        
        # Limit length
        if len(sanitized) > max_length:
            sanitized = sanitized[:max_length].rsplit(' ', 1)[0]
        
        # Ensure not empty
        if not sanitized:
            sanitized = "untitled"
        
        return sanitized
    
    def create_paper_folder(self, title: str, authors: List[str], 
                           publication_year: Optional[int] = None) -> str:
        """Create organized folder for a research paper."""
        # Determine year
        year = publication_year or datetime.now().year
        
        # Get first author's last name
        first_author = authors[0] if authors else "Unknown"
        author_lastname = first_author.split()[-1] if ' ' in first_author else first_author
        
        # Sanitize title
        sanitized_title = self.sanitize_filename(title, max_length=80)
        
        # Create folder name: [YEAR]/[AUTHOR_LASTNAME]_[SANITIZED_TITLE]
        folder_name = f"{self.sanitize_filename(author_lastname)}_{sanitized_title}"
        paper_path = self.base_path / "papers" / str(year) / folder_name
        
        # Handle duplicates
        counter = 1
        original_path = paper_path
        while paper_path.exists():
            paper_path = original_path.parent / f"{original_path.name}_{counter}"
            counter += 1
        
        # Create the folder structure
        paper_path.mkdir(parents=True, exist_ok=True)
        
        # Create subfolders for this paper
        subfolders = [
            "original",      # Original PDF and source files
            "processed",     # Processed content and extracted data
            "generated",     # All generated content
            "videos",        # Final videos
            "audio",         # Audio files
            "visuals",       # Visual assets
            "code",          # Generated code
            "metadata"       # Metadata and configuration files
        ]
        
        for subfolder in subfolders:
            (paper_path / subfolder).mkdir(exist_ok=True)
        
        # Create metadata file
        metadata = {
            "title": title,
            "authors": authors,
            "publication_year": year,
            "folder_created": datetime.now().isoformat(),
            "folder_path": str(paper_path.relative_to(self.base_path)),
            "folder_name": folder_name
        }
        
        metadata_file = paper_path / "metadata" / "paper_info.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Created paper folder: {paper_path}")
        return str(paper_path.relative_to(self.base_path))
    
    def get_asset_path(self, paper_folder: str, asset_type: str, 
                      filename: str, create_dirs: bool = True) -> str:
        """Get standardized path for an asset."""
        paper_path = self.base_path / paper_folder
        
        # Define asset type mappings
        asset_mappings = {
            # Video assets
            "final_video": "videos",
            "scene_video": "videos",
            "draft_video": "videos",
            "thumbnail": "videos",
            
            # Audio assets
            "narration": "audio",
            "music": "audio", 
            "effects": "audio",
            "raw_audio": "audio",
            
            # Visual assets
            "animation": "visuals",
            "slide": "visuals",
            "diagram": "visuals",
            "3d_model": "visuals",
            "chart": "visuals",
            
            # Code assets
            "manim_code": "code",
            "motion_canvas_code": "code",
            "remotion_code": "code",
            "blender_code": "code",
            
            # Metadata
            "metadata": "metadata",
            "config": "metadata"
        }
        
        subfolder = asset_mappings.get(asset_type, "generated")
        asset_path = paper_path / subfolder
        
        if create_dirs:
            asset_path.mkdir(parents=True, exist_ok=True)
        
        return str(asset_path / filename)
    
    def organize_existing_files(self, source_dir: str) -> Dict[str, List[str]]:
        """Organize existing files into the new structure."""
        source_path = Path(source_dir)
        organized_files = {
            "moved": [],
            "skipped": [],
            "errors": []
        }
        
        if not source_path.exists():
            logger.warning(f"Source directory does not exist: {source_dir}")
            return organized_files
        
        for file_path in source_path.rglob("*"):
            if file_path.is_file():
                try:
                    # Determine file type and destination
                    destination = self._determine_file_destination(file_path)
                    
                    if destination:
                        dest_path = self.base_path / destination
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        
                        # Move file if destination doesn't exist
                        if not dest_path.exists():
                            shutil.move(str(file_path), str(dest_path))
                            organized_files["moved"].append(str(dest_path))
                        else:
                            organized_files["skipped"].append(str(file_path))
                    else:
                        organized_files["skipped"].append(str(file_path))
                        
                except Exception as e:
                    logger.error(f"Error organizing file {file_path}: {e}")
                    organized_files["errors"].append(str(file_path))
        
        return organized_files
    
    def _determine_file_destination(self, file_path: Path) -> Optional[str]:
        """Determine appropriate destination for a file."""
        suffix = file_path.suffix.lower()
        name = file_path.name.lower()
        
        # Video files
        if suffix in ['.mp4', '.avi', '.mov', '.mkv', '.webm']:
            if 'final' in name or 'output' in name:
                return f"videos/final/{file_path.name}"
            elif 'scene' in name:
                return f"videos/scenes/{file_path.name}"
            else:
                return f"videos/drafts/{file_path.name}"
        
        # Audio files
        elif suffix in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            if 'narration' in name or 'voice' in name:
                return f"audio/narration/{file_path.name}"
            elif 'music' in name or 'background' in name:
                return f"audio/music/{file_path.name}"
            elif 'effect' in name or 'sound' in name:
                return f"audio/effects/{file_path.name}"
            else:
                return f"audio/raw/{file_path.name}"
        
        # Image files
        elif suffix in ['.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp']:
            if 'slide' in name:
                return f"visuals/slides/{file_path.name}"
            elif 'diagram' in name or 'chart' in name:
                return f"visuals/diagrams/{file_path.name}"
            else:
                return f"visuals/animations/{file_path.name}"
        
        # Code files
        elif suffix in ['.py', '.js', '.ts', '.jsx', '.tsx']:
            if 'manim' in name:
                return f"code/manim/{file_path.name}"
            elif 'motion' in name or 'canvas' in name:
                return f"code/motion_canvas/{file_path.name}"
            elif 'remotion' in name:
                return f"code/remotion/{file_path.name}"
            elif 'blender' in name:
                return f"code/blender/{file_path.name}"
            else:
                return f"code/{file_path.name}"
        
        # Document files
        elif suffix in ['.pdf', '.doc', '.docx', '.txt', '.md']:
            return f"papers/{file_path.name}"
        
        # Metadata files
        elif suffix in ['.json', '.yaml', '.yml', '.xml']:
            return f"metadata/{file_path.name}"
        
        return None
    
    def calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of a file."""
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {file_path}: {e}")
            return ""
    
    def find_duplicates(self, directory: Optional[str] = None) -> Dict[str, List[str]]:
        """Find duplicate files based on content hash."""
        search_path = Path(directory) if directory else self.base_path
        file_hashes = {}
        duplicates = {}
        
        for file_path in search_path.rglob("*"):
            if file_path.is_file():
                file_hash = self.calculate_file_hash(str(file_path))
                if file_hash:
                    if file_hash in file_hashes:
                        if file_hash not in duplicates:
                            duplicates[file_hash] = [file_hashes[file_hash]]
                        duplicates[file_hash].append(str(file_path))
                    else:
                        file_hashes[file_hash] = str(file_path)
        
        return duplicates
    
    def cleanup_empty_directories(self, directory: Optional[str] = None):
        """Remove empty directories."""
        search_path = Path(directory) if directory else self.base_path
        removed_dirs = []
        
        # Walk directories bottom-up to handle nested empty dirs
        for dir_path in sorted(search_path.rglob("*"), key=lambda p: len(p.parts), reverse=True):
            if dir_path.is_dir():
                try:
                    # Try to remove if empty
                    dir_path.rmdir()
                    removed_dirs.append(str(dir_path))
                except OSError:
                    # Directory not empty, skip
                    pass
        
        if removed_dirs:
            logger.info(f"Removed {len(removed_dirs)} empty directories")
        
        return removed_dirs
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics for the organized files."""
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "by_category": {},
            "by_extension": {},
            "largest_files": []
        }
        
        file_sizes = []
        
        for file_path in self.base_path.rglob("*"):
            if file_path.is_file():
                try:
                    size = file_path.stat().st_size
                    stats["total_files"] += 1
                    stats["total_size_bytes"] += size
                    
                    # Category stats
                    category = self._get_file_category(file_path)
                    if category not in stats["by_category"]:
                        stats["by_category"][category] = {"count": 0, "size": 0}
                    stats["by_category"][category]["count"] += 1
                    stats["by_category"][category]["size"] += size
                    
                    # Extension stats
                    ext = file_path.suffix.lower()
                    if ext not in stats["by_extension"]:
                        stats["by_extension"][ext] = {"count": 0, "size": 0}
                    stats["by_extension"][ext]["count"] += 1
                    stats["by_extension"][ext]["size"] += size
                    
                    # Track for largest files
                    file_sizes.append((str(file_path), size))
                    
                except Exception as e:
                    logger.warning(f"Error getting stats for {file_path}: {e}")
        
        # Get top 10 largest files
        file_sizes.sort(key=lambda x: x[1], reverse=True)
        stats["largest_files"] = file_sizes[:10]
        
        return stats
    
    def _get_file_category(self, file_path: Path) -> str:
        """Get category for a file based on its location."""
        parts = file_path.parts
        if len(parts) > 1:
            if "videos" in parts:
                return "videos"
            elif "audio" in parts:
                return "audio"
            elif "visuals" in parts:
                return "visuals"
            elif "code" in parts:
                return "code"
            elif "papers" in parts:
                return "papers"
            elif "metadata" in parts:
                return "metadata"
        return "other"
    
    def create_backup(self, backup_type: str = "daily") -> str:
        """Create backup of organized files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"backup_{backup_type}_{timestamp}"
        backup_path = self.base_path / "backups" / backup_type / backup_name
        
        try:
            # Create backup directory
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Copy important directories (exclude temp and cache)
            important_dirs = ["papers", "videos", "audio", "visuals", "code", "metadata"]
            
            for dir_name in important_dirs:
                source_dir = self.base_path / dir_name
                if source_dir.exists():
                    dest_dir = backup_path / dir_name
                    shutil.copytree(source_dir, dest_dir, dirs_exist_ok=True)
            
            # Create backup manifest
            manifest = {
                "backup_type": backup_type,
                "created_at": datetime.now().isoformat(),
                "directories_backed_up": important_dirs,
                "backup_path": str(backup_path)
            }
            
            manifest_file = backup_path / "backup_manifest.json"
            with open(manifest_file, 'w') as f:
                json.dump(manifest, f, indent=2)
            
            logger.info(f"Backup created: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            raise
    
    def restore_backup(self, backup_path: str) -> bool:
        """Restore from backup."""
        backup_dir = Path(backup_path)
        
        if not backup_dir.exists():
            logger.error(f"Backup directory does not exist: {backup_path}")
            return False
        
        try:
            # Read backup manifest
            manifest_file = backup_dir / "backup_manifest.json"
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                directories = manifest.get("directories_backed_up", [])
            else:
                # Fallback to all directories in backup
                directories = [d.name for d in backup_dir.iterdir() if d.is_dir()]
            
            # Restore each directory
            for dir_name in directories:
                source_dir = backup_dir / dir_name
                dest_dir = self.base_path / dir_name
                
                if source_dir.exists():
                    if dest_dir.exists():
                        shutil.rmtree(dest_dir)
                    shutil.copytree(source_dir, dest_dir)
            
            logger.info(f"Backup restored from: {backup_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error restoring backup: {e}")
            return False


# Global file organization manager (initialized on demand)
_file_org_manager = None


def get_file_org_manager() -> FileOrganizationManager:
    """Get the global file organization manager."""
    global _file_org_manager
    if _file_org_manager is None:
        _file_org_manager = FileOrganizationManager()
    return _file_org_manager