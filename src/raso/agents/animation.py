"""
Animation Agent for the RASO platform.

Handles animation generation using simple, reliable methods without complex
AI dependencies. Uses SimpleAnimationGenerator for FFmpeg-based animations.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from agents.base import BaseAgent
from backend.models import AgentType
from backend.models.state import RASOMasterState
from backend.models.script import NarrationScript, Scene
from backend.models.animation import AnimationAssets, RenderedScene
from agents.retry import retry


class AnimationAgent(BaseAgent):
    """Agent responsible for animation generation using simple, reliable methods."""
    
    name = "AnimationAgent"
    description = "Generates animations using FFmpeg text overlays and simple visual content"
    
    def __init__(self, agent_type: AgentType):
        """Initialize animation agent with simple generation approach."""
        super().__init__(agent_type)
        
        # Animation configuration
        self.animation_config = {
            'resolution': '1920x1080',
            'fps': 30,
            'background_color': '#1a1a2e',
            'text_color': '#ffffff',
            'font_size': 48,
        }
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute animation generation using simple, reliable approach.
        
        Args:
            state: Current workflow state with script
            
        Returns:
            Updated state with animation assets
        """
        self.validate_input(state)
        
        try:
            script = state.script
            
            self.log_progress("Starting simple animation generation", state)
            self.logger.info(f"Script has {len(script.scenes)} scenes")
            
            # Use simple animation generator as primary method
            from agents.simple_animation_generator import SimpleAnimationGenerator
            simple_generator = SimpleAnimationGenerator()
            
            self.logger.info("Generating animations using simple, reliable method")
            self.logger.info(f"Animation capabilities: {simple_generator.get_capabilities()}")
            
            # Generate animation assets
            animation_assets = await simple_generator.generate_animation_assets(
                script=script,
                output_dir=self.config.temp_path
            )
            
            # Validate generated animations
            validation_results = []
            for scene in animation_assets.scenes:
                validation = simple_generator.validate_animation_file(scene.file_path)
                validation_results.append(validation)
                
                if not validation["valid"]:
                    self.logger.warning(f"Animation validation failed for scene {scene.scene_id}: {validation['errors']}")
                elif validation["warnings"]:
                    self.logger.info(f"Animation validation warnings for scene {scene.scene_id}: {validation['warnings']}")
            
            # Update state
            state.animations = animation_assets
            
            self.logger.info(f"Animation generation completed: {len(animation_assets.scenes)} scenes, {animation_assets.total_duration:.1f}s total")
            self.log_progress(f"Completed animation generation for {len(animation_assets.scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Simple animation generation failed: {e}")
            # Fallback to creating placeholder animations
            return await self._generate_fallback_animations(state)
    
    async def _generate_fallback_animations(self, state: RASOMasterState) -> RASOMasterState:
        """Generate fallback animations when simple generation fails."""
        try:
            script = state.script
            
            self.logger.info("Generating fallback placeholder animations")
            
            # Create basic animation assets with placeholders
            from backend.models.animation import AnimationAssets, RenderedScene, VideoResolution, RenderStatus
            
            rendered_scenes = []
            
            for scene in script.scenes:
                # Create a basic rendered scene entry (placeholder)
                rendered_scene = RenderedScene(
                    scene_id=scene.id,
                    file_path="",  # No actual file for placeholder
                    duration=scene.duration,
                    framework="fallback",
                    resolution=VideoResolution.from_string(self.animation_config['resolution']),
                    frame_rate=self.animation_config['fps'],
                    status=RenderStatus.FAILED
                )
                rendered_scenes.append(rendered_scene)
            
            # Create animation assets
            total_duration = sum(scene.duration for scene in rendered_scenes)
            
            animation_assets = AnimationAssets(
                scenes=rendered_scenes,
                total_duration=total_duration,
                resolution=VideoResolution.from_string(self.animation_config['resolution'])
            )
            
            state.animations = animation_assets
            
            self.logger.warning(f"Generated fallback animations: {len(rendered_scenes)} placeholder scenes")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Fallback animation generation failed: {e}")
            raise
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state for animation generation."""
        if not state.script:
            raise ValueError("Narration script not found in state")
        
        if not state.script.scenes:
            raise ValueError("No scenes found in narration script")
        
        self.logger.info(f"Animation input validation passed - {len(state.script.scenes)} scenes to animate")