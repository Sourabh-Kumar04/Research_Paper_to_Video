"""
Motion Canvas Generator for RASO Platform

This module generates Motion Canvas animation code using AI models for
concept visualizations, diagrams, and educational content.
"""

import re
import json
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
class MotionCanvasScene:
    """Represents a Motion Canvas scene configuration."""
    scene_id: str
    title: str
    content_type: str  # "concept", "diagram", "flowchart", "process"
    typescript_code: str
    duration: float
    output_path: Optional[str] = None
    resolution: str = "1920x1080"


class MotionCanvasPrompts:
    """Prompt templates for Motion Canvas code generation."""
    
    CONCEPT_VISUALIZATION = """
Generate Motion Canvas TypeScript code to visualize this concept:

Concept: {concept}
Description: {description}
Duration: {duration} seconds

Create a Motion Canvas scene that:
1. Introduces the concept with clear visuals
2. Uses appropriate shapes, colors, and animations
3. Shows relationships between components
4. Includes smooth transitions and effects
5. Maintains educational clarity

Requirements:
- Use Motion Canvas TypeScript syntax
- Import necessary components from @motion-canvas/2d
- Create a scene function that yields animations
- Use appropriate timing and easing
- Include clear visual hierarchy
- Duration should be approximately {duration} seconds

Return only the complete TypeScript code, no explanations.
"""
    
    FLOWCHART_ANIMATION = """
Generate Motion Canvas TypeScript code for an animated flowchart:

Process: {process_name}
Steps: {steps}
Connections: {connections}
Duration: {duration} seconds

Create a Motion Canvas scene that:
1. Builds the flowchart step by step
2. Shows the flow between steps clearly
3. Uses appropriate shapes and arrows
4. Includes smooth animations
5. Highlights the process flow

Requirements:
- Use Motion Canvas TypeScript syntax
- Import Rect, Circle, Line, Txt from @motion-canvas/2d
- Create animated flowchart elements
- Use appropriate colors and styling
- Show clear directional flow
- Duration should be approximately {duration} seconds

Return only the complete TypeScript code, no explanations.
"""
    
    DIAGRAM_ANIMATION = """
Generate Motion Canvas TypeScript code for an animated diagram:

Diagram Type: {diagram_type}
Components: {components}
Layout: {layout}
Duration: {duration} seconds

Create a Motion Canvas scene that:
1. Builds the diagram progressively
2. Shows relationships between components
3. Uses clear labels and annotations
4. Includes engaging animations
5. Maintains visual clarity

Requirements:
- Use Motion Canvas TypeScript syntax
- Import necessary components from @motion-canvas/2d
- Create clear, educational diagrams
- Use appropriate colors and fonts
- Include smooth transitions
- Duration should be approximately {duration} seconds

Return only the complete TypeScript code, no explanations.
"""


