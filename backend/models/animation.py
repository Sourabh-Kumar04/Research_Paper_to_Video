"""
Animation models for the RASO platform.

Models for animation assets, rendering metadata, and video resolution
specifications for the animation generation pipeline.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field, validator


class VideoResolution(BaseModel):
    """Video resolution specification."""
    
    width: int = Field(..., gt=0, description="Video width in pixels")
    height: int = Field(..., gt=0, description="Video height in pixels")
    
    @validator("width", "height")
    def validate_dimensions(cls, v):
        """Validate video dimensions."""
        if v % 2 != 0:
            raise ValueError("Video dimensions must be even numbers")
        if v < 480:
            raise ValueError("Minimum dimension is 480 pixels")
        if v > 7680:  # 8K max
            raise ValueError("Maximum dimension is 7680 pixels")
        return v
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio."""
        return self.width / self.height
    
    @property
    def is_standard_ratio(self) -> bool:
        """Check if resolution uses standard aspect ratio."""
        ratio = self.aspect_ratio
        standard_ratios = [16/9, 4/3, 21/9, 1/1]  # Common video ratios
        return any(abs(ratio - std) < 0.01 for std in standard_ratios)
    
    def __str__(self) -> str:
        """String representation of resolution."""
        return f"{self.width}x{self.height}"
    
    @classmethod
    def from_string(cls, resolution_str: str) -> "VideoResolution":
        """Create resolution from string format."""
        if "x" not in resolution_str:
            raise ValueError("Resolution string must be in format 'WIDTHxHEIGHT'")
        
        width_str, height_str = resolution_str.split("x")
        return cls(width=int(width_str), height=int(height_str))
    
    class Config:
        schema_extra = {
            "examples": [
                {"width": 1920, "height": 1080},  # 1080p
                {"width": 3840, "height": 2160},  # 4K
                {"width": 1280, "height": 720},   # 720p
            ]
        }


class RenderStatus(str, Enum):
    """Status of animation rendering."""
    PENDING = "pending"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class SceneMetadata(BaseModel):
    """Metadata for a rendered scene."""
    
    # Rendering information
    render_start_time: Optional[datetime] = Field(default=None, description="Render start timestamp")
    render_end_time: Optional[datetime] = Field(default=None, description="Render completion timestamp")
    render_duration: Optional[float] = Field(default=None, description="Render time in seconds")
    
    # Technical details
    framework_version: Optional[str] = Field(default=None, description="Animation framework version")
    template_id: Optional[str] = Field(default=None, description="Template used for rendering")
    parameters_used: Dict[str, Any] = Field(default_factory=dict, description="Parameters used for rendering")
    
    # Quality metrics
    file_size_bytes: Optional[int] = Field(default=None, description="Output file size in bytes")
    actual_duration: Optional[float] = Field(default=None, description="Actual video duration")
    frame_count: Optional[int] = Field(default=None, description="Total number of frames")
    
    # Error information
    error_message: Optional[str] = Field(default=None, description="Error message if rendering failed")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    @property
    def render_time_minutes(self) -> Optional[float]:
        """Get render time in minutes."""
        if self.render_duration:
            return self.render_duration / 60
        return None
    
    @property
    def file_size_mb(self) -> Optional[float]:
        """Get file size in megabytes."""
        if self.file_size_bytes:
            return self.file_size_bytes / (1024 * 1024)
        return None


