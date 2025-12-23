"""
TTS and Audio Processing Service for the RASO platform.

Provides text-to-speech generation, audio synchronization, and processing
using Coqui TTS and other audio libraries.
"""

import os
import asyncio
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import wave
import json

from pydantic import BaseModel, Field

from backend.config import get_config
from agents.logging import AgentLogger
from agents.retry import retry


class AudioSegment(BaseModel):
    """Audio segment with timing information."""
    
    text: str = Field(..., description="Text content")
    start_time: float = Field(..., description="Start time in seconds")
    end_time: float = Field(..., description="End time in seconds")
    file_path: Optional[str] = Field(default=None, description="Path to audio file")
    
    @property
    def duration(self) -> float:
        """Get segment duration."""
        return self.end_time - self.start_time


class AudioProcessingResult(BaseModel):
    """Result of audio processing."""
    
    success: bool = Field(..., description="Whether processing succeeded")
    output_path: Optional[str] = Field(default=None, description="Path to processed audio")
    duration: float = Field(..., description="Audio duration in seconds")
    sample_rate: int = Field(..., description="Audio sample rate")
    channels: int = Field(default=1, description="Number of audio channels")
    file_size: int = Field(default=0, description="File size in bytes")
    processing_time: float = Field(..., description="Processing time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")


