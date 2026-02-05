from manim import *

class MultiHeadAttentionScene(Scene):
    def construct(self):
        # Color scheme
        orange = ORANGE
        purple = PURPLE

        # --- Opening Title Slide (10 seconds) ---
        title = Text("Multi-Head Attention: Capturing Diverse Relationships", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        context = Text("Understanding the core mechanism behind modern NLP models", font_size=28)
        context.scale_to_fit_width(10)
        context.next_to(title, DOWN)
        self.play(Write(context))
        self.wait(5)
        self.play(FadeOut(title, context))

        # --- Single-Head Attention Introduction (20 seconds) ---
        single_head_title = Text("Single-Head Attention: A Quick Recap", font_size=32)
        single_head_title.scale_to_fit_width(10)
        self.play(Write(single_head_title))
        self.wait(2)

        # Simplified diagram of single-head attention
        query = Text("Query (Q)", font_size=24)
        key = Text("Key (K)", font_size=24)
        value = Text("Value (V)", font_size=24)
        query.arrange(DOWN, aligned_edge=LEFT)
        key.arrange(DOWN, aligned_edge=LEFT)
        value.arrange(DOWN, aligned_edge=LEFT)
        query.next_to(single_head_title, DOWN, buff=0.5)

        attention_box = SurroundingRectangle(query, key, value, color=BLUE, buff=0.2)
        attention_output = Text("Attention Output", font_size=24)
        attention_output.next_to(attention_box, RIGHT)

        self.play(Create(attention_box), Write(attention_output))
        self.wait(5)
        self.play(Indicate(query, color=YELLOW, scale_factor=1.2), Indicate(key, color=YELLOW, scale_factor=1.2), Indicate(value, color=YELLOW, scale_factor=1.2))
        self.wait(5)
        self.play(FadeOut(single_head_title, query, key, value, attention_box, attention_output))

        # --- The Limitation of Single-Head Attention (15 seconds) ---
        limitation_title = Text("The Problem: Limited Relationship Capture", font_size=32)
        limitation_title.scale_to_fit_width(10)
        self.play(Write(limitation_title))
        self.wait(3)

        sentence = Text("The cat sat on the mat.", font_size=28)
        sentence.scale_to_fit_width(10)
        sentence.next_to(limitation_title, DOWN)
        self.play(Write(sentence))
        self.wait(5)

        explanation = Text("Single-head attention might focus only on 'cat' and 'sat', missing the 'mat' relationship.", font_size=24)
        explanation.scale_to_fit_width(10)
        explanation.next_to(sentence, DOWN)
        self.play(Write(explanation))
        self.wait(5)
        self.play(FadeOut(limitation_title, sentence, explanation))

        # --- Introducing Multi-Head Attention (20 seconds) ---
        multi_head_title = Text("Multi-Head Attention: Capturing Diverse Relationships", font_size=32)
        multi_head_title.scale_to_fit_width(10)
        self.play(Write(multi_head_title))
        self.wait(2)

        # Visual metaphor: multiple lenses
        lenses = VGroup(*[Circle(radius=0.5, color=orange) for _ in range(4)])
        lenses.arrange(RIGHT, buff=0.3)
        lenses.next_to(multi_head_title, DOWN)
        self.play(Create(lenses))
        self.wait(5)

        explanation_lenses = Text("Each 'head' is like a different lens, focusing on different aspects of the input.", font_size=24)
        explanation_lenses.scale_to_fit_width(10)
        explanation_lenses.next_to(lenses, DOWN)
        self.play(Write(explanation_lenses))
        self.wait(5)
        self.play(FadeOut(multi_head_title, lenses, explanation_lenses))

        # --- The Multi-Head Attention Process (40 seconds) ---
        process_title = Text("How Multi-Head Attention Works", font_size=32)
        process_title.scale_to_fit_width(10)
        self.play(Write(process_title))
        self.wait(2)

        # Input sequence
        input_seq = Text("Input Sequence (X)", font_size=28)
        input_seq.next_to(process_title, DOWN)
        self.play(Write(input_seq))
        self.wait(2)

        # Linear Projections
        linear_proj_title = Text("1. Linear Projections", font_size=24)
        linear_proj_title.next_to(input_seq, DOWN)
        self.play(Write(linear_proj_title))

        q_proj = Text("Q = XW_Q", font_size=20)
        k_proj = Text("K = XW_K", font_size=20)
        v_proj = Text("V = XW_V", font_size=20)
        q_proj.next_to(linear_proj_title, DOWN, aligned_edge=LEFT)
        k_proj.next_to(q_proj, RIGHT)
        v_proj.next_to(k_proj, RIGHT)
        self.play(Write(q_proj), Write(k_proj), Write(v_proj))
        self.wait(5)

        # Multiple Heads
        heads_title = Text("2. Multiple Heads (Parallel Attention)", font_size=24)
        heads_title.next_to(v_proj, DOWN)
        self.play(Write(heads_title))

        head1 = Rectangle(color=orange, width=2, height=1)
        head2 = Rectangle(color=orange, width=2, height=1)
        head1.next_to(heads_title, DOWN, aligned_edge=LEFT)
        head2.next_to(head1, RIGHT)
        self.play(Create(head1), Create(head2))
        self.wait(3)

        # Concatenation and Transformation
        concat_title = Text("3. Concatenation & Transformation", font_size=24)
        concat_title.next_to(head2, DOWN)
        self.play(Write(concat_title))

        concat_formula = MathTex("Concat(head_1, ..., head_h)W_O", font_size=20)
        concat_formula.next_to(concat_title, DOWN)
        self.play(Write(concat_formula))
        self.wait(5)

        self.play(FadeOut(process_title, input_seq, linear_proj_title, q_proj, k_proj, v_proj, heads_title, head1, head2, concat_title, concat_formula))

        # --- Comparison Table (20 seconds) ---
        comparison_title = Text("Single-Head vs. Multi-Head Attention", font_size=32)
        comparison_title.scale_to_fit_width(10)
        self.play(Write(comparison_title))
        self.wait(2)

        table_data = [
            ["Feature", "Single-Head", "Multi-Head"],
            ["Relationship Capture", "Limited", "Diverse"],
            ["Parallel Processing", "No", "Yes"],
            ["Complexity", "Lower", "Higher"]
        ]

        table = Table(table_data, include_header=True, row_labels=None, col_labels=None, font_size=20)
        table.scale_to_fit_width(10)
        table.next_to(comparison_title, DOWN)
        self.play(Create(table))
        self.wait(10)
        self.play(FadeOut(comparison_title, table))

        # --- Conclusion (10 seconds) ---
        conclusion_title = Text("Multi-Head Attention: A Powerful Tool", font_size=32)
        conclusion_title.scale_to_fit_width(10)
        self.play(Write(conclusion_title))
        self.wait(5)
        summary = Text("Enables models to understand complex relationships within data.", font_size=24)
        summary.scale_to_fit_width(10)
        summary.next_to(conclusion_title, DOWN)
        self.play(Write(summary))
        self.wait(5)
        self.play(FadeOut(conclusion_title, summary))