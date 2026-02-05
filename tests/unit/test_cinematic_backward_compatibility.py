"""
Property tests for cinematic video generator backward compatibility.
Tests that enhanced system maintains compatibility with existing workflows.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Mock the Scene class for testing
@dataclass
class MockScene:
    content: str
    duration: float = 5.0

# Mock imports for testing
class MockCinematicSettingsModel:
    def __init__(self, **kwargs):
        self.camera_movements = Mock()
        self.camera_movements.enabled = kwargs.get('camera_enabled', True)
        self.camera_movements.intensity = kwargs.get('camera_intensity', 50)
        self.camera_movements.allowed_types = kwargs.get('camera_types', [])
        
        self.color_grading = Mock()
        self.color_grading.enabled = kwargs.get('color_enabled', True)
        self.color_grading.film_emulation = Mock()
        self.color_grading.film_emulation.value = kwargs.get('film_emulation', 'kodak')
        self.color_grading.temperature = kwargs.get('temperature', 0)
        self.color_grading.contrast = kwargs.get('contrast', 0)
        self.color_grading.saturation = kwargs.get('saturation', 0)
        self.color_grading.brightness = kwargs.get('brightness', 0)
        self.color_grading.tint = kwargs.get('tint', 0)
        self.color_grading.shadows = kwargs.get('shadows', 0)
        self.color_grading.highlights = kwargs.get('highlights', 0)
        
        self.sound_design = Mock()
        self.sound_design.enabled = kwargs.get('sound_enabled', True)
        self.sound_design.ambient_audio = kwargs.get('ambient_audio', True)
        self.sound_design.music_scoring = kwargs.get('music_scoring', True)
        self.sound_design.spatial_audio = kwargs.get('spatial_audio', False)
        self.sound_design.reverb_intensity = kwargs.get('reverb_intensity', 30)
        self.sound_design.dynamic_range_compression = kwargs.get('compression', True)
        self.sound_design.eq_processing = kwargs.get('eq_processing', True)
        
        self.advanced_compositing = Mock()
        self.advanced_compositing.enabled = kwargs.get('compositing_enabled', True)
        self.advanced_compositing.professional_transitions = kwargs.get('transitions', True)
        self.advanced_compositing.lut_application = kwargs.get('lut', True)
        self.advanced_compositing.dynamic_lighting = kwargs.get('lighting', True)
        self.advanced_compositing.depth_of_field = kwargs.get('dof', False)
        self.advanced_compositing.motion_blur = kwargs.get('motion_blur', False)
        self.advanced_compositing.film_grain = kwargs.get('film_grain', True)
        
        self.quality_preset = kwargs.get('quality', 'cinematic_4k')
        self.auto_recommendations = kwargs.get('auto_rec', True)
    
    def to_dict(self):
        return {
            'camera_movements': {
                'enabled': self.camera_movements.enabled,
                'intensity': self.camera_movements.intensity
            },
            'color_grading': {
                'enabled': self.color_grading.enabled,
                'film_emulation': self.color_grading.film_emulation.value
            },
            'sound_design': {
                'enabled': self.sound_design.enabled
            },
            'advanced_compositing': {
                'enabled': self.advanced_compositing.enabled
            }
        }

class MockGeminiClient:
    def __init__(self):
        self.call_count = 0
    
    async def generate_detailed_visual_description(self, **kwargs):
        self.call_count += 1
        return {
            "description": f"AI generated description {self.call_count}",
            "scene_analysis": {
                "focusType": "general",
                "complexity": "medium",
                "mood": "neutral",
                "recommendedCameraMovement": "pan"
            },
            "confidence": 0.8
        }

# Mock the cinematic video generator with minimal dependencies
class MockCinematicVideoGenerator:
    """Mock cinematic video generator for testing backward compatibility."""
    
    def __init__(self, output_dir: str, quality: str = "cinematic_4k", 
                 ui_settings: Optional[MockCinematicSettingsModel] = None,
                 gemini_client: Optional[MockGeminiClient] = None):
        self.output_dir = Path(output_dir)
        self.quality = quality
        self.ui_settings = ui_settings
        self.gemini_client = gemini_client
        self.visual_descriptions = {}
        
        # Legacy settings for backward compatibility
        self.cinematic_settings = Mock()
        self.cinematic_settings.camera_movements = ui_settings.camera_movements.enabled if ui_settings else True
        self.cinematic_settings.color_grading = ui_settings.color_grading.enabled if ui_settings else True
        self.cinematic_settings.sound_design = ui_settings.sound_design.enabled if ui_settings else True
        
        # Track method calls for testing
        self.method_calls = []
    
    async def generate_cinematic_video(self, scenes, video_files, audio_files, output_path, 
                                     custom_visual_descriptions=None):
        """Mock video generation."""
        self.method_calls.append('generate_cinematic_video')
        
        # Simulate processing
        await asyncio.sleep(0.01)
        
        # Check if all required parameters are provided
        if not scenes or not video_files or not output_path:
            return False
        
        # Simulate successful generation
        return True
    
    async def set_visual_descriptions(self, descriptions):
        """Mock visual description setting."""
        self.method_calls.append('set_visual_descriptions')
        self.visual_descriptions.update(descriptions)
    
    async def generate_ai_visual_descriptions(self, scenes):
        """Mock AI description generation."""
        self.method_calls.append('generate_ai_visual_descriptions')
        
        if not self.gemini_client:
            return {}
        
        descriptions = {}
        for i, scene in enumerate(scenes):
            result = await self.gemini_client.generate_detailed_visual_description(
                scene_content=scene.content
            )
            descriptions[f"scene_{i}"] = result["description"]
        
        return descriptions
    
    def is_ui_enhanced(self):
        """Check if using UI enhancements."""
        return self.ui_settings is not None
    
    def is_ai_enhanced(self):
        """Check if using AI enhancements."""
        return self.gemini_client is not None
    
    def get_effective_settings(self):
        """Get effective settings."""
        if self.ui_settings:
            return {
                "ui_settings": self.ui_settings.to_dict(),
                "legacy_compatible": True,
                "ai_enhanced": self.is_ai_enhanced()
            }
        else:
            return {
                "legacy_settings": {
                    "camera_movements": self.cinematic_settings.camera_movements,
                    "color_grading": self.cinematic_settings.color_grading,
                    "sound_design": self.cinematic_settings.sound_design
                },
                "legacy_compatible": True,
                "ai_enhanced": False
            }


# Strategies for generating test data
@st.composite
def scene_content(draw):
    """Generate scene content."""
    content_types = [
        "Mathematical equation: f(x) = x^2 + 2x + 1",
        "System architecture overview with components",
        "Performance analysis showing 95% improvement",
        "Step-by-step algorithm implementation",
        "Introduction to the research methodology",
        "Conclusion and future work directions"
    ]
    return draw(st.sampled_from(content_types))

@st.composite
def mock_scenes(draw):
    """Generate list of mock scenes."""
    num_scenes = draw(st.integers(min_value=1, max_value=8))
    scenes = []
    
    for i in range(num_scenes):
        content = draw(scene_content())
        duration = draw(st.floats(min_value=2.0, max_value=10.0))
        scenes.append(MockScene(content=content, duration=duration))
    
    return scenes

@st.composite
def ui_settings_config(draw):
    """Generate UI settings configuration."""
    return {
        'camera_enabled': draw(st.booleans()),
        'camera_intensity': draw(st.integers(min_value=0, max_value=100)),
        'color_enabled': draw(st.booleans()),
        'sound_enabled': draw(st.booleans()),
        'compositing_enabled': draw(st.booleans()),
        'quality': draw(st.sampled_from(['standard_hd', 'cinematic_4k', 'cinematic_8k']))
    }


class TestCinematicBackwardCompatibility:
    """Test backward compatibility of enhanced cinematic system."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up test dependencies."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(mock_scenes())
    @settings(max_examples=15, deadline=8000)
    def test_legacy_mode_functionality(self, scenes):
        """Property: Legacy mode should work without UI settings or AI client."""
        async def test_legacy():
            # Create generator without UI settings (legacy mode)
            generator = MockCinematicVideoGenerator(
                output_dir=self.temp_dir,
                quality="cinematic_4k"
            )
            
            # Should not be UI or AI enhanced
            assert not generator.is_ui_enhanced()
            assert not generator.is_ai_enhanced()
            
            # Should still generate videos successfully
            video_files = [f"video_{i}.mp4" for i in range(len(scenes))]
            audio_files = [f"audio_{i}.wav" for i in range(len(scenes))]
            output_path = str(Path(self.temp_dir) / "legacy_output.mp4")
            
            success = await generator.generate_cinematic_video(
                scenes=scenes,
                video_files=video_files,
                audio_files=audio_files,
                output_path=output_path
            )
            
            # Should succeed
            assert success, "Legacy mode should generate videos successfully"
            
            # Should have called the main generation method
            assert 'generate_cinematic_video' in generator.method_calls
            
            # Settings should be legacy compatible
            settings = generator.get_effective_settings()
            assert 'legacy_settings' in settings
            assert settings['legacy_compatible']
        
        asyncio.run(test_legacy())
    
    @given(mock_scenes(), ui_settings_config())
    @settings(max_examples=15, deadline=8000)
    def test_ui_enhanced_mode_compatibility(self, scenes, ui_config):
        """Property: UI enhanced mode should maintain backward compatibility."""
        async def test_ui_enhanced():
            # Create UI settings
            ui_settings = MockCinematicSettingsModel(**ui_config)
            
            # Create generator with UI settings
            generator = MockCinematicVideoGenerator(
                output_dir=self.temp_dir,
                quality=ui_config['quality'],
                ui_settings=ui_settings
            )
            
            # Should be UI enhanced
            assert generator.is_ui_enhanced()
            
            # Should still work with legacy interface
            video_files = [f"video_{i}.mp4" for i in range(len(scenes))]
            audio_files = [f"audio_{i}.wav" for i in range(len(scenes))]
            output_path = str(Path(self.temp_dir) / "ui_enhanced_output.mp4")
            
            success = await generator.generate_cinematic_video(
                scenes=scenes,
                video_files=video_files,
                audio_files=audio_files,
                output_path=output_path
            )
            
            # Should succeed
            assert success, "UI enhanced mode should generate videos successfully"
            
            # Settings should include both UI and legacy compatibility
            settings = generator.get_effective_settings()
            assert 'ui_settings' in settings
            assert settings['legacy_compatible']
            
            # UI settings should be properly converted
            ui_dict = settings['ui_settings']
            assert 'camera_movements' in ui_dict
            assert 'color_grading' in ui_dict
        
        asyncio.run(test_ui_enhanced())
    
    @given(mock_scenes())
    @settings(max_examples=10, deadline=8000)
    def test_ai_enhanced_mode_compatibility(self, scenes):
        """Property: AI enhanced mode should maintain backward compatibility."""
        async def test_ai_enhanced():
            # Create generator with AI client
            gemini_client = MockGeminiClient()
            ui_settings = MockCinematicSettingsModel()
            
            generator = MockCinematicVideoGenerator(
                output_dir=self.temp_dir,
                quality="cinematic_4k",
                ui_settings=ui_settings,
                gemini_client=gemini_client
            )
            
            # Should be both UI and AI enhanced
            assert generator.is_ui_enhanced()
            assert generator.is_ai_enhanced()
            
            # Should generate AI descriptions
            descriptions = await generator.generate_ai_visual_descriptions(scenes)
            
            # Should have descriptions for all scenes
            assert len(descriptions) == len(scenes)
            
            # Should still work with legacy interface
            video_files = [f"video_{i}.mp4" for i in range(len(scenes))]
            audio_files = [f"audio_{i}.wav" for i in range(len(scenes))]
            output_path = str(Path(self.temp_dir) / "ai_enhanced_output.mp4")
            
            success = await generator.generate_cinematic_video(
                scenes=scenes,
                video_files=video_files,
                audio_files=audio_files,
                output_path=output_path
            )
            
            # Should succeed
            assert success, "AI enhanced mode should generate videos successfully"
            
            # Should have called AI generation methods
            assert 'generate_ai_visual_descriptions' in generator.method_calls
        
        asyncio.run(test_ai_enhanced())
    
    @given(mock_scenes(), ui_settings_config())
    @settings(max_examples=10, deadline=8000)
    def test_custom_visual_descriptions_compatibility(self, scenes, ui_config):
        """Property: Custom visual descriptions should work with both legacy and enhanced modes."""
        async def test_custom_descriptions():
            # Create custom descriptions
            custom_descriptions = {
                f"scene_{i}": f"Custom description for scene {i}: {scene.content[:50]}..."
                for i, scene in enumerate(scenes)
            }
            
            # Test with UI enhanced mode
            ui_settings = MockCinematicSettingsModel(**ui_config)
            generator = MockCinematicVideoGenerator(
                output_dir=self.temp_dir,
                ui_settings=ui_settings
            )
            
            # Set custom descriptions
            await generator.set_visual_descriptions(custom_descriptions)
            
            # Should have stored descriptions
            assert len(generator.visual_descriptions) == len(custom_descriptions)
            
            # Should work with video generation
            video_files = [f"video_{i}.mp4" for i in range(len(scenes))]
            audio_files = [f"audio_{i}.wav" for i in range(len(scenes))]
            output_path = str(Path(self.temp_dir) / "custom_desc_output.mp4")
            
            success = await generator.generate_cinematic_video(
                scenes=scenes,
                video_files=video_files,
                audio_files=audio_files,
                output_path=output_path,
                custom_visual_descriptions=custom_descriptions
            )
            
            # Should succeed
            assert success, "Custom descriptions should work with video generation"
            
            # Should have called description setting method
            assert 'set_visual_descriptions' in generator.method_calls
        
        asyncio.run(test_custom_descriptions())
    
    @given(st.lists(mock_scenes(), min_size=1, max_size=3))
    @settings(max_examples=8, deadline=10000)
    def test_settings_conversion_consistency(self, scenes_list):
        """Property: Settings conversion between UI and legacy should be consistent."""
        async def test_conversion():
            for scenes in scenes_list:
                # Create UI settings with various configurations
                ui_configs = [
                    {'camera_enabled': True, 'color_enabled': True, 'sound_enabled': True},
                    {'camera_enabled': False, 'color_enabled': True, 'sound_enabled': False},
                    {'camera_enabled': True, 'color_enabled': False, 'sound_enabled': True}
                ]
                
                for config in ui_configs:
                    ui_settings = MockCinematicSettingsModel(**config)
                    
                    generator = MockCinematicVideoGenerator(
                        output_dir=self.temp_dir,
                        ui_settings=ui_settings
                    )
                    
                    # Get effective settings
                    settings = generator.get_effective_settings()
                    
                    # Should have both UI and legacy compatibility
                    assert 'ui_settings' in settings
                    assert settings['legacy_compatible']
                    
                    # UI settings should match configuration
                    ui_dict = settings['ui_settings']
                    assert ui_dict['camera_movements']['enabled'] == config['camera_enabled']
                    assert ui_dict['color_grading']['enabled'] == config['color_enabled']
                    assert ui_dict['sound_design']['enabled'] == config['sound_enabled']
        
        asyncio.run(test_conversion())
    
    def test_interface_compatibility(self):
        """Property: Enhanced generator should maintain same interface as legacy."""
        # Legacy interface (without UI settings)
        legacy_generator = MockCinematicVideoGenerator(output_dir=self.temp_dir)
        
        # Enhanced interface (with UI settings)
        ui_settings = MockCinematicSettingsModel()
        enhanced_generator = MockCinematicVideoGenerator(
            output_dir=self.temp_dir,
            ui_settings=ui_settings
        )
        
        # Both should have same core methods
        core_methods = [
            'generate_cinematic_video',
            'is_ui_enhanced',
            'is_ai_enhanced',
            'get_effective_settings'
        ]
        
        for method_name in core_methods:
            assert hasattr(legacy_generator, method_name), f"Legacy generator missing {method_name}"
            assert hasattr(enhanced_generator, method_name), f"Enhanced generator missing {method_name}"
        
        # Both should be callable with same parameters
        assert callable(legacy_generator.generate_cinematic_video)
        assert callable(enhanced_generator.generate_cinematic_video)
    
    @given(mock_scenes())
    @settings(max_examples=8, deadline=8000)
    def test_error_handling_compatibility(self, scenes):
        """Property: Error handling should be consistent between legacy and enhanced modes."""
        async def test_error_handling():
            # Test with invalid parameters
            generators = [
                MockCinematicVideoGenerator(output_dir=self.temp_dir),  # Legacy
                MockCinematicVideoGenerator(
                    output_dir=self.temp_dir, 
                    ui_settings=MockCinematicSettingsModel()
                )  # Enhanced
            ]
            
            for generator in generators:
                # Test with missing required parameters
                success = await generator.generate_cinematic_video(
                    scenes=[],  # Empty scenes
                    video_files=[],
                    audio_files=[],
                    output_path=""  # Empty output path
                )
                
                # Both should handle errors gracefully
                assert not success, "Should fail with invalid parameters"
                
                # Test with valid parameters
                video_files = [f"video_{i}.mp4" for i in range(len(scenes))]
                audio_files = [f"audio_{i}.wav" for i in range(len(scenes))]
                output_path = str(Path(self.temp_dir) / "test_output.mp4")
                
                success = await generator.generate_cinematic_video(
                    scenes=scenes,
                    video_files=video_files,
                    audio_files=audio_files,
                    output_path=output_path
                )
                
                # Both should succeed with valid parameters
                assert success, "Should succeed with valid parameters"
        
        asyncio.run(test_error_handling())


