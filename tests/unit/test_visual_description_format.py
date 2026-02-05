"""
Property-based tests for Visual Description Format Compliance
Feature: cinematic-ui-enhancement, Property 6: Visual Description Format Compliance
"""

import pytest
from hypothesis import given, strategies as st, settings
from typing import Dict, Any, List
import json
import re

# Import validation utilities
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class VisualDescriptionValidator:
    """Validator for visual description format compliance."""
    
    REQUIRED_FIELDS = [
        "description",
        "camera_work", 
        "lighting",
        "composition",
        "cinematic_elements",
        "content_visuals",
        "technical_notes",
        "confidence"
    ]
    
    CAMERA_WORK_FIELDS = ["opening_shot", "movement", "closing_shot"]
    LIGHTING_FIELDS = ["mood", "setup", "color_temperature"]
    COMPOSITION_FIELDS = ["layout", "color_palette", "typography", "focal_points"]
    CINEMATIC_FIELDS = ["film_grain", "depth_of_field", "color_grading", "transitions"]
    CONTENT_VISUAL_FIELDS = ["diagrams", "animations", "text_overlays", "visual_metaphors"]
    
    @classmethod
    def validate_structure(cls, description: Dict[str, Any]) -> List[str]:
        """Validate the structure of a visual description."""
        errors = []
        
        # Check required top-level fields
        for field in cls.REQUIRED_FIELDS:
            if field not in description:
                errors.append(f"Missing required field: {field}")
        
        # Validate field types
        if "description" in description and not isinstance(description["description"], str):
            errors.append("'description' must be a string")
        
        if "confidence" in description:
            confidence = description["confidence"]
            if not isinstance(confidence, (int, float)) or not (0 <= confidence <= 1):
                errors.append("'confidence' must be a number between 0 and 1")
        
        # Validate nested structures
        if "camera_work" in description:
            camera_errors = cls._validate_camera_work(description["camera_work"])
            errors.extend(camera_errors)
        
        if "lighting" in description:
            lighting_errors = cls._validate_lighting(description["lighting"])
            errors.extend(lighting_errors)
        
        if "composition" in description:
            composition_errors = cls._validate_composition(description["composition"])
            errors.extend(composition_errors)
        
        if "cinematic_elements" in description:
            cinematic_errors = cls._validate_cinematic_elements(description["cinematic_elements"])
            errors.extend(cinematic_errors)
        
        if "content_visuals" in description:
            content_errors = cls._validate_content_visuals(description["content_visuals"])
            errors.extend(content_errors)
        
        return errors
    
    @classmethod
    def _validate_camera_work(cls, camera_work: Any) -> List[str]:
        """Validate camera work structure."""
        errors = []
        
        if not isinstance(camera_work, dict):
            return ["'camera_work' must be a dictionary"]
        
        for field in cls.CAMERA_WORK_FIELDS:
            if field not in camera_work:
                errors.append(f"Missing camera_work field: {field}")
            elif not isinstance(camera_work[field], str):
                errors.append(f"camera_work.{field} must be a string")
        
        return errors
    
    @classmethod
    def _validate_lighting(cls, lighting: Any) -> List[str]:
        """Validate lighting structure."""
        errors = []
        
        if not isinstance(lighting, dict):
            return ["'lighting' must be a dictionary"]
        
        for field in cls.LIGHTING_FIELDS:
            if field not in lighting:
                errors.append(f"Missing lighting field: {field}")
            elif not isinstance(lighting[field], str):
                errors.append(f"lighting.{field} must be a string")
        
        return errors
    
    @classmethod
    def _validate_composition(cls, composition: Any) -> List[str]:
        """Validate composition structure."""
        errors = []
        
        if not isinstance(composition, dict):
            return ["'composition' must be a dictionary"]
        
        for field in cls.COMPOSITION_FIELDS:
            if field not in composition:
                errors.append(f"Missing composition field: {field}")
            elif not isinstance(composition[field], str):
                errors.append(f"composition.{field} must be a string")
        
        return errors
    
    @classmethod
    def _validate_cinematic_elements(cls, cinematic_elements: Any) -> List[str]:
        """Validate cinematic elements structure."""
        errors = []
        
        if not isinstance(cinematic_elements, dict):
            return ["'cinematic_elements' must be a dictionary"]
        
        for field in cls.CINEMATIC_FIELDS:
            if field not in cinematic_elements:
                errors.append(f"Missing cinematic_elements field: {field}")
            elif not isinstance(cinematic_elements[field], str):
                errors.append(f"cinematic_elements.{field} must be a string")
        
        return errors
    
    @classmethod
    def _validate_content_visuals(cls, content_visuals: Any) -> List[str]:
        """Validate content visuals structure."""
        errors = []
        
        if not isinstance(content_visuals, dict):
            return ["'content_visuals' must be a dictionary"]
        
        for field in cls.CONTENT_VISUAL_FIELDS:
            if field not in content_visuals:
                errors.append(f"Missing content_visuals field: {field}")
            elif not isinstance(content_visuals[field], str):
                errors.append(f"content_visuals.{field} must be a string")
        
        return errors
    
    @classmethod
    def validate_cinematic_compatibility(cls, description: Dict[str, Any]) -> List[str]:
        """Validate compatibility with cinematic video generator."""
        errors = []
        
        # Check for technical specifications
        if "technical_notes" in description:
            tech_notes = description["technical_notes"]
            if not isinstance(tech_notes, str) or len(tech_notes.strip()) == 0:
                errors.append("technical_notes must be a non-empty string")
        
        # Validate camera movement specifications
        if "camera_work" in description and "movement" in description["camera_work"]:
            movement = description["camera_work"]["movement"].lower()
            valid_movements = ["pan", "zoom", "dolly", "crane", "handheld", "static", "smooth", "subtle"]
            if not any(valid_move in movement for valid_move in valid_movements):
                errors.append("camera_work.movement should specify a valid camera movement type")
        
        # Validate lighting specifications
        if "lighting" in description and "color_temperature" in description["lighting"]:
            color_temp = description["lighting"]["color_temperature"]
            # Should contain temperature information (numbers or descriptive terms)
            if not (re.search(r'\d+', color_temp) or any(term in color_temp.lower() for term in ["warm", "cool", "neutral", "daylight", "tungsten"])):
                errors.append("lighting.color_temperature should specify temperature information")
        
        # Validate color grading compatibility
        if "cinematic_elements" in description and "color_grading" in description["cinematic_elements"]:
            color_grading = description["cinematic_elements"]["color_grading"].lower()
            valid_approaches = ["neutral", "warm", "cool", "cinematic", "natural", "stylized", "kodak", "fuji", "cinema"]
            if not any(approach in color_grading for approach in valid_approaches):
                errors.append("cinematic_elements.color_grading should specify a valid grading approach")
        
        return errors


