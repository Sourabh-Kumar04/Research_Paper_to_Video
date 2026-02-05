from manim import *

class SequencesVectorsEmbeddings(Scene):
    def construct(self):
        # --- Introduction (10 seconds) ---
        title = Text("Sequences, Vectors, & Embeddings", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        subtext = Text("Foundational Concepts for Machine Learning", font_size=24)
        subtext.scale_to_fit_width(10)
        subtext.next_to(title, DOWN)
        self.play(Write(subtext))
        self.wait(5)
        self.play(FadeOut(title, subtext))

        # --- Sequences (30 seconds) ---
        sequence_title = Text("What are Sequences?", font_size=32)
        sequence_title.scale_to_fit_width(10)
        self.play(Write(sequence_title))
        self.wait(3)

        words = ["cat", "dog", "bird", "fish"]
        word_objects = VGroup(*[Text(word, font_size=28) for word in words])
        word_objects.arrange(RIGHT, buff=0.5)
        self.play(Write(word_objects))
        self.wait(5)

        sequence_definition = Text("A sequence is an ordered list of items.", font_size=24)
        sequence_definition.scale_to_fit_width(10)
        sequence_definition.next_to(word_objects, DOWN, buff=0.5)
        self.play(Write(sequence_definition))
        self.wait(7)

        highlight_arrow = Arrow(word_objects[0].get_bottom(), word_objects[3].get_bottom(), buff=0.1)
        self.play(Indicate(highlight_arrow, color=BLUE, scale_factor=1.2))
        self.wait(5)

        self.play(FadeOut(sequence_title, word_objects, sequence_definition, highlight_arrow))

        # --- Vectors (40 seconds) ---
        vector_title = Text("Introducing Vectors", font_size=32)
        vector_title.scale_to_fit_width(10)
        self.play(Write(vector_title))
        self.wait(3)

        vector_definition = Text("A vector represents a direction and magnitude.", font_size=24)
        vector_definition.scale_to_fit_width(10)
        vector_definition.next_to(vector_title, DOWN, buff=0.5)
        self.play(Write(vector_definition))
        self.wait(5)

        axes = Axes(
            x_range=[-5, 5, 1],
            y_range=[-5, 5, 1],
            axis_config={"include_numbers": False},
        )
        axes.add_coordinate_labels()
        self.play(Create(axes))
        self.wait(2)

        vector = Arrow(axes.coords_to_point(0, 0), axes.coords_to_point(3, 2), buff=0.1)
        vector.set_color(BLUE)
        self.play(Create(vector))
        self.wait(5)

        vector_components = Text("[3, 2]", font_size=28)
        vector_components.scale_to_fit_width(5)
        vector_components.next_to(vector, RIGHT, buff=0.5)
        self.play(Write(vector_components))
        self.wait(7)

        self.play(FadeOut(vector_title, vector_definition, axes, vector, vector_components))

        # --- Word Embeddings (30 seconds) ---
        embedding_title = Text("Word Embeddings: Vectors for Words", font_size=32)
        embedding_title.scale_to_fit_width(10)
        self.play(Write(embedding_title))
        self.wait(3)

        embedding_definition = Text("Representing words as numerical vectors.", font_size=24)
        embedding_definition.scale_to_fit_width(10)
        embedding_definition.next_to(embedding_title, DOWN, buff=0.5)
        self.play(Write(embedding_definition))
        self.wait(5)

        # Create a scatter plot of word embeddings (simplified)
        dots = VGroup(*[Dot(np.array([i, j, 0]), color=BLUE) for i, j in [(1, 2), (2, 1), (3, 3), (-1, -2)]])
        labels = VGroup(*[Text(word, font_size=16) for word in ["king", "queen", "man", "woman"]])
        labels.arrange(DOWN, aligned_edge=LEFT)
        labels.next_to(dots, RIGHT, buff=0.5)

        self.play(Create(dots))
        self.play(Write(labels))
        self.wait(7)

        self.play(FadeOut(embedding_title, embedding_definition, dots, labels))

        # --- Summary (10 seconds) ---
        summary_title = Text("Putting it Together", font_size=32)
        summary_title.scale_to_fit_width(10)
        self.play(Write(summary_title))
        self.wait(5)

        summary_text = Text("Sequences become vectors through embeddings, enabling computers to understand language.", font_size=24)
        summary_text.scale_to_fit_width(10)
        summary_text.next_to(summary_title, DOWN, buff=0.5)
        self.play(Write(summary_text))
        self.wait(5)