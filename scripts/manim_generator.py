"""
Manim Code Generator for RASO Platform

This module generates Manim animation code using AI models for mathematical
visualizations, equations, and educational content.
"""

import re
import ast
import tempfile
import subprocess
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import logging

from utils.ai_model_manager import ai_model_manager, ModelType

logger = logging.getLogger(__name__)


@dataclass
class ManimScene:
    """Represents a Manim scene configuration."""
    scene_id: str
    title: str
    content_type: str  # "equation", "diagram", "proof", "concept"
    manim_code: str
    duration: float
    output_path: Optional[str] = None
    render_quality: str = "medium_quality"


class ManimPrompts:
    """Prompt templates for Manim code generation."""
    
    EQUATION_ANIMATION = """
Generate Manim code to animate this mathematical equation or formula:

Equation: {equation}
Context: {context}
Duration: {duration} seconds

Create a Manim scene that:
1. Introduces the equation step by step
2. Highlights key components
3. Shows transformations or derivations if applicable
4. Uses clear, educational animations
5. Includes proper LaTeX formatting

Requirements:
- Use Manim Community Edition syntax
- Scene class should inherit from Scene
- Include proper imports
- Add smooth animations and transitions
- Use appropriate colors and styling
- Duration should be approximately {duration} seconds

Return only the complete Python code, no explanations.
"""
    
    CONCEPT_VISUALIZATION = """
Generate Manim code to visualize this concept:

Concept: {concept}
Description: {description}
Visual Type: {visual_type}
Duration: {duration} seconds

Create a Manim scene that:
1. Introduces the concept clearly
2. Uses appropriate visual metaphors
3. Shows relationships between components
4. Includes smooth transitions
5. Maintains educational clarity

Requirements:
- Use Manim Community Edition syntax
- Scene class should inherit from Scene
- Include proper imports
- Create engaging visual representations
- Use appropriate colors and styling
- Duration should be approximately {duration} seconds

Return only the complete Python code, no explanations.
"""
    
    DIAGRAM_ANIMATION = """
Generate Manim code to create an animated diagram:

Diagram Type: {diagram_type}
Components: {components}
Relationships: {relationships}
Duration: {duration} seconds

Create a Manim scene that:
1. Builds the diagram step by step
2. Shows relationships between components
3. Uses clear labels and annotations
4. Includes smooth animations
5. Maintains visual clarity

Requirements:
- Use Manim Community Edition syntax
- Scene class should inherit from Scene
- Include proper imports
- Create clear, educational diagrams
- Use appropriate colors and styling
- Duration should be approximately {duration} seconds

Return only the complete Python code, no explanations.
"""
    
    CODE_VALIDATION = """
Review this Manim code for correctness and educational quality:

```python
{manim_code}
```

Check for:
1. Syntax errors
2. Manim API compatibility
3. Educational effectiveness
4. Animation timing
5. Visual clarity

Provide specific suggestions for improvement. Keep response under 200 words.
"""