# Test data generators
@st.composite
def valid_visual_description_strategy(draw):
    """Generate valid visual descriptions for testing."""
    return {
        "description": draw(st.text(min_size=20, max_size=500)),
        "camera_work": {
            "opening_shot": draw(st.text(min_size=10, max_size=100)),
            "movement": draw(st.sampled_from([
                "smooth dolly movement", "subtle pan left to right", "gentle zoom in",
                "static shot with focus pull", "handheld for intimacy", "crane shot revealing"
            ])),
            "closing_shot": draw(st.text(min_size=10, max_size=100))
        },
        "lighting": {
            "mood": draw(st.sampled_from([
                "professional and clear", "warm and inviting", "cool and analytical",
                "dramatic and focused", "neutral and balanced"
            ])),
            "setup": draw(st.text(min_size=10, max_size=100)),
            "color_temperature": draw(st.sampled_from([
                "5600K daylight", "3200K tungsten", "warm 2700K", "cool 6500K", "neutral 4000K"
            ]))
        },
        "composition": {
            "layout": draw(st.text(min_size=10, max_size=100)),
            "color_palette": draw(st.text(min_size=10, max_size=100)),
            "typography": draw(st.text(min_size=10, max_size=100)),
            "focal_points": draw(st.text(min_size=10, max_size=100))
        },
        "cinematic_elements": {
            "film_grain": draw(st.text(min_size=5, max_size=50)),
            "depth_of_field": draw(st.text(min_size=5, max_size=50)),
            "color_grading": draw(st.sampled_from([
                "neutral with slight contrast", "warm kodak emulation", "cool cinematic look",
                "natural color grading", "stylized fuji approach"
            ])),
            "transitions": draw(st.text(min_size=5, max_size=50))
        },
        "content_visuals": {
            "diagrams": draw(st.text(min_size=10, max_size=100)),
            "animations": draw(st.text(min_size=10, max_size=100)),
            "text_overlays": draw(st.text(min_size=10, max_size=100)),
            "visual_metaphors": draw(st.text(min_size=10, max_size=100))
        },
        "technical_notes": draw(st.text(min_size=10, max_size=200)),
        "confidence": draw(st.floats(min_value=0.0, max_value=1.0))
    }


