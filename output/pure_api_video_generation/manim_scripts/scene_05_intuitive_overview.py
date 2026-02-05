from manim import *

class TransformerAttentionScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("The Transformer: A High-Level Look at Attention", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("Understanding the Core Concepts", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(7)
        self.play(FadeOut(title, subtitle))

        # --- Attention as a Focusing Mechanism ---
        attention_title = Text("Attention: Focusing on What Matters", font_size=32)
        attention_title.scale_to_fit_width(12)
        self.play(Write(attention_title))
        self.wait(3)

        sentence = Text("The quick brown fox jumps over the lazy dog.", font_size=24)
        sentence.scale_to_fit_width(12)
        self.play(Write(sentence))
        self.wait(3)

        # Spotlight metaphor
        spotlight = Circle(radius=0.5, color=ORANGE, stroke_width=2)
        spotlight.move_to(sentence[0])  # Start on "The"
        self.play(Create(spotlight))
        self.wait(2)

        # Move spotlight across words
        for i in range(1, len(sentence.get_words())):
            self.play(spotlight.animate.move_to(sentence.get_words()[i]))
            self.wait(1)

        self.play(FadeOut(spotlight))
        attention_explanation = Text("Attention allows the model to focus on different parts of the input when processing it.", font_size=20)
        attention_explanation.scale_to_fit_width(12)
        self.play(Write(attention_explanation))
        self.wait(8)
        self.play(FadeOut(attention_title, sentence, attention_explanation))

        # --- Encoder-Decoder Architecture ---
        encoder_decoder_title = Text("The Encoder-Decoder Structure", font_size=32)
        encoder_decoder_title.scale_to_fit_width(12)
        self.play(Write(encoder_decoder_title))
        self.wait(3)

        # Simplified diagram
        encoder = Rectangle(color=BLUE, width=3, height=2)
        decoder = Rectangle(color=BLUE, width=3, height=2)
        encoder.move_to(LEFT * 3)
        decoder.move_to(RIGHT * 3)

        encoder_text = Text("Encoder", font_size=24)
        encoder_text.move_to(encoder.get_center())
        decoder_text = Text("Decoder", font_size=24)
        decoder_text.move_to(decoder.get_center())

        self.play(Create(encoder), Create(encoder_text))
        self.wait(2)
        self.play(Create(decoder), Create(decoder_text))
        self.wait(2)

        # Connection between encoder and decoder
        arrow = Arrow(encoder.get_right(), decoder.get_left(), color=BLUE)
        self.play(Create(arrow))
        self.wait(5)

        encoder_decoder_explanation = Text("The encoder processes the input, and the decoder generates the output based on the encoded information.", font_size=20)
        encoder_decoder_explanation.scale_to_fit_width(12)
        self.play(Write(encoder_decoder_explanation))
        self.wait(8)
        self.play(FadeOut(encoder_decoder_title, encoder, decoder, encoder_text, decoder_text, arrow, encoder_decoder_explanation))

        # --- Attention within Encoder-Decoder ---
        attention_in_ed_title = Text("Attention: Connecting Encoder and Decoder", font_size=32)
        attention_in_ed_title.scale_to_fit_width(12)
        self.play(Write(attention_in_ed_title))
        self.wait(3)

        # Simplified diagram with attention lines
        encoder = Rectangle(color=BLUE, width=3, height=2)
        decoder = Rectangle(color=BLUE, width=3, height=2)
        encoder.move_to(LEFT * 3)
        decoder.move_to(RIGHT * 3)

        encoder_text = Text("Encoder", font_size=24)
        encoder_text.move_to(encoder.get_center())
        decoder_text = Text("Decoder", font_size=24)
        decoder_text.move_to(decoder.get_center())

        self.play(Create(encoder), Create(encoder_text))
        self.wait(1)
        self.play(Create(decoder), Create(decoder_text))
        self.wait(1)

        # Attention lines
        attention_lines = [Line(encoder.get_right(), decoder.get_left(), color=ORANGE) for _ in range(3)]
        self.play(Create(attention_lines[0]))
        self.wait(1)
        self.play(Create(attention_lines[1]))
        self.wait(1)
        self.play(Create(attention_lines[2]))
        self.wait(3)

        attention_in_ed_explanation = Text("Attention lines show which parts of the encoder output the decoder is focusing on.", font_size=20)
        attention_in_ed_explanation.scale_to_fit_width(12)
        self.play(Write(attention_in_ed_explanation))
        self.wait(8)
        self.play(FadeOut(attention_in_ed_title, encoder, decoder, encoder_text, decoder_text, *attention_lines, attention_in_ed_explanation))

        # --- Parallel Processing ---
        parallel_title = Text("Parallel Processing: Speeding Things Up", font_size=32)
        parallel_title.scale_to_fit_width(12)
        self.play(Write(parallel_title))
        self.wait(3)

        # Visual metaphor: People in a discussion
        person1 = Circle(radius=0.5, color=GREEN)
        person2 = Circle(radius=0.5, color=RED)
        person1.move_to(LEFT * 2)
        person2.move_to(RIGHT * 2)

        self.play(Create(person1), Create(person2))
        self.wait(1)

        # Lines representing communication (attention)
        line1 = Line(person1.get_center(), person2.get_center(), color=ORANGE)
        self.play(Create(line1))
        self.wait(2)

        # Multiple lines representing parallel communication
        line2 = Line(person1.get_center(), person2.get_center(), color=ORANGE)
        line2.shift(UP * 0.5)
        self.play(Create(line2))
        self.wait(2)

        parallel_explanation = Text("Transformers can process all parts of the input simultaneously, unlike sequential models.", font_size=20)
        parallel_explanation.scale_to_fit_width(12)
        self.play(Write(parallel_explanation))
        self.wait(8)
        self.play(FadeOut(parallel_title, person1, person2, line1, line2, parallel_explanation))

        # --- Summary ---
        summary_title = Text("Key Takeaways", font_size=32)
        summary_title.scale_to_fit_width(12)
        self.play(Write(summary_title))
        self.wait(3)

        summary_points = VGroup(
            Text("Attention focuses on relevant parts of the input.", font_size=20),
            Text("Transformers use an encoder-decoder architecture.", font_size=20),
            Text("Parallel processing enables faster computation.", font_size=20)
        )
        summary_points.arrange(DOWN, aligned_edge=LEFT)
        summary_points.scale_to_fit_width(12)
        self.play(Write(summary_points))
        self.wait(10)
        self.play(FadeOut(summary_title, summary_points))