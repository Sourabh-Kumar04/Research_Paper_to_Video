"""
Audio models for the RASO platform.

Models for audio assets, TTS generation, and audio synchronization
for the video production pipeline.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime

from pydantic import BaseModel, Field, validator


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    AAC = "aac"


class VoiceGender(str, Enum):
    """Voice gender options."""
    MALE = "male"
    FEMALE = "female"
    NEUTRAL = "neutral"


class VoiceOption(BaseModel):
    """Available voice option for TTS."""
    
    id: str = Field(..., description="Unique voice identifier")
    name: str = Field(..., description="Human-readable voice name")
    language: str = Field(..., description="Language code (e.g., 'en', 'es')")
    gender: VoiceGender = Field(..., description="Voice gender")
    
    # Voice characteristics
    sample_rate: int = Field(default=22050, description="Default sample rate")
    quality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Voice quality score")
    naturalness_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Voice naturalness score")
    
    # Technical details
    model_name: Optional[str] = Field(default=None, description="TTS model name")
    provider: str = Field(default="coqui", description="TTS provider")
    
    @validator("language")
    def validate_language(cls, v):
        """Validate language code."""
        if len(v) < 2:
            raise ValueError("Language code must be at least 2 characters")
        return v.lower()
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "id": "en_female_1",
                    "name": "Sarah (English)",
                    "language": "en",
                    "gender": "female",
                    "quality_score": 0.85,
                    "naturalness_score": 0.80,
                    "provider": "coqui"
                }
            ]
        }


class AudioProcessingSettings(BaseModel):
    """Settings for audio processing."""
    
    # Basic settings
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    bit_depth: int = Field(default=16, description="Audio bit depth")
    channels: int = Field(default=1, description="Number of audio channels")
    
    # Processing settings
    normalize_volume: bool = Field(default=True, description="Whether to normalize volume")
    target_volume_db: float = Field(default=-20.0, description="Target volume in dB")
    noise_reduction: bool = Field(default=True, description="Whether to apply noise reduction")
    
    # Speed and pitch
    speed_multiplier: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed multiplier")
    pitch_shift: float = Field(default=0.0, ge=-12.0, le=12.0, description="Pitch shift in semitones")
    
    @validator("sample_rate")
    def validate_sample_rate(cls, v):
        """Validate sample rate."""
        valid_rates = [8000, 16000, 22050, 44100, 48000]
        if v not in valid_rates:
            raise ValueError(f"Sample rate must be one of {valid_rates}")
        return v
    
    @validator("bit_depth")
    def validate_bit_depth(cls, v):
        """Validate bit depth."""
        valid_depths = [8, 16, 24, 32]
        if v not in valid_depths:
            raise ValueError(f"Bit depth must be one of {valid_depths}")
        return v


class AudioScene(BaseModel):
    """Audio for a single scene."""
    
    scene_id: str = Field(..., description="Reference to scene ID")
    file_path: str = Field(..., description="Path to audio file")
    duration: float = Field(..., gt=0.0, description="Audio duration in seconds")
    transcript: str = Field(..., description="Text transcript of the audio")
    
    # Audio specifications
    format: AudioFormat = Field(default=AudioFormat.WAV, description="Audio file format")
    sample_rate: int = Field(default=22050, description="Audio sample rate")
    bit_depth: int = Field(default=16, description="Audio bit depth")
    
    # Generation metadata
    voice_id: Optional[str] = Field(default=None, description="Voice ID used for generation")
    processing_settings: AudioProcessingSettings = Field(default_factory=AudioProcessingSettings, description="Processing settings used")
    
    # Timing information
    timing_markers: List[Dict[str, Any]] = Field(default_factory=list, description="Word-level timing markers")
    
    # Quality metrics
    generation_time: Optional[float] = Field(default=None, description="Time taken to generate audio")
    quality_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Audio quality score")
    
    @validator("file_path")
    def validate_file_path(cls, v):
        """Validate audio file path."""
        if not v:
            raise ValueError("File path cannot be empty")
        
        valid_extensions = [".wav", ".mp3", ".flac", ".aac"]
        path = Path(v)
        if path.suffix.lower() not in valid_extensions:
            raise ValueError(f"File must have a valid audio extension: {valid_extensions}")
        
        return v
    
    @validator("transcript")
    def validate_transcript(cls, v):
        """Validate transcript."""
        if len(v.strip()) < 5:
            raise ValueError("Transcript must be at least 5 characters")
        return v.strip()
    
    @property
    def file_exists(self) -> bool:
        """Check if the audio file exists."""
        return Path(self.file_path).exists()
    
    @property
    def estimated_words(self) -> int:
        """Estimate number of words in transcript."""
        return len(self.transcript.split())
    
    @property
    def words_per_minute(self) -> float:
        """Calculate words per minute."""
        if self.duration > 0:
            return (self.estimated_words / self.duration) * 60
        return 0.0
    
    def get_file_size(self) -> Optional[int]:
        """Get audio file size in bytes."""
        if self.file_exists:
            return Path(self.file_path).stat().st_size
        return None
    
    def add_timing_marker(self, word: str, start_time: float, end_time: float) -> None:
        """Add a word-level timing marker."""
        marker = {
            "word": word,
            "start_time": start_time,
            "end_time": end_time,
            "duration": end_time - start_time
        }
        self.timing_markers.append(marker)
    
    def get_timing_at_position(self, position: float) -> Optional[Dict[str, Any]]:
        """Get timing marker at specific position."""
        for marker in self.timing_markers:
            if marker["start_time"] <= position <= marker["end_time"]:
                return marker
        return None


class AudioAssets(BaseModel):
    """Collection of audio assets for video production."""
    
    scenes: List[AudioScene] = Field(..., description="Audio scenes in order")
    total_duration: float = Field(..., gt=0.0, description="Total audio duration")
    sample_rate: int = Field(default=22050, description="Common sample rate for all scenes")
    
    # Global audio settings
    master_volume: float = Field(default=1.0, ge=0.0, le=2.0, description="Master volume multiplier")
    background_music_path: Optional[str] = Field(default=None, description="Path to background music file")
    background_music_volume: float = Field(default=0.1, ge=0.0, le=1.0, description="Background music volume")
    
    # Asset metadata
    creation_time: datetime = Field(default_factory=datetime.now, description="Asset creation timestamp")
    voice_consistency_score: Optional[float] = Field(default=None, ge=0.0, le=1.0, description="Voice consistency across scenes")
    
    @validator("scenes")
    def validate_scenes(cls, v):
        """Validate audio scenes."""
        if not v:
            raise ValueError("At least one audio scene is required")
        
        # Check for duplicate scene IDs
        scene_ids = [scene.scene_id for scene in v]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique")
        
        return v
    
    @validator("total_duration")
    def validate_total_duration(cls, v, values):
        """Validate total duration matches scene durations."""
        scenes = values.get("scenes", [])
        if scenes:
            calculated_duration = sum(scene.duration for scene in scenes)
            if abs(v - calculated_duration) > 1.0:  # Allow 1 second tolerance
                raise ValueError("Total duration must match sum of scene durations")
        return v
    
    def get_scene_by_id(self, scene_id: str) -> Optional[AudioScene]:
        """Get an audio scene by ID."""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None
    
    def get_total_word_count(self) -> int:
        """Get total word count across all scenes."""
        return sum(scene.estimated_words for scene in self.scenes)
    
    def get_average_words_per_minute(self) -> float:
        """Get average words per minute across all scenes."""
        if self.total_duration > 0:
            return (self.get_total_word_count() / self.total_duration) * 60
        return 0.0
    
    def get_total_file_size(self) -> int:
        """Get total file size of all audio scenes."""
        total_size = 0
        for scene in self.scenes:
            size = scene.get_file_size()
            if size:
                total_size += size
        return total_size
    
    def get_voice_distribution(self) -> Dict[str, int]:
        """Get distribution of voices used."""
        distribution = {}
        for scene in self.scenes:
            voice_id = scene.voice_id or "unknown"
            distribution[voice_id] = distribution.get(voice_id, 0) + 1
        return distribution
    
    def check_sample_rate_consistency(self) -> bool:
        """Check if all scenes have consistent sample rates."""
        return all(scene.sample_rate == self.sample_rate for scene in self.scenes)
    
    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get statistics about audio generation."""
        generation_times = [scene.generation_time for scene in self.scenes 
                          if scene.generation_time is not None]
        quality_scores = [scene.quality_score for scene in self.scenes 
                         if scene.quality_score is not None]
        
        stats = {
            "total_scenes": len(self.scenes),
            "total_duration": self.total_duration,
            "total_words": self.get_total_word_count(),
            "average_wpm": self.get_average_words_per_minute(),
            "total_file_size_mb": self.get_total_file_size() / (1024 * 1024),
        }
        
        if generation_times:
            stats.update({
                "average_generation_time": sum(generation_times) / len(generation_times),
                "total_generation_time": sum(generation_times),
            })
        
        if quality_scores:
            stats.update({
                "average_quality_score": sum(quality_scores) / len(quality_scores),
                "min_quality_score": min(quality_scores),
                "max_quality_score": max(quality_scores),
            })
        
        return stats
    
    class Config:
        schema_extra = {
            "example": {
                "scenes": [
                    {
                        "scene_id": "scene1",
                        "file_path": "/data/audio/scene1.wav",
                        "duration": 30.0,
                        "transcript": "Welcome to our exploration of the Transformer architecture...",
                        "voice_id": "en_female_1",
                        "sample_rate": 22050
                    }
                ],
                "total_duration": 75.0,
                "sample_rate": 22050,
                "master_volume": 1.0
            }
        }