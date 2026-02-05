"""
TTS Model Manager for RASO Platform

This module manages multiple open-source TTS (Text-to-Speech) models,
providing high-quality voice synthesis with various options for speed and quality.
"""

import asyncio
import subprocess
import tempfile
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import numpy as np
import soundfile as sf

logger = logging.getLogger(__name__)


class TTSModelType(Enum):
    """Types of TTS models available."""
    COQUI = "coqui"          # High-quality neural TTS (DEFAULT for quality)
    BARK = "bark"            # Generative audio with emotions and effects
    TORTOISE = "tortoise"    # Ultra-high quality but slower generation
    XTTS = "xtts"           # Multilingual voice cloning capabilities
    PIPER = "piper"         # Fast, lightweight TTS (DEFAULT for speed)
    ESPEAK = "espeak"       # Fallback lightweight TTS


class VoiceStyle(Enum):
    """Voice styles and emotions."""
    NEUTRAL = "neutral"
    EXCITED = "excited"
    CALM = "calm"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"
    CONVERSATIONAL = "conversational"


@dataclass
class TTSModelInfo:
    """Information about a TTS model."""
    name: str
    model_type: TTSModelType
    description: str
    quality_score: float  # 0-1, higher is better
    speed_score: float    # 0-1, higher is faster
    memory_usage_mb: int
    supports_voice_cloning: bool
    supports_emotions: bool
    supports_multilingual: bool
    available_languages: List[str]
    installation_command: Optional[str] = None
    model_size_mb: Optional[int] = None
    gpu_acceleration: bool = False


@dataclass
class VoiceConfig:
    """Configuration for voice synthesis."""
    model_type: TTSModelType
    voice_id: str
    language: str = "en"
    style: VoiceStyle = VoiceStyle.NEUTRAL
    speed: float = 1.0        # 0.5-2.0
    pitch: float = 1.0        # 0.5-2.0
    volume: float = 1.0       # 0.0-1.0
    sample_rate: int = 22050
    use_gpu: bool = True


