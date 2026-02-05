from manim import *

class GemmaVideoGenerationImpact(Scene):
    def construct(self):
        # --- SCENE 1: Conceptual Overview (60 seconds) ---
        title = Text("Gemma: Transforming Video Generation", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        overview_text = Text(
            "Video generation is evolving rapidly.\n"
            "Traditionally, it required extensive resources and expertise.\n"
            "Gemma, a new model, aims to democratize video creation.",
            font_size=28
        )
        overview_text.scale_to_fit_width(10)
        self.play(Write(overview_text))
        self.wait(15)

        # Visual Metaphor: Seed to Tree
        seed = Circle(color=BLUE, radius=0.5)
        seed.move_to(DOWN * 2)
        tree = VGroup(
            Polygon(color=GREEN, vertices=[LEFT * 3, RIGHT * 3, UP * 2, DOWN * 2]),
            *[Circle(color=GREEN, radius=0.2).move_to(LEFT * 2 + UP * i) for i in range(3)],
            *[Circle(color=GREEN, radius=0.2).move_to(RIGHT * 2 + UP * i) for i in range(3)]
        )
        tree.move_to(DOWN * 2)
        tree.shift(RIGHT * 4)
        self.play(Create(seed))
        self.wait(3)
        self.play(Transform(seed, tree))
        self.wait(10)

        # Transition to next scene
        self.play(FadeOut(title, overview_text, seed, tree))
        self.wait(2)

        # --- SCENE 2: Detailed Component Analysis (60 seconds) ---
        title2 = Text("Gemma's Core Components", font_size=36)
        title2.scale_to_fit_width(10)
        self.play(Write(title2))
        self.wait(5)

        # Diagram: Input -> Model -> Output
        input_box = Rectangle(color=BLUE, width=2, height=1)
        model_box = Rectangle(color=ORANGE, width=2, height=1)
        output_box = Rectangle(color=GREEN, width=2, height=1)

        input_box.move_to(LEFT * 3)
        model_box.move_to(ORIGIN)
        output_box.move_to(RIGHT * 3)

        input_text = Text("Text Prompt", font_size=24).next_to(input_box, UP)
        model_text = Text("Gemma Model", font_size=24).next_to(model_box, UP)
        output_text = Text("Generated Video", font_size=24).next_to(output_box, UP)

        arrow1 = Arrow(input_box.get_right(), model_box.get_left())
        arrow2 = Arrow(model_box.get_right(), output_box.get_left())

        self.play(Create(input_box), Create(model_box), Create(output_box))
        self.play(Write(input_text), Write(model_text), Write(output_text))
        self.play(Create(arrow1), Create(arrow2))
        self.wait(15)

        # Highlight Model
        self.play(Indicate(model_box, color=YELLOW, scale_factor=1.2))
        self.wait(5)

        # Explain Model (simplified)
        model_explanation = Text(
            "Gemma uses deep learning to translate text into visual content.\n"
            "It learns patterns from vast datasets of videos and text.",
            font_size=24
        )
        model_explanation.scale_to_fit_width(10)
        model_explanation.next_to(model_box, DOWN)
        self.play(Write(model_explanation))
        self.wait(15)

        self.play(FadeOut(title2, input_box, model_box, output_box, input_text, model_text, output_text, model_explanation, arrow1, arrow2))
        self.wait(2)

        # --- SCENE 3: Practical Applications (63 seconds) ---
        title3 = Text("Real-World Applications", font_size=36)
        title3.scale_to_fit_width(10)
        self.play(Write(title3))
        self.wait(5)

        # Application Grid
        app1 = Text("Marketing & Advertising", font_size=28)
        app2 = Text("Education & Training", font_size=28)
        app3 = Text("Content Creation", font_size=28)

        app1.move_to(UP * 2)
        app2.move_to(ORIGIN)
        app3.move_to(DOWN * 2)

        icon1 = ImageMobject("icons8-advertising-64.png", width=1) # Replace with actual icon path
        icon2 = ImageMobject("icons8-school-64.png", width=1) # Replace with actual icon path
        icon3 = ImageMobject("icons8-video-camera-64.png", width=1) # Replace with actual icon path

        icon1.next_to(app1, LEFT)
        icon2.next_to(app2, LEFT)
        icon3.next_to(app3, LEFT)

        self.play(Write(app1), Create(icon1))
        self.wait(8)
        self.play(Write(app2), Create(icon2))
        self.wait(8)
        self.play(Write(app3), Create(icon3))
        self.wait(15)

        # Before/After Comparison (Content Creation)
        before_text = Text("Traditional Video Editing: Time-Consuming", font_size=24)
        after_text = Text("Gemma: Rapid Prototyping & Iteration", font_size=24)

        before_text.move_to(LEFT * 3)
        after_text.move_to(RIGHT * 3)

        self.play(Write(before_text))
        self.wait(5)
        self.play(Write(after_text))
        self.wait(10)

        # Highlight the speed improvement
        arrow_comp = Arrow(before_text.get_right(), after_text.get_left(), buff=0.5)
        self.play(Create(arrow_comp))
        self.wait(10)

        self.play(FadeOut(title3, app1, app2, app3, icon1, icon2, icon3, before_text, after_text, arrow_comp))
        self.wait(2)