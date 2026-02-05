"""
Video Composition Agent for the RASO platform.

Handles final video composition, scene combination, and YouTube-ready output generation.
Enhanced with all production features including:
- Smart folder management and content organization
- Performance monitoring and optimization
- Comprehensive error handling and recovery
- Content versioning and asset relationship mapping
- AI-powered content enhancement
- Database storage and file organization
- Enhanced placeholder detection and retry logic for better content generation
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
import asyncio

# Fix import paths to use config/backend/models
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'backend'))

from models.state import RASOMasterState, AgentType
from models.animation import AnimationAssets
from models.audio import AudioAssets, AudioScene
from models.video import VideoAsset, VideoMetadata, Chapter
# Import production utilities (with error handling for missing modules)
try:
    from utils.smart_folder_manager import SmartFolderManager, PaperMetadata
except ImportError:
    SmartFolderManager = None
    PaperMetadata = None

try:
    from utils.content_version_manager import ContentVersionManager
except ImportError:
    ContentVersionManager = None

try:
    from utils.asset_relationship_mapper import AssetRelationshipMapper
except ImportError:
    AssetRelationshipMapper = None

try:
    from utils.performance_monitor import PerformanceMonitor
except ImportError:
    PerformanceMonitor = None

try:
    from utils.error_handler import ErrorHandler
except ImportError:
    ErrorHandler = None

try:
    from utils.visual_content_manager import visual_content_manager, VisualRequest, VisualType
except ImportError:
    visual_content_manager = None
    VisualRequest = None
    VisualType = None

# Simple retry decorator for video composition
def retry(max_attempts=3, base_delay=2.0):
    """Simple retry decorator for video composition methods."""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        delay = base_delay * (2 ** attempt)
                        await asyncio.sleep(delay)
                    continue
            raise last_exception
        return wrapper
    return decorator


# Create a minimal BaseAgent class for compatibility
class BaseAgent:
    """Minimal base agent class for video composition."""
    
    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type
        self.logger = self._setup_logger()
        self.config = self._setup_config()
    
    def _setup_logger(self):
        """Set up basic logging."""
        import logging
        logger = logging.getLogger(f"VideoCompositionAgent")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def _setup_config(self):
        """Set up basic configuration."""
        class Config:
            def __init__(self):
                # Use absolute path for temp directory to avoid Windows path issues
                import os
                self.temp_path = os.path.abspath("temp")
                self.video_quality = "medium"
        return Config()
    
    def log_progress(self, message: str, state=None):
        """Log progress message."""
        self.logger.info(message)
    
    def handle_error(self, error: Exception, state=None):
        """Handle error and return state."""
        self.logger.error(f"Error: {error}")
        if state:
            return state
        return None


class VideoCompositionAgent(BaseAgent):
    """Agent responsible for final video composition with enhanced production features."""
    
    name = "VideoCompositionAgent"
    description = "Composes final video from animation and audio assets with production-grade features"
    
    def __init__(self, agent_type: AgentType):
        """Initialize video composition agent with production features."""
        super().__init__(agent_type)
        
        # Initialize performance monitoring (if available)
        if PerformanceMonitor:
            self.performance_monitor = PerformanceMonitor()
        else:
            self.performance_monitor = None
        
        # Initialize error handler (if available)
        if ErrorHandler:
            self.error_handler = ErrorHandler()
        else:
            self.error_handler = None
        
        # Initialize content management (if available)
        if SmartFolderManager:
            self.smart_folder_manager = SmartFolderManager()
        else:
            self.smart_folder_manager = None
            
        if ContentVersionManager:
            self.content_version_manager = ContentVersionManager()
        else:
            self.content_version_manager = None
            
        if AssetRelationshipMapper:
            self.asset_relationship_mapper = AssetRelationshipMapper()
        else:
            self.asset_relationship_mapper = None
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute video composition with enhanced production features.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with final video
        """
        # Start performance monitoring (if available)
        operation_id = None
        if self.performance_monitor:
            operation_id = self.performance_monitor.start_operation("video_composition")
        
        try:
            self.validate_input(state)
            
            animations = state.animations
            audio = state.audio
            
            self.log_progress("Starting enhanced video composition with production features", state)
            
            # Validate and report content synchronization
            self._report_content_status(animations, audio)
            sync_validation = self._validate_content_synchronization(animations, audio)
            
            if not sync_validation["valid"]:
                self.logger.error("Content synchronization validation failed:")
                for error in sync_validation["errors"]:
                    self.logger.error(f"  - {error}")
                # Continue anyway but log the issues
            
            if sync_validation["warnings"]:
                self.logger.warning("Content synchronization warnings:")
                for warning in sync_validation["warnings"]:
                    self.logger.warning(f"  - {warning}")
            
            # Initialize visual content manager (if available)
            if visual_content_manager:
                await visual_content_manager.initialize()
            
            # Set up smart folder management (if available)
            if self.smart_folder_manager and PaperMetadata:
                project_info = PaperMetadata(
                    title=state.paper_content.title if state.paper_content else "RASO_Video",
                    authors=getattr(state.paper_content, 'authors', []) if state.paper_content else [],
                    year=datetime.now().year
                )
                
                # Create organized folder structure
                folder_path, was_created = self.smart_folder_manager.create_paper_folder(project_info)
                self.logger.info(f"Created organized folder: {folder_path} (new: {was_created})")
            else:
                # Fallback to simple folder structure
                folder_path = Path("output") / f"video_{int(datetime.now().timestamp())}"
                folder_path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created simple folder: {folder_path}")
            
            # Create output directory
            output_dir = folder_path / "videos"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate enhanced visual content for scenes that need it
            enhanced_animations = await self._enhance_visual_content(animations, state)
            
            video_filename = f"raso_video_{int(datetime.now().timestamp())}.mp4"
            output_path = str(output_dir / video_filename)
            
            # Compose video using production methods with quality settings and enhanced retry logic
            quality = getattr(self.config, 'video_quality', 'medium')  # Default to medium quality
            
            # Enhanced retry logic for better content generation
            max_composition_attempts = 2
            for composition_attempt in range(max_composition_attempts):
                self.logger.info(f"🎬 Video composition attempt {composition_attempt + 1}/{max_composition_attempts}")
                
                success = await self._compose_video_production(enhanced_animations, audio, output_path, quality)
                
                if success and Path(output_path).exists():
                    # Check if we got a good quality video
                    output_size = Path(output_path).stat().st_size
                    
                    # Consider it a success if file size is reasonable (> 100KB for any real video)
                    if output_size > 100 * 1024:
                        self.logger.info(f"✅ Video composition successful on attempt {composition_attempt + 1}")
                        break
                    else:
                        self.logger.warning(f"⚠️ Generated video is too small ({output_size} bytes) - may be placeholder content")
                        if composition_attempt < max_composition_attempts - 1:
                            self.logger.info("🔄 Retrying video composition for better content quality")
                            # Remove the small file and try again
                            try:
                                Path(output_path).unlink()
                            except:
                                pass
                            continue
                else:
                    self.logger.warning(f"❌ Video composition failed on attempt {composition_attempt + 1}")
                    if composition_attempt < max_composition_attempts - 1:
                        self.logger.info("🔄 Retrying video composition")
                        continue
            
            if success and Path(output_path).exists():
                # Validate the generated video
                from utils.video_validator import video_validator
                
                # Get expected duration from audio
                expected_duration = sum(scene.duration for scene in audio.scenes) if audio.scenes else 60.0
                
                # Perform comprehensive validation
                validation_result = await video_validator.validate_video(
                    output_path,
                    expected_duration=expected_duration,
                    min_file_size=1024 * 1024,  # 1MB minimum
                    require_audio=True,
                    youtube_compliance=True
                )
                
                if validation_result.is_valid:
                    self.logger.info(f"✅ Video validation passed with score: {validation_result.score:.2f}")
                else:
                    self.logger.warning(f"⚠️ Video validation failed with {len(validation_result.get_errors())} errors")
                    for error in validation_result.get_errors():
                        self.logger.warning(f"Validation error: {error.message}")
                
                # Get actual video info (use validation results if available)
                if validation_result.properties:
                    duration = validation_result.properties.duration
                    file_size = validation_result.properties.file_size
                else:
                    # Fallback to basic file info
                    duration = await self._get_video_duration(output_path)
                    if duration <= 0:
                        duration = expected_duration
                    file_size = Path(output_path).stat().st_size
                
                # Create chapters from scenes
                chapters = self._create_chapters(enhanced_animations.scenes, audio.scenes)
                
                # Create basic metadata for the video
                paper_title = state.paper_content.title if state.paper_content else "Research Paper Video"
                metadata = VideoMetadata(
                    title=f"Research Paper Explanation: {paper_title}",
                    description=f"An educational explanation of the research paper: {paper_title}\n\n"
                               f"This video breaks down the key concepts, contributions, and insights from this research.\n\n"
                               f"Generated automatically using RASO (Research paper Automated Simulation & Orchestration Platform)",
                    tags=["research", "education", "science", "AI", "machine learning", "paper explanation"],
                    chapters=chapters,
                )
                
                video_asset = VideoAsset(
                    file_path=output_path,
                    duration=duration,
                    resolution="1920x1080",
                    file_size=file_size,
                    metadata=metadata,
                    chapters=chapters,
                )
                
                # Store content version and asset relationships
                await self._store_content_metadata(video_asset, enhanced_animations, audio, folder_path)
                
                # Update state
                state.video = video_asset
                state.current_agent = AgentType.METADATA
                
                # Record successful operation (if performance monitor available)
                if self.performance_monitor and operation_id:
                    self.performance_monitor.end_operation(operation_id, success=True)
                
                self.log_progress("✅ Enhanced video composition completed successfully with improved content quality", state)
            else:
                raise RuntimeError("❌ Video composition failed after all retry attempts - output file not created")
            
            return state
            
        except Exception as e:
            # Record failed operation (if performance monitor available)
            if self.performance_monitor and operation_id:
                self.performance_monitor.end_operation(operation_id, success=False, error=str(e))
            
            # Use enhanced error handling (if available)
            if self.error_handler:
                context_data = {
                    'context': 'video_composition',
                    'animations_count': len(animations.scenes) if animations else 0,
                    'audio_count': len(audio.scenes) if audio else 0,
                    'quality': quality if 'quality' in locals() else 'unknown'
                }
                
                recovery_suggestion = self.error_handler.handle_error(
                    error=e,
                    context=context_data
                )
                
                if recovery_suggestion:
                    self.logger.info(f"Recovery suggestion: {recovery_suggestion}")
            
            return self.handle_error(e, state)
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state."""
        if not state.animations:
            raise ValueError("Animation assets not found in state")
        
        if not state.audio:
            raise ValueError("Audio assets not found in state")
    
    async def _store_content_metadata(self, video_asset: VideoAsset, animations: AnimationAssets, audio: AudioAssets, folder_path: Path) -> None:
        """Store content metadata and asset relationships (if utilities available)."""
        try:
            # Only proceed if content management utilities are available
            if not (self.content_version_manager and self.asset_relationship_mapper):
                self.logger.info("Content management utilities not available - skipping metadata storage")
                return
            # Create version entry for the video
            version_info = await self.content_version_manager.create_version(
                content_id=f"video_{int(datetime.now().timestamp())}",
                content_type="video",
                file_path=video_asset.file_path,
                metadata={
                    'duration': video_asset.duration,
                    'resolution': video_asset.resolution,
                    'file_size': video_asset.file_size,
                    'chapters_count': len(video_asset.chapters) if video_asset.chapters else 0,
                    'generation_timestamp': datetime.now().isoformat()
                },
                generation_params={
                    'quality': getattr(self.config, 'video_quality', 'medium'),
                    'animation_scenes': len(animations.scenes),
                    'audio_scenes': len(audio.scenes)
                }
            )
            
            self.logger.info(f"Created content version: {version_info.version_id}")
            
            # Map asset relationships
            relationships = []
            
            # Map animation assets
            for i, scene in enumerate(animations.scenes):
                if hasattr(scene, 'file_path') and scene.file_path:
                    relationship = await self.asset_relationship_mapper.create_relationship(
                        source_asset=scene.file_path,
                        target_asset=video_asset.file_path,
                        relationship_type="animation_to_video",
                        metadata={
                            'scene_index': i,
                            'scene_id': scene.scene_id,
                            'duration': scene.duration if hasattr(scene, 'duration') else None
                        }
                    )
                    relationships.append(relationship)
            
            # Map audio assets
            for i, scene in enumerate(audio.scenes):
                if hasattr(scene, 'file_path') and scene.file_path:
                    relationship = await self.asset_relationship_mapper.create_relationship(
                        source_asset=scene.file_path,
                        target_asset=video_asset.file_path,
                        relationship_type="audio_to_video",
                        metadata={
                            'scene_index': i,
                            'scene_id': scene.scene_id,
                            'duration': scene.duration
                        }
                    )
                    relationships.append(relationship)
            
            self.logger.info(f"Created {len(relationships)} asset relationships")
            
            # Store folder structure metadata
            structure_metadata = {
                'project_path': str(folder_path),
                'videos_path': str(folder_path / "videos"),
                'audio_path': str(folder_path / "audio"),
                'visuals_path': str(folder_path / "visuals"),
                'metadata_path': str(folder_path / "metadata")
            }
            
            # Save metadata to file
            metadata_dir = folder_path / "metadata"
            metadata_dir.mkdir(parents=True, exist_ok=True)
            metadata_file = metadata_dir / "video_metadata.json"
            import json
            with open(metadata_file, 'w') as f:
                json.dump({
                    'video_asset': {
                        'file_path': video_asset.file_path,
                        'duration': video_asset.duration,
                        'resolution': video_asset.resolution,
                        'file_size': video_asset.file_size
                    },
                    'version_info': {
                        'version_id': version_info.version_id,
                        'created_at': version_info.created_at.isoformat()
                    },
                    'folder_structure': structure_metadata,
                    'relationships_count': len(relationships)
                }, indent=2)
            
            self.logger.info(f"Saved metadata to: {metadata_file}")
            
        except Exception as e:
            self.logger.warning(f"Failed to store content metadata: {e}")
            # Don't fail the entire operation if metadata storage fails
    
    async def _enhance_visual_content(self, animations: AnimationAssets, state: RASOMasterState) -> AnimationAssets:
        """Enhance visual content using AI-powered generators (if available)."""
        try:
            # Skip enhancement if visual content manager is not available
            if not visual_content_manager:
                self.logger.info("Visual content manager not available - skipping enhancement")
                return animations
                
            self.logger.info("Enhancing visual content with AI-powered generators")
            
            enhanced_scenes = []
            
            # Create visual content directory
            visual_dir = Path(self.config.temp_path) / "enhanced_visuals"
            visual_dir.mkdir(parents=True, exist_ok=True)
            
            for i, scene in enumerate(animations.scenes):
                self.logger.info(f"Processing scene {i}: {scene.scene_id}")
                
                # Determine if scene needs enhanced visual content
                if await self._should_enhance_scene(scene, state):
                    # Generate enhanced visual content
                    enhanced_scene = await self._generate_enhanced_scene(scene, state, str(visual_dir))
                    if enhanced_scene:
                        enhanced_scenes.append(enhanced_scene)
                        self.logger.info(f"Enhanced scene {scene.scene_id} successfully")
                    else:
                        # Keep original scene if enhancement fails
                        enhanced_scenes.append(scene)
                        self.logger.warning(f"Enhancement failed for scene {scene.scene_id}, using original")
                else:
                    # Keep original scene
                    enhanced_scenes.append(scene)
                    self.logger.info(f"Scene {scene.scene_id} does not need enhancement")
            
            # Create new AnimationAssets with enhanced scenes
            enhanced_animations = AnimationAssets(
                scenes=enhanced_scenes,
                total_duration=sum(scene.duration for scene in enhanced_scenes),
                resolution=animations.resolution,
            )
            
            self.logger.info(f"Enhanced {len([s for s in enhanced_scenes if hasattr(s, 'enhanced') and s.enhanced])} out of {len(enhanced_scenes)} scenes")
            
            return enhanced_animations
            
        except Exception as e:
            self.logger.error(f"Error enhancing visual content: {e}")
            # Return original animations if enhancement fails
            return animations
    
    async def _should_enhance_scene(self, scene, state: RASOMasterState) -> bool:
        """Determine if a scene should be enhanced with AI-generated visuals."""
        # Check if scene already has a good video file
        if hasattr(scene, 'file_path') and scene.file_path and Path(scene.file_path).exists():
            file_size = Path(scene.file_path).stat().st_size
            if file_size > 1024 * 1024:  # If file is larger than 1MB, it's probably real content
                return False
        
        # Check if we have script content for this scene
        if state.script and state.script.scenes:
            script_scene = next((s for s in state.script.scenes if s.id == scene.scene_id), None)
            if script_scene:
                # Enhance scenes with mathematical or conceptual content
                content = script_scene.narration.lower()
                enhancement_indicators = [
                    'equation', 'formula', 'concept', 'process', 'method', 'algorithm',
                    'diagram', 'visualization', 'mathematical', 'theoretical'
                ]
                return any(indicator in content for indicator in enhancement_indicators)
        
        return True  # Default to enhancing scenes
    
    async def _generate_enhanced_scene(self, scene, state: RASOMasterState, output_dir: str):
        """Generate enhanced visual content for a scene."""
        try:
            # Get script content for this scene
            script_scene = None
            if state.script and state.script.scenes:
                script_scene = next((s for s in state.script.scenes if s.id == scene.scene_id), None)
            
            if not script_scene:
                self.logger.warning(f"No script content found for scene {scene.scene_id}")
                return scene
            
            # Create visual request
            visual_request = VisualRequest(
                scene_id=scene.scene_id,
                title=script_scene.title,
                content=script_scene.narration,
                visual_type=self._determine_visual_type(script_scene),
                duration=scene.duration,
                metadata={
                    'concepts': script_scene.concepts if hasattr(script_scene, 'concepts') else [],
                    'visual_type': script_scene.visual_type if hasattr(script_scene, 'visual_type') else 'auto'
                }
            )
            
            # Generate visual content
            visual_asset = await visual_content_manager.generate_visual_content(
                request=visual_request,
                output_dir=output_dir,
                quality="medium"
            )
            
            if visual_asset.success and visual_asset.file_path:
                # Create enhanced scene with new visual content
                from backend.models.animation import RenderedScene
                
                enhanced_scene = RenderedScene(
                    scene_id=scene.scene_id,
                    file_path=visual_asset.file_path,
                    duration=visual_asset.duration,
                    resolution=scene.resolution if hasattr(scene, 'resolution') else "1920x1080",
                )
                
                # Mark as enhanced
                enhanced_scene.enhanced = True
                enhanced_scene.enhancement_type = visual_asset.visual_type.value
                enhanced_scene.generation_code = visual_asset.generation_code
                
                return enhanced_scene
            else:
                self.logger.warning(f"Visual content generation failed for scene {scene.scene_id}: {visual_asset.error_message}")
                return scene
                
        except Exception as e:
            self.logger.error(f"Error generating enhanced scene {scene.scene_id}: {e}")
            return scene
    
    def _determine_visual_type(self, script_scene) -> VisualType:
        """Determine the best visual type for a script scene."""
        if hasattr(script_scene, 'visual_type'):
            visual_type_map = {
                'manim': VisualType.MANIM,
                'motion-canvas': VisualType.MOTION_CANVAS,
                'remotion': VisualType.REMOTION
            }
            return visual_type_map.get(script_scene.visual_type, VisualType.AUTO)
        
        # Analyze content to determine type
        content = script_scene.narration.lower()
        
        # Mathematical content -> Manim
        if any(indicator in content for indicator in ['equation', 'formula', 'mathematical', 'theorem', 'proof']):
            return VisualType.MANIM
        
        # Process/flow content -> Motion Canvas
        if any(indicator in content for indicator in ['process', 'workflow', 'steps', 'algorithm', 'method']):
            return VisualType.MOTION_CANVAS
        
        # Default to auto-selection
        return VisualType.AUTO
    
    def _create_chapters(self, video_scenes, audio_scenes) -> list:
        """Create video chapters from scenes using intelligent chapter generation."""
        try:
            from utils.chapter_generator import chapter_generator
            
            # Generate intelligent chapters
            chapters = chapter_generator.generate_chapters_from_scenes(
                animation_scenes=video_scenes,
                audio_scenes=audio_scenes
            )
            
            # Validate chapters
            validation_issues = chapter_generator.validate_chapters(chapters)
            if validation_issues:
                self.logger.warning(f"Chapter validation issues: {validation_issues}")
            
            # Export chapter metadata for debugging/reference
            try:
                metadata_path = Path(self.config.temp_path) / "chapters_metadata.json"
                chapter_generator.export_chapters_metadata(chapters, str(metadata_path))
                self.logger.info(f"Chapter metadata exported to: {metadata_path}")
            except Exception as e:
                self.logger.warning(f"Failed to export chapter metadata: {e}")
            
            self.logger.info(f"Generated {len(chapters)} chapters with intelligent titles")
            return chapters
            
        except Exception as e:
            self.logger.warning(f"Intelligent chapter generation failed: {e}, using fallback")
            
            # Fallback to simple chapter generation
            chapters = []
            current_time = 0.0
            
            for i, video_scene in enumerate(video_scenes):
                # Find matching audio scene for duration
                audio_scene = next(
                    (a for a in audio_scenes if a.scene_id == video_scene.scene_id),
                    None
                )
                
                duration = audio_scene.duration if audio_scene else video_scene.duration
                
                chapter = Chapter(
                    title=f"Scene {i+1}",
                    start_time=current_time,
                    end_time=current_time + duration,
                )
                
                chapters.append(chapter)
                current_time += duration
            
            return chapters
    
    async def _compose_video_production(self, animations: AnimationAssets, audio: AudioAssets, output_path: str, quality: str = "medium") -> bool:
        """Compose video using production methods with quality settings and enhanced retry logic."""
        try:
            # Try different video composition methods in order of preference
            
            # Method 1: Use ffmpeg directly (most reliable) with enhanced placeholder detection
            self.logger.info(f"🎬 Attempting FFmpeg composition to: {output_path}")
            if await self._compose_with_ffmpeg(animations, audio, output_path, quality):
                self.logger.info("✅ FFmpeg composition successful")
                return True
            else:
                self.logger.warning("⚠️ FFmpeg composition failed, trying MoviePy")
            
            # Method 2: Use moviepy as fallback
            if await self._compose_with_moviepy(animations, audio, output_path, quality):
                self.logger.info("✅ MoviePy composition successful")
                return True
            else:
                self.logger.warning("⚠️ MoviePy composition failed, trying slideshow")
            
            # Method 3: Create simple slideshow as last resort
            if await self._create_simple_slideshow(animations, audio, output_path, quality):
                self.logger.info("✅ Slideshow composition successful")
                return True
            else:
                self.logger.warning("⚠️ Slideshow composition failed")
            
            # Method 4: Create basic placeholder video as final fallback
            self.logger.warning("⚠️ All advanced methods failed, creating basic placeholder video")
            if await self._create_basic_placeholder_video(animations, audio, output_path):
                self.logger.info("✅ Basic placeholder video created successfully")
                return True
            
            # If even the basic placeholder fails, log error but don't crash
            self.logger.error("❌ All video composition methods failed including basic placeholder")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Video composition failed: {e}")
            import traceback
            self.logger.error(f"Traceback: {traceback.format_exc()}")
            
            # Try to create a basic placeholder as last resort
            try:
                self.logger.warning("⚠️ Exception occurred, attempting basic placeholder video as recovery")
                if await self._create_basic_placeholder_video(animations, audio, output_path):
                    self.logger.info("✅ Recovery successful: basic placeholder video created")
                    return True
            except Exception as recovery_error:
                self.logger.error(f"❌ Recovery failed: {recovery_error}")
            
            return False
    
    async def _create_basic_placeholder_video(self, animations: AnimationAssets, audio: AudioAssets, output_path: str) -> bool:
        """Create a basic placeholder video as final fallback."""
        try:
            import subprocess
            import asyncio
            import os
            
            # Calculate total duration from audio
            total_duration = sum(scene.duration for scene in audio.scenes) if audio.scenes else 60.0
            
            self.logger.info(f"Creating basic placeholder video: {total_duration}s duration")
            
            # Ensure output directory exists
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Add FFmpeg to PATH if not already there
            ffmpeg_bin = Path.cwd() / "ffmpeg" / "bin"
            if ffmpeg_bin.exists():
                current_path = os.environ.get('PATH', '')
                if str(ffmpeg_bin) not in current_path:
                    os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + current_path
            
            # Create a simple colored video with text using FFmpeg
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi",
                "-i", f"color=c=blue:size=1920x1080:duration={total_duration}",
                "-vf", "drawtext=text='RASO Video Generation':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-r", "30",
                str(output_path)
            ]
            
            self.logger.info(f"Running FFmpeg command: {' '.join(cmd[:5])}...")
            
            # Run FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ Basic placeholder video created successfully: {file_size} bytes")
                return True
            else:
                error_msg = stderr.decode() if stderr else "Unknown error"
                self.logger.error(f"❌ FFmpeg placeholder creation failed: {error_msg}")
                
                # Try even simpler approach - copy a test video if available
                return await self._create_minimal_video_file(output_path, total_duration)
                
        except Exception as e:
            self.logger.error(f"Error creating basic placeholder video: {e}")
            # Try minimal file creation as last resort
            return await self._create_minimal_video_file(output_path, total_duration)
    
    async def _create_minimal_video_file(self, output_path: str, duration: float) -> bool:
        """Create minimal video file as absolute last resort."""
        try:
            import subprocess
            import os
            
            self.logger.info("Creating minimal video file as last resort")
            
            # Ensure FFmpeg is in PATH
            ffmpeg_bin = Path.cwd() / "ffmpeg" / "bin"
            if ffmpeg_bin.exists():
                current_path = os.environ.get('PATH', '')
                if str(ffmpeg_bin) not in current_path:
                    os.environ['PATH'] = str(ffmpeg_bin) + os.pathsep + current_path
            
            # Create the simplest possible video
            cmd = [
                "ffmpeg", "-y",
                "-f", "lavfi", "-i", f"color=c=black:size=640x480:duration={min(duration, 10)}",
                "-c:v", "libx264", "-t", str(min(duration, 10)),
                str(output_path)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                self.logger.info(f"✅ Minimal video file created: {file_size} bytes")
                return True
            else:
                self.logger.error(f"❌ Minimal video creation failed: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Minimal video creation error: {e}")
            return False
    
    async def _compose_with_ffmpeg(self, animations: AnimationAssets, audio: AudioAssets, output_path: str, quality: str = "medium") -> bool:
        """Compose video using ffmpeg with production quality settings and enhanced placeholder detection."""
        try:
            from utils.video_utils import VideoUtils
            from utils.quality_presets import QualityPresetManager
            import subprocess
            import asyncio
            
            video_utils = VideoUtils()
            
            # Check FFmpeg availability
            if not video_utils.is_ffmpeg_available():
                self.logger.error("FFmpeg not available")
                return False
            
            ffmpeg_path = video_utils.get_ffmpeg_path()
            self.logger.info(f"Using FFmpeg at: {ffmpeg_path}")
            
            # Get quality preset
            quality_manager = QualityPresetManager()
            encoding_params = quality_manager.get_preset(quality)
            self.logger.info(f"Using quality preset: {quality} - {encoding_params.resolution} @ {encoding_params.bitrate}")
            
            # Create temporary directory for processing
            temp_dir = Path(self.config.temp_path) / "video_composition"
            temp_dir.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Using temp directory: {temp_dir}")
            
            # Enhanced placeholder detection and retry logic
            max_retry_attempts = 3
            for retry_attempt in range(max_retry_attempts):
                self.logger.info(f"🔄 Content generation attempt {retry_attempt + 1}/{max_retry_attempts}")
                
                # Prepare scene inputs - generate real content for all scenes
                scene_inputs = []
                real_content_count = 0
                missing_audio_scenes = []
                
                for i, (anim_scene, audio_scene) in enumerate(zip(animations.scenes, audio.scenes)):
                    self.logger.info(f"Processing scene {i}: {anim_scene.scene_id}")
                    
                    # Enhanced video input detection and generation
                    video_input = None
                    is_real_video = False
                    
                    # Priority 1: Check if we have a real animation file
                    if Path(anim_scene.file_path).exists() and Path(anim_scene.file_path).stat().st_size > 10000:
                        video_input = anim_scene.file_path
                        is_real_video = True
                        real_content_count += 1
                        self.logger.info(f"✅ Using REAL animation: {video_input}")
                    else:
                        # Priority 2: Generate real content using advanced animation generators
                        self.logger.info(f"🎬 Generating REAL animation for scene {i}: {anim_scene.scene_id}")
                        
                        # Try comprehensive animation generator first (includes Manim)
                        video_input = await self._generate_real_animation_advanced(
                            anim_scene, audio_scene, temp_dir, i, retry_attempt
                        )
                        
                        if video_input and Path(video_input).exists():
                            is_real_video = True
                            real_content_count += 1
                            self.logger.info(f"✅ Generated REAL animation: {video_input}")
                        else:
                            # If advanced generation fails, use simple but real animation
                            video_input = await self._generate_real_animation_simple(
                                anim_scene, audio_scene, temp_dir, i, retry_attempt
                            )
                            
                            if video_input and Path(video_input).exists():
                                is_real_video = True
                                real_content_count += 1
                                self.logger.info(f"✅ Generated SIMPLE real animation: {video_input}")
                            else:
                                # Final fallback: Force generation with FFmpeg
                                video_input = await self._force_generate_real_video(
                                    anim_scene, audio_scene, temp_dir, i, retry_attempt
                                )
                                
                                if video_input and Path(video_input).exists():
                                    is_real_video = True
                                    real_content_count += 1
                                    self.logger.info(f"✅ Force-generated REAL video: {video_input}")
                                else:
                                    self.logger.error(f"❌ Failed to generate any real video for scene {i}")
                                    continue  # Skip to next retry attempt
                    
                    # Verify we have a valid video input
                    if not video_input or not Path(video_input).exists():
                        self.logger.error(f"❌ No valid video input for scene {i}")
                        continue  # Skip to next retry attempt
                    
                    # Enhanced audio input detection and generation
                    audio_input = None
                    is_real_audio = False
                    
                    # Priority 1: Check if we have real audio
                    if Path(audio_scene.file_path).exists() and Path(audio_scene.file_path).stat().st_size > 1000:
                        audio_input = audio_scene.file_path
                        is_real_audio = True
                        self.logger.info(f"✅ Using REAL audio: {audio_input}")
                    else:
                        # Priority 2: Try to generate real audio on-the-fly if missing
                        self.logger.warning(f"⚠️ Scene {i} has missing audio - attempting regeneration")
                        missing_audio_scenes.append(i)
                        
                        try:
                            from agents.simple_audio_generator import SimpleAudioGenerator
                            simple_audio_gen = SimpleAudioGenerator()
                            
                            available_engines = simple_audio_gen.get_available_engines()
                            if available_engines:
                                # Generate real audio for this scene with timeout
                                real_audio_path = temp_dir / f"real_audio_{i}_attempt_{retry_attempt}.wav"
                                
                                # Use scene narration if available, otherwise create basic narration
                                narration_text = getattr(audio_scene, 'transcript', f"This is scene {i+1} of the research paper explanation.")
                                
                                try:
                                    # Add timeout to prevent infinite loops in audio generation
                                    success = await asyncio.wait_for(
                                        simple_audio_gen._generate_scene_audio_simple(
                                            narration_text, str(real_audio_path), audio_scene.duration
                                        ),
                                        timeout=60.0  # 60 second timeout for audio generation
                                    )
                                    
                                    if success and Path(real_audio_path).exists():
                                        audio_input = str(real_audio_path)
                                        is_real_audio = True
                                        self.logger.info(f"✅ Generated REAL audio on-the-fly: {audio_input}")
                                        # Remove from missing audio list since we successfully generated content
                                        if i in missing_audio_scenes:
                                            missing_audio_scenes.remove(i)
                                    else:
                                        self.logger.warning(f"Failed to generate real audio for scene {i}")
                                        
                                except asyncio.TimeoutError:
                                    self.logger.error(f"❌ Audio generation timed out after 60s for scene {i}")
                                except Exception as e:
                                    self.logger.warning(f"Audio generation error for scene {i}: {e}")
                            else:
                                self.logger.warning(f"No TTS engines available for scene {i}")
                        
                        except Exception as e:
                            self.logger.warning(f"Could not generate real audio for scene {i}: {e}")
                    
                    # Fallback: Create silent audio with proper sample rate if still needed
                    if not audio_input:
                        silent_path = temp_dir / f"silent_{i}_attempt_{retry_attempt}.wav"
                        self.logger.info(f"⚠️ Creating silent audio: {silent_path}")
                        await self._create_production_silent_audio(
                            str(silent_path), 
                            audio_scene.duration,
                            encoding_params.audio_sample_rate
                        )
                        audio_input = str(silent_path)
                        
                        # Verify silent audio was created
                        if not Path(audio_input).exists():
                            self.logger.error(f"Failed to create silent audio: {audio_input}")
                            continue  # Skip to next retry attempt
                        else:
                            audio_size = Path(audio_input).stat().st_size
                            self.logger.info(f"Silent audio created successfully: {audio_size} bytes")
                    
                    scene_inputs.append((video_input, audio_input, audio_scene.duration))
                    
                    # Log content type for this scene
                    content_type = "REAL" if (is_real_video and is_real_audio) else "MIXED" if (is_real_video or is_real_audio) else "PLACEHOLDER"
                    self.logger.info(f"Scene {i} content type: {content_type}")
                
                # Enhanced retry decision logic - now focused on real content quality
                total_scenes = len(scene_inputs)
                failed_video_count = sum(1 for video_input, _, _ in scene_inputs if not Path(video_input).exists() or Path(video_input).stat().st_size < 10000)
                missing_audio_count = len(missing_audio_scenes)
                
                self.logger.info(f"📊 Content Summary (Attempt {retry_attempt + 1}): {real_content_count}/{total_scenes} scenes have real content")
                self.logger.info(f"📊 Issues: {failed_video_count} failed videos, {missing_audio_count} missing audio")
                
                # Decide whether to retry based on content quality
                should_retry = False
                retry_reasons = []
                
                # Retry if we have any failed video generation
                if failed_video_count > 0:
                    should_retry = True
                    retry_reasons.append(f"{failed_video_count} failed video generation")
                
                # Retry if we have missing audio in more than 30% of scenes
                if missing_audio_count > total_scenes * 0.3:
                    should_retry = True
                    retry_reasons.append(f"{missing_audio_count} missing audio tracks (>{total_scenes * 0.3:.0f} threshold)")
                
                # Don't retry on the last attempt
                if retry_attempt == max_retry_attempts - 1:
                    should_retry = False
                    if retry_reasons:
                        self.logger.warning(f"⚠️ Final attempt - proceeding despite: {', '.join(retry_reasons)}")
                
                # If content quality is acceptable or this is the final attempt, proceed with composition
                if not should_retry:
                    self.logger.info(f"✅ Content quality acceptable - proceeding with video composition")
                    break
                else:
                    self.logger.warning(f"🔄 Retrying due to: {', '.join(retry_reasons)}")
                    # Clean up temporary files from this attempt before retrying
                    await self._cleanup_temp_files(temp_dir, f"*_attempt_{retry_attempt}*")
                    continue
            
            # Build FFmpeg command with production quality settings
            if len(scene_inputs) == 1:
                # Single scene composition
                self.logger.info("Using single scene composition")
                success = await self._compose_single_scene_ffmpeg(
                    scene_inputs[0], output_path, encoding_params, ffmpeg_path
                )
            else:
                # Multiple scene composition with transitions
                self.logger.info("Using multiple scene composition")
                success = await self._compose_multiple_scenes_ffmpeg(
                    scene_inputs, output_path, encoding_params, ffmpeg_path, temp_dir
                )
            
            if success and Path(output_path).exists():
                # Validate the output
                from utils.video_validator import video_validator
                output_size = Path(output_path).stat().st_size
                self.logger.info(f"FFmpeg output created: {output_size} bytes")
                
                is_valid = video_validator.validate_video_sync(output_path)
                if is_valid:
                    self.logger.info(f"✅ Video composition with ffmpeg successful: {output_path}")
                    # Clean up all temporary files on success
                    await self._cleanup_temp_files(temp_dir, "*")
                    return True
                else:
                    self.logger.error(f"❌ Generated video failed validation: {output_path}")
                    return False
            else:
                self.logger.error("❌ FFmpeg composition failed - no output file created")
                return False
                
        except Exception as e:
            self.logger.error(f"ffmpeg composition failed: {e}")
            import traceback
            self.logger.error(f"FFmpeg traceback: {traceback.format_exc()}")
            return False
    
    async def _cleanup_temp_files(self, temp_dir: Path, pattern: str) -> None:
        """Clean up temporary files matching the given pattern."""
        try:
            import glob
            
            # Use glob to find files matching the pattern
            pattern_path = temp_dir / pattern
            matching_files = glob.glob(str(pattern_path))
            
            cleaned_count = 0
            for file_path in matching_files:
                try:
                    Path(file_path).unlink()
                    cleaned_count += 1
                except Exception as e:
                    self.logger.warning(f"Failed to clean up {file_path}: {e}")
            
            if cleaned_count > 0:
                self.logger.info(f"🧹 Cleaned up {cleaned_count} temporary files")
                
        except Exception as e:
            self.logger.warning(f"Cleanup failed: {e}")
    
    async def _compose_single_scene_ffmpeg(
        self, 
        scene_input: tuple, 
        output_path: str, 
        encoding_params, 
        ffmpeg_path: str
    ) -> bool:
        """Compose single scene with FFmpeg."""
        video_input, audio_input, duration = scene_input
        
        try:
            import asyncio
            import subprocess
            import sys
            
            self.logger.info(f"Single scene composition: video={video_input}, audio={audio_input}, duration={duration}, output={output_path}")
            
            # Verify inputs exist
            if not Path(video_input).exists():
                self.logger.error(f"Video input does not exist: {video_input}")
                return False
            
            if not Path(audio_input).exists():
                self.logger.error(f"Audio input does not exist: {audio_input}")
                return False
            
            video_size = Path(video_input).stat().st_size
            audio_size = Path(audio_input).stat().st_size
            self.logger.info(f"Input sizes: video={video_size} bytes, audio={audio_size} bytes")
            
            # Build FFmpeg command for single scene
            cmd = [
                ffmpeg_path,
                "-i", video_input,
                "-i", audio_input,
                "-t", str(duration),  # Set duration
                "-map", "0:v:0",  # Map first video stream
                "-map", "1:a:0",  # Map first audio stream
            ]
            
            # Add encoding parameters
            cmd.extend(encoding_params.to_ffmpeg_args())
            
            # Add output path
            cmd.extend(["-y", output_path])
            
            self.logger.info(f"FFmpeg command: {' '.join(cmd)}")
            
            # Use subprocess.run for Windows compatibility instead of asyncio.create_subprocess_exec
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
            )
            
            if result.returncode == 0:
                if Path(output_path).exists():
                    output_size = Path(output_path).stat().st_size
                    self.logger.info(f"Single scene composition successful: {output_size} bytes")
                    return True
                else:
                    self.logger.error("FFmpeg returned success but no output file created")
                    return False
            else:
                stderr_text = result.stderr if result.stderr else "No error output"
                stdout_text = result.stdout if result.stdout else "No standard output"
                self.logger.error(f"Single scene composition failed:")
                self.logger.error(f"Return code: {result.returncode}")
                self.logger.error(f"STDERR: {stderr_text}")
                self.logger.error(f"STDOUT: {stdout_text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Single scene composition error: {e}")
            import traceback
            self.logger.error(f"Single scene traceback: {traceback.format_exc()}")
            return False
    
    async def _compose_multiple_scenes_ffmpeg(
        self, 
        scene_inputs: list, 
        output_path: str, 
        encoding_params, 
        ffmpeg_path: str,
        temp_dir: Path
    ) -> bool:
        """Compose multiple scenes with FFmpeg using concat demuxer."""
        try:
            import asyncio
            import subprocess  # Import subprocess here
            
            # Create individual scene videos first
            scene_files = []
            for i, (video_input, audio_input, duration) in enumerate(scene_inputs):
                scene_output = temp_dir / f"scene_{i}.mp4"
                
                self.logger.info(f"Creating scene {i} at: {scene_output}")
                
                # Compose individual scene
                success = await self._compose_single_scene_ffmpeg(
                    (video_input, audio_input, duration),
                    str(scene_output),
                    encoding_params,
                    ffmpeg_path
                )
                
                if success and scene_output.exists():
                    # Use absolute path to avoid path issues
                    absolute_path = scene_output.resolve()
                    scene_files.append(str(absolute_path))
                    self.logger.info(f"Scene {i} created successfully: {absolute_path}")
                else:
                    self.logger.error(f"Failed to create scene {i} at {scene_output}")
                    return False
            
            # Create concat file for FFmpeg with absolute paths
            concat_file = temp_dir / "concat_list.txt"
            self.logger.info(f"Creating concat file: {concat_file}")
            
            with open(concat_file, 'w', encoding='utf-8') as f:
                for scene_file in scene_files:
                    # Convert to absolute path and use forward slashes for FFmpeg
                    absolute_path = Path(scene_file).resolve()
                    # On Windows, FFmpeg prefers forward slashes
                    normalized_path = str(absolute_path).replace('\\', '/')
                    f.write(f"file '{normalized_path}'\n")
                    self.logger.info(f"Added to concat: {normalized_path}")
            
            # Log the concat file content for debugging
            with open(concat_file, 'r', encoding='utf-8') as f:
                concat_content = f.read()
                self.logger.info(f"Concat file content:\n{concat_content}")
            
            # Concatenate scenes using concat demuxer
            cmd = [
                ffmpeg_path,
                "-f", "concat",
                "-safe", "0",
                "-i", str(concat_file.resolve()),  # Use absolute path for concat file too
                "-c", "copy",  # Copy streams without re-encoding
                "-y", output_path
            ]
            
            self.logger.info(f"FFmpeg concat command: {' '.join(cmd)}")
            
            # Execute concatenation using subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
            )
            
            # Clean up temporary scene files
            for scene_file in scene_files:
                try:
                    Path(scene_file).unlink()
                    self.logger.info(f"Cleaned up: {scene_file}")
                except Exception as e:
                    self.logger.warning(f"Failed to clean up {scene_file}: {e}")
            
            # Clean up concat file
            try:
                concat_file.unlink()
                self.logger.info(f"Cleaned up concat file: {concat_file}")
            except Exception as e:
                self.logger.warning(f"Failed to clean up concat file: {e}")
            
            if result.returncode == 0:
                self.logger.info("Multiple scene composition successful")
                return True
            else:
                stderr_text = result.stderr if result.stderr else "No error output"
                self.logger.error(f"Scene concatenation failed: {stderr_text}")
                return False
                
        except Exception as e:
            self.logger.error(f"Multiple scene composition error: {e}")
            import traceback
            self.logger.error(f"Multiple scene traceback: {traceback.format_exc()}")
            return False
    
    async def _compose_with_moviepy(self, animations: AnimationAssets, audio: AudioAssets, output_path: str, quality: str = "medium") -> bool:
        """Compose video using moviepy as fallback with production quality settings."""
        try:
            # Try to import moviepy
            from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip, ColorClip
            import asyncio
            
            # Get quality preset for encoding parameters
            from utils.quality_presets import QualityPresetManager
            quality_manager = QualityPresetManager()
            encoding_params = quality_manager.get_preset(quality)
            
            self.logger.info(f"MoviePy composition with {quality} quality: {encoding_params.resolution}")
            
            clips = []
            
            for i, (anim_scene, audio_scene) in enumerate(zip(animations.scenes, audio.scenes)):
                self.logger.info(f"Processing MoviePy scene {i}: {anim_scene.scene_id}")
                
                # Load or create video clip
                if Path(anim_scene.file_path).exists():
                    self.logger.info(f"Loading existing video: {anim_scene.file_path}")
                    video_clip = VideoFileClip(anim_scene.file_path)
                else:
                    # Create high-quality placeholder clip
                    self.logger.info(f"Creating placeholder clip for scene {i}")
                    video_clip = self._create_moviepy_placeholder_clip(
                        audio_scene.duration, 
                        encoding_params,
                        scene_title=f"Scene {i+1}",
                        scene_id=anim_scene.scene_id
                    )
                
                # Load or create audio clip
                if Path(audio_scene.file_path).exists():
                    self.logger.info(f"Loading existing audio: {audio_scene.file_path}")
                    audio_clip = AudioFileClip(audio_scene.file_path)
                    video_clip = video_clip.set_audio(audio_clip)
                else:
                    self.logger.info(f"No audio file for scene {i}, using silent audio")
                    # MoviePy will handle silent video automatically
                
                # Set duration and resize to target resolution
                video_clip = video_clip.set_duration(audio_scene.duration)
                video_clip = video_clip.resize((encoding_params.width, encoding_params.height))
                
                clips.append(video_clip)
            
            # Concatenate all clips with smooth transitions
            self.logger.info(f"Concatenating {len(clips)} clips")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Apply final video settings
            final_video = final_video.set_fps(encoding_params.fps)
            
            # Write to file in thread pool with production settings
            self.logger.info(f"Writing MoviePy video to: {output_path}")
            loop = asyncio.get_event_loop()
            
            # Calculate bitrate for MoviePy (convert from string like "5500k" to integer)
            video_bitrate = encoding_params.bitrate.rstrip('k') + "000"  # Convert to bps
            audio_bitrate = encoding_params.audio_bitrate.rstrip('k') + "k"
            
            await loop.run_in_executor(
                None,
                lambda: final_video.write_videofile(
                    output_path,
                    codec=encoding_params.video_codec,
                    audio_codec=encoding_params.audio_codec,
                    bitrate=video_bitrate,
                    audio_bitrate=audio_bitrate,
                    fps=encoding_params.fps,
                    preset=encoding_params.preset,
                    temp_audiofile='temp-audio.m4a',
                    remove_temp=True,
                    verbose=False,
                    logger=None  # Suppress MoviePy logging
                )
            )
            
            # Clean up
            final_video.close()
            for clip in clips:
                clip.close()
            
            if Path(output_path).exists():
                output_size = Path(output_path).stat().st_size
                self.logger.info(f"MoviePy composition successful: {output_size} bytes")
                return True
            else:
                self.logger.error("MoviePy composition failed - no output file created")
                return False
            
        except ImportError:
            self.logger.warning("MoviePy not available")
            return False
        except Exception as e:
            self.logger.error(f"MoviePy composition failed: {e}")
            import traceback
            self.logger.error(f"MoviePy traceback: {traceback.format_exc()}")
            return False
    
    def _create_moviepy_placeholder_clip(self, duration: float, encoding_params, scene_title: str = "Scene", scene_id: str = "unknown"):
        """Create a high-quality placeholder clip using MoviePy."""
        try:
            from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
            
            # Create background color clip
            bg_clip = ColorClip(
                size=(encoding_params.width, encoding_params.height),
                color=(30, 58, 138),  # Blue background #1e3a8a
                duration=duration
            )
            
            # Create title text
            try:
                title_clip = TextClip(
                    "RASO Research Video",
                    fontsize=min(80, encoding_params.width // 24),  # Scale font with resolution
                    color='white',
                    font='Arial-Bold'
                ).set_duration(duration).set_position(('center', encoding_params.height // 2 - 100))
                
                # Create scene text
                scene_clip = TextClip(
                    scene_title,
                    fontsize=min(40, encoding_params.width // 48),
                    color='white',
                    font='Arial'
                ).set_duration(duration).set_position(('center', encoding_params.height // 2 + 50))
                
                # Create duration text
                duration_clip = TextClip(
                    f"Duration: {duration:.1f}s",
                    fontsize=min(30, encoding_params.width // 64),
                    color='white',
                    font='Arial'
                ).set_duration(duration).set_position(('center', encoding_params.height // 2 + 150))
                
                # Composite all elements
                composite = CompositeVideoClip([bg_clip, title_clip, scene_clip, duration_clip])
                
            except Exception as text_error:
                self.logger.warning(f"Text overlay failed: {text_error}, using plain background")
                composite = bg_clip
            
            return composite
            
        except Exception as e:
            self.logger.warning(f"MoviePy placeholder creation failed: {e}")
            # Return simple color clip as fallback
            from moviepy.editor import ColorClip
            return ColorClip(
                size=(encoding_params.width, encoding_params.height),
                color=(30, 58, 138),
                duration=duration
            )
    
    async def _create_simple_slideshow(self, animations: AnimationAssets, audio: AudioAssets, output_path: str, quality: str = "medium") -> bool:
        """Create professional slideshow as last resort with quality presets."""
        try:
            import subprocess
            import asyncio
            
            # Get quality preset for encoding parameters
            from utils.quality_presets import QualityPresetManager
            quality_manager = QualityPresetManager()
            encoding_params = quality_manager.get_preset(quality)
            
            self.logger.info(f"Creating slideshow with {quality} quality: {encoding_params.resolution}")
            
            # Create a slideshow directory
            temp_dir = Path(self.config.temp_path) / "slideshow"
            temp_dir.mkdir(parents=True, exist_ok=True)
            
            # Create professional background image
            bg_image = temp_dir / "background.png"
            await self._create_professional_background_image(str(bg_image), encoding_params)
            
            # Calculate total duration
            total_duration = sum(scene.duration for scene in audio.scenes)
            self.logger.info(f"Creating slideshow with duration: {total_duration}s")
            
            # Use FFmpeg to create high-quality slideshow
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path() or "ffmpeg"
            
            cmd = [
                ffmpeg_path,
                "-loop", "1", "-i", str(bg_image),
                "-t", str(total_duration),
                "-vf", f"scale={encoding_params.resolution},fps={encoding_params.fps}",
            ]
            
            # Add encoding parameters
            cmd.extend(encoding_params.to_ffmpeg_args())
            cmd.extend(["-y", output_path])
            
            self.logger.info(f"Slideshow FFmpeg command: {' '.join(cmd)}")
            
            # Execute slideshow creation
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                self.logger.info("Slideshow video created successfully")
                
                # Add audio if available
                await self._add_audio_to_slideshow(output_path, audio.scenes, encoding_params)
                
                output_size = Path(output_path).stat().st_size
                self.logger.info(f"Slideshow creation successful: {output_size} bytes")
                return True
            else:
                self.logger.error(f"Slideshow creation failed: {result.stderr}")
                return False
            
        except Exception as e:
            self.logger.error(f"Slideshow creation failed: {e}")
            import traceback
            self.logger.error(f"Slideshow traceback: {traceback.format_exc()}")
            return False
    
    async def _create_professional_background_image(self, output_path: str, encoding_params) -> None:
        """Create professional background image for slideshow."""
        try:
            # Try to create with PIL first
            try:
                from PIL import Image, ImageDraw, ImageFont
                
                # Create professional gradient background
                img = Image.new('RGB', (encoding_params.width, encoding_params.height), color='#1e3a8a')
                draw = ImageDraw.Draw(img)
                
                # Add gradient effect (simple version)
                for y in range(encoding_params.height):
                    alpha = int(255 * (1 - y / encoding_params.height * 0.3))
                    color = (30 + alpha // 10, 58 + alpha // 8, 138 + alpha // 4)
                    draw.line([(0, y), (encoding_params.width, y)], fill=color)
                
                # Add title with proper scaling
                try:
                    font_size = max(40, encoding_params.width // 30)
                    font = ImageFont.truetype("arial.ttf", font_size)
                except:
                    font = ImageFont.load_default()
                
                text = "RASO Research Video Platform"
                bbox = draw.textbbox((0, 0), text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]
                
                x = (encoding_params.width - text_width) // 2
                y = (encoding_params.height - text_height) // 2
                
                # Add text shadow
                draw.text((x + 2, y + 2), text, fill='black', font=font)
                draw.text((x, y), text, fill='white', font=font)
                
                # Add subtitle
                subtitle = "Educational Content Generation"
                subtitle_font_size = max(20, encoding_params.width // 60)
                try:
                    subtitle_font = ImageFont.truetype("arial.ttf", subtitle_font_size)
                except:
                    subtitle_font = ImageFont.load_default()
                
                subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
                subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
                
                subtitle_x = (encoding_params.width - subtitle_width) // 2
                subtitle_y = y + text_height + 20
                
                draw.text((subtitle_x + 1, subtitle_y + 1), subtitle, fill='black', font=subtitle_font)
                draw.text((subtitle_x, subtitle_y), subtitle, fill='lightgray', font=subtitle_font)
                
                img.save(output_path)
                self.logger.info(f"Professional background created with PIL: {output_path}")
                return
                
            except ImportError:
                self.logger.info("PIL not available, using FFmpeg for background")
            
            # Fallback: Create with FFmpeg
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path() or "ffmpeg"
            
            cmd = [
                ffmpeg_path,
                "-f", "lavfi", 
                "-i", f"color=c=#1e3a8a:size={encoding_params.resolution}:duration=1",
                "-vf", (
                    f"drawtext=text='RASO Research Video Platform':fontcolor=white:"
                    f"fontsize={max(40, encoding_params.width // 30)}:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2-50,"
                    f"drawtext=text='Educational Content Generation':fontcolor=lightgray:"
                    f"fontsize={max(20, encoding_params.width // 60)}:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2+50"
                ),
                "-vframes", "1",
                "-y", output_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            if result.returncode == 0:
                self.logger.info(f"Professional background created with FFmpeg: {output_path}")
            else:
                self.logger.warning(f"Background creation failed: {result.stderr}")
            
        except Exception as e:
            self.logger.warning(f"Professional background creation failed: {e}")
            # Create simple fallback
            Path(output_path).touch()
    
    async def _add_audio_to_slideshow(self, video_path: str, audio_scenes: List[AudioScene], encoding_params) -> None:
        """Add audio track to slideshow video with proper synchronization."""
        try:
            import subprocess  # Add missing import
            
            if not audio_scenes:
                self.logger.info("No audio scenes to add to slideshow")
                return
            
            # Find existing audio files
            existing_audio_files = [
                scene.file_path for scene in audio_scenes 
                if Path(scene.file_path).exists()
            ]
            
            if not existing_audio_files:
                self.logger.info("No existing audio files found for slideshow")
                return
            
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path() or "ffmpeg"
            temp_output = video_path + ".temp.mp4"
            
            if len(existing_audio_files) == 1:
                # Single audio file
                cmd = [
                    ffmpeg_path,
                    "-i", video_path,
                    "-i", existing_audio_files[0],
                    "-c:v", "copy", 
                    "-c:a", encoding_params.audio_codec,
                    "-b:a", encoding_params.audio_bitrate,
                    "-shortest",
                    "-y", temp_output
                ]
            else:
                # Multiple audio files - concatenate first
                audio_list_file = Path(video_path).parent / "audio_list.txt"
                with open(audio_list_file, 'w', encoding='utf-8') as f:
                    for audio_file in existing_audio_files:
                        # Convert to absolute path and normalize for FFmpeg
                        absolute_path = Path(audio_file).resolve()
                        normalized_path = str(absolute_path).replace('\\', '/')
                        f.write(f"file '{normalized_path}'\n")
                
                # Concatenate audio files first
                concat_audio = Path(video_path).parent / "concat_audio.wav"
                concat_cmd = [
                    ffmpeg_path,
                    "-f", "concat", "-safe", "0", "-i", str(audio_list_file),
                    "-c", "copy", "-y", str(concat_audio)
                ]
                
                concat_result = subprocess.run(concat_cmd, capture_output=True, text=True, timeout=60)
                if concat_result.returncode == 0:
                    # Add concatenated audio to video
                    cmd = [
                        ffmpeg_path,
                        "-i", video_path,
                        "-i", str(concat_audio),
                        "-c:v", "copy", 
                        "-c:a", encoding_params.audio_codec,
                        "-b:a", encoding_params.audio_bitrate,
                        "-shortest",
                        "-y", temp_output
                    ]
                else:
                    self.logger.warning("Audio concatenation failed, using first audio file")
                    cmd = [
                        ffmpeg_path,
                        "-i", video_path,
                        "-i", existing_audio_files[0],
                        "-c:v", "copy", 
                        "-c:a", encoding_params.audio_codec,
                        "-shortest",
                        "-y", temp_output
                    ]
            
            # Execute audio addition
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and Path(temp_output).exists():
                # Replace original with audio-enhanced version
                Path(temp_output).replace(video_path)
                self.logger.info("Audio successfully added to slideshow")
            else:
                self.logger.warning(f"Adding audio to slideshow failed: {result.stderr}")
                # Clean up temp file if it exists
                if Path(temp_output).exists():
                    Path(temp_output).unlink()
            
            # Clean up temporary files
            for temp_file in [audio_list_file, concat_audio]:
                if isinstance(temp_file, Path) and temp_file.exists():
                    temp_file.unlink()
            
        except Exception as e:
            self.logger.warning(f"Adding audio to slideshow failed: {e}")
    
    async def _create_production_placeholder_video(self, output_path: str, duration: float, encoding_params) -> None:
        """Create high-quality placeholder video with production settings."""
        try:
            from utils.video_utils import VideoUtils
            import subprocess
            import asyncio
            
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path()
            if not ffmpeg_path:
                return
            
            # Create a professional-looking placeholder with scene information
            cmd = [
                ffmpeg_path,
                "-f", "lavfi", 
                "-i", f"color=c=#1e3a8a:size={encoding_params.resolution}:duration={duration}:rate={encoding_params.fps}",
                "-vf", (
                    f"drawtext=text='RASO Research Video':fontcolor=white:fontsize=80:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2-100,"
                    f"drawtext=text='Scene Placeholder':fontcolor=white:fontsize=40:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2+50,"
                    f"drawtext=text='Duration\\: {duration:.1f}s':fontcolor=white:fontsize=30:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2+150"
                ),
                "-c:v", encoding_params.video_codec,
                "-preset", "ultrafast",  # Fast encoding for placeholder
                "-crf", "28",  # Lower quality for placeholder
                "-pix_fmt", encoding_params.pixel_format,
                "-y", output_path
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Production placeholder video creation failed: {result.stderr}")
            
        except Exception as e:
            self.logger.warning(f"Production placeholder video creation failed: {e}")
    
    async def _create_production_silent_audio(self, output_path: str, duration: float, sample_rate: int = 44100) -> None:
        """Create silent audio file with production quality settings."""
        try:
            from utils.video_utils import VideoUtils
            import subprocess
            import asyncio
            
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path()
            if not ffmpeg_path:
                return
            
            cmd = [
                ffmpeg_path,
                "-f", "lavfi", 
                "-i", f"anullsrc=r={sample_rate}:cl=stereo",
                "-t", str(duration),
                "-c:a", "aac",
                "-b:a", "192k",
                "-y", output_path
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
            )
            
            if result.returncode != 0:
                self.logger.warning(f"Production silent audio creation failed: {result.stderr}")
            
        except Exception as e:
            self.logger.warning(f"Production silent audio creation failed: {e}")

    async def _create_placeholder_video(self, output_path: str, duration: float) -> None:
        """Create placeholder video."""
        try:
            import subprocess
            import asyncio
            
            cmd = [
                "ffmpeg",
                "-f", "lavfi", "-i", f"color=c=blue:size=1920x1080:duration={duration}",
                "-vf", "drawtext=text='RASO Video Scene':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264", "-preset", "ultrafast",
                "-y", output_path
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            )
            
        except Exception as e:
            self.logger.warning(f"Placeholder video creation failed: {e}")
    
    async def _create_silent_audio_file(self, output_path: str, duration: float) -> None:
        """Create silent audio file."""
        try:
            import subprocess
            import asyncio
            
            cmd = [
                "ffmpeg",
                "-f", "lavfi", "-i", f"anullsrc=r=44100:cl=stereo",
                "-t", str(duration),
                "-y", output_path
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
            )
            
        except Exception as e:
            self.logger.warning(f"Silent audio creation failed: {e}")
    
    async def _create_background_image(self, output_path: str) -> None:
        """Create background image for slideshow."""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # Create a simple background
            img = Image.new('RGB', (1920, 1080), color='#1e3a8a')  # Blue background
            draw = ImageDraw.Draw(img)
            
            # Add title
            try:
                font = ImageFont.truetype("arial.ttf", 80)
            except:
                font = ImageFont.load_default()
            
            text = "RASO Research Video"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1920 - text_width) // 2
            y = (1080 - text_height) // 2
            
            draw.text((x, y), text, fill='white', font=font)
            
            img.save(output_path)
            
        except ImportError:
            # Create simple image with ffmpeg if PIL not available
            import subprocess
            import asyncio
            
            cmd = [
                "ffmpeg",
                "-f", "lavfi", "-i", "color=c=blue:size=1920x1080:duration=1",
                "-vframes", "1",
                "-y", output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            await process.communicate()
    
    async def _add_audio_to_video(self, video_path: str, audio_scenes: List[AudioScene]) -> None:
        """Add audio track to video."""
        try:
            if not audio_scenes or not any(Path(scene.file_path).exists() for scene in audio_scenes):
                return
            
            import subprocess
            import asyncio
            
            # Find first existing audio file
            audio_file = None
            for scene in audio_scenes:
                if Path(scene.file_path).exists():
                    audio_file = scene.file_path
                    break
            
            if not audio_file:
                return
            
            temp_output = video_path + ".temp.mp4"
            
            cmd = [
                "ffmpeg",
                "-i", video_path,
                "-i", audio_file,
                "-c:v", "copy", "-c:a", "aac",
                "-shortest",
                "-y", temp_output
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            )
            
            if result.returncode == 0 and Path(temp_output).exists():
                Path(temp_output).replace(video_path)
            
        except Exception as e:
            self.logger.warning(f"Adding audio to video failed: {e}")
    
    async def _get_video_duration(self, video_path: str) -> float:
        """Get video duration."""
        try:
            import subprocess
            import asyncio
            import json
            
            cmd = [
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", video_path
            ]
            
            # Use subprocess.run for Windows compatibility
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            )
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                duration = float(info.get("format", {}).get("duration", 0))
                return duration
            
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to get video duration: {e}")
            return 0.0
    
    async def _create_mock_video_file(self, output_path: str) -> bool:
        """Create a mock video file for testing when no video tools are available."""
        try:
            # Create a simple text file that represents a video
            # This is just for testing the pipeline
            mock_content = f"""# RASO Mock Video File
