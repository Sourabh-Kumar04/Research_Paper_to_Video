"""
Video Validator for RASO Platform

This module provides comprehensive video validation functionality including
format compliance checking, codec verification, and quality assurance.
"""

import json
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from utils.video_utils import video_utils


class ValidationSeverity(Enum):
    """Validation issue severity levels."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """Represents a validation issue."""
    severity: ValidationSeverity
    message: str
    field: Optional[str] = None
    expected: Optional[str] = None
    actual: Optional[str] = None


@dataclass
class VideoProperties:
    """Video file properties."""
    duration: float
    file_size: int
    format_name: str
    video_codec: str
    audio_codec: str
    resolution: str
    width: int
    height: int
    fps: float
    bitrate: int
    audio_sample_rate: int
    audio_bitrate: int
    has_video: bool
    has_audio: bool
    aspect_ratio: float
    pixel_format: str


@dataclass
class ValidationResult:
    """Video validation result."""
    is_valid: bool
    properties: Optional[VideoProperties]
    issues: List[ValidationIssue]
    score: float  # 0.0 to 1.0, higher is better
    
    def has_errors(self) -> bool:
        """Check if validation has any errors."""
        return any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
    
    def has_warnings(self) -> bool:
        """Check if validation has any warnings."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)
    
    def get_errors(self) -> List[ValidationIssue]:
        """Get all error issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.ERROR]
    
    def get_warnings(self) -> List[ValidationIssue]:
        """Get all warning issues."""
        return [issue for issue in self.issues if issue.severity == ValidationSeverity.WARNING]


class VideoValidator:
    """Comprehensive video validation system."""
    
    def __init__(self):
        self.ffprobe_path = video_utils.get_ffprobe_path()
    
    async def validate_video(
        self,
        video_path: str,
        expected_duration: Optional[float] = None,
        min_file_size: int = 1024 * 1024,  # 1MB minimum
        require_audio: bool = True,
        youtube_compliance: bool = True
    ) -> ValidationResult:
        """
        Perform comprehensive video validation.
        
        Args:
            video_path: Path to the video file
            expected_duration: Expected video duration in seconds
            min_file_size: Minimum file size in bytes
            require_audio: Whether audio track is required
            youtube_compliance: Whether to check YouTube compliance
            
        Returns:
            ValidationResult with detailed validation information
        """
        issues = []
        
        # Check if file exists
        video_file = Path(video_path)
        if not video_file.exists():
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Video file not found: {video_path}"
            ))
            return ValidationResult(False, None, issues, 0.0)
        
        # Check file size
        file_size = video_file.stat().st_size
        if file_size < min_file_size:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"File size too small: {file_size} bytes, minimum: {min_file_size} bytes",
                "file_size",
                str(min_file_size),
                str(file_size)
            ))
        
        # Get video properties using FFprobe
        properties = await self._get_video_properties(video_path)
        if not properties:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "Failed to analyze video file - may be corrupted or invalid format"
            ))
            return ValidationResult(False, None, issues, 0.0)
        
        # Validate format compliance
        self._validate_format_compliance(properties, issues)
        
        # Validate codec compliance
        self._validate_codec_compliance(properties, issues)
        
        # Validate resolution and quality
        self._validate_resolution_quality(properties, issues)
        
        # Validate duration
        if expected_duration is not None:
            self._validate_duration(properties, expected_duration, issues)
        
        # Validate audio requirements
        if require_audio:
            self._validate_audio_requirements(properties, issues)
        
        # Validate YouTube compliance
        if youtube_compliance:
            self._validate_youtube_compliance(properties, issues)
        
        # Calculate validation score
        score = self._calculate_validation_score(issues)
        
        # Determine overall validity
        is_valid = not any(issue.severity == ValidationSeverity.ERROR for issue in issues)
        
        return ValidationResult(is_valid, properties, issues, score)
    
    async def _get_video_properties(self, video_path: str) -> Optional[VideoProperties]:
        """Extract video properties using FFprobe."""
        if not self.ffprobe_path:
            return None
        
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                "-show_streams",
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return None
            
            info = json.loads(result.stdout)
            return self._parse_video_properties(info, video_path)
            
        except Exception:
            return None
    
    def _parse_video_properties(self, ffprobe_info: Dict[str, Any], video_path: str) -> VideoProperties:
        """Parse FFprobe output into VideoProperties."""
        format_info = ffprobe_info.get("format", {})
        streams = ffprobe_info.get("streams", [])
        
        # Find video and audio streams
        video_stream = None
        audio_stream = None
        
        for stream in streams:
            if stream.get("codec_type") == "video" and not video_stream:
                video_stream = stream
            elif stream.get("codec_type") == "audio" and not audio_stream:
                audio_stream = stream
        
        # Extract properties
        duration = float(format_info.get("duration", 0))
        file_size = int(format_info.get("size", Path(video_path).stat().st_size))
        format_name = format_info.get("format_name", "")
        
        # Video properties
        video_codec = video_stream.get("codec_name", "") if video_stream else ""
        width = int(video_stream.get("width", 0)) if video_stream else 0
        height = int(video_stream.get("height", 0)) if video_stream else 0
        fps = self._parse_fps(video_stream.get("r_frame_rate", "0/1")) if video_stream else 0
        pixel_format = video_stream.get("pix_fmt", "") if video_stream else ""
        
        # Audio properties
        audio_codec = audio_stream.get("codec_name", "") if audio_stream else ""
        audio_sample_rate = int(audio_stream.get("sample_rate", 0)) if audio_stream else 0
        
        # Calculate bitrate
        bitrate = int(format_info.get("bit_rate", 0))
        audio_bitrate = int(audio_stream.get("bit_rate", 0)) if audio_stream else 0
        
        # Calculate aspect ratio
        aspect_ratio = width / height if height > 0 else 0
        
        return VideoProperties(
            duration=duration,
            file_size=file_size,
            format_name=format_name,
            video_codec=video_codec,
            audio_codec=audio_codec,
            resolution=f"{width}x{height}",
            width=width,
            height=height,
            fps=fps,
            bitrate=bitrate,
            audio_sample_rate=audio_sample_rate,
            audio_bitrate=audio_bitrate,
            has_video=video_stream is not None,
            has_audio=audio_stream is not None,
            aspect_ratio=aspect_ratio,
            pixel_format=pixel_format
        )
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse FPS from FFprobe format (e.g., '30/1')."""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den)
            return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0.0
    
    def _validate_format_compliance(self, properties: VideoProperties, issues: List[ValidationIssue]):
        """Validate video format compliance."""
        # Check for MP4 format
        if "mp4" not in properties.format_name.lower():
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Invalid container format: {properties.format_name}, expected MP4",
                "format",
                "mp4",
                properties.format_name
            ))
        
        # Check duration
        if properties.duration <= 0:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Invalid duration: {properties.duration} seconds",
                "duration"
            ))
        elif properties.duration > 3600:  # 1 hour
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Very long video: {properties.duration} seconds ({properties.duration/60:.1f} minutes)"
            ))
    
    def _validate_codec_compliance(self, properties: VideoProperties, issues: List[ValidationIssue]):
        """Validate codec compliance."""
        # Video codec validation
        if not properties.has_video:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "No video stream found"
            ))
        elif properties.video_codec != "h264":
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Invalid video codec: {properties.video_codec}, expected H.264",
                "video_codec",
                "h264",
                properties.video_codec
            ))
        
        # Audio codec validation
        if properties.has_audio and properties.audio_codec != "aac":
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Non-standard audio codec: {properties.audio_codec}, recommended: AAC",
                "audio_codec",
                "aac",
                properties.audio_codec
            ))
    
    def _validate_resolution_quality(self, properties: VideoProperties, issues: List[ValidationIssue]):
        """Validate resolution and quality parameters."""
        # Minimum resolution check
        if properties.width < 640 or properties.height < 480:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                f"Resolution too low: {properties.resolution}, minimum 640x480",
                "resolution",
                "640x480",
                properties.resolution
            ))
        
        # Standard resolution check
        standard_resolutions = [
            (1280, 720),   # 720p
            (1920, 1080),  # 1080p
            (2560, 1440),  # 1440p
            (3840, 2160),  # 4K
        ]
        
        is_standard = any(
            properties.width == w and properties.height == h
            for w, h in standard_resolutions
        )
        
        if not is_standard:
            issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                f"Non-standard resolution: {properties.resolution}"
            ))
        
        # Frame rate validation
        if properties.fps < 24:
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Low frame rate: {properties.fps} FPS, recommended: 30 FPS",
                "fps",
                "30",
                str(properties.fps)
            ))
        elif properties.fps > 60:
            issues.append(ValidationIssue(
                ValidationSeverity.INFO,
                f"High frame rate: {properties.fps} FPS"
            ))
        
        # Pixel format validation
        if properties.pixel_format != "yuv420p":
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Non-standard pixel format: {properties.pixel_format}, recommended: yuv420p",
                "pixel_format",
                "yuv420p",
                properties.pixel_format
            ))
    
    def _validate_duration(self, properties: VideoProperties, expected_duration: float, issues: List[ValidationIssue]):
        """Validate video duration against expected duration."""
        duration_diff = abs(properties.duration - expected_duration)
        tolerance = max(1.0, expected_duration * 0.05)  # 5% tolerance or 1 second minimum
        
        if duration_diff > tolerance:
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Duration mismatch: {properties.duration:.1f}s, expected: {expected_duration:.1f}s",
                "duration",
                f"{expected_duration:.1f}s",
                f"{properties.duration:.1f}s"
            ))
    
    def _validate_audio_requirements(self, properties: VideoProperties, issues: List[ValidationIssue]):
        """Validate audio requirements."""
        if not properties.has_audio:
            issues.append(ValidationIssue(
                ValidationSeverity.ERROR,
                "No audio stream found, audio is required"
            ))
            return
        
        # Sample rate validation
        if properties.audio_sample_rate != 44100:
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Non-standard audio sample rate: {properties.audio_sample_rate} Hz, recommended: 44100 Hz",
                "audio_sample_rate",
                "44100",
                str(properties.audio_sample_rate)
            ))
        
        # Audio bitrate validation
        if properties.audio_bitrate > 0:
            if properties.audio_bitrate < 128000:  # 128 kbps
                issues.append(ValidationIssue(
                    ValidationSeverity.WARNING,
                    f"Low audio bitrate: {properties.audio_bitrate//1000} kbps, recommended: 192+ kbps"
                ))
    
    def _validate_youtube_compliance(self, properties: VideoProperties, issues: List[ValidationIssue]):
        """Validate YouTube compliance requirements."""
        # Aspect ratio check (16:9 is preferred)
        target_aspect_ratio = 16.0 / 9.0
        aspect_ratio_diff = abs(properties.aspect_ratio - target_aspect_ratio)
        
        if aspect_ratio_diff > 0.1:  # Allow some tolerance
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Non-standard aspect ratio: {properties.aspect_ratio:.2f}, YouTube prefers 16:9 ({target_aspect_ratio:.2f})",
                "aspect_ratio",
                f"{target_aspect_ratio:.2f}",
                f"{properties.aspect_ratio:.2f}"
            ))
        
        # File size check (YouTube limit is 128GB, but warn at 2GB)
        if properties.file_size > 2 * 1024 * 1024 * 1024:  # 2GB
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Large file size: {properties.file_size // (1024*1024)} MB, consider compression"
            ))
        
        # Duration check (YouTube allows up to 12 hours for verified accounts)
        if properties.duration > 12 * 3600:  # 12 hours
            issues.append(ValidationIssue(
                ValidationSeverity.WARNING,
                f"Very long video: {properties.duration/3600:.1f} hours, YouTube limit is 12 hours"
            ))
    
    def _calculate_validation_score(self, issues: List[ValidationIssue]) -> float:
        """Calculate validation score based on issues."""
        if not issues:
            return 1.0
        
        # Scoring weights
        error_weight = -0.3
        warning_weight = -0.1
        info_weight = -0.02
        
        score = 1.0
        
        for issue in issues:
            if issue.severity == ValidationSeverity.ERROR:
                score += error_weight
            elif issue.severity == ValidationSeverity.WARNING:
                score += warning_weight
            elif issue.severity == ValidationSeverity.INFO:
                score += info_weight
        
        return max(0.0, min(1.0, score))
    
    def validate_video_sync(self, video_path: str) -> bool:
        """
        Quick synchronous validation check.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if basic validation passes
        """
        try:
            video_file = Path(video_path)
            if not video_file.exists():
                return False
            
            # Check file size (must be > 1KB)
            if video_file.stat().st_size < 1024:
                return False
            
            # Try to get basic info with FFprobe
            if not self.ffprobe_path:
                return True  # Can't validate without FFprobe, assume OK
            
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            return result.returncode == 0
            
        except Exception:
            return False


# Global instance for easy access
video_validator = VideoValidator()