class ManimGenerator:
    """Generates Manim animation code using AI models."""
    
    def __init__(self):
        self.prompts = ManimPrompts()
        self.manim_available = False
        self.manim_path = None
        
    async def initialize(self) -> bool:
        """Initialize Manim generator and check dependencies."""
        try:
            # Check if Manim is installed
            result = await asyncio.create_subprocess_exec(
                "manim", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version_info = stdout.decode().strip()
                logger.info(f"Manim available: {version_info}")
                self.manim_available = True
                self.manim_path = "manim"
                return True
            else:
                logger.warning("Manim not found. Install with: pip install manim")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to initialize Manim: {e}")
            return False
    
    async def generate_equation_animation(
        self,
        equation: str,
        context: str,
        duration: float = 30.0,
        scene_id: str = None
    ) -> Optional[ManimScene]:
        """Generate Manim code for equation animation."""
        try:
            # Get appropriate AI model for code generation
            model = ai_model_manager.get_model_for_task("manim_code")
            if not model:
                logger.error("No suitable AI model available for Manim code generation")
                return None
            
            # Generate prompt
            prompt = self.prompts.EQUATION_ANIMATION.format(
                equation=equation,
                context=context,
                duration=duration
            )
            
            # Generate code using AI model
            manim_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.2,  # Lower temperature for code generation
                max_tokens=2048
            )
            
            if not manim_code:
                logger.error("Failed to generate Manim code")
                return None
            
            # Clean and validate the generated code
            cleaned_code = self._clean_manim_code(manim_code)
            
            if not self._validate_manim_code(cleaned_code):
                logger.warning("Generated Manim code failed validation")
                # Try to fix common issues
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene object
            scene = ManimScene(
                scene_id=scene_id or f"equation_{hash(equation) % 10000}",
                title=f"Equation: {equation[:50]}...",
                content_type="equation",
                manim_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating equation animation: {e}")
            return None
    
    async def generate_concept_visualization(
        self,
        concept: str,
        description: str,
        visual_type: str = "diagram",
        duration: float = 45.0,
        scene_id: str = None
    ) -> Optional[ManimScene]:
        """Generate Manim code for concept visualization."""
        try:
            # Get appropriate AI model
            model = ai_model_manager.get_model_for_task("manim_code")
            if not model:
                logger.error("No suitable AI model available")
                return None
            
            # Generate prompt
            prompt = self.prompts.CONCEPT_VISUALIZATION.format(
                concept=concept,
                description=description,
                visual_type=visual_type,
                duration=duration
            )
            
            # Generate code
            manim_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            if not manim_code:
                return None
            
            # Clean and validate
            cleaned_code = self._clean_manim_code(manim_code)
            
            if not self._validate_manim_code(cleaned_code):
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene
            scene = ManimScene(
                scene_id=scene_id or f"concept_{hash(concept) % 10000}",
                title=f"Concept: {concept}",
                content_type="concept",
                manim_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating concept visualization: {e}")
            return None
    
    async def generate_diagram_animation(
        self,
        diagram_type: str,
        components: List[str],
        relationships: List[str],
        duration: float = 40.0,
        scene_id: str = None
    ) -> Optional[ManimScene]:
        """Generate Manim code for diagram animation."""
        try:
            # Get appropriate AI model
            model = ai_model_manager.get_model_for_task("manim_code")
            if not model:
                return None
            
            # Format components and relationships
            components_text = ", ".join(components)
            relationships_text = "; ".join(relationships)
            
            # Generate prompt
            prompt = self.prompts.DIAGRAM_ANIMATION.format(
                diagram_type=diagram_type,
                components=components_text,
                relationships=relationships_text,
                duration=duration
            )
            
            # Generate code
            manim_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            if not manim_code:
                return None
            
            # Clean and validate
            cleaned_code = self._clean_manim_code(manim_code)
            
            if not self._validate_manim_code(cleaned_code):
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene
            scene = ManimScene(
                scene_id=scene_id or f"diagram_{hash(diagram_type) % 10000}",
                title=f"Diagram: {diagram_type}",
                content_type="diagram",
                manim_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating diagram animation: {e}")
            return None
    
    def _clean_manim_code(self, code: str) -> str:
        """Clean and format Manim code."""
        # Remove markdown code blocks if present
        code = re.sub(r'```python\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        
        # Remove any explanatory text before/after code
        lines = code.split('\n')
        
        # Find the start of actual Python code (imports or class definition)
        start_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('from manim') or 
                stripped.startswith('import manim') or
                stripped.startswith('class ') and 'Scene' in stripped):
                start_idx = i
                break
        
        # Find the end of the class definition
        end_idx = len(lines)
        class_indent = None
        in_class = False
        
        for i in range(start_idx, len(lines)):
            line = lines[i]
            stripped = line.strip()
            
            if stripped.startswith('class ') and 'Scene' in stripped:
                in_class = True
                class_indent = len(line) - len(line.lstrip())
                continue
            
            if in_class and stripped and not line.startswith(' ' * (class_indent + 1)):
                # We've left the class definition
                end_idx = i
                break
        
        # Extract the relevant code
        cleaned_lines = lines[start_idx:end_idx]
        
        # Ensure proper imports
        has_manim_import = any('from manim' in line or 'import manim' in line 
                             for line in cleaned_lines[:5])
        
        if not has_manim_import:
            cleaned_lines.insert(0, "from manim import *")
        
        return '\n'.join(cleaned_lines)
    
    def _validate_manim_code(self, code: str) -> bool:
        """Validate Manim code for syntax and basic structure."""
        try:
            # Check if it's valid Python syntax
            ast.parse(code)
            
            # Check for required Manim elements
            required_elements = [
                'Scene',  # Must inherit from Scene
                'construct',  # Must have construct method
            ]
            
            for element in required_elements:
                if element not in code:
                    logger.warning(f"Missing required element: {element}")
                    return False
            
            # Check for common Manim patterns
            if 'self.play(' not in code and 'self.add(' not in code:
                logger.warning("No Manim animations found")
                return False
            
            return True
            
        except SyntaxError as e:
            logger.warning(f"Syntax error in generated code: {e}")
            return False
        except Exception as e:
            logger.warning(f"Code validation error: {e}")
            return False
    
    def _fix_common_issues(self, code: str) -> str:
        """Fix common issues in generated Manim code."""
        # Ensure proper imports
        if 'from manim import *' not in code and 'import manim' not in code:
            code = "from manim import *\n\n" + code
        
        # Fix class definition if needed
        if 'class ' not in code or 'Scene' not in code:
            # Wrap code in a basic scene class
            code = f"""from manim import *

class GeneratedScene(Scene):
    def construct(self):
{self._indent_code(code, 8)}
"""
        
        # Ensure construct method exists
        if 'def construct(self):' not in code:
            # Find the class and add construct method
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if 'class ' in line and 'Scene' in line:
                    # Insert construct method after class definition
                    lines.insert(i + 1, '    def construct(self):')
                    break
            code = '\n'.join(lines)
        
        return code
    
    def _indent_code(self, code: str, spaces: int) -> str:
        """Indent code by specified number of spaces."""
        lines = code.split('\n')
        indented_lines = [' ' * spaces + line if line.strip() else line for line in lines]
        return '\n'.join(indented_lines)
    
    async def render_scene(
        self,
        scene: ManimScene,
        output_dir: str,
        quality: str = "medium_quality"
    ) -> Optional[str]:
        """Render a Manim scene to video file."""
        if not self.manim_available:
            logger.error("Manim not available for rendering")
            return None
        
        try:
            # Create temporary Python file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
                f.write(scene.manim_code)
                temp_py_file = f.name
            
            # Create output directory
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Render with Manim
            cmd = [
                self.manim_path,
                "-q", quality,  # Quality setting
                "--output_file", f"{scene.scene_id}.mp4",
                "--media_dir", str(output_path),
                temp_py_file
            ]
            
            logger.info(f"Rendering Manim scene: {scene.scene_id}")
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Clean up temporary file
            Path(temp_py_file).unlink()
            
            if process.returncode == 0:
                # Find the output video file
                video_files = list(output_path.rglob(f"{scene.scene_id}.mp4"))
                if video_files:
                    output_file = str(video_files[0])
                    scene.output_path = output_file
                    logger.info(f"Manim scene rendered successfully: {output_file}")
                    return output_file
                else:
                    logger.error("Manim rendering completed but output file not found")
                    return None
            else:
                logger.error(f"Manim rendering failed: {stderr.decode()}")
                return None
                
        except Exception as e:
            logger.error(f"Error rendering Manim scene: {e}")
            return None
    
    async def create_fallback_scene(
        self,
        scene_id: str,
        title: str,
        content: str,
        duration: float = 30.0
    ) -> ManimScene:
        """Create a fallback Manim scene when AI generation fails."""
        fallback_code = f'''from manim import *

class {scene_id.replace("-", "_").title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{title}", font_size=48)
        title.to_edge(UP)
        
        # Content
        content = Text(
            "{content[:100]}...",
            font_size=24,
            line_spacing=1.5
        )
        content.next_to(title, DOWN, buff=1)
        
        # Animations
        self.play(Write(title))
        self.wait(1)
        self.play(Write(content))
        self.wait({duration - 3})
        self.play(FadeOut(title), FadeOut(content))
'''
        
        return ManimScene(
            scene_id=scene_id,
            title=title,
            content_type="fallback",
            manim_code=fallback_code,
            duration=duration
        )
    
    def get_quality_settings(self) -> Dict[str, str]:
        """Get available Manim quality settings."""
        return {
            "low_quality": "480p15",
            "medium_quality": "720p30", 
            "high_quality": "1080p60",
            "production_quality": "1080p60"
        }
    
    async def validate_scene_code(self, scene: ManimScene) -> List[str]:
        """Validate Manim scene code and return issues."""
        issues = []
        
        # Basic syntax check
        try:
            ast.parse(scene.manim_code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
        
        # Check for required elements
        code = scene.manim_code
        
        if 'from manim' not in code and 'import manim' not in code:
            issues.append("Missing Manim imports")
        
        if 'class ' not in code or 'Scene' not in code:
            issues.append("Missing Scene class definition")
        
        if 'def construct(self):' not in code:
            issues.append("Missing construct method")
        
        if 'self.play(' not in code and 'self.add(' not in code:
            issues.append("No Manim animations found")
        
        # Check for common issues
        if 'self.wait(' not in code:
            issues.append("Consider adding wait() calls for better pacing")
        
        # Estimate duration
        play_count = code.count('self.play(')
        wait_matches = re.findall(r'self\.wait\(([^)]*)\)', code)
        
        estimated_duration = play_count * 2  # Assume 2 seconds per play
        for wait_match in wait_matches:
            try:
                if wait_match.strip():
                    estimated_duration += float(wait_match.strip())
                else:
                    estimated_duration += 1  # Default wait
            except ValueError:
                estimated_duration += 1
        
        if abs(estimated_duration - scene.duration) > scene.duration * 0.3:
            issues.append(f"Duration mismatch: estimated {estimated_duration:.1f}s, target {scene.duration:.1f}s")
        
        return issues


# Global instance for easy access
manim_generator = ManimGenerator()