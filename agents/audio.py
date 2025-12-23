"""
Audio Agent for the RASO platform.

Handles TTS generation, audio synchronization, and audio processing
for video narration using the TTS service.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from agents.base import BaseAgent
from backend.models.script import NarrationScript, Scene
from backend.models.animation import AnimationAssets, RenderedScene
from backend.models.audio import AudioAssets, AudioScene, TimingMarker
from audio.tts_service import tts_service, audio_synchronizer
from agents.retry import retry


class AudioAgent(BaseAgent):
    """Agent responsible for audio generation and synchronization."""
    
    name = "AudioAgent"
    description = "Generates TTS narration and synchronizes audio with visual content"
    
    def __init__(self):
        """Initialize audio agent."""
        super().__init__()
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute audio generation and synchronization.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with audio assets
        """
        self.validate_input(state)
        
        try:
            script = NarrationScript(**state["script"])
            animations = AnimationAssets(**state["animations"])
            
            self.log_progress("Starting audio generation", state)
            
            # Initialize TTS service
            await tts_service.initialize()
            
            # Generate audio for each scene
            audio_scenes = []
            
            for scene in script.scenes:
                # Find corresponding rendered scene for timing
                rendered_scene = self._find_rendered_scene(scene.id, animations.scenes)
                target_duration = rendered_scene.duration if rendered_scene else scene.duration
                
                # Generate TTS audio
                audio_result = await self._generate_scene_audio(scene, target_duration)
                
                if audio_result:
                    audio_scenes.append(audio_result)
                else:
                    self.logger.warning(f"Failed to generate audio for scene {scene.id}")
            
            # Normalize audio levels across all scenes
            if audio_scenes:
                audio_scenes = await self._normalize_audio_levels(audio_scenes)
            
            # Create audio assets
            total_duration = sum(scene.duration for scene in audio_scenes)
            
            audio_assets = AudioAssets(
                scenes=audio_scenes,
                total_duration=total_duration,
                sample_rate=self.config.audio.sample_rate,
            )
            
            # Update state
            state["audio"] = audio_assets.dict()
            state["current_agent"] = "VideoCompositionAgent"
            
            self.log_progress(f"Completed audio generation for {len(audio_scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state for audio generation."""
        if "script" not in state:
            raise ValueError("Narration script not found in state")
        
        if "animations" not in state:
            raise ValueError("Animation assets not found in state")
    
    def _find_rendered_scene(self, scene_id: str, rendered_scenes: List[RenderedScene]) -> Optional[RenderedScene]:
        """Find rendered scene by ID."""
        for rendered_scene in rendered_scenes:
            if rendered_scene.scene_id == scene_id:
                return rendered_scene
        return None
    
    async def _generate_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """Generate audio for a single scene."""
        try:
            # Create output path
            audio_dir = Path(self.config.temp_path) / "audio" / scene.id
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            raw_audio_path = str(audio_dir / f"{scene.id}_raw.wav")
            final_audio_path = str(audio_dir / f"{scene.id}.wav")
            
            # Generate TTS
            tts_result = await tts_service.generate_speech(
                text=scene.narration,
                output_path=raw_audio_path,
                voice_speed=self.config.audio.voice_speed,
                voice_pitch=self.config.audio.voice_pitch,
            )
            
            if not tts_result.success:
                self.logger.error(f"TTS generation failed for scene {scene.id}: {tts_result.error_message}")
                return None
            
            # Synchronize with target duration
            sync_result = await audio_synchronizer.synchronize_scene_audio(
                audio_path=raw_audio_path,
                target_duration=target_duration,
                output_path=final_audio_path,
            )
            
            if not sync_result.success:
                self.logger.error(f"Audio synchronization failed for scene {scene.id}: {sync_result.error_message}")
                return None
            
            # Create timing markers (simple word-level timing)
            timing_markers = self._create_timing_markers(scene.narration, sync_result.duration)
            
            # Create audio scene
            audio_scene = AudioScene(
                scene_id=scene.id,
                file_path=final_audio_path,
                duration=sync_result.duration,
                transcript=scene.narration,
                timing_markers=timing_markers,
            )
            
            return audio_scene
            
        except Exception as e:
            self.logger.error(f"Error generating audio for scene {scene.id}: {str(e)}")
            return None
    
    def _create_timing_markers(self, text: str, total_duration: float) -> List[TimingMarker]:
        """Create simple timing markers for text."""
        words = text.split()
        if not words:
            return []
        
        markers = []
        time_per_word = total_duration / len(words)
        
        current_time = 0.0
        for i, word in enumerate(words):
            markers.append(TimingMarker(
                word=word,
                start_time=current_time,
                end_time=current_time + time_per_word,
                confidence=0.8,  # Default confidence
            ))
            current_time += time_per_word
        
        return markers
    
    async def _normalize_audio_levels(self, audio_scenes: List[AudioScene]) -> List[AudioScene]:
        """Normalize audio levels across scenes."""
        try:
            # Extract audio file paths
            audio_paths = [scene.file_path for scene in audio_scenes]
            
            # Create normalized output directory
            normalized_dir = Path(self.config.temp_path) / "audio" / "normalized"
            
            # Normalize audio levels
            normalized_results = await audio_synchronizer.normalize_audio_levels(
                audio_paths=audio_paths,
                output_dir=str(normalized_dir),
            )
            
            # Update audio scenes with normalized paths
            updated_scenes = []
            for i, (scene, result) in enumerate(zip(audio_scenes, normalized_results)):
                if result.success:
                    # Update scene with normalized audio path
                    updated_scene = AudioScene(
                        scene_id=scene.scene_id,
                        file_path=result.output_path,
                        duration=result.duration,
                        transcript=scene.transcript,
                        timing_markers=scene.timing_markers,
                    )
                    updated_scenes.append(updated_scene)
                else:
                    # Keep original if normalization failed
                    self.logger.warning(f"Audio normalization failed for scene {scene.scene_id}")
                    updated_scenes.append(scene)
            
            return updated_scenes
            
        except Exception as e:
            self.logger.warning(f"Audio normalization error: {str(e)}")
            return audio_scenes  # Return original scenes if normalization fails
    
    async def generate_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """
        Public method to generate audio for a single scene.
        
        Args:
            scene: Scene to generate audio for
            target_duration: Target audio duration
            
        Returns:
            Audio scene if successful
        """
        return await self._generate_scene_audio(scene, target_duration)
    
    async def estimate_audio_duration(self, text: str) -> float:
        """
        Estimate audio duration for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated duration in seconds
        """
        return await tts_service.estimate_speech_duration(text)