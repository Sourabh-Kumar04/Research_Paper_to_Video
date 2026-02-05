from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- SCENE 1: Problem Definition (60 seconds) ---
        title = Text("Conditional Memory: A New Axis of Sparsity", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        problem_statement = Text(
            "Large Language Models (LLMs) face challenges with long contexts and computational cost.",
            font_size=28
        )
        problem_statement.scale_to_fit_width(10)
        self.play(Write(problem_statement.next_to(title, DOWN, buff=0.5)))
        self.wait(8)

        # Visual metaphor: Expanding circle representing context length
        circle = Circle(radius=1, color=BLUE)
        self.play(Create(circle))
        self.wait(2)

        # Expanding circle animation
        self.play(circle.animate.set(radius=3))
        self.wait(3)

        cost_text = Text("Increasing context = Increasing cost", font_size=24)
        cost_text.scale_to_fit_width(10)
        self.play(Write(cost_text.next_to(circle, DOWN, buff=0.5)))
        self.wait(5)

        # Challenge 1: Long-Range Dependencies
        challenge1 = Text("Challenge 1: Long-Range Dependencies", font_size=28, color=ORANGE)
        challenge1.scale_to_fit_width(10)
        self.play(Write(challenge1.next_to(cost_text, DOWN, buff=0.5)))
        self.wait(5)

        # Challenge 2: Computational Complexity
        challenge2 = Text("Challenge 2: Computational Complexity", font_size=28, color=ORANGE)
        challenge2.scale_to_fit_width(10)
        self.play(Write(challenge2.next_to(challenge1, DOWN, buff=0.5)))
        self.wait(5)

        self.play(FadeOut(title, problem_statement, circle, cost_text, challenge1, challenge2))
        self.wait(2)

        # --- SCENE 2: Core Concepts - Scalable Lookup (80 seconds) ---
        concept_title = Text("Scalable Lookup: The Core Idea", font_size=36)
        concept_title.scale_to_fit_width(10)
        self.play(Write(concept_title))
        self.wait(5)

        # Visual: Key-Value Store
        key_value_store = VGroup(
            Text("Key", font_size=24),
            Rectangle(width=1, height=0.5, color=BLUE).next_to(Text("Key", font_size=24), RIGHT),
            Arrow(Rectangle(width=1, height=0.5, color=BLUE).get_right(), Text("Value", font_size=24).next_to(Rectangle(width=1, height=0.5, color=BLUE), RIGHT)),
            Text("Value", font_size=24)
        ).arrange(RIGHT)
        key_value_store.scale_to_fit_width(8)
        self.play(Create(key_value_store))
        self.wait(5)

        # Explanation
        explanation = Text("Store information as key-value pairs for efficient retrieval.", font_size=24)
        explanation.scale_to_fit_width(10)
        self.play(Write(explanation.next_to(key_value_store, DOWN, buff=0.5)))
        self.wait(10)

        # Scalability Visualization
        scalability_chart = Line(start=LEFT * 5, end=RIGHT * 5, color=GREEN)
        scalability_label = Text("Scalability: Linear with Key Count", font_size=24, color=GREEN)
        scalability_label.scale_to_fit_width(10)
        self.play(Create(scalability_chart), Write(scalability_label.next_to(scalability_chart, DOWN, buff=0.5)))
        self.wait(8)

        # Conditional Memory: Adding a Condition
        conditional_memory = Text("Conditional Memory: Key + Condition -> Value", font_size=28, color=ORANGE)
        conditional_memory.scale_to_fit_width(10)
        self.play(Write(conditional_memory.next_to(scalability_label, DOWN, buff=0.5)))
        self.wait(10)

        # Condition as a filter
        condition_filter = Rectangle(width=1, height=0.5, color=PURPLE)
        self.play(Create(condition_filter.next_to(conditional_memory, DOWN, buff=0.5)))
        condition_text = Text("Condition acts as a filter", font_size=24, color=PURPLE)
        condition_text.scale_to_fit_width(10)
        self.play(Write(condition_text.next_to(condition_filter, RIGHT, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(concept_title, key_value_store, explanation, scalability_chart, scalability_label, conditional_memory, condition_filter, condition_text))
        self.wait(2)

        # --- SCENE 3: Integration and Relationships (60 seconds) ---
        integration_title = Text("Integrating Conditional Memory into LLMs", font_size=36)
        integration_title.scale_to_fit_width(10)
        self.play(Write(integration_title))
        self.wait(5)

        # LLM Block Diagram
        llm_block = Rectangle(width=4, height=2, color=BLUE)
        self.play(Create(llm_block))
        self.wait(2)

        conditional_memory_block = Rectangle(width=2, height=1, color=ORANGE).next_to(llm_block, RIGHT)
        self.play(Create(conditional_memory_block))
        self.wait(2)

        arrow = Arrow(llm_block.get_right(), conditional_memory_block.get_left())
        self.play(Create(arrow))
        self.wait(2)

        # Explanation
        integration_explanation = Text("LLM queries Conditional Memory for relevant information.", font_size=24)
        integration_explanation.scale_to_fit_width(10)
        self.play(Write(integration_explanation.next_to(conditional_memory_block, DOWN, buff=0.5)))
        self.wait(8)

        # Before/After Comparison
        before_text = Text("Without Conditional Memory: Full Context Scan", font_size=24, color=RED)
        before_text.scale_to_fit_width(10)
        self.play(Write(before_text.next_to(integration_explanation, DOWN, buff=0.5)))
        self.wait(5)

        after_text = Text("With Conditional Memory: Targeted Lookup", font_size=24, color=GREEN)
        after_text.scale_to_fit_width(10)
        self.play(Write(after_text.next_to(before_text, DOWN, buff=0.5)))
        self.wait(8)

        # Efficiency Gain
        efficiency_gain = Text("Significant reduction in computational cost and latency.", font_size=24)
        efficiency_gain.scale_to_fit_width(10)
        self.play(Write(efficiency_gain.next_to(after_text, DOWN, buff=0.5)))
        self.wait(10)

        self.play(FadeOut(integration_title, llm_block, conditional_memory_block, arrow, integration_explanation, before_text, after_text, efficiency_gain))
        self.wait(2)

        # --- SCENE 4: Practical Applications & Future (60 seconds) ---
        applications_title = Text("Practical Applications & Future Directions", font_size=36)
        applications_title.scale_to_fit_width(10)
        self.play(Write(applications_title))
        self.wait(5)

        # Application 1: Long Document Summarization
        app1 = Text("Long Document Summarization: Efficiently process lengthy texts.", font_size=24, color=GREEN)
        app1.scale_to_fit_width(10)
        self.play(Write(app1))
        self.wait(5)

        # Application 2: Personalized Recommendations
        app2 = Text("Personalized Recommendations: Tailor suggestions based on user context.", font_size=24, color=GREEN)
        app2.scale_to_fit_width(10)
        self.play(Write(app2.next_to(app1, DOWN, buff=0.5)))
        self.wait(5)

        # Future Possibilities
        future_text = Text("Future: Combining with other sparsity techniques for even greater efficiency.", font_size=24, color=PURPLE)
        future_text.scale_to_fit_width(10)
        self.play(Write(future_text.next_to(app2, DOWN, buff=0.5)))
        self.wait(10)

        # Summary
        summary = Text("Conditional Memory offers a promising path towards scalable and efficient LLMs.", font_size=28, color=BLUE)
        summary.scale_to_fit_width(10)
        self.play(Write(summary.next_to(future_text, DOWN, buff=0.5)))
        self.wait(15)

        self.play(FadeOut(applications_title, app1, app2, future_text, summary))
        self.wait(5)