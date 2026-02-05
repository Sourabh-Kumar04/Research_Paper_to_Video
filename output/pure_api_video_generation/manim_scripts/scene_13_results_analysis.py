from manim import *

class TransformerPerformance(Scene):
    def construct(self):
        # --- Opening Title Slide ---
        title = Text("Breaking Records: The Transformer's Performance", font_size=36)
        title.scale_to_fit_width(12)
        subtitle = Text("A Beginner's Guide to Revolutionary Translation", font_size=28)
        subtitle.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(5)
        self.play(FadeOut(title, subtitle))

        # --- Introducing Machine Translation ---
        heading1 = Text("What is Machine Translation?", font_size=32)
        heading1.scale_to_fit_width(12)
        self.play(Write(heading1))
        self.wait(3)

        text1 = Text("Converting text from one language to another automatically.", font_size=28)
        text1.scale_to_fit_width(12)
        self.play(Write(text1))
        self.wait(5)

        # --- Previous Models & Their Limitations ---
        heading2 = Text("Before Transformers: The Struggle", font_size=32)
        heading2.scale_to_fit_width(12)
        self.play(Transform(heading1, heading2))
        self.wait(3)

        text2 = Text("Older models (like RNNs) had trouble with long sentences.", font_size=28)
        text2.scale_to_fit_width(12)
        self.play(Transform(text1, text2))
        self.wait(5)

        # Visual Metaphor: A winding road representing RNNs struggling with long sentences
        road = Line(LEFT * 5, RIGHT * 5, color=RED)
        road.set_stroke(width=3)
        self.play(Create(road))
        self.wait(3)
        
        text3 = Text("Information 'forgotten' as it traveled along the road.", font_size=24)
        text3.scale_to_fit_width(12)
        text3.next_to(road, DOWN)
        self.play(Write(text3))
        self.wait(5)
        self.play(FadeOut(road, text3))

        # --- Introducing the Transformer ---
        heading3 = Text("Enter the Transformer!", font_size=32)
        heading3.scale_to_fit_width(12)
        self.play(Transform(heading1, heading3))
        self.wait(3)

        text4 = Text("A new architecture that revolutionized machine translation.", font_size=28)
        text4.scale_to_fit_width(12)
        self.play(Transform(text1, text4))
        self.wait(5)

        # Visual Metaphor: A direct highway representing the Transformer's ability to handle long sentences
        highway = Line(LEFT * 5, RIGHT * 5, color=GREEN)
        highway.set_stroke(width=3)
        self.play(Create(highway))
        self.wait(3)

        text5 = Text("Information travels directly, no 'forgetting'!", font_size=24)
        text5.scale_to_fit_width(12)
        text5.next_to(highway, DOWN)
        self.play(Write(text5))
        self.wait(5)
        self.play(FadeOut(highway, text5))

        # --- BLEU Score Comparison ---
        heading4 = Text("Measuring Performance: The BLEU Score", font_size=32)
        heading4.scale_to_fit_width(12)
        self.play(Transform(heading1, heading4))
        self.wait(3)

        text6 = Text("BLEU (Bilingual Evaluation Understudy) measures translation quality.", font_size=28)
        text6.scale_to_fit_width(12)
        self.play(Transform(text1, text6))
        self.wait(5)

        # Bar Graph
        bars = VGroup(*[Bar(height=i/10, width=0.8, color=GREEN) for i in [0.4, 0.6, 0.8, 0.9]])
        bars.arrange(DOWN, aligned_edge=LEFT)
        labels = VGroup(*[Text(str(i/10), font_size=24) for i in [4, 6, 8, 9]])
        labels.arrange(DOWN, aligned_edge=LEFT)
        
        x_labels = VGroup(*[Text("RNN", font_size=24), Text("LSTM", font_size=24), Text("GRU", font_size=24), Text("Transformer", font_size=24)])
        x_labels.arrange(DOWN, aligned_edge=LEFT)
        x_labels.next_to(bars, DOWN)

        self.play(Create(bars), Write(labels))
        self.play(Write(x_labels))
        self.wait(8)
        self.play(FadeOut(bars, labels, x_labels))

        # --- Training Time Reduction ---
        heading5 = Text("Faster Training: A Huge Advantage", font_size=32)
        heading5.scale_to_fit_width(12)
        self.play(Transform(heading1, heading5))
        self.wait(3)

        text7 = Text("Transformers train much faster than previous models.", font_size=28)
        text7.scale_to_fit_width(12)
        self.play(Transform(text1, text7))
        self.wait(5)

        # Chart showing training time reduction
        chart = Line(start=ORIGIN, end=RIGHT * 5, color=BLUE)
        point1 = Dot(LEFT * 2, chart, color=RED)
        label1 = Text("RNN/LSTM/GRU", point1.get_top(), font_size=24)
        point2 = Dot(RIGHT * 2, chart, color=GREEN)
        label2 = Text("Transformer", point2.get_top(), font_size=24)
        
        self.play(Create(chart), Create(point1), Write(label1), Create(point2), Write(label2))
        self.wait(8)
        self.play(FadeOut(chart, point1, label1, point2, label2))

        # --- Example Translations ---
        heading6 = Text("Seeing is Believing: Example Translations", font_size=32)
        heading6.scale_to_fit_width(12)
        self.play(Transform(heading1, heading6))
        self.wait(3)

        text8 = Text("The Transformer produces more fluent and accurate translations.", font_size=28)
        text8.scale_to_fit_width(12)
        self.play(Transform(text1, text8))
        self.wait(5)

        # Example Translation 1
        example1_before = Text("The cat is on the mat.", font_size=24)
        example1_after = Text("Le chat est sur le tapis.", font_size=24)
        example1_before.scale_to_fit_width(12)
        example1_after.scale_to_fit_width(12)
        example1_before.next_to(text1, DOWN)
        example1_after.next_to(example1_before, DOWN)
        self.play(Write(example1_before))
        self.wait(2)
        self.play(Write(example1_after))
        self.wait(5)

        # --- Summary ---
        heading7 = Text("The Transformer: A Game Changer", font_size=32)
        heading7.scale_to_fit_width(12)
        self.play(Transform(heading1, heading7))
        self.wait(3)

        text9 = Text("Higher quality, faster training, and a new era for machine translation.", font_size=28)
        text9.scale_to_fit_width(12)
        self.play(Transform(text1, text9))
        self.wait(8)

        self.play(FadeOut(heading1, text1))
        self.wait(2)