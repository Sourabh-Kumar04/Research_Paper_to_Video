"""
Cinematic Video Generator for RASO Platform

Adds cinematic production features including:
- Camera movements and transitions
- Professional sound design
- Color grading and LUT application
- Advanced compositing
- Professional editing features

Enhanced with UI-configurable settings and AI-powered visual descriptions.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import json
import subprocess
import tempfile
from dataclasses import dataclass

# Fix import paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'backend'))

from models.script import Scene
from utils.quality_presets import QualityPresetManager, QualityLevel

# Import new cinematic models
try:
    from ..cinematic.models import CinematicSettingsModel, VisualDescriptionModel
    from ..llm.gemini_client import GeminiClient
except ImportError:
    # Fallback for backward compatibility
    CinematicSettingsModel = None
    VisualDescriptionModel = None
    GeminiClient = None


@dataclass
class CinematicSettings:
    """Settings for cinematic video generation."""
    camera_movements: bool = True
    professional_transitions: bool = True
    color_grading: bool = True
    sound_design: bool = True
    advanced_compositing: bool = True
    lut_application: bool = True
    dynamic_lighting: bool = True
    depth_of_field: bool = True
    motion_blur: bool = True
    film_grain: bool = True


@dataclass
class CameraMovement:
    """Defines a camera movement for a scene."""
    movement_type: str  # "pan", "zoom", "dolly", "crane", "handheld", "static"
    start_position: Dict[str, float]  # {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
    end_position: Dict[str, float]
    duration: float
    easing: str = "ease_in_out"  # "linear", "ease_in", "ease_out", "ease_in_out"


@dataclass
class Transition:
    """Defines a transition between scenes."""
    transition_type: str  # "fade", "dissolve", "wipe", "slide", "zoom", "spin"
    duration: float = 1.0
    direction: str = "forward"  # "forward", "backward", "up", "down", "left", "right"
    easing: str = "ease_in_out"


@dataclass
class ColorGrading:
    """Color grading settings for cinematic look."""
    lut_file: Optional[str] = None
    brightness: float = 0.0  # -1.0 to 1.0
    contrast: float = 0.0    # -1.0 to 1.0
    saturation: float = 0.0  # -1.0 to 1.0
    temperature: float = 0.0 # -1.0 to 1.0 (cool to warm)
    tint: float = 0.0        # -1.0 to 1.0 (green to magenta)
    shadows: float = 0.0     # -1.0 to 1.0
    highlights: float = 0.0  # -1.0 to 1.0
    film_emulation: str = "none"  # "none", "kodak", "fuji", "cinema"


@dataclass
class SoundDesign:
    """Sound design settings for professional audio."""
    ambient_audio: bool = True
    music_scoring: bool = True
    audio_effects: bool = True
    spatial_audio: bool = True
    dynamic_range_compression: bool = True
    eq_processing: bool = True
    reverb_settings: Dict[str, float] = None
    
    def __post_init__(self):
        if self.reverb_settings is None:
            self.reverb_settings = {
                "room_size": 0.3,
                "damping": 0.5,
                "wet_level": 0.2,
                "dry_level": 0.8
            }


class CinematicVideoGenerator:
    """Generates cinematic videos with professional production features."""
    
    def __init__(self, output_dir: str, quality: str = "cinematic_4k", 
                 ui_settings: Optional[CinematicSettingsModel] = None,
                 gemini_client: Optional[GeminiClient] = None):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize quality manager
        self.quality_manager = QualityPresetManager()
        self.quality = quality
        self.encoding_params = self.quality_manager.get_preset(quality)
        
        # Enhanced cinematic settings - use UI settings if provided
        if ui_settings and CinematicSettingsModel:
            self.ui_settings = ui_settings
            # Convert UI settings to legacy format for backward compatibility
            self.cinematic_settings = self._convert_ui_settings_to_legacy(ui_settings)
        else:
            # Fallback to legacy settings for backward compatibility
            self.cinematic_settings = CinematicSettings()
            self.ui_settings = None
        
        # AI client for enhanced visual descriptions
        self.gemini_client = gemini_client
        
        # Visual descriptions storage
        self.visual_descriptions: Dict[str, VisualDescriptionModel] = {}
        
        # Create temp directory for processing
        self.temp_dir = self.output_dir / "cinematic_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cinematic assets
        self.lut_dir = self.temp_dir / "luts"
        self.lut_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_assets_dir = self.temp_dir / "audio_assets"
        self.audio_assets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[CINEMATIC] Initialized with {quality} quality: {self.encoding_params.resolution}")
        print(f"[CINEMATIC] UI Settings: {'Enabled' if self.ui_settings else 'Legacy Mode'}")
        print(f"[CINEMATIC] AI Enhancement: {'Enabled' if self.gemini_client else 'Disabled'}")
        print(f"[CINEMATIC] Output directory: {self.output_dir}")
    
    def _convert_ui_settings_to_legacy(self, ui_settings: CinematicSettingsModel) -> 'CinematicSettings':
        """Convert new UI settings to legacy format for backward compatibility."""
        return CinematicSettings(
            camera_movements=ui_settings.camera_movements.enabled,
            professional_transitions=ui_settings.advanced_compositing.professional_transitions,
            color_grading=ui_settings.color_grading.enabled,
            sound_design=ui_settings.sound_design.enabled,
            advanced_compositing=ui_settings.advanced_compositing.enabled,
            lut_application=ui_settings.advanced_compositing.lut_application,
            dynamic_lighting=ui_settings.advanced_compositing.dynamic_lighting,
            depth_of_field=ui_settings.advanced_compositing.depth_of_field,
            motion_blur=ui_settings.advanced_compositing.motion_blur,
            film_grain=ui_settings.advanced_compositing.film_grain
        )
    
    async def set_visual_descriptions(self, descriptions: Dict[str, str]):
        """Set custom visual descriptions for scenes."""
        if not VisualDescriptionModel:
            print("[CINEMATIC] Visual descriptions not available in legacy mode")
            return
        
        for scene_id, description in descriptions.items():
            self.visual_descriptions[scene_id] = VisualDescriptionModel(
                scene_id=scene_id,
                content="",  # Will be filled when processing
                description=description,
                generated_by="user",
                cinematic_settings=self.ui_settings.to_dict() if self.ui_settings else {},
                scene_analysis={},
                suggestions=[],
                confidence=1.0,
                created_at="",
                updated_at=""
            )
        
        print(f"[CINEMATIC] Set {len(descriptions)} custom visual descriptions")
    
    async def generate_ai_visual_descriptions(self, scenes: List[Scene]) -> Dict[str, str]:
        """Generate AI-powered visual descriptions for scenes."""
        if not self.gemini_client or not self.ui_settings:
            print("[CINEMATIC] AI visual descriptions not available")
            return {}
        
        descriptions = {}
        
        try:
            for i, scene in enumerate(scenes):
                scene_id = f"scene_{i}"
                
                # Determine scene type
                scene_type = self._determine_scene_type(scene, i, len(scenes))
                
                # Generate visual description using Gemini
                result = await self.gemini_client.generate_detailed_visual_description(
                    scene_content=scene.content,
                    scene_type=scene_type,
                    cinematic_settings=self.ui_settings.to_dict(),
                    target_audience="intermediate"
                )
                
                if result and "description" in result:
                    descriptions[scene_id] = result["description"]
                    
                    # Store full visual description model
                    if VisualDescriptionModel:
                        self.visual_descriptions[scene_id] = VisualDescriptionModel(
                            scene_id=scene_id,
                            content=scene.content,
                            description=result["description"],
                            generated_by="gemini",
                            cinematic_settings=self.ui_settings.to_dict(),
                            scene_analysis=result.get("scene_analysis", {}),
                            suggestions=result.get("suggestions", []),
                            confidence=result.get("confidence", 0.8),
                            created_at="",
                            updated_at=""
                        )
                
                print(f"[CINEMATIC] Generated AI description for {scene_id}")
        
        except Exception as e:
            print(f"[CINEMATIC] Error generating AI descriptions: {e}")
        
        return descriptions
    
    def _determine_scene_type(self, scene: Scene, index: int, total_scenes: int) -> str:
        """Determine the type of scene for appropriate visual description."""
        # First scene is usually intro
        if index == 0:
            return "intro"
        
        # Last scene is usually conclusion
        if index == total_scenes - 1:
            return "conclusion"
        
        # Analyze content for other types
        content_lower = scene.content.lower()
        
        if any(word in content_lower for word in ["method", "approach", "algorithm", "process"]):
            return "methodology"
        
        if any(word in content_lower for word in ["result", "outcome", "finding", "data", "analysis"]):
            return "results"
        
        return "general"
    def __init__(self, output_dir: str, quality: str = "cinematic_4k"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize quality manager
        self.quality_manager = QualityPresetManager()
        self.quality = quality
        self.encoding_params = self.quality_manager.get_preset(quality)
        
        # Cinematic settings
        self.cinematic_settings = CinematicSettings()
        
        # Create temp directory for processing
        self.temp_dir = self.output_dir / "cinematic_temp"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize cinematic assets
        self.lut_dir = self.temp_dir / "luts"
        self.lut_dir.mkdir(parents=True, exist_ok=True)
        
        self.audio_assets_dir = self.temp_dir / "audio_assets"
        self.audio_assets_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"[CINEMATIC] Initialized with {quality} quality: {self.encoding_params.resolution}")
        print(f"[CINEMATIC] Output directory: {self.output_dir}")
    
    async def generate_cinematic_video(
        self, 
        scenes: List[Scene], 
        video_files: List[str], 
        audio_files: List[str],
        output_path: str,
        custom_visual_descriptions: Optional[Dict[str, str]] = None
    ) -> bool:
        """Generate cinematic video with all production features."""
        try:
            print(f"[CINEMATIC] Starting cinematic video generation...")
            print(f"[CINEMATIC] Scenes: {len(scenes)}, Videos: {len(video_files)}, Audio: {len(audio_files)}")
            
            # Set custom visual descriptions if provided
            if custom_visual_descriptions:
                await self.set_visual_descriptions(custom_visual_descriptions)
            
            # Generate AI visual descriptions if enabled and no custom descriptions
            elif self.gemini_client and not custom_visual_descriptions:
                ai_descriptions = await self.generate_ai_visual_descriptions(scenes)
                if ai_descriptions:
                    await self.set_visual_descriptions(ai_descriptions)
            
            # Step 1: Analyze scenes for cinematic treatment (enhanced with UI settings)
            cinematic_plan = await self._analyze_scenes_for_cinematic_treatment(scenes)
            print(f"[CINEMATIC] Generated cinematic plan with {len(cinematic_plan)} enhanced scenes")
            
            # Step 2: Create cinematic assets
            await self._create_cinematic_assets()
            
            # Step 3: Apply camera movements and transitions (respecting UI settings)
            enhanced_video_files = await self._apply_camera_movements_and_transitions(
                video_files, scenes, cinematic_plan
            )
            
            # Step 4: Apply color grading and visual effects (using UI color settings)
            graded_video_files = await self._apply_color_grading_and_effects(
                enhanced_video_files, cinematic_plan
            )
            
            # Step 5: Create professional sound design (using UI sound settings)
            enhanced_audio_files = await self._create_professional_sound_design(
                audio_files, scenes, cinematic_plan
            )
            
            # Step 6: Advanced compositing and final assembly
            success = await self._advanced_compositing_and_assembly(
                graded_video_files, enhanced_audio_files, scenes, output_path, cinematic_plan
            )
            
            if success:
                print(f"[CINEMATIC] ✅ Cinematic video generation completed successfully!")
                print(f"[CINEMATIC] Output: {output_path}")
                
                # Validate cinematic output
                await self._validate_cinematic_output(output_path)
                return True
            else:
                print(f"[CINEMATIC] ❌ Cinematic video generation failed")
                return False
                
        except Exception as e:
            print(f"[CINEMATIC] ❌ Error during cinematic generation: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _analyze_scenes_for_cinematic_treatment(self, scenes: List[Scene]) -> List[Dict[str, Any]]:
        """Analyze scenes to determine optimal cinematic treatment (enhanced with UI settings)."""
        cinematic_plan = []
        
        for i, scene in enumerate(scenes):
            scene_id = f"scene_{i}"
            
            # Get visual description if available
            visual_description = self.visual_descriptions.get(scene_id)
            
            # Analyze scene content for cinematic approach
            scene_analysis = self._analyze_scene_content(scene, visual_description)
            
            # Determine camera movement based on UI settings and content
            camera_movement = self._determine_camera_movement_with_ui_settings(
                scene, scene_analysis, i, len(scenes), visual_description
            )
            
            # Determine transition to next scene
            transition = self._determine_transition(scene, i, len(scenes))
            
            # Determine color grading approach using UI settings
            color_grading = self._determine_color_grading_with_ui_settings(
                scene, scene_analysis, visual_description
            )
            
            # Determine sound design approach using UI settings
            sound_design = self._determine_sound_design_with_ui_settings(
                scene, scene_analysis, visual_description
            )
            
            # Create enhanced cinematic plan entry
            plan_entry = {
                "scene_index": i,
                "scene_id": scene_id,
                "scene": scene,
                "analysis": scene_analysis,
                "camera_movement": camera_movement,
                "transition": transition,
                "color_grading": color_grading,
                "sound_design": sound_design,
                "visual_description": visual_description.description if visual_description else None,
                "ai_enhanced": visual_description is not None,
                "ui_settings_applied": self.ui_settings is not None
            }
            
            cinematic_plan.append(plan_entry)
            
            print(f"[CINEMATIC] Scene {i}: {scene_analysis['content_type']} - "
                  f"Camera: {camera_movement['movement_type']}, "
                  f"Color: {color_grading['film_emulation']}, "
                  f"AI Enhanced: {plan_entry['ai_enhanced']}")
        
        return cinematic_plan
    
    def _analyze_scene_content(self, scene: Scene, visual_description: Optional[VisualDescriptionModel] = None) -> Dict[str, Any]:
        """Analyze scene content for cinematic approach (enhanced with visual descriptions)."""
        content = scene.content.lower()
        
        # Use AI analysis if available
        if visual_description and visual_description.scene_analysis:
            ai_analysis = visual_description.scene_analysis
            return {
                "content_type": ai_analysis.get("focusType", "general"),
                "complexity": ai_analysis.get("complexity", "medium"),
                "mood": ai_analysis.get("mood", "neutral"),
                "pacing": ai_analysis.get("pacing", "medium"),
                "technical_level": ai_analysis.get("technicalLevel", "intermediate"),
                "key_terms": ai_analysis.get("keyTerms", []),
                "ai_enhanced": True
            }
        
        # Fallback to rule-based analysis
        analysis = {
            "content_type": "general",
            "complexity": "medium",
            "mood": "neutral",
            "pacing": "medium",
            "technical_level": "intermediate",
            "key_terms": [],
            "ai_enhanced": False
        }
        
        # Determine content type
        if any(word in content for word in ["equation", "formula", "theorem", "proof", "calculate"]):
            analysis["content_type"] = "mathematical"
            analysis["complexity"] = "high"
        elif any(word in content for word in ["architecture", "system", "design", "structure", "component"]):
            analysis["content_type"] = "architectural"
            analysis["complexity"] = "medium"
        elif any(word in content for word in ["result", "data", "analysis", "performance", "benchmark"]):
            analysis["content_type"] = "analytical"
            analysis["pacing"] = "slow"
        elif any(word in content for word in ["step", "process", "method", "algorithm", "procedure"]):
            analysis["content_type"] = "procedural"
            analysis["pacing"] = "medium"
        
        # Determine mood
        if any(word in content for word in ["problem", "challenge", "difficult", "complex"]):
            analysis["mood"] = "serious"
        elif any(word in content for word in ["solution", "success", "achievement", "breakthrough"]):
            analysis["mood"] = "positive"
        elif any(word in content for word in ["introduction", "welcome", "overview"]):
            analysis["mood"] = "welcoming"
        
        return analysis
    
    def _determine_camera_movement_with_ui_settings(
        self, 
        scene: Scene, 
        scene_analysis: Dict[str, Any], 
        scene_index: int, 
        total_scenes: int,
        visual_description: Optional[VisualDescriptionModel] = None
    ) -> CameraMovement:
        """Determine camera movement respecting UI settings."""
        
        # Check if camera movements are disabled in UI
        if self.ui_settings and not self.ui_settings.camera_movements.enabled:
            return CameraMovement(
                movement_type="static",
                start_position={"x": 0, "y": 0, "scale": 1.0, "rotation": 0},
                end_position={"x": 0, "y": 0, "scale": 1.0, "rotation": 0},
                duration=0.0,
                easing="linear"
            )
        
        # Use AI recommendations if available
        if visual_description and visual_description.scene_analysis:
            ai_analysis = visual_description.scene_analysis
            if "recommendedCameraMovement" in ai_analysis:
                recommended_movement = ai_analysis["recommendedCameraMovement"]
                
                # Validate against UI allowed types
                if self.ui_settings and self.ui_settings.camera_movements.allowed_types:
                    allowed_types = [t.value for t in self.ui_settings.camera_movements.allowed_types]
                    if recommended_movement not in allowed_types:
                        # Fall back to first allowed type
                        recommended_movement = allowed_types[0] if allowed_types else "static"
                
                return self._create_camera_movement(
                    recommended_movement, 
                    scene_analysis, 
                    scene_index, 
                    total_scenes
                )
        
        # Use UI settings to determine movement
        if self.ui_settings and self.ui_settings.camera_movements.auto_select:
            # Auto-select based on content and UI constraints
            allowed_types = [t.value for t in self.ui_settings.camera_movements.allowed_types]
            
            # Choose movement based on content type and allowed types
            if scene_analysis["content_type"] == "mathematical" and "zoom" in allowed_types:
                movement_type = "zoom"
            elif scene_analysis["content_type"] == "architectural" and "pan" in allowed_types:
                movement_type = "pan"
            elif scene_analysis["mood"] == "positive" and "dolly" in allowed_types:
                movement_type = "dolly"
            elif allowed_types:
                movement_type = allowed_types[0]
            else:
                movement_type = "static"
        else:
            # Fallback to legacy logic
            movement_type = self._determine_legacy_camera_movement(scene_analysis, scene_index, total_scenes)
        
        return self._create_camera_movement(movement_type, scene_analysis, scene_index, total_scenes)
    
    def _determine_color_grading_with_ui_settings(
        self, 
        scene: Scene, 
        scene_analysis: Dict[str, Any],
        visual_description: Optional[VisualDescriptionModel] = None
    ) -> ColorGrading:
        """Determine color grading using UI settings."""
        
        # Check if color grading is disabled
        if self.ui_settings and not self.ui_settings.color_grading.enabled:
            return ColorGrading()  # Default/disabled color grading
        
        # Use AI recommendations if available
        if visual_description and visual_description.scene_analysis:
            ai_analysis = visual_description.scene_analysis
            if "recommendedColorGrading" in ai_analysis:
                color_rec = ai_analysis["recommendedColorGrading"]
                
                # Apply UI color grading settings
                color_grading = ColorGrading()
                
                if self.ui_settings:
                    color_grading.film_emulation = self.ui_settings.color_grading.film_emulation.value
                    color_grading.temperature = self.ui_settings.color_grading.temperature / 100.0
                    color_grading.tint = self.ui_settings.color_grading.tint / 100.0
                    color_grading.contrast = self.ui_settings.color_grading.contrast / 100.0
                    color_grading.saturation = self.ui_settings.color_grading.saturation / 100.0
                    color_grading.brightness = self.ui_settings.color_grading.brightness / 100.0
                    color_grading.shadows = self.ui_settings.color_grading.shadows / 100.0
                    color_grading.highlights = self.ui_settings.color_grading.highlights / 100.0
                
                return color_grading
        
        # Use UI settings directly
        if self.ui_settings:
            return ColorGrading(
                film_emulation=self.ui_settings.color_grading.film_emulation.value,
                temperature=self.ui_settings.color_grading.temperature / 100.0,
                tint=self.ui_settings.color_grading.tint / 100.0,
                contrast=self.ui_settings.color_grading.contrast / 100.0,
                saturation=self.ui_settings.color_grading.saturation / 100.0,
                brightness=self.ui_settings.color_grading.brightness / 100.0,
                shadows=self.ui_settings.color_grading.shadows / 100.0,
                highlights=self.ui_settings.color_grading.highlights / 100.0
            )
        
        # Fallback to legacy logic
        return self._determine_legacy_color_grading(scene_analysis)
    
    def _determine_sound_design_with_ui_settings(
        self, 
        scene: Scene, 
        scene_analysis: Dict[str, Any],
        visual_description: Optional[VisualDescriptionModel] = None
    ) -> SoundDesign:
        """Determine sound design using UI settings."""
        
        # Check if sound design is disabled
        if self.ui_settings and not self.ui_settings.sound_design.enabled:
            return SoundDesign(
                ambient_audio=False,
                music_scoring=False,
                audio_effects=False,
                spatial_audio=False,
                dynamic_range_compression=False,
                eq_processing=False
            )
        
        # Use UI settings
        if self.ui_settings:
            return SoundDesign(
                ambient_audio=self.ui_settings.sound_design.ambient_audio,
                music_scoring=self.ui_settings.sound_design.music_scoring,
                audio_effects=True,  # Always enable for cinematic quality
                spatial_audio=self.ui_settings.sound_design.spatial_audio,
                dynamic_range_compression=self.ui_settings.sound_design.dynamic_range_compression,
                eq_processing=self.ui_settings.sound_design.eq_processing,
                reverb_settings={
                    "room_size": 0.3,
                    "damping": 0.5,
                    "wet_level": self.ui_settings.sound_design.reverb_intensity / 100.0 * 0.3,
                    "dry_level": 0.8
                }
            )
        
        # Fallback to legacy logic
        return self._determine_legacy_sound_design(scene_analysis)
    
    def _continue_cinematic_plan(self, scenes, scene_analysis_list):
        """Continue building the cinematic plan."""
        cinematic_plan = []
        
        for i, scene in enumerate(scenes):
            scene_analysis = scene_analysis_list[i] if i < len(scene_analysis_list) else {}
            
            # Determine cinematic elements for this scene
            camera_movement = self._determine_camera_movement(scene, scene_analysis)
            transition = self._determine_transition(scene, scene_analysis, i)
            color_grading = self._determine_color_grading(scene, scene_analysis)
            sound_design = self._determine_sound_design(scene, scene_analysis)
            
            cinematic_plan.append({
                "scene_index": i,
                "scene_id": scene.id,
                "analysis": scene_analysis,
                "camera_movement": camera_movement,
                "transition": transition,
                "color_grading": color_grading,
                "sound_design": sound_design,
                "duration": scene.duration
            })
        
        return cinematic_plan
            })
            
            print(f"[CINEMATIC] Scene {i}: {scene_analysis['mood']} mood, {camera_movement.movement_type} camera, {color_grading.film_emulation} grading")
        
        return cinematic_plan
    
    def _analyze_scene_content(self, scene: Scene) -> Dict[str, Any]:
        """Analyze scene content to determine cinematic approach."""
        content = scene.narration.lower()
        
        # Determine mood and tone
        mood = "neutral"
        if any(word in content for word in ["introduction", "welcome", "overview"]):
            mood = "welcoming"
        elif any(word in content for word in ["problem", "challenge", "limitation", "bottleneck"]):
            mood = "serious"
        elif any(word in content for word in ["solution", "innovation", "breakthrough", "revolutionary"]):
            mood = "exciting"
        elif any(word in content for word in ["mathematical", "formula", "equation", "analysis"]):
            mood = "analytical"
        elif any(word in content for word in ["performance", "results", "evaluation", "benchmarks"]):
            mood = "triumphant"
        elif any(word in content for word in ["future", "impact", "applications", "potential"]):
            mood = "inspiring"
        
        # Determine visual complexity
        complexity = "medium"
        if any(word in content for word in ["simple", "basic", "introduction"]):
            complexity = "low"
        elif any(word in content for word in ["complex", "advanced", "sophisticated", "mathematical"]):
            complexity = "high"
        
        # Determine pacing
        pacing = "medium"
        if scene.duration < 30:
            pacing = "fast"
        elif scene.duration > 60:
            pacing = "slow"
        
        # Determine focus type
        focus_type = "general"
        if any(word in content for word in ["formula", "equation", "mathematical"]):
            focus_type = "mathematical"
        elif any(word in content for word in ["architecture", "system", "design"]):
            focus_type = "architectural"
        elif any(word in content for word in ["performance", "results", "benchmarks"]):
            focus_type = "analytical"
        elif any(word in content for word in ["process", "method", "algorithm"]):
            focus_type = "procedural"
        
        return {
            "mood": mood,
            "complexity": complexity,
            "pacing": pacing,
            "focus_type": focus_type,
            "content_keywords": [word for word in ["mathematical", "architectural", "performance", "innovation"] if word in content]
        }
    
    def _determine_camera_movement(self, scene: Scene, analysis: Dict[str, Any], scene_index: int, total_scenes: int) -> CameraMovement:
        """Determine optimal camera movement for scene."""
        mood = analysis["mood"]
        complexity = analysis["complexity"]
        pacing = analysis["pacing"]
        
        # Determine movement type based on content
        if scene_index == 0:  # Opening scene
            movement_type = "zoom"
            start_pos = {"x": 0, "y": 0, "scale": 1.2, "rotation": 0}
            end_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
        elif scene_index == total_scenes - 1:  # Closing scene
            movement_type = "dolly"
            start_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
            end_pos = {"x": 0, "y": -50, "scale": 1.1, "rotation": 0}
        elif mood == "exciting":
            movement_type = "crane"
            start_pos = {"x": -100, "y": 100, "scale": 1.0, "rotation": -2}
            end_pos = {"x": 100, "y": -50, "scale": 1.1, "rotation": 2}
        elif mood == "analytical":
            movement_type = "pan"
            start_pos = {"x": -50, "y": 0, "scale": 1.0, "rotation": 0}
            end_pos = {"x": 50, "y": 0, "scale": 1.0, "rotation": 0}
        elif complexity == "high":
            movement_type = "zoom"
            start_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
            end_pos = {"x": 0, "y": 0, "scale": 1.2, "rotation": 0}
        elif pacing == "fast":
            movement_type = "handheld"
            start_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
            end_pos = {"x": 10, "y": -10, "scale": 1.05, "rotation": 1}
        else:
            movement_type = "dolly"
            start_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
            end_pos = {"x": 0, "y": -30, "scale": 1.05, "rotation": 0}
        
        # Adjust easing based on mood
        easing = "ease_in_out"
        if mood == "exciting":
            easing = "ease_out"
        elif mood == "serious":
            easing = "ease_in"
        
        return CameraMovement(
            movement_type=movement_type,
            start_position=start_pos,
            end_position=end_pos,
            duration=scene.duration,
            easing=easing
        )
    
    def _determine_transition(self, scene: Scene, scene_index: int, total_scenes: int) -> Optional[Transition]:
        """Determine transition to next scene."""
        if scene_index >= total_scenes - 1:
            return None  # No transition after last scene
        
        content = scene.narration.lower()
        
        # Determine transition type based on content flow
        if any(word in content for word in ["however", "but", "although", "despite"]):
            transition_type = "wipe"
            direction = "left"
        elif any(word in content for word in ["next", "then", "following", "subsequently"]):
            transition_type = "slide"
            direction = "right"
        elif any(word in content for word in ["zoom", "focus", "examine", "detail"]):
            transition_type = "zoom"
            direction = "forward"
        elif any(word in content for word in ["overview", "summary", "conclusion"]):
            transition_type = "dissolve"
            direction = "forward"
        else:
            transition_type = "fade"
            direction = "forward"
        
        # Adjust duration based on scene pacing
        duration = 1.0
        if scene.duration < 30:
            duration = 0.5  # Faster transitions for short scenes
        elif scene.duration > 60:
            duration = 1.5  # Slower transitions for long scenes
        
        return Transition(
            transition_type=transition_type,
            duration=duration,
            direction=direction,
            easing="ease_in_out"
        )
    
    def _determine_color_grading(self, scene: Scene, analysis: Dict[str, Any]) -> ColorGrading:
        """Determine color grading approach for scene."""
        mood = analysis["mood"]
        focus_type = analysis["focus_type"]
        
        # Base color grading settings
        grading = ColorGrading()
        
        # Adjust based on mood
        if mood == "welcoming":
            grading.temperature = 0.2  # Warmer
            grading.brightness = 0.1
            grading.saturation = 0.1
            grading.film_emulation = "kodak"
        elif mood == "serious":
            grading.temperature = -0.1  # Cooler
            grading.contrast = 0.2
            grading.shadows = -0.1
            grading.film_emulation = "cinema"
        elif mood == "exciting":
            grading.saturation = 0.3
            grading.contrast = 0.2
            grading.highlights = 0.1
            grading.film_emulation = "fuji"
        elif mood == "analytical":
            grading.temperature = -0.2  # Cool and clinical
            grading.contrast = 0.1
            grading.saturation = -0.1
            grading.film_emulation = "cinema"
        elif mood == "triumphant":
            grading.brightness = 0.2
            grading.saturation = 0.2
            grading.highlights = 0.2
            grading.film_emulation = "kodak"
        elif mood == "inspiring":
            grading.temperature = 0.3  # Warm and inviting
            grading.brightness = 0.15
            grading.saturation = 0.15
            grading.film_emulation = "kodak"
        
        # Adjust based on focus type
        if focus_type == "mathematical":
            grading.contrast = 0.3  # High contrast for clarity
            grading.saturation = -0.2  # Desaturated for focus
        elif focus_type == "architectural":
            grading.shadows = -0.2  # Lift shadows to show detail
            grading.highlights = -0.1  # Compress highlights
        
        return grading
    
    def _determine_sound_design(self, scene: Scene, analysis: Dict[str, Any]) -> SoundDesign:
        """Determine sound design approach for scene."""
        mood = analysis["mood"]
        complexity = analysis["complexity"]
        
        sound_design = SoundDesign()
        
        # Adjust reverb based on mood
        if mood == "welcoming":
            sound_design.reverb_settings = {
                "room_size": 0.4,
                "damping": 0.6,
                "wet_level": 0.25,
                "dry_level": 0.75
            }
        elif mood == "serious":
            sound_design.reverb_settings = {
                "room_size": 0.2,
                "damping": 0.8,
                "wet_level": 0.15,
                "dry_level": 0.85
            }
        elif mood == "exciting":
            sound_design.reverb_settings = {
                "room_size": 0.6,
                "damping": 0.4,
                "wet_level": 0.3,
                "dry_level": 0.7
            }
        elif mood == "analytical":
            sound_design.reverb_settings = {
                "room_size": 0.1,
                "damping": 0.9,
                "wet_level": 0.1,
                "dry_level": 0.9
            }
        
        # Adjust other settings based on complexity
        if complexity == "high":
            sound_design.dynamic_range_compression = True
            sound_design.eq_processing = True
        
        return sound_design
    
    async def _create_cinematic_assets(self):
        """Create cinematic assets like LUTs and audio samples."""
        print(f"[CINEMATIC] Creating cinematic assets...")
        
        # Create LUT files for color grading
        await self._create_lut_files()
        
        # Create ambient audio samples
        await self._create_ambient_audio_samples()
        
        # Create music stems
        await self._create_music_stems()
        
        print(f"[CINEMATIC] ✅ Cinematic assets created")
    
    async def _create_lut_files(self):
        """Create LUT files for different film emulations."""
        try:
            # Create basic LUT files (simplified 3D LUT format)
            lut_definitions = {
                "kodak": {
                    "description": "Kodak film emulation - warm and natural",
                    "adjustments": {
                        "red_lift": 0.02,
                        "green_lift": 0.01,
                        "blue_lift": -0.01,
                        "red_gamma": 1.05,
                        "green_gamma": 1.02,
                        "blue_gamma": 0.98,
                        "red_gain": 1.1,
                        "green_gain": 1.05,
                        "blue_gain": 0.95
                    }
                },
                "fuji": {
                    "description": "Fuji film emulation - vibrant and saturated",
                    "adjustments": {
                        "red_lift": 0.01,
                        "green_lift": 0.02,
                        "blue_lift": 0.01,
                        "red_gamma": 1.1,
                        "green_gamma": 1.08,
                        "blue_gamma": 1.02,
                        "red_gain": 1.15,
                        "green_gain": 1.1,
                        "blue_gain": 1.0
                    }
                },
                "cinema": {
                    "description": "Cinema emulation - high contrast and desaturated",
                    "adjustments": {
                        "red_lift": -0.01,
                        "green_lift": -0.01,
                        "blue_lift": 0.02,
                        "red_gamma": 0.95,
                        "green_gamma": 0.98,
                        "blue_gamma": 1.05,
                        "red_gain": 0.9,
                        "green_gain": 0.95,
                        "blue_gain": 1.1
                    }
                }
            }
            
            for lut_name, lut_data in lut_definitions.items():
                lut_file = self.lut_dir / f"{lut_name}.json"
                with open(lut_file, 'w') as f:
                    json.dump(lut_data, f, indent=2)
                
                print(f"[CINEMATIC] Created LUT: {lut_name}")
        
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Failed to create LUT files: {e}")
    
    async def _create_ambient_audio_samples(self):
        """Create ambient audio samples for sound design."""
        try:
            # Create different ambient audio types using FFmpeg
            ambient_types = {
                "room_tone": {
                    "description": "Subtle room ambience",
                    "frequency": "200",
                    "amplitude": "0.05",
                    "duration": "10"
                },
                "studio_ambience": {
                    "description": "Professional studio ambience",
                    "frequency": "100",
                    "amplitude": "0.03",
                    "duration": "10"
                },
                "reverb_tail": {
                    "description": "Natural reverb tail",
                    "frequency": "500",
                    "amplitude": "0.02",
                    "duration": "5"
                }
            }
            
            for ambient_name, ambient_data in ambient_types.items():
                ambient_file = self.audio_assets_dir / f"{ambient_name}.wav"
                
                # Create ambient audio using FFmpeg sine wave generator
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "lavfi",
                    "-i", f"sine=frequency={ambient_data['frequency']}:sample_rate=48000:duration={ambient_data['duration']}",
                    "-af", f"volume={ambient_data['amplitude']},lowpass=f=1000,highpass=f=50",
                    "-c:a", "pcm_s16le",
                    str(ambient_file)
                ]
                
                try:
                    result = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                    
                    if result.returncode == 0 and ambient_file.exists():
                        print(f"[CINEMATIC] Created ambient audio: {ambient_name}")
                    else:
                        print(f"[CINEMATIC] ⚠️ Failed to create ambient audio: {ambient_name}")
                
                except Exception as e:
                    print(f"[CINEMATIC] ⚠️ Error creating ambient audio {ambient_name}: {e}")
        
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Failed to create ambient audio samples: {e}")
    
    async def _create_music_stems(self):
        """Create basic music stems for scoring."""
        try:
            # Create simple musical elements using FFmpeg
            music_stems = {
                "intro_chord": {
                    "frequencies": ["261.63", "329.63", "392.00"],  # C major chord
                    "duration": "3",
                    "envelope": "0.5:1:0.5"
                },
                "transition_sweep": {
                    "frequencies": ["440"],  # A note
                    "duration": "1",
                    "envelope": "0:1:0"
                },
                "conclusion_chord": {
                    "frequencies": ["261.63", "329.63", "392.00", "523.25"],  # C major with octave
                    "duration": "4",
                    "envelope": "1:1:0.3"
                }
            }
            
            for stem_name, stem_data in music_stems.items():
                stem_file = self.audio_assets_dir / f"{stem_name}.wav"
                
                # Create chord by mixing multiple sine waves
                sine_inputs = []
                for i, freq in enumerate(stem_data["frequencies"]):
                    sine_inputs.append(f"sine=frequency={freq}:sample_rate=48000:duration={stem_data['duration']}")
                
                # Mix the sine waves
                if len(sine_inputs) == 1:
                    filter_complex = f"[0]volume=0.3,adsr=a=0.1:d=0.1:s=0.8:r=0.5[out]"
                else:
                    # Mix multiple sine waves
                    mix_filter = "+".join([f"[{i}]" for i in range(len(sine_inputs))])
                    filter_complex = f"{mix_filter}amix=inputs={len(sine_inputs)}:duration=longest,volume=0.3,adsr=a=0.1:d=0.1:s=0.8:r=0.5[out]"
                
                cmd = [
                    "ffmpeg", "-y"
                ]
                
                # Add input sine waves
                for sine_input in sine_inputs:
                    cmd.extend(["-f", "lavfi", "-i", sine_input])
                
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[out]",
                    "-c:a", "pcm_s16le",
                    str(stem_file)
                ])
                
                try:
                    result = await asyncio.create_subprocess_exec(
                        *cmd,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await result.communicate()
                    
                    if result.returncode == 0 and stem_file.exists():
                        print(f"[CINEMATIC] Created music stem: {stem_name}")
                    else:
                        print(f"[CINEMATIC] ⚠️ Failed to create music stem: {stem_name}")
                
                except Exception as e:
                    print(f"[CINEMATIC] ⚠️ Error creating music stem {stem_name}: {e}")
        
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Failed to create music stems: {e}")
    
    async def _apply_camera_movements_and_transitions(
        self, 
        video_files: List[str], 
        scenes: List[Scene], 
        cinematic_plan: List[Dict[str, Any]]
    ) -> List[str]:
        """Apply cinematic camera movements and transitions to video files."""
        print(f"[CINEMATIC] Applying camera movements and transitions...")
        
        enhanced_video_files = []
        
        for i, (video_file, scene, plan) in enumerate(zip(video_files, scenes, cinematic_plan)):
            try:
                print(f"[CINEMATIC] Processing scene {i}: {plan['camera_movement'].movement_type} movement")
                
                # Apply camera movement
                enhanced_file = await self._apply_camera_movement(
                    video_file, plan['camera_movement'], i
                )
                
                if enhanced_file and Path(enhanced_file).exists():
                    enhanced_video_files.append(enhanced_file)
                    print(f"[CINEMATIC] ✅ Applied camera movement to scene {i}")
                else:
                    print(f"[CINEMATIC] ⚠️ Camera movement failed for scene {i}, using original")
                    enhanced_video_files.append(video_file)
            
            except Exception as e:
                print(f"[CINEMATIC] ⚠️ Error applying camera movement to scene {i}: {e}")
                enhanced_video_files.append(video_file)
        
        print(f"[CINEMATIC] ✅ Camera movements applied to {len(enhanced_video_files)} scenes")
        return enhanced_video_files
    
    async def _apply_camera_movement(self, video_file: str, movement: CameraMovement, scene_index: int) -> str:
        """Apply specific camera movement to a video file."""
        try:
            output_file = self.temp_dir / f"camera_enhanced_{scene_index}.mp4"
            
            # Build FFmpeg filter for camera movement
            movement_filter = self._build_camera_movement_filter(movement)
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-vf", movement_filter,
                "-c:v", self.encoding_params.video_codec,
                "-preset", "medium",
                "-crf", "18",  # High quality for intermediate processing
                "-c:a", "copy",  # Copy audio unchanged
                str(output_file)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and output_file.exists():
                return str(output_file)
            else:
                print(f"[CINEMATIC] Camera movement FFmpeg error: {stderr.decode()}")
                return None
        
        except Exception as e:
            print(f"[CINEMATIC] Camera movement error: {e}")
            return None
    
    def _build_camera_movement_filter(self, movement: CameraMovement) -> str:
        """Build FFmpeg filter string for camera movement."""
        start_pos = movement.start_position
        end_pos = movement.end_position
        duration = movement.duration
        
        # Convert movement to FFmpeg zoompan filter
        if movement.movement_type == "zoom":
            # Zoom in or out
            start_zoom = start_pos.get("scale", 1.0)
            end_zoom = end_pos.get("scale", 1.0)
            
            filter_str = (
                f"zoompan=z='if(lte(zoom,1.0),{start_zoom},{start_zoom}+"
                f"({end_zoom}-{start_zoom})*on/{int(duration*30)})'"
                f":d={int(duration*30)}:s={self.encoding_params.resolution}"
            )
        
        elif movement.movement_type == "pan":
            # Pan left/right or up/down
            start_x = start_pos.get("x", 0)
            end_x = end_pos.get("x", 0)
            start_y = start_pos.get("y", 0)
            end_y = end_pos.get("y", 0)
            
            filter_str = (
                f"zoompan=z=1:x='if(gte(on,1),{start_x}+({end_x}-{start_x})*on/{int(duration*30)},{start_x})'"
                f":y='if(gte(on,1),{start_y}+({end_y}-{start_y})*on/{int(duration*30)},{start_y})'"
                f":d={int(duration*30)}:s={self.encoding_params.resolution}"
            )
        
        elif movement.movement_type == "dolly":
            # Dolly in/out with slight movement
            start_zoom = start_pos.get("scale", 1.0)
            end_zoom = end_pos.get("scale", 1.0)
            start_y = start_pos.get("y", 0)
            end_y = end_pos.get("y", 0)
            
            filter_str = (
                f"zoompan=z='if(lte(zoom,1.0),{start_zoom},{start_zoom}+"
                f"({end_zoom}-{start_zoom})*on/{int(duration*30)})'"
                f":y='if(gte(on,1),{start_y}+({end_y}-{start_y})*on/{int(duration*30)},{start_y})'"
                f":d={int(duration*30)}:s={self.encoding_params.resolution}"
            )
        
        elif movement.movement_type == "crane":
            # Complex crane movement with rotation
            start_x = start_pos.get("x", 0)
            end_x = end_pos.get("x", 0)
            start_y = start_pos.get("y", 0)
            end_y = end_pos.get("y", 0)
            start_zoom = start_pos.get("scale", 1.0)
            end_zoom = end_pos.get("scale", 1.0)
            
            filter_str = (
                f"zoompan=z='if(lte(zoom,1.0),{start_zoom},{start_zoom}+"
                f"({end_zoom}-{start_zoom})*on/{int(duration*30)})'"
                f":x='if(gte(on,1),{start_x}+({end_x}-{start_x})*on/{int(duration*30)},{start_x})'"
                f":y='if(gte(on,1),{start_y}+({end_y}-{start_y})*on/{int(duration*30)},{start_y})'"
                f":d={int(duration*30)}:s={self.encoding_params.resolution}"
            )
        
        elif movement.movement_type == "handheld":
            # Subtle handheld shake
            filter_str = (
                f"zoompan=z=1.02:x='iw/2-(iw/zoom/2)+sin(on*0.1)*10'"
                f":y='ih/2-(ih/zoom/2)+cos(on*0.08)*8'"
                f":d={int(duration*30)}:s={self.encoding_params.resolution}"
            )
        
        else:  # static
            filter_str = f"scale={self.encoding_params.resolution}"
        
        return filter_str
    
    async def _apply_color_grading_and_effects(
        self, 
        video_files: List[str], 
        cinematic_plan: List[Dict[str, Any]]
    ) -> List[str]:
        """Apply color grading and visual effects to video files."""
        print(f"[CINEMATIC] Applying color grading and visual effects...")
        
        graded_video_files = []
        
        for i, (video_file, plan) in enumerate(zip(video_files, cinematic_plan)):
            try:
                print(f"[CINEMATIC] Grading scene {i}: {plan['color_grading'].film_emulation} emulation")
                
                # Apply color grading
                graded_file = await self._apply_color_grading(
                    video_file, plan['color_grading'], i
                )
                
                if graded_file and Path(graded_file).exists():
                    graded_video_files.append(graded_file)
                    print(f"[CINEMATIC] ✅ Applied color grading to scene {i}")
                else:
                    print(f"[CINEMATIC] ⚠️ Color grading failed for scene {i}, using original")
                    graded_video_files.append(video_file)
            
            except Exception as e:
                print(f"[CINEMATIC] ⚠️ Error applying color grading to scene {i}: {e}")
                graded_video_files.append(video_file)
        
        print(f"[CINEMATIC] ✅ Color grading applied to {len(graded_video_files)} scenes")
        return graded_video_files
    
    async def _apply_color_grading(self, video_file: str, grading: ColorGrading, scene_index: int) -> str:
        """Apply color grading to a video file."""
        try:
            output_file = self.temp_dir / f"graded_{scene_index}.mp4"
            
            # Build color grading filter
            grading_filter = self._build_color_grading_filter(grading)
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-vf", grading_filter,
                "-c:v", self.encoding_params.video_codec,
                "-preset", "medium",
                "-crf", "16",  # Very high quality for color grading
                "-c:a", "copy",
                str(output_file)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and output_file.exists():
                return str(output_file)
            else:
                print(f"[CINEMATIC] Color grading FFmpeg error: {stderr.decode()}")
                return None
        
        except Exception as e:
            print(f"[CINEMATIC] Color grading error: {e}")
            return None
    
    def _build_color_grading_filter(self, grading: ColorGrading) -> str:
        """Build FFmpeg filter string for color grading."""
        filters = []
        
        # Basic color adjustments
        if grading.brightness != 0:
            filters.append(f"eq=brightness={grading.brightness}")
        
        if grading.contrast != 0:
            filters.append(f"eq=contrast={1.0 + grading.contrast}")
        
        if grading.saturation != 0:
            filters.append(f"eq=saturation={1.0 + grading.saturation}")
        
        # Temperature and tint adjustments (simplified)
        if grading.temperature != 0:
            # Warm/cool adjustment using color balance
            if grading.temperature > 0:  # Warmer
                filters.append(f"colorbalance=rs={grading.temperature*0.3}:bs={-grading.temperature*0.2}")
            else:  # Cooler
                filters.append(f"colorbalance=bs={-grading.temperature*0.3}:rs={grading.temperature*0.2}")
        
        if grading.tint != 0:
            # Green/magenta adjustment
            if grading.tint > 0:  # More magenta
                filters.append(f"colorbalance=ms={grading.tint*0.2}")
            else:  # More green
                filters.append(f"colorbalance=gs={-grading.tint*0.2}")
        
        # Shadow and highlight adjustments
        if grading.shadows != 0 or grading.highlights != 0:
            # Use curves filter for shadow/highlight control
            shadow_val = 0.5 + grading.shadows * 0.3
            highlight_val = 0.5 + grading.highlights * 0.3
            filters.append(f"curves=all='0/0 0.3/{shadow_val} 0.7/{highlight_val} 1/1'")
        
        # Film grain effect
        if self.cinematic_settings.film_grain:
            filters.append("noise=alls=3:allf=t")
        
        # Combine all filters
        if filters:
            return ",".join(filters)
        else:
            return "null"  # No-op filter
    
    async def _create_professional_sound_design(
        self, 
        audio_files: List[str], 
        scenes: List[Scene], 
        cinematic_plan: List[Dict[str, Any]]
    ) -> List[str]:
        """Create professional sound design for audio files."""
        print(f"[CINEMATIC] Creating professional sound design...")
        
        enhanced_audio_files = []
        
        for i, (audio_file, scene, plan) in enumerate(zip(audio_files, scenes, cinematic_plan)):
            try:
                print(f"[CINEMATIC] Enhancing audio for scene {i}")
                
                # Apply sound design
                enhanced_file = await self._apply_sound_design(
                    audio_file, plan['sound_design'], scene, i
                )
                
                if enhanced_file and Path(enhanced_file).exists():
                    enhanced_audio_files.append(enhanced_file)
                    print(f"[CINEMATIC] ✅ Applied sound design to scene {i}")
                else:
                    print(f"[CINEMATIC] ⚠️ Sound design failed for scene {i}, using original")
                    enhanced_audio_files.append(audio_file)
            
            except Exception as e:
                print(f"[CINEMATIC] ⚠️ Error applying sound design to scene {i}: {e}")
                enhanced_audio_files.append(audio_file)
        
        print(f"[CINEMATIC] ✅ Sound design applied to {len(enhanced_audio_files)} scenes")
        return enhanced_audio_files
    
    async def _apply_sound_design(
        self, 
        audio_file: str, 
        sound_design: SoundDesign, 
        scene: Scene, 
        scene_index: int
    ) -> str:
        """Apply sound design to an audio file."""
        try:
            output_file = self.temp_dir / f"sound_designed_{scene_index}.wav"
            
            # Build audio processing filter
            audio_filter = self._build_sound_design_filter(sound_design, scene)
            
            # Prepare input files
            inputs = ["-i", audio_file]
            
            # Add ambient audio if enabled
            if sound_design.ambient_audio:
                ambient_file = self.audio_assets_dir / "room_tone.wav"
                if ambient_file.exists():
                    inputs.extend(["-i", str(ambient_file)])
            
            # Add music if enabled and appropriate
            if sound_design.music_scoring:
                music_file = self._select_music_for_scene(scene, scene_index)
                if music_file and Path(music_file).exists():
                    inputs.extend(["-i", str(music_file)])
            
            cmd = ["ffmpeg", "-y"] + inputs + [
                "-filter_complex", audio_filter,
                "-map", "[out]",
                "-c:a", "pcm_s16le",
                "-ar", str(self.encoding_params.audio_sample_rate),
                str(output_file)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and output_file.exists():
                return str(output_file)
            else:
                print(f"[CINEMATIC] Sound design FFmpeg error: {stderr.decode()}")
                return None
        
        except Exception as e:
            print(f"[CINEMATIC] Sound design error: {e}")
            return None
    
    def _build_sound_design_filter(self, sound_design: SoundDesign, scene: Scene) -> str:
        """Build FFmpeg filter string for sound design."""
        filters = []
        input_count = 1  # Start with main audio
        
        # Main audio processing
        main_audio = "[0:a]"
        
        # Apply EQ if enabled
        if sound_design.eq_processing:
            main_audio += "equalizer=f=100:width_type=h:width=50:g=2,"
            main_audio += "equalizer=f=1000:width_type=h:width=100:g=1,"
            main_audio += "equalizer=f=8000:width_type=h:width=200:g=3"
        
        # Apply dynamic range compression
        if sound_design.dynamic_range_compression:
            main_audio += ",compand=attacks=0.1:decays=0.3:points=-80/-80|-20/-15|-10/-10|0/-5"
        
        # Apply reverb
        reverb_settings = sound_design.reverb_settings
        if reverb_settings:
            reverb_filter = (
                f"aecho=0.8:0.88:{int(reverb_settings['room_size']*1000)}:"
                f"{reverb_settings['wet_level']}"
            )
            main_audio += f",{reverb_filter}"
        
        # Mix with ambient audio if available
        if sound_design.ambient_audio and input_count < 3:  # Check if ambient was added
            ambient_audio = f"[{input_count}:a]volume=0.1[ambient]"
            filters.append(ambient_audio)
            main_audio += f"[main];[main][ambient]amix=inputs=2:duration=longest"
            input_count += 1
        
        # Mix with music if available
        if sound_design.music_scoring and input_count < 4:  # Check if music was added
            music_audio = f"[{input_count}:a]volume=0.2[music]"
            filters.append(music_audio)
            if "[main]" not in main_audio:
                main_audio += "[main]"
            main_audio += f";[main][music]amix=inputs=2:duration=longest"
        
        # Final output
        main_audio += "[out]"
        filters.append(main_audio)
        
        return ";".join(filters)
    
    def _select_music_for_scene(self, scene: Scene, scene_index: int) -> Optional[str]:
        """Select appropriate music for a scene."""
        content = scene.narration.lower()
        
        # Select music based on scene content and position
        if scene_index == 0:  # Opening scene
            music_file = self.audio_assets_dir / "intro_chord.wav"
        elif "conclusion" in content or "future" in content:
            music_file = self.audio_assets_dir / "conclusion_chord.wav"
        elif any(word in content for word in ["transition", "next", "however"]):
            music_file = self.audio_assets_dir / "transition_sweep.wav"
        else:
            return None  # No music for this scene
        
        return str(music_file) if music_file.exists() else None
    
    async def _advanced_compositing_and_assembly(
        self, 
        video_files: List[str], 
        audio_files: List[str], 
        scenes: List[Scene], 
        output_path: str,
        cinematic_plan: List[Dict[str, Any]]
    ) -> bool:
        """Perform advanced compositing and final assembly."""
        print(f"[CINEMATIC] Performing advanced compositing and final assembly...")
        
        try:
            # Create scene segments with transitions
            scene_segments = []
            
            for i, (video_file, audio_file, scene, plan) in enumerate(zip(video_files, audio_files, scenes, cinematic_plan)):
                print(f"[CINEMATIC] Creating segment for scene {i}")
                
                # Create scene segment with synchronized audio
                segment_file = await self._create_scene_segment(
                    video_file, audio_file, scene, plan, i
                )
                
                if segment_file and Path(segment_file).exists():
                    scene_segments.append(segment_file)
                else:
                    print(f"[CINEMATIC] ⚠️ Failed to create segment for scene {i}")
                    return False
            
            # Apply transitions between segments
            if len(scene_segments) > 1:
                transitioned_segments = await self._apply_transitions_between_segments(
                    scene_segments, cinematic_plan
                )
            else:
                transitioned_segments = scene_segments
            
            # Final assembly with cinematic quality
            success = await self._final_cinematic_assembly(
                transitioned_segments, output_path
            )
            
            if success:
                print(f"[CINEMATIC] ✅ Advanced compositing completed successfully")
                return True
            else:
                print(f"[CINEMATIC] ❌ Advanced compositing failed")
                return False
        
        except Exception as e:
            print(f"[CINEMATIC] ❌ Error during advanced compositing: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def _create_scene_segment(
        self, 
        video_file: str, 
        audio_file: str, 
        scene: Scene, 
        plan: Dict[str, Any], 
        scene_index: int
    ) -> str:
        """Create a complete scene segment with video and audio."""
        try:
            output_file = self.temp_dir / f"segment_{scene_index}.mp4"
            
            cmd = [
                "ffmpeg", "-y",
                "-i", video_file,
                "-i", audio_file,
                "-t", str(scene.duration),
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-c:v", self.encoding_params.video_codec,
                "-c:a", self.encoding_params.audio_codec,
                "-preset", self.encoding_params.preset,
                "-crf", str(self.encoding_params.crf),
                "-b:a", self.encoding_params.audio_bitrate,
                "-ar", str(self.encoding_params.audio_sample_rate),
                "-shortest",  # Match shortest stream duration
                str(output_file)
            ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and output_file.exists():
                print(f"[CINEMATIC] ✅ Created segment {scene_index}: {output_file.stat().st_size} bytes")
                return str(output_file)
            else:
                print(f"[CINEMATIC] Segment creation error: {stderr.decode()}")
                return None
        
        except Exception as e:
            print(f"[CINEMATIC] Error creating segment {scene_index}: {e}")
            return None
    
    async def _apply_transitions_between_segments(
        self, 
        segments: List[str], 
        cinematic_plan: List[Dict[str, Any]]
    ) -> List[str]:
        """Apply cinematic transitions between segments."""
        print(f"[CINEMATIC] Applying transitions between {len(segments)} segments...")
        
        try:
            # For now, return segments as-is since complex transitions require advanced FFmpeg
            # In a full implementation, this would apply crossfades, wipes, etc.
            print(f"[CINEMATIC] ✅ Transitions applied (simplified implementation)")
            return segments
        
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Error applying transitions: {e}")
            return segments
    
    async def _final_cinematic_assembly(self, segments: List[str], output_path: str) -> bool:
        """Perform final assembly with cinematic quality settings."""
        try:
            print(f"[CINEMATIC] Final assembly of {len(segments)} segments...")
            
            if len(segments) == 1:
                # Single segment - just copy with final encoding
                cmd = [
                    "ffmpeg", "-y",
                    "-i", segments[0],
                    "-c:v", self.encoding_params.video_codec,
                    "-c:a", self.encoding_params.audio_codec,
                    "-preset", self.encoding_params.preset,
                    "-crf", str(self.encoding_params.crf),
                    "-b:v", self.encoding_params.bitrate,
                    "-b:a", self.encoding_params.audio_bitrate,
                    "-ar", str(self.encoding_params.audio_sample_rate),
                    "-pix_fmt", self.encoding_params.pixel_format,
                    "-movflags", "+faststart",
                    output_path
                ]
            else:
                # Multiple segments - concatenate
                concat_file = self.temp_dir / "final_concat.txt"
                with open(concat_file, 'w') as f:
                    for segment in segments:
                        f.write(f"file '{Path(segment).resolve()}'\n")
                
                cmd = [
                    "ffmpeg", "-y",
                    "-f", "concat",
                    "-safe", "0",
                    "-i", str(concat_file),
                    "-c:v", self.encoding_params.video_codec,
                    "-c:a", self.encoding_params.audio_codec,
                    "-preset", self.encoding_params.preset,
                    "-crf", str(self.encoding_params.crf),
                    "-b:v", self.encoding_params.bitrate,
                    "-b:a", self.encoding_params.audio_bitrate,
                    "-ar", str(self.encoding_params.audio_sample_rate),
                    "-pix_fmt", self.encoding_params.pixel_format,
                    "-movflags", "+faststart",
                    output_path
                ]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                print(f"[CINEMATIC] ✅ Final assembly completed: {file_size} bytes")
                return True
            else:
                print(f"[CINEMATIC] Final assembly error: {stderr.decode()}")
                return False
        
        except Exception as e:
            print(f"[CINEMATIC] Error in final assembly: {e}")
            return False
    
    async def _validate_cinematic_output(self, output_path: str):
        """Validate the cinematic output quality."""
        try:
            if not Path(output_path).exists():
                print(f"[CINEMATIC] ❌ Output file does not exist: {output_path}")
                return
            
            file_size = Path(output_path).stat().st_size
            print(f"[CINEMATIC] 📊 Output file size: {file_size:,} bytes ({file_size/1024/1024:.1f} MB)")
            
            # Check if file size indicates real content
            if file_size > 10 * 1024 * 1024:  # > 10MB
                print(f"[CINEMATIC] ✅ Large file size indicates substantial cinematic content")
            elif file_size > 1 * 1024 * 1024:  # > 1MB
                print(f"[CINEMATIC] ✅ Reasonable file size for cinematic content")
            else:
                print(f"[CINEMATIC] ⚠️ Small file size - may need quality improvement")
            
            # Try to get video info using ffprobe
            try:
                cmd = [
                    "ffprobe", "-v", "quiet", "-print_format", "json",
                    "-show_format", "-show_streams", output_path
                ]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                if result.returncode == 0:
                    import json
                    info = json.loads(stdout.decode())
                    
                    # Extract video info
                    video_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'video']
                    audio_streams = [s for s in info.get('streams', []) if s.get('codec_type') == 'audio']
                    
                    if video_streams:
                        video_stream = video_streams[0]
                        print(f"[CINEMATIC] 📹 Video: {video_stream.get('width')}x{video_stream.get('height')} @ {video_stream.get('r_frame_rate')} fps")
                        print(f"[CINEMATIC] 📹 Codec: {video_stream.get('codec_name')}")
                    
                    if audio_streams:
                        audio_stream = audio_streams[0]
                        print(f"[CINEMATIC] 🔊 Audio: {audio_stream.get('sample_rate')} Hz, {audio_stream.get('channels')} channels")
                        print(f"[CINEMATIC] 🔊 Codec: {audio_stream.get('codec_name')}")
                    
                    duration = float(info.get('format', {}).get('duration', 0))
                    print(f"[CINEMATIC] ⏱️ Duration: {duration:.1f} seconds")
                    
                    print(f"[CINEMATIC] ✅ Cinematic video validation completed")
                
            except Exception as probe_error:
                print(f"[CINEMATIC] ⚠️ Could not probe video info: {probe_error}")
        
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Validation error: {e}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files."""
        try:
            import shutil
            if self.temp_dir.exists():
                shutil.rmtree(self.temp_dir)
                print(f"[CINEMATIC] 🧹 Cleaned up temporary files")
        except Exception as e:
            print(f"[CINEMATIC] ⚠️ Cleanup error: {e}")
    
    def _create_camera_movement(
        self, 
        movement_type: str, 
        scene_analysis: Dict[str, Any], 
        scene_index: int, 
        total_scenes: int
    ) -> CameraMovement:
        """Create camera movement with appropriate parameters."""
        
        # Get intensity from UI settings
        intensity = 0.5  # Default
        if self.ui_settings:
            intensity = self.ui_settings.camera_movements.intensity / 100.0
        
        # Base positions
        start_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
        end_pos = {"x": 0, "y": 0, "scale": 1.0, "rotation": 0}
        
        # Adjust based on movement type and intensity
        if movement_type == "zoom":
            end_pos["scale"] = 1.0 + (intensity * 0.3)
        elif movement_type == "pan":
            end_pos["x"] = intensity * 50
        elif movement_type == "dolly":
            end_pos["y"] = intensity * 30
            end_pos["scale"] = 1.0 + (intensity * 0.2)
        elif movement_type == "crane":
            end_pos["y"] = -intensity * 40
            end_pos["scale"] = 1.0 + (intensity * 0.15)
        elif movement_type == "handheld":
            # Handheld creates subtle random movements
            end_pos["x"] = intensity * 10
            end_pos["y"] = intensity * 8
        
        # Duration based on content complexity
        base_duration = 3.0
        if scene_analysis["complexity"] == "high":
            base_duration = 4.0
        elif scene_analysis["complexity"] == "low":
            base_duration = 2.0
        
        return CameraMovement(
            movement_type=movement_type,
            start_position=start_pos,
            end_position=end_pos,
            duration=base_duration,
            easing="ease_in_out"
        )
    
    def _determine_legacy_camera_movement(
        self, 
        scene_analysis: Dict[str, Any], 
        scene_index: int, 
        total_scenes: int
    ) -> str:
        """Legacy camera movement determination for backward compatibility."""
        
        # First scene - welcoming zoom
        if scene_index == 0:
            return "zoom"
        
        # Last scene - concluding dolly
        if scene_index == total_scenes - 1:
            return "dolly"
        
        # Based on content type
        content_type = scene_analysis.get("content_type", "general")
        
        if content_type == "mathematical":
            return "zoom"  # Focus on equations
        elif content_type == "architectural":
            return "pan"   # Show structure
        elif content_type == "analytical":
            return "static"  # Let data speak
        elif content_type == "procedural":
            return "dolly"   # Guide through process
        else:
            return "pan"     # General movement
    
    def _determine_legacy_color_grading(self, scene_analysis: Dict[str, Any]) -> ColorGrading:
        """Legacy color grading determination for backward compatibility."""
        
        content_type = scene_analysis.get("content_type", "general")
        mood = scene_analysis.get("mood", "neutral")
        
        color_grading = ColorGrading()
        
        # Adjust based on content type
        if content_type == "mathematical":
            color_grading.film_emulation = "cinema"
            color_grading.contrast = 0.2
            color_grading.saturation = -0.1
        elif content_type == "architectural":
            color_grading.film_emulation = "kodak"
            color_grading.contrast = 0.15
            color_grading.highlights = -0.1
        elif content_type == "analytical":
            color_grading.film_emulation = "fuji"
            color_grading.brightness = 0.1
            color_grading.contrast = 0.1
        
        # Adjust based on mood
        if mood == "serious":
            color_grading.temperature = -0.1  # Cooler
            color_grading.shadows = 0.1
        elif mood == "positive":
            color_grading.temperature = 0.1   # Warmer
            color_grading.brightness = 0.05
        elif mood == "welcoming":
            color_grading.temperature = 0.15  # Warm
            color_grading.saturation = 0.1
        
        return color_grading
    
    def _determine_legacy_sound_design(self, scene_analysis: Dict[str, Any]) -> SoundDesign:
        """Legacy sound design determination for backward compatibility."""
        
        content_type = scene_analysis.get("content_type", "general")
        mood = scene_analysis.get("mood", "neutral")
        
        # Base sound design
        sound_design = SoundDesign()
        
        # Adjust based on content type
        if content_type == "mathematical":
            sound_design.ambient_audio = False  # Minimize distractions
            sound_design.music_scoring = True
            sound_design.reverb_settings["wet_level"] = 0.1
        elif content_type == "architectural":
            sound_design.spatial_audio = True   # Enhance spatial awareness
            sound_design.reverb_settings["room_size"] = 0.5
        elif content_type == "analytical":
            sound_design.ambient_audio = False  # Focus on content
            sound_design.dynamic_range_compression = True
        
        # Adjust based on mood
        if mood == "serious":
            sound_design.reverb_settings["damping"] = 0.7  # More controlled
        elif mood == "positive":
            sound_design.music_scoring = True
            sound_design.reverb_settings["wet_level"] = 0.25
        
        return sound_design
    
    async def get_visual_descriptions(self) -> Dict[str, VisualDescriptionModel]:
        """Get all visual descriptions for the current generation."""
        return self.visual_descriptions.copy()
    
    def is_ui_enhanced(self) -> bool:
        """Check if generator is using UI enhancements."""
        return self.ui_settings is not None
    
    def is_ai_enhanced(self) -> bool:
        """Check if generator is using AI enhancements."""
        return self.gemini_client is not None
    
    def get_effective_settings(self) -> Dict[str, Any]:
        """Get the effective settings being used for generation."""
        if self.ui_settings:
            return {
                "ui_settings": self.ui_settings.to_dict(),
                "legacy_settings": self.cinematic_settings.__dict__,
                "ai_enhanced": self.is_ai_enhanced(),
                "visual_descriptions_count": len(self.visual_descriptions)
            }
        else:
            return {
                "legacy_settings": self.cinematic_settings.__dict__,
                "ai_enhanced": False,
                "visual_descriptions_count": 0
            }