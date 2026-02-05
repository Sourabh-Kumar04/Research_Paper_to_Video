from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Conceptual Overview (60 seconds) ---
        title = Text("Conditional Memory via Scalable Lookup", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("A New Axis of Sparsity for Large Language Models", font_size=24)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(10)

        # Visual Metaphor: Library Analogy
        library_image = ImageMobject("library.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(library_image))
        self.wait(5)

        explanation1 = Text("Traditional LLMs: Like a huge, disorganized library.", font_size=28)
        explanation1.scale_to_fit_width(10)
        self.play(Write(explanation1.next_to(library_image, DOWN)))
        self.wait(10)

        explanation2 = Text("Finding information is slow and inefficient.", font_size=28)
        explanation2.scale_to_fit_width(10)
        self.play(Write(explanation2.next_to(explanation1, DOWN)))
        self.wait(10)

        # Introduce Conditional Memory
        conditional_memory_text = Text("Conditional Memory: A well-organized library with a smart catalog.", font_size=28, color=ORANGE)
        conditional_memory_text.scale_to_fit_width(10)
        self.play(Write(conditional_memory_text.next_to(explanation2, DOWN)) )
        self.wait(10)

        self.play(FadeOut(library_image, explanation1, explanation2, conditional_memory_text))

        # --- SCENE 2: Detailed Component Analysis (60 seconds) ---
        # Simplified Diagram
        rect1 = Rectangle(color=BLUE, width=2, height=1)
        rect2 = Rectangle(color=GREEN, width=2, height=1)
        rect3 = Rectangle(color=ORANGE, width=2, height=1)

        rect1.move_to(LEFT * 3)
        rect2.move_to(ORIGIN)
        rect3.move_to(RIGHT * 3)

        label1 = Text("Input", font_size=24)
        label2 = Text("Lookup Table", font_size=24)
        label3 = Text("Output", font_size=24)

        label1.move_to(rect1.get_center())
        label2.move_to(rect2.get_center())
        label3.move_to(rect3.get_center())

        self.play(Create(rect1), Create(rect2), Create(rect3))
        self.play(Write(label1), Write(label2), Write(label3))
        self.wait(5)

        # Animation: Data Flow
        arrow1 = Arrow(rect1.get_right(), rect2.get_left(), buff=0.2)
        arrow2 = Arrow(rect2.get_right(), rect3.get_left(), buff=0.2)

        self.play(Create(arrow1))
        self.wait(3)
        self.play(Create(arrow2))
        self.wait(5)

        explanation3 = Text("Scalable Lookup Table: Stores key-value pairs based on input.", font_size=28)
        explanation3.scale_to_fit_width(10)
        self.play(Write(explanation3.next_to(rect3, DOWN)))
        self.wait(10)

        self.play(FadeOut(rect1, rect2, rect3, label1, label2, label3, arrow1, arrow2, explanation3))

        # --- SCENE 3: Integration and Relationships (40 seconds) ---
        # Comparison: Traditional vs. Conditional Memory
        traditional_text = Text("Traditional Memory: Dense, full connections.", font_size=28, color=BLUE)
        conditional_text = Text("Conditional Memory: Sparse, selective connections.", font_size=28, color=ORANGE)

        traditional_text.scale_to_fit_width(10)
        conditional_text.scale_to_fit_width(10)

        self.play(Write(traditional_text))
        self.wait(5)
        self.play(Write(conditional_text.next_to(traditional_text, DOWN)))
        self.wait(10)

        # Visual: Sparse Matrix vs. Dense Matrix
        dense_matrix = Matrix([[1, 1, 1], [1, 1, 1], [1, 1, 1]], element_font_size=20)
        sparse_matrix = Matrix([[1, 0, 0], [0, 1, 0], [0, 0, 1]], element_font_size=20)

        dense_matrix.scale(0.5).move_to(LEFT * 3)
        sparse_matrix.scale(0.5).move_to(RIGHT * 3)

        self.play(Create(dense_matrix))
        self.wait(5)
        self.play(Create(sparse_matrix))
        self.wait(10)

        self.play(FadeOut(traditional_text, conditional_text, dense_matrix, sparse_matrix))

        # --- SCENE 4: Practical Applications & Summary (27.5 seconds) ---
        applications_text = Text("Applications: Reduced memory footprint, faster inference.", font_size=28, color=GREEN)
        applications_text.scale_to_fit_width(10)
        self.play(Write(applications_text))
        self.wait(10)

        summary_text = Text("Conditional Memory offers a promising path towards more efficient and scalable LLMs.", font_size=28)
        summary_text.scale_to_fit_width(10)
        self.play(Write(summary_text.next_to(applications_text, DOWN)))
        self.wait(10)

        self.wait(7.5)