from manim import *

class ScaledDotProductAttention(Scene):
    def construct(self):
        # --- Introduction (10 seconds) ---
        title = Text("Scaled Dot-Product Attention", font_size=48)
        title.scale_to_fit_width(10)
        subtitle = Text("The Heart of the Transformer", font_size=32)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(7)

        # --- Queries, Keys, and Values (30 seconds) ---
        self.clear()
        search_engine = SVGMobject("search_engine.svg", width=4, height=3) # Replace with actual SVG path or file
        search_engine.move_to(ORIGIN)
        self.play(Create(search_engine))
        self.wait(2)

        query_text = Text("Query: What are cats?", font_size=28)
        query_text.scale_to_fit_width(8)
        query_text.next_to(search_engine, UP, buff=0.5)
        self.play(Write(query_text))
        self.wait(3)

        key_text = Text("Keys: Documents about animals", font_size=28)
        key_text.scale_to_fit_width(8)
        key_text.next_to(query_text, DOWN, aligned_edge=LEFT, buff=0.5)
        self.play(Write(key_text))
        self.wait(3)

        value_text = Text("Values: Content of those documents", font_size=28)
        value_text.scale_to_fit_width(8)
        value_text.next_to(key_text, DOWN, aligned_edge=LEFT, buff=0.5)
        self.play(Write(value_text))
        self.wait(7)

        self.play(Indicate(query_text, color=ORANGE), Indicate(key_text, color=ORANGE), Indicate(value_text, color=ORANGE))
        self.wait(10)

        # --- Dot Product Calculation (40 seconds) ---
        self.clear()
        q = Tex("Q = Query", font_size=32)
        k = Tex("K = Key", font_size=32)
        v = Tex("V = Value", font_size=32)
        q.to_edge(UP)
        k.next_to(q, DOWN, aligned_edge=LEFT)
        v.next_to(k, DOWN, aligned_edge=LEFT)

        self.play(Write(q), Write(k), Write(v))
        self.wait(2)

        dot_product = Tex("Q \\cdot K^T", font_size=32)
        dot_product.next_to(v, DOWN, buff=1)
        self.play(Write(dot_product))
        self.wait(5)

        explanation_dot = Text("Measures similarity between Query and Keys", font_size=24)
        explanation_dot.scale_to_fit_width(8)
        explanation_dot.next_to(dot_product, DOWN, buff=0.5)
        self.play(Write(explanation_dot))
        self.wait(10)

        scaled_dot_product = Tex("Q \\cdot K^T / \\sqrt{d_k}", font_size=32)
        scaled_dot_product.next_to(explanation_dot, DOWN, buff=1)
        self.play(Write(scaled_dot_product))
        self.wait(5)

        explanation_scale = Text("Scaling prevents gradients from vanishing", font_size=24)
        explanation_scale.scale_to_fit_width(8)
        explanation_scale.next_to(scaled_dot_product, DOWN, buff=0.5)
        self.play(Write(explanation_scale))
        self.wait(10)

        # --- Softmax and Attention Weights (40 seconds) ---
        self.clear()
        softmax_formula = Tex("softmax(\\frac{Q \\cdot K^T}{\\sqrt{d_k}})", font_size=32)
        softmax_formula.to_edge(UP)
        self.play(Write(softmax_formula))
        self.wait(3)

        explanation_softmax = Text("Normalizes scores into probabilities", font_size=24)
        explanation_softmax.scale_to_fit_width(8)
        explanation_softmax.next_to(softmax_formula, DOWN, buff=0.5)
        self.play(Write(explanation_softmax))
        self.wait(7)

        attention_weights = Tex("Attention Weights", font_size=32)
        attention_weights.next_to(explanation_softmax, DOWN, buff=1)
        self.play(Write(attention_weights))
        self.wait(5)

        attention_equation = Tex("Attention(Q, K, V) = softmax(\\frac{Q \\cdot K^T}{\\sqrt{d_k}})V", font_size=32)
        attention_equation.next_to(attention_weights, DOWN, buff=1)
        attention_equation.set_color(PURPLE)
        self.play(Write(attention_equation))
        self.wait(10)

        explanation_attention = Text("Weighted sum of Values based on attention weights", font_size=24)
        explanation_attention.scale_to_fit_width(8)
        explanation_attention.next_to(attention_equation, DOWN, buff=0.5)
        self.play(Write(explanation_attention))
        self.wait(10)

        # --- Summary (20 seconds) ---
        self.clear()
        summary_title = Text("In Summary", font_size=48)
        summary_title.scale_to_fit_width(10)
        self.play(Write(summary_title))
        self.wait(3)

        summary_points = VGroup(
            Text("Attention focuses on relevant parts of the input.", font_size=28),
            Text("Queries, Keys, and Values are core components.", font_size=28),
            Text("Softmax normalizes scores for probability distribution.", font_size=28)
        )
        summary_points.arrange(DOWN, aligned_edge=LEFT)
        summary_points.scale_to_fit_width(10)
        self.play(Write(summary_points))
        self.wait(17)