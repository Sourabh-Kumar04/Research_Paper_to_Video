"""
Python-based Video Generator for RASO platform.
Creates real video files using FFmpeg for proper MP4 generation.
"""

import os
import sys
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import subprocess
import asyncio

try:
    from PIL import Image, ImageDraw, ImageFont
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class PythonVideoGenerator:
    """Generate real video files using FFmpeg for proper MP4 generation."""
    
    def __init__(self):
        """Initialize the Python video generator."""
        self.resolution = (1920, 1080)
        self.fps = 30
        self.background_color = (26, 26, 46)  # #1a1a2e
        self.text_color = (255, 255, 255)    # #ffffff
        self.font_size = 48
        
        # Check capabilities
        self.pil_available = PIL_AVAILABLE
        self.ffmpeg_available = self._check_ffmpeg_availability()
        
    def _check_ffmpeg_availability(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            # Try to get FFmpeg path from video utils
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            return video_utils.is_ffmpeg_available()
        except:
            # Fallback: try direct FFmpeg call
            try:
                result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=5)
                return result.returncode == 0
            except:
                return False
        
    def get_capabilities(self) -> Dict[str, bool]:
        """Get video generation capabilities."""
        return {
            "pil_available": self.pil_available,
            "ffmpeg_available": self.ffmpeg_available,
            "can_generate_video": self.ffmpeg_available,
            "fallback_available": True
        }
    
    def create_text_video(self, title: str, content: str, duration: float, output_path: str) -> bool:
        """Create a video with text content using FFmpeg for proper MP4 generation."""
        try:
            if not self.ffmpeg_available:
                print(f"    FFmpeg not available for video generation")
                return False
            
            print(f"    Creating real MP4 video for: {title}")
            return self._create_ffmpeg_text_video(title, content, duration, output_path)
            
        except Exception as e:
            print(f"  Python video generation failed: {e}")
            return False
    
    def _create_ffmpeg_text_video(self, title: str, content: str, duration: float, output_path: str) -> bool:
        """Create a real MP4 video using FFmpeg with enhanced text overlay."""
        try:
            # Get FFmpeg path
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path() or "ffmpeg"
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Truncate content for display (avoid overly long text)
            display_content = content[:200] + "..." if len(content) > 200 else content
            # Clean content for FFmpeg (escape special characters including colons)
            # For FFmpeg drawtext, we need to escape: ' " : \ [ ]
            clean_title = title.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace(':', '\\:').replace('[', '\\[').replace(']', '\\]')
            clean_content = display_content.replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace(':', '\\:').replace('[', '\\[').replace(']', '\\]')
            
            # Create enhanced FFmpeg command for professional-looking video
            cmd = [
                ffmpeg_path,
                "-f", "lavfi",
                "-i", f"color=c=#1a1a2e:size={self.resolution[0]}x{self.resolution[1]}:duration={duration}:rate={self.fps}",
                "-vf", (
                    # Main title
                    f"drawtext=text='{clean_title}':fontcolor=white:fontsize=56:"
                    f"x=(w-text_w)/2:y=150:enable='between(t,0,{duration})',"
                    # Subtitle
                    f"drawtext=text='Research Paper Explanation':fontcolor=#4CAF50:fontsize=28:"
                    f"x=(w-text_w)/2:y=220:enable='between(t,0,{duration})',"
                    # Content preview (first part)
                    f"drawtext=text='{clean_content[:100]}':fontcolor=#E0E0E0:fontsize=24:"
                    f"x=(w-text_w)/2:y=400:enable='between(t,1,{duration})',"
                    # Duration indicator
                    f"drawtext=text='Duration\\: {duration:.1f} seconds':fontcolor=#888888:fontsize=20:"
                    f"x=(w-text_w)/2:y=600:enable='between(t,0,{duration})',"
                    # Progress bar background
                    f"drawbox=x=460:y=700:w=1000:h=8:color=#333333:enable='between(t,0,{duration})',"
                    # Progress bar (animated)
                    f"drawbox=x=460:y=700:w=1000*t/{duration}:h=8:color=#4CAF50:enable='between(t,0,{duration})'"
                ),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "medium",  # Better quality than "fast"
                "-crf", "20",  # Higher quality (lower CRF)
                "-movflags", "+faststart",  # Optimize for streaming
                "-y", output_path
            ]
            
            print(f"    Running enhanced FFmpeg command for professional video generation...")
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120  # 2 minute timeout for better quality
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                if file_size > 50000:  # At least 50KB for a real video
                    print(f"    ✅ Created enhanced MP4 video: {file_size} bytes")
                    return True
                else:
                    print(f"    ❌ Generated video too small: {file_size} bytes")
                    return False
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"    ❌ FFmpeg video generation failed: {error_msg}")
                return False
            
        except Exception as e:
            print(f"    Enhanced FFmpeg video creation failed: {e}")
            return False