"""
Video Composition System for the RASO platform.

Handles video composition, scene combination, audio-video synchronization,
and YouTube-compliant MP4 output generation using FFmpeg.
"""

import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from pydantic import BaseModel, Field

from backend.config import get_config
from backend.models.animation import AnimationAssets, RenderedScene
from backend.models.audio import AudioAssets, AudioScene
from backend.models.video import VideoAsset, Chapter
from agents.logging import AgentLogger
from agents.retry import retry


class CompositionResult(BaseModel):
    """Result of video composition."""
    
    success: bool = Field(..., description="Whether composition succeeded")
    output_path: Optional[str] = Field(default=None, description="Path to composed video")
    duration: float = Field(..., description="Total video duration")
    resolution: str = Field(..., description="Video resolution")
    file_size: int = Field(default=0, description="File size in bytes")
    composition_time: float = Field(..., description="Time taken to compose")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class VideoComposer:
    """Handles video composition and rendering."""
    
    def __init__(self):
        """Initialize video composer."""
        self.config = get_config()
        self.logger = AgentLogger(None)
    
    @retry(max_attempts=3, base_delay=2.0)
    async def compose_video(
        self,
        animation_assets: AnimationAssets,
        audio_assets: AudioAssets,
        output_path: str,
    ) -> CompositionResult:
        """
        Compose final video from animation and audio assets.
        
        Args:
            animation_assets: Rendered animation scenes
            audio_assets: Generated audio scenes
            output_path: Output video file path
            
        Returns:
            Composition result
        """
        start_time = datetime.now()
        
        try:
            # Create temporary directory for composition
            temp_dir = Path(self.config.temp_path) / "composition"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Prepare scene list with audio-video pairs
            scene_pairs = self._match_audio_video_scenes(
                animation_assets.scenes,
                audio_assets.scenes
            )
            
            if not scene_pairs:
                return CompositionResult(
                    success=False,
                    duration=0.0,
                    resolution=self.config.animation.resolution,
                    composition_time=0.0,
                    error_message="No matching audio-video scene pairs found",
                )
            
            # Create individual scene compositions
            composed_scenes = []
            for video_scene, audio_scene in scene_pairs:
                scene_output = temp_dir / f"composed_{video_scene.scene_id}.mp4"
                
                scene_result = await self._compose_single_scene(
                    video_scene=video_scene,
                    audio_scene=audio_scene,
                    output_path=str(scene_output),
                )
                
                if scene_result.success:
                    composed_scenes.append(str(scene_output))
                else:
                    self.logger.warning(f"Failed to compose scene {video_scene.scene_id}")
            
            if not composed_scenes:
                return CompositionResult(
                    success=False,
                    duration=0.0,
                    resolution=self.config.animation.resolution,
                    composition_time=(datetime.now() - start_time).total_seconds(),
                    error_message="No scenes were successfully composed",
                )
            
            # Concatenate all scenes into final video
            final_result = await self._concatenate_scenes(
                scene_paths=composed_scenes,
                output_path=output_path,
            )
            
            return final_result
            
        except Exception as e:
            composition_time = (datetime.now() - start_time).total_seconds()
            
            return CompositionResult(
                success=False,
                duration=0.0,
                resolution=self.config.animation.resolution,
                composition_time=composition_time,
                error_message=str(e),
            )    

    def _match_audio_video_scenes(
        self,
        video_scenes: List[RenderedScene],
        audio_scenes: List[AudioScene],
    ) -> List[Tuple[RenderedScene, AudioScene]]:
        """Match video and audio scenes by scene ID."""
        pairs = []
        
        for video_scene in video_scenes:
            # Find matching audio scene
            audio_scene = next(
                (a for a in audio_scenes if a.scene_id == video_scene.scene_id),
                None
            )
            
            if audio_scene:
                pairs.append((video_scene, audio_scene))
            else:
                self.logger.warning(f"No audio found for video scene {video_scene.scene_id}")
        
        return pairs
    
    async def _compose_single_scene(
        self,
        video_scene: RenderedScene,
        audio_scene: AudioScene,
        output_path: str,
    ) -> CompositionResult:
        """Compose a single scene with audio and video."""
        start_time = datetime.now()
        
        try:
            # Build ffmpeg command for audio-video composition
            command = [
                "ffmpeg",
                "-i", video_scene.file_path,  # Video input
                "-i", audio_scene.file_path,  # Audio input
                "-c:v", "libx264",  # Video codec
                "-c:a", "aac",      # Audio codec
                "-preset", self.config.video.preset,
                "-crf", "23",       # Quality setting
                "-shortest",        # Match shortest stream duration
                "-y",               # Overwrite output
                output_path
            ]
            
            # Execute ffmpeg
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            composition_time = (datetime.now() - start_time).total_seconds()
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Get video info
                duration, resolution = await self._get_video_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return CompositionResult(
                    success=True,
                    output_path=output_path,
                    duration=duration,
                    resolution=resolution,
                    file_size=file_size,
                    composition_time=composition_time,
                )
            else:
                return CompositionResult(
                    success=False,
                    duration=0.0,
                    resolution=self.config.animation.resolution,
                    composition_time=composition_time,
                    error_message=f"FFmpeg failed: {stderr.decode()}",
                )
                
        except Exception as e:
            composition_time = (datetime.now() - start_time).total_seconds()
            
            return CompositionResult(
                success=False,
                duration=0.0,
                resolution=self.config.animation.resolution,
                composition_time=composition_time,
                error_message=str(e),
            )
    
    async def _concatenate_scenes(
        self,
        scene_paths: List[str],
        output_path: str,
    ) -> CompositionResult:
        """Concatenate multiple scene videos into final output."""
        start_time = datetime.now()
        
        try:
            if len(scene_paths) == 1:
                # Single scene, just copy
                import shutil
                shutil.copy2(scene_paths[0], output_path)
                
                duration, resolution = await self._get_video_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return CompositionResult(
                    success=True,
                    output_path=output_path,
                    duration=duration,
                    resolution=resolution,
                    file_size=file_size,
                    composition_time=(datetime.now() - start_time).total_seconds(),
                )
            
            # Multiple scenes, use ffmpeg concat
            concat_file = Path(output_path).parent / "concat_list.txt"
            
            # Create concat file list
            with open(concat_file, 'w') as f:
                for scene_path in scene_paths:
                    f.write(f"file '{scene_path}'\n")
            
            # Build ffmpeg concat command
            command = [
                "ffmpeg",
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file),
                "-c", "copy",  # Copy streams without re-encoding
                "-y",
                output_path
            ]
            
            # Execute ffmpeg
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            composition_time = (datetime.now() - start_time).total_seconds()
            
            # Cleanup concat file
            if concat_file.exists():
                concat_file.unlink()
            
            if process.returncode == 0 and os.path.exists(output_path):
                duration, resolution = await self._get_video_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return CompositionResult(
                    success=True,
                    output_path=output_path,
                    duration=duration,
                    resolution=resolution,
                    file_size=file_size,
                    composition_time=composition_time,
                )
            else:
                return CompositionResult(
                    success=False,
                    duration=0.0,
                    resolution=self.config.animation.resolution,
                    composition_time=composition_time,
                    error_message=f"Concatenation failed: {stderr.decode()}",
                )
                
        except Exception as e:
            composition_time = (datetime.now() - start_time).total_seconds()
            
            return CompositionResult(
                success=False,
                duration=0.0,
                resolution=self.config.animation.resolution,
                composition_time=composition_time,
                error_message=str(e),
            )
    
    async def _get_video_info(self, video_path: str) -> Tuple[float, str]:
        """Get video duration and resolution."""
        try:
            command = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                video_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                
                # Get video stream info
                video_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "video":
                        video_stream = stream
                        break
                
                if video_stream:
                    duration = float(video_stream.get("duration", 0))
                    width = int(video_stream.get("width", 1920))
                    height = int(video_stream.get("height", 1080))
                    resolution = f"{width}x{height}"
                    
                    return duration, resolution
            
        except Exception as e:
            self.logger.warning(f"Failed to get video info: {str(e)}")
        
        # Fallback
        return 0.0, self.config.animation.resolution


# Global video composer instance
video_composer = VideoComposer()