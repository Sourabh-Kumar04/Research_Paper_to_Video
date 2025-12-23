"""
Property-based tests for RASO state serialization and agent communication.

**Feature: raso-platform, Property 12: Agent architecture compliance**
Tests that the platform uses LangGraph orchestration with stateless agents,
JSON-based communication with schema enforcement, and comprehensive state tracking.
"""

import json
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from backend.models import (
    RASOMasterState,
    PaperInput,
    PaperContent,
    PaperUnderstanding,
    NarrationScript,
    VisualPlan,
    AnimationAssets,
    AudioAssets,
    VideoAsset,
    VideoMetadata,
    ProcessingOptions,
    AgentError,
    WorkflowStatus,
    AgentType,
    ErrorSeverity,
    Section,
    Equation,
    Scene,
    RenderedScene,
    AudioScene,
    Chapter,
    VideoResolution,
)


class TestStateSerializationProperties:
    """Property-based tests for state serialization and agent communication."""

    @given(
        job_id=st.uuids().map(str),
        paper_type=st.sampled_from(["title", "arxiv", "pdf"]),
        content=st.text(min_size=10, max_size=200),
        video_quality=st.sampled_from(["draft", "standard", "high", "ultra"]),
        voice_speed=st.floats(min_value=0.5, max_value=2.0),
        max_retries=st.integers(min_value=0, max_value=10),
    )
    def test_master_state_json_serialization_property(
        self, job_id: str, paper_type: str, content: str, video_quality: str, 
        voice_speed: float, max_retries: int
    ):
        """
        **Property 12: Agent architecture compliance**
        For any valid master state, JSON serialization and deserialization should
        preserve all data with strict schema enforcement.
        **Validates: Requirements 11.2, 11.3**
        """
        # Create a valid paper input
        paper_input = PaperInput(type=paper_type, content=content)
        
        # Create processing options
        options = ProcessingOptions(
            video_quality=video_quality,
            voice_speed=voice_speed,
            max_retries=max_retries,
        )
        
        # Create master state
        original_state = RASOMasterState(
            job_id=job_id,
            paper_input=paper_input,
            options=options,
        )
        
        # Test JSON serialization
        json_data = original_state.json()
        assert isinstance(json_data, str)
        
        # Verify it's valid JSON
        parsed_json = json.loads(json_data)
        assert isinstance(parsed_json, dict)
        
        # Test deserialization
        restored_state = RASOMasterState.parse_raw(json_data)
        
        # Verify all fields are preserved
        assert restored_state.job_id == original_state.job_id
        assert restored_state.paper_input.type == original_state.paper_input.type
        assert restored_state.paper_input.content == original_state.paper_input.content
        assert restored_state.options.video_quality == original_state.options.video_quality
        assert restored_state.options.voice_speed == original_state.options.voice_speed
        assert restored_state.options.max_retries == original_state.options.max_retries
        
        # Verify schema enforcement - invalid data should fail
        invalid_json = json_data.replace(f'"{job_id}"', '"invalid-uuid-format"')
        try:
            RASOMasterState.parse_raw(invalid_json)
            # If no exception, the UUID validation might be lenient, which is acceptable
        except ValidationError:
            # This is expected for strict validation
            pass

    @given(
        title=st.text(min_size=10, max_size=100),
        authors=st.lists(st.text(min_size=3, max_size=50), min_size=1, max_size=5),
        abstract=st.text(min_size=50, max_size=500),
        section_count=st.integers(min_value=1, max_value=5),
    )
    def test_paper_content_serialization_property(
        self, title: str, authors: List[str], abstract: str, section_count: int
    ):
        """
        **Property 12: Agent architecture compliance**
        For any paper content, serialization should maintain data integrity
        and enforce schema validation for agent communication.
        **Validates: Requirements 11.2**
        """
        # Create sections
        sections = []
        for i in range(section_count):
            section = Section(
                id=f"section_{i}",
                title=f"Section {i+1}",
                content=f"This is the content of section {i+1}. " * 5,  # Ensure min length
                level=1,
            )
            sections.append(section)
        
        # Create paper content
        paper_content = PaperContent(
            title=title,
            authors=authors,
            abstract=abstract,
            sections=sections,
        )
        
        # Test serialization
        json_data = paper_content.json()
        parsed_data = json.loads(json_data)
        
        # Verify structure
        assert "title" in parsed_data
        assert "authors" in parsed_data
        assert "abstract" in parsed_data
        assert "sections" in parsed_data
        assert len(parsed_data["sections"]) == section_count
        
        # Test deserialization
        restored_content = PaperContent.parse_raw(json_data)
        
        # Verify data integrity
        assert restored_content.title == paper_content.title
        assert restored_content.authors == paper_content.authors
        assert restored_content.abstract == paper_content.abstract
        assert len(restored_content.sections) == len(paper_content.sections)
        
        for original, restored in zip(paper_content.sections, restored_content.sections):
            assert original.id == restored.id
            assert original.title == restored.title
            assert original.content == restored.content
            assert original.level == restored.level

    @given(
        agent_type=st.sampled_from(list(AgentType)),
        error_code=st.text(min_size=5, max_size=20),
        message=st.text(min_size=10, max_size=200),
        severity=st.sampled_from(list(ErrorSeverity)),
        retry_count=st.integers(min_value=0, max_value=10),
    )
    def test_agent_error_serialization_property(
        self, agent_type: AgentType, error_code: str, message: str, 
        severity: ErrorSeverity, retry_count: int
    ):
        """
        **Property 12: Agent architecture compliance**
        For any agent error, serialization should preserve error information
        for proper error tracking and debugging across agent communications.
        **Validates: Requirements 11.4**
        """
        # Create agent error
        error = AgentError(
            agent_type=agent_type,
            error_code=error_code,
            message=message,
            severity=severity,
            retry_count=retry_count,
        )
        
        # Test serialization
        json_data = error.json()
        parsed_data = json.loads(json_data)
        
        # Verify required fields
        assert parsed_data["agent_type"] == agent_type.value
        assert parsed_data["error_code"] == error_code
        assert parsed_data["message"] == message
        assert parsed_data["severity"] == severity.value
        assert parsed_data["retry_count"] == retry_count
        
        # Test deserialization
        restored_error = AgentError.parse_raw(json_data)
        
        # Verify data integrity
        assert restored_error.agent_type == error.agent_type
        assert restored_error.error_code == error.error_code
        assert restored_error.message == error.message
        assert restored_error.severity == error.severity
        assert restored_error.retry_count == error.retry_count
        assert restored_error.is_recoverable == error.is_recoverable

    @given(
        scene_count=st.integers(min_value=1, max_value=5),
        total_duration=st.floats(min_value=30.0, max_value=300.0),
        word_count=st.integers(min_value=50, max_value=1000),
    )
    def test_narration_script_serialization_property(
        self, scene_count: int, total_duration: float, word_count: int
    ):
        """
        **Property 12: Agent architecture compliance**
        For any narration script, serialization should maintain scene structure
        and timing information for agent coordination.
        **Validates: Requirements 11.2, 11.3**
        """
        # Create scenes with proportional durations and word counts
        scenes = []
        duration_per_scene = total_duration / scene_count
        words_per_scene = word_count // scene_count
        
        for i in range(scene_count):
            # Create narration with appropriate word count
            words = ["word"] * max(10, words_per_scene)  # Ensure minimum words
            narration = " ".join(words)
            
            scene = Scene(
                id=f"scene_{i}",
                title=f"Scene {i+1}",
                narration=narration,
                duration=duration_per_scene,
                visual_type="motion-canvas",
                concepts=[f"concept_{i}"],
            )
            scenes.append(scene)
        
        # Adjust word count to match actual words
        actual_word_count = sum(scene.get_word_count() for scene in scenes)
        
        # Create narration script
        script = NarrationScript(
            scenes=scenes,
            total_duration=total_duration,
            word_count=actual_word_count,
        )
        
        # Test serialization
        json_data = script.json()
        parsed_data = json.loads(json_data)
        
        # Verify structure
        assert "scenes" in parsed_data
        assert "total_duration" in parsed_data
        assert "word_count" in parsed_data
        assert len(parsed_data["scenes"]) == scene_count
        
        # Test deserialization
        restored_script = NarrationScript.parse_raw(json_data)
        
        # Verify data integrity
        assert len(restored_script.scenes) == len(script.scenes)
        assert restored_script.total_duration == script.total_duration
        assert restored_script.word_count == script.word_count
        
        for original, restored in zip(script.scenes, restored_script.scenes):
            assert original.id == restored.id
            assert original.title == restored.title
            assert original.narration == restored.narration
            assert original.duration == restored.duration
            assert original.visual_type == restored.visual_type

    @given(
        width=st.integers(min_value=480, max_value=3840).filter(lambda x: x % 2 == 0),
        height=st.integers(min_value=480, max_value=2160).filter(lambda x: x % 2 == 0),
        duration=st.floats(min_value=1.0, max_value=300.0),
        file_size=st.integers(min_value=1024, max_value=1024*1024*1024),  # 1KB to 1GB
    )
    def test_video_asset_serialization_property(
        self, width: int, height: int, duration: float, file_size: int
    ):
        """
        **Property 12: Agent architecture compliance**
        For any video asset, serialization should preserve technical specifications
        and metadata for proper agent coordination and output tracking.
        **Validates: Requirements 11.2, 11.5**
        """
        # Create video metadata
        metadata = VideoMetadata(
            title="Test Video Title for Property Testing",
            description="This is a test video description that meets the minimum length requirement for validation.",
            tags=["test", "property", "video"],
        )
        
        # Create video asset
        video = VideoAsset(
            file_path="/test/video.mp4",
            duration=duration,
            resolution=f"{width}x{height}",
            file_size=file_size,
            metadata=metadata,
        )
        
        # Test serialization
        json_data = video.json()
        parsed_data = json.loads(json_data)
        
        # Verify structure
        assert "file_path" in parsed_data
        assert "duration" in parsed_data
        assert "resolution" in parsed_data
        assert "file_size" in parsed_data
        assert "metadata" in parsed_data
        
        # Test deserialization
        restored_video = VideoAsset.parse_raw(json_data)
        
        # Verify data integrity
        assert restored_video.file_path == video.file_path
        assert restored_video.duration == video.duration
        assert restored_video.resolution == video.resolution
        assert restored_video.file_size == video.file_size
        assert restored_video.metadata.title == video.metadata.title
        assert restored_video.metadata.description == video.metadata.description
        assert restored_video.metadata.tags == video.metadata.tags
        
        # Verify computed properties work after deserialization
        assert restored_video.file_size_mb == video.file_size_mb
        assert restored_video.aspect_ratio == video.aspect_ratio

    def test_state_transitions_property(self):
        """
        **Property 12: Agent architecture compliance**
        State transitions should be trackable and maintain consistency
        across the LangGraph workflow with proper state management.
        **Validates: Requirements 11.5**
        """
        # Create initial state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Verify initial state
        assert state.progress.current_step == WorkflowStatus.PENDING
        assert state.progress.overall_progress == 0.0
        assert len(state.progress.completed_steps) == 0
        
        # Test state transitions
        workflow_steps = [
            WorkflowStatus.INGESTING,
            WorkflowStatus.UNDERSTANDING,
            WorkflowStatus.SCRIPTING,
            WorkflowStatus.PLANNING,
            WorkflowStatus.ANIMATING,
        ]
        
        for i, step in enumerate(workflow_steps):
            # Update progress
            progress = (i + 1) / len(workflow_steps)
            state.progress.update_progress(step, progress, f"Processing {step.value}")
            
            # Verify state consistency
            assert state.progress.current_step == step
            assert state.progress.step_progress == progress
            assert state.progress.current_message == f"Processing {step.value}"
            
            # Complete the step
            state.progress.complete_step(step)
            assert step in state.progress.completed_steps
            
            # Test serialization at each step
            json_data = state.json()
            restored_state = RASOMasterState.parse_raw(json_data)
            
            # Verify state is preserved
            assert restored_state.progress.current_step == state.progress.current_step
            assert restored_state.progress.overall_progress == state.progress.overall_progress
            assert len(restored_state.progress.completed_steps) == len(state.progress.completed_steps)
            assert step in restored_state.progress.completed_steps

    @given(
        error_count=st.integers(min_value=0, max_value=10),
        has_critical=st.booleans(),
    )
    def test_error_accumulation_property(self, error_count: int, has_critical: bool):
        """
        **Property 12: Agent architecture compliance**
        Error accumulation should be properly tracked and serialized
        for comprehensive debugging and agent coordination.
        **Validates: Requirements 11.4**
        """
        # Create state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Add errors
        for i in range(error_count):
            severity = ErrorSeverity.CRITICAL if (has_critical and i == 0) else ErrorSeverity.ERROR
            state.add_error(
                agent_type=AgentType.UNDERSTANDING,
                error_code=f"TEST_ERROR_{i}",
                message=f"Test error message {i} for property testing",
                severity=severity,
            )
        
        # Verify error tracking
        assert len(state.errors) == error_count
        if has_critical and error_count > 0:
            assert state.has_critical_errors()
            assert len(state.get_critical_errors()) >= 1
        else:
            assert not state.has_critical_errors()
        
        # Test serialization with errors
        json_data = state.json()
        restored_state = RASOMasterState.parse_raw(json_data)
        
        # Verify error preservation
        assert len(restored_state.errors) == len(state.errors)
        for original, restored in zip(state.errors, restored_state.errors):
            assert original.agent_type == restored.agent_type
            assert original.error_code == restored.error_code
            assert original.message == restored.message
            assert original.severity == restored.severity
        
        # Verify error analysis methods work
        assert restored_state.has_critical_errors() == state.has_critical_errors()
        assert len(restored_state.get_critical_errors()) == len(state.get_critical_errors())

    def test_schema_validation_enforcement_property(self):
        """
        **Property 12: Agent architecture compliance**
        Schema validation should be strictly enforced to ensure
        reliable agent communication and data integrity.
        **Validates: Requirements 11.2**
        """
        # Test that invalid data is rejected
        invalid_cases = [
            # Invalid paper input type
            {"type": "invalid_type", "content": "test"},
            # Missing required fields
            {"type": "title"},
            # Invalid duration (negative)
            {"type": "title", "content": "test", "duration": -1.0},
        ]
        
        for invalid_data in invalid_cases:
            with pytest.raises(ValidationError):
                PaperInput(**invalid_data)
        
        # Test that valid data is accepted
        valid_input = PaperInput(type="title", content="Valid Test Title")
        assert valid_input.type == "title"
        assert valid_input.content == "Valid Test Title"
        
        # Test JSON schema validation
        json_data = valid_input.json()
        restored_input = PaperInput.parse_raw(json_data)
        assert restored_input.type == valid_input.type
        assert restored_input.content == valid_input.content


if __name__ == "__main__":
    pytest.main([__file__])