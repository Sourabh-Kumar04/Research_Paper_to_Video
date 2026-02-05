from manim import *

class ResidualConnectionsAndLayerNorm(Scene):
    def construct(self):
        # --- Introduction (15 seconds) ---
        title = Text("Residual Connections & Layer Normalization", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("Stabilizing Deep Neural Network Training", font_size=28)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(7)

        # --- The Vanishing Gradient Problem (30 seconds) ---
        problem_title = Text("The Vanishing Gradient Problem", font_size=32)
        problem_title.scale_to_fit_width(10)
        self.play(FadeOut(title, subtitle), Write(problem_title))
        self.wait(3)

        # Visual metaphor: a ball rolling down a long, winding hill
        hill = Line(LEFT * 5, RIGHT * 5, color=GRAY)
        ball = Circle(radius=0.2, color=RED)
        ball.move_to(LEFT * 5 + DOWN)

        arrow = Arrow(LEFT * 5 + DOWN, RIGHT * 5 + DOWN, buff=0.1)

        self.play(Create(hill), Create(ball), Create(arrow))
        self.wait(5)

        # Animate the ball slowing down
        self.play(ApplyMethod(ball.set_color, GREEN), ball.animate.move_to(RIGHT * 5 + DOWN, rate_func=lambda t: t*t)) # Slow down
        self.wait(5)

        problem_explanation = Text("In deep networks, gradients can become very small as they propagate back.", font_size=24)
        problem_explanation.scale_to_fit_width(10)
        problem_explanation.next_to(hill, UP)
        self.play(Write(problem_explanation))
        self.wait(7)

        self.play(FadeOut(hill, ball, arrow, problem_title, problem_explanation))

        # --- Residual Connections (45 seconds) ---
        residual_title = Text("Residual Connections", font_size=32)
        residual_title.scale_to_fit_width(10)
        self.play(Write(residual_title))
        self.wait(3)

        # Diagram: Simple layer vs. Residual Block
        simple_layer = Rectangle(color=BLUE, width=2, height=1)
        input_node = Circle(radius=0.3, color=GREEN)
        output_node = Circle(radius=0.3, color=RED)

        input_node.move_to(LEFT * 3)
        output_node.move_to(RIGHT * 3)
        simple_layer.move_to(ORIGIN)

        arrow1 = Arrow(input_node.get_right(), simple_layer.get_left())
        arrow2 = Arrow(simple_layer.get_right(), output_node.get_left())

        self.play(Create(input_node), Create(simple_layer), Create(output_node), Create(arrow1), Create(arrow2))
        self.wait(5)

        # Add the residual connection
        residual_connection = Line(input_node.get_right(), output_node.get_left(), color=GREEN)
        self.play(Create(residual_connection))
        self.wait(5)

        residual_explanation = Text("Residual connections add the input directly to the output.", font_size=24)
        residual_explanation.scale_to_fit_width(10)
        residual_explanation.next_to(output_node, UP)
        self.play(Write(residual_explanation))
        self.wait(10)

        residual_benefit = Text("This helps gradients flow more easily, mitigating the vanishing gradient problem.", font_size=24)
        residual_benefit.scale_to_fit_width(10)
        residual_benefit.next_to(residual_explanation, DOWN)
        self.play(Write(residual_benefit))
        self.wait(12)

        self.play(FadeOut(residual_title, input_node, simple_layer, output_node, arrow1, arrow2, residual_connection, residual_explanation, residual_benefit))

        # --- Layer Normalization (30 seconds) ---
        layer_norm_title = Text("Layer Normalization", font_size=32)
        layer_norm_title.scale_to_fit_width(10)
        self.play(Write(layer_norm_title))
        self.wait(3)

        # Visual metaphor: Adjusting the distribution of activations
        activation_distribution = VGroup(*[Dot(x, y, color=BLUE) for x in np.linspace(-3, 3, 50) for y in np.linspace(-3, 3, 50) if x**2 + y**2 <= 9])
        activation_distribution.move_to(ORIGIN)

        self.play(Create(activation_distribution))
        self.wait(5)

        # Normalize the distribution
        normalized_distribution = VGroup(*[Dot(x, y, color=GREEN) for x in np.linspace(-1, 1, 50) for y in np.linspace(-1, 1, 50) if x**2 + y**2 <= 1])
        normalized_distribution.move_to(ORIGIN)

        self.play(Transform(activation_distribution, normalized_distribution))
        self.wait(5)

        layer_norm_explanation = Text("Layer normalization stabilizes learning by normalizing activations across features.", font_size=24)
        layer_norm_explanation.scale_to_fit_width(10)
        layer_norm_explanation.next_to(normalized_distribution, UP)
        self.play(Write(layer_norm_explanation))
        self.wait(12)

        self.play(FadeOut(layer_norm_title, activation_distribution, layer_norm_explanation))

        # --- Conclusion (10 seconds) ---
        conclusion = Text("Residual connections and layer normalization are powerful techniques for training deep networks.", font_size=28)
        conclusion.scale_to_fit_width(10)
        self.play(Write(conclusion))
        self.wait(7)