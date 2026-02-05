from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Conceptual Overview (60 seconds) ---
        title = Text("Conditional Memory via Scalable Lookup", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("A New Axis of Sparsity for Large Language Models", font_size=24)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(3)
        self.play(Write(subtitle))
        self.wait(5)

        # Visual Metaphor: Library Analogy
        library_image = ImageMobject("library.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(library_image))
        self.wait(5)

        explanation1 = Text("Traditional LLMs: Like searching every book in a library.", font_size=28)
        explanation1.scale_to_fit_width(10)
        self.play(Write(explanation1.next_to(library_image, DOWN)))
        self.wait(8)

        explanation2 = Text("Conditional Memory: Like having a librarian who knows exactly where to find what you need.", font_size=28)
        explanation2.scale_to_fit_width(10)
        self.play(Write(explanation2.next_to(explanation1, DOWN)))
        self.wait(10)

        self.play(FadeOut(library_image, explanation1, explanation2, title, subtitle))

        # --- SCENE 2: Detailed Component Analysis (60 seconds) ---
        # Core Concept: Key-Value Store
        kv_title = Text("Key-Value Store: The Foundation", font_size=32)
        kv_title.scale_to_fit_width(10)
        self.play(Write(kv_title))
        self.wait(3)

        key_box = Rectangle(color=BLUE, width=2, height=1)
        value_box = Rectangle(color=GREEN, width=4, height=1)
        arrow = Arrow(key_box.get_right(), value_box.get_left())

        key_text = Text("Key", font_size=24).move_to(key_box.get_center())
        value_text = Text("Value", font_size=24).move_to(value_box.get_center())

        self.play(Create(key_box), Create(value_box), Create(arrow), Write(key_text), Write(value_text))
        self.wait(8)

        explanation3 = Text("Keys are used to quickly retrieve associated values.", font_size=28)
        explanation3.scale_to_fit_width(10)
        self.play(Write(explanation3.next_to(value_box, DOWN)))
        self.wait(10)

        # Scalable Lookup Table
        lookup_title = Text("Scalable Lookup Table", font_size=32)
        lookup_title.scale_to_fit_width(10)
        self.play(Transform(kv_title, lookup_title))
        self.wait(3)

        # Simplified representation of the lookup table
        table = VGroup(*[Rectangle(color=BLUE, width=1, height=0.5).move_to(x * 1.5, y=0) for x in range(5) for y in range(2)])
        self.play(FadeOut(key_box, value_box, arrow, key_text, value_text, explanation3))
        self.play(Create(table))
        self.wait(10)

        self.play(FadeOut(kv_title, table))

        # --- SCENE 3: Integration and Relationships (40 seconds) ---
        integration_title = Text("Integrating with Large Language Models", font_size=32)
        integration_title.scale_to_fit_width(10)
        self.play(Write(integration_title))
        self.wait(3)

        llm_box = Rectangle(color=ORANGE, width=5, height=3)
        memory_box = Rectangle(color=BLUE, width=3, height=2).next_to(llm_box, RIGHT)

        llm_text = Text("LLM", font_size=24).move_to(llm_box.get_center())
        memory_text = Text("Conditional Memory", font_size=24).move_to(memory_box.get_center())

        self.play(Create(llm_box), Create(memory_box), Write(llm_text), Write(memory_text))
        self.wait(5)

        connection_arrow = Arrow(memory_box.get_right(), llm_box.get_left())
        self.play(Create(connection_arrow))
        self.wait(8)

        explanation4 = Text("The LLM queries the Conditional Memory for relevant information.", font_size=28)
        explanation4.scale_to_fit_width(10)
        self.play(Write(explanation4.next_to(llm_box, DOWN)))
        self.wait(10)

        self.play(FadeOut(integration_title, llm_box, memory_box, connection_arrow, llm_text, memory_text, explanation4))

        # --- SCENE 4: Practical Applications & Future Possibilities (28.25 seconds) ---
        applications_title = Text("Future Possibilities & Applications", font_size=32)
        applications_title.scale_to_fit_width(10)
        self.play(Write(applications_title))
        self.wait(3)

        app1 = Text("• Enhanced Long-Context Understanding", font_size=24)
        app2 = Text("• Personalized AI Assistants", font_size=24)
        app3 = Text("• Efficient Knowledge Retrieval", font_size=24)

        app1.scale_to_fit_width(10)
        app2.scale_to_fit_width(10)
        app3.scale_to_fit_width(10)

        self.play(Write(app1.next_to(applications_title, DOWN, buff=0.5)))
        self.wait(5)
        self.play(Write(app2.next_to(app1, DOWN, buff=0.5)))
        self.wait(5)
        self.play(Write(app3.next_to(app2, DOWN, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(applications_title, app1, app2, app3))