"""
Comprehensive Content Validation System for RASO platform.

Validates script files, audio files, and animation files to ensure
they contain real content and meet quality standards.
"""

import os
import json
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ValidationResult:
    """Result of content validation."""
    valid: bool
    score: float  # 0.0 to 1.0
    errors: List[str]
    warnings: List[str]
    stats: Dict[str, Any]


class ContentValidator:
    """Comprehensive content validation system."""
    
    def __init__(self):
        """Initialize the content validator."""
        self.min_script_length = 50  # Minimum characters for real script
        self.min_audio_size = 1000   # Minimum bytes for real audio
        self.min_video_size = 10000  # Minimum bytes for real video
        self.max_silence_ratio = 0.8  # Maximum ratio of silence in audio
    
    def validate_script_content(self, script_file_path: str) -> ValidationResult:
        """Validate script file contains real content."""
        errors = []
        warnings = []
        stats = {}
        
        try:
            script_path = Path(script_file_path)
            
            # Check file existence
            if not script_path.exists():
                errors.append("Script file does not exist")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            # Check file size
            file_size = script_path.stat().st_size
            stats["file_size_bytes"] = file_size
            
            if file_size == 0:
                errors.append("Script file is empty")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            # Read and analyze content
            try:
                with open(script_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                try:
                    with open(script_path, 'r', encoding='latin-1') as f:
                        content = f.read()
                except Exception as e:
                    errors.append(f"Cannot read script file: {e}")
                    return ValidationResult(False, 0.0, errors, warnings, stats)
            
            # Analyze content quality
            content_length = len(content.strip())
            stats["content_length"] = content_length
            
            if content_length < self.min_script_length:
                errors.append(f"Script too short: {content_length} characters (minimum: {self.min_script_length})")
            
            # Check for placeholder content
            placeholder_indicators = [
                "placeholder", "lorem ipsum", "sample text", "test content",
                "todo", "tbd", "coming soon", "under construction"
            ]
            
            content_lower = content.lower()
            found_placeholders = [p for p in placeholder_indicators if p in content_lower]
            if found_placeholders:
                warnings.append(f"Possible placeholder content detected: {found_placeholders}")
            
            # Check for meaningful content
            word_count = len(content.split())
            stats["word_count"] = word_count
            
            if word_count < 20:
                errors.append(f"Script has too few words: {word_count} (minimum: 20)")
            
            # Check for JSON structure (if it's a structured script)
            try:
                if content.strip().startswith('{') or content.strip().startswith('['):
                    json_data = json.loads(content)
                    stats["is_json"] = True
                    stats["json_structure"] = type(json_data).__name__
                    
                    # Validate JSON script structure
                    if isinstance(json_data, dict) and "scenes" in json_data:
                        scenes = json_data["scenes"]
                        stats["scene_count"] = len(scenes)
                        
                        if len(scenes) == 0:
                            errors.append("Script has no scenes")
                        elif len(scenes) < 2:
                            warnings.append("Script has only one scene")
                        
                        # Check scene content
                        empty_scenes = 0
                        for i, scene in enumerate(scenes):
                            if isinstance(scene, dict):
                                narration = scene.get("narration", "")
                                if not narration or len(narration.strip()) < 10:
                                    empty_scenes += 1
                        
                        if empty_scenes > 0:
                            errors.append(f"{empty_scenes} scenes have empty or minimal narration")
                        
                        stats["empty_scenes"] = empty_scenes
                else:
                    stats["is_json"] = False
            except json.JSONDecodeError:
                stats["is_json"] = False
            
            # Calculate quality score
            score = 1.0
            if content_length < self.min_script_length:
                score -= 0.5
            if word_count < 20:
                score -= 0.3
            if found_placeholders:
                score -= 0.2
            if stats.get("empty_scenes", 0) > 0:
                score -= 0.3
            
            score = max(0.0, score)
            stats["quality_score"] = score
            
            is_valid = len(errors) == 0
            return ValidationResult(is_valid, score, errors, warnings, stats)
            
        except Exception as e:
            errors.append(f"Script validation failed: {e}")
            return ValidationResult(False, 0.0, errors, warnings, stats)
    
    def validate_audio_content(self, audio_file_path: str) -> ValidationResult:
        """Validate audio file contains real content (not silent)."""
        errors = []
        warnings = []
        stats = {}
        
        try:
            audio_path = Path(audio_file_path)
            
            # Check file existence
            if not audio_path.exists():
                errors.append("Audio file does not exist")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            # Check file size
            file_size = audio_path.stat().st_size
            stats["file_size_bytes"] = file_size
            
            if file_size == 0:
                errors.append("Audio file is empty")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            if file_size < self.min_audio_size:
                warnings.append(f"Audio file is very small: {file_size} bytes")
            
            # Use ffprobe to analyze audio properties
            try:
                result = subprocess.run([
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_format", "-show_streams", str(audio_path)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    
                    # Check format info
                    format_info = info.get("format", {})
                    duration = float(format_info.get("duration", 0))
                    stats["duration"] = duration
                    
                    if duration == 0:
                        errors.append("Audio file has zero duration")
                    elif duration < 1.0:
                        warnings.append(f"Audio file is very short: {duration:.2f}s")
                    
                    # Check stream info
                    streams = info.get("streams", [])
                    audio_streams = [s for s in streams if s.get("codec_type") == "audio"]
                    
                    if not audio_streams:
                        errors.append("No audio stream found in file")
                    else:
                        audio_stream = audio_streams[0]
                        stats["codec"] = audio_stream.get("codec_name", "unknown")
                        stats["sample_rate"] = audio_stream.get("sample_rate", "unknown")
                        stats["channels"] = audio_stream.get("channels", "unknown")
                        
                        # Check for reasonable audio properties
                        sample_rate = int(audio_stream.get("sample_rate", 0))
                        if sample_rate > 0 and sample_rate < 8000:
                            warnings.append(f"Low sample rate: {sample_rate}Hz")
                        elif sample_rate > 96000:
                            warnings.append(f"Very high sample rate: {sample_rate}Hz")
                
                else:
                    warnings.append("Could not analyze audio properties with ffprobe")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
                warnings.append(f"Audio analysis failed: {e}")
            
            # Try to detect silence using ffmpeg
            try:
                silence_result = self._detect_silence_ratio(str(audio_path))
                if silence_result is not None:
                    stats["silence_ratio"] = silence_result
                    
                    if silence_result > self.max_silence_ratio:
                        errors.append(f"Audio is mostly silent: {silence_result:.1%} silence")
                    elif silence_result > 0.5:
                        warnings.append(f"Audio has significant silence: {silence_result:.1%}")
                        
            except Exception as e:
                warnings.append(f"Silence detection failed: {e}")
            
            # Calculate quality score
            score = 1.0
            if file_size < self.min_audio_size:
                score -= 0.3
            if stats.get("duration", 0) < 1.0:
                score -= 0.4
            if stats.get("silence_ratio", 0) > self.max_silence_ratio:
                score -= 0.5
            elif stats.get("silence_ratio", 0) > 0.5:
                score -= 0.2
            
            score = max(0.0, score)
            stats["quality_score"] = score
            
            is_valid = len(errors) == 0
            return ValidationResult(is_valid, score, errors, warnings, stats)
            
        except Exception as e:
            errors.append(f"Audio validation failed: {e}")
            return ValidationResult(False, 0.0, errors, warnings, stats)
    
    def validate_video_content(self, video_file_path: str) -> ValidationResult:
        """Validate video file contains real content."""
        errors = []
        warnings = []
        stats = {}
        
        try:
            video_path = Path(video_file_path)
            
            # Check file existence
            if not video_path.exists():
                errors.append("Video file does not exist")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            # Check file size
            file_size = video_path.stat().st_size
            stats["file_size_bytes"] = file_size
            
            if file_size == 0:
                errors.append("Video file is empty")
                return ValidationResult(False, 0.0, errors, warnings, stats)
            
            if file_size < self.min_video_size:
                warnings.append(f"Video file is very small: {file_size} bytes")
            
            # Use ffprobe to analyze video properties
            try:
                result = subprocess.run([
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_format", "-show_streams", str(video_path)
                ], capture_output=True, text=True, timeout=30)
                
                if result.returncode == 0:
                    info = json.loads(result.stdout)
                    
                    # Check format info
                    format_info = info.get("format", {})
                    duration = float(format_info.get("duration", 0))
                    stats["duration"] = duration
                    
                    if duration == 0:
                        errors.append("Video file has zero duration")
                    elif duration < 1.0:
                        warnings.append(f"Video file is very short: {duration:.2f}s")
                    
                    # Check stream info
                    streams = info.get("streams", [])
                    video_streams = [s for s in streams if s.get("codec_type") == "video"]
                    
                    if not video_streams:
                        errors.append("No video stream found in file")
                    else:
                        video_stream = video_streams[0]
                        stats["codec"] = video_stream.get("codec_name", "unknown")
                        stats["width"] = video_stream.get("width", 0)
                        stats["height"] = video_stream.get("height", 0)
                        stats["fps"] = video_stream.get("r_frame_rate", "unknown")
                        
                        # Check for reasonable video properties
                        width = int(video_stream.get("width", 0))
                        height = int(video_stream.get("height", 0))
                        
                        if width == 0 or height == 0:
                            errors.append("Video has invalid dimensions")
                        elif width < 640 or height < 480:
                            warnings.append(f"Low resolution video: {width}x{height}")
                        
                        stats["resolution"] = f"{width}x{height}"
                
                else:
                    warnings.append("Could not analyze video properties with ffprobe")
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError) as e:
                warnings.append(f"Video analysis failed: {e}")
            
            # Calculate quality score
            score = 1.0
            if file_size < self.min_video_size:
                score -= 0.3
            if stats.get("duration", 0) < 1.0:
                score -= 0.4
            if stats.get("width", 0) < 640 or stats.get("height", 0) < 480:
                score -= 0.2
            
            score = max(0.0, score)
            stats["quality_score"] = score
            
            is_valid = len(errors) == 0
            return ValidationResult(is_valid, score, errors, warnings, stats)
            
        except Exception as e:
            errors.append(f"Video validation failed: {e}")
            return ValidationResult(False, 0.0, errors, warnings, stats)
    
    def _detect_silence_ratio(self, audio_path: str) -> Optional[float]:
        """Detect the ratio of silence in an audio file."""
        try:
            # Use ffmpeg silencedetect filter
            cmd = [
                "ffmpeg", "-i", audio_path,
                "-af", "silencedetect=noise=-30dB:duration=0.1",
                "-f", "null", "-"
            ]
            
            process = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
            
            # Parse silence detection output
            stderr_text = process.stderr.decode()
            silence_starts = []
            silence_ends = []
            
            for line in stderr_text.split('\n'):
                if 'silence_start:' in line:
                    try:
                        start_time = float(line.split('silence_start:')[1].strip())
                        silence_starts.append(start_time)
                    except (ValueError, IndexError):
                        pass
                elif 'silence_end:' in line:
                    try:
                        end_time = float(line.split('silence_end:')[1].split('|')[0].strip())
                        silence_ends.append(end_time)
                    except (ValueError, IndexError):
                        pass
            
            # Calculate total silence duration
            total_silence = 0.0
            for start, end in zip(silence_starts, silence_ends):
                total_silence += (end - start)
            
            # Get total duration
            duration_result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", audio_path
            ], capture_output=True, text=True, timeout=10)
            
            if duration_result.returncode == 0:
                info = json.loads(duration_result.stdout)
                total_duration = float(info.get("format", {}).get("duration", 0))
                
                if total_duration > 0:
                    silence_ratio = total_silence / total_duration
                    return min(1.0, silence_ratio)  # Cap at 100%
            
            return None
            
        except Exception:
            return None
    
    def validate_all_content(self, script_path: str, audio_files: List[str], video_files: List[str]) -> Dict[str, ValidationResult]:
        """Validate all content files comprehensively."""
        results = {}
        
        # Validate script
        if script_path:
            results["script"] = self.validate_script_content(script_path)
        
        # Validate audio files
        results["audio"] = []
        for audio_file in audio_files:
            result = self.validate_audio_content(audio_file)
            results["audio"].append(result)
        
        # Validate video files
        results["video"] = []
        for video_file in video_files:
            result = self.validate_video_content(video_file)
            results["video"].append(result)
        
        return results


# Global content validator instance
content_validator = ContentValidator()