"""
Video Composition Agent for the RASO platform.

Handles final video composition, scene combination, and YouTube-ready output generation.
"""

from typing import Dict, Any
from datetime import datetime
from pathlib import Path

from agents.base import BaseAgent
from backend.models.animation import AnimationAssets
from backend.models.audio import AudioAssets
from backend.models.video import VideoAsset, Chapter
from video.composition import video_composer
from agents.retry import retry


class VideoCompositionAgent(BaseAgent):
    """Agent responsible for final video composition."""
    
    name = "VideoCompositionAgent"
    description = "Composes final video from animation and audio assets"
    
    def __init__(self):
        """Initialize video composition agent."""
        super().__init__()
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute video composition.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final video
        """
        self.validate_input(state)
        
        try:
            animations = AnimationAssets(**state["animations"])
            audio = AudioAssets(**state["audio"])
            
            self.log_progress("Starting video composition", state)
            
            # Create output path
            output_dir = Path(self.config.data_path) / "videos"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            video_filename = f"raso_video_{int(datetime.now().timestamp())}.mp4"
            output_path = str(output_dir / video_filename)
            
            # Compose video
            result = await video_composer.compose_video(
                animation_assets=animations,
                audio_assets=audio,
                output_path=output_path,
            )
            
            if result.success:
                # Create chapters from scenes
                chapters = self._create_chapters(animations.scenes, audio.scenes)
                
                # Create video asset
                video_asset = VideoAsset(
                    file_path=result.output_path,
                    duration=result.duration,
                    resolution=result.resolution,
                    file_size=result.file_size,
                    chapters=chapters,
                )
                
                # Update state
                state["video"] = video_asset.dict()
                state["current_agent"] = "MetadataAgent"
                
                self.log_progress("Video composition completed successfully", state)
            else:
                raise RuntimeError(f"Video composition failed: {result.error_message}")
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state."""
        if "animations" not in state:
            raise ValueError("Animation assets not found in state")
        
        if "audio" not in state:
            raise ValueError("Audio assets not found in state")
    
    def _create_chapters(self, video_scenes, audio_scenes) -> list:
        """Create video chapters from scenes."""
        chapters = []
        current_time = 0.0
        
        for i, video_scene in enumerate(video_scenes):
            # Find matching audio scene for duration
            audio_scene = next(
                (a for a in audio_scenes if a.scene_id == video_scene.scene_id),
                None
            )
            
            duration = audio_scene.duration if audio_scene else video_scene.duration
            
            chapter = Chapter(
                title=f"Scene {i+1}",
                start_time=current_time,
                end_time=current_time + duration,
            )
            
            chapters.append(chapter)
            current_time += duration
        
        return chapters