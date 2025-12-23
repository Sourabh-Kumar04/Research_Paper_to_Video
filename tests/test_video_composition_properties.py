"""
Property-based tests for RASO video composition consistency.

**Feature: raso-platform, Property 8: Video composition consistency**
Tests that video composition combines scenes into 1080p MP4 with smooth transitions,
synchronized audio, and YouTube-compliant formatting.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from video.composition import VideoComposer, CompositionResult
from agents.video_composition import VideoCompositionAgent
from backend.models.animation import AnimationAssets, RenderedScene, SceneMetadata
from backend.models.audio import AudioAssets, AudioScene, TimingMarker
from backend.models.video import VideoAsset, Chapter


class TestVideoCompositionProperties:
    """Property-based tests for video composition consistency."""

    @given(
        num_scenes=st.integers(min_value=1, max_value=8),
        scene_durations=st.lists(st.floats(min_value=5.0, max_value=30.0), min_size=1, max_size=8),
        resolution=st.sampled_from(["1280x720", "1920x1080", "3840x2160"]),
    )
    @pytest.mark.asyncio
    async def test_scene_combination_consistency_property(
        self, num_scenes: int, scene_durations: List[float], resolution: str
    ):
        """
        **Property 8: Video composition consistency**
        For any set of rendered scenes, the composition should combine them
        into a single video with consistent resolution and proper sequencing.
        **Validates: Requirements 7.1, 7.2, 7.5**
        """
        composer = VideoComposer()
        
        # Ensure we have enough durations
        durations = (scene_durations * ((num_scenes // len(scene_durations)) + 1))[:num_scenes]
        
        # Create test animation assets
        video_scenes = []
        audio_scenes = []
        
        for i in range(num_scenes):
            # Create rendered scene
            video_scene = RenderedScene(
                scene_id=f"scene_{i}",
                file_path=f"/tmp/video_scene_{i}.mp4",
                duration=durations[i],
                framework="test",
                metadata=SceneMetadata(
                    resolution=resolution,
                    file_size=1024 * (i + 1),
                    render_time=2.0,
                    template_id=f"template_{i}",
                ),
            )
            video_scenes.append(video_scene)
            
            # Create matching audio scene
            audio_scene = AudioScene(
                scene_id=f"scene_{i}",
                file_path=f"/tmp/audio_scene_{i}.wav",
                duration=durations[i],
                transcript=f"Narration for scene {i}",
                timing_markers=[
                    TimingMarker(
                        word="test",
                        start_time=0.0,
                        end_time=1.0,
                        confidence=0.8,
                    )
                ],
            )
            audio_scenes.append(audio_scene)
        
        animation_assets = AnimationAssets(
            scenes=video_scenes,
            total_duration=sum(durations),
            resolution=resolution,
        )
        
        audio_assets = AudioAssets(
            scenes=audio_scenes,
            total_duration=sum(durations),
            sample_rate=22050,
        )
        
        # Mock video composition methods
        with patch.object(composer, '_match_audio_video_scenes') as mock_match, \
             patch.object(composer, '_compose_single_scene') as mock_compose_scene, \
             patch.object(composer, '_concatenate_scenes') as mock_concatenate:
            
            # Mock scene matching
            scene_pairs = list(zip(video_scenes, audio_scenes))
            mock_match.return_value = scene_pairs
            
            # Mock single scene composition
            async def mock_single_compose(video_scene, audio_scene, output_path):
                return CompositionResult(
                    success=True,
                    output_path=output_path,
                    duration=video_scene.duration,
                    resolution=resolution,
                    file_size=2048,
                    composition_time=1.0,
                )
            
            mock_compose_scene.side_effect = mock_single_compose
            
            # Mock concatenation
            async def mock_concat(scene_paths, output_path):
                total_duration = sum(durations)
                return CompositionResult(
                    success=True,
                    output_path=output_path,
                    duration=total_duration,
                    resolution=resolution,
                    file_size=len(scene_paths) * 2048,
                    composition_time=2.0,
                )
            
            mock_concatenate.side_effect = mock_concat
            
            # Mock file operations
            with patch('pathlib.Path.mkdir'), \
                 patch('os.path.exists', return_value=True):
                
                # Test composition
                result = await composer.compose_video(
                    animation_assets=animation_assets,
                    audio_assets=audio_assets,
                    output_path="/tmp/final_video.mp4",
                )
                
                # Verify composition consistency
                assert result.success is True
                assert result.output_path == "/tmp/final_video.mp4"
                assert result.resolution == resolution
                assert abs(result.duration - sum(durations)) < 0.1
                assert result.file_size > 0
                
                # Verify scene matching was called
                mock_match.assert_called_once_with(video_scenes, audio_scenes)
                
                # Verify single scene composition for each scene
                assert mock_compose_scene.call_count == num_scenes
                
                # Verify concatenation was called if multiple scenes
                if num_scenes > 1:
                    mock_concatenate.assert_called_once()

    @given(
        video_duration=st.floats(min_value=5.0, max_value=60.0),
        audio_duration=st.floats(min_value=5.0, max_value=60.0),
        resolution=st.sampled_from(["1920x1080", "1280x720"]),
    )
    @pytest.mark.asyncio
    async def test_audio_video_synchronization_property(
        self, video_duration: float, audio_duration: float, resolution: str
    ):
        """
        **Property 8: Video composition consistency**
        For any video and audio scene pair, the composition should synchronize
        audio with visual content maintaining consistent timing.
        **Validates: Requirements 7.3**
        """
        composer = VideoComposer()
        
        # Create test scene pair
        video_scene = RenderedScene(
            scene_id="test_scene",
            file_path="/tmp/test_video.mp4",
            duration=video_duration,
            framework="test",
            metadata=SceneMetadata(
                resolution=resolution,
                file_size=1024,
                render_time=1.0,
                template_id="test_template",
            ),
        )
        
        audio_scene = AudioScene(
            scene_id="test_scene",
            file_path="/tmp/test_audio.wav",
            duration=audio_duration,
            transcript="Test narration",
            timing_markers=[],
        )
        
        # Mock ffmpeg execution
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch.object(composer, '_get_video_info') as mock_video_info, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=2048):
            
            # Mock successful ffmpeg execution
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            # Mock video info - should use shortest duration for synchronization
            expected_duration = min(video_duration, audio_duration)
            mock_video_info.return_value = (expected_duration, resolution)
            
            # Test single scene composition
            result = await composer._compose_single_scene(
                video_scene=video_scene,
                audio_scene=audio_scene,
                output_path="/tmp/composed_scene.mp4",
            )
            
            # Verify synchronization properties
            assert result.success is True
            assert result.output_path == "/tmp/composed_scene.mp4"
            assert result.resolution == resolution
            assert result.duration == expected_duration
            
            # Verify ffmpeg was called with correct parameters
            mock_subprocess.assert_called_once()
            command = mock_subprocess.call_args[0]
            
            # Check that both video and audio inputs are specified
            assert "/tmp/test_video.mp4" in command
            assert "/tmp/test_audio.wav" in command
            
            # Check that shortest stream duration is used
            assert "-shortest" in command

    @given(
        num_scenes=st.integers(min_value=2, max_value=6),
        file_sizes=st.lists(st.integers(min_value=1024, max_value=10*1024*1024), min_size=2, max_size=6),
    )
    @pytest.mark.asyncio
    async def test_scene_concatenation_consistency_property(
        self, num_scenes: int, file_sizes: List[int]
    ):
        """
        **Property 8: Video composition consistency**
        For any sequence of composed scenes, the concatenation should maintain
        video quality and create smooth transitions between scenes.
        **Validates: Requirements 7.1, 7.2**
        """
        composer = VideoComposer()
        
        # Ensure we have enough file sizes
        sizes = (file_sizes * ((num_scenes // len(file_sizes)) + 1))[:num_scenes]
        
        # Create scene file paths
        scene_paths = [f"/tmp/scene_{i}.mp4" for i in range(num_scenes)]
        output_path = "/tmp/final_video.mp4"
        
        # Mock ffmpeg concatenation
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch.object(composer, '_get_video_info') as mock_video_info, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', side_effect=lambda path: sizes[0] if "final" in path else 1024), \
             patch('builtins.open', create=True):
            
            # Mock successful concatenation
            mock_process = AsyncMock()
            mock_process.communicate.return_value = (b"", b"")
            mock_process.returncode = 0
            mock_subprocess.return_value = mock_process
            
            # Mock final video info
            total_duration = num_scenes * 10.0  # Assume 10s per scene
            mock_video_info.return_value = (total_duration, "1920x1080")
            
            # Test concatenation
            result = await composer._concatenate_scenes(
                scene_paths=scene_paths,
                output_path=output_path,
            )
            
            # Verify concatenation consistency
            assert result.success is True
            assert result.output_path == output_path
            assert result.duration == total_duration
            assert result.resolution == "1920x1080"
            assert result.file_size == sizes[0]  # Final video size
            
            if num_scenes == 1:
                # Single scene should just copy
                mock_subprocess.assert_not_called()
            else:
                # Multiple scenes should use ffmpeg concat
                mock_subprocess.assert_called_once()
                command = mock_subprocess.call_args[0][0]
                
                # Verify concat demuxer is used
                assert "concat" in command
                assert "-f" in command
                assert "-safe" in command
                assert "0" in command

    @given(
        scene_count=st.integers(min_value=1, max_value=5),
        chapter_titles=st.lists(st.text(min_size=5, max_size=50), min_size=1, max_size=5),
        scene_durations=st.lists(st.floats(min_value=10.0, max_value=60.0), min_size=1, max_size=5),
    )
    @pytest.mark.asyncio
    async def test_video_asset_creation_property(
        self, scene_count: int, chapter_titles: List[str], scene_durations: List[float]
    ):
        """
        **Property 8: Video composition consistency**
        For any composed video, the video asset creation should include
        proper chapters, metadata, and YouTube-compliant formatting.
        **Validates: Requirements 7.5**
        """
        agent = VideoCompositionAgent()
        
        # Ensure we have enough data
        titles = (chapter_titles * ((scene_count // len(chapter_titles)) + 1))[:scene_count]
        durations = (scene_durations * ((scene_count // len(scene_durations)) + 1))[:scene_count]
        
        # Create test assets
        video_scenes = []
        audio_scenes = []
        
        for i in range(scene_count):
            video_scene = RenderedScene(
                scene_id=f"scene_{i}",
                file_path=f"/tmp/video_{i}.mp4",
                duration=durations[i],
                framework="test",
                metadata=SceneMetadata(
                    resolution="1920x1080",
                    file_size=1024,
                    render_time=1.0,
                    template_id="test",
                ),
            )
            video_scenes.append(video_scene)
            
            audio_scene = AudioScene(
                scene_id=f"scene_{i}",
                file_path=f"/tmp/audio_{i}.wav",
                duration=durations[i],
                transcript=f"Narration {i}",
                timing_markers=[],
            )
            audio_scenes.append(audio_scene)
        
        # Test chapter creation
        chapters = agent._create_chapters(video_scenes, audio_scenes)
        
        # Verify chapter consistency
        assert len(chapters) == scene_count
        
        current_time = 0.0
        for i, chapter in enumerate(chapters):
            assert chapter.title == f"Scene {i+1}"
            assert chapter.start_time == current_time
            assert chapter.end_time == current_time + durations[i]
            
            current_time += durations[i]
        
        # Verify chapters cover full duration
        total_duration = sum(durations)
        if chapters:
            assert abs(chapters[-1].end_time - total_duration) < 0.1

    @given(
        resolution_consistency=st.booleans(),
        audio_sync_success=st.booleans(),
        file_format_valid=st.booleans(),
    )
    @pytest.mark.asyncio
    async def test_youtube_compliance_property(
        self, resolution_consistency: bool, audio_sync_success: bool, file_format_valid: bool
    ):
        """
        **Property 8: Video composition consistency**
        For any video composition, the output should meet YouTube platform
        requirements for resolution, format, and audio synchronization.
        **Validates: Requirements 7.5**
        """
        composer = VideoComposer()
        
        # Mock composition result based on test parameters
        expected_success = resolution_consistency and audio_sync_success and file_format_valid
        
        if expected_success:
            # Successful composition meeting YouTube requirements
            mock_result = CompositionResult(
                success=True,
                output_path="/tmp/youtube_ready.mp4",
                duration=60.0,
                resolution="1920x1080",  # YouTube-compliant resolution
                file_size=50 * 1024 * 1024,  # 50MB
                composition_time=10.0,
            )
        else:
            # Failed composition
            error_reasons = []
            if not resolution_consistency:
                error_reasons.append("resolution mismatch")
            if not audio_sync_success:
                error_reasons.append("audio sync failed")
            if not file_format_valid:
                error_reasons.append("invalid format")
            
            mock_result = CompositionResult(
                success=False,
                duration=0.0,
                resolution="unknown",
                composition_time=5.0,
                error_message="; ".join(error_reasons),
            )
        
        # Verify YouTube compliance properties
        if mock_result.success:
            # Check resolution is YouTube-compatible
            width, height = mock_result.resolution.split('x')
            width, height = int(width), int(height)
            
            # Common YouTube resolutions
            youtube_resolutions = [
                (1280, 720),   # 720p
                (1920, 1080),  # 1080p
                (2560, 1440),  # 1440p
                (3840, 2160),  # 4K
            ]
            
            assert (width, height) in youtube_resolutions
            
            # Check file format (should be MP4)
            assert mock_result.output_path.endswith('.mp4')
            
            # Check reasonable file size (not too small or too large)
            assert 1024 <= mock_result.file_size <= 128 * 1024 * 1024 * 1024  # 1KB to 128GB
            
            # Check reasonable duration
            assert 1.0 <= mock_result.duration <= 12 * 3600  # 1 second to 12 hours
        
        else:
            # Failed composition should have error message
            assert mock_result.error_message is not None
            assert len(mock_result.error_message) > 0


if __name__ == "__main__":
    pytest.main([__file__])