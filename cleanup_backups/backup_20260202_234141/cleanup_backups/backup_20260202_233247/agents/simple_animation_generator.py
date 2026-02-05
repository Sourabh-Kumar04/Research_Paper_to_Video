"""
Simple Animation Generator for RASO platform.
Creates basic animations using FFmpeg without complex dependencies.
"""

import os
import asyncio
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any

# Import Python video generator for fallback
try:
    from agents.python_video_generator import PythonVideoGenerator
    PYTHON_VIDEO_AVAILABLE = True
except ImportError:
    PYTHON_VIDEO_AVAILABLE = False

# Import Manim animation generator
try:
    from agents.manim_animation_generator import ManimAnimationGenerator
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False


class SimpleAnimationGenerator:
    """Simple, reliable animation generator using FFmpeg text overlays."""
    
    def __init__(self):
        """Initialize the simple animation generator."""
        self.resolution = "1920x1080"
        self.fps = 30
        self.background_color = "#1a1a2e"
        self.text_color = "#ffffff"
        self.font_size = 48
        self.ffmpeg_available = self._check_ffmpeg_availability()
        
        # Initialize Python video generator for fallback
        if PYTHON_VIDEO_AVAILABLE:
            self.python_video_generator = PythonVideoGenerator()
        else:
            self.python_video_generator = None
            
        # Initialize Manim animation generator
        if MANIM_AVAILABLE:
            self.manim_generator = ManimAnimationGenerator()
        else:
            self.manim_generator = None
    
    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available on the system."""
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, timeout=5)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_capabilities(self) -> Dict[str, bool]:
        """Get animation generation capabilities."""
        python_video_caps = self.python_video_generator.get_capabilities() if self.python_video_generator else {}
        manim_caps = self.manim_generator.get_capabilities() if self.manim_generator else {}
        
        return {
            "ffmpeg_available": self.ffmpeg_available,
            "text_overlay": self.ffmpeg_available,
            "manim_available": MANIM_AVAILABLE and manim_caps.get("manim_available", False),
            "complex_animations": MANIM_AVAILABLE and manim_caps.get("complex_animations", False),
            "python_video_available": PYTHON_VIDEO_AVAILABLE and python_video_caps.get("can_generate_video", False),
            "fallback_animation": True  # Always available - we have multiple fallback options
        }

    async def generate_animation_assets(self, script, output_dir: str):
        """Generate animation assets from a narration script."""
        # Import here to avoid circular imports
        from backend.models.animation import AnimationAssets, RenderedScene, VideoResolution, RenderStatus
        
        # Create output directory
        animation_dir = Path(output_dir) / "animations"
        animation_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate animations for each scene
        rendered_scenes = []
        
        for i, scene in enumerate(script.scenes):
            print(f"Generating animation for scene {i+1}/{len(script.scenes)}: {scene.title}")
            
            rendered_scene = await self._generate_scene_animation(scene, animation_dir)
            
            if rendered_scene:
                rendered_scenes.append(rendered_scene)
                print(f"✅ Animation generated for scene {scene.id}")
            else:
                print(f"❌ Failed to generate animation for scene {scene.id}")
                # Create fallback animation
                rendered_scene = await self._create_fallback_animation(scene, animation_dir)
                if rendered_scene:
                    rendered_scenes.append(rendered_scene)
        
        # Create animation assets
        total_duration = sum(scene.duration for scene in rendered_scenes)
        
        animation_assets = AnimationAssets(
            scenes=rendered_scenes,
            total_duration=total_duration,
            resolution=VideoResolution.from_string(self.resolution)
        )
        
        return animation_assets

    async def _generate_scene_animation(self, scene, output_dir: Path):
        """Generate animation for a single scene."""
        from backend.models.animation import RenderedScene, VideoResolution, RenderStatus
        
        try:
            # Create scene-specific directory
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = scene_dir / f"{scene.id}.mp4"
            
            # Create simple text overlay animation
            success = await self._create_text_overlay_animation(scene, str(video_path))
            
            if not success:
                print(f"  Animation generation failed for scene {scene.id}")
                return None
            
            # Verify video file was created
            if not video_path.exists() or video_path.stat().st_size == 0:
                print(f"  Video file not created or empty for scene {scene.id}")
                return None
            
            # Get actual video duration
            actual_duration = await self._get_video_duration(str(video_path))
            if actual_duration == 0:
                actual_duration = scene.duration
            
            # Create rendered scene
            rendered_scene = RenderedScene(
                scene_id=scene.id,
                file_path=str(video_path),
                duration=actual_duration,
                framework=scene.visual_type,
                resolution=VideoResolution.from_string(self.resolution),
                frame_rate=self.fps,
                status=RenderStatus.COMPLETED
            )
            
            return rendered_scene
            
        except Exception as e:
            print(f"Error generating animation for scene {scene.id}: {e}")
            return None

    async def _create_text_overlay_animation(self, scene, output_path: str) -> bool:
        """Create simple text overlay animation using FFmpeg."""
        try:
            if not self.ffmpeg_available:
                print(f"  FFmpeg not available, skipping animation for {scene.id}")
                return False
            
            # Prepare text for display
            title_text = self._escape_text_for_ffmpeg(scene.title)
            
            # Create FFmpeg command for text overlay
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c={self.background_color}:size={self.resolution}:duration={scene.duration}:rate={self.fps}',
                '-vf', f'drawtext=text=\'{title_text}\':fontsize={self.font_size}:fontcolor={self.text_color}:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-y', output_path
            ]
            
            # Execute FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"  Created text overlay animation for scene {scene.id}")
                return True
            else:
                print(f"  FFmpeg failed for scene {scene.id}: {stderr.decode()}")
                return False
            
        except Exception as e:
            print(f"Text overlay animation failed for scene {scene.id}: {e}")
            return False

    async def _create_fallback_animation(self, scene, output_dir: Path):
        """Create fallback animation when FFmpeg fails."""
        from backend.models.animation import RenderedScene, VideoResolution, RenderStatus
        
        try:
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = scene_dir / f"{scene.id}_fallback.mp4"
            
            # Try to create a simple solid color video
            if self.ffmpeg_available:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', f'color=c={self.background_color}:size={self.resolution}:duration={scene.duration}:rate={self.fps}',
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-y', str(video_path)
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                if process.returncode == 0 and video_path.exists():
                    rendered_scene = RenderedScene(
                        scene_id=scene.id,
                        file_path=str(video_path),
                        duration=scene.duration,
                        framework="fallback",
                        resolution=VideoResolution.from_string(self.resolution),
                        frame_rate=self.fps,
                        status=RenderStatus.COMPLETED
                    )
                    
                    print(f"  Created fallback animation for scene {scene.id}")
                    return rendered_scene
            
            return None
            
        except Exception as e:
            print(f"Failed to create fallback animation for scene {scene.id}: {e}")
            return None

    def _escape_text_for_ffmpeg(self, text: str) -> str:
        """Escape text for FFmpeg drawtext filter."""
        text = text.replace("'", "\\'")
        text = text.replace(":", "\\:")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace(",", "\\,")
        text = text.replace(";", "\\;")
        
        if len(text) > 100:
            text = text[:97] + "..."
        
        return text

    async def _get_video_duration(self, video_path: str) -> float:
        """Get video file duration using ffprobe."""
        try:
            process = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", video_path,
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

    def validate_animation_file(self, file_path: str) -> Dict[str, Any]:
        """Validate an animation file for completeness and quality."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            video_path = Path(file_path)
            
            if not video_path.exists():
                validation["errors"].append("Animation file does not exist")
                validation["valid"] = False
                return validation
            
            file_size = video_path.stat().st_size
            validation["stats"]["file_size_bytes"] = file_size
            
            if file_size == 0:
                validation["errors"].append("Animation file is empty")
                validation["valid"] = False
            elif file_size < 10000:
                validation["warnings"].append("Animation file is very small")
            
            if not file_path.lower().endswith(('.mp4', '.avi', '.mov', '.mkv')):
                validation["warnings"].append("Unusual video file extension")
            
        except Exception as e:
            validation["errors"].append(f"Error validating animation file: {e}")
            validation["valid"] = False
        
        return validation
    async def generate_animation_assets(self, script, output_dir: str):
        """Generate animation assets from a narration script."""
        # Import here to avoid circular imports
        from backend.models.animation import AnimationAssets, RenderedScene, VideoResolution, RenderStatus
        
        # Create output directory
        animation_dir = Path(output_dir) / "animations"
        animation_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate animations for each scene
        rendered_scenes = []
        
        for i, scene in enumerate(script.scenes):
            print(f"Generating animation for scene {i+1}/{len(script.scenes)}: {scene.title}")
            
            rendered_scene = await self._generate_scene_animation(scene, animation_dir)
            
            if rendered_scene:
                rendered_scenes.append(rendered_scene)
                print(f"✅ Animation generated for scene {scene.id}")
            else:
                print(f"❌ Failed to generate animation for scene {scene.id}")
                # Create fallback animation
                rendered_scene = await self._create_fallback_animation(scene, animation_dir)
                if rendered_scene:
                    rendered_scenes.append(rendered_scene)
        
        # Create animation assets
        total_duration = sum(scene.duration for scene in rendered_scenes)
        
        animation_assets = AnimationAssets(
            scenes=rendered_scenes,
            total_duration=total_duration,
            resolution=VideoResolution.from_string(self.resolution)
        )
        
        return animation_assets

    async def _generate_scene_animation(self, scene, output_dir: Path):
        """Generate animation for a single scene."""
        from backend.models.animation import RenderedScene, VideoResolution, RenderStatus
        
        try:
            # Create scene-specific directory
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = scene_dir / f"{scene.id}.mp4"
            
            # Create simple text overlay animation
            success = await self._create_text_overlay_animation(scene, str(video_path))
            
            if not success:
                print(f"  Animation generation failed for scene {scene.id}")
                return None
            
            # Verify video file was created
            if not video_path.exists() or video_path.stat().st_size == 0:
                print(f"  Video file not created or empty for scene {scene.id}")
                return None
            
            # Get actual video duration
            actual_duration = await self._get_video_duration(str(video_path))
            if actual_duration == 0:
                actual_duration = scene.duration
            
            # Create rendered scene
            rendered_scene = RenderedScene(
                scene_id=scene.id,
                file_path=str(video_path),
                duration=actual_duration,
                framework=scene.visual_type,
                resolution=VideoResolution.from_string(self.resolution),
                frame_rate=self.fps,
                status=RenderStatus.COMPLETED
            )
            
            return rendered_scene
            
        except Exception as e:
            print(f"Error generating animation for scene {scene.id}: {e}")
            return None

    async def _create_text_overlay_animation(self, scene, output_path: str) -> bool:
        """Create simple text overlay animation using FFmpeg."""
        try:
            if not self.ffmpeg_available:
                print(f"  FFmpeg not available, skipping animation for {scene.id}")
                return False
            
            # Prepare text for display
            title_text = self._escape_text_for_ffmpeg(scene.title)
            
            # Create FFmpeg command for text overlay
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c={self.background_color}:size={self.resolution}:duration={scene.duration}:rate={self.fps}',
                '-vf', f'drawtext=text=\'{title_text}\':fontsize={self.font_size}:fontcolor={self.text_color}:x=(w-text_w)/2:y=(h-text_h)/2',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-y', output_path
            ]
            
            # Execute FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"  Created text overlay animation for scene {scene.id}")
                return True
            else:
                print(f"  FFmpeg failed for scene {scene.id}: {stderr.decode()}")
                return False
            
        except Exception as e:
            print(f"Text overlay animation failed for scene {scene.id}: {e}")
            return False

    async def _create_fallback_animation(self, scene, output_dir: Path):
        """Create fallback animation when FFmpeg fails."""
        from backend.models.animation import RenderedScene, VideoResolution, RenderStatus
        
        try:
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            video_path = scene_dir / f"{scene.id}_fallback.mp4"
            
            # Try to create a simple solid color video
            if self.ffmpeg_available:
                ffmpeg_cmd = [
                    'ffmpeg',
                    '-f', 'lavfi',
                    '-i', f'color=c={self.background_color}:size={self.resolution}:duration={scene.duration}:rate={self.fps}',
                    '-c:v', 'libx264',
                    '-pix_fmt', 'yuv420p',
                    '-y', str(video_path)
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *ffmpeg_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await process.communicate()
                
                if process.returncode == 0 and video_path.exists():
                    rendered_scene = RenderedScene(
                        scene_id=scene.id,
                        file_path=str(video_path),
                        duration=scene.duration,
                        framework="fallback",
                        resolution=VideoResolution.from_string(self.resolution),
                        frame_rate=self.fps,
                        status=RenderStatus.COMPLETED
                    )
                    
                    print(f"  Created fallback animation for scene {scene.id}")
                    return rendered_scene
            
            return None
            
        except Exception as e:
            print(f"Failed to create fallback animation for scene {scene.id}: {e}")
            return None

    def _escape_text_for_ffmpeg(self, text: str) -> str:
        """Escape text for FFmpeg drawtext filter."""
        text = text.replace("'", "\\'")
        text = text.replace(":", "\\:")
        text = text.replace("[", "\\[")
        text = text.replace("]", "\\]")
        text = text.replace(",", "\\,")
        text = text.replace(";", "\\;")
        
        if len(text) > 100:
            text = text[:97] + "..."
        
        return text

    async def _get_video_duration(self, video_path: str) -> float:
        """Get video file duration using ffprobe."""
        try:
            process = await asyncio.create_subprocess_exec(
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", video_path,
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
    async def create_slide_animation(self, scene, output_path: str) -> bool:
        """Create slide-style animation with text content."""
        try:
            if not self.ffmpeg_available:
                print(f"  FFmpeg not available, skipping slide animation for {scene.id}")
                return False
            
            # Prepare slide content
            title_text = self._escape_text_for_ffmpeg(scene.title)
            
            # Split narration into key points for slides
            narration_lines = self._split_narration_into_slides(scene.narration)
            
            # Create slide transition animation
            ffmpeg_cmd = [
                'ffmpeg',
                '-f', 'lavfi',
                '-i', f'color=c={self.background_color}:size={self.resolution}:duration={scene.duration}:rate={self.fps}',
                '-vf', self._create_slide_filter(title_text, narration_lines, scene.duration),
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-y', output_path
            ]
            
            # Execute FFmpeg command
            process = await asyncio.create_subprocess_exec(
                *ffmpeg_cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0:
                print(f"  Created slide animation for scene {scene.id}")
                return True
            else:
                print(f"  FFmpeg slide animation failed for scene {scene.id}: {stderr.decode()}")
                return False
            
        except Exception as e:
            print(f"Slide animation failed for scene {scene.id}: {e}")
            return False
    
    def _split_narration_into_slides(self, narration: str) -> List[str]:
        """Split narration into key points for slide display."""
        # Split by sentences and group into slides
        sentences = narration.split('. ')
        slides = []
        
        current_slide = ""
        max_chars_per_slide = 120
        
        for sentence in sentences:
            if len(current_slide + sentence) < max_chars_per_slide:
                current_slide += sentence + ". "
            else:
                if current_slide:
                    slides.append(current_slide.strip())
                current_slide = sentence + ". "
        
        if current_slide:
            slides.append(current_slide.strip())
        
        # Ensure we have at least one slide
        if not slides:
            slides = [narration[:max_chars_per_slide] + "..."]
        
        return slides[:4]  # Limit to 4 slides max
    
    def _create_slide_filter(self, title: str, slides: List[str], duration: float) -> str:
        """Create FFmpeg filter for slide transitions."""
        slide_duration = duration / len(slides) if slides else duration
        
        # Create title overlay
        title_filter = f"drawtext=text='{title}':fontsize={self.font_size + 12}:fontcolor={self.text_color}:x=(w-text_w)/2:y=100"
        
        # Create slide content filters with fade transitions
        slide_filters = []
        for i, slide_text in enumerate(slides):
            start_time = i * slide_duration
            end_time = (i + 1) * slide_duration
            
            escaped_text = self._escape_text_for_ffmpeg(slide_text)
            
            slide_filter = (
                f"drawtext=text='{escaped_text}':fontsize={self.font_size - 8}:fontcolor={self.text_color}:"
                f"x=(w-text_w)/2:y=300:enable='between(t,{start_time},{end_time})'"
            )
            slide_filters.append(slide_filter)
        
        # Combine all filters
        all_filters = [title_filter] + slide_filters
        return ",".join(all_filters)
    def validate_animation_duration(self, file_path: str, expected_duration: float) -> Dict[str, Any]:
        """Validate animation duration matches expected duration."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Get actual duration using ffprobe
            import subprocess
            import json
            
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_format", file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                actual_duration = float(info.get("format", {}).get("duration", 0))
                validation["stats"]["actual_duration"] = actual_duration
                validation["stats"]["expected_duration"] = expected_duration
                
                # Check duration match (±2 seconds tolerance)
                duration_diff = abs(actual_duration - expected_duration)
                if duration_diff > 2.0:
                    validation["errors"].append(f"Duration mismatch: expected {expected_duration}s, got {actual_duration}s")
                    validation["valid"] = False
                elif duration_diff > 0.5:
                    validation["warnings"].append(f"Duration slightly off: expected {expected_duration}s, got {actual_duration}s")
            else:
                validation["errors"].append("Could not read video duration")
                validation["valid"] = False
                
        except Exception as e:
            validation["errors"].append(f"Duration validation failed: {e}")
            validation["valid"] = False
        
        return validation
    
    def validate_animation_quality(self, file_path: str) -> Dict[str, Any]:
        """Validate animation quality and properties."""
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {}
        }
        
        try:
            # Get video properties using ffprobe
            import subprocess
            import json
            
            result = subprocess.run([
                "ffprobe", "-v", "quiet", "-print_format", "json",
                "-show_streams", "-show_format", file_path
            ], capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                info = json.loads(result.stdout)
                
                # Check video stream
                video_streams = [s for s in info.get("streams", []) if s.get("codec_type") == "video"]
                if not video_streams:
                    validation["errors"].append("No video stream found")
                    validation["valid"] = False
                    return validation
                
                video_stream = video_streams[0]
                
                # Validate resolution
                width = int(video_stream.get("width", 0))
                height = int(video_stream.get("height", 0))
                validation["stats"]["resolution"] = f"{width}x{height}"
                
                expected_width, expected_height = map(int, self.resolution.split('x'))
                if width != expected_width or height != expected_height:
                    validation["warnings"].append(f"Resolution mismatch: expected {self.resolution}, got {width}x{height}")
                
                # Validate frame rate
                fps_str = video_stream.get("r_frame_rate", "0/1")
                if '/' in fps_str:
                    num, den = map(int, fps_str.split('/'))
                    actual_fps = num / den if den != 0 else 0
                else:
                    actual_fps = float(fps_str)
                
                validation["stats"]["fps"] = actual_fps
                if abs(actual_fps - self.fps) > 1:
                    validation["warnings"].append(f"Frame rate mismatch: expected {self.fps}, got {actual_fps}")
                
                # Validate codec
                codec = video_stream.get("codec_name", "unknown")
                validation["stats"]["codec"] = codec
                if codec not in ["h264", "libx264"]:
                    validation["warnings"].append(f"Unexpected codec: {codec}")
                
            else:
                validation["errors"].append("Could not read video properties")
                validation["valid"] = False
                
        except Exception as e:
            validation["errors"].append(f"Quality validation failed: {e}")
            validation["valid"] = False
        
        return validation
    
    def comprehensive_validation(self, file_path: str, expected_duration: float) -> Dict[str, Any]:
        """Perform comprehensive validation of animation file."""
        # Start with basic file validation
        validation = self.validate_animation_file(file_path)
        
        if not validation["valid"]:
            return validation
        
        # Add duration validation
        duration_validation = self.validate_animation_duration(file_path, expected_duration)
        validation["errors"].extend(duration_validation["errors"])
        validation["warnings"].extend(duration_validation["warnings"])
        validation["stats"].update(duration_validation["stats"])
        
        if not duration_validation["valid"]:
            validation["valid"] = False
        
        # Add quality validation
        quality_validation = self.validate_animation_quality(file_path)
        validation["errors"].extend(quality_validation["errors"])
        validation["warnings"].extend(quality_validation["warnings"])
        validation["stats"].update(quality_validation["stats"])
        
        if not quality_validation["valid"]:
            validation["valid"] = False
        
        return validation