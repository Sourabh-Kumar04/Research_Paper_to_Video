"""
Property-based tests for RASO visual planning framework assignment rules.

**Feature: raso-platform, Property 5: Framework assignment rules**
Tests that for any content type, the visual planning assigns the appropriate
animation framework and generates complete scene plans with proper transitions.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, strategies as st

from agents.visual_planning import (
    VisualPlanningAgent,
    AnimationFramework,
    ContentType,
    FrameworkAssignmentRules,
)
from backend.models.script import NarrationScript, Scene
from backend.models.understanding import PaperUnderstanding, KeyEquation, VisualizableConcept
from backend.models.visual import VisualPlan, ScenePlan
from backend.services.llm import LLMResponse, LLMProvider


class TestFrameworkAssignmentProperties:
    """Property-based tests for framework assignment rules."""

    @given(
        mathematical_keywords=st.lists(
            st.sampled_from(FrameworkAssignmentRules.MATHEMATICAL_KEYWORDS),
            min_size=1,
            max_size=3
        ),
        scene_title=st.text(min_size=5, max_size=50),
        scene_duration=st.floats(min_value=10.0, max_value=120.0),
    )
    @pytest.mark.asyncio
    async def test_mathematical_content_assigns_manim_property(
        self, mathematical_keywords: List[str], scene_title: str, scene_duration: float
    ):
        """
        **Property 5: Framework assignment rules**
        For any scene containing mathematical keywords, the system should
        assign Manim CE for equations, proofs, and mathematical visualizations.
        **Validates: Requirements 4.2**
        """
        agent = VisualPlanningAgent()
        
        # Create scene with mathematical content
        narration = f"In this section, we explore the {mathematical_keywords[0]} and its applications. "
        narration += f"The {mathematical_keywords[-1]} demonstrates the key principles."
        
        scene = Scene(
            id="math_scene",
            title=scene_title,
            narration=narration,
            duration=scene_duration,
            visual_type="manim",  # Expected assignment
            concepts=mathematical_keywords,
        )
        
        # Create understanding with mathematical equations
        understanding = PaperUnderstanding(
            problem="Mathematical problem statement",
            intuition="Mathematical intuition",
            contributions=["Mathematical contribution"],
            key_equations=[
                KeyEquation(
                    equation_id="eq1",
                    importance=8,
                    visualization_hint="Mathematical visualization",
                    related_concepts=mathematical_keywords,
                )
            ],
            visualizable_concepts=[],
        )
        
        # Test framework assignment
        assigned_framework = await agent.assign_framework_to_scene(scene, understanding)
        
        # Verify Manim is assigned for mathematical content
        assert assigned_framework == AnimationFramework.MANIM
        
        # Test content type classification
        content_type = agent._classify_content_type(scene, understanding)
        assert content_type == ContentType.MATHEMATICAL
        
        # Verify framework mapping rule
        expected_framework = agent.assignment_rules.FRAMEWORK_MAPPING[ContentType.MATHEMATICAL]
        assert expected_framework == AnimationFramework.MANIM

    @given(
        conceptual_keywords=st.lists(
            st.sampled_from(FrameworkAssignmentRules.CONCEPTUAL_KEYWORDS),
            min_size=1,
            max_size=3
        ),
        scene_title=st.text(min_size=5, max_size=50),
        scene_duration=st.floats(min_value=10.0, max_value=120.0),
    )
    @pytest.mark.asyncio
    async def test_conceptual_content_assigns_motion_canvas_property(
        self, conceptual_keywords: List[str], scene_title: str, scene_duration: float
    ):
        """
        **Property 5: Framework assignment rules**
        For any scene containing conceptual content, the system should
        assign Motion Canvas for general visual animations and illustrations.
        **Validates: Requirements 4.3**
        """
        agent = VisualPlanningAgent()
        
        # Create scene with conceptual content
        narration = f"This {conceptual_keywords[0]} represents a novel {conceptual_keywords[-1]}. "
        narration += "The approach demonstrates significant improvements."
        
        scene = Scene(
            id="concept_scene",
            title=scene_title,
            narration=narration,
            duration=scene_duration,
            visual_type="motion-canvas",  # Expected assignment
            concepts=conceptual_keywords,
        )
        
        # Create understanding with conceptual elements
        understanding = PaperUnderstanding(
            problem="Conceptual problem statement",
            intuition="Conceptual intuition",
            contributions=["Conceptual contribution"],
            key_equations=[],
            visualizable_concepts=[
                VisualizableConcept(
                    name="Test Concept",
                    description="A conceptual visualization",
                    visualization_type="animation",
                    complexity="medium",
                    related_equations=[],
                )
            ],
        )
        
        # Test framework assignment
        assigned_framework = await agent.assign_framework_to_scene(scene, understanding)
        
        # Verify Motion Canvas is assigned for conceptual content
        assert assigned_framework == AnimationFramework.MOTION_CANVAS
        
        # Test content type classification
        content_type = agent._classify_content_type(scene, understanding)
        assert content_type == ContentType.CONCEPTUAL
        
        # Verify framework mapping rule
        expected_framework = agent.assignment_rules.FRAMEWORK_MAPPING[ContentType.CONCEPTUAL]
        assert expected_framework == AnimationFramework.MOTION_CANVAS

    @given(
        ui_keywords=st.lists(
            st.sampled_from(FrameworkAssignmentRules.UI_KEYWORDS),
            min_size=1,
            max_size=3
        ),
        scene_title=st.text(min_size=5, max_size=50),
        scene_duration=st.floats(min_value=5.0, max_value=60.0),
    )
    @pytest.mark.asyncio
    async def test_ui_content_assigns_remotion_property(
        self, ui_keywords: List[str], scene_title: str, scene_duration: float
    ):
        """
        **Property 5: Framework assignment rules**
        For any scene containing UI elements, the system should
        assign Remotion for titles, overlays, and interface components.
        **Validates: Requirements 4.4**
        """
        agent = VisualPlanningAgent()
        
        # Create scene with UI content
        narration = f"The {ui_keywords[0]} provides access to the {ui_keywords[-1]}. "
        narration += "Users can interact with various elements."
        
        scene = Scene(
            id="ui_scene",
            title=scene_title,
            narration=narration,
            duration=scene_duration,
            visual_type="remotion",  # Expected assignment
            concepts=ui_keywords,
        )
        
        # Create basic understanding
        understanding = PaperUnderstanding(
            problem="UI problem statement",
            intuition="UI intuition",
            contributions=["UI contribution"],
            key_equations=[],
            visualizable_concepts=[],
        )
        
        # Test framework assignment
        assigned_framework = await agent.assign_framework_to_scene(scene, understanding)
        
        # Verify Remotion is assigned for UI content
        assert assigned_framework == AnimationFramework.REMOTION
        
        # Test content type classification
        content_type = agent._classify_content_type(scene, understanding)
        assert content_type == ContentType.UI_ELEMENTS
        
        # Verify framework mapping rule
        expected_framework = agent.assignment_rules.FRAMEWORK_MAPPING[ContentType.UI_ELEMENTS]
        assert expected_framework == AnimationFramework.REMOTION

    @given(
        intro_titles=st.sampled_from(["Introduction", "Welcome", "Overview", "Getting Started"]),
        conclusion_titles=st.sampled_from(["Conclusion", "Summary", "Final Thoughts", "Wrap Up"]),
        scene_duration=st.floats(min_value=5.0, max_value=30.0),
    )
    @pytest.mark.asyncio
    async def test_intro_conclusion_assigns_remotion_property(
        self, intro_titles: str, conclusion_titles: str, scene_duration: float
    ):
        """
        **Property 5: Framework assignment rules**
        For any introduction or conclusion scenes, the system should
        assign Remotion for title sequences and summary cards.
        **Validates: Requirements 4.4**
        """
        agent = VisualPlanningAgent()
        
        # Create understanding
        understanding = PaperUnderstanding(
            problem="Research problem",
            intuition="Research intuition", 
            contributions=["Research contribution"],
            key_equations=[],
            visualizable_concepts=[],
        )
        
        # Test introduction scene
        intro_scene = Scene(
            id="intro_scene",
            title=intro_titles,
            narration="Welcome to this research presentation.",
            duration=scene_duration,
            visual_type="remotion",
            concepts=[],
        )
        
        intro_framework = await agent.assign_framework_to_scene(intro_scene, understanding)
        intro_content_type = agent._classify_content_type(intro_scene, understanding)
        
        assert intro_framework == AnimationFramework.REMOTION
        assert intro_content_type == ContentType.INTRODUCTION
        
        # Test conclusion scene
        conclusion_scene = Scene(
            id="conclusion_scene",
            title=conclusion_titles,
            narration="In summary, we have demonstrated key findings.",
            duration=scene_duration,
            visual_type="remotion",
            concepts=[],
        )
        
        conclusion_framework = await agent.assign_framework_to_scene(conclusion_scene, understanding)
        conclusion_content_type = agent._classify_content_type(conclusion_scene, understanding)
        
        assert conclusion_framework == AnimationFramework.REMOTION
        assert conclusion_content_type == ContentType.CONCLUSION

    @given(
        num_scenes=st.integers(min_value=2, max_value=8),
        scene_durations=st.lists(st.floats(min_value=10.0, max_value=60.0), min_size=2, max_size=8),
    )
    @pytest.mark.asyncio
    async def test_complete_visual_plan_generation_property(
        self, num_scenes: int, scene_durations: List[float]
    ):
        """
        **Property 5: Framework assignment rules**
        For any complete narration script, the system should generate
        a detailed scene sequence with assigned frameworks and transition styles.
        **Validates: Requirements 4.1, 4.5**
        """
        agent = VisualPlanningAgent()
        
        # Ensure we have enough durations
        durations = (scene_durations * ((num_scenes // len(scene_durations)) + 1))[:num_scenes]
        
        # Create diverse scenes
        scenes = []
        content_types = [ContentType.INTRODUCTION, ContentType.MATHEMATICAL, ContentType.CONCEPTUAL, ContentType.CONCLUSION]
        
        for i in range(num_scenes):
            content_type = content_types[i % len(content_types)]
            
            if content_type == ContentType.MATHEMATICAL:
                narration = "This equation demonstrates the mathematical relationship."
                concepts = ["equation", "formula"]
            elif content_type == ContentType.CONCEPTUAL:
                narration = "The concept illustrates the underlying mechanism."
                concepts = ["concept", "process"]
            elif content_type == ContentType.INTRODUCTION:
                narration = "Welcome to this research presentation."
                concepts = []
            else:  # CONCLUSION
                narration = "In conclusion, we have shown significant results."
                concepts = []
            
            scenes.append(Scene(
                id=f"scene_{i}",
                title=f"Scene {i+1}",
                narration=narration,
                duration=durations[i],
                visual_type="auto",
                concepts=concepts,
            ))
        
        script = NarrationScript(
            scenes=scenes,
            total_duration=sum(durations),
            word_count=len(" ".join(s.narration for s in scenes).split()),
        )
        
        understanding = PaperUnderstanding(
            problem="Research problem",
            intuition="Research intuition",
            contributions=["Research contribution"],
            key_equations=[
                KeyEquation(
                    equation_id="eq1",
                    importance=8,
                    visualization_hint="Mathematical visualization",
                    related_concepts=["equation"],
                )
            ],
            visualizable_concepts=[
                VisualizableConcept(
                    name="Test Concept",
                    description="A test concept",
                    visualization_type="animation",
                    complexity="medium",
                    related_equations=[],
                )
            ],
        )
        
        # Mock LLM response for scene analysis
        mock_assignments = {
            "scene_assignments": [
                {
                    "scene_id": f"scene_{i}",
                    "content_type": content_types[i % len(content_types)].value,
                    "framework": agent.assignment_rules.FRAMEWORK_MAPPING[content_types[i % len(content_types)]].value,
                    "complexity": "medium",
                    "visual_elements": ["test element"],
                    "transition_in": "fade",
                    "transition_out": "fade",
                }
                for i in range(num_scenes)
            ]
        }
        
        with patch('agents.visual_planning.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=json.dumps(mock_assignments),
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Execute visual planning
            state = {
                "script": script.dict(),
                "understanding": understanding.dict(),
                "paper_content": {"title": "Test Paper"},
            }
            
            result_state = await agent.execute(state)
            
            # Verify complete visual plan generation
            assert "visual_plan" in result_state
            visual_plan_data = result_state["visual_plan"]
            visual_plan = VisualPlan(**visual_plan_data)
            
            # Verify all scenes have plans
            assert len(visual_plan.scenes) == num_scenes
            
            # Verify each scene plan has required components
            for scene_plan in visual_plan.scenes:
                assert scene_plan.scene_id is not None
                assert scene_plan.framework in [f.value for f in AnimationFramework]
                assert scene_plan.template is not None
                assert scene_plan.parameters is not None
                assert scene_plan.duration > 0
            
            # Verify transitions are planned (should be num_scenes - 1)
            assert len(visual_plan.transitions) == num_scenes - 1
            
            # Verify each transition connects adjacent scenes
            for i, transition in enumerate(visual_plan.transitions):
                assert transition.from_scene == f"scene_{i}"
                assert transition.to_scene == f"scene_{i+1}"
                assert transition.duration > 0
            
            # Verify style guide is created
            assert visual_plan.overall_style is not None
            assert visual_plan.overall_style.theme is not None
            assert visual_plan.overall_style.primary_color is not None

    @given(
        framework=st.sampled_from([AnimationFramework.MANIM, AnimationFramework.MOTION_CANVAS, AnimationFramework.REMOTION]),
        complexity=st.sampled_from(["simple", "medium", "complex"]),
        scene_duration=st.floats(min_value=10.0, max_value=120.0),
    )
    def test_template_selection_consistency_property(
        self, framework: AnimationFramework, complexity: str, scene_duration: float
    ):
        """
        **Property 5: Framework assignment rules**
        For any framework and complexity combination, the template selection
        should be consistent and appropriate for the content type.
        **Validates: Requirements 4.1, 4.5**
        """
        agent = VisualPlanningAgent()
        
        # Create assignment data
        assignment = {
            "framework": framework.value,
            "content_type": "mathematical" if framework == AnimationFramework.MANIM else "conceptual",
            "complexity": complexity,
        }
        
        # Test template selection
        template = agent._select_template(assignment)
        
        # Verify template is selected
        assert template is not None
        assert len(template) > 0
        
        # Verify framework-specific templates
        if framework == AnimationFramework.MANIM:
            assert "manim" in template.lower() or "equation" in template.lower()
        elif framework == AnimationFramework.MOTION_CANVAS:
            assert "motion" in template.lower() or "canvas" in template.lower() or "diagram" in template.lower() or "concept" in template.lower()
        elif framework == AnimationFramework.REMOTION:
            assert "remotion" in template.lower() or "title" in template.lower() or "text" in template.lower() or "interface" in template.lower()
        
        # Test parameter generation
        scene = Scene(
            id="test_scene",
            title="Test Scene",
            narration="Test narration content",
            duration=scene_duration,
            visual_type=framework.value,
            concepts=["test"],
        )
        
        parameters = agent._generate_parameters(assignment, scene)
        
        # Verify parameters are generated
        assert parameters is not None
        assert "duration" in parameters
        assert parameters["duration"] == scene_duration
        assert "title" in parameters
        assert parameters["title"] == scene.title

    def test_framework_capabilities_completeness_property(self):
        """
        **Property 5: Framework assignment rules**
        The framework capabilities should comprehensively cover all
        supported animation types and content categories.
        **Validates: Requirements 4.1, 4.2, 4.3, 4.4**
        """
        agent = VisualPlanningAgent()
        
        # Get framework capabilities
        capabilities = agent.get_framework_capabilities()
        
        # Verify all frameworks are covered
        assert AnimationFramework.MANIM in capabilities
        assert AnimationFramework.MOTION_CANVAS in capabilities
        assert AnimationFramework.REMOTION in capabilities
        
        # Verify each framework has capabilities
        for framework, caps in capabilities.items():
            assert caps is not None
            assert len(caps) > 0
            assert all(isinstance(cap, str) and len(cap) > 0 for cap in caps)
        
        # Verify Manim capabilities include mathematical content
        manim_caps = capabilities[AnimationFramework.MANIM]
        assert any("equation" in cap.lower() or "math" in cap.lower() for cap in manim_caps)
        
        # Verify Motion Canvas capabilities include conceptual content
        motion_caps = capabilities[AnimationFramework.MOTION_CANVAS]
        assert any("concept" in cap.lower() or "diagram" in cap.lower() for cap in motion_caps)
        
        # Verify Remotion capabilities include UI content
        remotion_caps = capabilities[AnimationFramework.REMOTION]
        assert any("title" in cap.lower() or "ui" in cap.lower() or "interface" in cap.lower() for cap in remotion_caps)


if __name__ == "__main__":
    pytest.main([__file__])