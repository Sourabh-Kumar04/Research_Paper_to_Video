
from manim import *
import numpy as np

class ResultsScene(Scene):
    def construct(self):
        # Title
        title = Text("Scene 4", font_size=48, color=WHITE)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # Create axes
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 100, 10],
            x_length=8,
            y_length=5,
            axis_config={"color": WHITE},
            x_axis_config={"numbers_to_include": np.arange(0, 11, 2)},
            y_axis_config={"numbers_to_include": np.arange(0, 101, 20)}
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
