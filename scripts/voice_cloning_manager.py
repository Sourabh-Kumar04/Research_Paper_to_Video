"""
Voice Cloning and Customization Manager for RASO Platform

This module provides advanced voice cloning capabilities, emotion control,
and voice customization features using open-source TTS models.
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

from .tts_model_manager import TTSModelManager, TTSModelType, VoiceStyle, VoiceConfig

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """Types of emotions for voice synthesis."""
    NEUTRAL = "neutral"
    HAPPY = "happy"
    SAD = "sad"
    ANGRY = "angry"
    EXCITED = "excited"
    CALM = "calm"
    SURPRISED = "surprised"
    FEARFUL = "fearful"
    DISGUSTED = "disgusted"
    CONFIDENT = "confident"
    UNCERTAIN = "uncertain"
    PROFESSIONAL = "professional"
    FRIENDLY = "friendly"
    AUTHORITATIVE = "authoritative"


class VoiceCharacteristics(Enum):
    """Voice characteristics that can be modified."""
    PITCH = "pitch"
    SPEED = "speed"
    VOLUME = "volume"
    BREATHINESS = "breathiness"
    ROUGHNESS = "roughness"
    WARMTH = "warmth"
    CLARITY = "clarity"
    RESONANCE = "resonance"


@dataclass
class VoiceProfile:
    """Complete voice profile with all characteristics."""
    name: str
    base_model: TTSModelType
    voice_id: str
    language: str
    gender: str  # male, female, neutral
    age_group: str  # child, young_adult, adult, elderly
    accent: str  # american, british, australian, etc.
    
    # Emotional characteristics
    default_emotion: EmotionType
    emotion_range: List[EmotionType]
    
    # Voice characteristics (0.0-2.0, 1.0 is neutral)
    pitch: float = 1.0
    speed: float = 1.0
    volume: float = 1.0
    breathiness: float = 1.0
    roughness: float = 1.0
    warmth: float = 1.0
    clarity: float = 1.0
    resonance: float = 1.0
    
    # Cloning information
    is_cloned: bool = False
    reference_audio_path: Optional[str] = None
    cloning_quality: float = 0.0  # 0-1, quality of the clone
    
    # Usage statistics
    usage_count: int = 0
    last_used: Optional[str] = None
    user_rating: float = 0.0  # User satisfaction rating


@dataclass
class EmotionConfig:
    """Configuration for emotional voice synthesis."""
    emotion: EmotionType
    intensity: float = 1.0  # 0.0-2.0, how strong the emotion is
    
    # Emotion-specific parameters
    pitch_modifier: float = 1.0
    speed_modifier: float = 1.0
    volume_modifier: float = 1.0
    pause_modifier: float = 1.0  # Affects pauses between words/sentences
    
    # Advanced emotional parameters
    vibrato: float = 0.0  # Voice trembling/vibration
    tension: float = 0.0  # Voice tension/stress
    energy: float = 1.0   # Overall energy level


class VoiceCloningManager:
    """Manages voice cloning, customization, and emotional synthesis."""
    
    def __init__(self):
        self.tts_manager = TTSModelManager()
        self.voice_profiles = {}
        self.emotion_presets = self._create_emotion_presets()
        self.voice_cache = {}
        self.profiles_file = Path("config/voice_profiles.json")
        
        # Load existing profiles
        self._load_voice_profiles()
    
    def _create_emotion_presets(self) -> Dict[EmotionType, EmotionConfig]:
        """Create predefined emotion configurations."""
        return {
            EmotionType.NEUTRAL: EmotionConfig(
                emotion=EmotionType.NEUTRAL,
                intensity=1.0,
                pitch_modifier=1.0,
                speed_modifier=1.0,
                volume_modifier=1.0,
                pause_modifier=1.0
            ),
            
            EmotionType.HAPPY: EmotionConfig(
                emotion=EmotionType.HAPPY,
                intensity=1.0,
                pitch_modifier=1.2,  # Higher pitch
                speed_modifier=1.1,  # Slightly faster
                volume_modifier=1.1, # Slightly louder
                pause_modifier=0.8,  # Shorter pauses
                energy=1.3
            ),
            
            EmotionType.SAD: EmotionConfig(
                emotion=EmotionType.SAD,
                intensity=1.0,
                pitch_modifier=0.8,  # Lower pitch
                speed_modifier=0.8,  # Slower
                volume_modifier=0.9, # Quieter
                pause_modifier=1.3,  # Longer pauses
                energy=0.7
            ),
            
            EmotionType.ANGRY: EmotionConfig(
                emotion=EmotionType.ANGRY,
                intensity=1.0,
                pitch_modifier=1.1,  # Slightly higher pitch
                speed_modifier=1.2,  # Faster
                volume_modifier=1.3, # Louder
                pause_modifier=0.6,  # Shorter pauses
                tension=1.5,
                energy=1.5
            ),
            
            EmotionType.EXCITED: EmotionConfig(
                emotion=EmotionType.EXCITED,
                intensity=1.0,
                pitch_modifier=1.3,  # Higher pitch
                speed_modifier=1.3,  # Much faster
                volume_modifier=1.2, # Louder
                pause_modifier=0.5,  # Very short pauses
                energy=1.6,
                vibrato=0.3
            ),
            
            EmotionType.CALM: EmotionConfig(
                emotion=EmotionType.CALM,
                intensity=1.0,
                pitch_modifier=0.95, # Slightly lower pitch
                speed_modifier=0.9,  # Slower
                volume_modifier=0.95,# Slightly quieter
                pause_modifier=1.2,  # Longer pauses
                energy=0.8
            ),
            
            EmotionType.PROFESSIONAL: EmotionConfig(
                emotion=EmotionType.PROFESSIONAL,
                intensity=1.0,
                pitch_modifier=1.0,  # Neutral pitch
                speed_modifier=0.95, # Slightly slower for clarity
                volume_modifier=1.0, # Normal volume
                pause_modifier=1.1,  # Slightly longer pauses
                energy=1.0
            ),
            
            EmotionType.CONFIDENT: EmotionConfig(
                emotion=EmotionType.CONFIDENT,
                intensity=1.0,
                pitch_modifier=0.9,  # Lower, more authoritative
                speed_modifier=0.95, # Measured pace
                volume_modifier=1.1, # Slightly louder
                pause_modifier=1.0,  # Normal pauses
                energy=1.2
            ),
            
            EmotionType.FRIENDLY: EmotionConfig(
                emotion=EmotionType.FRIENDLY,
                intensity=1.0,
                pitch_modifier=1.1,  # Slightly higher, warmer
                speed_modifier=1.0,  # Normal speed
                volume_modifier=1.05,# Slightly louder
                pause_modifier=0.9,  # Shorter pauses
                energy=1.1
            )
        }
    
    def _load_voice_profiles(self) -> None:
        """Load voice profiles from file."""
        try:
            if self.profiles_file.exists():
                with open(self.profiles_file, 'r') as f:
                    data = json.load(f)
                    
                for profile_name, profile_data in data.items():
                    # Convert enum strings back to enums
                    if 'default_emotion' in profile_data:
                        profile_data['default_emotion'] = EmotionType(profile_data['default_emotion'])
                    if 'emotion_range' in profile_data:
                        profile_data['emotion_range'] = [EmotionType(e) for e in profile_data['emotion_range']]
                    if 'base_model' in profile_data:
                        profile_data['base_model'] = TTSModelType(profile_data['base_model'])
                    
                    self.voice_profiles[profile_name] = VoiceProfile(**profile_data)
                    
                logger.info(f"Loaded {len(self.voice_profiles)} voice profiles")
                
        except Exception as e:
            logger.warning(f"Failed to load voice profiles: {e}")
    
    def _save_voice_profiles(self) -> None:
        """Save voice profiles to file."""
        try:
            self.profiles_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert profiles to serializable format
            data = {}
            for name, profile in self.voice_profiles.items():
                profile_dict = asdict(profile)
                # Convert enums to strings
                profile_dict['default_emotion'] = profile.default_emotion.value
                profile_dict['emotion_range'] = [e.value for e in profile.emotion_range]
                profile_dict['base_model'] = profile.base_model.value
                data[name] = profile_dict
            
            with open(self.profiles_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
                
            logger.info("Voice profiles saved successfully")
            
        except Exception as e:
            logger.error(f"Failed to save voice profiles: {e}")
    
    async def clone_voice_from_audio(
        self,
        reference_audio_path: Path,
        profile_name: str,
        language: str = "en",
        model_type: Optional[TTSModelType] = None
    ) -> Optional[VoiceProfile]:
        """Clone a voice from reference audio and create a voice profile."""
        if not reference_audio_path.exists():
            logger.error(f"Reference audio file not found: {reference_audio_path}")
            return None
        
        try:
            # Analyze reference audio
            audio_analysis = await self._analyze_reference_audio(reference_audio_path)
            
            # Select best cloning model if not specified
            if model_type is None:
                model_type = await self._select_best_cloning_model()
            
            if model_type is None:
                logger.error("No suitable voice cloning models available")
                return None
            
            # Test the cloning quality
            test_text = "This is a test to evaluate the quality of voice cloning."
            test_output = await self.tts_manager.clone_voice(
                reference_audio_path, test_text, model_type=model_type
            )
            
            if test_output is None:
                logger.error("Voice cloning test failed")
                return None
            
            # Evaluate cloning quality
            cloning_quality = await self._evaluate_cloning_quality(
                reference_audio_path, test_output
            )
            
            # Create voice profile
            voice_profile = VoiceProfile(
                name=profile_name,
                base_model=model_type,
                voice_id=f"cloned_{profile_name}",
                language=language,
                gender=audio_analysis.get("gender", "neutral"),
                age_group=audio_analysis.get("age_group", "adult"),
                accent=audio_analysis.get("accent", "neutral"),
                default_emotion=EmotionType.NEUTRAL,
                emotion_range=[EmotionType.NEUTRAL, EmotionType.HAPPY, EmotionType.CALM, EmotionType.PROFESSIONAL],
                pitch=audio_analysis.get("pitch", 1.0),
                speed=audio_analysis.get("speed", 1.0),
                volume=audio_analysis.get("volume", 1.0),
                is_cloned=True,
                reference_audio_path=str(reference_audio_path),
                cloning_quality=cloning_quality
            )
            
            # Save profile
            self.voice_profiles[profile_name] = voice_profile
            self._save_voice_profiles()
            
            # Clean up test file
            if test_output.exists():
                test_output.unlink()
            
            logger.info(f"Successfully cloned voice '{profile_name}' with quality {cloning_quality:.2f}")
            return voice_profile
            
        except Exception as e:
            logger.error(f"Voice cloning failed: {e}")
            return None
    
    async def _analyze_reference_audio(self, audio_path: Path) -> Dict[str, Any]:
        """Analyze reference audio to extract voice characteristics."""
        try:
            # Load audio
            audio, sr = librosa.load(str(audio_path), sr=None)
            
            # Extract features
            analysis = {}
            
            # Pitch analysis
            pitches, magnitudes = librosa.piptrack(y=audio, sr=sr)
            pitch_values = pitches[magnitudes > np.median(magnitudes)]
            if len(pitch_values) > 0:
                mean_pitch = np.mean(pitch_values[pitch_values > 0])
                analysis["pitch"] = min(2.0, max(0.5, mean_pitch / 200.0))  # Normalize to 0.5-2.0
            else:
                analysis["pitch"] = 1.0
            
            # Speed analysis (approximate)
            tempo, _ = librosa.beat.beat_track(y=audio, sr=sr)
            analysis["speed"] = min(2.0, max(0.5, tempo / 120.0))  # Normalize around 120 BPM
            
            # Volume analysis
            rms = librosa.feature.rms(y=audio)[0]
            mean_volume = np.mean(rms)
            analysis["volume"] = min(2.0, max(0.5, mean_volume * 10))  # Normalize
            
            # Gender estimation (very basic)
            fundamental_freq = np.mean(pitch_values[pitch_values > 0]) if len(pitch_values) > 0 else 150
            if fundamental_freq > 180:
                analysis["gender"] = "female"
            elif fundamental_freq < 120:
                analysis["gender"] = "male"
            else:
                analysis["gender"] = "neutral"
            
            # Age group estimation (basic)
            if fundamental_freq > 250:
                analysis["age_group"] = "child"
            elif fundamental_freq > 200:
                analysis["age_group"] = "young_adult"
            elif fundamental_freq > 100:
                analysis["age_group"] = "adult"
            else:
                analysis["age_group"] = "elderly"
            
            # Accent detection (placeholder)
            analysis["accent"] = "neutral"  # Would need more sophisticated analysis
            
            return analysis
            
        except Exception as e:
            logger.warning(f"Audio analysis failed: {e}")
            return {
                "pitch": 1.0,
                "speed": 1.0,
                "volume": 1.0,
                "gender": "neutral",
                "age_group": "adult",
                "accent": "neutral"
            }
    
    async def _select_best_cloning_model(self) -> Optional[TTSModelType]:
        """Select the best available model for voice cloning."""
        # Priority order for cloning quality
        cloning_models = [
            TTSModelType.TORTOISE,  # Highest quality
            TTSModelType.COQUI,     # Good quality, faster
            TTSModelType.BARK,      # Good with emotions
            TTSModelType.XTTS       # Fast cloning
        ]
        
        for model_type in cloning_models:
            if await self.tts_manager.check_model_availability(model_type):
                model_info = self.tts_manager.get_model_info(model_type)
                if model_info and model_info.supports_voice_cloning:
                    return model_type
        
        return None
    
    async def _evaluate_cloning_quality(
        self, 
        reference_path: Path, 
        cloned_path: Path
    ) -> float:
        """Evaluate the quality of voice cloning (0-1 score)."""
        try:
            # Load both audio files
            ref_audio, ref_sr = librosa.load(str(reference_path), sr=None)
            cloned_audio, cloned_sr = librosa.load(str(cloned_path), sr=None)
            
            # Resample if needed
            if ref_sr != cloned_sr:
                cloned_audio = librosa.resample(cloned_audio, orig_sr=cloned_sr, target_sr=ref_sr)
            
            # Extract features for comparison
            ref_mfcc = librosa.feature.mfcc(y=ref_audio, sr=ref_sr, n_mfcc=13)
            cloned_mfcc = librosa.feature.mfcc(y=cloned_audio, sr=ref_sr, n_mfcc=13)
            
            # Calculate similarity (simplified)
            # In practice, would use more sophisticated metrics
            min_frames = min(ref_mfcc.shape[1], cloned_mfcc.shape[1])
            ref_mfcc_truncated = ref_mfcc[:, :min_frames]
            cloned_mfcc_truncated = cloned_mfcc[:, :min_frames]
            
            # Cosine similarity
            ref_flat = ref_mfcc_truncated.flatten()
            cloned_flat = cloned_mfcc_truncated.flatten()
            
            dot_product = np.dot(ref_flat, cloned_flat)
            norm_ref = np.linalg.norm(ref_flat)
            norm_cloned = np.linalg.norm(cloned_flat)
            
            if norm_ref == 0 or norm_cloned == 0:
                return 0.5  # Default score
            
            similarity = dot_product / (norm_ref * norm_cloned)
            
            # Convert to 0-1 score (cosine similarity is -1 to 1)
            quality_score = (similarity + 1) / 2
            
            return max(0.0, min(1.0, quality_score))
            
        except Exception as e:
            logger.warning(f"Quality evaluation failed: {e}")
            return 0.5  # Default score
    
    async def synthesize_with_emotion(
        self,
        text: str,
        voice_profile: VoiceProfile,
        emotion: EmotionType,
        intensity: float = 1.0,
        output_path: Optional[Path] = None
    ) -> Optional[Path]:
        """Synthesize speech with specific emotion and voice profile."""
        try:
            # Get emotion configuration
            emotion_config = self.emotion_presets.get(emotion, self.emotion_presets[EmotionType.NEUTRAL])
            
            # Apply intensity scaling
            scaled_config = EmotionConfig(
                emotion=emotion,
                intensity=intensity,
                pitch_modifier=1.0 + (emotion_config.pitch_modifier - 1.0) * intensity,
                speed_modifier=1.0 + (emotion_config.speed_modifier - 1.0) * intensity,
                volume_modifier=1.0 + (emotion_config.volume_modifier - 1.0) * intensity,
                pause_modifier=1.0 + (emotion_config.pause_modifier - 1.0) * intensity,
                vibrato=emotion_config.vibrato * intensity,
                tension=emotion_config.tension * intensity,
                energy=1.0 + (emotion_config.energy - 1.0) * intensity
            )
            
            # Create voice configuration
            voice_config = VoiceConfig(
                model_type=voice_profile.base_model,
                voice_id=voice_profile.voice_id,
                language=voice_profile.language,
                speed=voice_profile.speed * scaled_config.speed_modifier,
                pitch=voice_profile.pitch * scaled_config.pitch_modifier,
                volume=voice_profile.volume * scaled_config.volume_modifier
            )
            
            # Preprocess text for emotion
            processed_text = await self._preprocess_text_for_emotion(text, scaled_config)
            
            # Synthesize speech
            if voice_profile.is_cloned and voice_profile.reference_audio_path:
                # Use voice cloning
                result_path = await self.tts_manager.clone_voice(
                    Path(voice_profile.reference_audio_path),
                    processed_text,
                    output_path,
                    voice_profile.base_model
                )
            else:
                # Use regular synthesis
                result_path = await self.tts_manager.synthesize_speech(
                    processed_text,
                    voice_config,
                    output_path
                )
            
            # Apply post-processing for emotion
            if result_path:
                await self._apply_emotion_post_processing(result_path, scaled_config)
            
            # Update usage statistics
            voice_profile.usage_count += 1
            voice_profile.last_used = str(asyncio.get_event_loop().time())
            self._save_voice_profiles()
            
            return result_path
            
        except Exception as e:
            logger.error(f"Emotional synthesis failed: {e}")
            return None
    
    async def _preprocess_text_for_emotion(self, text: str, emotion_config: EmotionConfig) -> str:
        """Preprocess text to enhance emotional expression."""
        try:
            processed_text = text
            
            # Add pauses for emotional effect
            if emotion_config.pause_modifier > 1.2:
                # Add longer pauses for sad/calm emotions
                processed_text = processed_text.replace(". ", "... ")
                processed_text = processed_text.replace(", ", ",... ")
            elif emotion_config.pause_modifier < 0.8:
                # Reduce pauses for excited/happy emotions
                processed_text = processed_text.replace("...", ".")
                processed_text = processed_text.replace(", ", ",")
            
            # Add emphasis for strong emotions
            if emotion_config.intensity > 1.3:
                # Add emphasis markers (model-dependent)
                if emotion_config.emotion == EmotionType.EXCITED:
                    processed_text = processed_text.replace("!", "!!")
                elif emotion_config.emotion == EmotionType.ANGRY:
                    processed_text = processed_text.upper()
            
            return processed_text
            
        except Exception as e:
            logger.warning(f"Text preprocessing failed: {e}")
            return text
    
    async def _apply_emotion_post_processing(self, audio_path: Path, emotion_config: EmotionConfig) -> None:
        """Apply post-processing effects to enhance emotional expression."""
        try:
            # Load audio
            audio, sr = librosa.load(str(audio_path), sr=None)
            
            # Apply vibrato effect
            if emotion_config.vibrato > 0:
                vibrato_rate = 5.0  # Hz
                vibrato_depth = emotion_config.vibrato * 0.1
                t = np.arange(len(audio)) / sr
                vibrato = 1 + vibrato_depth * np.sin(2 * np.pi * vibrato_rate * t)
                audio = audio * vibrato
            
            # Apply tension effect (slight distortion)
            if emotion_config.tension > 1.0:
                tension_factor = min(emotion_config.tension, 2.0)
                audio = np.tanh(audio * tension_factor) / tension_factor
            
            # Apply energy modification (dynamic range)
            if emotion_config.energy != 1.0:
                audio = audio * emotion_config.energy
                # Prevent clipping
                audio = np.clip(audio, -1.0, 1.0)
            
            # Save modified audio
            sf.write(str(audio_path), audio, sr)
            
        except Exception as e:
            logger.warning(f"Emotion post-processing failed: {e}")
    
    def create_custom_voice_profile(
        self,
        name: str,
        base_model: TTSModelType,
        voice_id: str,
        language: str = "en",
        characteristics: Optional[Dict[VoiceCharacteristics, float]] = None
    ) -> VoiceProfile:
        """Create a custom voice profile with specified characteristics."""
        # Default characteristics
        default_chars = {
            VoiceCharacteristics.PITCH: 1.0,
            VoiceCharacteristics.SPEED: 1.0,
            VoiceCharacteristics.VOLUME: 1.0,
            VoiceCharacteristics.BREATHINESS: 1.0,
            VoiceCharacteristics.ROUGHNESS: 1.0,
            VoiceCharacteristics.WARMTH: 1.0,
            VoiceCharacteristics.CLARITY: 1.0,
            VoiceCharacteristics.RESONANCE: 1.0
        }
        
        if characteristics:
            default_chars.update(characteristics)
        
        voice_profile = VoiceProfile(
            name=name,
            base_model=base_model,
            voice_id=voice_id,
            language=language,
            gender="neutral",
            age_group="adult",
            accent="neutral",
            default_emotion=EmotionType.NEUTRAL,
            emotion_range=list(EmotionType),
            pitch=default_chars[VoiceCharacteristics.PITCH],
            speed=default_chars[VoiceCharacteristics.SPEED],
            volume=default_chars[VoiceCharacteristics.VOLUME],
            breathiness=default_chars[VoiceCharacteristics.BREATHINESS],
            roughness=default_chars[VoiceCharacteristics.ROUGHNESS],
            warmth=default_chars[VoiceCharacteristics.WARMTH],
            clarity=default_chars[VoiceCharacteristics.CLARITY],
            resonance=default_chars[VoiceCharacteristics.RESONANCE]
        )
        
        # Save profile
        self.voice_profiles[name] = voice_profile
        self._save_voice_profiles()
        
        return voice_profile
    
    def get_voice_profile(self, name: str) -> Optional[VoiceProfile]:
        """Get a voice profile by name."""
        return self.voice_profiles.get(name)
    
    def list_voice_profiles(self) -> List[VoiceProfile]:
        """Get all available voice profiles."""
        return list(self.voice_profiles.values())
    
    def delete_voice_profile(self, name: str) -> bool:
        """Delete a voice profile."""
        if name in self.voice_profiles:
            del self.voice_profiles[name]
            self._save_voice_profiles()
            return True
        return False
    
    async def test_voice_profile(
        self,
        profile_name: str,
        test_text: Optional[str] = None,
        emotion: EmotionType = EmotionType.NEUTRAL
    ) -> Optional[Path]:
        """Test a voice profile with sample text."""
        profile = self.get_voice_profile(profile_name)
        if not profile:
            logger.error(f"Voice profile '{profile_name}' not found")
            return None
        
        if test_text is None:
            test_text = f"Hello, this is a test of the {profile_name} voice profile with {emotion.value} emotion."
        
        return await self.synthesize_with_emotion(
            test_text, profile, emotion
        )
    
    def get_emotion_presets(self) -> Dict[EmotionType, EmotionConfig]:
        """Get all available emotion presets."""
        return self.emotion_presets.copy()
    
    def create_custom_emotion(
        self,
        name: str,
        base_emotion: EmotionType,
        modifications: Dict[str, float]
    ) -> EmotionConfig:
        """Create a custom emotion configuration."""
        base_config = self.emotion_presets[base_emotion]
        
        # Apply modifications
        custom_config = EmotionConfig(
            emotion=EmotionType.NEUTRAL,  # Custom emotion
            intensity=modifications.get("intensity", base_config.intensity),
            pitch_modifier=modifications.get("pitch_modifier", base_config.pitch_modifier),
            speed_modifier=modifications.get("speed_modifier", base_config.speed_modifier),
            volume_modifier=modifications.get("volume_modifier", base_config.volume_modifier),
            pause_modifier=modifications.get("pause_modifier", base_config.pause_modifier),
            vibrato=modifications.get("vibrato", base_config.vibrato),
            tension=modifications.get("tension", base_config.tension),
            energy=modifications.get("energy", base_config.energy)
        )
        
        # Store custom emotion (could be saved to file)
        self.emotion_presets[EmotionType.NEUTRAL] = custom_config  # Placeholder
        
        return custom_config


# Global instance for easy access
voice_cloning_manager = VoiceCloningManager()