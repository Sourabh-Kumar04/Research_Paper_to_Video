"""
Video models for the RASO platform.

Models for final video assets, metadata generation, and YouTube integration
for the complete video production pipeline.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime, timedelta

from pydantic import BaseModel, Field, validator, HttpUrl


class VideoQuality(str, Enum):
    """Video quality presets."""
    DRAFT = "draft"
    STANDARD = "standard"
    HIGH = "high"
    ULTRA = "ultra"


class PrivacyStatus(str, Enum):
    """YouTube privacy status options."""
    PUBLIC = "public"
    UNLISTED = "unlisted"
    PRIVATE = "private"


class Chapter(BaseModel):
    """Video chapter marker."""
    
    title: str = Field(..., description="Chapter title")
    start_time: float = Field(..., ge=0.0, description="Chapter start time in seconds")
    end_time: Optional[float] = Field(default=None, description="Chapter end time in seconds")
    
    # Optional metadata
    description: Optional[str] = Field(default=None, description="Chapter description")
    thumbnail_path: Optional[str] = Field(default=None, description="Path to chapter thumbnail")
    
    @validator("title")
    def validate_title(cls, v):
        """Validate chapter title."""
        if len(v.strip()) < 3:
            raise ValueError("Chapter title must be at least 3 characters")
        return v.strip()
    
    @validator("end_time")
    def validate_end_time(cls, v, values):
        """Validate end time is after start time."""
        start_time = values.get("start_time")
        if v is not None and start_time is not None and v <= start_time:
            raise ValueError("End time must be after start time")
        return v
    
    @property
    def duration(self) -> Optional[float]:
        """Get chapter duration."""
        if self.end_time is not None:
            return self.end_time - self.start_time
        return None
    
    def format_timestamp(self, time_value: float) -> str:
        """Format time as MM:SS or HH:MM:SS."""
        td = timedelta(seconds=time_value)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def start_timestamp(self) -> str:
        """Get formatted start timestamp."""
        return self.format_timestamp(self.start_time)
    
    @property
    def end_timestamp(self) -> Optional[str]:
        """Get formatted end timestamp."""
        if self.end_time is not None:
            return self.format_timestamp(self.end_time)
        return None


class VideoMetadata(BaseModel):
    """Metadata for YouTube video optimization."""
    
    # Basic metadata
    title: str = Field(..., description="Video title")
    description: str = Field(..., description="Video description")
    tags: List[str] = Field(..., description="Video tags for SEO")
    
    # YouTube-specific
    category: str = Field(default="Education", description="YouTube category")
    privacy_status: PrivacyStatus = Field(default=PrivacyStatus.UNLISTED, description="Privacy setting")
    
    # Content organization
    chapters: List[Chapter] = Field(default_factory=list, description="Video chapters")
    thumbnail_path: Optional[str] = Field(default=None, description="Custom thumbnail path")
    
    # SEO and discovery
    keywords: List[str] = Field(default_factory=list, description="Additional keywords")
    language: str = Field(default="en", description="Video language")
    
    @validator("title")
    def validate_title(cls, v):
        """Validate video title."""
        if len(v.strip()) < 10:
            raise ValueError("Video title must be at least 10 characters")
        if len(v) > 100:
            raise ValueError("Video title cannot exceed 100 characters")
        return v.strip()
    
    @validator("description")
    def validate_description(cls, v):
        """Validate video description."""
        if len(v.strip()) < 50:
            raise ValueError("Video description must be at least 50 characters")
        if len(v) > 5000:
            raise ValueError("Video description cannot exceed 5000 characters")
        return v.strip()
    
    @validator("tags")
    def validate_tags(cls, v):
        """Validate video tags."""
        if len(v) > 500:  # YouTube limit
            raise ValueError("Cannot have more than 500 tags")
        
        # Clean and validate individual tags
        cleaned_tags = []
        for tag in v:
            cleaned_tag = tag.strip()
            if cleaned_tag and len(cleaned_tag) <= 30:  # YouTube tag length limit
                cleaned_tags.append(cleaned_tag)
        
        return cleaned_tags
    
    @validator("chapters")
    def validate_chapters(cls, v):
        """Validate chapter list."""
        if not v:
            return v
        
        # Sort chapters by start time
        v.sort(key=lambda x: x.start_time)
        
        # Validate no overlapping chapters
        for i in range(len(v) - 1):
            current_chapter = v[i]
            next_chapter = v[i + 1]
            
            if current_chapter.end_time and current_chapter.end_time > next_chapter.start_time:
                raise ValueError(f"Chapter '{current_chapter.title}' overlaps with '{next_chapter.title}'")
        
        return v
    
    def add_chapter(self, title: str, start_time: float, end_time: Optional[float] = None) -> None:
        """Add a chapter to the video."""
        chapter = Chapter(title=title, start_time=start_time, end_time=end_time)
        self.chapters.append(chapter)
        # Re-sort chapters
        self.chapters.sort(key=lambda x: x.start_time)
    
    def get_chapter_at_time(self, time: float) -> Optional[Chapter]:
        """Get the chapter at a specific time."""
        for chapter in self.chapters:
            if chapter.start_time <= time:
                if chapter.end_time is None or time < chapter.end_time:
                    return chapter
        return None
    
    def generate_youtube_description(self, paper_title: str, authors: List[str], 
                                   paper_url: Optional[str] = None) -> str:
        """Generate a comprehensive YouTube description."""
        description_parts = [
            self.description,
            "",
            "📚 Paper Information:",
            f"Title: {paper_title}",
            f"Authors: {', '.join(authors)}",
        ]
        
        if paper_url:
            description_parts.append(f"Paper URL: {paper_url}")
        
        if self.chapters:
            description_parts.extend([
                "",
                "📖 Chapters:",
            ])
            for chapter in self.chapters:
                description_parts.append(f"{chapter.start_timestamp} - {chapter.title}")
        
        if self.tags:
            description_parts.extend([
                "",
                f"🏷️ Tags: {', '.join(self.tags[:10])}",  # Limit displayed tags
            ])
        
        description_parts.extend([
            "",
            "🤖 This video was automatically generated using RASO (Research paper Automated Simulation & Orchestration Platform)",
            "",
            "#ResearchPaper #AI #Education #Science"
        ])
        
        return "\n".join(description_parts)


class VideoAsset(BaseModel):
    """Final video asset for distribution."""
    
    file_path: str = Field(..., description="Path to final video file")
    duration: float = Field(..., gt=0.0, description="Video duration in seconds")
    resolution: str = Field(..., description="Video resolution (e.g., '1920x1080')")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    
    # Technical specifications
    codec: str = Field(default="libx264", description="Video codec")
    bitrate: str = Field(default="5000k", description="Video bitrate")
    frame_rate: int = Field(default=30, description="Frame rate")
    audio_codec: str = Field(default="aac", description="Audio codec")
    
    # Content metadata
    chapters: List[Chapter] = Field(default_factory=list, description="Video chapters")
    metadata: VideoMetadata = Field(..., description="Video metadata")
    
    # Production metadata
    creation_time: datetime = Field(default_factory=datetime.now, description="Video creation time")
    render_time: Optional[float] = Field(default=None, description="Total render time in seconds")
    source_scenes: List[str] = Field(default_factory=list, description="Source scene IDs")
    
    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate video file path."""
        if not v:
            raise ValueError("File path cannot be empty")
        
        valid_extensions = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
        path = Path(v)
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f"File must have a valid video extension: {valid_extensions}")
        
        return v
    
    @validator("resolution")
    def validate_resolution(cls, v):
        """Validate resolution format."""
        if "x" not in v:
            raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        
        width_str, height_str = v.split("x")
        try:
            width, height = int(width_str), int(height_str)
            if width <= 0 or height <= 0:
                raise ValueError("Resolution dimensions must be positive")
        except ValueError:
            raise ValueError("Resolution dimensions must be numeric")
        
        return v
    
    @property
    def file_exists(self) -> bool:
        """Check if the video file exists."""
        return Path(self.file_path).exists()
    
    @property
    def file_size_mb(self) -> float:
        """Get file size in megabytes."""
        return self.file_size / (1024 * 1024)
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        td = timedelta(seconds=self.duration)
        total_seconds = int(td.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @property
    def aspect_ratio(self) -> float:
        """Calculate aspect ratio from resolution."""
        width_str, height_str = self.resolution.split("x")
        width, height = int(width_str), int(height_str)
        return width / height
    
    @property
    def is_youtube_ready(self) -> bool:
        """Check if video meets YouTube requirements."""
        # Basic YouTube requirements
        if self.file_size > 128 * 1024 * 1024 * 1024:  # 128GB limit
            return False
        
        if self.duration > 12 * 3600:  # 12 hour limit
            return False
        
        # Check if it's a supported format
        supported_formats = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
        path = Path(self.file_path)
        if path.suffix.lower() not in supported_formats:
            return False
        
        return True
    
    def get_upload_estimate(self, upload_speed_mbps: float = 10.0) -> float:
        """Estimate upload time in minutes."""
        file_size_mb = self.file_size_mb
        upload_speed_mbps_actual = upload_speed_mbps * 0.8  # Account for overhead
        upload_time_minutes = file_size_mb / upload_speed_mbps_actual / 60
        return upload_time_minutes
    
    def generate_filename(self, prefix: str = "raso_video") -> str:
        """Generate a standardized filename."""
        timestamp = self.creation_time.strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c for c in self.metadata.title if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title.replace(' ', '_')[:50]  # Limit length
        return f"{prefix}_{safe_title}_{timestamp}.mp4"
    
    class Config:
        schema_extra = {
            "example": {
                "file_path": "/data/output/final_video.mp4",
                "duration": 300.0,
                "resolution": "1920x1080",
                "file_size": 157286400,  # ~150MB
                "codec": "libx264",
                "bitrate": "5000k",
                "frame_rate": 30,
                "metadata": {
                    "title": "Understanding Transformer Architecture: Attention Is All You Need",
                    "description": "A comprehensive explanation of the revolutionary Transformer architecture...",
                    "tags": ["transformer", "attention", "neural networks", "AI", "machine learning"],
                    "category": "Education",
                    "privacy_status": "unlisted"
                },
                "source_scenes": ["scene1", "scene2", "scene3"]
            }
        }