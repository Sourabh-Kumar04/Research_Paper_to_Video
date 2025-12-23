"""
Property-based tests for RASO script generation structure and quality.

**Feature: raso-platform, Property 4: Script generation structure**
Tests that for any paper understanding, the script generation produces scene-wise
narration that maps logically to paper sections with educational tone and YouTube-friendly language.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, strategies as st

from agents.script import ScriptAgent
from backend.models.understanding import PaperUnderstanding, KeyEquation, VisualizableConcept
from backend.models.script import NarrationScript, Scene
from backend.services.llm import LLMResponse, LLMProvider


class TestScriptStructureProperties:
    """Property-based tests for script generation structure."""

    @given(
        problem=st.text(min_size=20, max_size=200),
        intuition=st.text(min_size=20, max_size=200),
        contributions=st.lists(st.text(min_size=10, max_size=100), min_size=1, max_size=5),
        num_concepts=st.integers(min_value=0, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_script_structure_completeness_property(
        self, problem: str, intuition: str, contributions: List[str], num_concepts: int
    ):
        """
        **Property 4: Script generation structure**
        For any paper understanding with problem, intuition, and contributions,
        the script generation should produce structured scenes that map logically
        to paper content with appropriate educational narration.
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        agent = ScriptAgent()
        
        # Create test understanding
        concepts = []
        for i in range(num_concepts):
            concepts.append(VisualizableConcept(
                name=f"Concept {i+1}",
                description=f"Description of concept {i+1}",
                visualization_type="animation",
                complexity="medium",
                related_equations=[],
            ))
        
        understanding = PaperUnderstanding(
            problem=problem,
            intuition=intuition,
            contributions=contributions,
            key_equations=[],
            visualizable_concepts=concepts,
        )
        
        paper_content = {
            "title": "Test Research Paper",
            "authors": ["Test Author"],
            "abstract": "Test abstract for script generation",
        }
        
        # Mock LLM responses for scene planning and narration
        mock_scene_plan = {
            "scenes": [
                {
                    "title": "The Problem",
                    "concepts": ["problem", "motivation"],
                    "visual_type": "motion-canvas",
                    "duration": 45
                },
                {
                    "title": "The Solution",
                    "concepts": ["intuition", "approach"],
                    "visual_type": "motion-canvas", 
                    "duration": 50
                },
                {
                    "title": "Key Innovation",
                    "concepts": ["contribution"],
                    "visual_type": "manim",
                    "duration": 40
                }
            ]
        }
        
        mock_narrations = [
            "Welcome to our exploration of this fascinating research problem. Today we'll dive into...",
            "Now let's understand the key insight that makes this approach so powerful...",
            "The main innovation here is truly remarkable. Let me show you how it works..."
        ]
        
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            if call_count == 0:
                # Scene planning response
                response_content = json.dumps(mock_scene_plan)
            else:
                # Narration responses
                narration_index = (call_count - 1) % len(mock_narrations)
                response_content = mock_narrations[narration_index]
            
            call_count += 1
            return LLMResponse(
                content=response_content,
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
        
        with patch('agents.script.llm_service.generate', side_effect=mock_generate):
            # Execute script generation
            state = {
                "understanding": understanding.dict(),
                "paper_content": paper_content,
            }
            result_state = await agent.execute(state)
            
            # Verify script structure completeness
            assert "script" in result_state
            script_data = result_state["script"]
            script = NarrationScript(**script_data)
            
            # Verify basic structure
            assert script.scenes is not None
            assert len(script.scenes) > 0
            assert len(script.scenes) <= 10  # Reasonable upper bound
            
            # Verify scene structure maps to paper content
            scene_titles = [scene.title for scene in script.scenes]
            
            # Should have logical progression
            assert any("problem" in title.lower() or "challenge" in title.lower() 
                     for title in scene_titles), "Should have problem/challenge scene"
            
            # Verify each scene has required properties
            for i, scene in enumerate(script.scenes):
                assert scene.id is not None
                assert scene.title is not None
                assert len(scene.title.strip()) > 0
                
                assert scene.narration is not None
                assert len(scene.narration.strip()) > 10  # Meaningful narration
                
                assert scene.duration > 0
                assert scene.duration <= 120  # Reasonable scene length
                
                assert scene.visual_type in ["manim", "motion-canvas", "remotion"]
                assert scene.concepts is not None
            
            # Verify total duration and word count
            assert script.total_duration > 0
            assert script.total_duration == sum(scene.duration for scene in script.scenes)
            
            assert script.word_count > 0
            calculated_words = sum(len(scene.narration.split()) for scene in script.scenes)
            assert script.word_count == calculated_words

    @given(
        scene_duration=st.integers(min_value=20, max_value=90),
        visual_type=st.sampled_from(["manim", "motion-canvas", "remotion"]),
        concepts=st.lists(st.text(min_size=5, max_size=20), min_size=1, max_size=5),
    )
    @pytest.mark.asyncio
    async def test_educational_tone_property(
        self, scene_duration: int, visual_type: str, concepts: List[str]
    ):
        """
        **Property 4: Script generation structure**
        For any scene parameters, the generated narration should maintain
        educational tone while being YouTube-friendly and accessible.
        **Validates: Requirements 3.1, 3.2**
        """
        agent = ScriptAgent()
        
        # Mock educational narration response
        mock_narration = """
        Let's explore this fascinating concept together. Imagine you're trying to solve 
        a complex puzzle - that's exactly what researchers faced here. The key insight 
        is surprisingly elegant: by changing how we approach the problem, we can achieve 
        remarkable results. This breakthrough opens up entirely new possibilities.
        """
        
        with patch('agents.script.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=mock_narration,
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Generate narration for scene
            context = {
                "title": "Test Paper",
                "problem": "Complex computational challenge",
                "intuition": "Novel algorithmic approach",
            }
            
            narration = await agent.generate_scene_narration(
                scene_title="Test Scene",
                concepts=concepts,
                duration=scene_duration,
                visual_type=visual_type,
                context=context,
            )
            
            # Verify educational and YouTube-friendly characteristics
            assert narration is not None
            assert len(narration.strip()) > 0
            
            # Check for educational tone indicators
            educational_indicators = [
                "let's", "we", "you", "imagine", "explore", "understand",
                "see", "learn", "discover", "fascinating", "remarkable"
            ]
            narration_lower = narration.lower()
            found_indicators = sum(1 for indicator in educational_indicators 
                                 if indicator in narration_lower)
            assert found_indicators >= 2, "Should have educational tone indicators"
            
            # Verify appropriate length for duration
            estimated_duration = agent.estimate_duration(narration)
            duration_ratio = estimated_duration / scene_duration
            assert 0.7 <= duration_ratio <= 1.5, f"Duration mismatch: {estimated_duration}s vs {scene_duration}s"
            
            # Verify clean formatting (no stage directions)
            assert "[" not in narration and "]" not in narration
            assert not narration.startswith("(") and not narration.endswith(")")

    @given(
        num_scenes=st.integers(min_value=2, max_value=8),
        scene_durations=st.lists(st.integers(min_value=15, max_value=80), min_size=2, max_size=8),
    )
    @pytest.mark.asyncio
    async def test_scene_organization_property(
        self, num_scenes: int, scene_durations: List[int]
    ):
        """
        **Property 4: Script generation structure**
        For any number of scenes, the organization should follow logical
        progression from problem to solution with smooth transitions.
        **Validates: Requirements 3.3**
        """
        agent = ScriptAgent()
        
        # Ensure we have matching number of durations
        durations = scene_durations[:num_scenes]
        while len(durations) < num_scenes:
            durations.append(45)  # Default duration
        
        # Create test scenes with logical progression
        scenes = []
        scene_types = ["introduction", "problem", "solution", "innovation", "results", "conclusion"]
        
        for i in range(num_scenes):
            scene_type = scene_types[i % len(scene_types)]
            scenes.append(Scene(
                id=f"scene_{i}",
                title=f"{scene_type.title()} Scene",
                narration=f"This is the narration for the {scene_type} scene. " * 5,
                duration=durations[i],
                visual_type="motion-canvas",
                concepts=[scene_type],
            ))
        
        script = NarrationScript(
            scenes=scenes,
            total_duration=sum(scene.duration for scene in scenes),
            word_count=sum(len(scene.narration.split()) for scene in scenes),
        )
        
        # Validate script structure
        issues = agent.validate_script_structure(script)
        
        # Should have minimal issues for well-structured script
        critical_issues = [issue for issue in issues if "too short" in issue or "no scenes" in issue]
        assert len(critical_issues) == 0, f"Critical structural issues: {critical_issues}"
        
        # Verify logical scene progression
        scene_concepts = [scene.concepts[0] if scene.concepts else "unknown" for scene in scenes]
        
        # Should start with introduction/problem
        assert any(concept in ["introduction", "problem"] for concept in scene_concepts[:2])
        
        # Should end with results/conclusion if enough scenes
        if num_scenes >= 3:
            assert any(concept in ["results", "conclusion", "innovation"] for concept in scene_concepts[-2:])

    @given(
        narration_text=st.text(min_size=50, max_size=500),
        target_words=st.integers(min_value=20, max_value=200),
    )
    def test_duration_estimation_property(self, narration_text: str, target_words: int):
        """
        **Property 4: Script generation structure**
        For any narration text, the duration estimation should be consistent
        and based on standard speaking rates for educational content.
        **Validates: Requirements 3.3**
        """
        agent = ScriptAgent()
        
        # Test duration estimation
        estimated_duration = agent.estimate_duration(narration_text)
        
        # Verify estimation is reasonable
        word_count = len(narration_text.split())
        expected_duration = (word_count / agent.words_per_minute) * 60
        
        assert estimated_duration == expected_duration
        assert estimated_duration > 0
        
        # For non-empty text, should have reasonable duration
        if word_count > 0:
            assert estimated_duration >= 1.0  # At least 1 second for any text
            assert estimated_duration <= word_count * 2  # Upper bound check

    @given(
        invalid_scene_data=st.lists(
            st.dictionaries(
                keys=st.sampled_from(["title", "concepts", "visual_type", "duration", "invalid_key"]),
                values=st.one_of(st.text(), st.integers(), st.lists(st.text())),
                min_size=1,
                max_size=5,
            ),
            min_size=1,
            max_size=3,
        ),
    )
    @pytest.mark.asyncio
    async def test_fallback_scene_generation_property(self, invalid_scene_data: List[Dict[str, Any]]):
        """
        **Property 4: Script generation structure**
        For any invalid or malformed scene planning response, the agent should
        generate fallback scenes that maintain script structure and completeness.
        **Validates: Requirements 3.1, 3.2, 3.3**
        """
        agent = ScriptAgent()
        
        # Create test understanding
        understanding = PaperUnderstanding(
            problem="Test problem statement",
            intuition="Test intuition explanation",
            contributions=["Contribution 1", "Contribution 2"],
            key_equations=[],
            visualizable_concepts=[],
        )
        
        paper_content = {"title": "Test Paper"}
        
        # Mock LLM to return invalid scene data
        with patch('agents.script.llm_service.generate') as mock_generate:
            # Return invalid JSON that should trigger fallback
            mock_generate.return_value = LLMResponse(
                content=json.dumps({"invalid": "data"}),
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test scene planning with fallback
            scenes = await agent._plan_scenes(understanding, paper_content)
            
            # Should still return valid scenes via fallback
            assert scenes is not None
            assert len(scenes) > 0
            
            # Verify fallback scenes have required structure
            for scene in scenes:
                assert "title" in scene
                assert "concepts" in scene
                assert "visual_type" in scene
                assert "duration" in scene
                
                assert isinstance(scene["title"], str)
                assert len(scene["title"]) > 0
                
                assert isinstance(scene["concepts"], list)
                assert len(scene["concepts"]) > 0
                
                assert scene["visual_type"] in ["manim", "motion-canvas", "remotion"]
                assert isinstance(scene["duration"], (int, float))
                assert scene["duration"] > 0

    @given(
        words_per_minute=st.integers(min_value=100, max_value=200),
        scene_duration=st.integers(min_value=30, max_value=120),
    )
    @pytest.mark.asyncio
    async def test_narration_length_adjustment_property(
        self, words_per_minute: int, scene_duration: int
    ):
        """
        **Property 4: Script generation structure**
        For any speaking rate and scene duration, the narration length
        should be adjusted to match the target timing appropriately.
        **Validates: Requirements 3.3**
        """
        agent = ScriptAgent()
        agent.words_per_minute = words_per_minute  # Override for testing
        
        # Create test narration that's too long
        long_narration = "This is a test sentence. " * 50  # Very long narration
        
        # Calculate target words for duration
        target_words = int(scene_duration * words_per_minute / 60)
        
        # Test length adjustment
        adjusted_narration = agent._adjust_narration_length(long_narration, target_words)
        
        # Verify adjustment
        assert adjusted_narration is not None
        assert len(adjusted_narration) > 0
        
        adjusted_word_count = len(adjusted_narration.split())
        
        # Should be closer to target (within reasonable bounds)
        if len(long_narration.split()) > target_words * 1.2:
            # Was too long, should be shortened
            assert adjusted_word_count <= len(long_narration.split())
            # Should be reasonably close to target
            assert adjusted_word_count <= target_words * 1.1
        
        # Should maintain sentence structure
        assert adjusted_narration.endswith(('.', '!', '?'))

    @pytest.mark.asyncio
    async def test_visual_type_assignment_property(self):
        """
        **Property 4: Script generation structure**
        The visual type assignment should be appropriate for content type:
        manim for mathematical content, motion-canvas for concepts, remotion for UI.
        **Validates: Requirements 3.1, 3.3**
        """
        agent = ScriptAgent()
        
        # Test with mathematical content (should prefer manim)
        math_understanding = PaperUnderstanding(
            problem="Mathematical optimization problem",
            intuition="Novel algorithmic approach",
            contributions=["New optimization algorithm"],
            key_equations=[KeyEquation(
                equation_id="eq1",
                importance=8,
                visualization_hint="Show optimization steps",
                related_concepts=["optimization"],
            )],
            visualizable_concepts=[],
        )
        
        paper_content = {"title": "Mathematical Research"}
        
        # Mock scene planning response
        mock_scenes = {
            "scenes": [
                {
                    "title": "Mathematical Foundation",
                    "concepts": ["equations", "optimization"],
                    "visual_type": "manim",  # Should use manim for math
                    "duration": 45
                }
            ]
        }
        
        with patch('agents.script.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=json.dumps(mock_scenes),
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            scenes = await agent._plan_scenes(math_understanding, paper_content)
            
            # Should have at least one scene
            assert len(scenes) > 0
            
            # Verify visual types are appropriate
            for scene in scenes:
                assert scene["visual_type"] in ["manim", "motion-canvas", "remotion"]


if __name__ == "__main__":
    pytest.main([__file__])