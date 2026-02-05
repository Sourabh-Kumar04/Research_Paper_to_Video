from manim import *

class AttentionMechanism(Scene):
    def construct(self):
        # --- Title Slide ---
        title = Text("Delving Deeper: The Math Behind Attention", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("Understanding the Core Concepts", font_size=28)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(10)
        self.play(FadeOut(title, subtitle))

        # --- Introduction to Attention ---
        attention_text = Text("Attention allows models to focus on relevant parts of the input.", font_size=32)
        attention_text.scale_to_fit_width(10)
        self.play(Write(attention_text))
        self.wait(8)
        self.play(FadeOut(attention_text))

        # --- Q, K, V Explanation ---
        q_text = Text("Q (Query): What are we looking for?", font_size=32)
        q_text.scale_to_fit_width(10)
        k_text = Text("K (Key): What does each element offer?", font_size=32)
        k_text.scale_to_fit_width(10)
        v_text = Text("V (Value): The actual content of each element.", font_size=32)
        v_text.scale_to_fit_width(10)

        self.play(Write(q_text))
        self.wait(5)
        self.play(Write(k_text))
        self.wait(5)
        self.play(Write(v_text))
        self.wait(10)
        self.play(FadeOut(q_text, k_text, v_text))

        # --- Matrix Multiplication QKᵀ ---
        qk_text = Tex("Q Kᵀ", font_size=48, color=BLUE)
        qk_text.scale_to_fit_width(8)
        qk_explanation = Text("Dot product of Query and Transposed Key.  Measures similarity.", font_size=28)
        qk_explanation.scale_to_fit_width(10)

        self.play(Write(qk_text))
        self.wait(5)
        self.play(Write(qk_explanation))
        self.wait(10)

        # Visualizing Matrix Multiplication
        matrix_q = Matrix([[1, 2], [3, 4]], element_font_size=24)
        matrix_k_t = Matrix([[5, 6], [7, 8]], element_font_size=24)
        matrix_qk = Matrix([[19, 22], [43, 50]], element_font_size=24)

        matrix_qk.move_to(RIGHT * 3)

        self.play(Create(matrix_q), Create(matrix_k_t))
        self.wait(3)
        arrow = Arrow(matrix_q.get_right(), matrix_qk.get_left(), buff=0.5)
        arrow_2 = Arrow(matrix_k_t.get_right(), matrix_qk.get_left(), buff=0.5)
        self.play(Create(arrow), Create(arrow_2), Write(matrix_qk))
        self.wait(8)
        self.play(FadeOut(matrix_q, matrix_k_t, matrix_qk, arrow, arrow_2, qk_text, qk_explanation))

        # --- Scaling Factor √dk ---
        scaling_text = Tex("QKᵀ / √{d_k}", font_size=48, color=BLUE)
        scaling_text.scale_to_fit_width(8)
        scaling_explanation = Text("Scaling prevents gradients from becoming too small.", font_size=28)
        scaling_explanation.scale_to_fit_width(10)

        self.play(Write(scaling_text))
        self.wait(5)
        self.play(Write(scaling_explanation))
        self.wait(10)
        self.play(FadeOut(scaling_text, scaling_explanation))

        # --- Softmax Function ---
        softmax_text = Tex("softmax(QKᵀ / √{d_k})", font_size=48, color=PURPLE)
        softmax_text.scale_to_fit_width(8)
        softmax_explanation = Text("Transforms scores into probabilities.  Highlights important elements.", font_size=28)
        softmax_explanation.scale_to_fit_width(10)

        self.play(Write(softmax_text))
        self.wait(5)
        self.play(Write(softmax_explanation))
        self.wait(10)
        self.play(FadeOut(softmax_text, softmax_explanation))

        # --- Weighted Sum ---
        weighted_sum_text = Tex("Attention(Q, K, V) = softmax(QKᵀ / √{d_k})V", font_size=48, color=PURPLE)
        weighted_sum_text.scale_to_fit_width(8)
        weighted_sum_explanation = Text("Weighted sum of values, based on attention weights.", font_size=28)
        weighted_sum_explanation.scale_to_fit_width(10)

        self.play(Write(weighted_sum_text))
        self.wait(5)
        self.play(Write(weighted_sum_explanation))
        self.wait(15)
        self.play(FadeOut(weighted_sum_text, weighted_sum_explanation))

        # --- Summary ---
        summary_text = Text("Attention: Focus on what matters!", font_size=36)
        summary_text.scale_to_fit_width(10)
        self.play(Write(summary_text))
        self.wait(10)
        self.play(FadeOut(summary_text))