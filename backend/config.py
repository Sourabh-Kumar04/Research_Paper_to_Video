"""
RASO Platform Configuration Management

Centralized configuration using Pydantic Settings with environment variable support.
Provides type-safe configuration with validation and default values.
"""

import os
from pathlib import Path
from typing import List, Optional

from pydantic import Field, validator
from pydantic_settings import BaseSettings


class LLMConfig(BaseSettings):
    """LLM service configuration."""
    
    provider: str = Field(default="ollama", description="LLM provider")
    
    # Ollama Configuration
    ollama_url: str = Field(default="http://localhost:11434", description="Ollama API URL")
    ollama_model: str = Field(default="deepseek-coder:6.7b", description="Ollama model name")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    openai_model: str = Field(default="gpt-4-turbo-preview", description="OpenAI model name")
    
    # Anthropic Configuration
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API key")
    anthropic_model: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model name")
    
    # Google Configuration
    google_api_key: Optional[str] = Field(default=None, description="Google API key")
    google_model: str = Field(default="gemini-pro", description="Google model name")
    
    # General LLM Settings
    timeout_seconds: int = Field(default=120, description="LLM request timeout")
    max_tokens: int = Field(default=4000, description="Maximum tokens per request")
    temperature: float = Field(default=0.1, description="LLM temperature")
    
    class Config:
        env_prefix = "RASO_"


class AnimationConfig(BaseSettings):
    """Animation generation configuration."""
    
    resolution: str = Field(default="1920x1080", description="Video resolution")
    fps: int = Field(default=30, description="Frames per second")
    quality: str = Field(default="high", description="Animation quality")
    manim_quality: str = Field(default="production_quality", description="Manim quality setting")
    
    # Template Configuration
    template_safety_level: str = Field(default="safe", description="Template safety level")
    max_scene_duration: int = Field(default=300, description="Maximum scene duration in seconds")
    
    class Config:
        env_prefix = "RASO_ANIMATION_"
    
    @validator("resolution")
    def validate_resolution(cls, v):
        """Validate resolution format."""
        if "x" not in v:
            raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        width, height = v.split("x")
        if not (width.isdigit() and height.isdigit()):
            raise ValueError("Resolution dimensions must be numeric")
        return v


class AudioConfig(BaseSettings):
    """Audio processing configuration."""
    
    tts_provider: str = Field(default="coqui", description="TTS provider")
    tts_model: str = Field(default="tts_models/en/ljspeech/tacotron2-DDC", description="TTS model")
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    bitrate: str = Field(default="128k", description="Audio bitrate")
    
    # Voice Configuration
    voice_speed: float = Field(default=1.0, description="Voice speed multiplier")
    voice_pitch: float = Field(default=1.0, description="Voice pitch multiplier")
    
    class Config:
        env_prefix = "RASO_AUDIO_"


class VideoConfig(BaseSettings):
    """Video processing configuration."""
    
    codec: str = Field(default="libx264", description="Video codec")
    bitrate: str = Field(default="5000k", description="Video bitrate")
    preset: str = Field(default="medium", description="Encoding preset")
    
    # Composition Settings
    transition_duration: float = Field(default=0.5, description="Transition duration in seconds")
    fade_duration: float = Field(default=0.2, description="Fade duration in seconds")
    
    class Config:
        env_prefix = "RASO_VIDEO_"


class YouTubeConfig(BaseSettings):
    """YouTube integration configuration."""
    
    client_id: Optional[str] = Field(default=None, description="YouTube API client ID")
    client_secret: Optional[str] = Field(default=None, description="YouTube API client secret")
    refresh_token: Optional[str] = Field(default=None, description="YouTube API refresh token")
    
    default_category: str = Field(default="Education", description="Default video category")
    default_privacy: str = Field(default="unlisted", description="Default video privacy")
    
    # Upload Settings
    chunk_size: int = Field(default=1024*1024, description="Upload chunk size in bytes")
    max_retries: int = Field(default=3, description="Maximum upload retries")
    
    class Config:
        env_prefix = "RASO_YOUTUBE_"
    
    @property
    def is_configured(self) -> bool:
        """Check if YouTube integration is properly configured."""
        return all([self.client_id, self.client_secret, self.refresh_token])


class SystemConfig(BaseSettings):
    """System-level configuration."""
    
    max_concurrent_jobs: int = Field(default=2, description="Maximum concurrent jobs")
    job_timeout_minutes: int = Field(default=60, description="Job timeout in minutes")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay_seconds: int = Field(default=5, description="Delay between retries")
    
    # Storage Configuration
    max_storage_gb: int = Field(default=50, description="Maximum storage in GB")
    cleanup_interval_hours: int = Field(default=24, description="Cleanup interval in hours")
    
    class Config:
        env_prefix = "RASO_"


class RASOMasterConfig(BaseSettings):
    """Master configuration for the RASO platform."""
    
    # Environment
    env: str = Field(default="development", description="Environment name")
    debug: bool = Field(default=False, description="Debug mode")
    log_level: str = Field(default="INFO", description="Logging level")
    
    # API Configuration
    api_host: str = Field(default="0.0.0.0", description="API host")
    api_port: int = Field(default=8000, description="API port")
    api_workers: int = Field(default=1, description="API workers")
    
    # Database
    database_url: str = Field(default="redis://localhost:6379/0", description="Database URL")
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    
    # Paths
    data_path: Path = Field(default=Path("./data"), description="Data directory path")
    temp_path: Path = Field(default=Path("./temp"), description="Temporary files path")
    log_path: Path = Field(default=Path("./logs"), description="Log files path")
    
    # Security
    secret_key: str = Field(default="dev-secret-key", description="Application secret key")
    cors_origins: List[str] = Field(default=["http://localhost:3000"], description="CORS origins")
    rate_limit_per_minute: int = Field(default=60, description="Rate limit per minute")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    metrics_port: int = Field(default=9090, description="Metrics port")
    health_check_interval: int = Field(default=30, description="Health check interval")
    
    # Component Configurations
    llm: LLMConfig = Field(default_factory=LLMConfig)
    animation: AnimationConfig = Field(default_factory=AnimationConfig)
    audio: AudioConfig = Field(default_factory=AudioConfig)
    video: VideoConfig = Field(default_factory=VideoConfig)
    youtube: YouTubeConfig = Field(default_factory=YouTubeConfig)
    system: SystemConfig = Field(default_factory=SystemConfig)
    
    class Config:
        env_prefix = "RASO_"
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Ensure required directories exist."""
        for path in [self.data_path, self.temp_path, self.log_path]:
            path.mkdir(parents=True, exist_ok=True)
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.env.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.env.lower() == "development"


# Global configuration instance
config = RASOMasterConfig()


def get_config() -> RASOMasterConfig:
    """Get the global configuration instance."""
    return config


def reload_config() -> RASOMasterConfig:
    """Reload configuration from environment variables."""
    global config
    config = RASOMasterConfig()
    return config