"""
Quality Preset Manager for RASO Video Generation

This module manages video quality presets, encoding parameters, and provides
configuration for different video quality levels (low/medium/high).
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from enum import Enum


class QualityLevel(Enum):
    """Video quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CUSTOM = "custom"


@dataclass
class EncodingParams:
    """Video encoding parameters."""
    resolution: str
    width: int
    height: int
    bitrate: str
    crf: int
    preset: str
    fps: int
    audio_codec: str
    video_codec: str
    pixel_format: str
    audio_bitrate: str
    audio_sample_rate: int
    
    def to_ffmpeg_args(self) -> List[str]:
        """Convert encoding parameters to FFmpeg command line arguments."""
        args = [
            "-c:v", self.video_codec,
            "-c:a", self.audio_codec,
            "-preset", self.preset,
            "-crf", str(self.crf),
            "-b:v", self.bitrate,
            "-b:a", self.audio_bitrate,
            "-ar", str(self.audio_sample_rate),
            "-r", str(self.fps),
            "-s", self.resolution,
            "-pix_fmt", self.pixel_format,
            "-movflags", "+faststart",  # Optimize for web streaming
            "-profile:v", "high",  # H.264 high profile
            "-level", "4.0",  # H.264 level 4.0 for broad compatibility
        ]
        return args
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "resolution": self.resolution,
            "width": self.width,
            "height": self.height,
            "bitrate": self.bitrate,
            "crf": self.crf,
            "preset": self.preset,
            "fps": self.fps,
            "audio_codec": self.audio_codec,
            "video_codec": self.video_codec,
            "pixel_format": self.pixel_format,
            "audio_bitrate": self.audio_bitrate,
            "audio_sample_rate": self.audio_sample_rate,
        }


