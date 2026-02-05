"""
Audio Agent for the RASO platform.

Handles TTS generation, audio synchronization, and audio processing
for video narration using the TTS service.
"""

import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from agents.base import BaseAgent
from config.backend.models import AgentType
from config.backend.models.state import RASOMasterState
from config.backend.models.script import NarrationScript, Scene, TimingMarker
from config.backend.models.animation import AnimationAssets, RenderedScene
from config.backend.models.audio import AudioAssets, AudioScene
from agents.retry import retry
from scripts.utils.ai_model_manager import ai_model_manager


class AudioAgent(BaseAgent):
    """Agent responsible for enhanced audio generation using multiple TTS options."""
    
    name = "AudioAgent"
    description = "Generates high-quality TTS narration with multiple voice options and audio enhancement"
    
    def __init__(self, agent_type: AgentType):
        """Initialize enhanced audio agent with multiple TTS options."""
        super().__init__(agent_type)
        
        # TTS configuration and available engines
        self.tts_engines = {
            'coqui': {'available': False, 'engine': None, 'quality': 'high'},
            'bark': {'available': False, 'engine': None, 'quality': 'high'},
            'piper': {'available': False, 'engine': None, 'quality': 'fast'},
            'system': {'available': False, 'engine': None, 'quality': 'basic'},
        }
        
        # Audio processing configuration
        self.audio_config = {
            'sample_rate': 44100,
            'channels': 1,  # Mono for narration
            'bit_depth': 16,
            'voice_speed': 1.0,
            'voice_pitch': 1.0,
            'enable_enhancement': True,
            'enable_normalization': True,
        }
        
        self.preferred_tts = 'coqui'  # Default to highest quality
        self.tts_initialized = False
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute audio generation using simple, reliable approach.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with audio assets
        """
        self.validate_input(state)
        
        try:
            script = state.script
            
            self.log_progress("Starting simple audio generation", state)
            self.logger.info(f"Script has {len(script.scenes)} scenes")
            
            # Use simple audio generator as primary method
            from agents.simple_audio_generator import SimpleAudioGenerator
            simple_generator = SimpleAudioGenerator()
            
            self.logger.info("Generating audio using simple, reliable method")
            self.logger.info(f"Available TTS engines: {simple_generator.get_available_engines()}")
            
            # Generate audio assets
            audio_assets = await simple_generator.generate_audio_assets(
                script=script,
                output_dir=self.config.temp_path
            )
            
            # Validate generated audio
            validation_results = []
            for scene in audio_assets.scenes:
                validation = simple_generator.validate_audio_file(scene.file_path)
                validation_results.append(validation)
                
                if not validation["valid"]:
                    self.logger.warning(f"Audio validation failed for scene {scene.scene_id}: {validation['errors']}")
                elif validation["warnings"]:
                    self.logger.info(f"Audio validation warnings for scene {scene.scene_id}: {validation['warnings']}")
            
            # Update state
            state.audio = audio_assets
            state.current_agent = AgentType.VIDEO_COMPOSING
            
            self.logger.info(f"Audio generation completed: {len(audio_assets.scenes)} scenes, {audio_assets.total_duration:.1f}s total")
            self.log_progress(f"Completed audio generation for {len(audio_assets.scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Simple audio generation failed: {e}")
            # Fallback to creating silent audio
            return await self._generate_fallback_audio(state)
    
    async def _initialize_enhanced_tts_services(self) -> None:
        """Initialize multiple TTS services for high-quality audio generation."""
        if self.tts_initialized:
            return
            
        try:
            self.logger.info("Initializing enhanced TTS services...")
            
            # Try to initialize Coqui TTS (highest quality)
            await self._initialize_coqui_tts()
            
            # Try to initialize Bark TTS (emotional and expressive)
            await self._initialize_bark_tts()
            
            # Try to initialize Piper TTS (fast and lightweight)
            await self._initialize_piper_tts()
            
            # Always have system TTS as fallback
            await self._initialize_system_tts()
            
            # Select best available TTS engine
            self._select_optimal_tts_engine()
            
            self.tts_initialized = True
            
            # Log available engines
            available_engines = [name for name, config in self.tts_engines.items() if config['available']]
            self.logger.info(f"Available TTS engines: {available_engines}")
            self.logger.info(f"Selected TTS engine: {self.preferred_tts}")
            
        except Exception as e:
            self.logger.error(f"Enhanced TTS initialization failed: {e}")
            self.tts_initialized = False
    
    async def _initialize_coqui_tts(self) -> None:
        """Initialize Coqui TTS for high-quality neural speech synthesis."""
        try:
            from TTS.api import TTS
            
            # Use a lightweight but high-quality model
            model_name = "tts_models/en/ljspeech/tacotron2-DDC"
            
            self.tts_engines['coqui']['engine'] = TTS(model_name=model_name)
            self.tts_engines['coqui']['available'] = True
            
            self.logger.info("✅ Coqui TTS initialized successfully")
            
        except ImportError:
            self.logger.warning("Coqui TTS not available (pip install TTS)")
        except Exception as e:
            self.logger.warning(f"Coqui TTS initialization failed: {e}")
    
    async def _initialize_bark_tts(self) -> None:
        """Initialize Bark TTS for expressive speech generation."""
        try:
            # Bark is more resource-intensive, only initialize if we have enough memory
            system_info = ai_model_manager.get_system_recommendations()
            memory_gb = system_info.get('memory_gb', 16)
            
            if memory_gb < 12:
                self.logger.info("Skipping Bark TTS (requires 12GB+ RAM)")
                return
            
            # Try to import and initialize Bark
            import bark
            
            self.tts_engines['bark']['engine'] = bark
            self.tts_engines['bark']['available'] = True
            
            self.logger.info("✅ Bark TTS initialized successfully")
            
        except ImportError:
            self.logger.warning("Bark TTS not available (pip install bark)")
        except Exception as e:
            self.logger.warning(f"Bark TTS initialization failed: {e}")
    
    async def _initialize_piper_tts(self) -> None:
        """Initialize Piper TTS for fast, lightweight speech synthesis."""
        try:
            # Piper is a fast, lightweight TTS system
            # For now, we'll use it through system calls if available
            import subprocess
            import asyncio
            
            # Check if piper is available
            result = await asyncio.create_subprocess_exec(
                "piper", "--help",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await result.communicate()
            
            if result.returncode == 0:
                self.tts_engines['piper']['available'] = True
                self.logger.info("✅ Piper TTS detected and available")
            
        except Exception as e:
            self.logger.warning(f"Piper TTS not available: {e}")
    
    async def _initialize_system_tts(self) -> None:
        """Initialize system TTS as fallback."""
        try:
            # System TTS is always available as fallback
            self.tts_engines['system']['available'] = True
            self.logger.info("✅ System TTS available as fallback")
            
        except Exception as e:
            self.logger.warning(f"System TTS initialization failed: {e}")
    
    def _select_optimal_tts_engine(self) -> None:
        """Select the best available TTS engine based on quality and system resources."""
        # Priority order: coqui > bark > piper > system
        priority_order = ['coqui', 'bark', 'piper', 'system']
        
        for engine_name in priority_order:
            if self.tts_engines[engine_name]['available']:
                self.preferred_tts = engine_name
                break
        
        # For 16GB systems, prefer lighter engines if Coqui is not available
        system_info = ai_model_manager.get_system_recommendations()
        memory_gb = system_info.get('memory_gb', 16)
        
        if memory_gb <= 16 and self.preferred_tts == 'bark':
            # Bark might be too heavy for 16GB systems
            if self.tts_engines['piper']['available']:
                self.preferred_tts = 'piper'
            elif self.tts_engines['system']['available']:
                self.preferred_tts = 'system'
    
    async def _generate_enhanced_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """Generate enhanced audio for a single scene using the best available TTS."""
        try:
            # Create output directory
            audio_dir = Path(self.config.temp_path) / "audio" / scene.id
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            raw_audio_path = str(audio_dir / f"{scene.id}_raw.wav")
            enhanced_audio_path = str(audio_dir / f"{scene.id}_enhanced.wav")
            final_audio_path = str(audio_dir / f"{scene.id}.wav")
            
            # Generate TTS using selected engine
            success = await self._generate_tts_with_engine(
                text=scene.narration,
                output_path=raw_audio_path,
                engine=self.preferred_tts
            )
            
            if not success:
                self.logger.warning(f"Primary TTS failed for scene {scene.id}, trying fallback")
                success = await self._generate_tts_fallback(scene.narration, raw_audio_path)
            
            if not success:
                return None
            
            # Apply audio enhancement if enabled
            if self.audio_config['enable_enhancement']:
                await self._enhance_audio_quality(raw_audio_path, enhanced_audio_path)
                processing_path = enhanced_audio_path
            else:
                processing_path = raw_audio_path
            
            # Synchronize with target duration
            await self._synchronize_audio_duration(processing_path, final_audio_path, target_duration)
            
            # Verify final audio file
            if not Path(final_audio_path).exists():
                self.logger.error(f"Final audio file not created for scene {scene.id}")
                return None
            
            # Get actual duration and create timing markers
            actual_duration = await self._get_audio_duration(final_audio_path)
            if actual_duration == 0:
                actual_duration = target_duration
            
            timing_markers = self._create_enhanced_timing_markers(scene.narration, actual_duration)
            
            # Create enhanced audio scene
            audio_scene = AudioScene(
                scene_id=scene.id,
                file_path=final_audio_path,
                duration=actual_duration,
                transcript=scene.narration,
                timing_markers=timing_markers,
            )
            
            return audio_scene
            
        except Exception as e:
            self.logger.error(f"Error generating enhanced audio for scene {scene.id}: {str(e)}")
            return None
    
    async def _generate_tts_with_engine(self, text: str, output_path: str, engine: str) -> bool:
        """Generate TTS using specified engine."""
        try:
            if engine == 'coqui' and self.tts_engines['coqui']['available']:
                return await self._generate_coqui_tts(text, output_path)
            elif engine == 'bark' and self.tts_engines['bark']['available']:
                return await self._generate_bark_tts(text, output_path)
            elif engine == 'piper' and self.tts_engines['piper']['available']:
                return await self._generate_piper_tts(text, output_path)
            elif engine == 'system' and self.tts_engines['system']['available']:
                return await self._generate_system_tts(text, output_path)
            else:
                return False
                
        except Exception as e:
            self.logger.error(f"TTS generation failed with engine {engine}: {e}")
            return False
    
    async def _generate_coqui_tts(self, text: str, output_path: str) -> bool:
        """Generate TTS using Coqui TTS."""
        try:
            import asyncio
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Generate TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.tts_engines['coqui']['engine'].tts_to_file(
                    text=cleaned_text,
                    file_path=output_path,
                    speed=self.audio_config['voice_speed'],
                )
            )
            
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
            
        except Exception as e:
            self.logger.error(f"Coqui TTS generation failed: {e}")
            return False
    
    async def _generate_bark_tts(self, text: str, output_path: str) -> bool:
        """Generate TTS using Bark (expressive TTS)."""
        try:
            import asyncio
            from bark import generate_audio, SAMPLE_RATE
            from scipy.io.wavfile import write as write_wav
            
            # Clean and prepare text
            cleaned_text = self._clean_text_for_tts(text)
            
            # Generate audio in thread pool
            loop = asyncio.get_event_loop()
            audio_array = await loop.run_in_executor(
                None,
                lambda: generate_audio(cleaned_text, history_prompt="v2/en_speaker_6")
            )
            
            # Save audio file
            write_wav(output_path, SAMPLE_RATE, audio_array)
            
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
            
        except Exception as e:
            self.logger.error(f"Bark TTS generation failed: {e}")
            return False
    
    async def _generate_piper_tts(self, text: str, output_path: str) -> bool:
        """Generate TTS using Piper."""
        try:
            import subprocess
            import asyncio
            
            # Clean text
            cleaned_text = self._clean_text_for_tts(text)
            
            # Use piper command line
            process = await asyncio.create_subprocess_exec(
                "piper", "--model", "en_US-lessac-medium", "--output_file", output_path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate(input=cleaned_text.encode())
            
            return process.returncode == 0 and Path(output_path).exists()
            
        except Exception as e:
            self.logger.error(f"Piper TTS generation failed: {e}")
            return False
    
    async def _generate_system_tts(self, text: str, output_path: str) -> bool:
        """Generate TTS using system TTS (fallback)."""
        # This is the existing system TTS implementation
        return await self._try_pyttsx3_tts(text, output_path) or await self._try_system_tts(text, output_path)
    
    async def _generate_tts_fallback(self, text: str, output_path: str) -> bool:
        """Generate TTS using fallback methods."""
        # Try all available engines in order
        for engine_name, config in self.tts_engines.items():
            if config['available'] and engine_name != self.preferred_tts:
                if await self._generate_tts_with_engine(text, output_path, engine_name):
                    self.logger.info(f"Fallback TTS successful with {engine_name}")
                    return True
        
        # If all TTS fails, create silent audio
        await self._create_silent_audio(output_path, 30.0)  # Default 30 seconds
        return True
    
    async def _enhance_audio_quality(self, input_path: str, output_path: str) -> None:
        """Apply audio enhancement using FFmpeg filters."""
        try:
            import subprocess
            import asyncio
            
            # Apply audio enhancement filters
            enhancement_filters = [
                "highpass=f=80",           # Remove low-frequency noise
                "lowpass=f=8000",          # Remove high-frequency noise
                "compand=0.02,0.05:-60/-60,-30/-10,-20/-8,-5/-8,-2/-8:6:0:-90:0.1",  # Dynamic range compression
                "volume=0.8",              # Normalize volume
            ]
            
            filter_chain = ",".join(enhancement_filters)
            
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", input_path,
                "-af", filter_chain,
                "-ar", str(self.audio_config['sample_rate']),
                "-ac", str(self.audio_config['channels']),
                "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                # If enhancement fails, copy original
                import shutil
                shutil.copy2(input_path, output_path)
                
        except Exception as e:
            self.logger.warning(f"Audio enhancement failed: {e}")
            # Copy original file if enhancement fails
            import shutil
            shutil.copy2(input_path, output_path)
    
    async def _synchronize_audio_duration(self, input_path: str, output_path: str, target_duration: float) -> None:
        """Synchronize audio duration with target duration."""
        try:
            current_duration = await self._get_audio_duration(input_path)
            
            if abs(current_duration - target_duration) < 0.1:
                # Duration is close enough, just copy
                import shutil
                shutil.copy2(input_path, output_path)
                return
            
            if current_duration == 0:
                # Can't adjust, copy original
                import shutil
                shutil.copy2(input_path, output_path)
                return
            
            # Calculate speed adjustment
            speed_factor = current_duration / target_duration
            speed_factor = max(0.7, min(1.4, speed_factor))  # Reasonable limits for natural speech
            
            import subprocess
            import asyncio
            
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", input_path,
                "-filter:a", f"atempo={speed_factor}",
                "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode != 0:
                # If synchronization fails, copy original
                import shutil
                shutil.copy2(input_path, output_path)
                
        except Exception as e:
            self.logger.warning(f"Audio synchronization failed: {e}")
            # Copy original file if synchronization fails
            import shutil
            shutil.copy2(input_path, output_path)
    
    def _create_enhanced_timing_markers(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """Create enhanced timing markers with word-level precision."""
        words = text.split()
        if not words:
            return []
        
        markers = []
        
        # Simple word-level timing (could be enhanced with forced alignment)
        time_per_word = total_duration / len(words)
        
        current_time = 0.0
        for i, word in enumerate(words):
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
                "duration": word_duration,
                "confidence": 0.8  # Estimated confidence
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
    
    async def _apply_advanced_audio_processing(self, audio_scenes: List[AudioScene]) -> List[AudioScene]:
        """Apply advanced audio processing across all scenes."""
        try:
            if not self.audio_config['enable_normalization']:
                return audio_scenes
            
            self.logger.info("Applying advanced audio processing...")
            
            # Create processed output directory
            processed_dir = Path(self.config.temp_path) / "audio" / "processed"
            processed_dir.mkdir(parents=True, exist_ok=True)
            
            updated_scenes = []
            
            for i, scene in enumerate(audio_scenes):
                if not Path(scene.file_path).exists():
                    updated_scenes.append(scene)
                    continue
                
                processed_path = str(processed_dir / f"processed_{scene.scene_id}.wav")
                
                # Apply advanced processing pipeline
                success = await self._apply_audio_processing_pipeline(
                    scene.file_path, processed_path
                )
                
                if success:
                    # Update scene with processed audio
                    updated_scene = AudioScene(
                        scene_id=scene.scene_id,
                        file_path=processed_path,
                        duration=scene.duration,
                        transcript=scene.transcript,
                        timing_markers=scene.timing_markers,
                    )
                    updated_scenes.append(updated_scene)
                    self.logger.info(f"Applied advanced processing to scene {scene.scene_id}")
                else:
                    # Keep original if processing failed
                    updated_scenes.append(scene)
                    self.logger.warning(f"Advanced processing failed for scene {scene.scene_id}")
            
            return updated_scenes
            
        except Exception as e:
            self.logger.warning(f"Advanced audio processing error: {str(e)}")
            return audio_scenes
    
    async def _apply_audio_processing_pipeline(self, input_path: str, output_path: str) -> bool:
        """Apply comprehensive audio processing pipeline."""
        try:
            import subprocess
            import asyncio
            
            # Advanced audio processing pipeline
            processing_filters = [
                "highpass=f=85",                    # Remove low-frequency rumble
                "lowpass=f=7500",                   # Remove high-frequency noise
                "afftdn=nf=-20",                    # Noise reduction
                "compand=0.02,0.05:-60/-60,-30/-15,-20/-10,-5/-8,-2/-8:6:0:-90:0.1",  # Multi-band compression
                "loudnorm=I=-16:TP=-1.5:LRA=11",    # Loudness normalization for broadcast
                "aresample=44100",                  # Ensure consistent sample rate
            ]
            
            filter_chain = ",".join(processing_filters)
            
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", input_path,
                "-af", filter_chain,
                "-ar", str(self.audio_config['sample_rate']),
                "-ac", str(self.audio_config['channels']),
                "-c:a", "pcm_s16le",  # Uncompressed for quality
                "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return process.returncode == 0 and Path(output_path).exists()
            
        except Exception as e:
            self.logger.error(f"Audio processing pipeline failed: {e}")
            return False
        """Validate input state for audio generation."""
        if not state.script:
            raise ValueError("Narration script not found in state")
        
        if not state.animations:
            raise ValueError("Animation assets not found in state")
    
    def _find_rendered_scene(self, scene_id: str, rendered_scenes: List[RenderedScene]) -> Optional[RenderedScene]:
        """Find rendered scene by ID."""
        for rendered_scene in rendered_scenes:
            if rendered_scene.scene_id == scene_id:
                return rendered_scene
        return None
    
    async def _generate_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """Generate audio for a single scene."""
        try:
            # Create output path
            audio_dir = Path(self.config.temp_path) / "audio" / scene.id
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            raw_audio_path = str(audio_dir / f"{scene.id}_raw.wav")
            final_audio_path = str(audio_dir / f"{scene.id}.wav")
            
            # Generate TTS
            tts_result = await tts_service.generate_speech(
                text=scene.narration,
                output_path=raw_audio_path,
                voice_speed=self.config.audio.voice_speed,
                voice_pitch=self.config.audio.voice_pitch,
            )
            
            if not tts_result.success:
                self.logger.error(f"TTS generation failed for scene {scene.id}: {tts_result.error_message}")
                return None
            
            # Synchronize with target duration
            sync_result = await audio_synchronizer.synchronize_scene_audio(
                audio_path=raw_audio_path,
                target_duration=target_duration,
                output_path=final_audio_path,
            )
            
            if not sync_result.success:
                self.logger.error(f"Audio synchronization failed for scene {scene.id}: {sync_result.error_message}")
                return None
            
            # Create timing markers (simple word-level timing)
            timing_markers = self._create_timing_markers(scene.narration, sync_result.duration)
            
            # Create audio scene
            audio_scene = AudioScene(
                scene_id=scene.id,
                file_path=final_audio_path,
                duration=sync_result.duration,
                transcript=scene.narration,
                timing_markers=timing_markers,
            )
            
            return audio_scene
            
        except Exception as e:
            self.logger.error(f"Error generating audio for scene {scene.id}: {str(e)}")
            return None
    
    def _create_timing_markers(self, text: str, total_duration: float) -> List[Dict[str, Any]]:
        """Create simple timing markers for text."""
        words = text.split()
        if not words:
            return []
        
        markers = []
        time_per_word = total_duration / len(words)
        
        current_time = 0.0
        for i, word in enumerate(words):
            markers.append({
                "word": word,
                "start_time": current_time,
                "end_time": current_time + time_per_word,
                "duration": time_per_word
            })
            current_time += time_per_word
        
        return markers
    
    async def _initialize_tts_service(self) -> None:
        """Initialize TTS service for production use."""
        try:
            # Try to import and initialize TTS
            try:
                from TTS.api import TTS
                self._tts_model = TTS(model_name=self.config.audio.tts_model)
                self.logger.info("TTS model loaded successfully")
                self._tts_available = True
            except ImportError:
                self.logger.warning("TTS library not available, using fallback text-to-speech")
                self._tts_available = False
            except Exception as e:
                self.logger.warning(f"Failed to load TTS model: {e}, using fallback")
                self._tts_available = False
                
        except Exception as e:
            self.logger.error(f"TTS initialization failed: {e}")
            self._tts_available = False
    
    async def _generate_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """Generate audio for a single scene using production TTS."""
        try:
            # Create output directory
            audio_dir = Path(self.config.temp_path) / "audio" / scene.id
            audio_dir.mkdir(parents=True, exist_ok=True)
            
            audio_path = str(audio_dir / f"{scene.id}.wav")
            
            if self._tts_available and hasattr(self, '_tts_model'):
                # Use real TTS
                await self._generate_tts_audio(scene.narration, audio_path, target_duration)
            else:
                # Use fallback method (system TTS or simple audio generation)
                await self._generate_fallback_audio(scene.narration, audio_path, target_duration)
            
            # Verify audio file was created
            if not Path(audio_path).exists():
                self.logger.error(f"Audio file not created for scene {scene.id}")
                return None
            
            # Get actual duration
            actual_duration = await self._get_audio_duration(audio_path)
            if actual_duration == 0:
                actual_duration = target_duration  # Fallback
            
            # Create timing markers
            timing_markers = self._create_timing_markers(scene.narration, actual_duration)
            
            # Create audio scene
            audio_scene = AudioScene(
                scene_id=scene.id,
                file_path=audio_path,
                duration=actual_duration,
                transcript=scene.narration,
                timing_markers=timing_markers,
            )
            
            return audio_scene
            
        except Exception as e:
            self.logger.error(f"Error generating audio for scene {scene.id}: {str(e)}")
            return None
    
    async def _generate_tts_audio(self, text: str, output_path: str, target_duration: float) -> None:
        """Generate audio using Coqui TTS."""
        try:
            import asyncio
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Generate TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._tts_model.tts_to_file(
                    text=cleaned_text,
                    file_path=output_path,
                    speed=self.config.audio.voice_speed,
                )
            )
            
            # Adjust duration if needed
            await self._adjust_audio_duration(output_path, target_duration)
            
        except Exception as e:
            self.logger.error(f"TTS generation failed: {e}")
            raise
    
    async def _generate_fallback_audio(self, text: str, output_path: str, target_duration: float) -> None:
        """Generate fallback audio using system TTS or simple methods."""
        try:
            # Try pyttsx3 first (which we confirmed is working)
            if await self._try_pyttsx3_tts(text, output_path):
                await self._adjust_audio_duration(output_path, target_duration)
                return
            
            # Try system TTS (Windows SAPI, macOS say, Linux espeak)
            if await self._try_system_tts(text, output_path):
                await self._adjust_audio_duration(output_path, target_duration)
                return
            
            # If system TTS fails, create a simple audio file with silence
            # This ensures the pipeline continues working
            await self._create_silent_audio(output_path, target_duration)
            
        except Exception as e:
            self.logger.error(f"Fallback audio generation failed: {e}")
            # Create silent audio as last resort
            await self._create_silent_audio(output_path, target_duration)
    
    async def _try_pyttsx3_tts(self, text: str, output_path: str) -> bool:
        """Try to use pyttsx3 for TTS."""
        try:
            import pyttsx3
            import asyncio
            
            def generate_tts():
                engine = pyttsx3.init()
                engine.setProperty('rate', 150)  # Speed
                engine.setProperty('volume', 0.9)  # Volume
                
                # Save to file
                engine.save_to_file(text, output_path)
                engine.runAndWait()
                engine.stop()
            
            # Run TTS in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(None, generate_tts)
            
            # Check if file was created
            return Path(output_path).exists() and Path(output_path).stat().st_size > 0
            
        except Exception as e:
            self.logger.warning(f"pyttsx3 TTS failed: {e}")
            return False
    
    async def _try_system_tts(self, text: str, output_path: str) -> bool:
        """Try to use system TTS."""
        try:
            import platform
            import subprocess
            import asyncio
            
            system = platform.system().lower()
            
            if system == "windows":
                # Use Windows SAPI
                powershell_cmd = f'''
                Add-Type -AssemblyName System.Speech
                $synth = New-Object System.Speech.Synthesis.SpeechSynthesizer
                $synth.SetOutputToWaveFile("{output_path}")
                $synth.Speak("{text}")
                $synth.Dispose()
                '''
                
                process = await asyncio.create_subprocess_exec(
                    "powershell", "-Command", powershell_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
                
            elif system == "darwin":
                # Use macOS say command
                temp_aiff = output_path.replace('.wav', '.aiff')
                process = await asyncio.create_subprocess_exec(
                    "say", "-o", temp_aiff, text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                
                if process.returncode == 0:
                    # Convert AIFF to WAV
                    convert_process = await asyncio.create_subprocess_exec(
                        "ffmpeg", "-i", temp_aiff, "-y", output_path,
                        stdout=asyncio.subprocess.PIPE,
                        stderr=asyncio.subprocess.PIPE
                    )
                    await convert_process.communicate()
                    
                    # Clean up temp file
                    if Path(temp_aiff).exists():
                        Path(temp_aiff).unlink()
                    
                    return convert_process.returncode == 0
                
            elif system == "linux":
                # Use espeak if available
                process = await asyncio.create_subprocess_exec(
                    "espeak", "-w", output_path, text,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                await process.communicate()
                return process.returncode == 0
            
            return False
            
        except Exception as e:
            self.logger.warning(f"System TTS failed: {e}")
            return False
    
    async def _create_silent_audio(self, output_path: str, duration: float) -> None:
        """Create a silent audio file as fallback."""
        try:
            import subprocess
            import asyncio
            
            # Use ffmpeg to create silent audio
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-f", "lavfi", "-i", f"anullsrc=r={self.config.audio.sample_rate}:cl=mono",
                "-t", str(duration), "-y", output_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await process.communicate()
            
            if process.returncode != 0:
                # If ffmpeg fails, create a simple WAV file with Python
                await self._create_simple_wav(output_path, duration)
                
        except Exception as e:
            self.logger.warning(f"Silent audio creation failed: {e}")
            # Create a minimal WAV file
            await self._create_simple_wav(output_path, duration)
    
    async def _create_simple_wav(self, output_path: str, duration: float) -> None:
        """Create a simple WAV file with silence using Python."""
        try:
            import wave
            import struct
            
            sample_rate = self.config.audio.sample_rate
            num_samples = int(sample_rate * duration)
            
            with wave.open(output_path, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Write silent samples
                for _ in range(num_samples):
                    wav_file.writeframes(struct.pack('<h', 0))
                    
        except Exception as e:
            self.logger.error(f"Simple WAV creation failed: {e}")
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
        """Get audio file duration."""
        try:
            import subprocess
            import asyncio
            import json
            
            # Use ffprobe to get duration
            process = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", audio_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, _ = await process.communicate()
            
            if process.returncode == 0:
                info = json.loads(stdout.decode())
                duration = float(info.get("format", {}).get("duration", 0))
                return duration
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to get audio duration: {e}")
            return 0.0
    
    async def _adjust_audio_duration(self, audio_path: str, target_duration: float) -> None:
        """Adjust audio duration to match target."""
        try:
            current_duration = await self._get_audio_duration(audio_path)
            
            if abs(current_duration - target_duration) < 0.1:
                return  # Close enough
            
            if current_duration == 0:
                return  # Can't adjust
            
            # Calculate speed adjustment
            speed_factor = current_duration / target_duration
            speed_factor = max(0.5, min(2.0, speed_factor))  # Reasonable limits
            
            # Create temporary file
            temp_path = audio_path + ".temp.wav"
            
            # Use ffmpeg to adjust speed
            import subprocess
            import asyncio
            
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", audio_path,
                "-filter:a", f"atempo={speed_factor}",
                "-y", temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
            
            if process.returncode == 0 and Path(temp_path).exists():
                # Replace original with adjusted
                Path(temp_path).replace(audio_path)
            else:
                # Clean up temp file if it exists
                if Path(temp_path).exists():
                    Path(temp_path).unlink()
                    
        except Exception as e:
            self.logger.warning(f"Audio duration adjustment failed: {e}")
    
    def _create_fallback_audio(self, scene: Scene, target_duration: float) -> AudioScene:
        """Create fallback audio scene when TTS fails."""
        # Use proper temp path instead of /tmp/ for Windows compatibility
        fallback_dir = Path(self.config.temp_path) / "audio" / "fallback"
        fallback_dir.mkdir(parents=True, exist_ok=True)
        fallback_path = fallback_dir / f"fallback_audio_{scene.id}.wav"
        
        return AudioScene(
            scene_id=scene.id,
            file_path=str(fallback_path),
            duration=target_duration,
            transcript=scene.narration,
            timing_markers=self._create_timing_markers(scene.narration, target_duration),
        )
    
    async def _normalize_audio_levels(self, audio_scenes: List[AudioScene]) -> List[AudioScene]:
        """Normalize audio levels across scenes."""
        try:
            # Create normalized output directory
            normalized_dir = Path(self.config.temp_path) / "audio" / "normalized"
            normalized_dir.mkdir(parents=True, exist_ok=True)
            
            updated_scenes = []
            
            for i, scene in enumerate(audio_scenes):
                if not Path(scene.file_path).exists():
                    # Keep original if file doesn't exist
                    updated_scenes.append(scene)
                    continue
                
                normalized_path = str(normalized_dir / f"normalized_{scene.scene_id}.wav")
                
                # Use ffmpeg loudnorm filter
                import subprocess
                import asyncio
                
                process = await asyncio.create_subprocess_exec(
                    "ffmpeg", "-i", scene.file_path,
                    "-af", "loudnorm=I=-16:TP=-1.5:LRA=11",
                    "-ar", str(self.config.audio.sample_rate),
                    "-y", normalized_path,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                if process.returncode == 0 and Path(normalized_path).exists():
                    # Update scene with normalized path
                    updated_scene = AudioScene(
                        scene_id=scene.scene_id,
                        file_path=normalized_path,
                        duration=scene.duration,
                        transcript=scene.transcript,
                        timing_markers=scene.timing_markers,
                    )
                    updated_scenes.append(updated_scene)
                else:
                    # Keep original if normalization failed
                    self.logger.warning(f"Audio normalization failed for scene {scene.scene_id}")
                    updated_scenes.append(scene)
            
            return updated_scenes
            
        except Exception as e:
            self.logger.warning(f"Audio normalization error: {str(e)}")
            return audio_scenes  # Return original scenes if normalization fails
    
    async def generate_scene_audio(self, scene: Scene, target_duration: float) -> Optional[AudioScene]:
        """
        Public method to generate audio for a single scene.
        
        Args:
            scene: Scene to generate audio for
            target_duration: Target audio duration
            
        Returns:
            Audio scene if successful
        """
        return await self._generate_scene_audio(scene, target_duration)
    
    async def estimate_audio_duration(self, text: str) -> float:
        """
        Estimate audio duration for text.
        
        Args:
            text: Text to estimate
            
        Returns:
            Estimated duration in seconds
        """
        # Simple estimation: ~150 words per minute, ~5 characters per word
        words = len(text.split())
        estimated_duration = (words / 150) * 60  # Convert to seconds
        return max(1.0, estimated_duration)  # Minimum 1 second
        self.preferred_tts = 'coqui'  # Default to highest quality
        self.tts_initialized = False
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute audio generation using simple, reliable approach.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with audio assets
        """
        self.validate_input(state)
        
        try:
            script = state.script
            
            self.log_progress("Starting simple audio generation", state)
            self.logger.info(f"Script has {len(script.scenes)} scenes")
            
            # Use simple audio generator as primary method
            from agents.simple_audio_generator import SimpleAudioGenerator
            simple_generator = SimpleAudioGenerator()
            
            self.logger.info("Generating audio using simple, reliable method")
            self.logger.info(f"Available TTS engines: {simple_generator.get_available_engines()}")
            
            # Generate audio assets
            audio_assets = await simple_generator.generate_audio_assets(
                script=script,
                output_dir=self.config.temp_path
            )
            
            # Validate generated audio
            validation_results = []
            for scene in audio_assets.scenes:
                validation = simple_generator.validate_audio_file(scene.file_path)
                validation_results.append(validation)
                
                if not validation["valid"]:
                    self.logger.warning(f"Audio validation failed for scene {scene.scene_id}: {validation['errors']}")
                elif validation["warnings"]:
                    self.logger.info(f"Audio validation warnings for scene {scene.scene_id}: {validation['warnings']}")
            
            # Update state
            state.audio = audio_assets
            state.current_agent = AgentType.VIDEO_COMPOSING
            
            self.logger.info(f"Audio generation completed: {len(audio_assets.scenes)} scenes, {audio_assets.total_duration:.1f}s total")
            self.log_progress(f"Completed audio generation for {len(audio_assets.scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            self.logger.error(f"Simple audio generation failed: {e}")
            # Fallback to creating silent audio
            return await self._generate_fallback_audio(state)
    
    async def _generate_fallback_audio(self, state: RASOMasterState) -> RASOMasterState:
        """Generate fallback audio when simple generation fails."""
        try:
            script = state.script
            
            self.logger.info("Generating fallback silent audio")
            
            # Create silent audio scenes
            audio_scenes = []
            
            for scene in script.scenes:
                # Create fallback audio scene with silent audio
                audio_scene = AudioScene(
                    scene_id=scene.id,
                    file_path=f"temp/audio/fallback_{scene.id}.wav",
                    duration=scene.duration,
                    transcript=scene.narration,
                    timing_markers=[]
                )
                audio_scenes.append(audio_scene)
            
            # Create audio assets
            total_duration = sum(scene.duration for scene in audio_scenes)
            
            audio_assets = AudioAssets(
                scenes=audio_scenes,
                total_duration=total_duration,
                sample_rate=44100
            )
            
            state.audio = audio_assets
            state.current_agent = AgentType.VIDEO_COMPOSING
            
            self.logger.warning("Using fallback silent audio - TTS generation failed")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Fallback audio generation failed: {e}")
            raise
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state for audio generation."""
        if not state.script:
            raise ValueError("Narration script not found in state")
        
        # Note: animations are not required for audio generation in simple mode
        # if not state.animations:
        #     raise ValueError("Animation assets not found in state")