from manim import *

class LongRangeDependencies(Scene):
    def construct(self):
        # --- Title Slide (5 seconds) ---
        title = Text("The Core Challenge: Long-Range Dependencies & Parallelization", font_size=36)
        title.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)
        self.play(FadeOut(title))

        # --- Introducing Long-Range Dependencies (30 seconds) ---
        sentence = Text("The cat, which was grey and fluffy, chased the mouse.", font_size=32)
        sentence.scale_to_fit_width(10)
        self.play(Write(sentence))
        self.wait(3)

        cat = sentence[0:3]  # "The" "cat"
        chased = sentence[34:39] # "chased"
        
        cat_box = SurroundingRectangle(cat, color=BLUE, buff=0.1)
        chased_box = SurroundingRectangle(chased, color=BLUE, buff=0.1)

        self.play(Create(cat_box), Create(chased_box))
        self.wait(5)

        arrow = Arrow(cat_box.get_center(), chased_box.get_center(), buff=0.2)
        self.play(Create(arrow))
        self.wait(7)

        dependency_text = Text("Long-Range Dependency: 'cat' influences 'chased'", font_size=28)
        dependency_text.scale_to_fit_width(8)
        dependency_text.next_to(sentence, DOWN, buff=0.5)
        self.play(Write(dependency_text))
        self.wait(10)

        self.play(FadeOut(cat_box, chased_box, arrow, dependency_text))

        # --- Sequential Processing Limitations (30 seconds) ---
        sequential_title = Text("Sequential Processing", font_size=32)
        sequential_title.scale_to_fit_width(10)
        self.play(Write(sequential_title))
        self.wait(3)

        blocks = VGroup(*[Rectangle(color=RED, width=1, height=1) for _ in range(5)])
        blocks.arrange(RIGHT, buff=0.2)
        self.play(Create(blocks))
        self.wait(2)

        # Animate processing one block at a time
        for i in range(5):
            self.play(Indicate(blocks[i], color=YELLOW, scale_factor=1.1))
            self.wait(2)

        self.play(FadeOut(blocks, sequential_title))

        sequential_time_text = Text("Time increases linearly with sequence length.", font_size=28)
        sequential_time_text.scale_to_fit_width(8)
        self.play(Write(sequential_time_text))
        self.wait(10)
        self.play(FadeOut(sequential_time_text))

        # --- The Need for Parallelization (30 seconds) ---
        parallel_title = Text("Parallel Processing", font_size=32)
        parallel_title.scale_to_fit_width(10)
        self.play(Write(parallel_title))
        self.wait(3)

        blocks = VGroup(*[Rectangle(color=BLUE, width=1, height=1) for _ in range(5)])
        blocks.arrange(RIGHT, buff=0.2)
        self.play(Create(blocks))
        self.wait(2)

        # Animate processing all blocks simultaneously
        self.play(Indicate(blocks, color=GREEN, scale_factor=1.1))
        self.wait(2)

        self.play(FadeOut(blocks, parallel_title))

        parallel_time_text = Text("Time remains constant regardless of sequence length.", font_size=28)
        parallel_time_text.scale_to_fit_width(8)
        self.play(Write(parallel_time_text))
        self.wait(10)
        self.play(FadeOut(parallel_time_text))

        # --- RNN vs Transformer (30 seconds) ---
        rnn_title = Text("RNNs: Sequential Bottleneck", font_size=32)
        rnn_title.scale_to_fit_width(10)
        self.play(Write(rnn_title))
        self.wait(3)

        rnn_diagram = Line(start=LEFT, end=RIGHT, color=RED)
        self.play(Create(rnn_diagram))
        self.wait(5)

        info_loss_text = Text("Information Loss over Long Sequences", font_size=28)
        info_loss_text.scale_to_fit_width(8)
        info_loss_text.next_to(rnn_diagram, DOWN, buff=0.5)
        self.play(Write(info_loss_text))
        self.wait(7)

        self.play(FadeOut(rnn_diagram, rnn_title, info_loss_text))

        transformer_title = Text("Transformers: Parallel Power", font_size=32)
        transformer_title.scale_to_fit_width(10)
        self.play(Write(transformer_title))
        self.wait(3)

        transformer_diagram = VGroup(*[Circle(color=BLUE, radius=0.5) for _ in range(5)]).arrange(RIGHT, buff=0.2)
        self.play(Create(transformer_diagram))
        self.wait(5)

        parallel_processing_text = Text("Parallel processing of all sequence elements.", font_size=28)
        parallel_processing_text.scale_to_fit_width(8)
        parallel_processing_text.next_to(transformer_diagram, DOWN, buff=0.5)
        self.play(Write(parallel_processing_text))
        self.wait(7)

        self.play(FadeOut(transformer_diagram, transformer_title, parallel_processing_text))

        # --- Summary (10 seconds) ---
        summary_text = Text("Parallelization is key to handling long-range dependencies efficiently.", font_size=28)
        summary_text.scale_to_fit_width(10)
        self.play(Write(summary_text))
        self.wait(10)