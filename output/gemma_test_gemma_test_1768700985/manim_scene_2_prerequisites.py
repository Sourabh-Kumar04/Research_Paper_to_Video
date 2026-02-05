from manim import *

class FoundationsScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Essential Foundations: Building Your Knowledge From Scratch", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        self.play(FadeOut(title))

        # --- Section 1: Algorithms as Recipes (60 seconds) ---
        section_title_1 = Text("Algorithms: Recipes for Computation", font_size=32)
        section_title_1.scale_to_fit_width(10)
        self.play(Write(section_title_1))
        self.wait(3)

        recipe_image = ImageMobject("recipe.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(recipe_image))
        self.wait(5)

        algorithm_text = Text("An algorithm is a step-by-step procedure to solve a problem.", font_size=28)
        algorithm_text.scale_to_fit_width(10)
        self.play(Write(algorithm_text.next_to(recipe_image, DOWN)))
        self.wait(10)

        recipe_steps = VGroup(
            Text("1. Gather ingredients", font_size=24),
            Text("2. Follow instructions", font_size=24),
            Text("3. Enjoy the result!", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.7)
        self.play(Write(recipe_steps.next_to(algorithm_text, DOWN)))
        self.wait(10)

        algorithm_example = Text("Example: Sorting numbers in ascending order", font_size=28)
        algorithm_example.scale_to_fit_width(10)
        self.play(Write(algorithm_example.next_to(recipe_steps, DOWN)))
        self.wait(5)

        self.play(FadeOut(recipe_image, algorithm_text, recipe_steps, algorithm_example, section_title_1))

        # --- Section 2: Data Structures as Organization (60 seconds) ---
        section_title_2 = Text("Data Structures: Organizing Information", font_size=32)
        section_title_2.scale_to_fit_width(10)
        self.play(Write(section_title_2))
        self.wait(3)

        filing_cabinet_image = ImageMobject("filing_cabinet.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(filing_cabinet_image))
        self.wait(5)

        data_structure_text = Text("A data structure is a way to store and organize data.", font_size=28)
        data_structure_text.scale_to_fit_width(10)
        self.play(Write(data_structure_text.next_to(filing_cabinet_image, DOWN)))
        self.wait(10)

        unordered_list = VGroup(
            Text("Unorganized data:", font_size=24),
            Text("Numbers: 5, 2, 8, 1, 9", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.7)
        self.play(Write(unordered_list.next_to(data_structure_text, DOWN)))
        self.wait(5)

        ordered_list = VGroup(
            Text("Organized data (sorted):", font_size=24),
            Text("Numbers: 1, 2, 5, 8, 9", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.7)
        self.play(Transform(unordered_list, ordered_list))
        self.wait(10)

        self.play(FadeOut(filing_cabinet_image, data_structure_text, unordered_list, section_title_2))

        # --- Section 3: Mathematical Precision Language (60 seconds) ---
        section_title_3 = Text("Mathematical Notation: A Precise Language", font_size=32)
        section_title_3.scale_to_fit_width(10)
        self.play(Write(section_title_3))
        self.wait(3)

        function_notation = Tex("f(x) = y", font_size=48)
        self.play(Write(function_notation))
        self.wait(5)

        x_label = Text("x = Input", font_size=28)
        y_label = Text("y = Output", font_size=28)
        f_label = Text("f = Rule", font_size=28)
        x_label.scale_to_fit_width(8)
        y_label.scale_to_fit_width(8)
        f_label.scale_to_fit_width(8)

        self.play(Write(x_label.next_to(function_notation, DOWN, buff=0.5).align_to(function_notation[0], LEFT)))
        self.play(Write(y_label.next_to(function_notation, DOWN, buff=0.5).align_to(function_notation[2], RIGHT)))
        self.play(Write(f_label.next_to(function_notation, UP, buff=0.5).align_to(function_notation[0], LEFT)))
        self.wait(10)

        music_score_image = ImageMobject("music_score.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(music_score_image.next_to(function_notation, DOWN)))
        self.wait(10)

        analogy_text = Text("Like a musical score, math notation transforms input into output.", font_size=28)
        analogy_text.scale_to_fit_width(10)
        self.play(Write(analogy_text.next_to(music_score_image, DOWN)))
        self.wait(5)

        self.play(FadeOut(function_notation, x_label, y_label, f_label, music_score_image, analogy_text, section_title_3))

        # --- Section 4: Complete Foundation Overview (57.75 seconds) ---
        section_title_4 = Text("Putting It All Together", font_size=32)
        section_title_4.scale_to_fit_width(10)
        self.play(Write(section_title_4))
        self.wait(3)

        foundation_elements = VGroup(
            Text("Algorithms", font_size=24),
            Text("Data Structures", font_size=24),
            Text("Mathematical Notation", font_size=24)
        ).arrange(DOWN, aligned_edge=LEFT).scale(0.7)
        self.play(Write(foundation_elements))
        self.wait(5)

        connection_arrow = Arrow(foundation_elements.get_right(), Text("Computational Thinking", font_size=28).next_to(foundation_elements, RIGHT))
        self.play(Create(connection_arrow))
        self.wait(10)

        summary_text = Text("These foundations are the building blocks for all computer science concepts.", font_size=28)
        summary_text.scale_to_fit_width(10)
        self.play(Write(summary_text.next_to(connection_arrow, DOWN)))
        self.wait(15)

        self.play(FadeOut(section_title_4, foundation_elements, connection_arrow, summary_text))

        self.wait(5) # Final pause