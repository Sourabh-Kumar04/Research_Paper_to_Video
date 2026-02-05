"""
Music Generation Manager for RASO Platform

This module integrates multiple open-source music generation models
for creating background music, sound effects, and audio enhancement.
"""

import asyncio
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


class MusicGenModel(Enum):
    """Available music generation models."""
    MUSICGEN = "musicgen"           # Meta's MusicGen model
    AUDIOCRAFT = "audiocraft"       # Meta's AudioCraft suite
    RIFFUSION = "riffusion"         # Spectrogram-based music generation
    JUKEBOX = "jukebox"            # OpenAI's Jukebox (if available)
    MAGENTA = "magenta"            # Google's Magenta models
    MUBERT = "mubert"              # Mubert API (free tier)


class MusicGenre(Enum):
    """Music genres for generation."""
    AMBIENT = "ambient"
    CLASSICAL = "classical"
    ELECTRONIC = "electronic"
    JAZZ = "jazz"
    ROCK = "rock"
    POP = "pop"
    CINEMATIC = "cinematic"
    CORPORATE = "corporate"
    UPBEAT = "upbeat"
    RELAXING = "relaxing"
    DRAMATIC = "dramatic"
    MYSTERIOUS = "mysterious"
    EDUCATIONAL = "educational"
    TECH = "tech"
    NATURE = "nature"


class MusicMood(Enum):
    """Music moods for content matching."""
    ENERGETIC = "energetic"
    CALM = "calm"
    INSPIRING = "inspiring"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    FOCUSED = "focused"
    UPLIFTING = "uplifting"
    CONTEMPLATIVE = "contemplative"
    DRAMATIC = "dramatic"
    MYSTERIOUS = "mysterious"
    PLAYFUL = "playful"
    SERIOUS = "serious"


@dataclass
class MusicModelInfo:
    """Information about a music generation model."""
    name: str
    model_type: MusicGenModel
    description: str
    quality_score: float  # 0-1
    generation_speed: float  # 0-1, higher is faster
    memory_usage_mb: int
    max_duration_seconds: int
    supports_conditioning: bool  # Can use text prompts
    supports_melody_conditioning: bool  # Can use melody input
    supports_genres: List[MusicGenre]
    installation_command: Optional[str] = None
    model_size_mb: Optional[int] = None
    gpu_required: bool = False
    free_tier_available: bool = True


@dataclass
class MusicGenerationConfig:
    """Configuration for music generation."""
    model_type: MusicGenModel
    duration_seconds: float
    genre: MusicGenre
    mood: MusicMood
    tempo: int = 120  # BPM
    key: str = "C"    # Musical key
    
    # Generation parameters
    temperature: float = 1.0  # Creativity level
    top_k: int = 250         # Sampling parameter
    top_p: float = 0.0       # Nucleus sampling
    
    # Conditioning
    text_prompt: Optional[str] = None
    melody_conditioning: Optional[Path] = None
    
    # Audio parameters
    sample_rate: int = 32000
    use_gpu: bool = True


@dataclass
class SoundEffect:
    """Sound effect configuration."""
    name: str
    description: str
    duration_seconds: float
    category: str  # transition, emphasis, ambient, etc.
    tags: List[str]
    file_path: Optional[Path] = None


