from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Conceptual Overview (60 seconds) ---
        title = Text("Conditional Memory: A New Axis of Sparsity", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        subtext = Text("For Large Language Models", font_size=28)
        subtext.scale_to_fit_width(10)
        subtext.next_to(title, DOWN)
        self.play(Write(subtext))
        self.wait(5)

        # Visual Metaphor: Library
        library_image = ImageMobject("library.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(library_image))
        self.wait(5)

        explanation1 = Text("Traditional LLMs: All books open all the time.", font_size=24)
        explanation1.scale_to_fit_width(10)
        explanation1.next_to(library_image, DOWN)
        self.play(Write(explanation1))
        self.wait(10)

        explanation2 = Text("Conditional Memory: Only open relevant books when needed.", font_size=24)
        explanation2.scale_to_fit_width(10)
        explanation2.next_to(explanation1, DOWN)
        self.play(Write(explanation2))
        self.wait(15)

        # Fade out library and explanations
        self.play(FadeOut(library_image, explanation1, explanation2, title, subtext))

        # --- SCENE 2: Detailed Component Analysis (70 seconds) ---
        heading2 = Text("Key Components", font_size=36)
        heading2.scale_to_fit_width(10)
        self.play(Write(heading2))
        self.wait(5)

        # Lookup Table
        lookup_table = Rectangle(color=BLUE, width=3, height=2)
        self.play(Create(lookup_table))
        self.wait(2)
        lookup_label = Text("Lookup Table", font_size=24, color=BLUE)
        lookup_label.scale_to_fit_width(8)
        lookup_label.next_to(lookup_table, DOWN)
        self.play(Write(lookup_label))
        self.wait(5)

        # Memory Bank
        memory_bank = Rectangle(color=GREEN, width=5, height=4)
        memory_bank.next_to(lookup_table, RIGHT, buff=1)
        self.play(Create(memory_bank))
        self.wait(2)
        memory_label = Text("Memory Bank", font_size=24, color=GREEN)
        memory_label.scale_to_fit_width(8)
        memory_label.next_to(memory_bank, DOWN)
        self.play(Write(memory_label))
        self.wait(5)

        # Query
        query = Text("Query", font_size=24, color=ORANGE)
        query.scale_to_fit_width(5)
        query.to_edge(UP)
        self.play(Write(query))
        self.wait(5)

        # Animation: Query -> Lookup Table -> Memory Bank
        arrow1 = Arrow(query.get_bottom(), lookup_table.get_top(), buff=0.2)
        arrow2 = Arrow(lookup_table.get_right(), memory_bank.get_left(), buff=0.2)
        self.play(Create(arrow1), Create(arrow2))
        self.wait(10)

        explanation3 = Text("Query used to index Lookup Table.", font_size=20)
        explanation3.scale_to_fit_width(10)
        explanation3.next_to(arrow1, DOWN)
        self.play(Write(explanation3))
        self.wait(10)

        explanation4 = Text("Lookup Table points to relevant Memory Bank entries.", font_size=20)
        explanation4.scale_to_fit_width(10)
        explanation4.next_to(arrow2, DOWN)
        self.play(Write(explanation4))
        self.wait(15)

        self.play(FadeOut(heading2, lookup_table, lookup_label, memory_bank, memory_label, query, arrow1, arrow2, explanation3, explanation4))

        # --- SCENE 3: Integration and Relationships (74 seconds) ---
        heading3 = Text("Scalability and Sparsity", font_size=36)
        heading3.scale_to_fit_width(10)
        self.play(Write(heading3))
        self.wait(5)

        # Graph: Memory Usage vs. Model Size
        axes = Axes(x_range=[0, 1000], y_range=[0, 100], x_length=8, y_length=4)
        axes.add_coordinate_labels()
        axes.axis_config["include_numbers"] = True

        traditional_curve = axes.plot(lambda x: 0.8 * x, color=RED)
        conditional_curve = axes.plot(lambda x: 0.2 * x, color=GREEN)

        traditional_label = Text("Traditional LLM", font_size=20, color=RED)
        traditional_label.scale_to_fit_width(8)
        traditional_label.next_to(axes, DOWN, buff=0.5)

        conditional_label = Text("Conditional Memory", font_size=20, color=GREEN)
        conditional_label.scale_to_fit_width(8)
        conditional_label.next_to(traditional_label, RIGHT)

        self.play(Create(axes), Create(traditional_curve), Create(conditional_curve), Write(traditional_label), Write(conditional_label))
        self.wait(15)

        explanation5 = Text("Conditional Memory significantly reduces memory usage.", font_size=20)
        explanation5.scale_to_fit_width(10)
        explanation5.next_to(axes, DOWN, buff=1)
        self.play(Write(explanation5))
        self.wait(15)

        # Highlight Sparsity
        rect = SurroundingRectangle(conditional_curve, color=YELLOW, buff=0.2)
        self.play(Create(rect))
        self.wait(10)

        explanation6 = Text("Increased Sparsity: Only relevant parameters are active.", font_size=20)
        explanation6.scale_to_fit_width(10)
        explanation6.next_to(rect, DOWN)
        self.play(Write(explanation6))
        self.wait(20)

        self.play(FadeOut(heading3, axes, traditional_curve, conditional_curve, traditional_label, conditional_label, explanation5, rect, explanation6))