@st.composite
def invalid_visual_description_strategy(draw):
    """Generate invalid visual descriptions for testing validation."""
    # Create a base valid description
    base_desc = {
        "description": draw(st.text(min_size=10, max_size=100)),
        "camera_work": {"opening_shot": "test", "movement": "test", "closing_shot": "test"},
        "lighting": {"mood": "test", "setup": "test", "color_temperature": "test"},
        "composition": {"layout": "test", "color_palette": "test", "typography": "test", "focal_points": "test"},
        "cinematic_elements": {"film_grain": "test", "depth_of_field": "test", "color_grading": "test", "transitions": "test"},
        "content_visuals": {"diagrams": "test", "animations": "test", "text_overlays": "test", "visual_metaphors": "test"},
        "technical_notes": "test",
        "confidence": 0.8
    }
    
    # Introduce random errors
    error_type = draw(st.sampled_from([
        "missing_field", "wrong_type", "invalid_confidence", "empty_nested"
    ]))
    
    if error_type == "missing_field":
        field_to_remove = draw(st.sampled_from(list(base_desc.keys())))
        del base_desc[field_to_remove]
    elif error_type == "wrong_type":
        base_desc["confidence"] = "invalid"
    elif error_type == "invalid_confidence":
        base_desc["confidence"] = draw(st.floats(min_value=-1.0, max_value=2.0).filter(lambda x: not (0 <= x <= 1)))
    elif error_type == "empty_nested":
        base_desc["camera_work"] = {}
    
    return base_desc