class QualityPresetManager:
    """Manages video quality presets and encoding parameters."""
    
    def __init__(self):
        self._presets = self._initialize_presets()
        self._custom_presets = {}
    
    def _initialize_presets(self) -> Dict[QualityLevel, EncodingParams]:
        """Initialize default quality presets."""
        return {
            QualityLevel.LOW: EncodingParams(
                resolution="1280x720",
                width=1280,
                height=720,
                bitrate="3500k",
                crf=28,
                preset="fast",
                fps=30,
                audio_codec="aac",
                video_codec="libx264",
                pixel_format="yuv420p",
                audio_bitrate="128k",
                audio_sample_rate=44100,
            ),
            QualityLevel.MEDIUM: EncodingParams(
                resolution="1920x1080",
                width=1920,
                height=1080,
                bitrate="5500k",
                crf=23,
                preset="medium",
                fps=30,
                audio_codec="aac",
                video_codec="libx264",
                pixel_format="yuv420p",
                audio_bitrate="192k",
                audio_sample_rate=44100,
            ),
            QualityLevel.HIGH: EncodingParams(
                resolution="1920x1080",
                width=1920,
                height=1080,
                bitrate="8500k",
                crf=18,
                preset="slow",
                fps=30,
                audio_codec="aac",
                video_codec="libx264",
                pixel_format="yuv420p",
                audio_bitrate="256k",
                audio_sample_rate=44100,
            ),
        }
    
    def get_preset(self, quality: str) -> EncodingParams:
        """
        Get encoding parameters for a quality level.
        
        Args:
            quality: Quality level string ("low", "medium", "high", or custom name)
            
        Returns:
            EncodingParams for the specified quality
            
        Raises:
            ValueError: If quality level is not found
        """
        # Try standard presets first
        try:
            quality_level = QualityLevel(quality.lower())
            if quality_level in self._presets:
                return self._presets[quality_level]
        except ValueError:
            pass
        
        # Try custom presets
        if quality in self._custom_presets:
            return self._custom_presets[quality]
        
        # Default to medium quality
        if quality.lower() not in ["low", "medium", "high"]:
            print(f"Warning: Unknown quality '{quality}', using medium quality")
            return self._presets[QualityLevel.MEDIUM]
        
        raise ValueError(f"Quality preset '{quality}' not found")
    
    def get_available_presets(self) -> List[str]:
        """Get list of available preset names."""
        standard_presets = [level.value for level in QualityLevel if level != QualityLevel.CUSTOM]
        custom_presets = list(self._custom_presets.keys())
        return standard_presets + custom_presets
    
    def add_custom_preset(self, name: str, params: EncodingParams) -> None:
        """
        Add a custom quality preset.
        
        Args:
            name: Name for the custom preset
            params: Encoding parameters
        """
        self._custom_presets[name] = params
    
    def create_custom_preset(
        self,
        name: str,
        resolution: str = "1920x1080",
        bitrate: str = "5500k",
        crf: int = 23,
        preset: str = "medium",
        fps: int = 30,
        audio_bitrate: str = "192k",
        **kwargs
    ) -> EncodingParams:
        """
        Create a custom quality preset with specified parameters.
        
        Args:
            name: Name for the custom preset
            resolution: Video resolution (e.g., "1920x1080")
            bitrate: Video bitrate (e.g., "5500k")
            crf: Constant Rate Factor (lower = higher quality)
            preset: FFmpeg preset (ultrafast, fast, medium, slow, veryslow)
            fps: Frames per second
            audio_bitrate: Audio bitrate (e.g., "192k")
            **kwargs: Additional parameters
            
        Returns:
            Created EncodingParams
        """
        # Parse resolution
        try:
            width, height = map(int, resolution.split('x'))
        except ValueError:
            raise ValueError(f"Invalid resolution format: {resolution}")
        
        # Create encoding parameters
        params = EncodingParams(
            resolution=resolution,
            width=width,
            height=height,
            bitrate=bitrate,
            crf=crf,
            preset=preset,
            fps=fps,
            audio_codec=kwargs.get("audio_codec", "aac"),
            video_codec=kwargs.get("video_codec", "libx264"),
            pixel_format=kwargs.get("pixel_format", "yuv420p"),
            audio_bitrate=audio_bitrate,
            audio_sample_rate=kwargs.get("audio_sample_rate", 44100),
        )
        
        # Validate parameters
        self._validate_encoding_params(params)
        
        # Add to custom presets
        self.add_custom_preset(name, params)
        
        return params
    
    def _validate_encoding_params(self, params: EncodingParams) -> None:
        """
        Validate encoding parameters.
        
        Args:
            params: Encoding parameters to validate
            
        Raises:
            ValueError: If parameters are invalid
        """
        # Validate resolution
        if params.width < 640 or params.height < 480:
            raise ValueError(f"Resolution too small: {params.resolution}, minimum 640x480")
        
        if params.width > 7680 or params.height > 4320:
            raise ValueError(f"Resolution too large: {params.resolution}, maximum 7680x4320")
        
        # Validate CRF
        if not 0 <= params.crf <= 51:
            raise ValueError(f"Invalid CRF value: {params.crf}, must be 0-51")
        
        # Validate FPS
        if not 1 <= params.fps <= 120:
            raise ValueError(f"Invalid FPS: {params.fps}, must be 1-120")
        
        # Validate preset
        valid_presets = ["ultrafast", "superfast", "veryfast", "faster", "fast", "medium", "slow", "slower", "veryslow"]
        if params.preset not in valid_presets:
            raise ValueError(f"Invalid preset: {params.preset}, must be one of {valid_presets}")
        
        # Validate codecs
        if params.video_codec not in ["libx264", "libx265", "h264_nvenc", "h264_qsv"]:
            print(f"Warning: Uncommon video codec: {params.video_codec}")
        
        if params.audio_codec not in ["aac", "mp3", "libmp3lame"]:
            print(f"Warning: Uncommon audio codec: {params.audio_codec}")
    
    def get_youtube_optimized_preset(self, base_quality: str = "medium") -> EncodingParams:
        """
        Get YouTube-optimized encoding parameters.
        
        Args:
            base_quality: Base quality level to optimize from
            
        Returns:
            YouTube-optimized EncodingParams
        """
        base_params = self.get_preset(base_quality)
        
        # YouTube-specific optimizations
        youtube_params = EncodingParams(
            resolution=base_params.resolution,
            width=base_params.width,
            height=base_params.height,
            bitrate=base_params.bitrate,
            crf=base_params.crf,
            preset=base_params.preset,
            fps=base_params.fps,
            audio_codec="aac",  # YouTube prefers AAC
            video_codec="libx264",  # YouTube prefers H.264
            pixel_format="yuv420p",  # YouTube requirement
            audio_bitrate=base_params.audio_bitrate,
            audio_sample_rate=44100,  # YouTube standard
        )
        
        return youtube_params
    
    def estimate_file_size(self, params: EncodingParams, duration_seconds: float) -> int:
        """
        Estimate output file size in bytes.
        
        Args:
            params: Encoding parameters
            duration_seconds: Video duration in seconds
            
        Returns:
            Estimated file size in bytes
        """
        # Parse bitrate (remove 'k' suffix and convert to bits per second)
        video_bitrate_kbps = int(params.bitrate.rstrip('k'))
        audio_bitrate_kbps = int(params.audio_bitrate.rstrip('k'))
        
        total_bitrate_bps = (video_bitrate_kbps + audio_bitrate_kbps) * 1000
        
        # Estimate file size (add 10% overhead for container and metadata)
        estimated_size = int((total_bitrate_bps * duration_seconds / 8) * 1.1)
        
        return estimated_size
    
    def get_preset_info(self, quality: str) -> Dict[str, Any]:
        """
        Get detailed information about a quality preset.
        
        Args:
            quality: Quality level name
            
        Returns:
            Dictionary with preset information
        """
        try:
            params = self.get_preset(quality)
            
            # Estimate file size for a 5-minute video
            estimated_size_5min = self.estimate_file_size(params, 300)
            
            return {
                "name": quality,
                "resolution": params.resolution,
                "bitrate": params.bitrate,
                "crf": params.crf,
                "preset": params.preset,
                "fps": params.fps,
                "audio_codec": params.audio_codec,
                "video_codec": params.video_codec,
                "estimated_size_5min_mb": round(estimated_size_5min / (1024 * 1024), 1),
                "parameters": params.to_dict(),
            }
        except ValueError as e:
            return {"error": str(e)}


# Global instance for easy access
quality_manager = QualityPresetManager()