"""
Property-based tests for RASO animation rendering reliability.

**Feature: raso-platform, Property 6: Animation safety and validation**
Tests that animation rendering implements retry logic with fallback templates,
validates output quality and resolution requirements, and maintains reliability.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from agents.rendering import (
    ManimAgent,
    MotionCanvasAgent,
    RemotionAgent,
    RenderingCoordinator,
    RenderingResult,
    RenderingError,
)
from backend.models.visual import VisualPlan, ScenePlan
from backend.models.animation import AnimationAssets, RenderedScene
from animation.templates import TemplateFramework
from backend.config import RASOMasterConfig, AnimationConfig


class TestRenderingReliabilityProperties:
    """Property-based tests for rendering reliability."""

    @given(
        scene_id=st.text(min_size=5, max_size=20),
        template_id=st.text(min_size=5, max_size=30),
        duration=st.floats(min_value=1.0, max_value=60.0),
        framework=st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
    )
    @pytest.mark.asyncio
    async def test_fallback_template_retry_property(
        self, scene_id: str, template_id: str, duration: float, framework: TemplateFramework
    ):
        """
        **Property 6: Animation safety and validation**
        For any scene rendering failure, the system should automatically
        retry with fallback templates and implement proper error recovery.
        **Validates: Requirements 5.4, 5.5**
        """
        # Create appropriate agent for framework
        if framework == TemplateFramework.MANIM:
            agent = ManimAgent()
        elif framework == TemplateFramework.MOTION_CANVAS:
            agent = MotionCanvasAgent()
        else:
            agent = RemotionAgent()
        
        # Create scene plan
        scene_plan = ScenePlan(
            scene_id=scene_id,
            framework=framework.value,
            template=template_id,
            parameters={"duration": duration},
            duration=duration,
        )
        
        # Mock primary rendering to fail
        original_render = agent.render_scene
        call_count = 0
        
        async def mock_render_scene(scene_plan_arg, output_path, **kwargs):
            nonlocal call_count
            call_count += 1
            
            if call_count == 1:
                # First call (primary template) fails
                return RenderingResult(
                    success=False,
                    duration=duration,
                    resolution="1920x1080",
                    render_time=1.0,
                    error_message="Primary template failed",
                )
            else:
                # Second call (fallback template) succeeds
                return RenderingResult(
                    success=True,
                    output_path=output_path,
                    duration=duration,
                    resolution="1920x1080",
                    file_size=1024,
                    render_time=2.0,
                )
        
        # Mock template engine to provide fallback
        with patch('agents.rendering.template_engine') as mock_engine:
            mock_engine.get_fallback_template.return_value = f"fallback_{framework.value}"
            mock_engine.generate_animation_code.return_value = "# Safe fallback code"
            
            with patch.object(agent, 'render_scene', side_effect=mock_render_scene):
                # Test fallback mechanism
                result = await agent.render_scene_with_fallback(scene_plan)
                
                # Should succeed with fallback
                assert result.success is True
                assert result.output_path is not None
                assert result.duration == duration
                assert result.error_message is None
                
                # Should have called render_scene twice (primary + fallback)
                assert call_count == 2
                
                # Should have requested fallback template
                mock_engine.get_fallback_template.assert_called_once_with(framework)

    @given(
        resolution=st.sampled_from(["1280x720", "1920x1080", "3840x2160"]),
        file_size=st.integers(min_value=1024, max_value=100*1024*1024),  # 1KB to 100MB
        render_time=st.floats(min_value=0.1, max_value=300.0),
        duration=st.floats(min_value=1.0, max_value=120.0),
    )
    def test_output_quality_validation_property(
        self, resolution: str, file_size: int, render_time: float, duration: float
    ):
        """
        **Property 6: Animation safety and validation**
        For any rendered output, the system should verify that quality
        and resolution requirements are met according to configuration.
        **Validates: Requirements 5.5**
        """
        # Create rendering result
        result = RenderingResult(
            success=True,
            output_path="/tmp/test_video.mp4",
            duration=duration,
            resolution=resolution,
            file_size=file_size,
            render_time=render_time,
        )
        
        # Verify quality metrics are present
        assert result.resolution is not None
        assert len(result.resolution) > 0
        assert "x" in result.resolution  # Should be in format "WIDTHxHEIGHT"
        
        # Verify resolution format
        width_str, height_str = result.resolution.split("x")
        width = int(width_str)
        height = int(height_str)
        assert width > 0
        assert height > 0
        
        # Verify file size is reasonable
        assert result.file_size >= 0
        
        # Verify duration matches expected
        assert result.duration > 0
        assert abs(result.duration - duration) < 0.1  # Allow small tolerance
        
        # Verify render time is recorded
        assert result.render_time >= 0

    @given(
        num_scenes=st.integers(min_value=1, max_value=10),
        frameworks=st.lists(
            st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
            min_size=1,
            max_size=10
        ),
        success_rates=st.lists(st.booleans(), min_size=1, max_size=10),
    )
    @pytest.mark.asyncio
    async def test_coordinated_rendering_reliability_property(
        self, num_scenes: int, frameworks: List[TemplateFramework], success_rates: List[bool]
    ):
        """
        **Property 6: Animation safety and validation**
        For any combination of scenes and frameworks, the rendering coordinator
        should handle partial failures gracefully and maintain system reliability.
        **Validates: Requirements 5.4, 5.5**
        """
        coordinator = RenderingCoordinator()
        
        # Ensure we have enough data
        frameworks = (frameworks * ((num_scenes // len(frameworks)) + 1))[:num_scenes]
        success_rates = (success_rates * ((num_scenes // len(success_rates)) + 1))[:num_scenes]
        
        # Create scene plans
        scene_plans = []
        for i in range(num_scenes):
            scene_plans.append(ScenePlan(
                scene_id=f"scene_{i}",
                framework=frameworks[i].value,
                template=f"template_{i}",
                parameters={"duration": 10.0},
                duration=10.0,
            ))
        
        visual_plan = VisualPlan(
            scenes=scene_plans,
            transitions=[],
            overall_style=MagicMock(),
        )
        
        # Mock agent execution
        async def mock_agent_execute(state):
            result_state = state.copy()
            rendered_scenes = []
            
            for i, scene_plan in enumerate(scene_plans):
                if scene_plan.framework == self.framework.value and success_rates[i]:
                    rendered_scenes.append({
                        "scene_id": scene_plan.scene_id,
                        "file_path": f"/tmp/{scene_plan.scene_id}.mp4",
                        "duration": scene_plan.duration,
                        "framework": scene_plan.framework,
                        "metadata": {
                            "resolution": "1920x1080",
                            "file_size": 1024,
                            "render_time": 2.0,
                            "template_id": scene_plan.template,
                        },
                    })
            
            result_state["animations"] = {
                "scenes": rendered_scenes,
                "total_duration": sum(s["duration"] for s in rendered_scenes),
                "resolution": "1920x1080",
            }
            
            return result_state
        
        # Mock all agents
        for framework, agent in coordinator.agents.items():
            agent.framework = framework  # Set framework for mock
            agent.execute = mock_agent_execute
            agent.validate_environment = lambda: []  # No environment errors
        
        # Execute coordinated rendering
        state = {"visual_plan": visual_plan.dict()}
        result_state = await coordinator.execute(state)
        
        # Verify coordination results
        assert "animations" in result_state
        animations = result_state["animations"]
        
        # Should have attempted all scenes
        assert "scenes" in animations
        rendered_scenes = animations["scenes"]
        
        # Number of successful renders should match success rate
        expected_successes = sum(success_rates)
        assert len(rendered_scenes) <= expected_successes  # May be less due to framework filtering
        
        # All rendered scenes should be valid
        for scene_data in rendered_scenes:
            assert "scene_id" in scene_data
            assert "file_path" in scene_data
            assert "duration" in scene_data
            assert scene_data["duration"] > 0

    @given(
        timeout_seconds=st.integers(min_value=1, max_value=300),
        command_duration=st.integers(min_value=1, max_value=400),
    )
    @pytest.mark.asyncio
    async def test_timeout_protection_property(
        self, timeout_seconds: int, command_duration: int
    ):
        """
        **Property 6: Animation safety and validation**
        For any rendering command, the system should implement timeout
        protection to prevent hanging processes and maintain system stability.
        **Validates: Requirements 5.4**
        """
        agent = ManimAgent()
        
        # Mock a long-running command
        async def mock_long_command():
            import asyncio
            await asyncio.sleep(command_duration)
            return 0, "output", ""
        
        # Test timeout behavior
        if command_duration > timeout_seconds:
            # Should timeout
            with pytest.raises(RenderingError, match="timed out"):
                await agent.run_command_with_timeout(
                    command=["sleep", str(command_duration)],
                    timeout=timeout_seconds,
                )
        else:
            # Should complete normally (but we'll mock it to avoid actual sleep)
            with patch('asyncio.create_subprocess_exec') as mock_subprocess:
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"output", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                return_code, stdout, stderr = await agent.run_command_with_timeout(
                    command=["echo", "test"],
                    timeout=timeout_seconds,
                )
                
                assert return_code == 0
                assert stdout == "output"
                assert stderr == ""

    @given(
        framework=st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
        has_dependencies=st.booleans(),
    )
    def test_environment_validation_property(
        self, framework: TemplateFramework, has_dependencies: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any rendering framework, the system should validate the environment
        and identify missing dependencies before attempting rendering.
        **Validates: Requirements 5.4, 5.5**
        """
        # Create appropriate agent
        if framework == TemplateFramework.MANIM:
            agent = ManimAgent()
            expected_commands = ["manim", "ffmpeg", "latex"]
        elif framework == TemplateFramework.MOTION_CANVAS:
            agent = MotionCanvasAgent()
            expected_commands = ["node", "npm"]
        else:
            agent = RemotionAgent()
            expected_commands = ["node", "npm"]
        
        # Mock subprocess calls
        def mock_subprocess_run(command, **kwargs):
            cmd_name = command[0]
            
            if has_dependencies and cmd_name in expected_commands:
                # Simulate successful dependency check
                result = MagicMock()
                result.returncode = 0
                return result
            else:
                # Simulate missing dependency
                raise FileNotFoundError(f"Command not found: {cmd_name}")
        
        with patch('subprocess.run', side_effect=mock_subprocess_run):
            validation_errors = agent.validate_environment()
            
            if has_dependencies:
                # Should have no errors when dependencies are present
                assert len(validation_errors) == 0
            else:
                # Should detect missing dependencies
                assert len(validation_errors) > 0
                
                # Should mention specific missing commands
                error_text = " ".join(validation_errors).lower()
                assert any(cmd in error_text for cmd in expected_commands)

    @given(
        sandbox_permissions=st.integers(min_value=0o000, max_value=0o777),
        cleanup_success=st.booleans(),
    )
    def test_sandbox_security_property(
        self, sandbox_permissions: int, cleanup_success: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any rendering operation, the system should create secure
        sandboxed environments and properly clean up resources.
        **Validates: Requirements 5.1, 5.4**
        """
        agent = ManimAgent()
        
        # Test sandbox creation
        with patch('tempfile.mkdtemp') as mock_mkdtemp, \
             patch('os.chmod') as mock_chmod, \
             patch('os.path.exists') as mock_exists, \
             patch('shutil.rmtree') as mock_rmtree:
            
            mock_sandbox_path = "/tmp/test_sandbox"
            mock_mkdtemp.return_value = mock_sandbox_path
            
            # Create sandbox
            sandbox_path = agent.create_sandbox_environment()
            
            # Verify sandbox creation
            assert sandbox_path == mock_sandbox_path
            mock_mkdtemp.assert_called_once()
            
            # Verify restrictive permissions are set
            mock_chmod.assert_called_once_with(mock_sandbox_path, 0o700)
            
            # Test cleanup
            mock_exists.return_value = True
            
            if cleanup_success:
                # Successful cleanup
                agent.cleanup_sandbox(sandbox_path)
                mock_rmtree.assert_called_once_with(sandbox_path)
            else:
                # Cleanup failure (should not raise exception)
                mock_rmtree.side_effect = OSError("Permission denied")
                
                # Should handle cleanup failure gracefully
                try:
                    agent.cleanup_sandbox(sandbox_path)
                except Exception:
                    pytest.fail("Cleanup failure should be handled gracefully")

    @given(
        scene_parameters=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.floats()),
            min_size=1,
            max_size=5,
        ),
        template_exists=st.booleans(),
    )
    @pytest.mark.asyncio
    async def test_code_generation_safety_property(
        self, scene_parameters: Dict[str, Any], template_exists: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any scene parameters, the code generation should validate
        templates and parameters to ensure safe execution.
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        agent = ManimAgent()
        
        scene_plan = ScenePlan(
            scene_id="test_scene",
            framework=TemplateFramework.MANIM.value,
            template="test_template",
            parameters=scene_parameters,
            duration=10.0,
        )
        
        # Mock template engine
        with patch('agents.rendering.template_engine') as mock_engine:
            if template_exists:
                # Template exists and generates safe code
                mock_engine.generate_animation_code.return_value = """
# Safe generated code
from manim import *

class TestScene(Scene):
    def construct(self):
        text = Text("Hello World")
        self.play(Write(text))
"""
            else:
                # Template not found
                mock_engine.generate_animation_code.side_effect = ValueError("Template not found")
            
            # Mock file operations and command execution
            with patch('builtins.open', create=True), \
                 patch.object(agent, 'run_command_with_timeout') as mock_run_command, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024):
                
                if template_exists:
                    # Successful rendering
                    mock_run_command.return_value = (0, "Success", "")
                    
                    result = await agent.render_scene(scene_plan, "/tmp/output.mp4")
                    
                    # Should succeed with valid template
                    assert result.success is True
                    assert result.output_path is not None
                    
                    # Should have called template engine with parameters
                    mock_engine.generate_animation_code.assert_called_once()
                    call_args = mock_engine.generate_animation_code.call_args
                    assert call_args[1]["parameters"] == scene_parameters
                
                else:
                    # Template not found - should fail gracefully
                    result = await agent.render_scene(scene_plan, "/tmp/output.mp4")
                    
                    # Should fail but not crash
                    assert result.success is False
                    assert result.error_message is not None


if __name__ == "__main__":
    pytest.main([__file__])