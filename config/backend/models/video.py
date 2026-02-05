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
    
    # Production fields for YouTube compliance
    codec_info: Dict[str, Any] = Field(default_factory=dict, description="Detailed codec information")
    quality_preset: str = Field(default="medium", description="Quality preset used for encoding")
    validation_status: str = Field(default="pending", description="YouTube compliance validation status")
    
    # YouTube compliance fields
    youtube_compliant: bool = Field(default=False, description="Whether video meets YouTube specifications")
    compliance_issues: List[str] = Field(default_factory=list, description="List of compliance issues")
    compliance_warnings: List[str] = Field(default_factory=list, description="List of compliance warnings")
    
    # Enhanced metadata
    aspect_ratio_calculated: str = Field(default="", description="Calculated aspect ratio (e.g., '16:9')")
    thumbnail_path: Optional[str] = Field(default=None, description="Path to generated thumbnail")
    
    # Content metadata
    chapters: List[Chapter] = Field(default_factory=list, description="Video chapters")
    metadata: VideoMetadata = Field(..., description="Video metadata")
    
    # Production metadata
    creation_time: datetime = Field(default_factory=datetime.now, description="Video creation time")
    render_time: Optional[float] = Field(default=None, description="Total render time in seconds")
    source_scenes: List[str] = Field(default_factory=list, description="Source scene IDs")
    
    # Processing history for backward compatibility
    processing_history: List[Dict[str, Any]] = Field(default_factory=list, description="Processing steps history")
    
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
    
    @validator("quality_preset")
    def validate_quality_preset(cls, v):
        """Validate quality preset."""
        valid_presets = ["low", "medium", "high", "ultra", "custom"]
        if v not in valid_presets:
            raise ValueError(f"Quality preset must be one of: {valid_presets}")
        return v
    
    @validator("validation_status")
    def validate_validation_status(cls, v):
        """Validate validation status."""
        valid_statuses = ["pending", "validating", "compliant", "non_compliant", "error"]
        if v not in valid_statuses:
            raise ValueError(f"Validation status must be one of: {valid_statuses}")
        return v
    
    def __init__(self, **data):
        """Initialize VideoAsset with automatic aspect ratio calculation."""
        super().__init__(**data)
        if not self.aspect_ratio_calculated:
            self.aspect_ratio_calculated = self._calculate_aspect_ratio()
    
    def _calculate_aspect_ratio(self) -> str:
        """Calculate aspect ratio from resolution."""
        def gcd(a, b):
            while b:
                a, b = b, a % b
            return a
        
        width_str, height_str = self.resolution.split("x")
        width, height = int(width_str), int(height_str)
        
        divisor = gcd(width, height)
        ratio_w = width // divisor
        ratio_h = height // divisor
        
        return f"{ratio_w}:{ratio_h}"
    
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
        """Calculate numeric aspect ratio from resolution."""
        width_str, height_str = self.resolution.split("x")
        width, height = int(width_str), int(height_str)
        return width / height
    
    @property
    def is_youtube_ready(self) -> bool:
        """Check if video meets YouTube requirements."""
        # Use the validation status and compliance flag
        return self.youtube_compliant and self.validation_status == "compliant"
    
    def update_compliance_status(self, compliant: bool, issues: List[str] = None, 
                                warnings: List[str] = None):
        """Update YouTube compliance status."""
        self.youtube_compliant = compliant
        self.compliance_issues = issues or []
        self.compliance_warnings = warnings or []
        
        if compliant and not issues:
            self.validation_status = "compliant"
        elif issues:
            self.validation_status = "non_compliant"
        else:
            self.validation_status = "pending"
    
    def add_processing_step(self, step_name: str, details: Dict[str, Any]):
        """Add a processing step to history for backward compatibility."""
        step = {
            "step": step_name,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.processing_history.append(step)
    
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
    
    def get_youtube_metadata_dict(self) -> Dict[str, Any]:
        """Get metadata formatted for YouTube upload."""
        return {
            "title": self.metadata.title,
            "description": self.metadata.description,
            "tags": self.metadata.tags,
            "category": self.metadata.category,
            "privacy_status": self.metadata.privacy_status.value,
            "language": self.metadata.language,
            "thumbnail": self.thumbnail_path,
            "chapters": [
                {
                    "time": chapter.start_timestamp,
                    "title": chapter.title
                }
                for chapter in self.chapters
            ]
        }
    
    def validate_youtube_compliance(self) -> Dict[str, Any]:
        """Validate against YouTube specifications."""
        issues = []
        warnings = []
        
        # File size check (128GB limit)
        if self.file_size > 128 * 1024 * 1024 * 1024:
            issues.append(f"File size exceeds YouTube limit: {self.file_size_mb:.2f}MB > 128GB")
        
        # Duration check (12 hour limit)
        if self.duration > 12 * 3600:
            issues.append(f"Duration exceeds YouTube limit: {self.duration/3600:.2f}h > 12h")
        
        # Aspect ratio check
        if self.aspect_ratio_calculated not in ["16:9", "4:3", "1:1", "9:16"]:
            warnings.append(f"Non-standard aspect ratio: {self.aspect_ratio_calculated}")
        elif self.aspect_ratio_calculated != "16:9":
            warnings.append(f"Non-recommended aspect ratio: {self.aspect_ratio_calculated}. Recommended: 16:9")
        
        # Resolution check
        width_str, height_str = self.resolution.split("x")
        width, height = int(width_str), int(height_str)
        
        recommended_resolutions = [(1920, 1080), (1280, 720), (854, 480), (640, 360)]
        if (width, height) not in recommended_resolutions:
            warnings.append(f"Non-standard resolution: {self.resolution}")
        
        # Frame rate check
        if self.frame_rate not in range(24, 61):
            issues.append(f"Unsupported frame rate: {self.frame_rate}fps")
        elif self.frame_rate not in [24, 25, 30, 50, 60]:
            warnings.append(f"Non-recommended frame rate: {self.frame_rate}fps")
        
        # Update compliance status
        compliant = len(issues) == 0
        self.update_compliance_status(compliant, issues, warnings)
        
        return {
            "compliant": compliant,
            "issues": issues,
            "warnings": warnings,
            "recommendations": self._get_compliance_recommendations()
        }
    
    def _get_compliance_recommendations(self) -> List[str]:
        """Get recommendations for better YouTube compliance."""
        recommendations = []
        
        if self.aspect_ratio_calculated != "16:9":
            recommendations.append("Consider using 16:9 aspect ratio for optimal YouTube display")
        
        if self.frame_rate not in [30, 60]:
            recommendations.append("Consider using 30fps or 60fps for better compatibility")
        
        width_str, height_str = self.resolution.split("x")
        height = int(height_str)
        
        if height < 720:
            recommendations.append("Consider using at least 720p resolution for better quality")
        
        if self.file_size_mb > 1000:  # 1GB
            recommendations.append("Consider optimizing file size for faster upload")
        
        return recommendations
    
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
                "codec_info": {
                    "video_codec": "H.264",
                    "audio_codec": "AAC",
                    "container": "MP4"
                },
                "quality_preset": "high",
                "validation_status": "compliant",
                "youtube_compliant": True,
                "aspect_ratio_calculated": "16:9",
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