class RenderedScene(BaseModel):
    """A rendered animation scene."""
    
    scene_id: str = Field(..., description="Reference to scene ID")
    file_path: str = Field(..., description="Path to rendered video file")
    duration: float = Field(..., gt=0.0, description="Scene duration in seconds")
    framework: str = Field(..., description="Animation framework used")
    
    # Technical specifications
    resolution: VideoResolution = Field(..., description="Video resolution")
    frame_rate: int = Field(..., gt=0, description="Frame rate")
    codec: str = Field(default="libx264", description="Video codec used")
    
    # Status and metadata
    status: RenderStatus = Field(default=RenderStatus.PENDING, description="Render status")
    metadata: SceneMetadata = Field(default_factory=SceneMetadata, description="Rendering metadata")
    
    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate file path."""
        if not v:
            raise ValueError("File path cannot be empty")
        
        # Check for valid video extensions
        valid_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
        path = Path(v)
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f"File must have a valid video extension: {valid_extensions}")
        
        return v
    
    @validator("framework")
    def validate_framework(cls, v):
        """Validate animation framework."""
        valid_frameworks = ["manim", "motion-canvas", "remotion"]
        if v.lower() not in valid_frameworks:
            raise ValueError(f"Framework must be one of {valid_frameworks}")
        return v.lower()
    
    @property
    def file_exists(self) -> bool:
        """Check if the rendered file exists."""
        return Path(self.file_path).exists()
    
    @property
    def is_completed(self) -> bool:
        """Check if rendering is completed successfully."""
        return self.status == RenderStatus.COMPLETED and self.file_exists
    
    def get_file_size(self) -> Optional[int]:
        """Get file size in bytes."""
        if self.file_exists:
            return Path(self.file_path).stat().st_size
        return None
    
    def update_metadata_from_file(self) -> None:
        """Update metadata from the actual file."""
        if self.file_exists:
            file_size = self.get_file_size()
            if file_size:
                self.metadata.file_size_bytes = file_size


class AnimationAssets(BaseModel):
    """Collection of rendered animation assets."""
    
    scenes: List[RenderedScene] = Field(..., description="List of rendered scenes")
    total_duration: float = Field(..., gt=0.0, description="Total duration of all scenes")
    resolution: VideoResolution = Field(..., description="Common resolution for all scenes")
    
    # Asset metadata
    creation_time: datetime = Field(default_factory=datetime.now, description="Asset creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last update timestamp")
    
    @validator("scenes")
    def validate_scenes(cls, v):
        """Validate scenes list."""
        if not v:
            raise ValueError("At least one scene is required")
        
        # Check for duplicate scene IDs
        scene_ids = [scene.scene_id for scene in v]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique")
        
        return v
    
    @validator("total_duration")
    def validate_total_duration(cls, v, values):
        """Validate total duration matches scene durations."""
        scenes = values.get("scenes", [])
        if scenes:
            calculated_duration = sum(scene.duration for scene in scenes)
            if abs(v - calculated_duration) > 1.0:  # Allow 1 second tolerance
                raise ValueError("Total duration must match sum of scene durations")
        return v
    
    def get_scene_by_id(self, scene_id: str) -> Optional[RenderedScene]:
        """Get a scene by its ID."""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None
    
    def get_scenes_by_framework(self, framework: str) -> List[RenderedScene]:
        """Get all scenes rendered with a specific framework."""
        return [scene for scene in self.scenes if scene.framework.lower() == framework.lower()]
    
    def get_scenes_by_status(self, status: RenderStatus) -> List[RenderedScene]:
        """Get all scenes with a specific render status."""
        return [scene for scene in self.scenes if scene.status == status]
    
    def get_completed_scenes(self) -> List[RenderedScene]:
        """Get all successfully completed scenes."""
        return [scene for scene in self.scenes if scene.is_completed]
    
    def get_failed_scenes(self) -> List[RenderedScene]:
        """Get all failed scenes."""
        return self.get_scenes_by_status(RenderStatus.FAILED)
    
    def get_total_file_size(self) -> int:
        """Get total file size of all scenes in bytes."""
        total_size = 0
        for scene in self.scenes:
            size = scene.get_file_size()
            if size:
                total_size += size
        return total_size
    
    def get_framework_distribution(self) -> Dict[str, int]:
        """Get distribution of animation frameworks used."""
        distribution = {}
        for scene in self.scenes:
            framework = scene.framework
            distribution[framework] = distribution.get(framework, 0) + 1
        return distribution
    
    def get_average_render_time(self) -> Optional[float]:
        """Get average render time across all scenes."""
        render_times = []
        for scene in self.scenes:
            if scene.metadata.render_duration:
                render_times.append(scene.metadata.render_duration)
        
        if render_times:
            return sum(render_times) / len(render_times)
        return None
    
    def is_all_completed(self) -> bool:
        """Check if all scenes are completed successfully."""
        return all(scene.is_completed for scene in self.scenes)
    
    def get_completion_percentage(self) -> float:
        """Get percentage of completed scenes."""
        if not self.scenes:
            return 0.0
        
        completed_count = len(self.get_completed_scenes())
        return (completed_count / len(self.scenes)) * 100
    
    class Config:
        schema_extra = {
            "example": {
                "scenes": [
                    {
                        "scene_id": "scene1",
                        "file_path": "/data/renders/scene1.mp4",
                        "duration": 30.0,
                        "framework": "motion-canvas",
                        "resolution": {"width": 1920, "height": 1080},
                        "frame_rate": 30,
                        "status": "completed"
                    }
                ],
                "total_duration": 75.0,
                "resolution": {"width": 1920, "height": 1080}
            }
        }