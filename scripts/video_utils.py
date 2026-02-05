"""
Video Processing Utilities for RASO Platform

This module provides utilities for video processing, FFmpeg detection,
and video validation for the production video generation system.
"""

import os
import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from utils.ffmpeg_installer import FFmpegInstaller


class VideoUtils:
    """Utilities for video processing and validation."""
    
    def __init__(self):
        self.installer = FFmpegInstaller()
        self.ffmpeg_path = None
        self.ffprobe_path = None
        self._initialize_ffmpeg()
    
    def _initialize_ffmpeg(self):
        """Initialize FFmpeg paths."""
        available, path = self.installer.check_ffmpeg_availability()
        if available:
            self.ffmpeg_path = self.installer.ffmpeg_path
            self.ffprobe_path = self.installer.ffprobe_path
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available for use."""
        return self.ffmpeg_path is not None
    
    def get_ffmpeg_path(self) -> Optional[str]:
        """Get the path to FFmpeg executable."""
        return self.ffmpeg_path
    
    def get_ffprobe_path(self) -> Optional[str]:
        """Get the path to FFprobe executable."""
        return self.ffprobe_path
    
    async def validate_video_file(self, video_path: str) -> Dict[str, Any]:
        """
        Validate a video file using FFprobe.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Dictionary with validation results
        """
        if not self.ffprobe_path:
            return {
                "valid": False,
                "error": "FFprobe not available"
            }
        
        if not Path(video_path).exists():
            return {
                "valid": False,
                "error": f"Video file not found: {video_path}"
            }
        
        try:
            # Get video information using ffprobe
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
                return {
                    "valid": False,
                    "error": f"FFprobe failed: {result.stderr}"
                }
            
            # Parse JSON output
            info = json.loads(result.stdout)
            
            # Validate video properties
            validation_result = self._validate_video_properties(info)
            validation_result["ffprobe_info"] = info
            
            return validation_result
            
        except subprocess.TimeoutExpired:
            return {
                "valid": False,
                "error": "FFprobe execution timed out"
            }
        except json.JSONDecodeError as e:
            return {
                "valid": False,
                "error": f"Failed to parse FFprobe output: {str(e)}"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": f"Video validation failed: {str(e)}"
            }
    
    def _validate_video_properties(self, ffprobe_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate video properties from FFprobe output.
        
        Args:
            ffprobe_info: FFprobe JSON output
            
        Returns:
            Validation results
        """
        validation = {
            "valid": True,
            "format_valid": False,
            "video_codec_valid": False,
            "audio_codec_valid": False,
            "duration_valid": False,
            "resolution_valid": False,
            "errors": [],
            "warnings": [],
            "properties": {}
        }
        
        try:
            # Check format
            format_info = ffprobe_info.get("format", {})
            format_name = format_info.get("format_name", "")
            
            if "mp4" in format_name:
                validation["format_valid"] = True
            else:
                validation["errors"].append(f"Invalid format: {format_name}, expected MP4")
            
            # Get duration
            duration = float(format_info.get("duration", 0))
            validation["properties"]["duration"] = duration
            
            if duration > 0:
                validation["duration_valid"] = True
            else:
                validation["errors"].append("Invalid duration: must be greater than 0")
            
            # Check streams
            streams = ffprobe_info.get("streams", [])
            video_stream = None
            audio_stream = None
            
            for stream in streams:
                if stream.get("codec_type") == "video":
                    video_stream = stream
                elif stream.get("codec_type") == "audio":
                    audio_stream = stream
            
            # Validate video stream
            if video_stream:
                video_codec = video_stream.get("codec_name", "")
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                
                validation["properties"]["video_codec"] = video_codec
                validation["properties"]["resolution"] = f"{width}x{height}"
                
                if video_codec == "h264":
                    validation["video_codec_valid"] = True
                else:
                    validation["errors"].append(f"Invalid video codec: {video_codec}, expected H.264")
                
                if width >= 1280 and height >= 720:
                    validation["resolution_valid"] = True
                else:
                    validation["errors"].append(f"Invalid resolution: {width}x{height}, minimum 1280x720")
            else:
                validation["errors"].append("No video stream found")
            
            # Validate audio stream
            if audio_stream:
                audio_codec = audio_stream.get("codec_name", "")
                sample_rate = int(audio_stream.get("sample_rate", 0))
                
                validation["properties"]["audio_codec"] = audio_codec
                validation["properties"]["sample_rate"] = sample_rate
                
                if audio_codec == "aac":
                    validation["audio_codec_valid"] = True
                else:
                    validation["warnings"].append(f"Audio codec: {audio_codec}, recommended: AAC")
                
                if sample_rate == 44100:
                    validation["properties"]["sample_rate_valid"] = True
                else:
                    validation["warnings"].append(f"Sample rate: {sample_rate}, recommended: 44100")
            else:
                validation["warnings"].append("No audio stream found")
            
            # Overall validation
            validation["valid"] = (
                validation["format_valid"] and
                validation["video_codec_valid"] and
                validation["duration_valid"] and
                validation["resolution_valid"]
            )
            
        except Exception as e:
            validation["valid"] = False
            validation["errors"].append(f"Property validation failed: {str(e)}")
        
        return validation
    
    def get_video_duration(self, video_path: str) -> float:
        """
        Get video duration in seconds.
        
        Args:
            video_path: Path to the video file
            
        Returns:
            Duration in seconds, or 0 if failed
        """
        if not self.ffprobe_path or not Path(video_path).exists():
            return 0.0
        
        try:
            cmd = [
                self.ffprobe_path,
                "-v", "quiet",
                "-print_format", "json",
                "-show_format",
                video_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info.get("format", {}).get("duration", 0))
                return duration
            
        except Exception:
            pass
        
        return 0.0
    
    def ensure_ffmpeg_available(self) -> Tuple[bool, str]:
        """
        Ensure FFmpeg is available, attempt installation if not.
        
        Returns:
            Tuple of (success, message)
        """
        if self.is_ffmpeg_available():
            return True, "FFmpeg is already available"
        
        # Try to detect FFmpeg again
        self._initialize_ffmpeg()
        if self.is_ffmpeg_available():
            return True, "FFmpeg detected"
        
        # Attempt automatic installation on Windows
        if self.installer.system == "windows":
            success, message = self.installer.install_ffmpeg_windows()
            if success:
                self._initialize_ffmpeg()
                return True, message
            else:
                return False, f"FFmpeg installation failed: {message}"
        else:
            instructions = self.installer.get_installation_instructions()
            return False, f"FFmpeg not found. Please install manually:\n{instructions}"


# Global instance for easy access
video_utils = VideoUtils()