from manim import *

class ConditionalMemoryScene(Scene):
    def construct(self):
        # --- Step 1: Conceptual Overview (60 seconds) ---
        title = Text("Conditional Memory: A New Axis of Sparsity", font_size=36)
        title.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)

        library_analogy = VGroup(
            Text("Imagine a vast library...", font_size=28),
            Text("Traditional LLMs: Searching every book for every query.", font_size=24, color=BLUE),
            Text("Conditional Memory:  Organizing books by topic, then searching *within* that section.", font_size=24, color=ORANGE)
        ).arrange(DOWN, aligned_edge=LEFT)
        library_analogy.scale_to_fit_width(10)
        self.play(Write(library_analogy))
        self.wait(15)

        # Visual: Bookshelves with books, highlighting search process
        bookshelf = VGroup(*[Rectangle(width=0.5, height=0.3, color=YELLOW) for _ in range(10)]).arrange(DOWN, aligned_edge=LEFT)
        search_highlight = SurroundingRectangle(bookshelf, color=BLUE, buff=0.1)
        self.play(Create(bookshelf))
        self.play(Indicate(search_highlight, scale_factor=1.2))
        self.wait(5)

        organized_bookshelf = VGroup(*[Rectangle(width=0.5, height=0.3, color=YELLOW) for _ in range(10)]).arrange(DOWN, aligned_edge=LEFT)
        organized_bookshelf.shift(RIGHT * 3)
        topic_label = Text("Topic: History", font_size=20, color=ORANGE).next_to(organized_bookshelf, UP)
        search_highlight_organized = SurroundingRectangle(organized_bookshelf, color=ORANGE, buff=0.1)
        self.play(Create(organized_bookshelf), Write(topic_label))
        self.play(Indicate(search_highlight_organized, scale_factor=1.2))
        self.wait(10)

        self.play(FadeOut(title, library_analogy, bookshelf, search_highlight, organized_bookshelf, topic_label, search_highlight_organized))

        # --- Step 2: Detailed Component Analysis (60 seconds) ---
        sequential_processing = Text("Sequential Processing: One step at a time.", font_size=28, color=BLUE)
        sequential_processing.scale_to_fit_width(10)
        self.play(Write(sequential_processing))
        self.wait(5)

        # Visual: A line of boxes representing steps
        steps = VGroup(*[Rectangle(width=0.5, height=0.3, color=BLUE) for _ in range(5)]).arrange(RIGHT, aligned_edge=DOWN)
        arrow_seq = Arrow(steps[0].get_right(), steps[1].get_left(), buff=0.1)
        self.play(Create(steps), Create(arrow_seq))
        self.wait(5)

        parallel_processing = Text("Parallel Processing: Multiple steps simultaneously.", font_size=28, color=GREEN)
        parallel_processing.scale_to_fit_width(10)
        self.play(Transform(sequential_processing, parallel_processing))
        self.wait(5)

        # Visual: Multiple lines of boxes representing parallel steps
        parallel_steps = VGroup(*[VGroup(*[Rectangle(width=0.5, height=0.3, color=GREEN) for _ in range(5)]).arrange(RIGHT, aligned_edge=DOWN) for _ in range(3)]).arrange(DOWN, aligned_edge=LEFT)
        self.play(Transform(steps, parallel_steps))
        self.wait(10)

        self.play(FadeOut(sequential_processing, steps))

        # Maze analogy
        maze_text = Text("Navigating a Maze: Traditional LLMs explore every path.", font_size=28, color=BLUE)
        maze_text.scale_to_fit_width(10)
        self.play(Write(maze_text))
        self.wait(5)

        maze = Line(start=LEFT * 5, end=RIGHT * 5, color=BLUE)
        maze_path = Line(start=LEFT * 5, end=RIGHT * 5, color=ORANGE, stroke_width=3)
        self.play(Create(maze))
        self.play(Create(maze_path))
        self.wait(10)

        self.play(FadeOut(maze_text, maze, maze_path))

        # --- Step 3: Integration and Relationships (60 seconds) ---
        system_overview = Text("Holistic System Perspective", font_size=32, color=BLUE)
        system_overview.scale_to_fit_width(10)
        self.play(Write(system_overview))
        self.wait(5)

        # Diagram: Input -> Conditional Memory -> Processing -> Output
        input_box = Rectangle(width=1, height=0.5, color=BLUE).to_edge(LEFT)
        cm_box = Rectangle(width=1.5, height=0.5, color=ORANGE).next_to(input_box, RIGHT)
        processing_box = Rectangle(width=1.5, height=0.5, color=GREEN).next_to(cm_box, RIGHT)
        output_box = Rectangle(width=1, height=0.5, color=BLUE).next_to(processing_box, RIGHT)

        arrow1 = Arrow(input_box.get_right(), cm_box.get_left())
        arrow2 = Arrow(cm_box.get_right(), processing_box.get_left())
        arrow3 = Arrow(processing_box.get_right(), output_box.get_left())

        self.play(Create(input_box), Create(cm_box), Create(processing_box), Create(output_box))
        self.play(Create(arrow1), Create(arrow2), Create(arrow3))
        self.wait(10)

        # Highlight Conditional Memory
        self.play(Indicate(cm_box, scale_factor=1.2))
        self.wait(5)

        # Comparison: Before/After
        before_text = Text("Without Conditional Memory: Slow, Inefficient", font_size=24, color=RED)
        after_text = Text("With Conditional Memory: Fast, Efficient", font_size=24, color=GREEN)
        before_text.scale_to_fit_width(10)
        after_text.scale_to_fit_width(10)
        before_text.to_edge(DOWN)
        after_text.next_to(before_text, RIGHT)
        self.play(Write(before_text), Write(after_text))
        self.wait(10)

        self.play(FadeOut(system_overview, input_box, cm_box, processing_box, output_box, arrow1, arrow2, arrow3, before_text, after_text))

        # --- Step 4: Practical Applications (63 seconds) ---
        applications_title = Text("Practical Applications", font_size=32, color=GREEN)
        applications_title.scale_to_fit_width(10)
        self.play(Write(applications_title))
        self.wait(5)

        # List of applications
        applications = VGroup(
            Text("• Enhanced Question Answering", font_size=24, color=GREEN),
            Text("• Improved Code Generation", font_size=24, color=GREEN),
            Text("• More Accurate Summarization", font_size=24, color=GREEN),
            Text("• Personalized Recommendations", font_size=24, color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT)
        applications.scale_to_fit_width(10)
        self.play(Write(applications))
        self.wait(15)

        # Future possibilities
        future_title = Text("Future Possibilities", font_size=32, color=PURPLE)
        future_title.scale_to_fit_width(10)
        self.play(Transform(applications_title, future_title))
        self.wait(5)

        future_ideas = VGroup(
            Text("• Scaling to even larger models", font_size=24, color=PURPLE),
            Text("• Combining with other sparsity techniques", font_size=24, color=PURPLE),
            Text("• Enabling real-time learning", font_size=24, color=PURPLE)
        ).arrange(DOWN, aligned_edge=LEFT)
        future_ideas.scale_to_fit_width(10)
        self.play(Transform(applications, future_ideas))
        self.wait(20)

        self.play(FadeOut(applications_title, applications))

        # Final Summary
        summary = Text("Conditional Memory offers a promising path towards more efficient and scalable LLMs.", font_size=28, color=BLUE)
        summary.scale_to_fit_width(10)
        self.play(Write(summary))
        self.wait(10)