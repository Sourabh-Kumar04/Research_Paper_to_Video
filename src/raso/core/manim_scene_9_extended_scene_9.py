from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Problem Definition (60 seconds) ---
        title = Text("Conditional Memory via Scalable Lookup", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("A New Axis of Sparsity for Large Language Models", font_size=24)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(7)

        problem_statement = Text("Large Language Models (LLMs) face a core challenge:", font_size=28)
        problem_statement.scale_to_fit_width(10)
        self.play(Write(problem_statement))
        self.wait(3)

        complexity_text = Text("Scaling to handle massive datasets and complex queries.", font_size=28)
        complexity_text.scale_to_fit_width(10)
        self.play(Write(complexity_text))
        self.wait(5)

        # Visual metaphor: Growing tree
        tree = VGroup(
            Line(UP, DOWN, color=GREEN),
            Line(UP, UP + LEFT, color=GREEN),
            Line(UP, UP + RIGHT, color=GREEN)
        ).shift(LEFT * 3)

        self.play(Create(tree))
        self.wait(3)

        growing_branches = VGroup(
            Line(UP + LEFT, UP + LEFT + LEFT, color=GREEN),
            Line(UP + RIGHT, UP + RIGHT + RIGHT, color=GREEN)
        )
        self.play(Create(growing_branches))
        self.wait(5)

        self.play(FadeOut(tree, growing_branches, problem_statement, complexity_text, title, subtitle))

        # --- SCENE 2: Multi-Dimensional Challenge Analysis (80 seconds) ---
        challenge_title = Text("The Multi-Dimensional Challenge", font_size=32)
        challenge_title.scale_to_fit_width(10)
        self.play(Write(challenge_title))
        self.wait(3)

        dimensions = VGroup(
            Text("Data Size", font_size=24),
            Text("Query Complexity", font_size=24),
            Text("Computational Cost", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT)
        for dim in dimensions:
            dim.scale_to_fit_width(8)
        self.play(Write(dimensions))
        self.wait(5)

        # Visual: 3D axes
        axes = ThreeDAxes(x_range=[-5, 5], y_range=[-5, 5], z_range=[-5, 5])
        axes.add_coordinate_labels()
        self.play(Create(axes))
        self.wait(5)

        # Highlight axes
        self.play(Indicate(axes.get_x_axis(), color=BLUE))
        self.play(Indicate(axes.get_y_axis(), color=GREEN))
        self.play(Indicate(axes.get_z_axis(), color=ORANGE))
        self.wait(5)

        # Explain axes
        data_size_label = Text("Data Size", font_size=18).next_to(axes.get_x_axis(), UP)
        query_complexity_label = Text("Query Complexity", font_size=18).next_to(axes.get_y_axis(), UP)
        comp_cost_label = Text("Computational Cost", font_size=18).next_to(axes.get_z_axis(), UP)
        self.play(Write(data_size_label), Write(query_complexity_label), Write(comp_cost_label))
        self.wait(10)

        self.play(FadeOut(challenge_title, dimensions, axes, data_size_label, query_complexity_label, comp_cost_label))

        # --- SCENE 3: Scalability Comparison (70 seconds) ---
        comparison_title = Text("Scalability: Traditional vs. Conditional Memory", font_size=32)
        comparison_title.scale_to_fit_width(10)
        self.play(Write(comparison_title))
        self.wait(3)

        # Create charts
        traditional_chart = Line(start=ORIGIN, end=RIGHT * 5, color=RED)
        conditional_chart = Line(start=ORIGIN, end=RIGHT * 8, color=BLUE)

        self.play(Create(traditional_chart))
        self.wait(3)
        self.play(Create(conditional_chart))
        self.wait(5)

        traditional_label = Text("Traditional Memory", font_size=20).next_to(traditional_chart, UP)
        conditional_label = Text("Conditional Memory", font_size=20).next_to(conditional_chart, UP)
        traditional_label.scale_to_fit_width(8)
        conditional_label.scale_to_fit_width(8)
        self.play(Write(traditional_label), Write(conditional_label))
        self.wait(10)

        # Highlight difference
        self.play(Indicate(conditional_chart, color=GREEN))
        self.wait(5)

        explanation_text = Text("Conditional memory scales more effectively with increasing data and complexity.", font_size=24)
        explanation_text.scale_to_fit_width(10)
        self.play(Write(explanation_text))
        self.wait(15)

        self.play(FadeOut(comparison_title, traditional_chart, conditional_chart, traditional_label, conditional_label, explanation_text))

        # --- SCENE 4: Practical Applications & Future (52.5 seconds) ---
        applications_title = Text("Practical Applications & Future Directions", font_size=32)
        applications_title.scale_to_fit_width(10)
        self.play(Write(applications_title))
        self.wait(3)

        applications_list = VGroup(
            Text("Improved Question Answering", font_size=20),
            Text("More Efficient Code Generation", font_size=20),
            Text("Enhanced Long-Form Text Summarization", font_size=20)
        ).arrange(DOWN, aligned_edge=LEFT)
        for app in applications_list:
            app.scale_to_fit_width(8)
        self.play(Write(applications_list))
        self.wait(10)

        future_text = Text("Conditional memory opens new possibilities for building more powerful and scalable LLMs.", font_size=24)
        future_text.scale_to_fit_width(10)
        self.play(Write(future_text))
        self.wait(15)

        thank_you = Text("Thank You!", font_size=48)
        thank_you.scale_to_fit_width(10)
        self.play(Write(thank_you))
        self.wait(10)