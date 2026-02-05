from manim import *

class TransformerRevolution(Scene):
    def construct(self):
        # --- Opening Title Slide (10 seconds) ---
        title = Text("Attention is All You Need: The Transformer Revolution", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("Vaswani et al., 2017", font_size=28)
        subtitle.scale_to_fit_width(10)
        subtitle.next_to(title, DOWN, buff=0.5)
        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(5)
        self.play(FadeOut(title, subtitle))

        # --- The Problem: Sequence Transduction (20 seconds) ---
        problem_title = Text("The Challenge: Sequence Transduction", font_size=32)
        problem_title.scale_to_fit_width(10)
        self.play(Write(problem_title))
        self.wait(2)

        # Before: RNN/LSTM Diagram (simplified)
        rnn_box = Rectangle(color=BLUE, width=4, height=2)
        rnn_text = Text("RNN/LSTM", font_size=24)
        rnn_text.move_to(rnn_box.get_center())
        self.play(Create(rnn_box), Write(rnn_text))
        self.wait(3)

        input_seq = Text("Input Sequence", font_size=20)
        input_seq.next_to(rnn_box, LEFT, buff=1)
        output_seq = Text("Output Sequence", font_size=20)
        output_seq.next_to(rnn_box, RIGHT, buff=1)
        arrow_in = Arrow(input_seq.get_right(), rnn_box.get_left())
        arrow_out = Arrow(rnn_box.get_right(), output_seq.get_left())

        self.play(Write(input_seq), Write(output_seq), Create(arrow_in), Create(arrow_out))
        self.wait(5)

        problem_explanation = Text("Recurrent networks process sequentially, limiting parallelization.", font_size=18)
        problem_explanation.scale_to_fit_width(10)
        problem_explanation.next_to(rnn_box, DOWN, buff=1)
        self.play(Write(problem_explanation))
        self.wait(5)

        self.play(FadeOut(problem_title, rnn_box, rnn_text, input_seq, output_seq, arrow_in, arrow_out, problem_explanation))

        # --- Introducing Attention (30 seconds) ---
        attention_title = Text("The Key Idea: Attention", font_size=32)
        attention_title.scale_to_fit_width(10)
        self.play(Write(attention_title))
        self.wait(2)

        attention_explanation = Text("Focus on relevant parts of the input when generating each output.", font_size=18)
        attention_explanation.scale_to_fit_width(10)
        attention_explanation.next_to(attention_title, DOWN, buff=0.5)
        self.play(Write(attention_explanation))
        self.wait(5)

        # Visual Metaphor: Spotlight
        spotlight = Circle(color=YELLOW, radius=0.5)
        input_text = Text("Input Sequence", font_size=20)
        input_text.to_edge(LEFT)
        output_text = Text("Output", font_size=20)
        output_text.to_edge(RIGHT)

        self.play(Write(input_text), Write(output_text))
        self.play(spotlight.move_to(input_text.get_center()))
        self.wait(2)
        self.play(spotlight.move_to(output_text.get_center()))
        self.wait(3)

        # Attention Formula
        attention_formula = MathTex("Attention(Q, K, V) = softmax(\\frac{QK^T}{\\sqrt{d_k}})V", font_size=24)
        attention_formula.scale_to_fit_width(10)
        attention_formula.next_to(attention_explanation, DOWN, buff=1)
        self.play(Write(attention_formula))
        self.wait(5)

        self.play(FadeOut(attention_title, attention_explanation, spotlight, input_text, output_text, attention_formula))

        # --- The Transformer Architecture (50 seconds) ---
        transformer_title = Text("The Transformer: A Parallel Revolution", font_size=32)
        transformer_title.scale_to_fit_width(10)
        self.play(Write(transformer_title))
        self.wait(2)

        # Encoder Block
        encoder_block = Rectangle(color=BLUE, width=6, height=3)
        encoder_text = Text("Encoder Block", font_size=20)
        encoder_text.move_to(encoder_block.get_center())
        self.play(Create(encoder_block), Write(encoder_text))
        self.wait(3)

        # Decoder Block
        decoder_block = Rectangle(color=ORANGE, width=6, height=3)
        decoder_text = Text("Decoder Block", font_size=20)
        decoder_text.move_to(decoder_block.get_center())
        decoder_block.next_to(encoder_block, DOWN, buff=1)
        self.play(Create(decoder_block), Write(decoder_text))
        self.wait(3)

        # Attention Layers
        attention_layer_encoder = Text("Self-Attention", font_size=16)
        attention_layer_encoder.next_to(encoder_block, UP, buff=0.5)
        attention_layer_decoder = Text("Self-Attention & Encoder-Decoder Attention", font_size=16)
        attention_layer_decoder.next_to(decoder_block, UP, buff=0.5)

        self.play(Write(attention_layer_encoder), Write(attention_layer_decoder))
        self.wait(5)

        # Overall Architecture Diagram
        transformer_diagram = VGroup(encoder_block, decoder_block, attention_layer_encoder, attention_layer_decoder)
        self.play(transformer_diagram.animate.shift(LEFT * 2))

        input_sequence_transformer = Text("Input Sequence", font_size=20)
        input_sequence_transformer.to_edge(LEFT)
        output_sequence_transformer = Text("Output Sequence", font_size=20)
        output_sequence_transformer.to_edge(RIGHT)

        arrow_in_transformer = Arrow(input_sequence_transformer.get_right(), encoder_block.get_left())
        arrow_out_transformer = Arrow(decoder_block.get_right(), output_sequence_transformer.get_left())

        self.play(Write(input_sequence_transformer), Write(output_sequence_transformer), Create(arrow_in_transformer), Create(arrow_out_transformer))
        self.wait(10)

        self.play(FadeOut(transformer_title, encoder_block, decoder_block, attention_layer_encoder, attention_layer_decoder, input_sequence_transformer, output_sequence_transformer, arrow_in_transformer, arrow_out_transformer))

        # --- Impact and Future Directions (30 seconds) ---
        impact_title = Text("Impact and Future Directions", font_size=32)
        impact_title.scale_to_fit_width(10)
        self.play(Write(impact_title))
        self.wait(2)

        impact_points = VGroup(
            Text("Breakthrough in Machine Translation", font_size=18),
            Text("Foundation for Large Language Models (LLMs)", font_size=18),
            Text("Ongoing research in efficiency and interpretability", font_size=18)
        )
        impact_points.arrange(DOWN, aligned_edge=LEFT, buff=0.5)
        impact_points.scale_to_fit_width(10)
        impact_points.next_to(impact_title, DOWN, buff=1)
        self.play(Write(impact_points))
        self.wait(10)

        # Visual Metaphor: Catalyst
        catalyst_image = ImageMobject("catalyst.png") # Replace with actual image path
        catalyst_image.scale_to_fit_width(6)
        catalyst_image.next_to(impact_points, RIGHT, buff=2)
        self.play(FadeIn(catalyst_image))
        self.wait(5)

        self.play(FadeOut(impact_title, impact_points, catalyst_image))