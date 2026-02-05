from manim import *

class VideoGenerationChallenges(Scene):
    def construct(self):
        # --- SCENE 1: Problem Definition (60 seconds) ---
        title = Text("Testing Gemma for Video Generation: Challenges", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        problem_statement = Text(
            "Generating high-quality, coherent videos is incredibly complex.\n"
            "It's far more challenging than generating images or text.",
            font_size=28
        )
        problem_statement.scale_to_fit_width(10)
        self.play(Write(problem_statement.next_to(title, DOWN, buff=0.5)))
        self.wait(10)

        complexity_visual = VGroup(
            Text("Image Generation", font_size=24),
            Rectangle(color=GREEN, width=2, height=0.5).next_to(Text("Image Generation", font_size=24), DOWN),
        ).arrange(DOWN)

        complexity_visual2 = VGroup(
            Text("Text Generation", font_size=24),
            Rectangle(color=GREEN, width=4, height=0.5).next_to(Text("Text Generation", font_size=24), DOWN),
        ).arrange(DOWN)

        complexity_visual3 = VGroup(
            Text("Video Generation", font_size=24),
            Rectangle(color=RED, width=8, height=0.5).next_to(Text("Video Generation", font_size=24), DOWN),
        ).arrange(DOWN)

        complexity_group = VGroup(complexity_visual, complexity_visual2, complexity_visual3).arrange(RIGHT)
        self.play(Create(complexity_group.next_to(problem_statement, DOWN, buff=1)))
        self.wait(15)

        self.play(FadeOut(title, problem_statement, complexity_group))

        # --- SCENE 2: Core Challenges - Multi-Dimensionality (70 seconds) ---
        title2 = Text("Multi-Dimensional Challenges", font_size=36)
        title2.scale_to_fit_width(10)
        self.play(Write(title2))
        self.wait(5)

        dimensions = VGroup(
            Text("Visual Content", font_size=28, color=BLUE),
            Text("Temporal Coherence", font_size=28, color=BLUE),
            Text("Audio Integration", font_size=28, color=BLUE),
            Text("Semantic Understanding", font_size=28, color=BLUE)
        ).arrange(DOWN, aligned_edge=LEFT)

        self.play(Write(dimensions))
        self.wait(10)

        # Visual metaphor: a cube representing the multi-dimensional space
        cube = Cube(side_length=2, fill_color=BLUE, fill_opacity=0.5)
        cube.move_to(RIGHT * 3)
        self.play(Create(cube))
        self.wait(10)

        # Highlight each dimension
        self.play(Indicate(dimensions[0], color=YELLOW))
        self.wait(5)
        self.play(Indicate(dimensions[1], color=YELLOW))
        self.wait(5)
        self.play(Indicate(dimensions[2], color=YELLOW))
        self.wait(5)
        self.play(Indicate(dimensions[3], color=YELLOW))
        self.wait(10)

        self.play(FadeOut(title2, dimensions, cube))

        # --- SCENE 3: Scalability & Real-World Constraints (70 seconds) ---
        title3 = Text("Scalability & Real-World Constraints", font_size=36)
        title3.scale_to_fit_width(10)
        self.play(Write(title3))
        self.wait(5)

        # Comparison chart: Before (low resolution, slow generation) vs. After (high resolution, fast generation)
        before_col = VGroup(
            Text("Low Resolution", font_size=24),
            Text("Slow Generation", font_size=24)
        ).arrange(DOWN)

        after_col = VGroup(
            Text("High Resolution", font_size=24),
            Text("Fast Generation", font_size=24)
        ).arrange(DOWN)

        comparison_group = VGroup(before_col, after_col).arrange(RIGHT)
        self.play(Write(comparison_group))
        self.wait(10)

        # Add visual representation of speed (arrows)
        arrow_before = Arrow(before_col.get_bottom(), RIGHT * 2, buff=0.2)
        arrow_after = Arrow(after_col.get_bottom(), RIGHT * 2, buff=0.2)

        self.play(Create(arrow_before), Create(arrow_after))
        self.wait(5)

        constraints = VGroup(
            Text("Computational Cost", font_size=24, color=ORANGE),
            Text("Data Requirements", font_size=24, color=ORANGE),
            Text("Memory Limitations", font_size=24, color=ORANGE)
        ).arrange(DOWN, aligned_edge=LEFT).next_to(comparison_group, DOWN, buff=1)

        self.play(Write(constraints))
        self.wait(15)

        self.play(FadeOut(title3, comparison_group, arrow_before, arrow_after, constraints))

        # --- SCENE 4: Future Possibilities & Gemma's Role (48 seconds) ---
        title4 = Text("Future Possibilities & Gemma's Role", font_size=36)
        title4.scale_to_fit_width(10)
        self.play(Write(title4))
        self.wait(5)

        potential_applications = VGroup(
            Text("Personalized Content Creation", font_size=24, color=PURPLE),
            Text("Automated Video Editing", font_size=24, color=PURPLE),
            Text("Interactive Storytelling", font_size=24, color=PURPLE)
        ).arrange(DOWN, aligned_edge=LEFT)

        self.play(Write(potential_applications))
        self.wait(10)

        gemma_role = Text("Gemma can help address these challenges by...", font_size=28, color=ORANGE)
        gemma_role.next_to(potential_applications, DOWN, buff=1)
        self.play(Write(gemma_role))
        self.wait(10)

        # Final thought
        final_thought = Text("Continued research and development are crucial.", font_size=24)
        final_thought.next_to(gemma_role, DOWN, buff=0.5)
        self.play(Write(final_thought))
        self.wait(10)

        self.play(FadeOut(title4, potential_applications, gemma_role, final_thought))