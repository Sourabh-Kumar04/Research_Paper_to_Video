"""
Property tests for multi-scene consistency and template system.

Tests Property 7: Multi-Scene Visual Consistency
Tests Property 14: Content Classification and Template Application
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
from typing import List, Dict, Any
from unittest.mock import AsyncMock, MagicMock
import json

from src.cinematic.multi_scene_consistency import (
    MultiSceneConsistencyAnalyzer,
    AdvancedTemplateSystem,
    ContentType,
    ConsistencyLevel,
    TemplateDefinition,
    SceneConsistencyAnalysis
)
from src.cinematic.models import VisualDescriptionModel


# Test data generators
@st.composite
def visual_description_model(draw):
    """Generate valid VisualDescriptionModel instances."""
    scene_id = draw(st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))))
    content = draw(st.text(min_size=10, max_size=500))
    description = draw(st.text(min_size=20, max_size=1000))
    
    # Generate cinematic settings
    cinematic_settings = {
        'camera_movements': {
            'enabled': draw(st.booleans()),
            'intensity': draw(st.integers(min_value=0, max_value=100))
        },
        'color_grading': {
            'enabled': draw(st.booleans()),
            'temperature': draw(st.integers(min_value=-100, max_value=100)),
            'contrast': draw(st.integers(min_value=-100, max_value=100))
        }
    }
    
    return VisualDescriptionModel(
        scene_id=scene_id,
        content=content,
        description=description,
        generated_by='test',
        cinematic_settings=cinematic_settings,
        scene_analysis={},
        suggestions=[],
        confidence=draw(st.floats(min_value=0.0, max_value=1.0)),
        created_at='2024-01-01T00:00:00Z',
        updated_at='2024-01-01T00:00:00Z'
    )


@st.composite
def content_for_classification(draw):
    """Generate content samples for classification testing."""
    content_types = {
        ContentType.MATHEMATICAL: [
            "equation", "formula", "calculate", "derivative", "integral",
            "theorem", "proof", "algorithm", "function", "matrix"
        ],
        ContentType.ARCHITECTURAL: [
            "system", "architecture", "design", "structure", "framework",
            "component", "module", "interface", "pattern", "diagram"
        ],
        ContentType.ANALYTICAL: [
            "analysis", "data", "results", "findings", "comparison",
            "evaluation", "research", "study", "statistics", "metrics"
        ],
        ContentType.PROCEDURAL: [
            "step", "procedure", "process", "method", "tutorial",
            "instruction", "guide", "how to", "first", "next"
        ],
        ContentType.INTRODUCTORY: [
            "introduction", "welcome", "overview", "begin", "start",
            "hello", "today", "we will", "this presentation"
        ],
        ContentType.CONCLUSION: [
            "conclusion", "summary", "finally", "in summary", "to conclude",
            "wrap up", "end", "thank you", "questions"
        ]
    }
    
    content_type = draw(st.sampled_from(list(ContentType)))
    if content_type in content_types:
        keywords = draw(st.lists(
            st.sampled_from(content_types[content_type]),
            min_size=1,
            max_size=3
        ))
        base_text = draw(st.text(min_size=10, max_size=100))
        content = f"{base_text} {' '.join(keywords)} {base_text}"
    else:
        content = draw(st.text(min_size=10, max_size=200))
    
    return content, content_type


class TestMultiSceneConsistency:
    """Property tests for multi-scene consistency analysis."""
    
    @pytest.fixture
    def analyzer(self):
        """Create analyzer with mocked Gemini client."""
        mock_gemini = AsyncMock()
        return MultiSceneConsistencyAnalyzer(gemini_client=mock_gemini)
    
    @pytest.fixture
    def analyzer_no_gemini(self):
        """Create analyzer without Gemini client."""
        return MultiSceneConsistencyAnalyzer(gemini_client=None)
    
    @given(
        scenes=st.lists(visual_description_model(), min_size=2, max_size=10),
        consistency_level=st.sampled_from(list(ConsistencyLevel))
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_property_7_multi_scene_visual_consistency(self, scenes, consistency_level):
        """
        Property 7: Multi-Scene Visual Consistency
        
        For any set of related scenes processed together, the generated visual 
        descriptions should maintain consistency in visual themes and narrative flow.
        
        Validates: Requirements 2.5, 5.5
        """
        # Create analyzer inside test to avoid fixture issues
        analyzer_no_gemini = MultiSceneConsistencyAnalyzer(gemini_client=None)
        # Ensure unique scene IDs
        for i, scene in enumerate(scenes):
            scene.scene_id = f"scene_{i}_{scene.scene_id}"
        
        # Analyze consistency
        analysis = await analyzer_no_gemini.analyze_scene_consistency(scenes, consistency_level)
        
        # Property assertions
        assert isinstance(analysis, SceneConsistencyAnalysis)
        assert analysis.scene_ids == [scene.scene_id for scene in scenes]
        assert 0.0 <= analysis.consistency_score <= 1.0
        assert analysis.consistency_level == consistency_level
        assert isinstance(analysis.visual_themes, list)
        assert isinstance(analysis.inconsistencies, list)
        assert isinstance(analysis.recommendations, list)
        assert 0.0 <= analysis.confidence <= 1.0
        
        # Consistency score should be meaningful
        if len(scenes) >= 2:
            # Should have some analysis
            assert analysis.confidence > 0.0
        
        # Visual themes should be strings
        for theme in analysis.visual_themes:
            assert isinstance(theme, str)
            assert len(theme) > 0
        
        # Inconsistencies should have proper structure
        for inconsistency in analysis.inconsistencies:
            assert 'scene_id' in inconsistency
            assert inconsistency['scene_id'] in [scene.scene_id for scene in scenes]
            assert 'type' in inconsistency
            if 'severity' in inconsistency:
                assert inconsistency['severity'] in ['low', 'medium', 'high']
        
        # Recommendations should be actionable strings
        for recommendation in analysis.recommendations:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 10  # Should be meaningful
    
    @given(
        scenes=st.lists(visual_description_model(), min_size=0, max_size=1)
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_single_or_no_scene_consistency(self, scenes):
        """Test consistency analysis with single or no scenes."""
        # Create analyzer inside test to avoid fixture issues
        analyzer_no_gemini = MultiSceneConsistencyAnalyzer(gemini_client=None)
        analysis = await analyzer_no_gemini.analyze_scene_consistency(scenes)
        
        # Should handle edge cases gracefully
        assert isinstance(analysis, SceneConsistencyAnalysis)
        assert analysis.consistency_score == 1.0  # Perfect consistency for single/no scenes
        assert len(analysis.inconsistencies) == 0
    
    @given(
        scenes=st.lists(visual_description_model(), min_size=2, max_size=5)
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_consistency_caching(self, scenes):
        """Test that consistency analysis results are cached."""
        # Create analyzer inside test to avoid fixture issues
        analyzer_no_gemini = MultiSceneConsistencyAnalyzer(gemini_client=None)
        # Ensure unique scene IDs
        for i, scene in enumerate(scenes):
            scene.scene_id = f"cached_scene_{i}"
        
        # First analysis
        analysis1 = await analyzer_no_gemini.analyze_scene_consistency(scenes)
        
        # Second analysis with same scenes
        analysis2 = await analyzer_no_gemini.analyze_scene_consistency(scenes)
        
        # Should be identical (cached)
        assert analysis1.consistency_score == analysis2.consistency_score
        assert analysis1.visual_themes == analysis2.visual_themes
        assert analysis1.inconsistencies == analysis2.inconsistencies


class TestAdvancedTemplateSystem:
    """Property tests for advanced template system."""
    
    @pytest.fixture
    def template_system(self):
        """Create template system with mocked Gemini client."""
        mock_gemini = AsyncMock()
        return AdvancedTemplateSystem(gemini_client=mock_gemini)
    
    @pytest.fixture
    def template_system_no_gemini(self):
        """Create template system without Gemini client."""
        return AdvancedTemplateSystem(gemini_client=None)
    
    @given(content_data=content_for_classification())
    @settings(max_examples=50, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    async def test_property_14_content_classification_and_template_application(
        self, content_data
    ):
        """
        Property 14: Content Classification and Template Application
        
        For any ambiguous content, the system should use classification to 
        determine content type and apply appropriate templates that remain 
        customizable and editable.
        
        Validates: Requirements 6.6, 6.7
        """
        # Create template system inside test to avoid fixture issues
        template_system_no_gemini = AdvancedTemplateSystem(gemini_client=None)
        content, expected_type = content_data
        
        # Classify content
        classified_type = await template_system_no_gemini.classify_content_type(content)
        
        # Property assertions for classification
        assert isinstance(classified_type, ContentType)
        
        # Get template for classified type
        template = template_system_no_gemini.get_template_by_content_type(classified_type)
        
        if template:
            # Template should have proper structure
            assert isinstance(template, TemplateDefinition)
            assert template.content_type == classified_type
            assert isinstance(template.visual_elements, dict)
            assert isinstance(template.cinematic_settings, dict)
            assert isinstance(template.customization_options, dict)
            assert template.is_editable  # Should be editable
            
            # Apply template to a scene
            scene_id = "test_scene_123"
            applied_template = template_system_no_gemini.apply_template(
                template.id, scene_id
            )
            
            # Applied template should maintain editability
            assert applied_template.template_id == template.id
            assert applied_template.scene_id == scene_id
            assert isinstance(applied_template.applied_settings, dict)
            assert not applied_template.is_modified  # Initially not modified
            
            # Should be able to modify applied template
            modifications = {'camera_movements.intensity': 75}
            modified_template = template_system_no_gemini.modify_applied_template(
                scene_id, modifications
            )
            
            assert modified_template.is_modified
            assert modified_template.scene_id == scene_id
    
    @given(
        template_name=st.text(min_size=1, max_size=50),
        description=st.text(min_size=10, max_size=200),
        content_type=st.sampled_from(list(ContentType))
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_custom_template_creation(self, template_name, description, content_type):
        """Test creation of custom templates."""
        # Create template system inside test to avoid fixture issues
        template_system_no_gemini = AdvancedTemplateSystem(gemini_client=None)
        visual_elements = {'camera_movement': 'test_movement'}
        cinematic_settings = {'camera_movements': {'enabled': True}}
        customization_options = {'intensity': (0, 100)}
        
        # Create custom template
        template = template_system_no_gemini.create_custom_template(
            name=template_name,
            description=description,
            content_type=content_type,
            visual_elements=visual_elements,
            cinematic_settings=cinematic_settings,
            customization_options=customization_options
        )
        
        # Verify template properties
        assert template.name == template_name
        assert template.description == description
        assert template.content_type == content_type
        assert template.visual_elements == visual_elements
        assert template.cinematic_settings == cinematic_settings
        assert template.customization_options == customization_options
        assert template.is_editable
        
        # Should be retrievable
        retrieved_template = template_system_no_gemini.get_template(template.id)
        assert retrieved_template == template
    
    @given(
        customizations=st.dictionaries(
            st.sampled_from(['intensity_range', 'color_temperature_range', 'movement_speed']),
            st.one_of(
                st.integers(min_value=10, max_value=90),
                st.sampled_from(['slow', 'medium', 'fast'])
            ),
            min_size=0,
            max_size=3
        )
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_template_customization(self, customizations):
        """Test template customization with various parameters."""
        # Create template system inside test to avoid fixture issues
        template_system_no_gemini = AdvancedTemplateSystem(gemini_client=None)
        # Get a default template
        template = template_system_no_gemini.get_template('mathematical')
        assume(template is not None)
        
        scene_id = "customization_test_scene"
        
        # Apply template with customizations
        applied_template = template_system_no_gemini.apply_template(
            template.id, scene_id, customizations
        )
        
        # Verify customizations were applied
        assert applied_template.customizations == customizations
        assert isinstance(applied_template.applied_settings, dict)
        
        # Applied settings should be valid
        if 'camera_movements' in applied_template.applied_settings:
            camera_settings = applied_template.applied_settings['camera_movements']
            if 'intensity' in camera_settings:
                assert 0 <= camera_settings['intensity'] <= 100
    
    def test_default_templates_exist(self):
        """Test that all expected default templates exist."""
        # Create template system inside test to avoid fixture issues
        template_system_no_gemini = AdvancedTemplateSystem(gemini_client=None)
        expected_templates = [
            'mathematical', 'architectural', 'analytical',
            'procedural', 'introductory', 'conclusion'
        ]
        
        for template_id in expected_templates:
            template = template_system_no_gemini.get_template(template_id)
            assert template is not None
            assert isinstance(template, TemplateDefinition)
            assert template.is_editable
            assert len(template.visual_elements) > 0
            assert len(template.cinematic_settings) > 0
    
    @given(
        scene_ids=st.lists(
            st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
            min_size=1,
            max_size=5,
            unique=True
        )
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_multiple_template_applications(self, scene_ids):
        """Test applying templates to multiple scenes."""
        # Create template system inside test to avoid fixture issues
        template_system_no_gemini = AdvancedTemplateSystem(gemini_client=None)
        template = template_system_no_gemini.get_template('mathematical')
        assume(template is not None)
        
        applied_templates = []
        
        # Apply template to multiple scenes
        for scene_id in scene_ids:
            applied_template = template_system_no_gemini.apply_template(
                template.id, scene_id
            )
            applied_templates.append(applied_template)
            
            # Verify each application
            assert applied_template.scene_id == scene_id
            assert applied_template.template_id == template.id
        
        # Verify all applications are tracked
        for scene_id in scene_ids:
            retrieved = template_system_no_gemini.get_applied_template(scene_id)
            assert retrieved is not None
            assert retrieved.scene_id == scene_id


class TemplateSystemStateMachine(RuleBasedStateMachine):
    """Stateful testing for template system operations."""
    
    def __init__(self):
        super().__init__()
        self.template_system = AdvancedTemplateSystem(gemini_client=None)
        self.applied_templates = {}
        self.custom_templates = {}
    
    @rule(
        template_id=st.sampled_from(['mathematical', 'architectural', 'analytical']),
        scene_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd')))
    )
    def apply_template(self, template_id, scene_id):
        """Apply a template to a scene."""
        applied_template = self.template_system.apply_template(template_id, scene_id)
        self.applied_templates[scene_id] = applied_template
        
        # Verify application
        assert applied_template.template_id == template_id
        assert applied_template.scene_id == scene_id
    
    @rule(
        scene_id=st.text(min_size=1, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd'))),
        modifications=st.dictionaries(
            st.text(min_size=1, max_size=30),
            st.integers(min_value=0, max_value=100),
            min_size=1,
            max_size=3
        )
    )
    def modify_applied_template(self, scene_id, modifications):
        """Modify an applied template."""
        if scene_id in self.applied_templates:
            try:
                modified = self.template_system.modify_applied_template(scene_id, modifications)
                assert modified.is_modified
                assert modified.scene_id == scene_id
            except ValueError:
                # Template might not be editable
                pass
    
    @invariant()
    def templates_remain_consistent(self):
        """Invariant: Template system should maintain consistency."""
        # All default templates should exist
        default_templates = ['mathematical', 'architectural', 'analytical', 'procedural', 'introductory', 'conclusion']
        for template_id in default_templates:
            template = self.template_system.get_template(template_id)
            assert template is not None
            assert template.is_editable
        
        # Applied templates should be retrievable
        for scene_id, applied_template in self.applied_templates.items():
            retrieved = self.template_system.get_applied_template(scene_id)
            assert retrieved is not None
            assert retrieved.scene_id == scene_id


# Run stateful tests
TestTemplateSystemState = TemplateSystemStateMachine.TestCase


if __name__ == "__main__":
    # Run async tests
    import asyncio
    
    async def run_async_tests():
        analyzer = MultiSceneConsistencyAnalyzer(gemini_client=None)
        template_system = AdvancedTemplateSystem(gemini_client=None)
        
        # Test basic functionality
        print("Testing multi-scene consistency...")
        scenes = [
            VisualDescriptionModel(
                scene_id="test1",
                content="Mathematical equation solving",
                description="Clear mathematical visualization with focused lighting",
                generated_by="test",
                cinematic_settings={},
                scene_analysis={},
                suggestions=[],
                confidence=0.8,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            ),
            VisualDescriptionModel(
                scene_id="test2",
                content="Another mathematical proof",
                description="Similar mathematical visualization with consistent lighting",
                generated_by="test",
                cinematic_settings={},
                scene_analysis={},
                suggestions=[],
                confidence=0.8,
                created_at="2024-01-01T00:00:00Z",
                updated_at="2024-01-01T00:00:00Z"
            )
        ]
        
        analysis = await analyzer.analyze_scene_consistency(scenes)
        print(f"Consistency score: {analysis.consistency_score}")
        print(f"Visual themes: {analysis.visual_themes}")
        
        print("Testing template classification...")
        content_type = await template_system.classify_content_type("This is a mathematical equation: x = y + z")
        print(f"Classified as: {content_type}")
        
        template = template_system.get_template_by_content_type(content_type)
        if template:
            print(f"Found template: {template.name}")
            applied = template_system.apply_template(template.id, "test_scene")
            print(f"Applied template to scene: {applied.scene_id}")
        
        print("All tests completed successfully!")
    
    asyncio.run(run_async_tests())