class MotionCanvasGenerator:
    """Generates Motion Canvas animation code using AI models."""
    
    def __init__(self):
        self.prompts = MotionCanvasPrompts()
        self.motion_canvas_available = False
        self.node_available = False
        
    async def initialize(self) -> bool:
        """Initialize Motion Canvas generator and check dependencies."""
        try:
            # Check if Node.js is available
            result = await asyncio.create_subprocess_exec(
                "node", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                node_version = stdout.decode().strip()
                logger.info(f"Node.js available: {node_version}")
                self.node_available = True
                
                # Check if Motion Canvas is available globally or can be installed
                await self._check_motion_canvas()
                return True
            else:
                logger.warning("Node.js not found. Install Node.js for Motion Canvas support.")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to initialize Motion Canvas: {e}")
            return False
    
    async def _check_motion_canvas(self) -> None:
        """Check if Motion Canvas is available."""
        try:
            # Try to check if @motion-canvas/cli is available
            result = await asyncio.create_subprocess_exec(
                "npx", "@motion-canvas/cli", "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode == 0:
                version = stdout.decode().strip()
                logger.info(f"Motion Canvas CLI available: {version}")
                self.motion_canvas_available = True
            else:
                logger.info("Motion Canvas CLI not found. Will install when needed.")
                self.motion_canvas_available = False
                
        except Exception as e:
            logger.warning(f"Failed to check Motion Canvas CLI: {e}")
            self.motion_canvas_available = False
    
    async def generate_concept_visualization(
        self,
        concept: str,
        description: str,
        duration: float = 30.0,
        scene_id: str = None
    ) -> Optional[MotionCanvasScene]:
        """Generate Motion Canvas code for concept visualization."""
        try:
            # Get appropriate AI model for code generation
            model = ai_model_manager.get_model_for_task("code_generation")
            if not model:
                logger.error("No suitable AI model available for Motion Canvas code generation")
                return None
            
            # Generate prompt
            prompt = self.prompts.CONCEPT_VISUALIZATION.format(
                concept=concept,
                description=description,
                duration=duration
            )
            
            # Generate code using AI model
            typescript_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.2,  # Lower temperature for code generation
                max_tokens=2048
            )
            
            if not typescript_code:
                logger.error("Failed to generate Motion Canvas code")
                return None
            
            # Clean and validate the generated code
            cleaned_code = self._clean_typescript_code(typescript_code)
            
            if not self._validate_motion_canvas_code(cleaned_code):
                logger.warning("Generated Motion Canvas code failed validation")
                # Try to fix common issues
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene object
            scene = MotionCanvasScene(
                scene_id=scene_id or f"concept_{hash(concept) % 10000}",
                title=f"Concept: {concept}",
                content_type="concept",
                typescript_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating concept visualization: {e}")
            return None
    
    async def generate_flowchart_animation(
        self,
        process_name: str,
        steps: List[str],
        connections: List[Tuple[str, str]],
        duration: float = 45.0,
        scene_id: str = None
    ) -> Optional[MotionCanvasScene]:
        """Generate Motion Canvas code for flowchart animation."""
        try:
            # Get appropriate AI model
            model = ai_model_manager.get_model_for_task("code_generation")
            if not model:
                return None
            
            # Format steps and connections
            steps_text = ", ".join(f'"{step}"' for step in steps)
            connections_text = ", ".join(f'"{conn[0]}" -> "{conn[1]}"' for conn in connections)
            
            # Generate prompt
            prompt = self.prompts.FLOWCHART_ANIMATION.format(
                process_name=process_name,
                steps=steps_text,
                connections=connections_text,
                duration=duration
            )
            
            # Generate code
            typescript_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            if not typescript_code:
                return None
            
            # Clean and validate
            cleaned_code = self._clean_typescript_code(typescript_code)
            
            if not self._validate_motion_canvas_code(cleaned_code):
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene
            scene = MotionCanvasScene(
                scene_id=scene_id or f"flowchart_{hash(process_name) % 10000}",
                title=f"Process: {process_name}",
                content_type="flowchart",
                typescript_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating flowchart animation: {e}")
            return None
    
    async def generate_diagram_animation(
        self,
        diagram_type: str,
        components: List[str],
        layout: str = "hierarchical",
        duration: float = 40.0,
        scene_id: str = None
    ) -> Optional[MotionCanvasScene]:
        """Generate Motion Canvas code for diagram animation."""
        try:
            # Get appropriate AI model
            model = ai_model_manager.get_model_for_task("code_generation")
            if not model:
                return None
            
            # Format components
            components_text = ", ".join(f'"{comp}"' for comp in components)
            
            # Generate prompt
            prompt = self.prompts.DIAGRAM_ANIMATION.format(
                diagram_type=diagram_type,
                components=components_text,
                layout=layout,
                duration=duration
            )
            
            # Generate code
            typescript_code = await ai_model_manager.generate_with_model(
                model_info=model,
                prompt=prompt,
                temperature=0.3,
                max_tokens=2048
            )
            
            if not typescript_code:
                return None
            
            # Clean and validate
            cleaned_code = self._clean_typescript_code(typescript_code)
            
            if not self._validate_motion_canvas_code(cleaned_code):
                cleaned_code = self._fix_common_issues(cleaned_code)
            
            # Create scene
            scene = MotionCanvasScene(
                scene_id=scene_id or f"diagram_{hash(diagram_type) % 10000}",
                title=f"Diagram: {diagram_type}",
                content_type="diagram",
                typescript_code=cleaned_code,
                duration=duration
            )
            
            return scene
            
        except Exception as e:
            logger.error(f"Error generating diagram animation: {e}")
            return None
    
    def _clean_typescript_code(self, code: str) -> str:
        """Clean and format TypeScript code."""
        # Remove markdown code blocks if present
        code = re.sub(r'```typescript\s*', '', code)
        code = re.sub(r'```ts\s*', '', code)
        code = re.sub(r'```\s*$', '', code)
        
        # Remove any explanatory text before/after code
        lines = code.split('\n')
        
        # Find the start of actual TypeScript code (imports or function definition)
        start_idx = 0
        for i, line in enumerate(lines):
            stripped = line.strip()
            if (stripped.startswith('import ') or 
                stripped.startswith('export ') or
                stripped.startswith('function*') or
                'yield*' in stripped):
                start_idx = i
                break
        
        # Extract the relevant code
        cleaned_lines = lines[start_idx:]
        
        # Ensure proper imports
        has_motion_canvas_import = any('@motion-canvas' in line for line in cleaned_lines[:10])
        
        if not has_motion_canvas_import:
            # Add basic imports
            import_lines = [
                "import { makeScene2D } from '@motion-canvas/2d/lib/scenes';",
                "import { Rect, Txt, Circle, Line } from '@motion-canvas/2d/lib/components';",
                "import { all, waitFor } from '@motion-canvas/core/lib/flow';",
                "import { createRef } from '@motion-canvas/core/lib/utils';",
                "",
            ]
            cleaned_lines = import_lines + cleaned_lines
        
        return '\n'.join(cleaned_lines)
    
    def _validate_motion_canvas_code(self, code: str) -> bool:
        """Validate Motion Canvas TypeScript code for basic structure."""
        try:
            # Check for required Motion Canvas elements
            required_elements = [
                '@motion-canvas',  # Must import Motion Canvas
                'makeScene2D',     # Must create a scene
                'yield',           # Must have generator function with yields
            ]
            
            for element in required_elements:
                if element not in code:
                    logger.warning(f"Missing required element: {element}")
                    return False
            
            # Check for common Motion Canvas patterns
            if 'function*' not in code and 'yield*' not in code:
                logger.warning("No generator function found")
                return False
            
            return True
            
        except Exception as e:
            logger.warning(f"Code validation error: {e}")
            return False
    
    def _fix_common_issues(self, code: str) -> str:
        """Fix common issues in generated Motion Canvas code."""
        # Ensure proper imports
        if '@motion-canvas' not in code:
            imports = """import { makeScene2D } from '@motion-canvas/2d/lib/scenes';
import { Rect, Txt, Circle, Line } from '@motion-canvas/2d/lib/components';
import { all, waitFor } from '@motion-canvas/core/lib/flow';
import { createRef } from '@motion-canvas/core/lib/utils';

"""
            code = imports + code
        
        # Ensure export default scene
        if 'export default' not in code:
            # Find the scene function and make it default export
            lines = code.split('\n')
            for i, line in enumerate(lines):
                if 'makeScene2D(' in line:
                    if not line.strip().startswith('export default'):
                        lines[i] = 'export default ' + line.strip()
                    break
            code = '\n'.join(lines)
        
        return code
    
    async def render_scene(
        self,
        scene: MotionCanvasScene,
        output_dir: str,
        quality: str = "1080p"
    ) -> Optional[str]:
        """Render a Motion Canvas scene to video file."""
        if not self.node_available:
            logger.error("Node.js not available for Motion Canvas rendering")
            return None
        
        try:
            # Create temporary project directory
            with tempfile.TemporaryDirectory() as temp_dir:
                project_dir = Path(temp_dir) / "motion_canvas_project"
                project_dir.mkdir()
                
                # Create package.json
                package_json = {
                    "name": "raso-motion-canvas",
                    "version": "1.0.0",
                    "type": "module",
                    "scripts": {
                        "render": "motion-canvas render scene.ts --output output.mp4"
                    },
                    "dependencies": {
                        "@motion-canvas/core": "^3.15.1",
                        "@motion-canvas/2d": "^3.15.1",
                        "@motion-canvas/cli": "^3.15.1"
                    }
                }
                
                with open(project_dir / "package.json", 'w') as f:
                    json.dump(package_json, f, indent=2)
                
                # Create TypeScript scene file
                scene_file = project_dir / "scene.ts"
                with open(scene_file, 'w') as f:
                    f.write(scene.typescript_code)
                
                # Install dependencies
                logger.info("Installing Motion Canvas dependencies...")
                install_process = await asyncio.create_subprocess_exec(
                    "npm", "install",
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                await install_process.communicate()
                
                if install_process.returncode != 0:
                    logger.error("Failed to install Motion Canvas dependencies")
                    return None
                
                # Render the scene
                logger.info(f"Rendering Motion Canvas scene: {scene.scene_id}")
                
                render_process = await asyncio.create_subprocess_exec(
                    "npx", "@motion-canvas/cli", "render", "scene.ts",
                    "--output", f"{scene.scene_id}.mp4",
                    "--quality", quality,
                    cwd=project_dir,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await render_process.communicate()
                
                if render_process.returncode == 0:
                    # Move output file to desired location
                    output_path = Path(output_dir)
                    output_path.mkdir(parents=True, exist_ok=True)
                    
                    source_file = project_dir / f"{scene.scene_id}.mp4"
                    target_file = output_path / f"{scene.scene_id}.mp4"
                    
                    if source_file.exists():
                        source_file.rename(target_file)
                        scene.output_path = str(target_file)
                        logger.info(f"Motion Canvas scene rendered successfully: {target_file}")
                        return str(target_file)
                    else:
                        logger.error("Motion Canvas rendering completed but output file not found")
                        return None
                else:
                    logger.error(f"Motion Canvas rendering failed: {stderr.decode()}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error rendering Motion Canvas scene: {e}")
            return None
    
    async def create_fallback_scene(
        self,
        scene_id: str,
        title: str,
        content: str,
        duration: float = 30.0
    ) -> MotionCanvasScene:
        """Create a fallback Motion Canvas scene when AI generation fails."""
        fallback_code = f'''import {{ makeScene2D }} from '@motion-canvas/2d/lib/scenes';
import {{ Rect, Txt }} from '@motion-canvas/2d/lib/components';
import {{ all, waitFor }} from '@motion-canvas/core/lib/flow';
import {{ createRef }} from '@motion-canvas/core/lib/utils';

export default makeScene2D(function* (view) {{
  const title = createRef<Txt>();
  const content = createRef<Txt>();
  
  view.add(
    <>
      <Rect
        width={{1920}}
        height={{1080}}
        fill="#1e3a8a"
      />
      <Txt
        ref={{title}}
        text="{title}"
        fontSize={{72}}
        fill="white"
        y={{-200}}
      />
      <Txt
        ref={{content}}
        text="{content[:100]}..."
        fontSize={{36}}
        fill="lightgray"
        y={{100}}
        textAlign="center"
        width={{1600}}
      />
    </>
  );
  
  yield* all(
    title().opacity(0, 0).to(1, 1),
    waitFor(1)
  );
  
  yield* all(
    content().opacity(0, 0).to(1, 1),
    waitFor(1)
  );
  
  yield* waitFor({duration - 3});
  
  yield* all(
    title().opacity(1, 0).to(0, 1),
    content().opacity(1, 0).to(0, 1)
  );
}});'''
        
        return MotionCanvasScene(
            scene_id=scene_id,
            title=title,
            content_type="fallback",
            typescript_code=fallback_code,
            duration=duration
        )
    
    def get_quality_settings(self) -> Dict[str, str]:
        """Get available Motion Canvas quality settings."""
        return {
            "720p": "720p",
            "1080p": "1080p",
            "1440p": "1440p",
            "4k": "4k"
        }
    
    async def validate_scene_code(self, scene: MotionCanvasScene) -> List[str]:
        """Validate Motion Canvas scene code and return issues."""
        issues = []
        
        code = scene.typescript_code
        
        # Check for required imports
        if '@motion-canvas' not in code:
            issues.append("Missing Motion Canvas imports")
        
        if 'makeScene2D' not in code:
            issues.append("Missing makeScene2D function")
        
        if 'function*' not in code and 'yield*' not in code:
            issues.append("Missing generator function")
        
        if 'yield' not in code:
            issues.append("No yield statements found (animations may not work)")
        
        # Check for export
        if 'export default' not in code:
            issues.append("Missing default export")
        
        # Estimate duration based on waitFor calls
        wait_matches = re.findall(r'waitFor\(([^)]*)\)', code)
        estimated_duration = 0
        
        for wait_match in wait_matches:
            try:
                if wait_match.strip():
                    estimated_duration += float(wait_match.strip())
            except ValueError:
                estimated_duration += 1  # Default wait
        
        if estimated_duration == 0:
            issues.append("No timing information found (consider adding waitFor calls)")
        elif abs(estimated_duration - scene.duration) > scene.duration * 0.3:
            issues.append(f"Duration mismatch: estimated {estimated_duration:.1f}s, target {scene.duration:.1f}s")
        
        return issues


# Global instance for easy access
motion_canvas_generator = MotionCanvasGenerator()