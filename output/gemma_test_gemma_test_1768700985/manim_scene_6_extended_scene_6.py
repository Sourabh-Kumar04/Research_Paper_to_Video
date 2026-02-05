from manim import *

class GemmaTestingScene(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Implementation & Engineering: Testing Gemma for Video Generation", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("Building Robust and Efficient Video Generation Systems", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(5)
        self.play(FadeOut(title, subtitle))

        # --- Step 1: Conceptual Overview (40 seconds) ---
        concept_title = Text("1. Conceptual Overview: The Pipeline", font_size=32)
        concept_title.scale_to_fit_width(12)
        self.play(Write(concept_title))
        self.wait(3)

        input_box = Rectangle(color=BLUE, width=2, height=1)
        input_box.move_to(LEFT * 3)
        input_text = Text("Input Video", font_size=24)
        input_text.move_to(input_box.get_center())
        input_text.scale_to_fit_width(1.8)

        processing_box = Rectangle(color=ORANGE, width=3, height=1)
        processing_box.move_to(ORIGIN)
        processing_text = Text("Gemma Model", font_size=24)
        processing_text.move_to(processing_box.get_center())
        processing_text.scale_to_fit_width(2.8)

        output_box = Rectangle(color=GREEN, width=2, height=1)
        output_box.move_to(RIGHT * 3)
        output_text = Text("Output Video", font_size=24)
        output_text.move_to(output_box.get_center())
        output_text.scale_to_fit_width(1.8)

        arrow1 = Arrow(input_box.get_right(), processing_box.get_left(), buff=0.2)
        arrow2 = Arrow(processing_box.get_right(), output_box.get_left(), buff=0.2)

        self.play(Create(input_box), Write(input_text))
        self.play(Create(processing_box), Write(processing_text))
        self.play(Create(output_box), Write(output_text))
        self.play(Create(arrow1), Create(arrow2))
        self.wait(10)

        explanation = Text("Gemma takes video input, processes it, and generates a new video.", font_size=24)
        explanation.scale_to_fit_width(12)
        explanation.next_to(output_box, DOWN, buff=0.5)
        self.play(Write(explanation))
        self.wait(10)
        self.play(FadeOut(concept_title, input_box, input_text, processing_box, processing_text, output_box, output_text, arrow1, arrow2, explanation))

        # --- Step 2: Detailed Component Analysis (50 seconds) ---
        component_title = Text("2. Component Analysis: Inside Gemma", font_size=32)
        component_title.scale_to_fit_width(12)
        self.play(Write(component_title))
        self.wait(3)

        encoder_box = Rectangle(color=BLUE, width=2, height=1)
        encoder_box.move_to(LEFT * 3)
        encoder_text = Text("Encoder", font_size=24)
        encoder_text.move_to(encoder_box.get_center())
        encoder_text.scale_to_fit_width(1.8)

        transformer_box = Rectangle(color=ORANGE, width=3, height=1)
        transformer_box.move_to(ORIGIN)
        transformer_text = Text("Transformer", font_size=24)
        transformer_text.move_to(transformer_box.get_center())
        transformer_text.scale_to_fit_width(2.8)

        decoder_box = Rectangle(color=GREEN, width=2, height=1)
        decoder_box.move_to(RIGHT * 3)
        decoder_text = Text("Decoder", font_size=24)
        decoder_text.move_to(decoder_box.get_center())
        decoder_text.scale_to_fit_width(1.8)

        arrow3 = Arrow(encoder_box.get_right(), transformer_box.get_left(), buff=0.2)
        arrow4 = Arrow(transformer_box.get_right(), decoder_box.get_left(), buff=0.2)

        self.play(Create(encoder_box), Write(encoder_text))
        self.play(Create(transformer_box), Write(transformer_text))
        self.play(Create(decoder_box), Write(decoder_text))
        self.play(Create(arrow3), Create(arrow4))
        self.wait(10)

        encoder_explain = Text("Encodes input into a latent representation.", font_size=20)
        encoder_explain.scale_to_fit_width(12)
        encoder_explain.next_to(encoder_box, DOWN, buff=0.5)

        transformer_explain = Text("Processes the latent representation.", font_size=20)
        transformer_explain.scale_to_fit_width(12)
        transformer_explain.next_to(transformer_box, DOWN, buff=0.5)

        decoder_explain = Text("Decodes the representation into output video.", font_size=20)
        decoder_explain.scale_to_fit_width(12)
        decoder_explain.next_to(decoder_box, DOWN, buff=0.5)

        self.play(Write(encoder_explain))
        self.play(Write(transformer_explain))
        self.play(Write(decoder_explain))
        self.wait(15)
        self.play(FadeOut(component_title, encoder_box, encoder_text, transformer_box, transformer_text, decoder_box, decoder_text, arrow3, arrow4, encoder_explain, transformer_explain, decoder_explain))

        # --- Step 3: Memory Management Visualization (45 seconds) ---
        memory_title = Text("3. Memory Management: Optimizing for Efficiency", font_size=32)
        memory_title.scale_to_fit_width(12)
        self.play(Write(memory_title))
        self.wait(3)

        memory_before = Text("Without Optimization: High Memory Usage", font_size=24)
        memory_before.scale_to_fit_width(12)
        memory_before.move_to(UP)

        memory_after = Text("With Optimization: Reduced Memory Usage", font_size=24)
        memory_after.scale_to_fit_width(12)
        memory_after.move_to(DOWN)

        memory_bar_before = BarGraph(x_range=[0, 10], y_range=[0, 100], bar_width=1, bar_height=80, color=RED)
        memory_bar_after = BarGraph(x_range=[0, 10], y_range=[0, 100], bar_width=1, bar_height=30, color=GREEN)

        memory_bar_before.move_to(memory_before.get_center() + DOWN * 1.5)
        memory_bar_after.move_to(memory_after.get_center() + DOWN * 1.5)

        self.play(Write(memory_before), Create(memory_bar_before))
        self.wait(5)
        self.play(Write(memory_after), Create(memory_bar_after))
        self.wait(10)

        optimization_text = Text("Techniques: Quantization, Gradient Checkpointing", font_size=20)
        optimization_text.scale_to_fit_width(12)
        optimization_text.next_to(memory_after, DOWN, buff=0.5)
        self.play(Write(optimization_text))
        self.wait(10)
        self.play(FadeOut(memory_title, memory_before, memory_bar_before, memory_after, memory_bar_after, optimization_text))

        # --- Step 4: Error Correction Mechanisms (40 seconds) ---
        error_title = Text("4. Error Correction: Ensuring Quality", font_size=32)
        error_title.scale_to_fit_width(12)
        self.play(Write(error_title))
        self.wait(3)

        error_detection_box = Rectangle(color=PURPLE, width=3, height=1)
        error_detection_box.move_to(LEFT)
        error_detection_text = Text("Error Detection", font_size=24)
        error_detection_text.move_to(error_detection_box.get_center())
        error_detection_text.scale_to_fit_width(2.8)

        error_correction_box = Rectangle(color=ORANGE, width=3, height=1)
        error_correction_box.move_to(RIGHT)
        error_correction_text = Text("Error Correction", font_size=24)
        error_correction_text.move_to(error_correction_box.get_center())
        error_correction_text.scale_to_fit_width(2.8)

        arrow5 = Arrow(error_detection_box.get_right(), error_correction_box.get_left(), buff=0.2)

        self.play(Create(error_detection_box), Write(error_detection_text))
        self.play(Create(error_correction_box), Write(error_correction_text))
        self.play(Create(arrow5))
        self.wait(10)

        error_explain = Text("Techniques: Redundancy, Checksums, Retransmission", font_size=20)
        error_explain.scale_to_fit_width(12)
        error_explain.next_to(error_correction_box, DOWN, buff=0.5)
        self.play(Write(error_explain))
        self.wait(10)
        self.play(FadeOut(error_title, error_detection_box, error_detection_text, error_correction_box, error_correction_text, arrow5, error_explain))