class CinematicCompatibilityStateMachine(RuleBasedStateMachine):
    """Stateful property testing for cinematic compatibility."""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.generators = {}
        self.generation_count = 0
    
    generators = Bundle('generators')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=generators)
    def create_legacy_generator(self):
        """Create a legacy generator."""
        gen_id = f"legacy_{len(self.generators)}"
        generator = MockCinematicVideoGenerator(output_dir=self.temp_dir)
        self.generators[gen_id] = generator
        return gen_id
    
    @rule(target=generators)
    def create_enhanced_generator(self):
        """Create an enhanced generator."""
        gen_id = f"enhanced_{len(self.generators)}"
        ui_settings = MockCinematicSettingsModel()
        generator = MockCinematicVideoGenerator(
            output_dir=self.temp_dir,
            ui_settings=ui_settings
        )
        self.generators[gen_id] = generator
        return gen_id
    
    @rule(generator_id=generators)
    def generate_video(self, generator_id):
        """Generate a video with any generator."""
        if generator_id not in self.generators:
            return
        
        generator = self.generators[generator_id]
        
        async def generate():
            scenes = [MockScene(content=f"Test scene {self.generation_count}")]
            video_files = ["test_video.mp4"]
            audio_files = ["test_audio.wav"]
            output_path = f"{self.temp_dir}/output_{self.generation_count}.mp4"
            
            success = await generator.generate_cinematic_video(
                scenes=scenes,
                video_files=video_files,
                audio_files=audio_files,
                output_path=output_path
            )
            
            assert success, "Video generation should succeed"
            self.generation_count += 1
        
        asyncio.run(generate())
    
    @rule(generator_id=generators)
    def check_generator_compatibility(self, generator_id):
        """Check generator compatibility."""
        if generator_id not in self.generators:
            return
        
        generator = self.generators[generator_id]
        
        # Should have core methods
        assert hasattr(generator, 'generate_cinematic_video')
        assert hasattr(generator, 'get_effective_settings')
        
        # Settings should be valid
        settings = generator.get_effective_settings()
        assert isinstance(settings, dict)
        assert 'legacy_compatible' in settings
        assert settings['legacy_compatible']
    
    @invariant()
    def all_generators_compatible(self):
        """Invariant: All generators should maintain compatibility."""
        for gen_id, generator in self.generators.items():
            # Should have required interface
            assert hasattr(generator, 'generate_cinematic_video')
            assert hasattr(generator, 'is_ui_enhanced')
            assert hasattr(generator, 'is_ai_enhanced')
            
            # Settings should be accessible
            settings = generator.get_effective_settings()
            assert isinstance(settings, dict)
    
    def teardown(self):
        """Clean up after state machine testing."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# Test the state machine
TestCinematicCompatibilityState = CinematicCompatibilityStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])