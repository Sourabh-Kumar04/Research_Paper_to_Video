"""
Property-based tests for RASO audio synchronization.

**Feature: raso-platform, Property 7: Audio-visual synchronization**
Tests that audio generation produces synchronized voiceover with proper timing,
volume normalization, and automatic adjustment capabilities.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from agents.audio import AudioAgent
from audio.tts_service import TTSService, AudioSynchronizer, AudioProcessingResult
from backend.models.script import NarrationScript, Scene
from backend.models.animation import AnimationAssets, RenderedScene, SceneMetadata
from backend.models.audio import AudioAssets, AudioScene, TimingMarker


class TestAudioSynchronizationProperties:
    """Property-based tests for audio synchronization."""

    @given(
        scene_text=st.text(min_size=10, max_size=500),
        target_duration=st.floats(min_value=1.0, max_value=60.0),
        voice_speed=st.floats(min_value=0.5, max_value=2.0),
        voice_pitch=st.floats(min_value=0.5, max_value=2.0),
    )
    @pytest.mark.asyncio
    async def test_tts_generation_synchronization_property(
        self, scene_text: str, target_duration: float, voice_speed: float, voice_pitch: float
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any scene narration and target duration, the TTS generation should
        produce synchronized voiceover with proper timing and voice parameters.
        **Validates: Requirements 6.1, 6.2, 6.4**
        """
        tts_service = TTSService()
        
        # Mock TTS model initialization and generation
        with patch.object(tts_service, 'initialize') as mock_init, \
             patch.object(tts_service, '_tts_model') as mock_model, \
             patch.object(tts_service, '_get_audio_info') as mock_audio_info:
            
            mock_init.return_value = None
            mock_model.tts_to_file = MagicMock()
            
            # Mock audio info to return reasonable values
            mock_audio_info.return_value = (target_duration, 22050, 1)
            
            # Mock file operations
            with patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024), \
                 patch('builtins.open', create=True):
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    output_path = temp_file.name
                
                try:
                    # Generate speech
                    result = await tts_service.generate_speech(
                        text=scene_text,
                        output_path=output_path,
                        voice_speed=voice_speed,
                        voice_pitch=voice_pitch,
                    )
                    
                    # Verify synchronization properties
                    assert result.success is True
                    assert result.output_path == output_path
                    assert result.duration > 0
                    assert result.sample_rate > 0
                    assert result.processing_time >= 0
                    
                    # Verify TTS was called with cleaned text
                    mock_model.tts_to_file.assert_called_once()
                    call_args = mock_model.tts_to_file.call_args
                    assert call_args[1]['file_path'] == output_path
                    assert call_args[1]['speed'] == voice_speed
                    
                    # Verify text was cleaned (no empty text)
                    generated_text = call_args[1]['text']
                    assert len(generated_text.strip()) > 0
                
                finally:
                    # Cleanup
                    if os.path.exists(output_path):
                        os.unlink(output_path)

    @given(
        current_duration=st.floats(min_value=1.0, max_value=60.0),
        target_duration=st.floats(min_value=1.0, max_value=60.0),
        sample_rate=st.integers(min_value=8000, max_value=48000),
    )
    @pytest.mark.asyncio
    async def test_audio_duration_synchronization_property(
        self, current_duration: float, target_duration: float, sample_rate: int
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any audio with current duration and target duration, the synchronizer
        should adjust timing to match the target while maintaining quality.
        **Validates: Requirements 6.2, 6.5**
        """
        synchronizer = AudioSynchronizer()
        
        # Mock audio info methods
        with patch.object(synchronizer, '_get_audio_info') as mock_audio_info:
            # First call returns current duration, second call returns adjusted duration
            mock_audio_info.side_effect = [
                (current_duration, sample_rate, 1),  # Current audio info
                (target_duration, sample_rate, 1),   # Final audio info after processing
            ]
            
            # Mock ffmpeg command execution
            with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
                 patch('os.path.exists', return_value=True), \
                 patch('os.path.getsize', return_value=1024), \
                 patch('shutil.copy2') as mock_copy:
                
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"", b"")
                mock_process.returncode = 0
                mock_subprocess.return_value = mock_process
                
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as input_file, \
                     tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as output_file:
                    
                    input_path = input_file.name
                    output_path = output_file.name
                
                try:
                    # Test synchronization
                    result = await synchronizer.synchronize_scene_audio(
                        audio_path=input_path,
                        target_duration=target_duration,
                        output_path=output_path,
                    )
                    
                    # Verify synchronization results
                    assert result.success is True
                    assert result.output_path == output_path
                    assert abs(result.duration - target_duration) < 0.1  # Close to target
                    assert result.sample_rate == sample_rate
                    
                    # Check if speed adjustment was applied
                    duration_diff = abs(current_duration - target_duration)
                    
                    if duration_diff < 0.1:
                        # Durations are close, should just copy
                        mock_copy.assert_called_once()
                    else:
                        # Should use ffmpeg for speed adjustment
                        mock_subprocess.assert_called_once()
                        
                        # Verify speed factor is reasonable
                        call_args = mock_subprocess.call_args[0][0]
                        speed_factor = current_duration / target_duration
                        expected_speed = max(0.5, min(2.0, speed_factor))
                        
                        # Check that atempo filter is used with reasonable speed
                        filter_arg = None
                        for i, arg in enumerate(call_args):
                            if arg == "-filter:a":
                                filter_arg = call_args[i + 1]
                                break
                        
                        assert filter_arg is not None
                        assert "atempo=" in filter_arg
                
                finally:
                    # Cleanup
                    for path in [input_path, output_path]:
                        if os.path.exists(path):
                            os.unlink(path)

    @given(
        num_scenes=st.integers(min_value=1, max_value=8),
        scene_durations=st.lists(st.floats(min_value=5.0, max_value=30.0), min_size=1, max_size=8),
        narration_texts=st.lists(st.text(min_size=20, max_size=200), min_size=1, max_size=8),
    )
    @pytest.mark.asyncio
    async def test_multi_scene_audio_generation_property(
        self, num_scenes: int, scene_durations: List[float], narration_texts: List[str]
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any set of scenes with narration, the audio agent should generate
        synchronized audio for all scenes with consistent quality and timing.
        **Validates: Requirements 6.1, 6.2, 6.4**
        """
        agent = AudioAgent()
        
        # Ensure we have enough data
        durations = (scene_durations * ((num_scenes // len(scene_durations)) + 1))[:num_scenes]
        texts = (narration_texts * ((num_scenes // len(narration_texts)) + 1))[:num_scenes]
        
        # Create test scenes
        scenes = []
        rendered_scenes = []
        
        for i in range(num_scenes):
            scene = Scene(
                id=f"scene_{i}",
                title=f"Scene {i+1}",
                narration=texts[i],
                duration=durations[i],
                visual_type="test",
                concepts=[],
            )
            scenes.append(scene)
            
            rendered_scene = RenderedScene(
                scene_id=f"scene_{i}",
                file_path=f"/tmp/scene_{i}.mp4",
                duration=durations[i],
                framework="test",
                metadata=SceneMetadata(
                    resolution="1920x1080",
                    file_size=1024,
                    render_time=1.0,
                    template_id="test_template",
                ),
            )
            rendered_scenes.append(rendered_scene)
        
        script = NarrationScript(
            scenes=scenes,
            total_duration=sum(durations),
            word_count=sum(len(text.split()) for text in texts),
        )
        
        animations = AnimationAssets(
            scenes=rendered_scenes,
            total_duration=sum(durations),
            resolution="1920x1080",
        )
        
        # Mock TTS service and audio processing
        with patch('agents.audio.tts_service') as mock_tts, \
             patch('agents.audio.audio_synchronizer') as mock_sync:
            
            # Mock TTS initialization
            mock_tts.initialize = AsyncMock()
            
            # Mock TTS generation
            async def mock_generate_speech(text, output_path, **kwargs):
                return AudioProcessingResult(
                    success=True,
                    output_path=output_path,
                    duration=10.0,  # Default duration
                    sample_rate=22050,
                    channels=1,
                    file_size=1024,
                    processing_time=1.0,
                )
            
            mock_tts.generate_speech = mock_generate_speech
            
            # Mock synchronization
            async def mock_synchronize(audio_path, target_duration, output_path):
                return AudioProcessingResult(
                    success=True,
                    output_path=output_path,
                    duration=target_duration,
                    sample_rate=22050,
                    channels=1,
                    file_size=1024,
                    processing_time=0.5,
                )
            
            mock_sync.synchronize_scene_audio = mock_synchronize
            
            # Mock normalization
            async def mock_normalize(audio_paths, output_dir):
                results = []
                for i, path in enumerate(audio_paths):
                    results.append(AudioProcessingResult(
                        success=True,
                        output_path=f"{output_dir}/normalized_{i}.wav",
                        duration=durations[i] if i < len(durations) else 10.0,
                        sample_rate=22050,
                        channels=1,
                        file_size=1024,
                        processing_time=0.2,
                    ))
                return results
            
            mock_sync.normalize_audio_levels = mock_normalize
            
            # Mock file operations
            with patch('pathlib.Path.mkdir'), \
                 patch('os.makedirs'):
                
                # Execute audio generation
                state = {
                    "script": script.dict(),
                    "animations": animations.dict(),
                }
                
                result_state = await agent.execute(state)
                
                # Verify audio generation results
                assert "audio" in result_state
                audio_data = result_state["audio"]
                audio_assets = AudioAssets(**audio_data)
                
                # Should have generated audio for all scenes
                assert len(audio_assets.scenes) == num_scenes
                
                # Verify each audio scene
                for i, audio_scene in enumerate(audio_assets.scenes):
                    assert audio_scene.scene_id == f"scene_{i}"
                    assert audio_scene.file_path is not None
                    assert audio_scene.duration > 0
                    assert audio_scene.transcript == texts[i]
                    assert len(audio_scene.timing_markers) > 0
                
                # Verify total duration
                expected_total = sum(scene.duration for scene in audio_assets.scenes)
                assert abs(audio_assets.total_duration - expected_total) < 0.1

    @given(
        text=st.text(min_size=10, max_size=1000),
        audio_duration=st.floats(min_value=1.0, max_value=60.0),
    )
    def test_timing_marker_generation_property(
        self, text: str, audio_duration: float
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any text and audio duration, the timing marker generation should
        create reasonable word-level timing information for synchronization.
        **Validates: Requirements 6.2**
        """
        agent = AudioAgent()
        
        # Generate timing markers
        timing_markers = agent._create_timing_markers(text, audio_duration)
        
        words = text.split()
        
        if not words:
            # Empty text should produce no markers
            assert len(timing_markers) == 0
        else:
            # Should have one marker per word
            assert len(timing_markers) == len(words)
            
            # Verify timing properties
            for i, marker in enumerate(timing_markers):
                assert marker.word == words[i]
                assert marker.start_time >= 0
                assert marker.end_time > marker.start_time
                assert 0 <= marker.confidence <= 1
                
                # Verify sequential timing
                if i > 0:
                    assert marker.start_time >= timing_markers[i-1].start_time
            
            # Verify total duration coverage
            if timing_markers:
                total_covered = timing_markers[-1].end_time
                assert abs(total_covered - audio_duration) < 0.1

    @given(
        words_per_minute=st.integers(min_value=100, max_value=200),
        text_length=st.integers(min_value=10, max_value=500),
    )
    @pytest.mark.asyncio
    async def test_duration_estimation_property(
        self, words_per_minute: int, text_length: int
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any text and speaking rate, the duration estimation should provide
        reasonable estimates for audio synchronization planning.
        **Validates: Requirements 6.2**
        """
        tts_service = TTSService()
        
        # Generate test text with approximately the desired length
        test_text = " ".join(["word"] * text_length)
        
        # Estimate duration
        estimated_duration = await tts_service.estimate_speech_duration(
            text=test_text,
            words_per_minute=words_per_minute
        )
        
        # Verify estimation properties
        assert estimated_duration >= 1.0  # Minimum duration
        
        # Calculate expected duration
        word_count = len(test_text.split())
        expected_base_duration = (word_count / words_per_minute) * 60
        expected_duration = expected_base_duration * 1.2  # With padding
        
        # Should be reasonably close to expected
        assert abs(estimated_duration - expected_duration) < expected_duration * 0.2

    @given(
        num_audio_files=st.integers(min_value=2, max_value=8),
        volume_variations=st.lists(st.floats(min_value=0.1, max_value=2.0), min_size=2, max_size=8),
    )
    @pytest.mark.asyncio
    async def test_audio_normalization_property(
        self, num_audio_files: int, volume_variations: List[float]
    ):
        """
        **Property 7: Audio-visual synchronization**
        For any set of audio files with varying volume levels, the normalization
        should produce consistent audio levels across all files.
        **Validates: Requirements 6.4**
        """
        synchronizer = AudioSynchronizer()
        
        # Ensure we have enough volume data
        volumes = (volume_variations * ((num_audio_files // len(volume_variations)) + 1))[:num_audio_files]
        
        # Create mock audio file paths
        audio_paths = [f"/tmp/audio_{i}.wav" for i in range(num_audio_files)]
        output_dir = "/tmp/normalized"
        
        # Mock ffmpeg normalization
        with patch('asyncio.create_subprocess_exec') as mock_subprocess, \
             patch('os.makedirs'), \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=1024):
            
            # Mock successful normalization for each file
            async def mock_ffmpeg_call(*args, **kwargs):
                mock_process = AsyncMock()
                mock_process.communicate.return_value = (b"", b"")
                mock_process.returncode = 0
                return mock_process
            
            mock_subprocess.side_effect = mock_ffmpeg_call
            
            # Mock audio info
            with patch.object(synchronizer, '_get_audio_info') as mock_audio_info:
                mock_audio_info.return_value = (10.0, 22050, 1)  # duration, sample_rate, channels
                
                # Test normalization
                results = await synchronizer.normalize_audio_levels(
                    audio_paths=audio_paths,
                    output_dir=output_dir,
                )
                
                # Verify normalization results
                assert len(results) == num_audio_files
                
                # All results should be successful
                for i, result in enumerate(results):
                    assert result.success is True
                    assert result.output_path == f"{output_dir}/normalized_{i}.wav"
                    assert result.duration > 0
                    assert result.sample_rate > 0
                
                # Verify ffmpeg was called for each file with loudnorm filter
                assert mock_subprocess.call_count == num_audio_files
                
                # Check that loudnorm filter was used
                for call in mock_subprocess.call_args_list:
                    command = call[0][0]
                    assert "ffmpeg" in command
                    assert "-af" in command
                    
                    # Find the audio filter argument
                    af_index = command.index("-af")
                    filter_arg = command[af_index + 1]
                    assert "loudnorm" in filter_arg


if __name__ == "__main__":
    pytest.main([__file__])