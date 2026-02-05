"""
Simple Audio Generator for RASO platform.

Creates working audio files from script scenes using basic TTS systems.
No complex AI dependencies - focuses on reliable audio generation.
"""

import os
import asyncio
import platform
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

# Fix import paths to use config/backend/models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'backend'))

from models.script import NarrationScript, Scene
from models.audio import AudioAssets, AudioScene


class SimpleAudioGenerator:
    """Simple, reliable audio generator without complex AI dependencies."""
    
    def __init__(self):
        """Initialize the simple audio generator."""
        self.sample_rate = 44100  # Use standard sample rate for video production
        self.channels = 1  # Mono for narration
        self.voice_speed = 150  # Words per minute
        
        # TTS engine availability
        self.tts_engines = {
            'pyttsx3': False,
            'windows_sapi': False,
            'macos_say': False,
            'linux_espeak': False
        }
        
        self._check_tts_availability()
    
    def _check_tts_availability(self) -> None:
        """Check which TTS engines are available on this system."""
        # Check pyttsx3
        try:
            import pyttsx3
            self.tts_engines['pyttsx3'] = True
        except ImportError:
            pass
        
        # Check system-specific TTS
        system = platform.system().lower()
        if system == "windows":
            self.tts_engines['windows_sapi'] = True
        elif system == "darwin":
            self.tts_engines['macos_say'] = True
        elif system == "linux":
            # Check if espeak is available
            try:
                result = subprocess.run(['espeak', '--version'], 
                                      capture_output=True, timeout=5)
                if result.returncode == 0:
                    self.tts_engines['linux_espeak'] = True
            except (subprocess.TimeoutExpired, FileNotFoundError):
                pass
    
    async def generate_audio_assets(self, script: NarrationScript, output_dir: str) -> AudioAssets:
        """
        Generate audio assets from a narration script.
        
        Args:
            script: The narration script to convert to audio
            output_dir: Directory to save audio files
            
        Returns:
            Complete audio assets with all scene audio files
        """
        # Create output directory
        audio_dir = Path(output_dir) / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate audio for each scene
        audio_scenes = []
        
        for i, scene in enumerate(script.scenes):
            print(f"Generating audio for scene {i+1}/{len(script.scenes)}: {scene.title}")
            
            audio_scene = await self._generate_scene_audio(scene, audio_dir)
            
            if audio_scene:
                audio_scenes.append(audio_scene)
                print(f"✅ Audio generated for scene {scene.id}")
            else:
                print(f"❌ Failed to generate audio for scene {scene.id}")
                # Create fallback silent audio
                audio_scene = await self._create_fallback_audio(scene, audio_dir)
                if audio_scene:
                    audio_scenes.append(audio_scene)
        
        # Create audio assets
        total_duration = sum(scene.duration for scene in audio_scenes)
        
        audio_assets = AudioAssets(
            scenes=audio_scenes,
            total_duration=total_duration,
            sample_rate=self.sample_rate
        )
        
        return audio_assets
    
    async def _generate_scene_audio(self, scene: Scene, output_dir: Path) -> Optional[AudioScene]:
        """Generate audio for a single scene."""
        try:
            # Create scene-specific directory
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            audio_path = scene_dir / f"{scene.id}.wav"
            
            # Try TTS engines in order of preference
            success = False
            
            # Try pyttsx3 first (cross-platform)
            if self.tts_engines['pyttsx3'] and not success:
                success = await self._generate_pyttsx3_audio(scene.narration, str(audio_path))
                if success:
                    print(f"  Used pyttsx3 TTS for scene {scene.id}")
            
            # Try system TTS
            if not success:
                if self.tts_engines['windows_sapi']:
                    success = await self._generate_windows_sapi_audio(scene.narration, str(audio_path))
                    if success:
                        print(f"  Used Windows SAPI for scene {scene.id}")
                
                elif self.tts_engines['macos_say']:
                    success = await self._generate_macos_say_audio(scene.narration, str(audio_path))
                    if success:
                        print(f"  Used macOS say for scene {scene.id}")
                
                elif self.tts_engines['linux_espeak']:
                    success = await self._generate_linux_espeak_audio(scene.narration, str(audio_path))
                    if success:
                        print(f"  Used Linux espeak for scene {scene.id}")
            
            if not success:
                print(f"  All TTS methods failed for scene {scene.id}")
                return None
            
            # Verify audio file was created
            if not audio_path.exists() or audio_path.stat().st_size == 0:
                print(f"  Audio file not created or empty for scene {scene.id}")
                return None
            
            # Get actual audio duration
            actual_duration = await self._get_audio_duration(str(audio_path))
            if actual_duration == 0:
                actual_duration = scene.duration  # Fallback to estimated duration
            
            # Create timing markers (simple word-level timing)
            timing_markers = self._create_timing_markers(scene.narration, actual_duration)
            
            # Create audio scene
            audio_scene = AudioScene(
                scene_id=scene.id,
                file_path=str(audio_path),
                duration=actual_duration,
                transcript=scene.narration,
                timing_markers=timing_markers
            )
            
            return audio_scene
            
        except Exception as e:
            print(f"Error generating audio for scene {scene.id}: {e}")
            return None
    
    async def _generate_pyttsx3_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using pyttsx3."""
        try:
            import pyttsx3
            
            def generate_tts():
                engine = pyttsx3.init()
                
                # Configure voice settings
                engine.setProperty('rate', self.voice_speed)  # Speed
                engine.setProperty('volume', 0.9)  # Volume
                
                # Try to set a good voice
                voices = engine.getProperty('voices')
                if voices:
                    # Prefer female voices for educational content
                    for voice in voices:
                        if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                            engine.setProperty('voice', voice.id)
                            break
                    else:
                        # Use first available voice
                        engine.setProperty('voice', voices[0].id)
                
                # Clean text for TTS
                cleaned_text = self._clean_text_for_tts(text)
                
                # Save to temporary file first
                temp_path = output_path.replace('.wav', '_temp.wav')
                engine.save_to_file(cleaned_text, temp_path)
                engine.runAndWait()
                engine.stop()
                
                return temp_path
            
            # Run TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            temp_path = await loop.run_in_executor(None, generate_tts)
            
            # Check if temp file was created
            if Path(temp_path).exists() and Path(temp_path).stat().st_size > 0:
                # Resample to correct sample rate using FFmpeg
                success = await self._resample_audio(temp_path, output_path, self.sample_rate)
                
                # Clean up temp file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                
                return success
            else:
                return False
            
        except Exception as e:
            print(f"pyttsx3 TTS failed: {e}")
            return False
    
    async def _generate_windows_sapi_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using Windows SAPI."""
        try:
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Create temporary file first
            temp_path = output_path.replace('.wav', '_sapi_temp.wav')
            
            # Use PowerShell with Windows Speech API
            powershell_cmd = f'''
            Add-Type -AssemblyName System.Speech
            $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
            $synth.SetOutputToWaveFile("{temp_path}")
            $synth.Rate = 0
            $synth.Volume = 90
            $synth.Speak("{cleaned_text}")
            $synth.Dispose()
            '''
            
            process = await asyncio.create_subprocess_exec(
                "powershell", "-Command", powershell_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and Path(temp_path).exists() and Path(temp_path).stat().st_size > 0:
                # Resample to correct sample rate
                success = await self._resample_audio(temp_path, output_path, self.sample_rate)
                
                # Clean up temp file
                try:
                    Path(temp_path).unlink()
                except:
                    pass
                
                return success
            else:
                return False
            
        except Exception as e:
            print(f"Windows SAPI TTS failed: {e}")
            return False
    
    async def _generate_macos_say_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using macOS say command."""
        try:
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Use say command to generate AIFF, then convert to WAV
            temp_aiff = output_path.replace('.wav', '.aiff')
            
            process = await asyncio.create_subprocess_exec(
                "say", "-o", temp_aiff, "-r", "150", cleaned_text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0 and Path(temp_aiff).exists():
                # Convert AIFF to WAV using ffmpeg
                convert_process = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-i", temp_aiff, "-y", output_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await convert_process.communicate()
                
                # Clean up temp file
                if Path(temp_aiff).exists():
                    Path(temp_aiff).unlink()
                
                return (convert_process.returncode == 0 and 
                        Path(output_path).exists() and 
                        Path(output_path).stat().st_size > 0)
            
            return False
            
        except Exception as e:
            print(f"macOS say TTS failed: {e}")
            return False
    
    async def _generate_linux_espeak_audio(self, text: str, output_path: str) -> bool:
        """Generate audio using Linux espeak."""
        try:
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            process = await asyncio.create_subprocess_exec(
                "espeak", "-w", output_path, "-s", "150", cleaned_text,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            return (process.returncode == 0 and 
                    Path(output_path).exists() and 
                    Path(output_path).stat().st_size > 0)
            
        except Exception as e:
            print(f"Linux espeak TTS failed: {e}")
            return False
    
    async def _create_fallback_audio(self, scene: Scene, output_dir: Path) -> Optional[AudioScene]:
        """Create fallback silent audio when TTS fails."""
        try:
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            audio_path = scene_dir / f"{scene.id}_silent.wav"
            
            # Create silent audio with proper duration
            await self._create_silent_audio(str(audio_path), scene.duration)
            
            if audio_path.exists():
                # Create timing markers for silent audio
                timing_markers = self._create_timing_markers(scene.narration, scene.duration)
                
                audio_scene = AudioScene(
                    scene_id=scene.id,
                    file_path=str(audio_path),
                    duration=scene.duration,
                    transcript=scene.narration,
                    timing_markers=timing_markers
                )
                
                print(f"  Created silent fallback audio for scene {scene.id}")
                return audio_scene
            
            return None
            
        except Exception as e:
            print(f"Failed to create fallback audio for scene {scene.id}: {e}")
            return None
    
    async def _create_silent_audio(self, output_path: str, duration: float) -> None:
        """Create a silent audio file with specified duration."""
        try:
            # Try using ffmpeg first
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=r={self.sample_rate}:cl=mono",
                "-t", str(duration), "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0:
                return
            
        except Exception:
            pass
        
        # Fallback: create simple WAV file with Python
        try:
            import wave
            import struct
            
            num_samples = int(self.sample_rate * duration)
            
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(self.channels)
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(self.sample_rate)
                
                # Write silent samples
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))
                    
        except Exception as e:
            print(f"Failed to create silent audio: {e}")
            # Create empty file as absolute fallback
            Path(output_path).touch()
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS processing."""
        import re
        
        # Remove markdown formatting
        text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)  # Links
        text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', text)  # Bold
        text = re.sub(r'\*([^\*]+)\*', r'\1', text)  # Italic
        text = re.sub(r'```[^`]*```', '', text)  # Code blocks
        text = re.sub(r'`([^`]+)`', r'\1', text)  # Inline code
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Escape quotes for shell commands
        text = text.replace('"', '\\"')
        text = text.replace("'", "\\'")
        
        # Limit length for TTS stability
        max_length = 1000
        if len(text) > max_length:
            # Find last sentence boundary within limit
            truncated = text[:max_length]
            last_period = truncated.rfind('.')
            if last_period > max_length * 0.8:
                text = truncated[:last_period + 1]
            else:
                text = truncated + "..."
        
        return text
    
    async def _get_audio_duration(self, audio_path: str) -> float:
        """Get audio file duration using ffprobe."""
        try:
            process = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                import json
                info = json.loads(stdout.decode())
                duration = float(info.get("format", {}).get("duration", 0))
                return duration
            
            return 0.0
            
        except Exception:
            return 0.0
    
    def _create_timing_markers(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """Create simple timing markers for text."""
        words = text.split()
        if not words:
            return []
        
        markers = []
        time_per_word = total_duration / len(words)
        
        current_time = 0.0
        for word in words:
            # Adjust timing based on word length and punctuation
            word_duration = time_per_word
            
            # Longer words get slightly more time
            if len(word) > 6:
                word_duration *= 1.2
            elif len(word) < 3:
                word_duration *= 0.8
            
            # Punctuation adds pause time
            if word.endswith(('.', '!', '?')):
                word_duration *= 1.3
            elif word.endswith((',', ';', ':')):
                word_duration *= 1.1
            
            markers.append({
                "word": word.strip('.,!?;:'),
                "start_time": current_time,
                "end_time": current_time + word_duration,
                "duration": word_duration
            })
            
            current_time += word_duration
        
        # Normalize to fit total duration
        if current_time > 0:
            scale_factor = total_duration / current_time
            for marker in markers:
                marker["start_time"] *= scale_factor
                marker["end_time"] *= scale_factor
                marker["duration"] *= scale_factor
        
        return markers
    
    def get_available_engines(self) -> List[str]:
        """Get list of available TTS engines."""
        return [engine for engine, available in self.tts_engines.items() if available]
    
    def validate_audio_file(self, file_path: str) -> Dict[str, Any]:
        """
        Validate an audio file for completeness and quality.
        
        Args:
            file_path: Path to the audio file to validate
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            audio_path = Path(file_path)
            
            # Check if file exists
            if not audio_path.exists():
                validation["errors"].append("Audio file does not exist")
                validation["valid"] = False
                return validation
            
            # Check file size
            file_size = audio_path.stat().st_size
            validation["stats"]["file_size_bytes"] = file_size
            
            if file_size == 0:
                validation["errors"].append("Audio file is empty")
                validation["valid"] = False
            elif file_size < 1000:  # Less than 1KB
                validation["warnings"].append("Audio file is very small")
            
            # Check if it's a valid audio file (basic check)
            if not file_path.lower().endswith(('.wav', '.mp3', '.aiff', '.flac')):
                validation["warnings"].append("Unusual audio file extension")
            
        except Exception as e:
            validation["errors"].append(f"Error validating audio file: {e}")
            validation["valid"] = False
        
        return validation
    async def _generate_scene_audio_simple(self, text: str, output_path: str, duration: float) -> bool:
        """Generate audio for a single scene with simple TTS."""
        try:
            # Clean the text
            cleaned_text = self._clean_text_for_tts(text)
            
            # Try available TTS engines in order of preference with timeout
            timeout_seconds = 30  # Add timeout to prevent hanging
            
            if self.tts_engines['pyttsx3']:
                try:
                    success = await asyncio.wait_for(
                        self._generate_pyttsx3_audio(cleaned_text, output_path),
                        timeout=timeout_seconds
                    )
                    if success:
                        return True
                except asyncio.TimeoutError:
                    print(f"pyttsx3 TTS timed out after {timeout_seconds}s")
                except Exception as e:
                    print(f"pyttsx3 TTS failed: {e}")
            
            if self.tts_engines['windows_sapi']:
                try:
                    success = await asyncio.wait_for(
                        self._generate_windows_sapi_audio(cleaned_text, output_path),
                        timeout=timeout_seconds
                    )
                    if success:
                        return True
                except asyncio.TimeoutError:
                    print(f"Windows SAPI TTS timed out after {timeout_seconds}s")
                except Exception as e:
                    print(f"Windows SAPI TTS failed: {e}")
            
            if self.tts_engines['macos_say']:
                try:
                    success = await asyncio.wait_for(
                        self._generate_macos_say_audio(cleaned_text, output_path),
                        timeout=timeout_seconds
                    )
                    if success:
                        return True
                except asyncio.TimeoutError:
                    print(f"macOS say TTS timed out after {timeout_seconds}s")
                except Exception as e:
                    print(f"macOS say TTS failed: {e}")
            
            if self.tts_engines['linux_espeak']:
                try:
                    success = await asyncio.wait_for(
                        self._generate_linux_espeak_audio(cleaned_text, output_path),
                        timeout=timeout_seconds
                    )
                    if success:
                        return True
                except asyncio.TimeoutError:
                    print(f"Linux espeak TTS timed out after {timeout_seconds}s")
                except Exception as e:
                    print(f"Linux espeak TTS failed: {e}")
            
            # If all TTS engines fail, create silent audio
            print("All TTS engines failed, creating silent audio as fallback")
            return await self._create_silent_audio(output_path, duration)
            
        except Exception as e:
            print(f"Simple audio generation failed: {e}")
            # Create silent audio as fallback
            return await self._create_silent_audio(output_path, duration)
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for TTS processing."""
        # Remove excessive whitespace
        text = ' '.join(text.split())
        
        # Limit length for TTS processing
        if len(text) > 500:
            text = text[:497] + "..."
        
        return text
    
    async def _resample_audio(self, input_path: str, output_path: str, target_sample_rate: int) -> bool:
        """Resample audio to target sample rate using FFmpeg."""
        try:
            cmd = [
                "ffmpeg", "-y",
                "-i", input_path,
                "-ar", str(target_sample_rate),
                "-ac", str(self.channels),
                "-c:a", "pcm_s16le",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                if file_size > 0:
                    print(f"    ✅ Resampled audio to {target_sample_rate}Hz: {file_size} bytes")
                    return True
            
            error_msg = stderr.decode() if stderr else "Unknown error"
            print(f"    ❌ Audio resampling failed: {error_msg}")
            return False
            
        except Exception as e:
            print(f"    Audio resampling error: {e}")
            return False
    
    async def _create_silent_audio(self, output_path: str, duration: float) -> bool:
        """Create silent audio file with specified duration."""
        try:
            # Use FFmpeg to create silent audio
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"anullsrc=channel_layout=mono:sample_rate={self.sample_rate}",
                "-t", str(duration),
                "-c:a", "pcm_s16le",
                output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            return process.returncode == 0 and Path(output_path).exists()
            
        except Exception as e:
            print(f"Failed to create silent audio: {e}")
            return False