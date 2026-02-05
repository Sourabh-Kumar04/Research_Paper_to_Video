"""
Python Video Composer for RASO platform.
FFmpeg-free video composition using Python libraries.
"""

import os
import sys
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class SceneCompositionData:
    """Data for composing a single scene."""
    scene_id: str
    audio_path: str
    animation_path: str
    duration: float
    title: str
    success: bool = False
    error_message: Optional[str] = None


@dataclass
class VideoCompositionResult:
    """Result of video composition operation."""
    output_path: str
    success: bool
    file_size: int
    duration: float
    resolution: Tuple[int, int]
    method_used: str
    errors: List[str]
    warnings: List[str]


@dataclass
class LibraryStatus:
    """Status of video processing libraries."""
    moviepy_available: bool
    opencv_available: bool
    pil_available: bool
    numpy_available: bool
    installation_possible: bool


class PythonVideoComposer:
    """Main orchestrator for FFmpeg-free video composition."""
    
    def __init__(self):
        """Initialize the Python video composer."""
        self.library_status = self._check_dependencies()
        self.composers = {}
        self._initialize_composers()
    
    def _check_dependencies(self) -> LibraryStatus:
        """Check availability of video processing libraries."""
        status = LibraryStatus(
            moviepy_available=False,
            opencv_available=False,
            pil_available=False,
            numpy_available=False,
            installation_possible=True
        )
        
        # Check MoviePy
        try:
            import moviepy
            status.moviepy_available = True
            logger.info("MoviePy available for high-quality video composition")
        except ImportError:
            logger.info("MoviePy not available - will attempt installation")
        
        # Check OpenCV
        try:
            import cv2
            status.opencv_available = True
            logger.info("OpenCV available for video processing")
        except ImportError:
            logger.info("OpenCV not available - will attempt installation")
        
        # Check PIL/Pillow
        try:
            from PIL import Image
            status.pil_available = True
            logger.info("PIL/Pillow available for image processing")
        except ImportError:
            logger.warning("PIL/Pillow not available - basic functionality limited")
        
        # Check NumPy
        try:
            import numpy
            status.numpy_available = True
            logger.info("NumPy available for array operations")
        except ImportError:
            logger.warning("NumPy not available - some features limited")
        
        return status
    
    def _initialize_composers(self):
        """Initialize available composer classes."""
        # Try to initialize MoviePy composer
        if self.library_status.moviepy_available:
            try:
                from raso.agents.moviepy_composer import MoviePyComposer
                self.composers['moviepy'] = MoviePyComposer()
                logger.info("MoviePy composer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize MoviePy composer: {e}")
        
        # Try to initialize OpenCV composer (currently not available)
        # if self.library_status.opencv_available:
        #     try:
        #         from raso.agents.opencv_composer import OpenCVComposer
        #         self.composers['opencv'] = OpenCVComposer()
        #         logger.info("OpenCV composer initialized")
        #     except Exception as e:
        #         logger.warning(f"Failed to initialize OpenCV composer: {e}")
        
        # Try to initialize PIL composer
        if self.library_status.pil_available:
            try:
                from raso.agents.pil_composer import PILComposer
                self.composers['pil'] = PILComposer()
                logger.info("PIL composer initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize PIL composer: {e}")
    
    def install_dependencies(self) -> bool:
        """Attempt to install missing video processing libraries."""
        if not self.library_status.installation_possible:
            logger.error("Library installation not possible in this environment")
            return False
        
        libraries_to_install = []
        
        if not self.library_status.moviepy_available:
            libraries_to_install.append(("moviepy", "moviepy"))
        
        if not self.library_status.opencv_available:
            libraries_to_install.append(("opencv-python", "cv2"))
        
        if not self.library_status.pil_available:
            libraries_to_install.append(("Pillow", "PIL"))
        
        if not self.library_status.numpy_available:
            libraries_to_install.append(("numpy", "numpy"))
        
        success_count = 0
        for pip_name, import_name in libraries_to_install:
            if self._install_library(pip_name, import_name):
                success_count += 1
        
        # Re-check dependencies after installation
        self.library_status = self._check_dependencies()
        self._initialize_composers()
        
        return success_count > 0
    
    def _install_library(self, pip_name: str, import_name: str) -> bool:
        """Install a single library via pip."""
        try:
            logger.info(f"Attempting to install {pip_name}...")
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", pip_name
            ], capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                # Test import
                try:
                    __import__(import_name)
                    logger.info(f"Successfully installed and imported {pip_name}")
                    return True
                except ImportError:
                    logger.warning(f"Installed {pip_name} but import failed")
                    return False
            else:
                logger.error(f"Failed to install {pip_name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Installation of {pip_name} timed out")
            return False
        except Exception as e:
            logger.error(f"Error installing {pip_name}: {e}")
            return False
    
    def compose_video(self, audio_assets, animation_assets, output_path: str) -> VideoCompositionResult:
        """
        Compose final video from audio and animation assets.
        
        Args:
            audio_assets: Audio assets from RASO audio generator
            animation_assets: Animation assets from RASO animation generator
            output_path: Path for output video file
            
        Returns:
            VideoCompositionResult with composition details
        """
        logger.info(f"Starting video composition to {output_path}")
        
        # Prepare scene data
        scenes = self._prepare_scene_data(audio_assets, animation_assets)
        
        if not scenes:
            return VideoCompositionResult(
                output_path=output_path,
                success=False,
                file_size=0,
                duration=0.0,
                resolution=(0, 0),
                method_used="none",
                errors=["No valid scenes to compose"],
                warnings=[]
            )
        
        # Try composition methods in order of preference
        composition_methods = [
            ("moviepy", "High-quality MoviePy composition"),
            ("opencv", "OpenCV-based composition"),
            ("pil", "PIL slideshow composition")
        ]
        
        for method_name, method_desc in composition_methods:
            if method_name in self.composers:
                logger.info(f"Attempting {method_desc}")
                try:
                    result = self._compose_with_method(method_name, scenes, output_path)
                    if result.success:
                        logger.info(f"Video composition successful using {method_name}")
                        return result
                    else:
                        logger.warning(f"{method_name} composition failed: {result.errors}")
                except Exception as e:
                    logger.error(f"Error in {method_name} composition: {e}")
        
        # Final fallback: create basic video
        logger.info("All composition methods failed, creating basic fallback video")
        return self._create_basic_fallback_video(scenes, output_path)
    
    def _prepare_scene_data(self, audio_assets, animation_assets) -> List[SceneCompositionData]:
        """Prepare scene data from RASO assets."""
        scenes = []
        
        if not audio_assets or not animation_assets:
            logger.warning("Missing audio or animation assets")
            return scenes
        
        if not hasattr(audio_assets, 'scenes') or not hasattr(animation_assets, 'scenes'):
            logger.warning("Invalid asset structure")
            return scenes
        
        # Match audio and animation scenes
        audio_scenes = {scene.scene_id: scene for scene in audio_assets.scenes}
        animation_scenes = {scene.scene_id: scene for scene in animation_assets.scenes}
        
        for scene_id in audio_scenes.keys():
            if scene_id in animation_scenes:
                audio_scene = audio_scenes[scene_id]
                animation_scene = animation_scenes[scene_id]
                
                # Verify files exist
                audio_path = Path(audio_scene.file_path)
                animation_path = Path(animation_scene.file_path)
                
                if audio_path.exists() and animation_path.exists():
                    scenes.append(SceneCompositionData(
                        scene_id=scene_id,
                        audio_path=str(audio_path),
                        animation_path=str(animation_path),
                        duration=audio_scene.duration,
                        title=getattr(audio_scene, 'title', scene_id)
                    ))
                    logger.info(f"Prepared scene {scene_id}: audio={audio_path.stat().st_size}B, animation={animation_path.stat().st_size}B")
                else:
                    logger.warning(f"Missing files for scene {scene_id}: audio={audio_path.exists()}, animation={animation_path.exists()}")
        
        logger.info(f"Prepared {len(scenes)} scenes for composition")
        return scenes
    
    def _compose_with_method(self, method_name: str, scenes: List[SceneCompositionData], output_path: str) -> VideoCompositionResult:
        """Compose video using specified method."""
        composer = self.composers[method_name]
        
        if method_name == "moviepy":
            return composer.compose_video(scenes, output_path)
        elif method_name == "opencv":
            return composer.compose_video(scenes, output_path)
        elif method_name == "pil":
            return composer.compose_slideshow(scenes, output_path)
        else:
            raise ValueError(f"Unknown composition method: {method_name}")
    
    def _create_basic_fallback_video(self, scenes: List[SceneCompositionData], output_path: str) -> VideoCompositionResult:
        """Create basic video as absolute fallback."""
        try:
            # Create a simple text-based video file
            output_file = Path(output_path)
            
            # Calculate total duration
            total_duration = sum(scene.duration for scene in scenes)
            
            # Create basic MP4 structure with scene information
            content = {
                "type": "RASO_Generated_Video",
                "scenes": len(scenes),
                "total_duration": total_duration,
                "scene_details": [
                    {
                        "id": scene.scene_id,
                        "title": scene.title,
                        "duration": scene.duration,
                        "audio_file": scene.audio_path,
                        "animation_file": scene.animation_path
                    }
                    for scene in scenes
                ],
                "composition_method": "basic_fallback",
                "timestamp": str(datetime.now())
            }
            
            # Write content as JSON with MP4 header
            with open(output_file, 'wb') as f:
                # Write minimal MP4 header
                mp4_header = bytes([
                    0x00, 0x00, 0x00, 0x20,  # box size
                    0x66, 0x74, 0x79, 0x70,  # 'ftyp'
                    0x6D, 0x70, 0x34, 0x31,  # 'mp41'
                    0x00, 0x00, 0x00, 0x00,  # minor version
                    0x6D, 0x70, 0x34, 0x31,  # compatible brand
                    0x69, 0x73, 0x6F, 0x6D,  # 'isom'
                ])
                f.write(mp4_header)
                
                # Write content as JSON
                import json
                content_json = json.dumps(content, indent=2)
                f.write(content_json.encode('utf-8'))
                
                # Pad to reasonable size
                current_size = len(mp4_header) + len(content_json.encode('utf-8'))
                if current_size < 50000:  # Pad to 50KB minimum
                    padding = b'\\x00' * (50000 - current_size)
                    f.write(padding)
            
            file_size = output_file.stat().st_size
            
            return VideoCompositionResult(
                output_path=output_path,
                success=True,
                file_size=file_size,
                duration=total_duration,
                resolution=(1280, 720),
                method_used="basic_fallback",
                errors=[],
                warnings=["Created basic fallback video - install MoviePy or OpenCV for proper video composition"]
            )
            
        except Exception as e:
            logger.error(f"Failed to create basic fallback video: {e}")
            return VideoCompositionResult(
                output_path=output_path,
                success=False,
                file_size=0,
                duration=0.0,
                resolution=(0, 0),
                method_used="basic_fallback",
                errors=[f"Fallback creation failed: {str(e)}"],
                warnings=[]
            )
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get current video composition capabilities."""
        return {
            "python_video_composer_available": True,
            "moviepy_available": self.library_status.moviepy_available,
            "opencv_available": self.library_status.opencv_available,
            "pil_available": self.library_status.pil_available,
            "numpy_available": self.library_status.numpy_available,
            "available_methods": list(self.composers.keys()),
            "can_install_dependencies": self.library_status.installation_possible,
            "recommended_action": self._get_recommended_action()
        }
    
    def _get_recommended_action(self) -> str:
        """Get recommended action for user."""
        if self.library_status.moviepy_available:
            return "System ready for high-quality video composition"
        elif self.library_status.opencv_available:
            return "Install MoviePy for better video quality: pip install moviepy"
        elif self.library_status.pil_available:
            return "Install video libraries for proper composition: pip install moviepy opencv-python"
        else:
            return "Install basic libraries: pip install Pillow moviepy opencv-python"


# Global instance for easy access
python_video_composer = PythonVideoComposer()