class MusicGenerationManager:
    """Manages music generation and audio enhancement."""
    
    def __init__(self):
        self.available_models = self._initialize_model_catalog()
        self.installed_models = {}
        self.generated_cache = {}
        self.sound_effects_library = self._initialize_sound_effects()
        
    def _initialize_model_catalog(self) -> Dict[MusicGenModel, MusicModelInfo]:
        """Initialize catalog of available music generation models."""
        return {
            MusicGenModel.MUSICGEN: MusicModelInfo(
                name="MusicGen",
                model_type=MusicGenModel.MUSICGEN,
                description="Meta's state-of-the-art music generation model",
                quality_score=0.9,
                generation_speed=0.6,
                memory_usage_mb=2000,
                max_duration_seconds=300,
                supports_conditioning=True,
                supports_melody_conditioning=True,
                supports_genres=[
                    MusicGenre.AMBIENT, MusicGenre.CLASSICAL, MusicGenre.ELECTRONIC,
                    MusicGenre.JAZZ, MusicGenre.ROCK, MusicGenre.POP, MusicGenre.CINEMATIC
                ],
                installation_command="pip install musicgen",
                model_size_mb=1500,
                gpu_required=True,
                free_tier_available=True
            ),
            
            MusicGenModel.AUDIOCRAFT: MusicModelInfo(
                name="AudioCraft",
                model_type=MusicGenModel.AUDIOCRAFT,
                description="Meta's comprehensive audio generation suite",
                quality_score=0.85,
                generation_speed=0.7,
                memory_usage_mb=1800,
                max_duration_seconds=180,
                supports_conditioning=True,
                supports_melody_conditioning=True,
                supports_genres=[
                    MusicGenre.AMBIENT, MusicGenre.ELECTRONIC, MusicGenre.CINEMATIC,
                    MusicGenre.CORPORATE, MusicGenre.TECH
                ],
                installation_command="pip install audiocraft",
                model_size_mb=1200,
                gpu_required=True,
                free_tier_available=True
            ),
            
            MusicGenModel.RIFFUSION: MusicModelInfo(
                name="Riffusion",
                model_type=MusicGenModel.RIFFUSION,
                description="Spectrogram-based music generation with visual feedback",
                quality_score=0.7,
                generation_speed=0.8,
                memory_usage_mb=1000,
                max_duration_seconds=120,
                supports_conditioning=True,
                supports_melody_conditioning=False,
                supports_genres=[
                    MusicGenre.ELECTRONIC, MusicGenre.AMBIENT, MusicGenre.TECH,
                    MusicGenre.UPBEAT, MusicGenre.RELAXING
                ],
                installation_command="pip install riffusion",
                model_size_mb=800,
                gpu_required=False,
                free_tier_available=True
            ),
            
            MusicGenModel.MAGENTA: MusicModelInfo(
                name="Magenta",
                model_type=MusicGenModel.MAGENTA,
                description="Google's machine learning music generation toolkit",
                quality_score=0.75,
                generation_speed=0.9,
                memory_usage_mb=800,
                max_duration_seconds=240,
                supports_conditioning=True,
                supports_melody_conditioning=True,
                supports_genres=[
                    MusicGenre.CLASSICAL, MusicGenre.JAZZ, MusicGenre.AMBIENT,
                    MusicGenre.EDUCATIONAL
                ],
                installation_command="pip install magenta",
                model_size_mb=600,
                gpu_required=False,
                free_tier_available=True
            ),
            
            MusicGenModel.MUBERT: MusicModelInfo(
                name="Mubert API",
                model_type=MusicGenModel.MUBERT,
                description="AI-powered royalty-free music generation API",
                quality_score=0.8,
                generation_speed=0.95,
                memory_usage_mb=100,  # API-based
                max_duration_seconds=600,
                supports_conditioning=True,
                supports_melody_conditioning=False,
                supports_genres=[
                    MusicGenre.AMBIENT, MusicGenre.ELECTRONIC, MusicGenre.CORPORATE,
                    MusicGenre.UPBEAT, MusicGenre.RELAXING, MusicGenre.TECH
                ],
                installation_command="pip install mubert-api",
                model_size_mb=0,  # API-based
                gpu_required=False,
                free_tier_available=True
            )
        }
    
    def _initialize_sound_effects(self) -> Dict[str, SoundEffect]:
        """Initialize library of sound effects."""
        return {
            "transition_whoosh": SoundEffect(
                name="Transition Whoosh",
                description="Smooth transition sound for scene changes",
                duration_seconds=2.0,
                category="transition",
                tags=["smooth", "professional", "clean"]
            ),
            
            "notification_chime": SoundEffect(
                name="Notification Chime",
                description="Gentle notification sound for important points",
                duration_seconds=1.5,
                category="emphasis",
                tags=["gentle", "attention", "positive"]
            ),
            
            "typing_keyboard": SoundEffect(
                name="Keyboard Typing",
                description="Realistic keyboard typing sounds for coding scenes",
                duration_seconds=5.0,
                category="ambient",
                tags=["coding", "realistic", "productivity"]
            ),
            
            "success_fanfare": SoundEffect(
                name="Success Fanfare",
                description="Celebratory sound for achievements or completions",
                duration_seconds=3.0,
                category="emphasis",
                tags=["celebration", "achievement", "positive"]
            ),
            
            "ambient_office": SoundEffect(
                name="Office Ambience",
                description="Subtle office background sounds",
                duration_seconds=60.0,
                category="ambient",
                tags=["office", "professional", "background"]
            ),
            
            "tech_beep": SoundEffect(
                name="Tech Beep",
                description="Futuristic beep for technical content",
                duration_seconds=0.5,
                category="emphasis",
                tags=["tech", "futuristic", "brief"]
            )
        }
    
    async def check_model_availability(self, model_type: MusicGenModel) -> bool:
        """Check if a music generation model is available."""
        try:
            if model_type == MusicGenModel.MUSICGEN:
                try:
                    import musicgen
                    return True
                except ImportError:
                    return False
            
            elif model_type == MusicGenModel.AUDIOCRAFT:
                try:
                    import audiocraft
                    return True
                except ImportError:
                    return False
            
            elif model_type == MusicGenModel.RIFFUSION:
                try:
                    import riffusion
                    return True
                except ImportError:
                    return False
            
            elif model_type == MusicGenModel.MAGENTA:
                try:
                    import magenta
                    return True
                except ImportError:
                    return False
            
            elif model_type == MusicGenModel.MUBERT:
                try:
                    import mubert_api
                    return True
                except ImportError:
                    return False
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking {model_type.value} availability: {e}")
            return False
    
    async def install_model(self, model_type: MusicGenModel) -> bool:
        """Install a music generation model."""
        model_info = self.available_models.get(model_type)
        if not model_info or not model_info.installation_command:
            return False
        
        try:
            logger.info(f"Installing {model_info.name}...")
            
            result = await asyncio.create_subprocess_shell(
                model_info.installation_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                logger.info(f"Successfully installed {model_info.name}")
                return True
            else:
                logger.error(f"Failed to install {model_info.name}: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing {model_info.name}: {e}")
            return False
    
    async def generate_background_music(
        self,
        config: MusicGenerationConfig,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Generate background music based on configuration."""
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".wav"))
        
        # Check if model is available
        if not await self.check_model_availability(config.model_type):
            logger.warning(f"Model {config.model_type.value} not available, trying fallback")
            fallback_model = await self._get_fallback_model()
            if fallback_model:
                config.model_type = fallback_model
            else:
                logger.error("No music generation models available")
                return None
        
        try:
            if config.model_type == MusicGenModel.MUSICGEN:
                return await self._generate_musicgen(config, output_path)
            elif config.model_type == MusicGenModel.AUDIOCRAFT:
                return await self._generate_audiocraft(config, output_path)
            elif config.model_type == MusicGenModel.RIFFUSION:
                return await self._generate_riffusion(config, output_path)
            elif config.model_type == MusicGenModel.MAGENTA:
                return await self._generate_magenta(config, output_path)
            elif config.model_type == MusicGenModel.MUBERT:
                return await self._generate_mubert(config, output_path)
            else:
                logger.error(f"Unsupported model type: {config.model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Music generation failed with {config.model_type.value}: {e}")
            return None
    
    async def _generate_musicgen(self, config: MusicGenerationConfig, output_path: Path) -> Optional[Path]:
        """Generate music using MusicGen."""
        try:
            # This would use the actual MusicGen implementation
            # For now, create a placeholder implementation
            logger.info(f"Generating music with MusicGen: {config.genre.value} for {config.duration_seconds}s")
            
            # Create prompt based on configuration
            prompt = self._create_music_prompt(config)
            
            # Simulate music generation (replace with actual MusicGen code)
            await asyncio.sleep(2)  # Simulate generation time
            
            # Create a simple sine wave as placeholder
            sample_rate = config.sample_rate
            duration = config.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Create a simple chord progression
            frequencies = [261.63, 329.63, 392.00, 523.25]  # C, E, G, C
            audio = np.zeros_like(t)
            
            for i, freq in enumerate(frequencies):
                start_time = i * duration / len(frequencies)
                end_time = (i + 1) * duration / len(frequencies)
                mask = (t >= start_time) & (t < end_time)
                audio[mask] += 0.3 * np.sin(2 * np.pi * freq * t[mask])
            
            # Add some variation based on mood
            if config.mood == MusicMood.ENERGETIC:
                audio *= 1.2
            elif config.mood == MusicMood.CALM:
                audio *= 0.7
            
            # Save audio
            sf.write(str(output_path), audio, sample_rate)
            
            logger.info(f"MusicGen generation complete: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"MusicGen generation failed: {e}")
            return None
    
    async def _generate_audiocraft(self, config: MusicGenerationConfig, output_path: Path) -> Optional[Path]:
        """Generate music using AudioCraft."""
        try:
            logger.info(f"Generating music with AudioCraft: {config.genre.value}")
            
            # Placeholder implementation
            # Would use actual AudioCraft API
            await asyncio.sleep(1.5)
            
            # Create placeholder audio
            sample_rate = config.sample_rate
            duration = config.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Create ambient-style audio
            audio = 0.2 * np.sin(2 * np.pi * 220 * t) * np.exp(-t / (duration * 0.3))
            audio += 0.1 * np.sin(2 * np.pi * 440 * t) * np.exp(-t / (duration * 0.5))
            
            sf.write(str(output_path), audio, sample_rate)
            return output_path
            
        except Exception as e:
            logger.error(f"AudioCraft generation failed: {e}")
            return None
    
    async def _generate_riffusion(self, config: MusicGenerationConfig, output_path: Path) -> Optional[Path]:
        """Generate music using Riffusion."""
        try:
            logger.info(f"Generating music with Riffusion: {config.text_prompt}")
            
            # Placeholder implementation
            await asyncio.sleep(1.0)
            
            # Create electronic-style placeholder
            sample_rate = config.sample_rate
            duration = config.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Electronic beat pattern
            beat_freq = config.tempo / 60.0  # Convert BPM to Hz
            audio = 0.3 * np.sin(2 * np.pi * beat_freq * 4 * t) * (np.sin(2 * np.pi * beat_freq * t) > 0)
            
            sf.write(str(output_path), audio, sample_rate)
            return output_path
            
        except Exception as e:
            logger.error(f"Riffusion generation failed: {e}")
            return None
    
    async def _generate_magenta(self, config: MusicGenerationConfig, output_path: Path) -> Optional[Path]:
        """Generate music using Magenta."""
        try:
            logger.info(f"Generating music with Magenta: {config.genre.value}")
            
            # Placeholder implementation
            await asyncio.sleep(1.2)
            
            # Create classical-style placeholder
            sample_rate = config.sample_rate
            duration = config.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Simple melody
            notes = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]  # C major scale
            audio = np.zeros_like(t)
            
            note_duration = duration / len(notes)
            for i, freq in enumerate(notes):
                start_idx = int(i * note_duration * sample_rate)
                end_idx = int((i + 1) * note_duration * sample_rate)
                if end_idx <= len(audio):
                    note_t = t[start_idx:end_idx] - t[start_idx]
                    audio[start_idx:end_idx] = 0.3 * np.sin(2 * np.pi * freq * note_t) * np.exp(-note_t * 2)
            
            sf.write(str(output_path), audio, sample_rate)
            return output_path
            
        except Exception as e:
            logger.error(f"Magenta generation failed: {e}")
            return None
    
    async def _generate_mubert(self, config: MusicGenerationConfig, output_path: Path) -> Optional[Path]:
        """Generate music using Mubert API."""
        try:
            logger.info(f"Generating music with Mubert API: {config.mood.value}")
            
            # This would use the actual Mubert API
            # For now, create a placeholder
            await asyncio.sleep(0.5)  # API calls are fast
            
            # Create corporate-style placeholder
            sample_rate = config.sample_rate
            duration = config.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            # Corporate background music style
            audio = 0.2 * np.sin(2 * np.pi * 200 * t) + 0.1 * np.sin(2 * np.pi * 400 * t)
            audio *= np.sin(2 * np.pi * 0.5 * t) * 0.5 + 0.5  # Slow amplitude modulation
            
            sf.write(str(output_path), audio, sample_rate)
            return output_path
            
        except Exception as e:
            logger.error(f"Mubert generation failed: {e}")
            return None
    
    def _create_music_prompt(self, config: MusicGenerationConfig) -> str:
        """Create a text prompt for music generation."""
        prompt_parts = []
        
        # Add genre
        prompt_parts.append(f"{config.genre.value} music")
        
        # Add mood
        prompt_parts.append(f"{config.mood.value} mood")
        
        # Add tempo description
        if config.tempo < 80:
            prompt_parts.append("slow tempo")
        elif config.tempo > 140:
            prompt_parts.append("fast tempo")
        else:
            prompt_parts.append("moderate tempo")
        
        # Add custom prompt if provided
        if config.text_prompt:
            prompt_parts.append(config.text_prompt)
        
        return ", ".join(prompt_parts)
    
    async def _get_fallback_model(self) -> Optional[MusicGenModel]:
        """Get the best available fallback music generation model."""
        fallback_order = [
            MusicGenModel.MUBERT,      # API-based, usually available
            MusicGenModel.RIFFUSION,   # Lightweight
            MusicGenModel.MAGENTA,     # Open source, stable
            MusicGenModel.AUDIOCRAFT,  # Good quality
            MusicGenModel.MUSICGEN     # Highest quality but resource intensive
        ]
        
        for model_type in fallback_order:
            if await self.check_model_availability(model_type):
                return model_type
        
        return None
    
    async def generate_sound_effect(
        self,
        effect_name: str,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Generate or retrieve a sound effect."""
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".wav"))
        
        effect = self.sound_effects_library.get(effect_name)
        if not effect:
            logger.error(f"Sound effect '{effect_name}' not found")
            return None
        
        try:
            # Check if we have a pre-generated file
            if effect.file_path and effect.file_path.exists():
                # Copy existing file
                import shutil
                shutil.copy2(effect.file_path, output_path)
                return output_path
            
            # Generate the sound effect
            return await self._generate_sound_effect(effect, output_path)
            
        except Exception as e:
            logger.error(f"Sound effect generation failed: {e}")
            return None
    
    async def _generate_sound_effect(self, effect: SoundEffect, output_path: Path) -> Optional[Path]:
        """Generate a specific sound effect."""
        try:
            sample_rate = 44100
            duration = effect.duration_seconds
            t = np.linspace(0, duration, int(sample_rate * duration))
            
            if effect.name == "Transition Whoosh":
                # Create whoosh sound
                freq = 200 * np.exp(-t * 2)  # Descending frequency
                audio = 0.5 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 3)
                
            elif effect.name == "Notification Chime":
                # Create chime sound
                frequencies = [523.25, 659.25, 783.99]  # C, E, G
                audio = np.zeros_like(t)
                for i, freq in enumerate(frequencies):
                    delay = i * 0.2
                    delayed_t = t - delay
                    mask = delayed_t >= 0
                    audio[mask] += 0.3 * np.sin(2 * np.pi * freq * delayed_t[mask]) * np.exp(-delayed_t[mask] * 4)
                
            elif effect.name == "Keyboard Typing":
                # Create typing sound
                audio = np.zeros_like(t)
                typing_rate = 8  # keystrokes per second
                for i in range(int(duration * typing_rate)):
                    keystroke_time = i / typing_rate
                    if keystroke_time < duration:
                        start_idx = int(keystroke_time * sample_rate)
                        end_idx = min(start_idx + int(0.1 * sample_rate), len(audio))
                        keystroke_t = np.linspace(0, 0.1, end_idx - start_idx)
                        # Random frequency for each keystroke
                        freq = np.random.uniform(800, 1200)
                        audio[start_idx:end_idx] += 0.1 * np.sin(2 * np.pi * freq * keystroke_t) * np.exp(-keystroke_t * 20)
                
            elif effect.name == "Success Fanfare":
                # Create fanfare sound
                notes = [261.63, 329.63, 392.00, 523.25, 659.25]  # C, E, G, C, E
                audio = np.zeros_like(t)
                note_duration = duration / len(notes)
                for i, freq in enumerate(notes):
                    start_time = i * note_duration
                    end_time = (i + 1) * note_duration
                    mask = (t >= start_time) & (t < end_time)
                    note_t = t[mask] - start_time
                    audio[mask] += 0.4 * np.sin(2 * np.pi * freq * note_t) * (1 - note_t / note_duration)
                
            elif effect.name == "Tech Beep":
                # Create tech beep
                freq = 1000
                audio = 0.3 * np.sin(2 * np.pi * freq * t) * np.exp(-t * 10)
                
            else:
                # Default simple tone
                audio = 0.2 * np.sin(2 * np.pi * 440 * t) * np.exp(-t * 2)
            
            # Normalize audio
            audio = audio / np.max(np.abs(audio)) * 0.8
            
            # Save audio
            sf.write(str(output_path), audio, sample_rate)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Sound effect generation failed: {e}")
            return None
    
    def get_recommended_music_config(
        self,
        content_type: str,
        video_duration: float,
        target_audience: str = "general"
    ) -> MusicGenerationConfig:
        """Get recommended music configuration based on content."""
        # Default configuration
        config = MusicGenerationConfig(
            model_type=MusicGenModel.MUBERT,  # Fast and reliable
            duration_seconds=min(video_duration, 300),  # Cap at 5 minutes
            genre=MusicGenre.AMBIENT,
            mood=MusicMood.PROFESSIONAL,
            tempo=100
        )
        
        # Adjust based on content type
        if content_type in ["coding", "programming", "technical"]:
            config.genre = MusicGenre.TECH
            config.mood = MusicMood.FOCUSED
            config.tempo = 110
            
        elif content_type in ["educational", "tutorial", "learning"]:
            config.genre = MusicGenre.EDUCATIONAL
            config.mood = MusicMood.CALM
            config.tempo = 90
            
        elif content_type in ["presentation", "business", "corporate"]:
            config.genre = MusicGenre.CORPORATE
            config.mood = MusicMood.PROFESSIONAL
            config.tempo = 95
            
        elif content_type in ["creative", "artistic", "design"]:
            config.genre = MusicGenre.AMBIENT
            config.mood = MusicMood.CREATIVE
            config.tempo = 105
            
        elif content_type in ["science", "research", "academic"]:
            config.genre = MusicGenre.CLASSICAL
            config.mood = MusicMood.CONTEMPLATIVE
            config.tempo = 85
        
        # Adjust based on target audience
        if target_audience in ["children", "kids"]:
            config.mood = MusicMood.PLAYFUL
            config.tempo = 120
        elif target_audience in ["professional", "enterprise"]:
            config.mood = MusicMood.PROFESSIONAL
            config.tempo = 90
        
        return config
    
    def list_available_sound_effects(self) -> List[Dict[str, Any]]:
        """Get list of available sound effects."""
        effects = []
        for name, effect in self.sound_effects_library.items():
            effects.append({
                "name": name,
                "display_name": effect.name,
                "description": effect.description,
                "duration": effect.duration_seconds,
                "category": effect.category,
                "tags": effect.tags
            })
        
        return effects
    
    def get_model_info(self, model_type: MusicGenModel) -> Optional[MusicModelInfo]:
        """Get information about a music generation model."""
        return self.available_models.get(model_type)
    
    def get_all_models_info(self) -> List[Dict[str, Any]]:
        """Get information about all available music generation models."""
        models_info = []
        
        for model_type, model_info in self.available_models.items():
            models_info.append({
                "type": model_type.value,
                "name": model_info.name,
                "description": model_info.description,
                "quality_score": model_info.quality_score,
                "generation_speed": model_info.generation_speed,
                "memory_usage_mb": model_info.memory_usage_mb,
                "max_duration_seconds": model_info.max_duration_seconds,
                "supports_conditioning": model_info.supports_conditioning,
                "supports_melody_conditioning": model_info.supports_melody_conditioning,
                "supported_genres": [g.value for g in model_info.supports_genres],
                "installation_command": model_info.installation_command,
                "model_size_mb": model_info.model_size_mb,
                "gpu_required": model_info.gpu_required,
                "free_tier_available": model_info.free_tier_available
            })
        
        # Sort by quality score
        models_info.sort(key=lambda x: x["quality_score"], reverse=True)
        return models_info


# Global instance for easy access
music_generation_manager = MusicGenerationManager()