class TTSModelManager:
    """Manages multiple TTS models and provides unified interface."""
    
    def __init__(self):
        self.available_models = self._initialize_model_catalog()
        self.installed_models = {}
        self.default_quality_model = TTSModelType.COQUI
        self.default_speed_model = TTSModelType.PIPER
        self.voice_cache = {}
        
    def _initialize_model_catalog(self) -> Dict[TTSModelType, TTSModelInfo]:
        """Initialize catalog of available TTS models."""
        return {
            TTSModelType.COQUI: TTSModelInfo(
                name="Coqui TTS",
                model_type=TTSModelType.COQUI,
                description="High-quality neural TTS with natural voices",
                quality_score=0.9,
                speed_score=0.6,
                memory_usage_mb=1500,
                supports_voice_cloning=True,
                supports_emotions=True,
                supports_multilingual=True,
                available_languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
                installation_command="pip install TTS",
                model_size_mb=500,
                gpu_acceleration=True
            ),
            
            TTSModelType.BARK: TTSModelInfo(
                name="Bark",
                model_type=TTSModelType.BARK,
                description="Generative audio model with emotions, music, and sound effects",
                quality_score=0.85,
                speed_score=0.3,
                memory_usage_mb=2000,
                supports_voice_cloning=True,
                supports_emotions=True,
                supports_multilingual=True,
                available_languages=["en", "zh", "fr", "de", "hi", "it", "ja", "ko", "pl", "pt", "ru", "es", "tr"],
                installation_command="pip install bark-voice-cloning",
                model_size_mb=1200,
                gpu_acceleration=True
            ),
            
            TTSModelType.TORTOISE: TTSModelInfo(
                name="Tortoise TTS",
                model_type=TTSModelType.TORTOISE,
                description="Ultra-high quality TTS with excellent voice cloning",
                quality_score=0.95,
                speed_score=0.2,
                memory_usage_mb=3000,
                supports_voice_cloning=True,
                supports_emotions=False,
                supports_multilingual=False,
                available_languages=["en"],
                installation_command="pip install tortoise-tts",
                model_size_mb=2000,
                gpu_acceleration=True
            ),
            
            TTSModelType.XTTS: TTSModelInfo(
                name="XTTS-v2",
                model_type=TTSModelType.XTTS,
                description="Multilingual voice cloning with real-time capabilities",
                quality_score=0.88,
                speed_score=0.7,
                memory_usage_mb=1200,
                supports_voice_cloning=True,
                supports_emotions=True,
                supports_multilingual=True,
                available_languages=["en", "es", "fr", "de", "it", "pt", "pl", "tr", "ru", "nl", "cs", "ar", "zh", "ja", "hu", "ko"],
                installation_command="pip install xtts-v2",
                model_size_mb=800,
                gpu_acceleration=True
            ),
            
            TTSModelType.PIPER: TTSModelInfo(
                name="Piper TTS",
                model_type=TTSModelType.PIPER,
                description="Fast, lightweight TTS optimized for speed",
                quality_score=0.7,
                speed_score=0.95,
                memory_usage_mb=200,
                supports_voice_cloning=False,
                supports_emotions=False,
                supports_multilingual=True,
                available_languages=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja", "ko"],
                installation_command="pip install piper-tts",
                model_size_mb=50,
                gpu_acceleration=False
            ),
            
            TTSModelType.ESPEAK: TTSModelInfo(
                name="eSpeak NG",
                model_type=TTSModelType.ESPEAK,
                description="Lightweight fallback TTS (always available)",
                quality_score=0.4,
                speed_score=1.0,
                memory_usage_mb=50,
                supports_voice_cloning=False,
                supports_emotions=False,
                supports_multilingual=True,
                available_languages=["en", "es", "fr", "de", "it", "pt", "nl", "ru", "zh", "ja", "ko", "ar", "hi"],
                installation_command="Available by default",
                model_size_mb=10,
                gpu_acceleration=False
            )
        }
    
    async def check_model_availability(self, model_type: TTSModelType) -> bool:
        """Check if a TTS model is available/installed."""
        try:
            if model_type == TTSModelType.COQUI:
                try:
                    import TTS
                    return True
                except ImportError:
                    return False
            
            elif model_type == TTSModelType.BARK:
                try:
                    import bark
                    return True
                except ImportError:
                    return False
            
            elif model_type == TTSModelType.TORTOISE:
                try:
                    import tortoise
                    return True
                except ImportError:
                    return False
            
            elif model_type == TTSModelType.XTTS:
                try:
                    import xtts
                    return True
                except ImportError:
                    return False
            
            elif model_type == TTSModelType.PIPER:
                # Check if piper command is available
                result = await asyncio.create_subprocess_exec(
                    "piper", "--help",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                return result.returncode == 0
            
            elif model_type == TTSModelType.ESPEAK:
                # Check if espeak command is available
                result = await asyncio.create_subprocess_exec(
                    "espeak", "--help",
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await result.communicate()
                return result.returncode == 0
            
            return False
            
        except Exception as e:
            logger.warning(f"Error checking {model_type.value} availability: {e}")
            return False
    
    async def install_model(self, model_type: TTSModelType) -> bool:
        """Install a TTS model."""
        model_info = self.available_models.get(model_type)
        if not model_info or not model_info.installation_command:
            return False
        
        if model_info.installation_command == "Available by default":
            return True
        
        try:
            logger.info(f"Installing {model_info.name}...")
            
            # Run installation command
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
    
    async def get_available_voices(self, model_type: TTSModelType) -> List[str]:
        """Get list of available voices for a model."""
        try:
            if model_type == TTSModelType.COQUI:
                try:
                    from TTS.api import TTS
                    # Get available models
                    models = TTS.list_models()
                    # Filter for TTS models
                    tts_models = [m for m in models if "tts" in m.lower()]
                    return tts_models[:10]  # Limit to first 10
                except Exception:
                    return ["tts_models/en/ljspeech/tacotron2-DDC", "tts_models/en/vctk/vits"]
            
            elif model_type == TTSModelType.BARK:
                return ["v2/en_speaker_0", "v2/en_speaker_1", "v2/en_speaker_2", "v2/en_speaker_3", 
                       "v2/en_speaker_4", "v2/en_speaker_5", "v2/en_speaker_6", "v2/en_speaker_7"]
            
            elif model_type == TTSModelType.TORTOISE:
                return ["angie", "daniel", "deniro", "emma", "freeman", "geralt", "halle", "jlaw", 
                       "lj", "mol", "pat", "pat2", "rainbow", "snakes", "tom", "train_daws", "weaver", "william"]
            
            elif model_type == TTSModelType.XTTS:
                return ["main", "female_1", "female_2", "male_1", "male_2"]
            
            elif model_type == TTSModelType.PIPER:
                return ["en_US-lessac-medium", "en_US-libritts-high", "en_US-ryan-high", 
                       "en_GB-alan-medium", "en_GB-southern_english_female-low"]
            
            elif model_type == TTSModelType.ESPEAK:
                return ["default", "male1", "male2", "male3", "female1", "female2", "female3"]
            
            return ["default"]
            
        except Exception as e:
            logger.warning(f"Error getting voices for {model_type.value}: {e}")
            return ["default"]
    
    async def synthesize_speech(
        self,
        text: str,
        voice_config: VoiceConfig,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Synthesize speech using specified model and configuration."""
        if not text.strip():
            logger.warning("Empty text provided for synthesis")
            return None
        
        # Check if model is available
        if not await self.check_model_availability(voice_config.model_type):
            logger.warning(f"Model {voice_config.model_type.value} not available, trying fallback")
            # Try fallback to available model
            fallback_model = await self._get_fallback_model()
            if fallback_model:
                voice_config.model_type = fallback_model
            else:
                logger.error("No TTS models available")
                return None
        
        # Create output path if not provided
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".wav"))
        
        try:
            if voice_config.model_type == TTSModelType.COQUI:
                return await self._synthesize_coqui(text, voice_config, output_path)
            elif voice_config.model_type == TTSModelType.BARK:
                return await self._synthesize_bark(text, voice_config, output_path)
            elif voice_config.model_type == TTSModelType.TORTOISE:
                return await self._synthesize_tortoise(text, voice_config, output_path)
            elif voice_config.model_type == TTSModelType.XTTS:
                return await self._synthesize_xtts(text, voice_config, output_path)
            elif voice_config.model_type == TTSModelType.PIPER:
                return await self._synthesize_piper(text, voice_config, output_path)
            elif voice_config.model_type == TTSModelType.ESPEAK:
                return await self._synthesize_espeak(text, voice_config, output_path)
            else:
                logger.error(f"Unsupported model type: {voice_config.model_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error synthesizing speech with {voice_config.model_type.value}: {e}")
            return None
    
    async def _synthesize_coqui(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using Coqui TTS."""
        try:
            from TTS.api import TTS
            
            # Initialize TTS model
            model_name = config.voice_id if config.voice_id != "default" else "tts_models/en/ljspeech/tacotron2-DDC"
            tts = TTS(model_name=model_name, gpu=config.use_gpu)
            
            # Generate speech
            tts.tts_to_file(
                text=text,
                file_path=str(output_path),
                speaker_wav=None,  # Could be used for voice cloning
                language=config.language
            )
            
            # Apply post-processing (speed, pitch adjustments)
            if config.speed != 1.0 or config.pitch != 1.0:
                await self._apply_audio_effects(output_path, config)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Coqui TTS synthesis failed: {e}")
            return None
    
    async def _synthesize_bark(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using Bark."""
        try:
            from bark import SAMPLE_RATE, generate_audio, preload_models
            from scipy.io.wavfile import write as write_wav
            
            # Preload models
            preload_models()
            
            # Generate audio
            audio_array = generate_audio(text, history_prompt=config.voice_id)
            
            # Save to file
            write_wav(str(output_path), SAMPLE_RATE, audio_array)
            
            # Apply post-processing
            if config.speed != 1.0 or config.pitch != 1.0:
                await self._apply_audio_effects(output_path, config)
            
            return output_path
            
        except Exception as e:
            logger.error(f"Bark synthesis failed: {e}")
            return None
    
    async def _synthesize_tortoise(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using Tortoise TTS."""
        try:
            import tortoise.api as tortoise_api
            
            # Initialize Tortoise
            tts = tortoise_api.TextToSpeech()
            
            # Generate speech
            voice_samples, conditioning_latents = tortoise_api.load_voice(config.voice_id)
            gen = tts.tts_with_preset(
                text, 
                voice_samples=voice_samples, 
                conditioning_latents=conditioning_latents,
                preset="fast"  # Can be "ultra_fast", "fast", "standard", "high_quality"
            )
            
            # Save audio
            tortoise_api.save_gen_with_voicefix(gen, str(output_path))
            
            return output_path
            
        except Exception as e:
            logger.error(f"Tortoise TTS synthesis failed: {e}")
            return None
    
    async def _synthesize_xtts(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using XTTS-v2."""
        try:
            # This would use the XTTS-v2 API when available
            # For now, fallback to a simpler implementation
            logger.warning("XTTS-v2 synthesis not fully implemented, using fallback")
            return await self._synthesize_espeak(text, config, output_path)
            
        except Exception as e:
            logger.error(f"XTTS synthesis failed: {e}")
            return None
    
    async def _synthesize_piper(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using Piper TTS."""
        try:
            # Use Piper command line
            cmd = [
                "piper",
                "--model", config.voice_id,
                "--output_file", str(output_path)
            ]
            
            # Run Piper
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=text.encode())
            
            if process.returncode == 0 and output_path.exists():
                # Apply post-processing
                if config.speed != 1.0 or config.pitch != 1.0:
                    await self._apply_audio_effects(output_path, config)
                return output_path
            else:
                logger.error(f"Piper synthesis failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Piper synthesis failed: {e}")
            return None
    
    async def _synthesize_espeak(self, text: str, config: VoiceConfig, output_path: Path) -> Optional[Path]:
        """Synthesize speech using eSpeak NG (fallback)."""
        try:
            # Build eSpeak command
            cmd = [
                "espeak",
                "-w", str(output_path),
                "-s", str(int(config.speed * 175)),  # Speed in words per minute
                "-p", str(int(config.pitch * 50)),   # Pitch (0-99)
                "-a", str(int(config.volume * 200)), # Amplitude (0-200)
                text
            ]
            
            # Run eSpeak
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and output_path.exists():
                return output_path
            else:
                logger.error(f"eSpeak synthesis failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"eSpeak synthesis failed: {e}")
            return None
    
    async def _apply_audio_effects(self, audio_path: Path, config: VoiceConfig) -> None:
        """Apply audio effects like speed and pitch changes."""
        try:
            # This would use audio processing libraries like librosa or pydub
            # For now, just log the intended effects
            logger.info(f"Applying audio effects: speed={config.speed}, pitch={config.pitch}")
            
            # Could implement with:
            # - librosa for advanced audio processing
            # - pydub for simple effects
            # - ffmpeg for command-line processing
            
        except Exception as e:
            logger.warning(f"Failed to apply audio effects: {e}")
    
    async def _get_fallback_model(self) -> Optional[TTSModelType]:
        """Get the best available fallback TTS model."""
        # Check models in order of preference
        fallback_order = [
            TTSModelType.PIPER,
            TTSModelType.ESPEAK,
            TTSModelType.COQUI,
            TTSModelType.XTTS
        ]
        
        for model_type in fallback_order:
            if await self.check_model_availability(model_type):
                return model_type
        
        return None
    
    def get_recommended_model(
        self, 
        priority: str = "balanced",  # speed, quality, balanced
        supports_cloning: bool = False,
        supports_emotions: bool = False
    ) -> TTSModelType:
        """Get recommended TTS model based on requirements."""
        if priority == "speed":
            if supports_cloning:
                return TTSModelType.XTTS  # Fast + cloning
            else:
                return TTSModelType.PIPER  # Fastest
        
        elif priority == "quality":
            if supports_cloning:
                return TTSModelType.TORTOISE  # Highest quality + cloning
            else:
                return TTSModelType.COQUI  # High quality
        
        else:  # balanced
            if supports_cloning or supports_emotions:
                return TTSModelType.COQUI  # Good balance + features
            else:
                return TTSModelType.PIPER  # Good balance
    
    async def clone_voice(
        self,
        reference_audio_path: Path,
        text: str,
        output_path: Optional[Path] = None,
        model_type: Optional[TTSModelType] = None
    ) -> Optional[Path]:
        """Clone a voice from reference audio and synthesize text."""
        if model_type is None:
            # Use best available cloning model
            for mt in [TTSModelType.TORTOISE, TTSModelType.COQUI, TTSModelType.BARK, TTSModelType.XTTS]:
                if await self.check_model_availability(mt):
                    model_info = self.available_models[mt]
                    if model_info.supports_voice_cloning:
                        model_type = mt
                        break
        
        if model_type is None:
            logger.error("No voice cloning models available")
            return None
        
        if output_path is None:
            output_path = Path(tempfile.mktemp(suffix=".wav"))
        
        try:
            if model_type == TTSModelType.COQUI:
                return await self._clone_voice_coqui(reference_audio_path, text, output_path)
            elif model_type == TTSModelType.TORTOISE:
                return await self._clone_voice_tortoise(reference_audio_path, text, output_path)
            # Add other cloning implementations as needed
            
        except Exception as e:
            logger.error(f"Voice cloning failed with {model_type.value}: {e}")
            return None
    
    async def _clone_voice_coqui(self, reference_path: Path, text: str, output_path: Path) -> Optional[Path]:
        """Clone voice using Coqui TTS."""
        try:
            from TTS.api import TTS
            
            # Use voice cloning model
            tts = TTS(model_name="tts_models/multilingual/multi-dataset/your_tts", gpu=True)
            
            # Clone and synthesize
            tts.tts_to_file(
                text=text,
                speaker_wav=str(reference_path),
                file_path=str(output_path),
                language="en"
            )
            
            return output_path
            
        except Exception as e:
            logger.error(f"Coqui voice cloning failed: {e}")
            return None
    
    async def _clone_voice_tortoise(self, reference_path: Path, text: str, output_path: Path) -> Optional[Path]:
        """Clone voice using Tortoise TTS."""
        try:
            # This would implement Tortoise voice cloning
            # Requires preprocessing the reference audio
            logger.warning("Tortoise voice cloning not fully implemented")
            return None
            
        except Exception as e:
            logger.error(f"Tortoise voice cloning failed: {e}")
            return None
    
    def get_model_info(self, model_type: TTSModelType) -> Optional[TTSModelInfo]:
        """Get information about a TTS model."""
        return self.available_models.get(model_type)
    
    def get_all_models_info(self) -> List[Dict[str, Any]]:
        """Get information about all available TTS models."""
        models_info = []
        
        for model_type, model_info in self.available_models.items():
            models_info.append({
                "type": model_type.value,
                "name": model_info.name,
                "description": model_info.description,
                "quality_score": model_info.quality_score,
                "speed_score": model_info.speed_score,
                "memory_usage_mb": model_info.memory_usage_mb,
                "supports_voice_cloning": model_info.supports_voice_cloning,
                "supports_emotions": model_info.supports_emotions,
                "supports_multilingual": model_info.supports_multilingual,
                "available_languages": model_info.available_languages,
                "installation_command": model_info.installation_command,
                "model_size_mb": model_info.model_size_mb,
                "gpu_acceleration": model_info.gpu_acceleration
            })
        
        # Sort by quality score (descending)
        models_info.sort(key=lambda x: x["quality_score"], reverse=True)
        return models_info
    
    async def benchmark_models(self) -> Dict[str, Any]:
        """Benchmark available TTS models."""
        results = {}
        test_text = "This is a test sentence for benchmarking text-to-speech synthesis quality and performance."
        
        for model_type in self.available_models.keys():
            if await self.check_model_availability(model_type):
                try:
                    import time
                    
                    config = VoiceConfig(
                        model_type=model_type,
                        voice_id="default"
                    )
                    
                    start_time = time.time()
                    output_path = await self.synthesize_speech(test_text, config)
                    end_time = time.time()
                    
                    if output_path and output_path.exists():
                        # Calculate metrics
                        synthesis_time = end_time - start_time
                        audio_duration = len(test_text.split()) * 0.6  # Rough estimate
                        real_time_factor = synthesis_time / audio_duration
                        
                        results[model_type.value] = {
                            "synthesis_time": synthesis_time,
                            "real_time_factor": real_time_factor,
                            "status": "success",
                            "output_size_bytes": output_path.stat().st_size
                        }
                        
                        # Clean up
                        output_path.unlink()
                    else:
                        results[model_type.value] = {
                            "status": "failed",
                            "error": "No output generated"
                        }
                        
                except Exception as e:
                    results[model_type.value] = {
                        "status": "error",
                        "error": str(e)
                    }
        
        return {"status": "completed", "results": results}


# Global instance for easy access
tts_model_manager = TTSModelManager()