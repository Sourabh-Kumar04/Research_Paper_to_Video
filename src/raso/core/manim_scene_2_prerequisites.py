from manim import *

class FoundationsScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Essential Foundations: Building Your Knowledge From Scratch", font_size=36)
        title.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(FadeOut(title))

        # --- Section 1: Algorithms as Recipes (60 seconds) ---
        section_title_1 = Text("Algorithms: Recipes for Computation", font_size=32)
        section_title_1.scale_to_fit_width(12)
        self.play(Write(section_title_1))
        self.wait(3)

        recipe_image = ImageMobject("recipe.png").scale(0.7) # Replace with actual image path
        self.play(FadeIn(recipe_image))
        self.wait(5)

        algorithm_text = Text("An algorithm is a step-by-step procedure to solve a problem.", font_size=28)
        algorithm_text.scale_to_fit_width(12)
        self.play(Write(algorithm_text.next_to(recipe_image, DOWN)))
        self.wait(10)

        recipe_highlight = SurroundingRectangle(recipe_image, color=YELLOW)
        self.play(Create(recipe_highlight))
        self.wait(5)
        self.play(FadeOut(recipe_highlight))

        example_algorithm = Text("Example: Making a sandwich\n1. Get bread\n2. Add filling\n3. Close sandwich", font_size=24)
        example_algorithm.scale_to_fit_width(12)
        self.play(Write(example_algorithm.next_to(algorithm_text, DOWN)))
        self.wait(10)

        self.play(FadeOut(recipe_image, algorithm_text, example_algorithm, section_title_1))
        self.wait(2)

        # --- Section 2: Data Structures as Organization (60 seconds) ---
        section_title_2 = Text("Data Structures: Organizing Information", font_size=32)
        section_title_2.scale_to_fit_width(12)
        self.play(Write(section_title_2))
        self.wait(3)

        filing_cabinet_image = ImageMobject("filing_cabinet.png").scale(0.7) # Replace with actual image path
        self.play(FadeIn(filing_cabinet_image))
        self.wait(5)

        data_structure_text = Text("A data structure is a way to store and organize data.", font_size=28)
        data_structure_text.scale_to_fit_width(12)
        self.play(Write(data_structure_text.next_to(filing_cabinet_image, DOWN)))
        self.wait(10)

        filing_highlight = SurroundingRectangle(filing_cabinet_image, color=GREEN)
        self.play(Create(filing_highlight))
        self.wait(5)
        self.play(FadeOut(filing_highlight))

        example_data_structure = Text("Example: A list of names\n[Alice, Bob, Charlie]", font_size=24)
        example_data_structure.scale_to_fit_width(12)
        self.play(Write(example_data_structure.next_to(data_structure_text, DOWN)))
        self.wait(10)

        self.play(FadeOut(filing_cabinet_image, data_structure_text, example_data_structure, section_title_2))
        self.wait(2)

        # --- Section 3: Mathematical Precision Language (60 seconds) ---
        section_title_3 = Text("Mathematical Notation: A Precise Language", font_size=32)
        section_title_3.scale_to_fit_width(12)
        self.play(Write(section_title_3))
        self.wait(3)

        music_score_image = ImageMobject("music_score.png").scale(0.7) # Replace with actual image path
        self.play(FadeIn(music_score_image))
        self.wait(5)

        function_text = Text("f(x) = y", font_size=36)
        function_text.scale_to_fit_width(12)
        self.play(Write(function_text.next_to(music_score_image, DOWN)))
        self.wait(5)

        explanation_text = Text("x = input, y = output, f = the rule", font_size=28)
        explanation_text.scale_to_fit_width(12)
        self.play(Write(explanation_text.next_to(function_text, DOWN)))
        self.wait(10)

        music_highlight = SurroundingRectangle(music_score_image, color=ORANGE)
        self.play(Create(music_highlight))
        self.wait(5)
        self.play(FadeOut(music_highlight))

        example_function = Text("Example: f(x) = x + 2\nIf x = 3, then y = 5", font_size=24)
        example_function.scale_to_fit_width(12)
        self.play(Write(example_function.next_to(explanation_text, DOWN)))
        self.wait(10)

        self.play(FadeOut(music_score_image, function_text, explanation_text, example_function, section_title_3))
        self.wait(2)

        # --- Section 4: Complete Foundation Overview (57.25 seconds) ---
        section_title_4 = Text("Putting It All Together", font_size=32)
        section_title_4.scale_to_fit_width(12)
        self.play(Write(section_title_4))
        self.wait(3)

        foundation_elements = VGroup(
            Text("Algorithms", font_size=24).scale_to_fit_width(6),
            Text("Data Structures", font_size=24).scale_to_fit_width(6),
            Text("Mathematical Notation", font_size=24).scale_to_fit_width(6)
        ).arrange(DOWN, aligned_edge=LEFT)

        self.play(Write(foundation_elements))
        self.wait(10)

        connection_arrow = Arrow(foundation_elements.get_right(), Text("Computational Thinking", font_size=28).scale_to_fit_width(8).next_to(foundation_elements, RIGHT))
        self.play(Create(connection_arrow))
        self.wait(10)

        summary_text = Text("These are the building blocks for understanding computer science.", font_size=28)
        summary_text.scale_to_fit_width(12)
        self.play(Write(summary_text.next_to(connection_arrow, DOWN)))
        self.wait(15)

        self.play(FadeOut(section_title_4, foundation_elements, connection_arrow, summary_text))
        self.wait(2)