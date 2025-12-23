"""
Property-based tests for RASO configuration validation.

**Feature: raso-platform, Property 11: Local-first operation**
Tests that the system operates entirely using local resources and open-source software
by default, with external APIs as optional enhancements that don't break core functionality.
"""

import os
import tempfile
from pathlib import Path
from typing import Any, Dict

import pytest
from hypothesis import given, strategies as st

from backend.config import (
    RASOMasterConfig,
    LLMConfig,
    AnimationConfig,
    AudioConfig,
    VideoConfig,
    YouTubeConfig,
    SystemConfig,
)


class TestConfigurationProperties:
    """Property-based tests for configuration validation."""

    @given(
        env=st.sampled_from(["development", "production", "test"]),
        debug=st.booleans(),
        log_level=st.sampled_from(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]),
        api_port=st.integers(min_value=1024, max_value=65535),
        max_concurrent_jobs=st.integers(min_value=1, max_value=10),
    )
    def test_master_config_validation_property(
        self, env: str, debug: bool, log_level: str, api_port: int, max_concurrent_jobs: int
    ):
        """
        **Property 11: Local-first operation**
        For any valid configuration parameters, the master config should initialize
        successfully with local-first defaults and create required directories.
        **Validates: Requirements 10.1, 10.2, 10.3**
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            
            config = RASOMasterConfig(
                env=env,
                debug=debug,
                log_level=log_level,
                api_port=api_port,
                data_path=temp_path / "data",
                temp_path=temp_path / "temp", 
                log_path=temp_path / "logs",
                system=SystemConfig(max_concurrent_jobs=max_concurrent_jobs),
            )
            
            # Verify local-first defaults
            assert config.llm.provider == "ollama"  # Local LLM by default
            assert "localhost" in config.llm.ollama_url  # Local Ollama instance
            assert config.llm.openai_api_key is None  # No cloud API keys required
            assert config.llm.anthropic_api_key is None
            assert config.llm.google_api_key is None
            
            # Verify configuration is valid
            assert config.env == env
            assert config.debug == debug
            assert config.log_level == log_level
            assert config.api_port == api_port
            assert config.system.max_concurrent_jobs == max_concurrent_jobs
            
            # Verify directories are created
            assert config.data_path.exists()
            assert config.temp_path.exists()
            assert config.log_path.exists()

    @given(
        provider=st.sampled_from(["ollama", "openai", "anthropic", "google"]),
        timeout=st.integers(min_value=10, max_value=300),
        max_tokens=st.integers(min_value=100, max_value=8000),
        temperature=st.floats(min_value=0.0, max_value=2.0),
    )
    def test_llm_config_local_first_property(
        self, provider: str, timeout: int, max_tokens: int, temperature: float
    ):
        """
        **Property 11: Local-first operation**
        For any LLM configuration, the system should default to local providers
        and treat external APIs as optional enhancements.
        **Validates: Requirements 10.2, 10.3**
        """
        config = LLMConfig(
            provider=provider,
            timeout_seconds=timeout,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        
        # Verify configuration is valid
        assert config.provider == provider
        assert config.timeout_seconds == timeout
        assert config.max_tokens == max_tokens
        assert config.temperature == temperature
        
        # Verify local-first defaults
        assert "localhost" in config.ollama_url
        assert config.ollama_model is not None
        
        # Verify external APIs are optional (None by default)
        if provider == "ollama":
            # Local provider should work without API keys
            assert config.openai_api_key is None
            assert config.anthropic_api_key is None
            assert config.google_api_key is None

    @given(
        resolution=st.sampled_from(["1280x720", "1920x1080", "3840x2160"]),
        fps=st.integers(min_value=24, max_value=60),
        quality=st.sampled_from(["draft", "standard", "high"]),
        max_duration=st.integers(min_value=60, max_value=600),
    )
    def test_animation_config_validation_property(
        self, resolution: str, fps: int, quality: str, max_duration: int
    ):
        """
        **Property 11: Local-first operation**
        For any animation configuration, the system should use local animation
        frameworks without requiring external services.
        **Validates: Requirements 10.1**
        """
        config = AnimationConfig(
            resolution=resolution,
            fps=fps,
            quality=quality,
            max_scene_duration=max_duration,
        )
        
        # Verify configuration is valid
        assert config.resolution == resolution
        assert config.fps == fps
        assert config.quality == quality
        assert config.max_scene_duration == max_duration
        
        # Verify local animation frameworks are used
        assert config.template_safety_level in ["safe", "restricted", "unsafe"]
        assert config.manim_quality is not None

    @given(
        tts_provider=st.sampled_from(["coqui", "espeak", "festival"]),
        sample_rate=st.sampled_from([16000, 22050, 44100]),
        voice_speed=st.floats(min_value=0.5, max_value=2.0),
        voice_pitch=st.floats(min_value=0.5, max_value=2.0),
    )
    def test_audio_config_local_providers_property(
        self, tts_provider: str, sample_rate: int, voice_speed: float, voice_pitch: float
    ):
        """
        **Property 11: Local-first operation**
        For any audio configuration, the system should use local TTS providers
        without requiring cloud services.
        **Validates: Requirements 10.1**
        """
        config = AudioConfig(
            tts_provider=tts_provider,
            sample_rate=sample_rate,
            voice_speed=voice_speed,
            voice_pitch=voice_pitch,
        )
        
        # Verify configuration is valid
        assert config.tts_provider == tts_provider
        assert config.sample_rate == sample_rate
        assert config.voice_speed == voice_speed
        assert config.voice_pitch == voice_pitch
        
        # Verify local TTS providers are supported
        local_providers = ["coqui", "espeak", "festival"]
        assert config.tts_provider in local_providers

    @given(
        codec=st.sampled_from(["libx264", "libx265", "av1"]),
        preset=st.sampled_from(["ultrafast", "fast", "medium", "slow"]),
        transition_duration=st.floats(min_value=0.1, max_value=2.0),
        fade_duration=st.floats(min_value=0.05, max_value=1.0),
    )
    def test_video_config_local_processing_property(
        self, codec: str, preset: str, transition_duration: float, fade_duration: float
    ):
        """
        **Property 11: Local-first operation**
        For any video configuration, the system should use local video processing
        tools without requiring cloud services.
        **Validates: Requirements 10.1**
        """
        config = VideoConfig(
            codec=codec,
            preset=preset,
            transition_duration=transition_duration,
            fade_duration=fade_duration,
        )
        
        # Verify configuration is valid
        assert config.codec == codec
        assert config.preset == preset
        assert config.transition_duration == transition_duration
        assert config.fade_duration == fade_duration
        
        # Verify local video processing (FFmpeg codecs)
        local_codecs = ["libx264", "libx265", "av1"]
        assert config.codec in local_codecs

    @given(
        has_credentials=st.booleans(),
        category=st.sampled_from(["Education", "Science & Technology", "Entertainment"]),
        privacy=st.sampled_from(["public", "unlisted", "private"]),
        chunk_size=st.integers(min_value=1024, max_value=10*1024*1024),
    )
    def test_youtube_config_optional_property(
        self, has_credentials: bool, category: str, privacy: str, chunk_size: int
    ):
        """
        **Property 11: Local-first operation**
        For any YouTube configuration, the integration should be optional
        and not break core functionality when disabled.
        **Validates: Requirements 10.3**
        """
        if has_credentials:
            config = YouTubeConfig(
                client_id="test_client_id",
                client_secret="test_client_secret", 
                refresh_token="test_refresh_token",
                default_category=category,
                default_privacy=privacy,
                chunk_size=chunk_size,
            )
            assert config.is_configured is True
        else:
            config = YouTubeConfig(
                default_category=category,
                default_privacy=privacy,
                chunk_size=chunk_size,
            )
            assert config.is_configured is False
        
        # Verify configuration is valid regardless of credentials
        assert config.default_category == category
        assert config.default_privacy == privacy
        assert config.chunk_size == chunk_size
        
        # Verify YouTube is optional (can be None)
        if not has_credentials:
            assert config.client_id is None
            assert config.client_secret is None
            assert config.refresh_token is None

    @given(
        env_vars=st.dictionaries(
            keys=st.sampled_from([
                "RASO_ENV",
                "RASO_LLM_PROVIDER", 
                "RASO_OLLAMA_URL",
                "RASO_OPENAI_API_KEY",
                "RASO_ANIMATION_RESOLUTION",
                "RASO_AUDIO_TTS_PROVIDER",
            ]),
            values=st.text(min_size=1, max_size=100),
            min_size=0,
            max_size=5,
        )
    )
    def test_environment_variable_override_property(self, env_vars: Dict[str, str]):
        """
        **Property 11: Local-first operation**
        For any set of environment variables, the configuration should
        maintain local-first defaults while allowing optional overrides.
        **Validates: Requirements 10.1, 10.3**
        """
        # Set environment variables
        original_env = {}
        for key, value in env_vars.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        try:
            with tempfile.TemporaryDirectory() as tmp_dir:
                temp_path = Path(tmp_dir)
                
                config = RASOMasterConfig(
                    data_path=temp_path / "data",
                    temp_path=temp_path / "temp",
                    log_path=temp_path / "logs",
                )
                
                # Verify local-first operation is maintained
                assert config.llm.provider in ["ollama", "openai", "anthropic", "google"]
                
                # If no LLM provider override, should default to local
                if "RASO_LLM_PROVIDER" not in env_vars:
                    assert config.llm.provider == "ollama"
                
                # Verify directories are created regardless of env vars
                assert config.data_path.exists()
                assert config.temp_path.exists()
                assert config.log_path.exists()
                
        finally:
            # Restore original environment
            for key, original_value in original_env.items():
                if original_value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = original_value

    def test_config_graceful_degradation_property(self):
        """
        **Property 11: Local-first operation**
        The configuration should gracefully handle missing optional services
        and maintain core functionality with local-only capabilities.
        **Validates: Requirements 10.3, 10.4**
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_path = Path(tmp_dir)
            
            # Test with minimal configuration (no external services)
            config = RASOMasterConfig(
                data_path=temp_path / "data",
                temp_path=temp_path / "temp",
                log_path=temp_path / "logs",
                llm=LLMConfig(provider="ollama"),  # Local only
                youtube=YouTubeConfig(),  # No credentials
            )
            
            # Verify core functionality is available
            assert config.llm.provider == "ollama"
            assert not config.youtube.is_configured
            
            # Verify local services are configured
            assert "localhost" in config.llm.ollama_url
            assert config.animation.resolution is not None
            assert config.audio.tts_provider is not None
            assert config.video.codec is not None
            
            # Verify directories exist for local operation
            assert config.data_path.exists()
            assert config.temp_path.exists()
            assert config.log_path.exists()


if __name__ == "__main__":
    pytest.main([__file__])