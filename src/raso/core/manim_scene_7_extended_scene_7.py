from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Introduction & Industry Transformation (60s) ---
        title = Text("Conditional Memory: A New Axis of Sparsity for LLMs", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        subtext = Text("Revolutionizing Large Language Models", font_size=28)
        subtext.scale_to_fit_width(10)
        subtext.next_to(title, DOWN)
        self.play(Write(subtext))
        self.wait(5)

        # Industry Timeline
        timeline_title = Text("Industry Transformation Timeline", font_size=32)
        timeline_title.scale_to_fit_width(8)
        timeline_title.to_edge(UP)
        self.play(Write(timeline_title))

        year_2017 = Text("2017: Transformers Introduced", font_size=24)
        year_2018 = Text("2018: BERT & Pre-training", font_size=24)
        year_2020 = Text("2020: GPT-3 & Scale", font_size=24)
        year_2023 = Text("2023: Conditional Memory", font_size=24)

        year_2017.next_to(timeline_title, DOWN, buff=0.5)
        year_2018.next_to(year_2017, DOWN, buff=0.3)
        year_2020.next_to(year_2018, DOWN, buff=0.3)
        year_2023.next_to(year_2020, DOWN, buff=0.3)

        self.play(Write(year_2017))
        self.wait(3)
        self.play(Write(year_2018))
        self.wait(3)
        self.play(Write(year_2020))
        self.wait(3)
        self.play(Write(year_2023))
        self.wait(10)

        self.play(FadeOut(title, subtext, timeline_title, year_2017, year_2018, year_2020, year_2023))

        # --- SCENE 2: Conceptual Overview (60s) ---
        concept_title = Text("Conceptual Overview", font_size=36)
        concept_title.scale_to_fit_width(10)
        self.play(Write(concept_title))
        self.wait(5)

        # Traditional LLM vs. Conditional Memory
        traditional_llm = Rectangle(color=BLUE, width=4, height=2)
        conditional_memory = Rectangle(color=GREEN, width=4, height=2)

        traditional_llm.to_edge(LEFT)
        conditional_memory.next_to(traditional_llm, RIGHT, buff=1)

        traditional_text = Text("Traditional LLM", font_size=24).next_to(traditional_llm, DOWN)
        conditional_text = Text("Conditional Memory", font_size=24).next_to(conditional_memory, DOWN)

        self.play(Create(traditional_llm), Write(traditional_text))
        self.wait(3)
        self.play(Create(conditional_memory), Write(conditional_text))
        self.wait(5)

        # Explain the difference
        explanation = Text("Traditional LLMs store all information equally.\nConditional Memory prioritizes relevant information.", font_size=20)
        explanation.scale_to_fit_width(8)
        explanation.next_to(conditional_text, DOWN, buff=0.5)
        self.play(Write(explanation))
        self.wait(15)

        # Visual Metaphor: Library
        library_image = ImageMobject("library.png").scale(0.5) # Replace with actual image path
        library_image.to_edge(DOWN)
        self.play(FadeOut(traditional_llm, traditional_text, conditional_memory, conditional_text, explanation))
        self.play(FadeIn(library_image))
        self.wait(10)

        library_explanation = Text("Think of a library.  Traditional LLMs are like a messy library.\nConditional Memory is like a well-organized library.", font_size=20)
        library_explanation.scale_to_fit_width(8)
        library_explanation.next_to(library_image, UP)
        self.play(Write(library_explanation))
        self.wait(10)

        self.play(FadeOut(concept_title, library_image, library_explanation))

        # --- SCENE 3: Detailed Component Analysis (60s) ---
        component_title = Text("Detailed Component Analysis", font_size=36)
        component_title.scale_to_fit_width(10)
        self.play(Write(component_title))
        self.wait(5)

        # Scalable Lookup Table
        lookup_table = Rectangle(color=ORANGE, width=4, height=2)
        lookup_table.to_edge(LEFT)
        lookup_table_text = Text("Scalable Lookup Table", font_size=24).next_to(lookup_table, DOWN)

        self.play(Create(lookup_table), Write(lookup_table_text))
        self.wait(3)

        # Key-Value Pairs
        key_value_pairs = VGroup(
            Text("Key:", font_size=20),
            Text("Value:", font_size=20)
        ).next_to(lookup_table_text, DOWN, buff=0.5)
        self.play(Write(key_value_pairs))
        self.wait(5)

        # Explain how it works
        explanation_2 = Text("The lookup table stores key-value pairs.\nKeys represent context, values represent relevant information.", font_size=20)
        explanation_2.scale_to_fit_width(8)
        explanation_2.next_to(key_value_pairs, DOWN, buff=0.5)
        self.play(Write(explanation_2))
        self.wait(15)

        # Conditional Logic
        conditional_logic = Rectangle(color=BLUE, width=3, height=1.5)
        conditional_logic.next_to(lookup_table, RIGHT, buff=1)
        conditional_logic_text = Text("Conditional Logic", font_size=24).next_to(conditional_logic, DOWN)

        self.play(Create(conditional_logic), Write(conditional_logic_text))
        self.wait(3)

        arrow = Arrow(lookup_table.get_right(), conditional_logic.get_left())
        self.play(Create(arrow))
        self.wait(5)

        self.play(FadeOut(component_title, lookup_table, lookup_table_text, key_value_pairs, explanation_2, conditional_logic, conditional_logic_text, arrow))

        # --- SCENE 4: Practical Applications & Future (60s) ---
        application_title = Text("Practical Applications & Future", font_size=36)
        application_title.scale_to_fit_width(10)
        self.play(Write(application_title))
        self.wait(5)

        # Application Domains
        domain_1 = Text("1. Personalized Medicine", font_size=24)
        domain_2 = Text("2. Financial Modeling", font_size=24)
        domain_3 = Text("3. Scientific Discovery", font_size=24)

        domain_1.to_edge(LEFT)
        domain_2.next_to(domain_1, DOWN, buff=0.3)
        domain_3.next_to(domain_2, DOWN, buff=0.3)

        self.play(Write(domain_1))
        self.wait(3)
        self.play(Write(domain_2))
        self.wait(3)
        self.play(Write(domain_3))
        self.wait(10)

        # Future Possibilities
        future_text = Text("Future: More efficient, adaptable, and intelligent LLMs.", font_size=28)
        future_text.scale_to_fit_width(10)
        future_text.to_edge(DOWN)
        self.play(Write(future_text))
        self.wait(10)

        self.play(FadeOut(application_title, domain_1, domain_2, domain_3, future_text))