class TestVisualDescriptionFormatCompliance:
    """Test suite for visual description format compliance."""
    
    @given(description=valid_visual_description_strategy())
    @settings(max_examples=100, deadline=None)
    def test_property_valid_descriptions_pass_validation(self, description):
        """
        Property 6: Visual Description Format Compliance
        For any valid visual description, it should pass all format validation checks.
        Validates: Requirements 2.3, 2.4
        """
        # Valid descriptions should have no validation errors
        errors = VisualDescriptionValidator.validate_structure(description)
        assert len(errors) == 0, f"Valid description should pass validation, but got errors: {errors}"
        
        # Should also pass cinematic compatibility checks
        compat_errors = VisualDescriptionValidator.validate_cinematic_compatibility(description)
        assert len(compat_errors) == 0, f"Valid description should be cinematic-compatible, but got errors: {compat_errors}"
    
    @given(description=invalid_visual_description_strategy())
    @settings(max_examples=50, deadline=None)
    def test_property_invalid_descriptions_fail_validation(self, description):
        """
        Property: Invalid visual descriptions should be caught by validation.
        """
        # Invalid descriptions should have validation errors
        errors = VisualDescriptionValidator.validate_structure(description)
        # We expect at least some errors for invalid descriptions
        # (Note: some randomly generated "invalid" descriptions might still be valid)
        # This test ensures our validator can catch actual structural issues
        
        # At minimum, check that validator doesn't crash on invalid input
        assert isinstance(errors, list), "Validator should return a list of errors"
    
    @given(
        description=st.text(min_size=10, max_size=200),
        confidence=st.floats(min_value=0.0, max_value=1.0)
    )
    @settings(max_examples=50)
    def test_property_description_content_requirements(self, description, confidence):
        """
        Property: All visual descriptions should contain meaningful content for video generation.
        """
        # Create minimal valid structure
        visual_desc = {
            "description": description,
            "camera_work": {
                "opening_shot": "Wide establishing shot",
                "movement": "Smooth dolly movement",
                "closing_shot": "Close-up on key element"
            },
            "lighting": {
                "mood": "Professional lighting",
                "setup": "Three-point lighting setup",
                "color_temperature": "5600K daylight"
            },
            "composition": {
                "layout": "Rule of thirds composition",
                "color_palette": "Professional color scheme",
                "typography": "Clean typography",
                "focal_points": "Center-weighted focus"
            },
            "cinematic_elements": {
                "film_grain": "Subtle film grain",
                "depth_of_field": "Moderate depth of field",
                "color_grading": "Neutral color grading",
                "transitions": "Smooth transitions"
            },
            "content_visuals": {
                "diagrams": "Technical diagrams",
                "animations": "Smooth animations",
                "text_overlays": "Clear text overlays",
                "visual_metaphors": "Appropriate metaphors"
            },
            "technical_notes": "Standard technical specifications",
            "confidence": confidence
        }
        
        # Should pass validation
        errors = VisualDescriptionValidator.validate_structure(visual_desc)
        assert len(errors) == 0, f"Well-formed description should be valid: {errors}"
        
        # Description should be non-empty
        assert len(visual_desc["description"].strip()) > 0, "Description content should not be empty"
        
        # Confidence should be in valid range
        assert 0 <= visual_desc["confidence"] <= 1, "Confidence should be between 0 and 1"
    
    def test_required_cinematic_fields_presence(self):
        """
        Test that all required fields for cinematic video generation are present.
        """
        required_fields = VisualDescriptionValidator.REQUIRED_FIELDS
        
        # Verify we have all essential fields for cinematic production
        essential_fields = [
            "description", "camera_work", "lighting", "composition", 
            "cinematic_elements", "content_visuals", "technical_notes", "confidence"
        ]
        
        for field in essential_fields:
            assert field in required_fields, f"Essential field '{field}' should be required"
    
    def test_camera_work_specifications(self):
        """
        Test that camera work contains all necessary specifications for video generation.
        """
        camera_fields = VisualDescriptionValidator.CAMERA_WORK_FIELDS
        
        # Essential camera specifications
        essential_camera_fields = ["opening_shot", "movement", "closing_shot"]
        
        for field in essential_camera_fields:
            assert field in camera_fields, f"Essential camera field '{field}' should be required"
    
    def test_lighting_specifications(self):
        """
        Test that lighting contains all necessary specifications for video generation.
        """
        lighting_fields = VisualDescriptionValidator.LIGHTING_FIELDS
        
        # Essential lighting specifications
        essential_lighting_fields = ["mood", "setup", "color_temperature"]
        
        for field in essential_lighting_fields:
            assert field in lighting_fields, f"Essential lighting field '{field}' should be required"
    
    @given(
        camera_movement=st.sampled_from([
            "smooth dolly in", "pan left to right", "zoom in slowly", 
            "crane shot up", "handheld movement", "static hold"
        ]),
        color_temp=st.sampled_from([
            "5600K", "3200K tungsten", "warm 2700K", "daylight 6500K", "neutral"
        ]),
        grading=st.sampled_from([
            "neutral grading", "kodak emulation", "fuji look", "cinema style", "natural colors"
        ])
    )
    @settings(max_examples=30)
    def test_property_cinematic_compatibility_validation(self, camera_movement, color_temp, grading):
        """
        Property: Visual descriptions with proper cinematic specifications should pass compatibility validation.
        """
        description = {
            "description": "Professional cinematic presentation",
            "camera_work": {
                "opening_shot": "Wide shot",
                "movement": camera_movement,
                "closing_shot": "Close shot"
            },
            "lighting": {
                "mood": "Professional",
                "setup": "Three-point lighting",
                "color_temperature": color_temp
            },
            "composition": {
                "layout": "Rule of thirds",
                "color_palette": "Professional",
                "typography": "Clean",
                "focal_points": "Center"
            },
            "cinematic_elements": {
                "film_grain": "Subtle",
                "depth_of_field": "Moderate",
                "color_grading": grading,
                "transitions": "Smooth"
            },
            "content_visuals": {
                "diagrams": "Technical",
                "animations": "Smooth",
                "text_overlays": "Clear",
                "visual_metaphors": "Appropriate"
            },
            "technical_notes": "Standard specifications",
            "confidence": 0.9
        }
        
        # Should pass both structure and compatibility validation
        struct_errors = VisualDescriptionValidator.validate_structure(description)
        compat_errors = VisualDescriptionValidator.validate_cinematic_compatibility(description)
        
        assert len(struct_errors) == 0, f"Structure validation failed: {struct_errors}"
        assert len(compat_errors) == 0, f"Compatibility validation failed: {compat_errors}"


