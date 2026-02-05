from manim import *

class BeforeTransformers(Scene):
    def construct(self):
        # --- Title Slide (5 seconds) ---
        title = Text("Before Transformers: RNNs, CNNs & Attention", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("Foundations for Modern Sequence Modeling", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(2)
        self.play(FadeOut(title, subtitle))

        # --- RNN Introduction (25 seconds) ---
        rnn_title = Text("Recurrent Neural Networks (RNNs)", font_size=32)
        rnn_title.scale_to_fit_width(12)
        self.play(Write(rnn_title))
        self.wait(2)

        # Simple RNN diagram
        rect1 = Rectangle(color=BLUE, width=1, height=1)
        rect2 = Rectangle(color=BLUE, width=1, height=1).next_to(rect1, RIGHT)
        rect3 = Rectangle(color=BLUE, width=1, height=1).next_to(rect2, RIGHT)

        arrow1 = Arrow(rect1.get_right(), rect2.get_left())
        arrow2 = Arrow(rect2.get_right(), rect3.get_left())

        self.play(Create(rect1), Create(arrow1))
        self.wait(2)
        self.play(Create(rect2), Create(arrow2))
        self.wait(2)
        self.play(Create(rect3))
        self.wait(3)

        text1 = Text("Input Sequence", font_size=24)
        text1.scale_to_fit_width(8)
        text1.next_to(rect1, DOWN)
        self.play(Write(text1))

        text2 = Text("Hidden State", font_size=24)
        text2.scale_to_fit_width(8)
        text2.next_to(rect1, UP)
        self.play(Write(text2))

        self.wait(5)
        self.play(FadeOut(rnn_title, rect1, rect2, rect3, arrow1, arrow2, text1, text2))

        # --- Vanishing Gradient Problem (20 seconds) ---
        vg_title = Text("The Vanishing Gradient Problem", font_size=32)
        vg_title.scale_to_fit_width(12)
        self.play(Write(vg_title))
        self.wait(2)

        # Visual metaphor: a long, winding path
        path = VMobject(color=RED)
        path.set_points_as_corners([LEFT * 5, LEFT * 4 + DOWN, LEFT * 3 + UP, LEFT * 2 + DOWN, LEFT * 1 + UP, ORIGIN + DOWN, RIGHT + UP])

        gradient_arrow = Arrow(LEFT * 5, RIGHT + UP, buff=0.1, color=GREEN)
        gradient_arrow.add_tip(Tip(length=0.2))

        self.play(Create(path), Create(gradient_arrow))
        self.wait(5)

        text3 = Text("Gradient weakens as it travels back", font_size=24)
        text3.scale_to_fit_width(10)
        text3.next_to(path, DOWN)
        self.play(Write(text3))
        self.wait(8)
        self.play(FadeOut(vg_title, path, gradient_arrow, text3))

        # --- LSTM/GRU Introduction (20 seconds) ---
        lstm_title = Text("LSTMs & GRUs: Solving the Problem", font_size=32)
        lstm_title.scale_to_fit_width(12)
        self.play(Write(lstm_title))
        self.wait(2)

        # Simplified LSTM cell diagram
        lstm_cell = Rectangle(color=BLUE, width=2, height=1.5)
        gate_text = Text("Gates control information flow", font_size=24)
        gate_text.scale_to_fit_width(10)
        gate_text.next_to(lstm_cell, DOWN)

        self.play(Create(lstm_cell), Write(gate_text))
        self.wait(8)

        text4 = Text("More complex memory cells", font_size=24)
        text4.scale_to_fit_width(10)
        text4.next_to(lstm_cell, UP)
        self.play(Write(text4))
        self.wait(5)
        self.play(FadeOut(lstm_title, lstm_cell, gate_text, text4))

        # --- CNNs for Sequence Processing (20 seconds) ---
        cnn_title = Text("Convolutional Neural Networks (CNNs) for Sequences", font_size=32)
        cnn_title.scale_to_fit_width(12)
        self.play(Write(cnn_title))
        self.wait(2)

        # CNN diagram
        conv_layer = Rectangle(color=BLUE, width=4, height=1)
        input_seq = Text("Input Sequence", font_size=24)
        input_seq.scale_to_fit_width(10)
        input_seq.next_to(conv_layer, DOWN)

        self.play(Create(conv_layer), Write(input_seq))
        self.wait(5)

        text5 = Text("Parallel processing of local patterns", font_size=24)
        text5.scale_to_fit_width(10)
        text5.next_to(conv_layer, UP)
        self.play(Write(text5))
        self.wait(8)
        self.play(FadeOut(cnn_title, conv_layer, input_seq, text5))

        # --- Attention Mechanism (15 seconds) ---
        attention_title = Text("Attention: Focusing on What Matters", font_size=32)
        attention_title.scale_to_fit_width(12)
        self.play(Write(attention_title))
        self.wait(2)

        # Attention highlighting
        sentence = Text("The quick brown fox jumps over the lazy dog.", font_size=24)
        sentence.scale_to_fit_width(12)
        highlight = SurroundingRectangle(sentence[10:13], color=ORANGE, buff=0.1) # Highlight "fox"

        self.play(Write(sentence), Create(highlight))
        self.wait(5)

        text6 = Text("Attention weights highlight relevant words", font_size=24)
        text6.scale_to_fit_width(10)
        text6.next_to(sentence, DOWN)
        self.play(Write(text6))
        self.wait(3)
        self.play(FadeOut(attention_title, sentence, highlight, text6))