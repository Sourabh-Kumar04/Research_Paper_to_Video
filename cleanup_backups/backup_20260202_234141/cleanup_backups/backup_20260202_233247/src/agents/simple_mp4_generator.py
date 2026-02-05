"""
Simple MP4 Generator using FFmpeg for proper video creation.
Creates real MP4 files that are compatible with video players and FFmpeg processing.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple


class SimpleMp4Generator:
    """Generate real MP4 files using FFmpeg for proper video creation."""
    
    def __init__(self):
        """Initialize the MP4 generator."""
        self.resolution = (1920, 1080)
        self.fps = 30
        self.background_color = (26, 26, 46)  # #1a1a2e
        self.text_color = (255, 255, 255)    # #ffffff
        self.font_size = 48
        
        # Check capabilities
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
            "ffmpeg_available": self.ffmpeg_available,
            "can_generate_video": self.ffmpeg_available,
            "fallback_available": False
        }
    
    def create_text_video(self, title: str, content: str, duration: float, output_path: str) -> bool:
        """Create an MP4 video with text content using FFmpeg."""
        try:
            if not self.ffmpeg_available:
                print(f"  FFmpeg not available for MP4 generation")
                return False
            
            # Create a real MP4 file using FFmpeg
            return self._create_ffmpeg_mp4(title, content, duration, output_path)
            
        except Exception as e:
            print(f"  MP4 video generation failed: {e}")
            return False
    
    def _create_ffmpeg_mp4(self, title: str, content: str, duration: float, output_path: str) -> bool:
        """Create a real MP4 file using FFmpeg."""
        try:
            # Get FFmpeg path
            from utils.video_utils import VideoUtils
            video_utils = VideoUtils()
            ffmpeg_path = video_utils.get_ffmpeg_path() or "ffmpeg"
            
            # Ensure output directory exists
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Truncate content for display
            display_content = content[:80] + "..." if len(content) > 80 else content
            
            # Create FFmpeg command for a proper MP4 video
            cmd = [
                ffmpeg_path,
                "-f", "lavfi",
                "-i", f"color=c=#1a1a2e:size={self.resolution[0]}x{self.resolution[1]}:duration={duration}:rate={self.fps}",
                "-vf", (
                    f"drawtext=text='{title}':fontcolor=white:fontsize=40:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2-60,"
                    f"drawtext=text='Generated Content':fontcolor=gray:fontsize=20:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2+40"
                ),
                "-c:v", "libx264",
                "-pix_fmt", "yuv420p",
                "-preset", "fast",
                "-crf", "23",
                "-movflags", "+faststart",  # Optimize for web playback
                "-y", output_path
            ]
            
            print(f"  Creating real MP4 with FFmpeg...")
            
            # Execute FFmpeg command
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60  # 1 minute timeout
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                file_size = Path(output_path).stat().st_size
                if file_size > 10000:  # At least 10KB for a real video
                    print(f"  ✅ Created real MP4 file: {file_size} bytes")
                    return True
                else:
                    print(f"  ❌ Generated MP4 too small: {file_size} bytes")
                    return False
            else:
                error_msg = result.stderr if result.stderr else "Unknown error"
                print(f"  ❌ FFmpeg MP4 creation failed: {error_msg}")
                return False
            
        except Exception as e:
            print(f"  FFmpeg MP4 creation error: {e}")
            return False