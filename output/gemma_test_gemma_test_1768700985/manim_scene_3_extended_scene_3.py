from manim import *

class ProblemDefinitionScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Testing Gemma for Video Generation: Problem Definition & Challenges", font_size=36)
        title.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(FadeOut(title))

        # --- Step 1: Conceptual Overview (60 seconds) ---
        concept_title = Text("The Challenge: From Text to Video", font_size=32)
        concept_title.scale_to_fit_width(12)
        self.play(Write(concept_title))
        self.wait(3)

        text_input = Tex(r"Text \rightarrow Gemma \rightarrow Video", font_size=28)
        text_input.scale_to_fit_width(12)
        self.play(Write(text_input.next_to(concept_title, DOWN, buff=0.5)))
        self.wait(5)

        complexity_box = SurroundingRectangle(text_input, color=BLUE, buff=0.2)
        self.play(Create(complexity_box))
        self.wait(3)

        complexity_text = Text("This is surprisingly complex!", font_size=24)
        complexity_text.scale_to_fit_width(12)
        self.play(Write(complexity_text.next_to(complexity_box, DOWN, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(concept_title, text_input, complexity_box, complexity_text))

        # --- Step 2: Detailed Component Analysis (70 seconds) ---
        analysis_title = Text("Breaking Down the Complexity", font_size=32)
        analysis_title.scale_to_fit_width(12)
        self.play(Write(analysis_title))
        self.wait(3)

        # Visual Metaphor: Gears
        gear1 = Circle(radius=1, color=BLUE)
        gear2 = Circle(radius=1, color=GREEN)
        gear3 = Circle(radius=1, color=ORANGE)

        gear1.move_to(LEFT * 2)
        gear2.move_to(ORIGIN)
        gear3.move_to(RIGHT * 2)

        self.play(Create(gear1), Create(gear2), Create(gear3))
        self.wait(2)

        gear1_label = Text("Text Understanding", font_size=20)
        gear1_label.scale_to_fit_width(8)
        gear1_label.next_to(gear1, DOWN)
        self.play(Write(gear1_label))

        gear2_label = Text("Content Creation", font_size=20)
        gear2_label.scale_to_fit_width(8)
        gear2_label.next_to(gear2, DOWN)
        self.play(Write(gear2_label))

        gear3_label = Text("Visual Rendering", font_size=20)
        gear3_label.scale_to_fit_width(8)
        gear3_label.next_to(gear3, DOWN)
        self.play(Write(gear3_label))

        self.wait(15)

        # Highlight each gear
        self.play(Indicate(gear1, color=BLUE, scale_factor=1.2))
        self.wait(5)
        self.play(Indicate(gear2, color=GREEN, scale_factor=1.2))
        self.wait(5)
        self.play(Indicate(gear3, color=ORANGE, scale_factor=1.2))
        self.wait(10)

        self.play(FadeOut(analysis_title, gear1, gear2, gear3, gear1_label, gear2_label, gear3_label))

        # --- Step 3: Integration and Relationships (60 seconds) ---
        integration_title = Text("Interdependencies & Scalability", font_size=32)
        integration_title.scale_to_fit_width(12)
        self.play(Write(integration_title))
        self.wait(3)

        # Scalability Chart
        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[0, 100, 10],
            axis_config={"include_numbers": True}
        )
        axes.scale_to_fit_width(10)
        axes.add_coordinate_labels()

        graph = axes.plot(lambda x: x**2, x_range=[0, 10], color=BLUE)
        graph_label = Text("Scalability Curve", font_size=20)
        graph_label.scale_to_fit_width(8)
        graph_label.next_to(axes, UP)

        self.play(Create(axes), Write(graph_label))
        self.play(Create(graph))
        self.wait(10)

        # Highlight the steepness of the curve
        self.play(Indicate(graph, color=ORANGE, scale_factor=1.2))
        self.wait(5)

        dependency_text = Text("Each component's performance impacts others.", font_size=24)
        dependency_text.scale_to_fit_width(12)
        self.play(Write(dependency_text.next_to(axes, DOWN, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(integration_title, axes, graph, graph_label, dependency_text))

        # --- Step 4: Practical Applications & Constraints (65 seconds) ---
        application_title = Text("Real-World Constraints & Future Directions", font_size=32)
        application_title.scale_to_fit_width(12)
        self.play(Write(application_title))
        self.wait(3)

        constraint_list = VGroup(
            Text("Computational Cost", font_size=20),
            Text("Data Requirements", font_size=20),
            Text("Content Bias", font_size=20)
        )
        constraint_list.arrange(DOWN, aligned_edge=LEFT)
        constraint_list.scale_to_fit_width(12)
        self.play(Write(constraint_list))
        self.wait(10)

        future_text = Text("Addressing these constraints unlocks powerful possibilities.", font_size=24)
        future_text.scale_to_fit_width(12)
        self.play(Write(future_text.next_to(constraint_list, DOWN, buff=0.5)))
        self.wait(10)

        # Visual Metaphor: Horizon
        horizon = Line(color=PURPLE, stroke_width=2)
        horizon.move_to(DOWN * 3)
        horizon.generate_target()
        horizon.target.shift(DOWN * 2)

        self.play(Create(horizon))
        self.play(MoveToTarget(horizon))
        self.wait(10)

        future_possibilities = Text("Expanding the horizon of video generation.", font_size=24)
        future_possibilities.scale_to_fit_width(12)
        self.play(Write(future_possibilities.next_to(horizon.target, UP, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(application_title, constraint_list, future_text, horizon, future_possibilities))