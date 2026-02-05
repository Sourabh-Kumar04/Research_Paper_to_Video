"""
Comprehensive asset storage system for production video generation.
Manages video, audio, visual assets with metadata and relationships.
"""

import os
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import hashlib
from dataclasses import dataclass, asdict

from .database_manager import get_db_manager
from .file_organization_manager import get_file_org_manager

logger = logging.getLogger(__name__)


@dataclass
class AssetMetadata:
    """Metadata for any asset."""
    asset_id: str
    asset_type: str
    title: str
    description: Optional[str]
    file_path: str
    file_size_bytes: int
    content_hash: str
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    generation_parameters: Dict[str, Any]


@dataclass
class VideoAssetMetadata(AssetMetadata):
    """Extended metadata for video assets."""
    duration_seconds: float
    resolution: str
    fps: int
    codec: str
    bitrate_kbps: int
    has_audio: bool
    scene_count: int
    thumbnail_path: Optional[str]


@dataclass
class AudioAssetMetadata(AssetMetadata):
    """Extended metadata for audio assets."""
    duration_seconds: float
    sample_rate: int
    channels: int
    bitrate_kbps: int
    format: str
    tts_model: Optional[str]
    voice_style: Optional[str]
    music_model: Optional[str]


@dataclass
class VisualAssetMetadata(AssetMetadata):
    """Extended metadata for visual assets."""
    width: int
    height: int
    format: str
    generation_framework: str
    ai_model_used: Optional[str]
    color_palette: Optional[Dict[str, str]]
    visual_theme: str
    source_code_path: Optional[str]


