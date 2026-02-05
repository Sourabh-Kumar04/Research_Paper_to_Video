"""
Professional Video Generator for RASO Platform
Creates broadcast-quality videos with cinematic features, Manim animations, and professional styling.
"""

import os
import sys
import subprocess
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import asyncio
import logging

logger = logging.getLogger(__name__)

class ProfessionalVideoGenerator:
    """Generate professional, broadcast-quality videos with cinematic features."""
    
    def __init__(self):
        """Initialize professional video generator."""
        self.resolution = (1920, 1080)
        self.fps = 24  # Cinematic frame rate
        self.font_path = self._find_font()
        
        # Professional color schemes
        self.color_schemes = {
            "professional": {
                "background": "#0a0e27",
                "primary": "#ffffff",
                "accent": "#00d9ff",
                "secondary": "#ff006e",
                "text": "#e8e8e8"
            },
            "academic": {
                "background": "#1a1a2e",
                "primary": "#eee",
                "accent": "#4CAF50",
                "secondary": "#2196F3",
                "text": "#ddd"
            },
            "cinematic": {
                "background": "#0d1117",
                "primary": "#f0f6fc",
                "accent": "#58a6ff",
                "secondary": "#8b949e",
                "text": "#c9d1d9"
            }
        }
        
    def _find_font(self) -> Optional[str]:
        """Find a suitable font for text rendering."""
        # Common font locations
        possible_fonts = [
            "C:\\Windows\\Fonts\\Arial.ttf",
            "C:\\Windows\\Fonts\\calibri.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "Arial", "Helvetica", "DejaVu Sans"
        ]
        
        for font in possible_fonts:
            if Path(font).exists() if font.endswith('.ttf') or font.endswith('.ttc') else True:
                return font
        
        return None
    
    async def create_professional_video(
        self,
        scene_data: Dict[str, Any],
        output_path: str,
        style: str = "cinematic"
    ) -> bool:
        """
        Create a professional video scene with cinematic features.
        
        Args:
            scene_data: Scene information including title, narration, visuals, etc.
            output_path: Path to save the video
            style: Visual style (professional, academic, cinematic)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Creating professional video: {scene_data.get('title', 'Untitled')}")
            
            # Get color scheme
            colors = self.color_schemes.get(style, self.color_schemes["cinematic"])
            
            # Extract scene information
            title = scene_data.get('title', 'Untitled Scene')
            narration = scene_data.get('narration', '')
            duration = float(scene_data.get('duration', 10.0))
            visual_type = scene_data.get('visual_type', 'text')
            
            # Create video based on visual type
            if visual_type == "manim" and scene_data.get('equations'):
                success = await self._create_manim_video(scene_data, output_path, colors)
            elif visual_type == "diagram":
                success = await self._create_diagram_video(scene_data, output_path, colors)
            else:
                success = await self._create_cinematic_text_video(scene_data, output_path, colors)
            
            if success:
                logger.info(f"✅ Professional video created: {output_path}")
            else:
                logger.error(f"❌ Failed to create professional video")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating professional video: {e}")
            return False
    
    async def _create_cinematic_text_video(
        self,
        scene_data: Dict[str, Any],
        output_path: str,
        colors: Dict[str, str]
    ) -> bool:
        """Create a cinematic text-based video with professional styling."""
        try:
            title = scene_data.get('title', 'Untitled')
            narration = scene_data.get('narration', '')
            duration = float(scene_data.get('duration', 10.0))
            
            # Sanitize text for FFmpeg
            def sanitize(text: str) -> str:
                return (text.replace("\\", "\\\\")
                       .replace("'", "\\'")
                       .replace('"', '\\"')
                       .replace(':', '\\:')
                       .replace('[', '\\[')
                       .replace(']', '\\]'))
            
            clean_title = sanitize(title)
            clean_narration = sanitize(narration[:300])  # Limit length
            
            # Split narration into lines for better readability
            narration_lines = self._split_text_into_lines(narration, max_length=60)
            
            # Build FFmpeg filter complex for cinematic effects
            filters = []
            
            # 1. Base layer with gradient background
            filters.append(
                f"color=c={colors['background']}:size={self.resolution[0]}x{self.resolution[1]}:"
                f"duration={duration}:rate={self.fps}[bg]"
            )
            
            # 2. Add film grain for cinematic look
            filters.append(
                "[bg]noise=alls=20:allf=t+u,format=yuv420p[grain]"
            )
            
            # 3. Title with fade in/out and glow effect
            title_start = 0.5
            title_end = min(3.0, duration - 0.5)
            
            # Font setup
            font_str = f":fontfile={self.font_path}" if self.font_path and Path(self.font_path).exists() else ""
            
            # Main title (large, centered)
            filters.append(
                f"[grain]drawtext=text='{clean_title}':"
                f"fontcolor={colors['primary']}:fontsize=72{font_str}:"
                f"x=(w-text_w)/2:y=200:"
                f"alpha='if(lt(t,{title_start}),0,if(lt(t,{title_start+0.5}),(t-{title_start})*2,if(lt(t,{title_end}),1,if(lt(t,{title_end+0.5}),2-2*(t-{title_end}),0))))':"
                f"shadowcolor=black@0.5:shadowx=4:shadowy=4[title]"
            )
            
            # 4. Subtitle (category/type)
            filters.append(
                f"[title]drawtext=text='Research Paper Analysis':"
                f"fontcolor={colors['accent']}:fontsize=28{font_str}:"
                f"x=(w-text_w)/2:y=300:"
                f"alpha='if(lt(t,{title_start+0.3}),0,if(lt(t,{title_start+0.8}),(t-{title_start-0.3})*2,1))'[subtitle]"
            )
            
            # 5. Content narration (appears after title)
            content_start = 3.5
            if len(narration_lines) > 0:
                y_pos = 450
                current_filter = "subtitle"
                for i, line in enumerate(narration_lines[:5]):  # Max 5 lines
                    clean_line = sanitize(line)
                    line_start = content_start + (i * 0.2)
                    next_filter = f"text{i}"
                    
                    filters.append(
                        f"[{current_filter}]drawtext=text='{clean_line}':"
                        f"fontcolor={colors['text']}:fontsize=32{font_str}:"
                        f"x=(w-text_w)/2:y={y_pos}:"
                        f"alpha='if(lt(t,{line_start}),0,if(lt(t,{line_start+0.3}),(t-{line_start})*3.3,1))'[{next_filter}]"
                    )
                    
                    current_filter = next_filter
                    y_pos += 50
                
                final_filter = current_filter
            else:
                final_filter = "subtitle"
            
            # 6. Add decorative elements (progress bar, timestamp)
            filters.append(
                f"[{final_filter}]drawbox=x=100:y=900:w=(w-200)*t/{duration}:h=4:"
                f"color={colors['accent']}:t=fill[progress]"
            )
            
            # 7. Timestamp (bottom right)
            filters.append(
                f"[progress]drawtext=text='Duration\\: {duration:.1f}s':"
                f"fontcolor={colors['secondary']}:fontsize=20{font_str}:"
                f"x=w-250:y=h-50[final]"
            )
            
            # Combine all filters
            filter_complex = ";".join(filters)
            
            # Build FFmpeg command
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", "anullsrc=channel_layout=stereo:sample_rate=48000",
                "-filter_complex", filter_complex,
                "-map", "[final]",
                "-map", "0:a",
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "18",  # High quality
                "-pix_fmt", "yuv420p",
                "-c:a", "aac",
                "-b:a", "192k",
                "-t", str(duration),
                "-movflags", "+faststart",
                "-y",
                output_path
            ]
            
            logger.info("Generating cinematic video with FFmpeg...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=180
            )
            
            if result.returncode == 0 and Path(output_path).exists():
                size = Path(output_path).stat().st_size
                if size > 100000:  # At least 100KB
                    logger.info(f"✅ Cinematic video created: {size} bytes")
                    return True
            
            logger.error(f"FFmpeg failed: {result.stderr[:500]}")
            return False
            
        except Exception as e:
            logger.error(f"Error creating cinematic text video: {e}")
            return False
    
    async def _create_manim_video(
        self,
        scene_data: Dict[str, Any],
        output_path: str,
        colors: Dict[str, str]
    ) -> bool:
        """Create a video with Manim animations for equations and mathematical content."""
        try:
            logger.info("Creating Manim animation video...")
            
            # Check if Manim is available
            try:
                subprocess.run(["manim", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Manim not available, falling back to text video")
                return await self._create_cinematic_text_video(scene_data, output_path, colors)
            
            # Generate Manim script
            manim_script = self._generate_manim_script(scene_data, colors)
            
            # Create temporary file for Manim script
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(manim_script)
                script_path = f.name
            
            try:
                # Run Manim to generate video
                temp_output = tempfile.mkdtemp()
                cmd = [
                    "manim",
                    script_path,
                    "ProfessionalScene",
                    "-qh",  # High quality
                    "--format=mp4",
                    f"--output_file={Path(output_path).name}",
                    f"--media_dir={temp_output}"
                ]
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Find generated video
                if result.returncode == 0:
                    generated_files = list(Path(temp_output).rglob("*.mp4"))
                    if generated_files:
                        # Copy to output path
                        import shutil
                        shutil.copy2(generated_files[0], output_path)
                        logger.info(f"✅ Manim video created successfully")
                        return True
                
                logger.error(f"Manim generation failed: {result.stderr[:500]}")
                return False
                
            finally:
                # Cleanup
                Path(script_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Error creating Manim video: {e}")
            return False
    
    async def _create_diagram_video(
        self,
        scene_data: Dict[str, Any],
        output_path: str,
        colors: Dict[str, str]
    ) -> bool:
        """Create a video with diagrams and visual explanations."""
        try:
            logger.info("Creating diagram video...")
            
            # For now, create an enhanced text video with diagram placeholders
            # TODO: Integrate actual diagram generation
            return await self._create_cinematic_text_video(scene_data, output_path, colors)
            
        except Exception as e:
            logger.error(f"Error creating diagram video: {e}")
            return False
    
    def _split_text_into_lines(self, text: str, max_length: int = 60) -> List[str]:
        """Split text into lines with maximum length."""
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        
        for word in words:
            if current_length + len(word) + 1 <= max_length:
                current_line.append(word)
                current_length += len(word) + 1
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
                current_length = len(word)
        
        if current_line:
            lines.append(' '.join(current_line))
        
        return lines
    
    def _generate_manim_script(self, scene_data: Dict[str, Any], colors: Dict[str, str]) -> str:
        """Generate Manim Python script for the scene."""
        title = scene_data.get('title', 'Untitled')
        equations = scene_data.get('equations', [])
        
        # Convert hex colors to RGB for Manim
        def hex_to_rgb(hex_color: str) -> str:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16)/255 for i in (0, 2, 4))
            return f"rgb({r:.2f}, {g:.2f}, {b:.2f})"
        
        script = f"""
