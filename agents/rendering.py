"""
Animation Rendering Agents for the RASO platform.

Implements ManimAgent, MotionCanvasAgent, and RemotionAgent for rendering
animations with sandboxing, timeout protection, and fallback mechanisms.
"""

import os
import asyncio
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod
from datetime import datetime, timedelta

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from backend.models.visual import VisualPlan, ScenePlan
from backend.models.animation import AnimationAssets, RenderedScene, SceneMetadata
from animation.templates import template_engine, TemplateFramework
from agents.retry import retry
from backend.config import get_config


class RenderingError(Exception):
    """Exception raised during animation rendering."""
    pass


class RenderingResult(BaseModel):
    """Result of animation rendering."""
    
    success: bool = Field(..., description="Whether rendering succeeded")
    output_path: Optional[str] = Field(default=None, description="Path to rendered video")
    duration: float = Field(..., description="Actual duration of rendered video")
    resolution: str = Field(..., description="Video resolution")
    file_size: int = Field(default=0, description="File size in bytes")
    render_time: float = Field(..., description="Time taken to render")
    error_message: Optional[str] = Field(default=None, description="Error message if failed")
    logs: List[str] = Field(default_factory=list, description="Rendering logs")


class BaseRenderingAgent(BaseAgent, ABC):
    """Base class for animation rendering agents."""
    
    def __init__(self, framework: TemplateFramework):
        """Initialize rendering agent."""
        super().__init__()
        self.framework = framework
        self.config = get_config()
        self.timeout_seconds = 300  # 5 minutes default timeout
    
    @abstractmethod
    async def render_scene(
        self,
        scene_plan: ScenePlan,
        output_path: str,
        **kwargs
    ) -> RenderingResult:
        """
        Render a single scene.
        
        Args:
            scene_plan: Scene plan with template and parameters
            output_path: Output file path
            **kwargs: Additional rendering options
            
        Returns:
            Rendering result
        """
        pass
    
    @abstractmethod
    def validate_environment(self) -> List[str]:
        """
        Validate rendering environment.
        
        Returns:
            List of validation errors
        """
        pass
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute animation rendering for assigned scenes.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with rendered animations
        """
        self.validate_input(state)
        
        try:
            visual_plan = VisualPlan(**state["visual_plan"])
            
            # Filter scenes for this framework
            my_scenes = [
                scene for scene in visual_plan.scenes 
                if scene.framework == self.framework.value
            ]
            
            if not my_scenes:
                self.log_progress(f"No scenes assigned to {self.framework.value}", state)
                return state
            
            self.log_progress(f"Rendering {len(my_scenes)} scenes with {self.framework.value}", state)
            
            rendered_scenes = []
            
            for scene_plan in my_scenes:
                try:
                    result = await self.render_scene_with_fallback(scene_plan)
                    
                    if result.success:
                        rendered_scene = RenderedScene(
                            scene_id=scene_plan.scene_id,
                            file_path=result.output_path,
                            duration=result.duration,
                            framework=self.framework.value,
                            metadata=SceneMetadata(
                                resolution=result.resolution,
                                file_size=result.file_size,
                                render_time=result.render_time,
                                template_id=scene_plan.template,
                            ),
                        )
                        rendered_scenes.append(rendered_scene)
                    else:
                        self.logger.error(f"Failed to render scene {scene_plan.scene_id}: {result.error_message}")
                        
                except Exception as e:
                    self.logger.error(f"Error rendering scene {scene_plan.scene_id}: {str(e)}")
            
            # Update state with rendered scenes
            if "animations" not in state:
                state["animations"] = {
                    "scenes": [],
                    "total_duration": 0.0,
                    "resolution": self.config.animation.resolution,
                }
            
            state["animations"]["scenes"].extend([scene.dict() for scene in rendered_scenes])
            
            self.log_progress(f"Completed rendering {len(rendered_scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state for rendering."""
        if "visual_plan" not in state:
            raise ValueError("Visual plan not found in state")
    
    @retry(max_attempts=3, base_delay=2.0)
    async def render_scene_with_fallback(self, scene_plan: ScenePlan) -> RenderingResult:
        """
        Render scene with fallback template on failure.
        
        Args:
            scene_plan: Scene plan to render
            
        Returns:
            Rendering result
        """
        # Create output path
        output_dir = Path(self.config.temp_path) / "renders" / scene_plan.scene_id
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = str(output_dir / f"{scene_plan.scene_id}.mp4")
        
        try:
            # Try primary template
            result = await self.render_scene(scene_plan, output_path)
            
            if result.success:
                return result
            
            self.logger.warning(f"Primary template failed for {scene_plan.scene_id}, trying fallback")
            
        except Exception as e:
            self.logger.warning(f"Primary rendering failed: {str(e)}")
        
        # Try fallback template
        fallback_template_id = template_engine.get_fallback_template(self.framework)
        if fallback_template_id and fallback_template_id != scene_plan.template:
            fallback_plan = ScenePlan(
                scene_id=scene_plan.scene_id,
                framework=scene_plan.framework,
                template=fallback_template_id,
                parameters=scene_plan.parameters,
                duration=scene_plan.duration,
            )
            
            try:
                result = await self.render_scene(fallback_plan, output_path)
                if result.success:
                    self.logger.info(f"Fallback template succeeded for {scene_plan.scene_id}")
                    return result
            except Exception as e:
                self.logger.error(f"Fallback rendering failed: {str(e)}")
        
        # All attempts failed
        return RenderingResult(
            success=False,
            duration=scene_plan.duration,
            resolution=self.config.animation.resolution,
            render_time=0.0,
            error_message="All rendering attempts failed",
        )
    
    async def run_command_with_timeout(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> tuple[int, str, str]:
        """
        Run command with timeout protection.
        
        Args:
            command: Command to run
            cwd: Working directory
            timeout: Timeout in seconds
            
        Returns:
            Tuple of (return_code, stdout, stderr)
        """
        timeout = timeout or self.timeout_seconds
        
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=timeout
            )
            
            return process.returncode, stdout.decode(), stderr.decode()
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise RenderingError(f"Command timed out after {timeout} seconds")
        
        except Exception as e:
            raise RenderingError(f"Command execution failed: {str(e)}")
    
    def create_sandbox_environment(self) -> str:
        """
        Create sandboxed environment for rendering.
        
        Returns:
            Path to sandbox directory
        """
        sandbox_dir = tempfile.mkdtemp(prefix=f"raso_{self.framework.value}_")
        
        # Set restrictive permissions
        os.chmod(sandbox_dir, 0o700)
        
        return sandbox_dir
    
    def cleanup_sandbox(self, sandbox_path: str) -> None:
        """
        Clean up sandbox environment.
        
        Args:
            sandbox_path: Path to sandbox directory
        """
        try:
            if os.path.exists(sandbox_path):
                shutil.rmtree(sandbox_path)
        except Exception as e:
            self.logger.warning(f"Failed to cleanup sandbox {sandbox_path}: {str(e)}")