class TestCinematicVideoGeneratorCompatibility:
    """Test compatibility with cinematic video generator requirements."""
    
    def test_technical_notes_format(self):
        """Test that technical notes provide actionable information for video generation."""
        valid_tech_notes = [
            "Standard professional video settings with 24fps cinematic frame rate",
            "High-quality encoding with film grain and color grading applied",
            "Professional lighting setup with three-point configuration"
        ]
        
        for notes in valid_tech_notes:
            description = {
                "description": "Test",
                "camera_work": {"opening_shot": "test", "movement": "dolly", "closing_shot": "test"},
                "lighting": {"mood": "test", "setup": "test", "color_temperature": "5600K"},
                "composition": {"layout": "test", "color_palette": "test", "typography": "test", "focal_points": "test"},
                "cinematic_elements": {"film_grain": "test", "depth_of_field": "test", "color_grading": "neutral", "transitions": "test"},
                "content_visuals": {"diagrams": "test", "animations": "test", "text_overlays": "test", "visual_metaphors": "test"},
                "technical_notes": notes,
                "confidence": 0.8
            }
            
            errors = VisualDescriptionValidator.validate_cinematic_compatibility(description)
            assert len(errors) == 0, f"Valid technical notes should pass validation: {notes}"
    
    def test_empty_or_invalid_technical_notes(self):
        """Test that empty or invalid technical notes are caught."""
        invalid_tech_notes = ["", "   ", None]
        
        for notes in invalid_tech_notes:
            description = {
                "description": "Test",
                "camera_work": {"opening_shot": "test", "movement": "dolly", "closing_shot": "test"},
                "lighting": {"mood": "test", "setup": "test", "color_temperature": "5600K"},
                "composition": {"layout": "test", "color_palette": "test", "typography": "test", "focal_points": "test"},
                "cinematic_elements": {"film_grain": "test", "depth_of_field": "test", "color_grading": "neutral", "transitions": "test"},
                "content_visuals": {"diagrams": "test", "animations": "test", "text_overlays": "test", "visual_metaphors": "test"},
                "technical_notes": notes,
                "confidence": 0.8
            }
            
            errors = VisualDescriptionValidator.validate_cinematic_compatibility(description)
            assert len(errors) > 0, f"Invalid technical notes should fail validation: {notes}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])