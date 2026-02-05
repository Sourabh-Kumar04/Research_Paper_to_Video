"""
Cinematic Preview Generation System
Generates real-time previews of cinematic effects for user interface.
"""

import os
import asyncio
import hashlib
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import base64
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import io

from .models import CinematicSettingsModel

logger = logging.getLogger(__name__)


@dataclass
class PreviewRequest:
    """Preview generation request."""
    scene_id: str
    settings: CinematicSettingsModel
    content: str
    feature_type: str  # 'color_grading', 'camera_movement', 'full_preview'
    target_size: Tuple[int, int] = (320, 180)  # Preview dimensions
    
    def get_cache_key(self) -> str:
        """Generate cache key for this request."""
        content_hash = hashlib.md5(
            f"{self.scene_id}{self.settings.to_dict()}{self.content}{self.feature_type}".encode()
        ).hexdigest()
        return f"preview_{content_hash[:16]}"


@dataclass
class PreviewResult:
    """Preview generation result."""
    scene_id: str
    preview_url: str
    thumbnail_url: str
    estimated_size: str
    estimated_duration: str
    processing_time: str
    effects_applied: List[str]
    generated_at: str
    cache_key: str
    confidence: float = 1.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)


class PreviewCache:
    """Cache for generated previews."""
    
    def __init__(self, cache_dir: str = "temp/preview_cache", max_size: int = 100):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.max_size = max_size
        self.cache_index = {}
        self.access_times = {}
        self._load_cache_index()
    
    def _load_cache_index(self):
        """Load cache index from disk."""
        index_file = self.cache_dir / "cache_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r') as f:
                    data = json.load(f)
                    self.cache_index = data.get('index', {})
                    self.access_times = data.get('access_times', {})
            except Exception as e:
                logger.warning(f"Failed to load cache index: {e}")
                self.cache_index = {}
                self.access_times = {}
    
    def _save_cache_index(self):
        """Save cache index to disk."""
        index_file = self.cache_dir / "cache_index.json"
        try:
            with open(index_file, 'w') as f:
                json.dump({
                    'index': self.cache_index,
                    'access_times': self.access_times
                }, f)
        except Exception as e:
            logger.warning(f"Failed to save cache index: {e}")
    
    def get(self, cache_key: str) -> Optional[PreviewResult]:
        """Get cached preview result."""
        if cache_key not in self.cache_index:
            return None
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        if not cache_file.exists():
            # Remove stale index entry
            del self.cache_index[cache_key]
            return None
        
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                result = PreviewResult(**data)
                
                # Update access time
                self.access_times[cache_key] = time.time()
                return result
        except Exception as e:
            logger.warning(f"Failed to load cached preview {cache_key}: {e}")
            return None
    
    def put(self, cache_key: str, result: PreviewResult):
        """Store preview result in cache."""
        # Clean up old entries if cache is full
        if len(self.cache_index) >= self.max_size:
            self._cleanup_old_entries()
        
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w') as f:
                json.dump(result.to_dict(), f)
            
            self.cache_index[cache_key] = {
                'created_at': time.time(),
                'file_path': str(cache_file)
            }
            self.access_times[cache_key] = time.time()
            self._save_cache_index()
        except Exception as e:
            logger.warning(f"Failed to cache preview {cache_key}: {e}")
    
    def _cleanup_old_entries(self):
        """Remove oldest cache entries."""
        if not self.access_times:
            return
        
        # Sort by access time and remove oldest 20%
        sorted_entries = sorted(self.access_times.items(), key=lambda x: x[1])
        entries_to_remove = sorted_entries[:len(sorted_entries) // 5]
        
        for cache_key, _ in entries_to_remove:
            self.invalidate(cache_key)
    
    def invalidate(self, cache_key: str):
        """Remove entry from cache."""
        if cache_key in self.cache_index:
            cache_file = Path(self.cache_index[cache_key]['file_path'])
            if cache_file.exists():
                cache_file.unlink()
            del self.cache_index[cache_key]
        
        if cache_key in self.access_times:
            del self.access_times[cache_key]
    
    def clear(self):
        """Clear all cache entries."""
        for cache_key in list(self.cache_index.keys()):
            self.invalidate(cache_key)
        self._save_cache_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'cache_size': len(self.cache_index),
            'max_size': self.max_size,
            'cache_dir': str(self.cache_dir),
            'oldest_entry': min(self.access_times.values()) if self.access_times else None,
            'newest_entry': max(self.access_times.values()) if self.access_times else None
        }


