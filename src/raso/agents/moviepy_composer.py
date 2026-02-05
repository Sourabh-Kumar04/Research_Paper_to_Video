"""
MoviePy-based video composer for high-quality video composition.
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

try:
    from moviepy.editor import (
        VideoFileClip, AudioFileClip, ImageClip, TextClip, 
        CompositeVideoClip, concatenate_videoclips, ColorClip
    )
    MOVIEPY_AVAILABLE = True
except ImportError:
    MOVIEPY_AVAILABLE = False
    logger.warning("MoviePy not available - high-quality composition disabled")


class MoviePyComposer:
    """High-quality video composition using MoviePy."""
    
    def __init__(self):
        """Initialize MoviePy composer."""
        if not MOVIEPY_AVAILABLE:
            raise ImportError("MoviePy is required for MoviePyComposer")
        
        self.default_resolution = (1280, 720)
        self.default_fps = 30
        self.default_bg_color = (26, 26, 46)  # Dark blue background
    
    def compose_video(self, scenes, output_path: str):
        """Compose video from scene data using MoviePy."""
        from agents.python_video_composer import VideoCompositionResult
        
        logger.info(f"Starting MoviePy composition for {len(scenes)} scenes")
        
        try:
            # Process each scene
            video_clips = []
            total_duration = 0
            
            for i, scene in enumerate(scenes):
                logger.info(f"Processing scene {i+1}/{len(scenes)}: {scene.scene_id}")
                
                try:
                    clip = self._create_scene_clip(scene)
                    if clip:
                        video_clips.append(clip)
                        total_duration += clip.duration
                        logger.info(f"Scene {scene.scene_id} processed: {clip.duration:.1f}s")
                    else:
                        logger.warning(f"Failed to create clip for scene {scene.scene_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing scene {scene.scene_id}: {e}")
                    # Create fallback clip for this scene
                    fallback_clip = self._create_fallback_scene_clip(scene)
                    if fallback_clip:
                        video_clips.append(fallback_clip)
                        total_duration += fallback_clip.duration
            
            if not video_clips:
                return VideoCompositionResult(
                    output_path=output_path,
                    success=False,
                    file_size=0,
                    duration=0.0,
                    resolution=(0, 0),
                    method_used="moviepy",
                    errors=["No video clips could be created"],
                    warnings=[]
                )
            
            # Concatenate all clips
            logger.info(f"Concatenating {len(video_clips)} clips")
            final_video = concatenate_videoclips(video_clips, method="compose")
            
            # Write final video
            logger.info(f"Writing final video to {output_path}")
            final_video.write_videofile(
                output_path,
                fps=self.default_fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None  # Suppress MoviePy logging
            )
            
            # Clean up clips
            for clip in video_clips:
                clip.close()
            final_video.close()
            
            # Get result info
            output_file = Path(output_path)
            file_size = output_file.stat().st_size if output_file.exists() else 0
            
            return VideoCompositionResult(
                output_path=output_path,
                success=True,
                file_size=file_size,
                duration=total_duration,
                resolution=self.default_resolution,
                method_used="moviepy",
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            logger.error(f"MoviePy composition failed: {e}")
            return VideoCompositionResult(
                output_path=output_path,
                success=False,
                file_size=0,
                duration=0.0,
                resolution=(0, 0),
                method_used="moviepy",
                errors=[f"MoviePy composition error: {str(e)}"],
                warnings=[]
            )
    
    def _create_scene_clip(self, scene):
        """Create a video clip for a single scene."""
        try:
            # Load animation video
            animation_path = Path(scene.animation_path)
            audio_path = Path(scene.audio_path)
            
            if not animation_path.exists():
                logger.warning(f"Animation file not found: {animation_path}")
                return self._create_fallback_scene_clip(scene)
            
            # Try to load animation as video
            try:
                video_clip = VideoFileClip(str(animation_path))
                logger.info(f"Loaded animation video: {video_clip.duration:.1f}s, {video_clip.size}")
            except Exception as e:
                logger.warning(f"Could not load animation as video: {e}")
                return self._create_fallback_scene_clip(scene)
            
            # Load audio
            audio_clip = None
            if audio_path.exists():
                try:
                    audio_clip = AudioFileClip(str(audio_path))
                    logger.info(f"Loaded audio: {audio_clip.duration:.1f}s")
                except Exception as e:
                    logger.warning(f"Could not load audio: {e}")
            
            # Synchronize audio and video
            if audio_clip:
                # Use audio duration as reference
                target_duration = audio_clip.duration
                
                if video_clip.duration < target_duration:
                    # Loop video to match audio duration
                    video_clip = video_clip.loop(duration=target_duration)
                elif video_clip.duration > target_duration:
                    # Trim video to match audio duration
                    video_clip = video_clip.subclip(0, target_duration)
                
                # Set audio
                video_clip = video_clip.set_audio(audio_clip)
            else:
                # Use scene duration if no audio
                if hasattr(scene, 'duration') and scene.duration > 0:
                    if video_clip.duration != scene.duration:
                        video_clip = video_clip.loop(duration=scene.duration)
            
            # Resize to standard resolution if needed
            if video_clip.size != self.default_resolution:
                video_clip = video_clip.resize(self.default_resolution)
            
            return video_clip
            
        except Exception as e:
            logger.error(f"Error creating scene clip: {e}")
            return self._create_fallback_scene_clip(scene)
    
    def _create_fallback_scene_clip(self, scene):
        """Create fallback clip when animation loading fails."""
        try:
            # Create text clip with scene title
            title_text = scene.title if hasattr(scene, 'title') else scene.scene_id
            duration = scene.duration if hasattr(scene, 'duration') and scene.duration > 0 else 5.0
            
            # Create background
            background = ColorClip(
                size=self.default_resolution,
                color=self.default_bg_color,
                duration=duration
            )
            
            # Create title text
            try:
                title_clip = TextClip(
                    title_text,
                    fontsize=72,
                    color='white',
                    font='Arial-Bold'
                ).set_position('center').set_duration(duration)
                
                # Composite background and text
                video_clip = CompositeVideoClip([background, title_clip])
                
            except Exception as e:
                logger.warning(f"Could not create text clip: {e}")
                # Use just background if text fails
                video_clip = background
            
            # Add audio if available
            audio_path = Path(scene.audio_path)
            if audio_path.exists():
                try:
                    audio_clip = AudioFileClip(str(audio_path))
                    # Adjust video duration to match audio
                    if audio_clip.duration != duration:
                        video_clip = video_clip.set_duration(audio_clip.duration)
                    video_clip = video_clip.set_audio(audio_clip)
                except Exception as e:
                    logger.warning(f"Could not add audio to fallback clip: {e}")
            
            logger.info(f"Created fallback clip for {scene.scene_id}: {video_clip.duration:.1f}s")
            return video_clip
            
        except Exception as e:
            logger.error(f"Failed to create fallback clip: {e}")
            return None
    
    def get_capabilities(self):
        """Get MoviePy composer capabilities."""
        return {
            "available": MOVIEPY_AVAILABLE,
            "can_compose_video": MOVIEPY_AVAILABLE,
            "can_sync_audio_video": MOVIEPY_AVAILABLE,
            "can_concatenate_scenes": MOVIEPY_AVAILABLE,
            "supports_effects": MOVIEPY_AVAILABLE,
            "output_formats": ["mp4", "avi", "mov"] if MOVIEPY_AVAILABLE else []
        }