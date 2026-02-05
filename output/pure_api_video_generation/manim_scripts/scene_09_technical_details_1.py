from manim import *

class PositionalEncodingScene(Scene):
    def construct(self):
        # --- Introduction (0-15 seconds) ---
        title = Text("Positional Encoding: Adding Order to Chaos", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        intro_text = Text("Word embeddings represent words as vectors, but they lose information about word order.", font_size=28)
        intro_text.scale_to_fit_width(10)
        intro_text.next_to(title, DOWN, buff=0.5)
        self.play(Write(intro_text))
        self.wait(10)

        # --- The Problem: Order Matters (15-30 seconds) ---
        problem_title = Text("Why Order Matters", font_size=32)
        problem_title.scale_to_fit_width(10)
        problem_title.to_edge(UP)
        self.play(Transform(title, problem_title))

        example_sentence1 = Text("The cat sat on the mat.", font_size=28)
        example_sentence1.scale_to_fit_width(10)
        example_sentence1.next_to(problem_title, DOWN, buff=0.5)

        example_sentence2 = Text("The mat sat on the cat.", font_size=28)
        example_sentence2.scale_to_fit_width(10)
        example_sentence2.next_to(example_sentence1, DOWN, buff=0.5)

        self.play(Write(example_sentence1))
        self.wait(3)
        self.play(Write(example_sentence2))
        self.wait(5)

        highlight_order = Indicate(example_sentence1[0:3], color=YELLOW, scale_factor=1.2)
        highlight_order2 = Indicate(example_sentence2[0:3], color=YELLOW, scale_factor=1.2)
        self.play(highlight_order, highlight_order2)
        self.wait(5)

        # --- Introducing Positional Encoding (30-45 seconds) ---
        pe_title = Text("Introducing Positional Encoding", font_size=32)
        pe_title.scale_to_fit_width(10)
        self.play(Transform(title, pe_title))

        pe_explanation = Text("Positional encoding adds information about the position of each word in the sequence.", font_size=28)
        pe_explanation.scale_to_fit_width(10)
        pe_explanation.next_to(pe_title, DOWN, buff=0.5)
        self.play(Write(pe_explanation))
        self.wait(10)

        # --- Sine and Cosine Waves (45-60 seconds) ---
        sine_cosine_title = Text("Sine and Cosine Waves", font_size=32)
        sine_cosine_title.scale_to_fit_width(10)
        self.play(Transform(title, sine_cosine_title))

        axes = Axes(
            x_range=[0, 10, 1],
            y_range=[-1.5, 1.5, 0.5],
            x_length=6,
            y_length=3,
            axis_config={"include_numbers": False}
        ).to_edge(DOWN)

        sine_wave = axes.plot(lambda x: np.sin(x), color=BLUE)
        cosine_wave = axes.plot(lambda x: np.cos(x), color=GREEN)

        self.play(Create(axes), Create(sine_wave), Create(cosine_wave))
        self.wait(5)

        sine_label = Text("Sine Wave", font_size=24, color=BLUE).next_to(sine_wave, UP)
        cosine_label = Text("Cosine Wave", font_size=24, color=GREEN).next_to(cosine_wave, UP)
        self.play(Write(sine_label), Write(cosine_label))
        self.wait(5)

        # --- The Formula (60-75 seconds) ---
        formula_title = Text("The Positional Encoding Formula", font_size=32)
        formula_title.scale_to_fit_width(10)
        self.play(Transform(title, formula_title))

        formula_pe = MathTex(
            "PE(pos, 2i) = sin(pos / 10000^{\\frac{2i}{d_{model}}})",
            "PE(pos, 2i+1) = cos(pos / 10000^{\\frac{2i}{d_{model}}})",
            font_size=28
        ).scale_to_fit_width(10)
        formula_pe.next_to(formula_title, DOWN, buff=0.5)
        self.play(Write(formula_pe))
        self.wait(10)

        formula_explanation = Text("pos = position, i = dimension", font_size=24).next_to(formula_pe, DOWN, buff=0.5)
        self.play(Write(formula_explanation))
        self.wait(5)

        # --- Adding PE to Word Embeddings (75-90 seconds) ---
        embedding_title = Text("Adding Positional Encoding", font_size=32)
        embedding_title.scale_to_fit_width(10)
        self.play(Transform(title, embedding_title))

        word_embedding = Rectangle(color=ORANGE, width=2, height=1).to_edge(LEFT)
        pe_vector = Rectangle(color=BLUE, width=2, height=1).next_to(word_embedding, RIGHT)

        embedding_label = Text("Word Embedding", font_size=24, color=ORANGE).next_to(word_embedding, DOWN)
        pe_label = Text("Positional Encoding", font_size=24, color=BLUE).next_to(pe_vector, DOWN)

        self.play(Create(word_embedding), Create(pe_vector), Write(embedding_label), Write(pe_label))
        self.wait(3)

        combined_embedding = Rectangle(color=PURPLE, width=2, height=1).next_to(pe_vector, RIGHT)
        arrow = Arrow(pe_vector.get_right(), combined_embedding.get_left())
        addition_text = Text(" + ", font_size=32).next_to(arrow, UP)

        self.play(Create(arrow), Write(addition_text), Create(combined_embedding))
        self.wait(5)

        # --- Before and After (90-105 seconds) ---
        comparison_title = Text("Before and After", font_size=32)
        comparison_title.scale_to_fit_width(10)
        self.play(Transform(title, comparison_title))

        before_embedding = Rectangle(color=ORANGE, width=2, height=1).to_edge(LEFT)
        after_embedding = Rectangle(color=PURPLE, width=2, height=1).to_edge(RIGHT)

        before_label = Text("Without Positional Encoding", font_size=24, color=ORANGE).next_to(before_embedding, DOWN)
        after_label = Text("With Positional Encoding", font_size=24, color=PURPLE).next_to(after_embedding, DOWN)

        self.play(Create(before_embedding), Create(after_embedding), Write(before_label), Write(after_label))
        self.wait(5)

        # --- Summary (105-120 seconds) ---
        summary_title = Text("Summary", font_size=32)
        summary_title.scale_to_fit_width(10)
        self.play(Transform(title, summary_title))

        summary_text = Text("Positional encoding adds crucial information about word order to word embeddings, enabling models to understand sequence meaning.", font_size=28)
        summary_text.scale_to_fit_width(10)
        summary_text.next_to(summary_title, DOWN, buff=0.5)
        self.play(Write(summary_text))
        self.wait(10)