class CinematicPreviewGenerator:
    """Generates previews for cinematic effects."""
    
    def __init__(self, cache_dir: str = "temp/preview_cache"):
        self.cache = PreviewCache(cache_dir)
        self.output_dir = Path("temp/previews")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Processing time estimation factors
        self.base_processing_time = 1.0  # seconds
        self.quality_multipliers = {
            "standard_hd": 1.0,
            "cinematic_4k": 2.0,
            "cinematic_8k": 4.0
        }
        
        # File size estimation factors (MB per minute)
        self.size_factors = {
            "standard_hd": 50,
            "cinematic_4k": 200,
            "cinematic_8k": 800
        }
    
    async def generate_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate preview for cinematic settings."""
        # Check cache first
        cached_result = self.cache.get(request.get_cache_key())
        if cached_result:
            logger.debug(f"Cache hit for preview {request.scene_id}")
            return cached_result
        
        logger.info(f"Generating preview for scene {request.scene_id}, feature: {request.feature_type}")
        
        start_time = time.time()
        
        try:
            # Generate preview based on feature type
            if request.feature_type == "color_grading":
                result = await self._generate_color_grading_preview(request)
            elif request.feature_type == "camera_movement":
                result = await self._generate_camera_movement_preview(request)
            elif request.feature_type == "full_preview":
                result = await self._generate_full_preview(request)
            else:
                result = await self._generate_generic_preview(request)
            
            # Cache the result
            self.cache.put(request.get_cache_key(), result)
            
            processing_time = time.time() - start_time
            logger.info(f"Preview generated in {processing_time:.2f}s for {request.scene_id}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to generate preview for {request.scene_id}: {e}")
            return self._generate_fallback_preview(request)
    
    async def _generate_color_grading_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate color grading preview."""
        # Simulate color grading processing
        await asyncio.sleep(0.1)  # Simulate processing time
        
        # Create a sample image with color grading applied
        preview_image = self._create_color_graded_image(request.settings.color_grading)
        preview_url = await self._save_preview_image(request.scene_id, "color_grading", preview_image)
        thumbnail_url = await self._save_thumbnail(request.scene_id, "color_grading", preview_image)
        
        effects = self._get_color_grading_effects(request.settings.color_grading)
        
        return PreviewResult(
            scene_id=request.scene_id,
            preview_url=preview_url,
            thumbnail_url=thumbnail_url,
            estimated_size=self._estimate_file_size(request.settings, request.content),
            estimated_duration=self._estimate_duration(request.content),
            processing_time=self._estimate_processing_time(request.settings),
            effects_applied=effects,
            generated_at=datetime.utcnow().isoformat(),
            cache_key=request.get_cache_key(),
            confidence=0.9
        )
    
    async def _generate_camera_movement_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate camera movement preview."""
        # Simulate camera movement processing
        await asyncio.sleep(0.15)  # Simulate processing time
        
        # Create animated preview frames
        preview_frames = self._create_camera_movement_frames(request.settings.camera_movements)
        preview_url = await self._save_animated_preview(request.scene_id, "camera_movement", preview_frames)
        thumbnail_url = await self._save_thumbnail(request.scene_id, "camera_movement", preview_frames[0])
        
        effects = self._get_camera_movement_effects(request.settings.camera_movements)
        
        return PreviewResult(
            scene_id=request.scene_id,
            preview_url=preview_url,
            thumbnail_url=thumbnail_url,
            estimated_size=self._estimate_file_size(request.settings, request.content),
            estimated_duration=self._estimate_duration(request.content),
            processing_time=self._estimate_processing_time(request.settings),
            effects_applied=effects,
            generated_at=datetime.utcnow().isoformat(),
            cache_key=request.get_cache_key(),
            confidence=0.85
        )
    
    async def _generate_full_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate full cinematic preview."""
        # Simulate full processing
        await asyncio.sleep(0.3)  # Simulate processing time
        
        # Create comprehensive preview
        preview_image = self._create_full_cinematic_preview(request.settings)
        preview_url = await self._save_preview_image(request.scene_id, "full", preview_image)
        thumbnail_url = await self._save_thumbnail(request.scene_id, "full", preview_image)
        
        effects = self._get_all_effects(request.settings)
        
        return PreviewResult(
            scene_id=request.scene_id,
            preview_url=preview_url,
            thumbnail_url=thumbnail_url,
            estimated_size=self._estimate_file_size(request.settings, request.content),
            estimated_duration=self._estimate_duration(request.content),
            processing_time=self._estimate_processing_time(request.settings),
            effects_applied=effects,
            generated_at=datetime.utcnow().isoformat(),
            cache_key=request.get_cache_key(),
            confidence=0.95
        )
    
    async def _generate_generic_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate generic preview for unknown feature types."""
        await asyncio.sleep(0.05)
        
        # Create basic preview
        preview_image = self._create_basic_preview()
        preview_url = await self._save_preview_image(request.scene_id, "generic", preview_image)
        thumbnail_url = await self._save_thumbnail(request.scene_id, "generic", preview_image)
        
        return PreviewResult(
            scene_id=request.scene_id,
            preview_url=preview_url,
            thumbnail_url=thumbnail_url,
            estimated_size=self._estimate_file_size(request.settings, request.content),
            estimated_duration=self._estimate_duration(request.content),
            processing_time=self._estimate_processing_time(request.settings),
            effects_applied=["Basic cinematic enhancement"],
            generated_at=datetime.utcnow().isoformat(),
            cache_key=request.get_cache_key(),
            confidence=0.7
        )
    
    def _generate_fallback_preview(self, request: PreviewRequest) -> PreviewResult:
        """Generate fallback preview when generation fails."""
        return PreviewResult(
            scene_id=request.scene_id,
            preview_url="/static/fallback_preview.jpg",
            thumbnail_url="/static/fallback_thumbnail.jpg",
            estimated_size="Unknown",
            estimated_duration="Unknown",
            processing_time="Unknown",
            effects_applied=["Preview generation failed"],
            generated_at=datetime.utcnow().isoformat(),
            cache_key=request.get_cache_key(),
            confidence=0.0
        )
    
    def _create_color_graded_image(self, color_settings) -> Image.Image:
        """Create sample image with color grading applied."""
        # Create base image
        img = Image.new('RGB', (320, 180), color=(50, 50, 50))
        draw = ImageDraw.Draw(img)
        
        # Add some geometric shapes to show color grading
        draw.rectangle([50, 50, 150, 130], fill=(100, 150, 200))
        draw.ellipse([170, 40, 270, 140], fill=(200, 100, 150))
        
        # Apply color grading effects
        if color_settings.enabled:
            # Temperature adjustment
            if color_settings.temperature != 0:
                enhancer = ImageEnhance.Color(img)
                factor = 1.0 + (color_settings.temperature / 200.0)
                img = enhancer.enhance(max(0.1, min(2.0, factor)))
            
            # Contrast adjustment
            if color_settings.contrast != 0:
                enhancer = ImageEnhance.Contrast(img)
                factor = 1.0 + (color_settings.contrast / 100.0)
                img = enhancer.enhance(max(0.1, min(2.0, factor)))
            
            # Saturation adjustment
            if color_settings.saturation != 0:
                enhancer = ImageEnhance.Color(img)
                factor = 1.0 + (color_settings.saturation / 100.0)
                img = enhancer.enhance(max(0.1, min(2.0, factor)))
        
        return img
    
    def _create_camera_movement_frames(self, camera_settings) -> List[Image.Image]:
        """Create frames showing camera movement."""
        frames = []
        base_img = Image.new('RGB', (320, 180), color=(30, 30, 30))
        draw = ImageDraw.Draw(base_img)
        
        # Add content to show movement
        draw.rectangle([100, 60, 220, 120], fill=(150, 100, 200))
        draw.text((130, 85), "Content", fill=(255, 255, 255))
        
        if camera_settings.enabled:
            # Create movement frames based on intensity
            num_frames = max(3, camera_settings.intensity // 20)
            
            for i in range(num_frames):
                frame = base_img.copy()
                
                # Simulate camera movement by shifting content
                offset = int((i / num_frames) * camera_settings.intensity * 0.5)
                
                # Create new frame with offset
                shifted_frame = Image.new('RGB', (320, 180), color=(30, 30, 30))
                shifted_frame.paste(frame, (offset, 0))
                frames.append(shifted_frame)
        else:
            frames.append(base_img)
        
        return frames
    
    def _create_full_cinematic_preview(self, settings: CinematicSettingsModel) -> Image.Image:
        """Create comprehensive cinematic preview."""
        img = Image.new('RGB', (320, 180), color=(20, 20, 25))
        draw = ImageDraw.Draw(img)
        
        # Add cinematic elements
        draw.rectangle([0, 0, 320, 20], fill=(0, 0, 0))  # Top letterbox
        draw.rectangle([0, 160, 320, 180], fill=(0, 0, 0))  # Bottom letterbox
        
        # Main content area
        draw.rectangle([60, 40, 260, 140], fill=(80, 120, 160))
        draw.text((120, 85), "Cinematic", fill=(255, 255, 255))
        draw.text((130, 100), "Preview", fill=(255, 255, 255))
        
        # Apply effects based on settings
        if settings.color_grading.enabled:
            enhancer = ImageEnhance.Color(img)
            img = enhancer.enhance(1.2)
        
        if settings.advanced_compositing.enabled and settings.advanced_compositing.film_grain:
            # Add subtle noise for film grain effect
            img = img.filter(ImageFilter.GaussianBlur(0.5))
        
        return img
    
    def _create_basic_preview(self) -> Image.Image:
        """Create basic preview image."""
        img = Image.new('RGB', (320, 180), color=(60, 60, 60))
        draw = ImageDraw.Draw(img)
        draw.text((120, 85), "Preview", fill=(255, 255, 255))
        return img
    
    async def _save_preview_image(self, scene_id: str, feature_type: str, image: Image.Image) -> str:
        """Save preview image and return URL."""
        filename = f"{scene_id}_{feature_type}_preview.jpg"
        filepath = self.output_dir / filename
        
        try:
            image.save(filepath, "JPEG", quality=85)
            return f"/api/v1/cinematic/preview/{filename}"
        except Exception as e:
            logger.error(f"Failed to save preview image: {e}")
            return "/static/fallback_preview.jpg"
    
    async def _save_thumbnail(self, scene_id: str, feature_type: str, image: Image.Image) -> str:
        """Save thumbnail and return URL."""
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((160, 90), Image.Resampling.LANCZOS)
        
        filename = f"{scene_id}_{feature_type}_thumb.jpg"
        filepath = self.output_dir / filename
        
        try:
            thumbnail.save(filepath, "JPEG", quality=75)
            return f"/api/v1/cinematic/preview/{filename}"
        except Exception as e:
            logger.error(f"Failed to save thumbnail: {e}")
            return "/static/fallback_thumbnail.jpg"
    
    async def _save_animated_preview(self, scene_id: str, feature_type: str, frames: List[Image.Image]) -> str:
        """Save animated preview (GIF) and return URL."""
        filename = f"{scene_id}_{feature_type}_preview.gif"
        filepath = self.output_dir / filename
        
        try:
            frames[0].save(
                filepath,
                "GIF",
                save_all=True,
                append_images=frames[1:],
                duration=200,  # 200ms per frame
                loop=0
            )
            return f"/api/v1/cinematic/preview/{filename}"
        except Exception as e:
            logger.error(f"Failed to save animated preview: {e}")
            return "/static/fallback_preview.gif"
    
    def _estimate_file_size(self, settings: CinematicSettingsModel, content: str) -> str:
        """Estimate output file size."""
        # Base size calculation
        content_minutes = max(1, len(content) / 1000)  # Rough estimate
        base_size = self.size_factors.get(settings.quality_preset, 200) * content_minutes
        
        # Adjust for enabled features
        multiplier = 1.0
        
        if settings.camera_movements.enabled:
            multiplier += 0.1
        
        if settings.color_grading.enabled:
            multiplier += 0.05
        
        if settings.advanced_compositing.enabled:
            if settings.advanced_compositing.film_grain:
                multiplier += 0.1
            if settings.advanced_compositing.dynamic_lighting:
                multiplier += 0.15
            if settings.advanced_compositing.depth_of_field:
                multiplier += 0.1
            if settings.advanced_compositing.motion_blur:
                multiplier += 0.1
        
        estimated_size = base_size * multiplier
        
        if estimated_size < 1:
            return f"{estimated_size * 1000:.0f} KB"
        else:
            return f"{estimated_size:.1f} MB"
    
    def _estimate_duration(self, content: str) -> str:
        """Estimate video duration based on content."""
        # Rough estimation: 150 words per minute speaking rate
        word_count = len(content.split())
        minutes = max(1, word_count / 150)
        
        if minutes < 1:
            return f"{minutes * 60:.0f} seconds"
        else:
            return f"{minutes:.1f} minutes"
    
    def _estimate_processing_time(self, settings: CinematicSettingsModel) -> str:
        """Estimate processing time based on settings complexity."""
        base_time = self.base_processing_time
        
        # Quality preset multiplier
        base_time *= self.quality_multipliers.get(settings.quality_preset, 2.0)
        
        # Feature complexity
        if settings.camera_movements.enabled:
            base_time += settings.camera_movements.intensity * 0.01
        
        if settings.color_grading.enabled:
            base_time += 0.5
        
        if settings.advanced_compositing.enabled:
            compositing_features = [
                settings.advanced_compositing.film_grain,
                settings.advanced_compositing.dynamic_lighting,
                settings.advanced_compositing.depth_of_field,
                settings.advanced_compositing.motion_blur
            ]
            enabled_count = sum(1 for feature in compositing_features if feature)
            base_time += enabled_count * 0.3
        
        if base_time < 60:
            return f"{base_time:.0f} seconds"
        else:
            return f"{base_time / 60:.1f} minutes"
    
    def _get_color_grading_effects(self, color_settings) -> List[str]:
        """Get list of color grading effects."""
        effects = []
        
        if not color_settings.enabled:
            return ["Color grading disabled"]
        
        if color_settings.film_emulation.value != "none":
            effects.append(f"Film emulation ({color_settings.film_emulation.value})")
        
        if color_settings.temperature != 0:
            direction = "warmer" if color_settings.temperature > 0 else "cooler"
            effects.append(f"Temperature adjustment ({direction})")
        
        if color_settings.contrast != 0:
            direction = "increased" if color_settings.contrast > 0 else "decreased"
            effects.append(f"Contrast {direction}")
        
        if color_settings.saturation != 0:
            direction = "enhanced" if color_settings.saturation > 0 else "reduced"
            effects.append(f"Saturation {direction}")
        
        if not effects:
            effects.append("Basic color grading")
        
        return effects
    
    def _get_camera_movement_effects(self, camera_settings) -> List[str]:
        """Get list of camera movement effects."""
        effects = []
        
        if not camera_settings.enabled:
            return ["Camera movement disabled"]
        
        intensity_desc = "subtle" if camera_settings.intensity < 30 else "moderate" if camera_settings.intensity < 70 else "dramatic"
        effects.append(f"Camera movement ({intensity_desc} intensity)")
        
        if camera_settings.allowed_types:
            movement_types = [t.value for t in camera_settings.allowed_types[:3]]  # Show first 3
            effects.append(f"Movement types: {', '.join(movement_types)}")
        
        return effects
    
    def _get_all_effects(self, settings: CinematicSettingsModel) -> List[str]:
        """Get comprehensive list of all effects."""
        effects = []
        
        # Camera movements
        if settings.camera_movements.enabled:
            effects.extend(self._get_camera_movement_effects(settings.camera_movements))
        
        # Color grading
        if settings.color_grading.enabled:
            effects.extend(self._get_color_grading_effects(settings.color_grading))
        
        # Sound design
        if settings.sound_design.enabled:
            sound_effects = []
            if settings.sound_design.ambient_audio:
                sound_effects.append("ambient audio")
            if settings.sound_design.music_scoring:
                sound_effects.append("music scoring")
            if settings.sound_design.spatial_audio:
                sound_effects.append("spatial audio")
            
            if sound_effects:
                effects.append(f"Sound design ({', '.join(sound_effects)})")
        
        # Advanced compositing
        if settings.advanced_compositing.enabled:
            compositing_effects = []
            if settings.advanced_compositing.film_grain:
                compositing_effects.append("film grain")
            if settings.advanced_compositing.dynamic_lighting:
                compositing_effects.append("dynamic lighting")
            if settings.advanced_compositing.depth_of_field:
                compositing_effects.append("depth of field")
            if settings.advanced_compositing.motion_blur:
                compositing_effects.append("motion blur")
            
            if compositing_effects:
                effects.append(f"Advanced compositing ({', '.join(compositing_effects)})")
        
        # Quality preset
        effects.append(f"Quality: {settings.quality_preset}")
        
        return effects if effects else ["Basic cinematic enhancement"]
    
    async def batch_generate_previews(self, requests: List[PreviewRequest]) -> List[PreviewResult]:
        """Generate multiple previews concurrently."""
        tasks = [self.generate_preview(request) for request in requests]
        return await asyncio.gather(*tasks, return_exceptions=True)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()
    
    def clear_cache(self):
        """Clear preview cache."""
        self.cache.clear()
    
    def cleanup_old_previews(self, max_age_hours: int = 24):
        """Clean up old preview files."""
        cutoff_time = time.time() - (max_age_hours * 3600)
        
        for file_path in self.output_dir.glob("*"):
            if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                try:
                    file_path.unlink()
                    logger.debug(f"Cleaned up old preview file: {file_path}")
                except Exception as e:
                    logger.warning(f"Failed to clean up preview file {file_path}: {e}")