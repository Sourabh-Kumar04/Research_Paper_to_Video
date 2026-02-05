from manim import *

class AttentionPower(Scene):
    def construct(self):
        # --- Opening Title ---
        title = Text("The Power of Attention: Why This Architecture Works", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        self.play(FadeOut(title))

        # --- RNN vs Transformer - Sequential vs Parallel ---
        rnn_title = Text("RNNs: Sequential Processing", font_size=32)
        rnn_title.scale_to_fit_width(8)
        rnn_box = SurroundingRectangle(rnn_title, color=BLUE, buff=0.2)
        self.play(Create(rnn_box), Write(rnn_title))
        self.wait(3)

        rnn_sequence = VGroup(*[Rectangle(color=BLUE, width=0.5, height=0.5).arrange(RIGHT) for _ in range(5)])
        arrow_rnn = Arrow(rnn_sequence[0].get_center(), rnn_sequence[1].get_center(), buff=0.1)
        self.play(Create(rnn_sequence), Create(arrow_rnn))
        self.wait(5)
        self.play(FadeOut(rnn_sequence, arrow_rnn, rnn_box))

        transformer_title = Text("Transformers: Parallel Processing", font_size=32)
        transformer_title.scale_to_fit_width(8)
        transformer_box = SurroundingRectangle(transformer_title, color=GREEN, buff=0.2)
        self.play(Create(transformer_box), Write(transformer_title))
        self.wait(3)

        transformer_sequence = VGroup(*[Rectangle(color=GREEN, width=0.5, height=0.5).arrange(DOWN) for _ in range(5)])
        self.play(Create(transformer_sequence))
        self.wait(5)
        self.play(FadeOut(transformer_sequence, transformer_box))

        comparison_text = Text("RNNs process data sequentially, one step at a time.\nTransformers process all data simultaneously.", font_size=28)
        comparison_text.scale_to_fit_width(10)
        self.play(Write(comparison_text))
        self.wait(10)
        self.play(FadeOut(comparison_text))

        # --- Long-Range Dependencies ---
        long_range_title = Text("Long-Range Dependencies", font_size=32)
        long_range_title.scale_to_fit_width(8)
        self.play(Write(long_range_title))
        self.wait(3)

        sentence = Text("The cat sat on the mat, and it was fluffy.", font_size=28)
        sentence.scale_to_fit_width(10)
        self.play(Write(sentence))
        self.wait(5)

        # Highlight "it" and "cat"
        it_highlight = SurroundingRectangle(sentence[11:13], color=ORANGE, buff=0.1)
        cat_highlight = SurroundingRectangle(sentence[4:7], color=ORANGE, buff=0.1)
        self.play(Create(it_highlight), Create(cat_highlight))
        self.wait(8)
        self.play(FadeOut(it_highlight, cat_highlight))

        rnn_difficulty = Text("RNNs struggle to connect 'it' to 'cat' over long distances.", font_size=28)
        rnn_difficulty.scale_to_fit_width(10)
        self.play(Write(rnn_difficulty))
        self.wait(8)
        self.play(FadeOut(rnn_difficulty))

        attention_explanation = Text("Attention allows the model to directly connect any two words, regardless of distance.", font_size=28)
        attention_explanation.scale_to_fit_width(10)
        self.play(Write(attention_explanation))
        self.wait(10)
        self.play(FadeOut(attention_explanation))

        # --- Attention Weights Visualization ---
        attention_title = Text("Visualizing Attention Weights", font_size=32)
        attention_title.scale_to_fit_width(8)
        self.play(Write(attention_title))
        self.wait(3)

        words = ["The", "cat", "sat", "on", "the", "mat", "and", "it", "was", "fluffy"]
        word_objects = VGroup(*[Text(word, font_size=24).scale_to_fit_width(1.5) for word in words])
        word_objects.arrange(DOWN, aligned_edge=LEFT)
        self.play(Create(word_objects))
        self.wait(3)

        # Create attention weight matrix (simplified)
        attention_matrix = [[0.1, 0.8, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                            [0.8, 0.1, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                            [0.1, 0.0, 0.7, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.2, 0.6, 0.2, 0.0, 0.0, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.2, 0.7, 0.1, 0.0, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.0, 0.1, 0.8, 0.1, 0.0, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.7, 0.2, 0.0, 0.0],
                            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.6, 0.2, 0.0],
                            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.7, 0.1],
                            [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.8]]

        # Visualize attention weights as lines
        for i in range(len(words)):
            for j in range(len(words)):
                if attention_matrix[i][j] > 0.5:
                    line = Line(word_objects[i].get_center(), word_objects[j].get_center(), color=ORANGE, stroke_width=attention_matrix[i][j]*3)
                    self.play(Create(line))
                    self.wait(0.5)

        self.wait(10)
        self.play(FadeOut(word_objects, *[line for line in self.mobjects if isinstance(line, Line)]))
        self.play(FadeOut(attention_title))

        # --- Interpretability ---
        interpretability_title = Text("Interpretability: Understanding Predictions", font_size=32)
        interpretability_title.scale_to_fit_width(8)
        self.play(Write(interpretability_title))
        self.wait(3)

        interpretability_text = Text("Attention weights reveal which parts of the input the model focuses on when making predictions.", font_size=28)
        interpretability_text.scale_to_fit_width(10)
        self.play(Write(interpretability_text))
        self.wait(10)
        self.play(FadeOut(interpretability_title, interpretability_text))

        # --- Summary ---
        summary_title = Text("Key Takeaways", font_size=36)
        summary_title.scale_to_fit_width(8)
        self.play(Write(summary_title))
        self.wait(3)

        summary_points = VGroup(
            Text("Parallelization: Transformers are much faster than RNNs.", font_size=28),
            Text("Long-Range Dependencies: Attention handles distant relationships effectively.", font_size=28),
            Text("Interpretability: Attention weights provide insights into model reasoning.", font_size=28)
        )
        summary_points.arrange(DOWN, aligned_edge=LEFT)
        summary_points.scale_to_fit_width(10)
        self.play(Write(summary_points))
        self.wait(10)
        self.play(FadeOut(summary_title, summary_points))