class TTSService:
    """Text-to-speech service using Coqui TTS."""
    
    def __init__(self):
        """Initialize TTS service."""
        self.config = get_config()
        self.logger = AgentLogger(None)
        self._tts_model = None
    
    async def initialize(self) -> None:
        """Initialize TTS model."""
        try:
            # Import TTS here to avoid startup delays
            from TTS.api import TTS
            
            model_name = self.config.audio.tts_model
            self.logger.info(f"Loading TTS model: {model_name}")
            
            # Load model in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            self._tts_model = await loop.run_in_executor(
                None, 
                lambda: TTS(model_name=model_name)
            )
            
            self.logger.info("TTS model loaded successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize TTS model: {str(e)}")
            raise
    
    @retry(max_attempts=3, base_delay=1.0)
    async def generate_speech(
        self,
        text: str,
        output_path: str,
        voice_speed: float = 1.0,
        voice_pitch: float = 1.0,
    ) -> AudioProcessingResult:
        """
        Generate speech from text.
        
        Args:
            text: Text to synthesize
            output_path: Output audio file path
            voice_speed: Speech speed multiplier
            voice_pitch: Voice pitch multiplier
            
        Returns:
            Audio processing result
        """
        start_time = datetime.now()
        
        try:
            if not self._tts_model:
                await self.initialize()
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            if not cleaned_text.strip():
                return AudioProcessingResult(
                    success=False,
                    duration=0.0,
                    sample_rate=self.config.audio.sample_rate,
                    processing_time=0.0,
                    error_message="Empty text after cleaning",
                )
            
            # Generate speech in thread pool
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._tts_model.tts_to_file(
                    text=cleaned_text,
                    file_path=output_path,
                    speed=voice_speed,
                )
            )
            
            # Post-process audio if needed
            if voice_pitch != 1.0:
                await self._adjust_pitch(output_path, voice_pitch)
            
            # Get audio info
            duration, sample_rate, channels = await self._get_audio_info(output_path)
            file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
            
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AudioProcessingResult(
                success=True,
                output_path=output_path,
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                file_size=file_size,
                processing_time=processing_time,
            )
            
        except Exception as e:
            processing_time = (datetime.now() - start_time).total_seconds()
            
            return AudioProcessingResult(
                success=False,
                duration=0.0,
                sample_rate=self.config.audio.sample_rate,
                processing_time=processing_time,
                error_message=str(e),
            )
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS processing."""
        # Remove markdown formatting
        import re
        
        # Remove markdown links
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
        
        # Remove markdown emphasis
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)
        
        # Remove code blocks
        text = re.sub(r'```[^`]*```', '', text)
        text = re.sub(r'`([^`]+)`', r'\1', text)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Limit length for TTS stability
        max_length = 1000
        if len(text) > max_length:
            # Find last sentence boundary within limit
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            if last_period > max_length * 0.8:  # If period is reasonably close to end
                text = truncated[:last_period + 1]
            else:
                text = truncated + "..."
        
        return text
    
    async def _adjust_pitch(self, audio_path: str, pitch_factor: float) -> None:
        """Adjust audio pitch using ffmpeg."""
        if abs(pitch_factor - 1.0) < 0.01:  # No significant change
            return
        
        temp_path = audio_path + ".temp.wav"
        
        # Use ffmpeg to adjust pitch
        command = [
            "ffmpeg", "-i", audio_path,
            "-af", f"asetrate={int(self.config.audio.sample_rate * pitch_factor)},aresample={self.config.audio.sample_rate}",
            "-y", temp_path
        ]
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                # Replace original with processed
                os.replace(temp_path, audio_path)
            else:
                self.logger.warning(f"Pitch adjustment failed for {audio_path}")
                
        except Exception as e:
            self.logger.warning(f"Pitch adjustment error: {str(e)}")
        
        finally:
            # Clean up temp file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
    async def _get_audio_info(self, audio_path: str) -> Tuple[float, int, int]:
        """Get audio file information."""
        try:
            # Use ffprobe to get audio info
            command = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                
                # Extract audio stream info
                audio_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "audio":
                        audio_stream = stream
                        break
                
                if audio_stream:
                    duration = float(audio_stream.get("duration", 0))
                    sample_rate = int(audio_stream.get("sample_rate", self.config.audio.sample_rate))
                    channels = int(audio_stream.get("channels", 1))
                    
                    return duration, sample_rate, channels
            
            # Fallback: try with wave module for WAV files
            if audio_path.lower().endswith('.wav'):
                with wave.open(audio_path, 'rb') as wav_file:
                    frames = wav_file.getnframes()
                    sample_rate = wav_file.getframerate()
                    channels = wav_file.getnchannels()
                    duration = frames / sample_rate
                    
                    return duration, sample_rate, channels
            
        except Exception as e:
            self.logger.warning(f"Failed to get audio info for {audio_path}: {str(e)}")
        
        # Default fallback
        return 0.0, self.config.audio.sample_rate, 1
    
    async def estimate_speech_duration(self, text: str, words_per_minute: int = 150) -> float:
        """
        Estimate speech duration for text.
        
        Args:
            text: Text to estimate
            words_per_minute: Speaking rate
            
        Returns:
            Estimated duration in seconds
        """
        cleaned_text = self._clean_text_for_tts(text)
        word_count = len(cleaned_text.split())
        
        # Calculate duration with some padding
        duration = (word_count / words_per_minute) * 60
        
        # Add padding for natural pauses
        duration *= 1.2
        
        return max(duration, 1.0)  # Minimum 1 second


class AudioSynchronizer:
    """Synchronizes audio with visual content."""
    
    def __init__(self):
        """Initialize audio synchronizer."""
        self.config = get_config()
        self.logger = AgentLogger(None)
    
    async def synchronize_scene_audio(
        self,
        audio_path: str,
        target_duration: float,
        output_path: str,
    ) -> AudioProcessingResult:
        """
        Synchronize audio to match target duration.
        
        Args:
            audio_path: Input audio file
            target_duration: Target duration in seconds
            output_path: Output audio file
            
        Returns:
            Audio processing result
        """
        start_time = datetime.now()
        
        try:
            # Get current audio duration
            current_duration, sample_rate, channels = await self._get_audio_info(audio_path)
            
            if abs(current_duration - target_duration) < 0.1:
                # Duration is close enough, just copy
                import shutil
                shutil.copy2(audio_path, output_path)
                
                return AudioProcessingResult(
                    success=True,
                    output_path=output_path,
                    duration=current_duration,
                    sample_rate=sample_rate,
                    channels=channels,
                    file_size=os.path.getsize(output_path),
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )
            
            # Calculate speed adjustment
            speed_factor = current_duration / target_duration
            
            # Limit speed adjustment to reasonable range
            speed_factor = max(0.5, min(2.0, speed_factor))
            
            # Use ffmpeg to adjust speed
            command = [
                "ffmpeg", "-i", audio_path,
                "-filter:a", f"atempo={speed_factor}",
                "-y", output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and os.path.exists(output_path):
                # Get final audio info
                final_duration, final_sample_rate, final_channels = await self._get_audio_info(output_path)
                file_size = os.path.getsize(output_path)
                
                return AudioProcessingResult(
                    success=True,
                    output_path=output_path,
                    duration=final_duration,
                    sample_rate=final_sample_rate,
                    channels=final_channels,
                    file_size=file_size,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                )
            else:
                return AudioProcessingResult(
                    success=False,
                    duration=0.0,
                    sample_rate=sample_rate,
                    processing_time=(datetime.now() - start_time).total_seconds(),
                    error_message=f"ffmpeg failed: {stderr.decode()}",
                )
                
        except Exception as e:
            return AudioProcessingResult(
                success=False,
                duration=0.0,
                sample_rate=self.config.audio.sample_rate,
                processing_time=(datetime.now() - start_time).total_seconds(),
                error_message=str(e),
            )
    
    async def _get_audio_info(self, audio_path: str) -> Tuple[float, int, int]:
        """Get audio file information (same as TTSService method)."""
        try:
            command = [
                "ffprobe", "-v", "quiet",
                "-print_format", "json",
                "-show_format", "-show_streams",
                audio_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                
                audio_stream = None
                for stream in info.get("streams", []):
                    if stream.get("codec_type") == "audio":
                        audio_stream = stream
                        break
                
                if audio_stream:
                    duration = float(audio_stream.get("duration", 0))
                    sample_rate = int(audio_stream.get("sample_rate", self.config.audio.sample_rate))
                    channels = int(audio_stream.get("channels", 1))
                    
                    return duration, sample_rate, channels
            
        except Exception as e:
            self.logger.warning(f"Failed to get audio info: {str(e)}")
        
        return 0.0, self.config.audio.sample_rate, 1
    
    async def normalize_audio_levels(
        self,
        audio_paths: List[str],
        output_dir: str,
    ) -> List[AudioProcessingResult]:
        """
        Normalize audio levels across multiple files.
        
        Args:
            audio_paths: List of input audio files
            output_dir: Output directory for normalized files
            
        Returns:
            List of processing results
        """
        results = []
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        for i, audio_path in enumerate(audio_paths):
            output_path = os.path.join(output_dir, f"normalized_{i}.wav")
            
            try:
                # Use ffmpeg loudnorm filter for audio normalization
                command = [
                    "ffmpeg", "-i", audio_path,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", str(self.config.audio.sample_rate),
                    "-y", output_path
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *command,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
                
                await process.communicate()
                
                if process.returncode == 0 and os.path.exists(output_path):
                    duration, sample_rate, channels = await self._get_audio_info(output_path)
                    file_size = os.path.getsize(output_path)
                    
                    results.append(AudioProcessingResult(
                        success=True,
                        output_path=output_path,
                        duration=duration,
                        sample_rate=sample_rate,
                        channels=channels,
                        file_size=file_size,
                        processing_time=0.0,
                    ))
                else:
                    results.append(AudioProcessingResult(
                        success=False,
                        duration=0.0,
                        sample_rate=self.config.audio.sample_rate,
                        processing_time=0.0,
                        error_message="Normalization failed",
                    ))
                    
            except Exception as e:
                results.append(AudioProcessingResult(
                    success=False,
                    duration=0.0,
                    sample_rate=self.config.audio.sample_rate,
                    processing_time=0.0,
                    error_message=str(e),
                ))
        
        return results


# Global service instances
tts_service = TTSService()
audio_synchronizer = AudioSynchronizer()