from manim import *

class ProfessionalScene(Scene):
    def construct(self):
        # Set background color
        self.camera.background_color = "{colors['background']}"
        
        # Title
        title = Text("{title}", font_size=60, color="{colors['primary']}")
        title.to_edge(UP, buff=0.5)
        
        self.play(Write(title), run_time=1.5)
        self.wait(0.5)
        
        # Equations or content
"""
        
        if equations:
            for i, eq in enumerate(equations[:3]):  # Max 3 equations
                eq_latex = eq if isinstance(eq, str) else eq.get('latex', 'E=mc^2')
                script += f"""
        # Equation {i+1}
        equation{i} = MathTex(r"{eq_latex}", font_size=48, color="{colors['accent']}")
        equation{i}.next_to(title, DOWN, buff=1.0 + {i}*1.5)
        
        self.play(Write(equation{i}), run_time=2)
        self.wait(1)
"""
        else:
            script += f"""
        # Content text
        content = Text("Mathematical content and diagrams", font_size=36, color="{colors['text']}")
        content.next_to(title, DOWN, buff=2)
        
        self.play(FadeIn(content), run_time=1.5)
        self.wait(2)
"""
        
        script += """
        # Fade out
        self.play(*[FadeOut(mob) for mob in self.mobjects], run_time=1)
        self.wait(0.5)
"""
        
        return script


# Integration function for use in existing pipeline
async def create_professional_scene_video(
    scene_data: Dict[str, Any],
    output_path: str,
    style: str = "cinematic"
) -> bool:
    """
    Create a professional video scene.
    
    Args:
        scene_data: Scene information
        output_path: Output video path
        style: Visual style (professional, academic, cinematic)
        
    Returns:
        True if successful
    """
    generator = ProfessionalVideoGenerator()
    return await generator.create_professional_video(scene_data, output_path, style)
