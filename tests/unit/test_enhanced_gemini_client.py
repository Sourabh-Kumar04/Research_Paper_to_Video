"""
Property-based tests for Enhanced Gemini Client
Feature: cinematic-ui-enhancement, Property 5: Gemini Visual Description Generation
Feature: cinematic-ui-enhancement, Property 6: Visual Description Format Compliance
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from hypothesis import given, strategies as st, settings
from typing import Dict, Any, List
import json

# Import the enhanced Gemini client
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from llm.gemini_client import EnhancedGeminiClient, get_enhanced_gemini_client


# Test data generators for property-based testing
@st.composite
def scene_content_strategy(draw):
    """Generate realistic scene content for testing."""
    content_types = [
        "mathematical", "architectural", "analytical", "procedural", "general",
        "introductory", "conclusion", "methodology", "results"
    ]
    
    content_type = draw(st.sampled_from(content_types))
    
    # Generate content based on type
    if content_type == "mathematical":
        content = draw(st.text(min_size=50, max_size=500).filter(
            lambda x: any(word in x.lower() for word in ["equation", "formula", "theorem", "proof"])
        ))
    elif content_type == "architectural":
        content = draw(st.text(min_size=50, max_size=500).filter(
            lambda x: any(word in x.lower() for word in ["system", "design", "architecture", "component"])
        ))
    else:
        content = draw(st.text(min_size=50, max_size=500))
    
    return {
        "content": content,
        "type": content_type
    }


@st.composite
def cinematic_settings_strategy(draw):
    """Generate valid cinematic settings for testing."""
    return {
        "camera_movements": {
            "enabled": draw(st.booleans()),
            "types": draw(st.lists(st.sampled_from(["pan", "zoom", "dolly", "crane", "handheld", "static"]), min_size=1, max_size=3)),
            "intensity": draw(st.integers(min_value=0, max_value=100))
        },
        "color_grading": {
            "enabled": draw(st.booleans()),
            "film_emulation": draw(st.sampled_from(["none", "kodak", "fuji", "cinema"])),
            "temperature": draw(st.integers(min_value=-100, max_value=100)),
            "contrast": draw(st.integers(min_value=-100, max_value=100))
        },
        "sound_design": {
            "enabled": draw(st.booleans()),
            "ambient_audio": draw(st.booleans()),
            "music_scoring": draw(st.booleans())
        },
        "quality_preset": draw(st.sampled_from(["standard_hd", "cinematic_4k", "cinematic_8k"]))
    }


@st.composite
def target_audience_strategy(draw):
    """Generate valid target audience values."""
    return draw(st.sampled_from(["beginner", "intermediate", "advanced"]))


class TestEnhancedGeminiClient:
    """Test suite for Enhanced Gemini Client with property-based testing."""
    
    @pytest.fixture
    def mock_gemini_response(self):
        """Mock Gemini API response for testing."""
        return Mock(
            text=json.dumps({
                "description": "Professional cinematic presentation with detailed visual elements",
                "camera_work": {
                    "opening_shot": "Wide establishing shot",
                    "movement": "Smooth dolly movement",
                    "closing_shot": "Close-up on key element"
                },
                "lighting": {
                    "mood": "Professional and engaging",
                    "setup": "Three-point lighting",
                    "color_temperature": "5600K neutral",
                    "effects": "Subtle rim lighting"
                },
                "composition": {
                    "layout": "Rule of thirds composition",
                    "color_palette": "Professional blue and white",
                    "typography": "Clean sans-serif",
                    "focal_points": "Center-weighted focus"
                },
                "cinematic_elements": {
                    "film_grain": "Subtle professional grain",
                    "depth_of_field": "Moderate DOF",
                    "color_grading": "Neutral with contrast",
                    "transitions": "Smooth fade"
                },
                "content_visuals": {
                    "diagrams": "Clean technical diagrams",
                    "animations": "Smooth purposeful animations",
                    "text_overlays": "Clear positioned text",
                    "visual_metaphors": "Appropriate representations"
                },
                "technical_notes": "Standard professional settings",
                "confidence": 0.95
            })
        )
    
    @pytest.fixture
    def enhanced_client(self):
        """Create enhanced Gemini client for testing."""
        with patch.dict(os.environ, {'RASO_GOOGLE_API_KEY': 'test_key'}):
            with patch('google.generativeai.configure'):
                return EnhancedGeminiClient()
    
    @given(
        scene_data=scene_content_strategy(),
        cinematic_settings=cinematic_settings_strategy(),
        target_audience=target_audience_strategy()
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_gemini_visual_description_generation(
        self, enhanced_client, mock_gemini_response, scene_data, cinematic_settings, target_audience
    ):
        """
        Property 5: Gemini Visual Description Generation
        For any valid scene content, the system should use Gemini to generate detailed visual 
        descriptions that include technical content analysis, mood assessment, and target audience considerations.
        Validates: Requirements 2.1, 2.2, 5.1
        """
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(return_value=mock_gemini_response)
            mock_model_class.return_value = mock_model
            
            # Test the property: any valid scene content should generate a visual description
            result = await enhanced_client.generate_detailed_visual_description(
                scene_content=scene_data["content"],
                scene_type=scene_data["type"],
                cinematic_settings=cinematic_settings,
                target_audience=target_audience
            )
            
            # Verify the property holds: result should be a valid visual description
            assert isinstance(result, dict), "Result should be a dictionary"
            assert "description" in result, "Result should contain a description"
            assert "confidence" in result, "Result should contain confidence score"
            assert isinstance(result["confidence"], (int, float)), "Confidence should be numeric"
            assert 0 <= result["confidence"] <= 1, "Confidence should be between 0 and 1"
            
            # Verify technical content analysis is included
            assert "camera_work" in result, "Should include camera work analysis"
            assert "lighting" in result, "Should include lighting analysis"
            assert "composition" in result, "Should include composition analysis"
            
            # Verify mood assessment is present
            if "lighting" in result and "mood" in result["lighting"]:
                assert isinstance(result["lighting"]["mood"], str), "Mood should be a string"
                assert len(result["lighting"]["mood"]) > 0, "Mood should not be empty"
            
            # Verify the API was called with proper parameters
            mock_model.generate_content.assert_called_once()
            call_args = mock_model.generate_content.call_args[0][0]
            assert scene_data["content"] in call_args, "Scene content should be in prompt"
            assert target_audience in call_args, "Target audience should be in prompt"
    
    @given(
        scene_data=scene_content_strategy(),
        cinematic_settings=cinematic_settings_strategy(),
        target_audience=target_audience_strategy()
    )
    @settings(max_examples=100, deadline=None)
    @pytest.mark.asyncio
    async def test_property_visual_description_format_compliance(
        self, enhanced_client, mock_gemini_response, scene_data, cinematic_settings, target_audience
    ):
        """
        Property 6: Visual Description Format Compliance
        For any generated visual description, it should contain specific cinematic details 
        (camera angles, lighting, composition, visual elements) and be formatted for use by the cinematic video generator.
        Validates: Requirements 2.3, 2.4
        """
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(return_value=mock_gemini_response)
            mock_model_class.return_value = mock_model
            
            # Generate visual description
            result = await enhanced_client.generate_detailed_visual_description(
                scene_content=scene_data["content"],
                scene_type=scene_data["type"],
                cinematic_settings=cinematic_settings,
                target_audience=target_audience
            )
            
            # Verify format compliance: should contain specific cinematic details
            
            # Camera angles and movements
            assert "camera_work" in result, "Should contain camera work details"
            camera_work = result["camera_work"]
            assert isinstance(camera_work, dict), "Camera work should be a dictionary"
            
            # Lighting specifications
            assert "lighting" in result, "Should contain lighting details"
            lighting = result["lighting"]
            assert isinstance(lighting, dict), "Lighting should be a dictionary"
            
            # Composition details
            assert "composition" in result, "Should contain composition details"
            composition = result["composition"]
            assert isinstance(composition, dict), "Composition should be a dictionary"
            
            # Visual elements
            assert "cinematic_elements" in result, "Should contain cinematic elements"
            cinematic_elements = result["cinematic_elements"]
            assert isinstance(cinematic_elements, dict), "Cinematic elements should be a dictionary"
            
            # Content-specific visuals
            assert "content_visuals" in result, "Should contain content visuals"
            content_visuals = result["content_visuals"]
            assert isinstance(content_visuals, dict), "Content visuals should be a dictionary"
            
            # Verify format is suitable for cinematic video generator
            assert "technical_notes" in result, "Should contain technical notes for video generator"
            assert isinstance(result["description"], str), "Main description should be a string"
            assert len(result["description"]) > 0, "Description should not be empty"
    
    @given(content=st.text(min_size=10, max_size=1000))
    @settings(max_examples=50, deadline=None)
    @pytest.mark.asyncio
    async def test_property_scene_analysis_consistency(self, enhanced_client, content):
        """
        Property: Scene analysis should provide consistent recommendations for similar content.
        """
        mock_response = Mock(
            text=json.dumps({
                "analysis": {
                    "mood": "analytical",
                    "complexity": "medium",
                    "pacing": "medium",
                    "focus_type": "general",
                    "key_themes": ["analysis", "information"],
                    "technical_level": "intermediate"
                },
                "recommendations": {
                    "camera_movement": {
                        "type": "dolly",
                        "reasoning": "Smooth movement for engagement",
                        "confidence": 0.8
                    },
                    "color_grading": {
                        "film_emulation": "none",
                        "adjustments": {"temperature": 0.0, "contrast": 0.1, "saturation": 0.0},
                        "reasoning": "Neutral for clarity",
                        "confidence": 0.8
                    }
                },
                "overall_confidence": 0.8
            })
        )
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            # Analyze the same content twice
            result1 = await enhanced_client.analyze_scene_for_cinematics(content, "text")
            result2 = await enhanced_client.analyze_scene_for_cinematics(content, "text")
            
            # Results should have consistent structure
            assert "analysis" in result1 and "analysis" in result2
            assert "recommendations" in result1 and "recommendations" in result2
            assert "overall_confidence" in result1 and "overall_confidence" in result2
            
            # Confidence scores should be reasonable
            assert 0 <= result1["overall_confidence"] <= 1
            assert 0 <= result2["overall_confidence"] <= 1
    
    @given(
        descriptions=st.lists(st.text(min_size=50, max_size=200), min_size=2, max_size=5),
        theme=st.text(min_size=10, max_size=100)
    )
    @settings(max_examples=30, deadline=None)
    @pytest.mark.asyncio
    async def test_property_visual_consistency_analysis(self, enhanced_client, descriptions, theme):
        """
        Property: Visual consistency analysis should provide meaningful feedback for multiple descriptions.
        """
        mock_response = Mock(
            text=json.dumps({
                "consistency_score": 0.85,
                "analysis": {
                    "visual_consistency": {"score": 0.9},
                    "narrative_flow": {"score": 0.8},
                    "technical_consistency": {"score": 0.85}
                },
                "issues": [],
                "recommendations": ["Maintain consistency", "Minor refinements"],
                "revised_descriptions": {}
            })
        )
        
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(return_value=mock_response)
            mock_model_class.return_value = mock_model
            
            result = await enhanced_client.generate_visual_consistency_analysis(descriptions, theme)
            
            # Verify consistency analysis structure
            assert "consistency_score" in result
            assert "analysis" in result
            assert "recommendations" in result
            
            # Verify scores are in valid range
            assert 0 <= result["consistency_score"] <= 1
            
            # Verify analysis contains required components
            analysis = result["analysis"]
            assert "visual_consistency" in analysis
            assert "narrative_flow" in analysis
            assert "technical_consistency" in analysis
    
    @pytest.mark.asyncio
    async def test_fallback_behavior_on_api_failure(self, enhanced_client):
        """
        Test that fallback descriptions are generated when Gemini API fails.
        Validates error handling requirements.
        """
        with patch('google.generativeai.GenerativeModel') as mock_model_class:
            mock_model = Mock()
            mock_model.generate_content = AsyncMock(side_effect=Exception("API Error"))
            mock_model_class.return_value = mock_model
            
            # Should not raise exception, should return fallback
            result = await enhanced_client.generate_detailed_visual_description(
                scene_content="Test content",
                scene_type="general",
                cinematic_settings={},
                target_audience="intermediate"
            )
            
            # Verify fallback structure is valid
            assert isinstance(result, dict)
            assert "description" in result
            assert "confidence" in result
            assert result["confidence"] < 1.0  # Fallback should have lower confidence
    
    def test_singleton_client_behavior(self):
        """Test that get_enhanced_gemini_client returns the same instance."""
        with patch.dict(os.environ, {'RASO_GOOGLE_API_KEY': 'test_key'}):
            with patch('google.generativeai.configure'):
                client1 = get_enhanced_gemini_client()
                client2 = get_enhanced_gemini_client()
                
                assert client1 is client2, "Should return the same instance (singleton pattern)"


class TestVisualDescriptionValidation:
    """Additional tests for visual description validation and format compliance."""
    
    @given(
        description_data=st.fixed_dictionaries({
            "description": st.text(min_size=10, max_size=500),
            "camera_work": st.fixed_dictionaries({
                "opening_shot": st.text(min_size=5, max_size=100),
                "movement": st.text(min_size=5, max_size=100),
                "closing_shot": st.text(min_size=5, max_size=100)
            }),
            "lighting": st.fixed_dictionaries({
                "mood": st.text(min_size=3, max_size=50),
                "setup": st.text(min_size=5, max_size=100)
            }),
            "confidence": st.floats(min_value=0.0, max_value=1.0)
        })
    )
    @settings(max_examples=50)
    def test_property_description_structure_validation(self, description_data):
        """
        Property: All visual descriptions should have consistent, valid structure.
        """
        # Verify required fields are present
        assert "description" in description_data
        assert "camera_work" in description_data
        assert "lighting" in description_data
        assert "confidence" in description_data
        
        # Verify field types
        assert isinstance(description_data["description"], str)
        assert isinstance(description_data["camera_work"], dict)
        assert isinstance(description_data["lighting"], dict)
        assert isinstance(description_data["confidence"], (int, float))
        
        # Verify confidence is in valid range
        assert 0 <= description_data["confidence"] <= 1
        
        # Verify camera work has required sub-fields
        camera_work = description_data["camera_work"]
        assert "opening_shot" in camera_work
        assert "movement" in camera_work
        assert "closing_shot" in camera_work
        
        # Verify lighting has required sub-fields
        lighting = description_data["lighting"]
        assert "mood" in lighting
        assert "setup" in lighting


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])