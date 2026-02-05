"""
Manim Animation Generator for RASO platform.
Creates complex mathematical and scientific animations using Manim.
"""

import os
import sys
import tempfile
import subprocess
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple
import json

try:
    from manim import *
    MANIM_AVAILABLE = True
except ImportError:
    MANIM_AVAILABLE = False


class ManimAnimationGenerator:
    """Generate complex animations using Manim for research paper explanations."""
    
    def __init__(self):
        """Initialize the Manim animation generator."""
        self.resolution = "1920x1080"
        self.fps = 30
        self.quality = "h"  # Manim quality setting (h = high)
        self.manim_available = MANIM_AVAILABLE
        
    def get_capabilities(self) -> Dict[str, bool]:
        """Get animation generation capabilities."""
        return {
            "manim_available": self.manim_available,
            "complex_animations": self.manim_available,
            "mathematical_visualizations": self.manim_available,
            "scientific_diagrams": self.manim_available,
            "can_generate_video": self.manim_available
        }
    
    async def generate_animation_assets(self, script, output_dir: str):
        """Generate Manim animation assets from a narration script."""
        from backend.models.animation import AnimationAssets, RenderedScene, VideoResolution, RenderStatus
        
        # Create output directory
        animation_dir = Path(output_dir) / "manim_animations"
        animation_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate animations for each scene
        rendered_scenes = []
        
        for i, scene in enumerate(script.scenes):
            print(f"Generating Manim animation for scene {i+1}/{len(script.scenes)}: {scene.title}")
            
            rendered_scene = await self._generate_manim_scene(scene, animation_dir)
            
            if rendered_scene:
                rendered_scenes.append(rendered_scene)
                print(f"✅ Manim animation generated for scene {scene.id}")
            else:
                print(f"❌ Failed to generate Manim animation for scene {scene.id}")
        
        # Create animation assets
        total_duration = sum(scene.duration for scene in rendered_scenes)
        
        animation_assets = AnimationAssets(
            scenes=rendered_scenes,
            total_duration=total_duration,
            resolution=VideoResolution.from_string(self.resolution)
        )
        
        return animation_assets
    
    async def _generate_manim_scene(self, scene, output_dir: Path):
        """Generate a single Manim animation scene."""
        from backend.models.animation import RenderedScene, VideoResolution, RenderStatus
        
        try:
            if not self.manim_available:
                print(f"  Manim not available for scene {scene.id}")
                return None
            
            # Create scene-specific directory
            scene_dir = output_dir / scene.id
            scene_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate Manim code for this scene
            manim_code = self._generate_manim_code(scene)
            
            # Save Manim code to file
            code_file = scene_dir / f"{scene.id}_animation.py"
            with open(code_file, 'w', encoding='utf-8') as f:
                f.write(manim_code)
            
            # Render the animation
            video_path = await self._render_manim_animation(code_file, scene_dir, scene.id)
            
            if video_path and video_path.exists():
                rendered_scene = RenderedScene(
                    scene_id=scene.id,
                    file_path=str(video_path),
                    duration=scene.duration,
                    framework="manim",
                    resolution=VideoResolution.from_string(self.resolution),
                    frame_rate=self.fps,
                    status=RenderStatus.COMPLETED
                )
                
                return rendered_scene
            else:
                print(f"  Failed to render Manim animation for scene {scene.id}")
                return None
                
        except Exception as e:
            print(f"Error generating Manim animation for scene {scene.id}: {e}")
            return None
    
    def _generate_manim_code(self, scene) -> str:
        """Generate Manim code based on scene content and type."""
        
        # Determine animation type based on scene content
        animation_type = self._classify_scene_type(scene)
        
        if animation_type == "mathematical":
            return self._generate_mathematical_animation(scene)
        elif animation_type == "diagram":
            return self._generate_diagram_animation(scene)
        elif animation_type == "graph":
            return self._generate_graph_animation(scene)
        elif animation_type == "network":
            return self._generate_network_animation(scene)
        else:
            return self._generate_text_animation(scene)
    
    def _classify_scene_type(self, scene) -> str:
        """Classify the type of animation needed based on scene content."""
        content = (scene.title + " " + scene.narration).lower()
        
        # Mathematical content indicators
        math_keywords = ["equation", "formula", "theorem", "proof", "derivative", "integral", 
                        "matrix", "vector", "function", "algorithm", "optimization"]
        
        # Diagram content indicators  
        diagram_keywords = ["architecture", "structure", "model", "framework", "system",
                           "pipeline", "workflow", "process", "mechanism"]
        
        # Graph content indicators
        graph_keywords = ["graph", "chart", "plot", "data", "results", "performance",
                         "comparison", "analysis", "statistics", "metrics"]
        
        # Network content indicators
        network_keywords = ["network", "neural", "layer", "node", "connection", "attention",
                           "transformer", "convolution", "activation"]
        
        if any(keyword in content for keyword in math_keywords):
            return "mathematical"
        elif any(keyword in content for keyword in network_keywords):
            return "network"
        elif any(keyword in content for keyword in graph_keywords):
            return "graph"
        elif any(keyword in content for keyword in diagram_keywords):
            return "diagram"
        else:
            return "text"
    
    def _generate_mathematical_animation(self, scene) -> str:
        """Generate Manim code for mathematical content."""
        return f'''
from manim import *

class {scene.id.title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{scene.title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Mathematical equation example
        equation = MathTex(
            r"\\text{{Attention}}(Q, K, V) = \\text{{softmax}}\\left(\\frac{{QK^T}}{{\\sqrt{{d_k}}}}\\right)V",
            font_size=36
        )
        equation.next_to(title, DOWN, buff=1)
        
        # Animate equation writing
        self.play(Write(equation))
        self.wait(2)
        
        # Explanation text
        explanation = Text(
            "Self-attention mechanism computes attention weights\\nfor all positions in the sequence",
            font_size=24,
            color=BLUE
        )
        explanation.next_to(equation, DOWN, buff=1)
        
        self.play(FadeIn(explanation))
        self.wait(3)
        
        # Highlight parts of equation
        q_part = equation[0][9:10]  # Q
        k_part = equation[0][10:11]  # K
        v_part = equation[0][11:12]  # V
        
        self.play(
            q_part.animate.set_color(RED),
            k_part.animate.set_color(GREEN), 
            v_part.animate.set_color(BLUE)
        )
        self.wait(2)
        
        # Matrix visualization
        matrix_q = Matrix([["q_1"], ["q_2"], ["q_3"]], left_bracket="[", right_bracket="]")
        matrix_k = Matrix([["k_1", "k_2", "k_3"]], left_bracket="[", right_bracket="]")
        matrix_v = Matrix([["v_1"], ["v_2"], ["v_3"]], left_bracket="[", right_bracket="]")
        
        matrices = VGroup(matrix_q, matrix_k, matrix_v)
        matrices.arrange(RIGHT, buff=1)
        matrices.next_to(explanation, DOWN, buff=1)
        
        matrix_q.set_color(RED)
        matrix_k.set_color(GREEN)
        matrix_v.set_color(BLUE)
        
        self.play(Create(matrices))
        self.wait(3)
        
        # Fade out everything
        self.play(FadeOut(VGroup(title, equation, explanation, matrices)))
        self.wait(1)
'''
    
    def _generate_network_animation(self, scene) -> str:
        """Generate Manim code for neural network visualizations."""
        return f'''
from manim import *

class {scene.id.title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{scene.title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Neural network visualization
        # Input layer
        input_nodes = VGroup(*[Circle(radius=0.3, color=BLUE, fill_opacity=0.7) for _ in range(4)])
        input_nodes.arrange(DOWN, buff=0.5)
        input_nodes.shift(LEFT * 4)
        
        # Hidden layer
        hidden_nodes = VGroup(*[Circle(radius=0.3, color=GREEN, fill_opacity=0.7) for _ in range(6)])
        hidden_nodes.arrange(DOWN, buff=0.3)
        hidden_nodes.shift(LEFT * 1)
        
        # Output layer
        output_nodes = VGroup(*[Circle(radius=0.3, color=RED, fill_opacity=0.7) for _ in range(3)])
        output_nodes.arrange(DOWN, buff=0.5)
        output_nodes.shift(RIGHT * 2)
        
        # Create connections
        connections = VGroup()
        for input_node in input_nodes:
            for hidden_node in hidden_nodes:
                line = Line(input_node.get_center(), hidden_node.get_center(), 
                           stroke_width=1, color=GRAY)
                connections.add(line)
        
        for hidden_node in hidden_nodes:
            for output_node in output_nodes:
                line = Line(hidden_node.get_center(), output_node.get_center(),
                           stroke_width=1, color=GRAY)
                connections.add(line)
        
        # Animate network creation
        self.play(Create(connections))
        self.play(Create(input_nodes), Create(hidden_nodes), Create(output_nodes))
        self.wait(2)
        
        # Add labels
        input_label = Text("Input", font_size=24, color=BLUE)
        input_label.next_to(input_nodes, DOWN)
        
        hidden_label = Text("Hidden", font_size=24, color=GREEN)
        hidden_label.next_to(hidden_nodes, DOWN)
        
        output_label = Text("Output", font_size=24, color=RED)
        output_label.next_to(output_nodes, DOWN)
        
        self.play(Write(input_label), Write(hidden_label), Write(output_label))
        self.wait(2)
        
        # Animate data flow
        for i in range(3):
            # Highlight input
            self.play(input_nodes.animate.set_fill(YELLOW, opacity=1))
            self.wait(0.5)
            
            # Flow to hidden
            self.play(
                input_nodes.animate.set_fill(BLUE, opacity=0.7),
                hidden_nodes.animate.set_fill(YELLOW, opacity=1)
            )
            self.wait(0.5)
            
            # Flow to output
            self.play(
                hidden_nodes.animate.set_fill(GREEN, opacity=0.7),
                output_nodes.animate.set_fill(YELLOW, opacity=1)
            )
            self.wait(0.5)
            
            # Reset
            self.play(output_nodes.animate.set_fill(RED, opacity=0.7))
            self.wait(0.5)
        
        # Fade out
        everything = VGroup(title, connections, input_nodes, hidden_nodes, output_nodes,
                           input_label, hidden_label, output_label)
        self.play(FadeOut(everything))
        self.wait(1)
'''
    
    def _generate_diagram_animation(self, scene) -> str:
        """Generate Manim code for architectural diagrams."""
        return f'''
from manim import *

class {scene.id.title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{scene.title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Architecture diagram
        # Main components
        input_box = Rectangle(width=2, height=1, color=BLUE, fill_opacity=0.3)
        input_text = Text("Input", font_size=20, color=WHITE)
        input_group = VGroup(input_box, input_text)
        input_group.shift(LEFT * 4)
        
        processor_box = Rectangle(width=2.5, height=1.5, color=GREEN, fill_opacity=0.3)
        processor_text = Text("Processor", font_size=20, color=WHITE)
        processor_group = VGroup(processor_box, processor_text)
        
        output_box = Rectangle(width=2, height=1, color=RED, fill_opacity=0.3)
        output_text = Text("Output", font_size=20, color=WHITE)
        output_group = VGroup(output_box, output_text)
        output_group.shift(RIGHT * 4)
        
        # Arrows
        arrow1 = Arrow(input_group.get_right(), processor_group.get_left(), 
                      stroke_width=3, color=YELLOW)
        arrow2 = Arrow(processor_group.get_right(), output_group.get_left(),
                      stroke_width=3, color=YELLOW)
        
        # Animate creation
        self.play(Create(input_group))
        self.wait(0.5)
        self.play(Create(arrow1))
        self.wait(0.5)
        self.play(Create(processor_group))
        self.wait(0.5)
        self.play(Create(arrow2))
        self.wait(0.5)
        self.play(Create(output_group))
        self.wait(2)
        
        # Add details
        detail_text = Text(
            "Data flows through the processing pipeline\\nwith transformations at each stage",
            font_size=24,
            color=GRAY
        )
        detail_text.next_to(processor_group, DOWN, buff=1)
        
        self.play(Write(detail_text))
        self.wait(3)
        
        # Highlight data flow
        for _ in range(2):
            self.play(input_group.animate.set_fill(YELLOW, opacity=0.8))
            self.wait(0.3)
            self.play(
                input_group.animate.set_fill(BLUE, opacity=0.3),
                arrow1.animate.set_color(WHITE)
            )
            self.wait(0.3)
            self.play(
                arrow1.animate.set_color(YELLOW),
                processor_group.animate.set_fill(YELLOW, opacity=0.8)
            )
            self.wait(0.3)
            self.play(
                processor_group.animate.set_fill(GREEN, opacity=0.3),
                arrow2.animate.set_color(WHITE)
            )
            self.wait(0.3)
            self.play(
                arrow2.animate.set_color(YELLOW),
                output_group.animate.set_fill(YELLOW, opacity=0.8)
            )
            self.wait(0.3)
            self.play(output_group.animate.set_fill(RED, opacity=0.3))
            self.wait(0.5)
        
        # Fade out
        everything = VGroup(title, input_group, processor_group, output_group,
                           arrow1, arrow2, detail_text)
        self.play(FadeOut(everything))
        self.wait(1)
'''
    
    def _generate_graph_animation(self, scene) -> str:
        """Generate Manim code for data visualizations and graphs."""
        return f'''
from manim import *
import numpy as np

class {scene.id.title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{scene.title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create axes
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 100, 10],
            x_length=8,
            y_length=5,
            axis_config={{"color": WHITE}},
            x_axis_config={{"numbers_to_include": np.arange(0, 11, 2)}},
            y_axis_config={{"numbers_to_include": np.arange(0, 101, 20)}}
        )
        
        # Labels
        x_label = axes.get_x_axis_label("Epochs", direction=DOWN)
        y_label = axes.get_y_axis_label("Accuracy (%)", direction=LEFT)
        
        self.play(Create(axes), Write(x_label), Write(y_label))
        self.wait(1)
        
        # Data points for training curve
        training_data = [10, 25, 45, 60, 72, 80, 85, 88, 90, 91, 92]
        validation_data = [8, 22, 40, 55, 68, 75, 78, 79, 80, 79, 78]
        
        # Create training curve
        training_points = [axes.coords_to_point(i, training_data[i]) for i in range(len(training_data))]
        training_curve = VMobject()
        training_curve.set_points_smoothly(training_points)
        training_curve.set_color(BLUE)
        training_curve.set_stroke(width=3)
        
        # Create validation curve
        validation_points = [axes.coords_to_point(i, validation_data[i]) for i in range(len(validation_data))]
        validation_curve = VMobject()
        validation_curve.set_points_smoothly(validation_points)
        validation_curve.set_color(RED)
        validation_curve.set_stroke(width=3)
        
        # Animate curves
        self.play(Create(training_curve), run_time=3)
        self.wait(0.5)
        self.play(Create(validation_curve), run_time=3)
        self.wait(1)
        
        # Add legend
        legend_training = VGroup(
            Line(ORIGIN, RIGHT * 0.5, color=BLUE, stroke_width=3),
            Text("Training", font_size=20, color=BLUE)
        )
        legend_training.arrange(RIGHT, buff=0.2)
        
        legend_validation = VGroup(
            Line(ORIGIN, RIGHT * 0.5, color=RED, stroke_width=3),
            Text("Validation", font_size=20, color=RED)
        )
        legend_validation.arrange(RIGHT, buff=0.2)
        
        legend = VGroup(legend_training, legend_validation)
        legend.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        legend.to_corner(UR, buff=1)
        
        self.play(FadeIn(legend))
        self.wait(2)
        
        # Highlight overfitting
        overfitting_text = Text(
            "Model starts overfitting after epoch 7",
            font_size=24,
            color=YELLOW
        )
        overfitting_text.next_to(axes, DOWN, buff=0.5)
        
        # Point to overfitting region
        overfitting_point = axes.coords_to_point(7, 79)
        dot = Dot(overfitting_point, color=YELLOW, radius=0.1)
        
        self.play(Write(overfitting_text), Create(dot))
        self.wait(3)
        
        # Fade out
        everything = VGroup(title, axes, x_label, y_label, training_curve, 
                           validation_curve, legend, overfitting_text, dot)
        self.play(FadeOut(everything))
        self.wait(1)
'''
    
    def _generate_text_animation(self, scene) -> str:
        """Generate Manim code for text-based content."""
        return f'''
from manim import *

class {scene.id.title()}Scene(Scene):
    def construct(self):
        # Title
        title = Text("{scene.title}", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Main content
        content_lines = [
            "{scene.narration[:80]}...",
            "Key concepts and explanations",
            "Research contributions",
            "Practical implications"
        ]
        
        content_group = VGroup()
        for i, line in enumerate(content_lines):
            text = Text(line, font_size=28, color=BLUE if i == 0 else WHITE)
            content_group.add(text)
        
        content_group.arrange(DOWN, buff=0.8, aligned_edge=LEFT)
        content_group.next_to(title, DOWN, buff=1.5)
        
        # Animate content appearance
        for text in content_group:
            self.play(Write(text))
            self.wait(1)
        
        self.wait(2)
        
        # Create bullet points
        bullets = VGroup()
        for i in range(3):
            bullet = Dot(radius=0.05, color=YELLOW)
            bullet.next_to(content_group[i+1], LEFT, buff=0.3)
            bullets.add(bullet)
        
        self.play(Create(bullets))
        self.wait(2)
        
        # Highlight key terms
        self.play(content_group[0].animate.set_color(YELLOW))
        self.wait(1)
        self.play(content_group[0].animate.set_color(BLUE))
        self.wait(1)
        
        # Fade out
        everything = VGroup(title, content_group, bullets)
        self.play(FadeOut(everything))
        self.wait(1)
'''
    
    async def _render_manim_animation(self, code_file: Path, output_dir: Path, scene_id: str) -> Optional[Path]:
        """Render the Manim animation from the generated code."""
        try:
            # Use absolute paths to avoid path confusion
            abs_code_file = code_file.resolve()
            abs_output_dir = output_dir.resolve()
            
            # Render command with absolute paths
            cmd = [
                sys.executable, "-m", "manim",
                str(abs_code_file),
                f"{scene_id.title()}Scene",
                "--quality", "h",
                "--format", "mp4",
                "--output_file", f"{scene_id}.mp4"
            ]
            
            print(f"  Rendering Manim animation: {' '.join(cmd)}")
            
            # Run Manim from the output directory
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
                cwd=str(abs_output_dir)
            )
            
            if result.returncode == 0:
                # Find the generated video file
                video_files = list(abs_output_dir.glob("*.mp4"))
                if video_files:
                    video_path = video_files[0]
                    print(f"  ✅ Manim animation rendered: {video_path}")
                    return video_path
                else:
                    print(f"  ❌ No video file found after rendering")
                    return None
            else:
                print(f"  ❌ Manim rendering failed:")
                print(f"  stdout: {result.stdout}")
                print(f"  stderr: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print(f"  ❌ Manim rendering timed out")
            return None
        except Exception as e:
            print(f"  ❌ Manim rendering error: {e}")
            return None