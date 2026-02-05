from manim import *

class MathematicalFoundations(Scene):
    def construct(self):
        # --- Scene 1: Conceptual Overview (60 seconds) ---
        title = Text("Mathematical Foundations for Video Generation", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        concept_box = SurroundingRectangle(title, color=BLUE, buff=0.5)
        self.play(Create(concept_box))
        self.wait(3)

        overview_text = Text("We'll explore the math behind creating videos,\nstarting with core concepts and building up to\ncomplex optimization landscapes.", font_size=28)
        overview_text.scale_to_fit_width(10)
        self.play(Write(overview_text))
        self.wait(10)

        # Visual metaphor: Building blocks
        block1 = Rectangle(color=BLUE, width=1, height=1)
        block2 = Rectangle(color=GREEN, width=1, height=1).next_to(block1, RIGHT)
        block3 = Rectangle(color=ORANGE, width=1, height=1).next_to(block2, RIGHT)

        self.play(Create(block1), Create(block2), Create(block3))
        self.wait(5)

        explanation = Text("These blocks represent different mathematical ideas.\nWe'll stack them to build a complete understanding.", font_size=24)
        explanation.scale_to_fit_width(10)
        explanation.next_to(block3, DOWN)
        self.play(Write(explanation))
        self.wait(10)

        self.play(FadeOut(title, concept_box, overview_text, block1, block2, block3, explanation))

        # --- Scene 2: Detailed Component Analysis (60 seconds) ---
        heading = Text("Core Components: Functions & Optimization", font_size=32)
        heading.scale_to_fit_width(10)
        self.play(Write(heading))
        self.wait(3)

        # Function visualization
        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"include_numbers": True},
        )
        axes.add_coordinate_labels()

        graph = axes.plot(lambda x: x**2, color=BLUE)
        self.play(Create(axes), Create(graph))
        self.wait(5)

        function_text = Text("A function maps inputs to outputs.\nHere, f(x) = x²", font_size=24)
        function_text.scale_to_fit_width(10)
        function_text.next_to(axes, DOWN)
        self.play(Write(function_text))
        self.wait(10)

        # Optimization landscape
        landscape = ParametricFunction(
            lambda t: [t, np.sin(t)],
            t_range=[0, 10, 0.1],
            color=ORANGE
        )
        self.play(Transform(graph, landscape))
        self.wait(5)

        optimization_text = Text("Optimization finds the best input to minimize or\nmaximize a function's output.", font_size=24)
        optimization_text.scale_to_fit_width(10)
        optimization_text.next_to(landscape, DOWN)
        self.play(Write(optimization_text))
        self.wait(10)

        self.play(FadeOut(heading, axes, landscape, function_text, optimization_text))

        # --- Scene 3: Integration & Relationships (40 seconds) ---
        heading2 = Text("Connecting Functions & Optimization", font_size=32)
        heading2.scale_to_fit_width(10)
        self.play(Write(heading2))
        self.wait(3)

        # Visual: Gradient Descent
        axes2 = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"include_numbers": True},
        )
        axes2.add_coordinate_labels()

        graph2 = axes2.plot(lambda x: x**2, color=BLUE)
        point = Dot(axes2.coords_to_point(4, 16), color=GREEN)
        self.play(Create(axes2), Create(graph2), Create(point))
        self.wait(3)

        arrow = Arrow(point, axes2.coords_to_point(3, 9), color=ORANGE)
        self.play(Create(arrow))
        self.wait(5)

        descent_text = Text("Gradient descent iteratively adjusts inputs\nto find the minimum of a function.", font_size=24)
        descent_text.scale_to_fit_width(10)
        descent_text.next_to(axes2, DOWN)
        self.play(Write(descent_text))
        self.wait(10)

        self.play(FadeOut(heading2, axes2, graph2, point, arrow, descent_text))

        # --- Scene 4: Practical Applications (41.75 seconds) ---
        heading3 = Text("Applications in Video Generation", font_size=32)
        heading3.scale_to_fit_width(10)
        self.play(Write(heading3))
        self.wait(3)

        # Before/After comparison
        before_image = ImageMobject("before.png").scale(0.5) # Replace with actual image
        after_image = ImageMobject("after.png").scale(0.5) # Replace with actual image

        self.play(Create(before_image))
        self.wait(5)

        self.play(Transform(before_image, after_image))
        self.wait(5)

        application_text = Text("Optimization algorithms are used to train\nmodels that generate realistic video frames.\nFunctions define the image quality, and\noptimization minimizes the difference between\ngenerated and real images.", font_size=24)
        application_text.scale_to_fit_width(10)
        application_text.next_to(after_image, DOWN)
        self.play(Write(application_text))
        self.wait(15)

        future_text = Text("Future possibilities include faster generation,\nhigher resolution, and more creative control.", font_size=24)
        future_text.scale_to_fit_width(10)
        future_text.next_to(application_text, DOWN)
        self.play(Write(future_text))
        self.wait(10)

        self.play(FadeOut(heading3, before_image, after_image, application_text, future_text))