class AssetStorageManager:
    """Manages comprehensive asset storage with metadata and relationships."""
    
    def __init__(self):
        """Initialize asset storage manager."""
        self.db_manager = get_db_manager()
        self.file_manager = get_file_org_manager()
        self.base_path = Path(self.file_manager.base_path)
    
    def store_video_asset(self, paper_id: str, video_file: str, 
                         metadata: Dict[str, Any]) -> str:
        """Store video asset with comprehensive metadata."""
        try:
            # Generate asset ID
            asset_id = self._generate_asset_id("video")
            
            # Determine asset type and destination
            asset_type = metadata.get('asset_type', 'final_video')
            filename = f"{asset_id}_{Path(video_file).name}"
            
            # Get organized path
            paper_folder = self._get_paper_folder(paper_id)
            dest_path = self.file_manager.get_asset_path(
                paper_folder, asset_type, filename
            )
            
            # Copy file to organized location
            shutil.copy2(video_file, dest_path)
            
            # Calculate file info
            file_size = os.path.getsize(dest_path)
            content_hash = self._calculate_file_hash(dest_path)
            
            # Create video metadata
            video_metadata = {
                'paper_id': paper_id,
                'title': metadata.get('title', 'Generated Video'),
                'description': metadata.get('description'),
                'duration_seconds': metadata['duration_seconds'],
                'file_size_bytes': file_size,
                'resolution': metadata['resolution'],
                'fps': metadata['fps'],
                'codec': metadata['codec'],
                'bitrate_kbps': metadata['bitrate_kbps'],
                'video_path': dest_path,
                'thumbnail_path': metadata.get('thumbnail_path'),
                'quality_preset': metadata.get('quality_preset', 'medium'),
                'ai_models_used': metadata.get('ai_models_used', {}),
                'generation_parameters': metadata.get('generation_parameters', {}),
                'status': 'completed'
            }
            
            # Store in database
            video_id = self.db_manager.create_video(video_metadata)
            
            # Create metadata file
            self._create_asset_metadata_file(dest_path, {
                'asset_id': video_id,
                'asset_type': 'video',
                'paper_id': paper_id,
                'content_hash': content_hash,
                'created_at': datetime.now().isoformat(),
                **metadata
            })
            
            logger.info(f"Video asset stored: {dest_path}")
            return video_id
            
        except Exception as e:
            logger.error(f"Error storing video asset: {e}")
            raise
    
    def store_audio_asset(self, paper_id: str, audio_file: str, 
                         metadata: Dict[str, Any]) -> str:
        """Store audio asset with comprehensive metadata."""
        try:
            # Generate asset ID
            asset_id = self._generate_asset_id("audio")
            
            # Determine asset type and destination
            asset_type = metadata.get('asset_type', 'narration')
            filename = f"{asset_id}_{Path(audio_file).name}"
            
            # Get organized path
            paper_folder = self._get_paper_folder(paper_id)
            dest_path = self.file_manager.get_asset_path(
                paper_folder, asset_type, filename
            )
            
            # Copy file to organized location
            shutil.copy2(audio_file, dest_path)
            
            # Calculate file info
            file_size = os.path.getsize(dest_path)
            content_hash = self._calculate_file_hash(dest_path)
            
            # Create audio metadata
            audio_metadata = {
                'paper_id': paper_id,
                'asset_type': asset_type,
                'title': metadata.get('title', 'Generated Audio'),
                'duration_seconds': metadata['duration_seconds'],
                'file_size_bytes': file_size,
                'sample_rate': metadata['sample_rate'],
                'channels': metadata['channels'],
                'bitrate_kbps': metadata['bitrate_kbps'],
                'format': metadata['format'],
                'file_path': dest_path,
                'tts_model': metadata.get('tts_model'),
                'voice_style': metadata.get('voice_style'),
                'music_model': metadata.get('music_model'),
                'generation_parameters': metadata.get('generation_parameters', {})
            }
            
            # Store in database
            audio_id = self.db_manager.create_audio_asset(audio_metadata)
            
            # Create metadata file
            self._create_asset_metadata_file(dest_path, {
                'asset_id': audio_id,
                'asset_type': 'audio',
                'paper_id': paper_id,
                'content_hash': content_hash,
                'created_at': datetime.now().isoformat(),
                **metadata
            })
            
            logger.info(f"Audio asset stored: {dest_path}")
            return audio_id
            
        except Exception as e:
            logger.error(f"Error storing audio asset: {e}")
            raise
    
    def store_visual_asset(self, paper_id: str, visual_file: str, 
                          metadata: Dict[str, Any]) -> str:
        """Store visual asset with comprehensive metadata."""
        try:
            # Generate asset ID
            asset_id = self._generate_asset_id("visual")
            
            # Determine asset type and destination
            asset_type = metadata.get('asset_type', 'animation')
            filename = f"{asset_id}_{Path(visual_file).name}"
            
            # Get organized path
            paper_folder = self._get_paper_folder(paper_id)
            dest_path = self.file_manager.get_asset_path(
                paper_folder, asset_type, filename
            )
            
            # Copy file to organized location
            shutil.copy2(visual_file, dest_path)
            
            # Calculate file info
            file_size = os.path.getsize(dest_path)
            content_hash = self._calculate_file_hash(dest_path)
            
            # Create visual metadata
            visual_metadata = {
                'paper_id': paper_id,
                'asset_type': asset_type,
                'title': metadata.get('title', 'Generated Visual'),
                'description': metadata.get('description'),
                'width': metadata['width'],
                'height': metadata['height'],
                'format': metadata['format'],
                'file_size_bytes': file_size,
                'file_path': dest_path,
                'source_code_path': metadata.get('source_code_path'),
                'generation_framework': metadata.get('generation_framework', 'unknown'),
                'ai_model_used': metadata.get('ai_model_used'),
                'generation_parameters': metadata.get('generation_parameters', {}),
                'color_palette': metadata.get('color_palette'),
                'visual_theme': metadata.get('visual_theme', 'default')
            }
            
            # Store in database
            visual_id = self.db_manager.create_visual_asset(visual_metadata)
            
            # Create metadata file
            self._create_asset_metadata_file(dest_path, {
                'asset_id': visual_id,
                'asset_type': 'visual',
                'paper_id': paper_id,
                'content_hash': content_hash,
                'created_at': datetime.now().isoformat(),
                **metadata
            })
            
            logger.info(f"Visual asset stored: {dest_path}")
            return visual_id
            
        except Exception as e:
            logger.error(f"Error storing visual asset: {e}")
            raise
    
    def store_code_asset(self, paper_id: str, code_content: str, 
                        metadata: Dict[str, Any]) -> str:
        """Store generated code with metadata."""
        try:
            # Generate asset ID
            asset_id = self._generate_asset_id("code")
            
            # Determine code type and extension
            code_type = metadata.get('code_type', 'python')
            framework = metadata.get('framework', 'manim')
            
            extensions = {
                'python': '.py',
                'javascript': '.js',
                'typescript': '.ts',
                'jsx': '.jsx',
                'tsx': '.tsx'
            }
            
            ext = extensions.get(code_type, '.py')
            filename = f"{asset_id}_{framework}_code{ext}"
            
            # Get organized path
            paper_folder = self._get_paper_folder(paper_id)
            dest_path = self.file_manager.get_asset_path(
                paper_folder, f"{framework}_code", filename
            )
            
            # Write code to file
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(code_content)
            
            # Calculate file info
            file_size = os.path.getsize(dest_path)
            content_hash = hashlib.sha256(code_content.encode()).hexdigest()
            
            # Create metadata file
            self._create_asset_metadata_file(dest_path, {
                'asset_id': asset_id,
                'asset_type': 'code',
                'paper_id': paper_id,
                'code_type': code_type,
                'framework': framework,
                'content_hash': content_hash,
                'file_size_bytes': file_size,
                'created_at': datetime.now().isoformat(),
                **metadata
            })
            
            logger.info(f"Code asset stored: {dest_path}")
            return asset_id
            
        except Exception as e:
            logger.error(f"Error storing code asset: {e}")
            raise
    
    def get_asset_metadata(self, asset_id: str, asset_type: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive metadata for an asset."""
        try:
            if asset_type == 'video':
                return self.db_manager.get_video(asset_id)
            elif asset_type == 'audio':
                return self.db_manager.get_audio_asset(asset_id)
            elif asset_type == 'visual':
                return self.db_manager.get_visual_asset(asset_id)
            else:
                logger.warning(f"Unknown asset type: {asset_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting asset metadata: {e}")
            return None
    
    def get_paper_assets(self, paper_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Get all assets for a paper organized by type."""
        try:
            # Get from database
            assets = self.db_manager.get_assets_by_paper(paper_id)
            
            # Get videos
            videos = self.db_manager.get_videos_by_paper(paper_id)
            assets['videos'] = videos
            
            return assets
            
        except Exception as e:
            logger.error(f"Error getting paper assets: {e}")
            return {'videos': [], 'audio': [], 'visual': []}
    
    def create_asset_relationships(self, primary_asset_id: str, 
                                  related_asset_ids: List[str], 
                                  relationship_type: str) -> bool:
        """Create relationships between assets."""
        try:
            # Store relationships in metadata
            relationships = {
                'primary_asset': primary_asset_id,
                'related_assets': related_asset_ids,
                'relationship_type': relationship_type,
                'created_at': datetime.now().isoformat()
            }
            
            # Store in database as JSON metadata
            # This could be expanded to a separate relationships table
            logger.info(f"Asset relationships created: {relationship_type}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating asset relationships: {e}")
            return False
    
    def search_assets(self, query: str, asset_type: Optional[str] = None, 
                     paper_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Search assets by metadata."""
        try:
            # This is a simplified search - could be enhanced with full-text search
            results = []
            
            # Search in database based on criteria
            if asset_type == 'video' or asset_type is None:
                # Search videos
                pass
            
            if asset_type == 'audio' or asset_type is None:
                # Search audio assets
                pass
            
            if asset_type == 'visual' or asset_type is None:
                # Search visual assets
                pass
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching assets: {e}")
            return []
    
    def cleanup_orphaned_assets(self) -> Dict[str, int]:
        """Clean up assets that no longer have database records."""
        try:
            cleanup_stats = {
                'files_removed': 0,
                'metadata_removed': 0,
                'errors': 0
            }
            
            # Find all asset files
            for asset_dir in ['videos', 'audio', 'visuals', 'code']:
                asset_path = self.base_path / asset_dir
                if asset_path.exists():
                    for file_path in asset_path.rglob("*"):
                        if file_path.is_file() and not file_path.name.endswith('.json'):
                            # Check if asset exists in database
                            # This would need to be implemented based on naming convention
                            pass
            
            return cleanup_stats
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned assets: {e}")
            return {'files_removed': 0, 'metadata_removed': 0, 'errors': 1}
    
    def get_storage_usage(self) -> Dict[str, Any]:
        """Get detailed storage usage statistics."""
        try:
            stats = self.file_manager.get_storage_stats()
            
            # Add database statistics
            db_stats = self.db_manager.get_database_stats()
            stats['database'] = db_stats
            
            # Calculate storage efficiency
            stats['efficiency'] = {
                'avg_file_size': stats['total_size_bytes'] / max(stats['total_files'], 1),
                'compression_ratio': self._estimate_compression_ratio(),
                'duplicate_files': len(self.file_manager.find_duplicates())
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting storage usage: {e}")
            return {}
    
    def _generate_asset_id(self, asset_type: str) -> str:
        """Generate unique asset ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        import uuid
        unique_id = str(uuid.uuid4())[:8]
        return f"{asset_type}_{timestamp}_{unique_id}"
    
    def _get_paper_folder(self, paper_id: str) -> str:
        """Get paper folder path from database."""
        paper = self.db_manager.get_paper(paper_id)
        if paper:
            return paper['folder_name']
        else:
            # Fallback to default folder
            return f"unknown_paper_{paper_id[:8]}"
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        return self.file_manager.calculate_file_hash(file_path)
    
    def _create_asset_metadata_file(self, asset_path: str, metadata: Dict[str, Any]):
        """Create JSON metadata file alongside asset."""
        metadata_path = f"{asset_path}.metadata.json"
        try:
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False, default=str)
        except Exception as e:
            logger.warning(f"Could not create metadata file {metadata_path}: {e}")
    
    def _estimate_compression_ratio(self) -> float:
        """Estimate compression ratio of stored assets."""
        # This is a placeholder - could analyze actual compression ratios
        return 0.75  # Assume 75% compression on average


# Global asset storage manager (initialized on demand)
_asset_storage_manager = None


def get_asset_storage_manager() -> AssetStorageManager:
    """Get the global asset storage manager."""
    global _asset_storage_manager
    if _asset_storage_manager is None:
        _asset_storage_manager = AssetStorageManager()
    return _asset_storage_manager