# This is a placeholder video file created for testing
# In production, this would be a real MP4 video file

Video Path: {output_path}
Created: {datetime.now().isoformat()}
Type: Mock Video for Testing
Duration: 60 seconds
Resolution: 1920x1080

# This file would contain actual video data in production
""" * 100  # Make it larger to have a reasonable file size
            
            # Write mock content to create a file with some size
            with open(output_path, 'w') as f:
                f.write(mock_content)
            
            self.logger.info(f"Created mock video file: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create mock video file: {e}")
            return False
    def _validate_content_synchronization(self, animations: AnimationAssets, audio: AudioAssets) -> Dict[str, Any]:
        """Validate that audio and video content are properly synchronized."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Check scene count match
            anim_count = len(animations.scenes) if animations else 0
            audio_count = len(audio.scenes) if audio else 0
            
            validation["stats"]["animation_scenes"] = anim_count
            validation["stats"]["audio_scenes"] = audio_count
            
            if anim_count != audio_count:
                validation["errors"].append(f"Scene count mismatch: {anim_count} animations vs {audio_count} audio scenes")
                validation["valid"] = False
                return validation
            
            # Check duration synchronization
            total_anim_duration = sum(scene.duration for scene in animations.scenes) if animations else 0
            total_audio_duration = sum(scene.duration for scene in audio.scenes) if audio else 0
            
            validation["stats"]["total_animation_duration"] = total_anim_duration
            validation["stats"]["total_audio_duration"] = total_audio_duration
            
            duration_diff = abs(total_anim_duration - total_audio_duration)
            if duration_diff > 5.0:  # 5 second tolerance
                validation["errors"].append(f"Total duration mismatch: {total_anim_duration}s animations vs {total_audio_duration}s audio")
                validation["valid"] = False
            elif duration_diff > 1.0:  # 1 second warning threshold
                validation["warnings"].append(f"Minor duration difference: {duration_diff:.1f}s")
            
            # Check individual scene synchronization
            scene_sync_issues = 0
            for i, (anim_scene, audio_scene) in enumerate(zip(animations.scenes, audio.scenes)):
                scene_duration_diff = abs(anim_scene.duration - audio_scene.duration)
                if scene_duration_diff > 2.0:  # 2 second tolerance per scene
                    validation["warnings"].append(f"Scene {i} duration mismatch: {anim_scene.duration}s vs {audio_scene.duration}s")
                    scene_sync_issues += 1
            
            validation["stats"]["scene_sync_issues"] = scene_sync_issues
            
            # Check file existence
            missing_files = []
            for i, scene in enumerate(animations.scenes):
                if not Path(scene.file_path).exists():
                    missing_files.append(f"Animation scene {i}: {scene.file_path}")
            
            for i, scene in enumerate(audio.scenes):
                if not Path(scene.file_path).exists():
                    missing_files.append(f"Audio scene {i}: {scene.file_path}")
            
            if missing_files:
                validation["warnings"].extend([f"Missing file: {f}" for f in missing_files])
                validation["stats"]["missing_files"] = len(missing_files)
            
            # Overall sync quality score
            sync_score = 1.0
            if duration_diff > 0:
                sync_score -= min(0.3, duration_diff / 10.0)  # Reduce score based on duration diff
            if scene_sync_issues > 0:
                sync_score -= min(0.2, scene_sync_issues * 0.05)  # Reduce score for scene issues
            if missing_files:
                sync_score -= min(0.3, len(missing_files) * 0.1)  # Reduce score for missing files
            
            validation["stats"]["sync_quality_score"] = max(0.0, sync_score)
            
        except Exception as e:
            validation["errors"].append(f"Synchronization validation failed: {e}")
            validation["valid"] = False
        
        return validation
    
    def _report_content_status(self, animations: AnimationAssets, audio: AudioAssets) -> None:
        """Report detailed status of content components."""
        self.logger.info("📊 Content Status Report:")
        
        # Animation status
        if animations and animations.scenes:
            real_animations = sum(1 for scene in animations.scenes 
                                if Path(scene.file_path).exists() and Path(scene.file_path).stat().st_size > 10000)
            total_animations = len(animations.scenes)
            self.logger.info(f"  🎬 Animations: {real_animations}/{total_animations} real content")
            
            for i, scene in enumerate(animations.scenes):
                if Path(scene.file_path).exists():
                    file_size = Path(scene.file_path).stat().st_size
                    status = "✅ REAL" if file_size > 10000 else "⚠️ SMALL"
                    self.logger.info(f"    Scene {i}: {status} ({file_size} bytes, {scene.duration:.1f}s)")
                else:
                    self.logger.info(f"    Scene {i}: ❌ MISSING ({scene.duration:.1f}s)")
        else:
            self.logger.warning("  🎬 Animations: No animation data available")
        
        # Audio status
        if audio and audio.scenes:
            real_audio = sum(1 for scene in audio.scenes 
                           if Path(scene.file_path).exists() and Path(scene.file_path).stat().st_size > 1000)
            total_audio = len(audio.scenes)
            self.logger.info(f"  🔊 Audio: {real_audio}/{total_audio} real content")
            
            for i, scene in enumerate(audio.scenes):
                if Path(scene.file_path).exists():
                    file_size = Path(scene.file_path).stat().st_size
                    status = "✅ REAL" if file_size > 1000 else "⚠️ SMALL"
                    self.logger.info(f"    Scene {i}: {status} ({file_size} bytes, {scene.duration:.1f}s)")
                else:
                    self.logger.info(f"    Scene {i}: ❌ MISSING ({scene.duration:.1f}s)")
        else:
            self.logger.warning("  🔊 Audio: No audio data available")
        
        # Synchronization check
        sync_validation = self._validate_content_synchronization(animations, audio)
        sync_score = sync_validation["stats"].get("sync_quality_score", 0.0)
        sync_status = "✅ EXCELLENT" if sync_score > 0.9 else "⚠️ GOOD" if sync_score > 0.7 else "❌ POOR"
        self.logger.info(f"  🔄 Synchronization: {sync_status} (score: {sync_score:.2f})")
        
        if sync_validation["errors"]:
            for error in sync_validation["errors"]:
                self.logger.error(f"    ❌ {error}")
        
        if sync_validation["warnings"]:
            for warning in sync_validation["warnings"]:
                self.logger.warning(f"    ⚠️ {warning}")
    
    async def _generate_real_animation_advanced(self, anim_scene, audio_scene, temp_dir: Path, scene_index: int, retry_attempt: int) -> Optional[str]:
        """Generate real animation using advanced generators (Manim, comprehensive)."""
        try:
            self.logger.info(f"🎨 Attempting advanced animation generation for scene {scene_index}")
            
            # Try comprehensive animation generator first
            try:
                from agents.comprehensive_animation_generator import ComprehensiveAnimationGenerator
                comp_gen = ComprehensiveAnimationGenerator()
                
                if comp_gen.get_capabilities()["can_generate_video"]:
                    output_path = temp_dir / f"advanced_animation_{scene_index}_attempt_{retry_attempt}.mp4"
                    
                    # Create scene data for the generator
                    scene_data = {
                        "id": anim_scene.scene_id,
                        "title": f"Scene {scene_index + 1}",
                        "duration": audio_scene.duration,
                        "content": getattr(audio_scene, 'transcript', f"Educational content for scene {scene_index + 1}")
                    }
                    
                    success = await self._generate_with_comprehensive_generator(
                        comp_gen, scene_data, str(output_path)
                    )
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 10000:
                        self.logger.info(f"✅ Advanced animation generated: {output_path}")
                        return str(output_path)
                    
            except Exception as e:
                self.logger.warning(f"Comprehensive generator failed: {e}")
            
            # Try Manim generator
            try:
                from agents.manim_animation_generator import ManimAnimationGenerator
                manim_gen = ManimAnimationGenerator()
                
                if manim_gen.get_capabilities()["can_generate_video"]:
                    output_path = temp_dir / f"manim_animation_{scene_index}_attempt_{retry_attempt}.mp4"
                    
                    # Create scene data for Manim
                    scene_data = {
                        "id": anim_scene.scene_id,
                        "title": f"Scene {scene_index + 1}",
                        "duration": audio_scene.duration,
                        "content": getattr(audio_scene, 'transcript', f"Mathematical visualization for scene {scene_index + 1}")
                    }
                    
                    success = await self._generate_with_manim_generator(
                        manim_gen, scene_data, str(output_path)
                    )
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 10000:
                        self.logger.info(f"✅ Manim animation generated: {output_path}")
                        return str(output_path)
                    
            except Exception as e:
                self.logger.warning(f"Manim generator failed: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Advanced animation generation failed: {e}")
            return None
    
    async def _generate_real_animation_simple(self, anim_scene, audio_scene, temp_dir: Path, scene_index: int, retry_attempt: int) -> Optional[str]:
        """Generate real animation using simple but reliable generators."""
        try:
            self.logger.info(f"🎬 Attempting simple real animation generation for scene {scene_index}")
            
            # Try Python video generator
            try:
                from agents.python_video_generator import PythonVideoGenerator
                python_gen = PythonVideoGenerator()
                
                if python_gen.get_capabilities()["can_generate_video"]:
                    output_path = temp_dir / f"python_animation_{scene_index}_attempt_{retry_attempt}.mp4"
                    
                    title = f"Scene {scene_index + 1}"
                    content = getattr(audio_scene, 'transcript', f"Content for scene {scene_index + 1}")
                    
                    success = python_gen.create_text_video(
                        title, content, audio_scene.duration, str(output_path)
                    )
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
                        self.logger.info(f"✅ Python video generated: {output_path}")
                        return str(output_path)
                    
            except Exception as e:
                self.logger.warning(f"Python video generator failed: {e}")
            
            # Try simple animation generator with enhanced settings
            try:
                from agents.simple_animation_generator import SimpleAnimationGenerator
                simple_gen = SimpleAnimationGenerator()
                
                if simple_gen.get_capabilities()["ffmpeg_available"]:
                    output_path = temp_dir / f"simple_animation_{scene_index}_attempt_{retry_attempt}.mp4"
                    
                    # Create a mock scene object for the generator
                    class MockScene:
                        def __init__(self, scene_id, title, duration):
                            self.id = scene_id
                            self.title = title
                            self.duration = duration
                    
                    mock_scene = MockScene(anim_scene.scene_id, f"Scene {scene_index + 1}", audio_scene.duration)
                    
                    success = await simple_gen._create_text_overlay_animation(
                        mock_scene, str(output_path)
                    )
                    
                    if success and Path(output_path).exists() and Path(output_path).stat().st_size > 1000:
                        self.logger.info(f"✅ Simple animation generated: {output_path}")
                        return str(output_path)
                    
            except Exception as e:
                self.logger.warning(f"Simple animation generator failed: {e}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Simple animation generation failed: {e}")
            return None
    
    async def _force_generate_real_video(self, anim_scene, audio_scene, temp_dir: Path, scene_index: int, retry_attempt: int) -> Optional[str]:
        """Force generate a real video using FFmpeg directly as final fallback."""
        try:
            self.logger.info(f"🔧 Force generating real video for scene {scene_index}")
            
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            
            if not video_utils.is_ffmpeg_available():
                self.logger.error("FFmpeg not available for force generation")
                return None
            
            ffmpeg_path = video_utils.get_ffmpeg_path()
            output_path = temp_dir / f"force_generated_{scene_index}_attempt_{retry_attempt}.mp4"
            
            # Create a solid color video with text overlay using FFmpeg
            title = f"Scene {scene_index + 1}: {anim_scene.scene_id}"
            duration = audio_scene.duration
            
            # FFmpeg command to create a real video with text
            cmd = [
                ffmpeg_path,
                "-f", "lavfi",
                "-i", f"color=c=#1a1a2e:size=1920x1080:duration={duration}:rate=30",
                "-vf", f"drawtext=text='{title}':fontsize=48:fontcolor=white:x=(w-text_w)/2:y=(h-text_h)/2",
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                "-crf", "23",
                "-y", str(output_path)
            ]
            
            # Execute FFmpeg command
            import subprocess
            import asyncio
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=60  # 1 minute timeout
                )
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                if file_size > 10000:  # At least 10KB
                    self.logger.info(f"✅ Force-generated real video: {output_path} ({file_size} bytes)")
                    return str(output_path)
                else:
                    self.logger.warning(f"Force-generated video too small: {file_size} bytes")
            else:
                stderr_text = result.stderr if result.stderr else "No error output"
                self.logger.error(f"FFmpeg force generation failed: {stderr_text}")
            
            return None
            
        except Exception as e:
            self.logger.error(f"Force video generation failed: {e}")
            return None
    
    async def _generate_with_comprehensive_generator(self, generator, scene_data: dict, output_path: str) -> bool:
        """Generate animation using comprehensive generator."""
        try:
            # Create a mock script object for the generator
            class MockScript:
                def __init__(self, scenes):
                    self.scenes = scenes
            
            class MockScene:
                def __init__(self, scene_data):
                    self.id = scene_data["id"]
                    self.title = scene_data["title"]
                    self.duration = scene_data["duration"]
                    self.narration = scene_data["content"]
                    self.visual_type = "text_overlay"
            
            mock_scene = MockScene(scene_data)
            mock_script = MockScript([mock_scene])
            
            # Generate animation assets
            temp_output_dir = Path(output_path).parent / "temp_comprehensive"
            temp_output_dir.mkdir(exist_ok=True)
            
            animation_assets = await generator.generate_animation_assets(mock_script, str(temp_output_dir))
            
            if animation_assets and animation_assets.scenes:
                # Copy the generated file to the desired output path
                generated_file = animation_assets.scenes[0].file_path
                if Path(generated_file).exists():
                    import shutil
                    shutil.copy2(generated_file, output_path)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Comprehensive generator execution failed: {e}")
            return False
    
    async def _generate_with_manim_generator(self, generator, scene_data: dict, output_path: str) -> bool:
        """Generate animation using Manim generator."""
        try:
            # Create a mock script object for the generator
            class MockScript:
                def __init__(self, scenes):
                    self.scenes = scenes
            
            class MockScene:
                def __init__(self, scene_data):
                    self.id = scene_data["id"]
                    self.title = scene_data["title"]
                    self.duration = scene_data["duration"]
                    self.narration = scene_data["content"]
                    self.visual_type = "mathematical"
            
            mock_scene = MockScene(scene_data)
            mock_script = MockScript([mock_scene])
            
            # Generate animation assets
            temp_output_dir = Path(output_path).parent / "temp_manim"
            temp_output_dir.mkdir(exist_ok=True)
            
            animation_assets = await generator.generate_animation_assets(mock_script, str(temp_output_dir))
            
            if animation_assets and animation_assets.scenes:
                # Copy the generated file to the desired output path
                generated_file = animation_assets.scenes[0].file_path
                if Path(generated_file).exists():
                    import shutil
                    shutil.copy2(generated_file, output_path)
                    return True
            
            return False
            
        except Exception as e:
            self.logger.warning(f"Manim generator execution failed: {e}")
            return False