class ManimAgent(BaseRenderingAgent):
    """Agent for rendering Manim animations."""
    
    name = "ManimAgent"
    description = "Renders mathematical animations using Manim CE"
    
    def __init__(self):
        """Initialize Manim agent."""
        super().__init__(TemplateFramework.MANIM)
    
    def validate_environment(self) -> List[str]:
        """Validate Manim environment."""
        errors = []
        
        # Check if manim is installed
        try:
            result = subprocess.run(
                ["manim", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                errors.append("Manim not properly installed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("Manim command not found")
        
        # Check for required system dependencies
        required_commands = ["ffmpeg", "latex"]
        for cmd in required_commands:
            try:
                subprocess.run([cmd, "--version"], capture_output=True, timeout=5)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                errors.append(f"Required dependency not found: {cmd}")
        
        return errors
    
    async def render_scene(
        self,
        scene_plan: ScenePlan,
        output_path: str,
        **kwargs
    ) -> RenderingResult:
        """Render Manim scene."""
        start_time = datetime.now()
        
        # Create sandbox
        sandbox_dir = self.create_sandbox_environment()
        
        try:
            # Generate animation code
            code = template_engine.generate_animation_code(
                template_id=scene_plan.template,
                parameters=scene_plan.parameters,
            )
            
            # Write code to file
            code_file = os.path.join(sandbox_dir, "scene.py")
            with open(code_file, 'w') as f:
                f.write(code)
            
            # Prepare manim command
            quality = self.config.animation.manim_quality
            resolution = self.config.animation.resolution
            
            command = [
                "manim",
                code_file,
                "--quality", quality,
                "--resolution", resolution,
                "--output_file", output_path,
                "--disable_caching",
            ]
            
            # Run manim
            return_code, stdout, stderr = await self.run_command_with_timeout(
                command=command,
                cwd=sandbox_dir,
            )
            
            render_time = (datetime.now() - start_time).total_seconds()
            
            if return_code == 0 and os.path.exists(output_path):
                # Get file info
                file_size = os.path.getsize(output_path)
                
                return RenderingResult(
                    success=True,
                    output_path=output_path,
                    duration=scene_plan.duration,
                    resolution=resolution,
                    file_size=file_size,
                    render_time=render_time,
                    logs=[stdout, stderr],
                )
            else:
                return RenderingResult(
                    success=False,
                    duration=scene_plan.duration,
                    resolution=resolution,
                    render_time=render_time,
                    error_message=f"Manim failed: {stderr}",
                    logs=[stdout, stderr],
                )
        
        finally:
            self.cleanup_sandbox(sandbox_dir)


class MotionCanvasAgent(BaseRenderingAgent):
    """Agent for rendering Motion Canvas animations."""
    
    name = "MotionCanvasAgent"
    description = "Renders conceptual animations using Motion Canvas"
    
    def __init__(self):
        """Initialize Motion Canvas agent."""
        super().__init__(TemplateFramework.MOTION_CANVAS)
    
    def validate_environment(self) -> List[str]:
        """Validate Motion Canvas environment."""
        errors = []
        
        # Check if Node.js is installed
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                errors.append("Node.js not properly installed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("Node.js not found")
        
        # Check if npm is available
        try:
            subprocess.run(["npm", "--version"], capture_output=True, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("npm not found")
        
        return errors
    
    async def render_scene(
        self,
        scene_plan: ScenePlan,
        output_path: str,
        **kwargs
    ) -> RenderingResult:
        """Render Motion Canvas scene."""
        start_time = datetime.now()
        
        # Create sandbox
        sandbox_dir = self.create_sandbox_environment()
        
        try:
            # Generate animation code
            code = template_engine.generate_animation_code(
                template_id=scene_plan.template,
                parameters=scene_plan.parameters,
            )
            
            # Create Motion Canvas project structure
            project_dir = os.path.join(sandbox_dir, "project")
            os.makedirs(project_dir, exist_ok=True)
            
            # Write package.json
            package_json = {
                "name": "raso-motion-canvas",
                "version": "1.0.0",
                "type": "module",
                "dependencies": {
                    "@motion-canvas/core": "^3.12.0",
                    "@motion-canvas/2d": "^3.12.0",
                    "@motion-canvas/ffmpeg": "^3.12.0"
                }
            }
            
            with open(os.path.join(project_dir, "package.json"), 'w') as f:
                import json
                json.dump(package_json, f, indent=2)
            
            # Write scene code
            scene_file = os.path.join(project_dir, "scene.ts")
            with open(scene_file, 'w') as f:
                f.write(code)
            
            # Write project configuration
            config_code = f"""
import {{Configuration}} from '@motion-canvas/core';

const config: Configuration = {{
  project: [
    './scene.ts',
  ],
  settings: {{
    size: {{width: 1920, height: 1080}},
    duration: {scene_plan.duration},
  }},
  output: '{output_path}',
}};

export default config;
"""
            
            with open(os.path.join(project_dir, "motion-canvas.config.ts"), 'w') as f:
                f.write(config_code)
            
            # Install dependencies
            install_code, install_stdout, install_stderr = await self.run_command_with_timeout(
                command=["npm", "install"],
                cwd=project_dir,
                timeout=120,  # 2 minutes for npm install
            )
            
            if install_code != 0:
                return RenderingResult(
                    success=False,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    render_time=0.0,
                    error_message=f"npm install failed: {install_stderr}",
                )
            
            # Render animation
            render_command = ["npx", "motion-canvas", "render"]
            
            return_code, stdout, stderr = await self.run_command_with_timeout(
                command=render_command,
                cwd=project_dir,
            )
            
            render_time = (datetime.now() - start_time).total_seconds()
            
            if return_code == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                
                return RenderingResult(
                    success=True,
                    output_path=output_path,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    file_size=file_size,
                    render_time=render_time,
                    logs=[stdout, stderr],
                )
            else:
                return RenderingResult(
                    success=False,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    render_time=render_time,
                    error_message=f"Motion Canvas failed: {stderr}",
                    logs=[stdout, stderr],
                )
        
        finally:
            self.cleanup_sandbox(sandbox_dir)


class RemotionAgent(BaseRenderingAgent):
    """Agent for rendering Remotion animations."""
    
    name = "RemotionAgent"
    description = "Renders UI animations and titles using Remotion"
    
    def __init__(self):
        """Initialize Remotion agent."""
        super().__init__(TemplateFramework.REMOTION)
    
    def validate_environment(self) -> List[str]:
        """Validate Remotion environment."""
        errors = []
        
        # Check if Node.js is installed
        try:
            result = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                errors.append("Node.js not properly installed")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("Node.js not found")
        
        # Check if npm is available
        try:
            subprocess.run(["npm", "--version"], capture_output=True, timeout=5)
        except (subprocess.TimeoutExpired, FileNotFoundError):
            errors.append("npm not found")
        
        return errors
    
    async def render_scene(
        self,
        scene_plan: ScenePlan,
        output_path: str,
        **kwargs
    ) -> RenderingResult:
        """Render Remotion scene."""
        start_time = datetime.now()
        
        # Create sandbox
        sandbox_dir = self.create_sandbox_environment()
        
        try:
            # Generate animation code
            code = template_engine.generate_animation_code(
                template_id=scene_plan.template,
                parameters=scene_plan.parameters,
            )
            
            # Create Remotion project structure
            project_dir = os.path.join(sandbox_dir, "project")
            os.makedirs(project_dir, exist_ok=True)
            
            # Write package.json
            package_json = {
                "name": "raso-remotion",
                "version": "1.0.0",
                "dependencies": {
                    "remotion": "^4.0.0",
                    "react": "^18.2.0",
                    "react-dom": "^18.2.0"
                },
                "devDependencies": {
                    "@types/react": "^18.0.0",
                    "typescript": "^5.0.0"
                }
            }
            
            with open(os.path.join(project_dir, "package.json"), 'w') as f:
                import json
                json.dump(package_json, f, indent=2)
            
            # Write component code
            component_file = os.path.join(project_dir, "Scene.tsx")
            with open(component_file, 'w') as f:
                f.write(code)
            
            # Write Remotion root
            root_code = f"""
import React from 'react';
import {{Composition}} from 'remotion';
import {{TitleSequence}} from './Scene';

export const RemotionRoot: React.FC = () => {{
    return (
        <>
            <Composition
                id="Scene"
                component={{TitleSequence}}
                durationInFrames={{Math.round({scene_plan.duration} * 30)}}
                fps={{30}}
                width={{1920}}
                height={{1080}}
            />
        </>
    );
}};
"""
            
            with open(os.path.join(project_dir, "Root.tsx"), 'w') as f:
                f.write(root_code)
            
            # Write remotion config
            config_code = """
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
"""
            
            with open(os.path.join(project_dir, "remotion.config.ts"), 'w') as f:
                f.write(config_code)
            
            # Install dependencies
            install_code, install_stdout, install_stderr = await self.run_command_with_timeout(
                command=["npm", "install"],
                cwd=project_dir,
                timeout=120,
            )
            
            if install_code != 0:
                return RenderingResult(
                    success=False,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    render_time=0.0,
                    error_message=f"npm install failed: {install_stderr}",
                )
            
            # Render video
            render_command = [
                "npx", "remotion", "render",
                "Scene",
                output_path,
                "--codec", "h264",
            ]
            
            return_code, stdout, stderr = await self.run_command_with_timeout(
                command=render_command,
                cwd=project_dir,
            )
            
            render_time = (datetime.now() - start_time).total_seconds()
            
            if return_code == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                
                return RenderingResult(
                    success=True,
                    output_path=output_path,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    file_size=file_size,
                    render_time=render_time,
                    logs=[stdout, stderr],
                )
            else:
                return RenderingResult(
                    success=False,
                    duration=scene_plan.duration,
                    resolution=self.config.animation.resolution,
                    render_time=render_time,
                    error_message=f"Remotion failed: {stderr}",
                    logs=[stdout, stderr],
                )
        
        finally:
            self.cleanup_sandbox(sandbox_dir)


class RenderingCoordinator(BaseAgent):
    """Coordinates rendering across multiple agents."""
    
    name = "RenderingCoordinator"
    description = "Coordinates animation rendering across Manim, Motion Canvas, and Remotion agents"
    
    def __init__(self):
        """Initialize rendering coordinator."""
        super().__init__()
        self.agents = {
            TemplateFramework.MANIM: ManimAgent(),
            TemplateFramework.MOTION_CANVAS: MotionCanvasAgent(),
            TemplateFramework.REMOTION: RemotionAgent(),
        }
    
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute coordinated rendering across all agents.
        
        Args:
            state: Current workflow state
            
        Returns:
            Updated state with all rendered animations
        """
        self.validate_input(state)
        
        try:
            visual_plan = VisualPlan(**state["visual_plan"])
            
            self.log_progress("Starting coordinated animation rendering", state)
            
            # Validate environments
            for framework, agent in self.agents.items():
                errors = agent.validate_environment()
                if errors:
                    self.logger.warning(f"{framework} environment issues: {errors}")
            
            # Run agents in parallel for their assigned scenes
            tasks = []
            for framework, agent in self.agents.items():
                # Check if this framework has scenes
                framework_scenes = [
                    scene for scene in visual_plan.scenes
                    if scene.framework == framework.value
                ]
                
                if framework_scenes:
                    tasks.append(agent.execute(state.copy()))
            
            # Wait for all rendering to complete
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Merge results
                all_rendered_scenes = []
                total_duration = 0.0
                
                for result in results:
                    if isinstance(result, dict) and "animations" in result:
                        scenes = result["animations"].get("scenes", [])
                        all_rendered_scenes.extend(scenes)
                        
                        for scene_data in scenes:
                            total_duration += scene_data.get("duration", 0.0)
                
                # Update state with all rendered scenes
                state["animations"] = AnimationAssets(
                    scenes=[RenderedScene(**scene_data) for scene_data in all_rendered_scenes],
                    total_duration=total_duration,
                    resolution=self.config.animation.resolution,
                ).dict()
                
                state["current_agent"] = "AudioAgent"
                
                self.log_progress(f"Completed rendering {len(all_rendered_scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state."""
        if "visual_plan" not in state:
            raise ValueError("Visual plan not found in state")