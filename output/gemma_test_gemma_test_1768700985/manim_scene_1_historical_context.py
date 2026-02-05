from manim import *

class HistoricalContext(Scene):
    def construct(self):
        # --- Title Slide ---
        title = Text("Historical Context: What Came Before", font_size=36)
        title.scale_to_fit_width(10)
        subtitle = Text("Understanding the Need for Innovation", font_size=28)
        subtitle.scale_to_fit_width(10)
        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(10)
        self.play(FadeOut(title, subtitle))

        # --- Timeline of Research Evolution ---
        timeline_title = Text("Early Approaches & Their Evolution", font_size=32)
        timeline_title.scale_to_fit_width(10)
        self.play(Write(timeline_title))
        self.wait(3)

        # Timeline elements
        approach1 = Text("Method A (1950s)", font_size=24)
        approach2 = Text("Method B (1980s)", font_size=24)
        approach3 = Text("Method C (2000s)", font_size=24)

        approach1.scale_to_fit_width(8)
        approach2.scale_to_fit_width(8)
        approach3.scale_to_fit_width(8)

        approach1.next_to(timeline_title, DOWN, buff=0.5)
        approach2.next_to(approach1, DOWN, buff=0.5)
        approach3.next_to(approach2, DOWN, buff=0.5)

        self.play(Write(approach1))
        self.wait(3)
        self.play(Write(approach2))
        self.wait(3)
        self.play(Write(approach3))
        self.wait(5)

        # --- Traffic Jam Analogy ---
        traffic_title = Text("The Traffic Jam Problem", font_size=32)
        traffic_title.scale_to_fit_width(10)
        self.play(Transform(timeline_title, traffic_title))
        self.wait(3)

        road = Line(LEFT * 5, RIGHT * 5, color=GRAY)
        cars = [Rectangle(color=RED, width=0.5, height=0.3) for _ in range(10)]
        for i, car in enumerate(cars):
            car.move_to(road.point_from_proportion(i / (len(cars) - 1)))

        self.play(Create(road))
        self.play(FadeIn(*cars))
        self.wait(3)

        # Animate cars moving slowly
        for car in cars:
            car.shift(RIGHT * 0.1)
        self.play(AnimationGroup(*[car.animate().shift(RIGHT * 0.1) for car in cars]), run_time=2)
        self.wait(3)

        # Add text explaining the analogy
        explanation = Text("Incremental fixes only shift the problem,\n they don't solve it.", font_size=24)
        explanation.scale_to_fit_width(10)
        explanation.next_to(road, DOWN, buff=0.5)
        self.play(Write(explanation))
        self.wait(10)

        self.play(FadeOut(road, *cars, explanation, traffic_title))

        # --- Limitation Comparison Charts ---
        comparison_title = Text("Limitations of Existing Methods", font_size=32)
        comparison_title.scale_to_fit_width(10)
        self.play(Write(comparison_title))
        self.wait(3)

        table_data = [
            ["Aspect", "Before", "Needed"],
            ["Speed", "Slow", "Fast"],
            ["Memory", "Excessive", "Efficient"],
            ["Accuracy", "Limited", "High"],
            ["Scalability", "Poor", "Excellent"]
        ]

        table = Table(table_data, include_header=True, row_labels=False)
        table.scale_to_fit_width(8)
        self.play(Create(table))
        self.wait(15)

        self.play(FadeOut(comparison_title, table))

        # --- Puzzle Pieces Not Fitting ---
        puzzle_title = Text("The Missing Piece", font_size=32)
        puzzle_title.scale_to_fit_width(10)
        self.play(Write(puzzle_title))
        self.wait(3)

        puzzle_pieces = [
            Rectangle(color=BLUE, width=1, height=1),
            Rectangle(color=GREEN, width=1, height=1),
            Rectangle(color=YELLOW, width=1, height=1),
            Rectangle(color=ORANGE, width=1, height=1)
        ]

        for piece in puzzle_pieces:
            piece.scale_to_fit_width(3)

        puzzle_pieces[0].move_to(LEFT * 2)
        puzzle_pieces[1].next_to(puzzle_pieces[0], RIGHT, buff=0.2)
        puzzle_pieces[2].next_to(puzzle_pieces[1], RIGHT, buff=0.2)
        puzzle_pieces[3].next_to(puzzle_pieces[2], RIGHT, buff=0.2)

        self.play(FadeIn(*puzzle_pieces))
        self.wait(3)

        # Add a missing piece shape
        missing_piece = Rectangle(color=RED, width=1, height=1)
        missing_piece.scale_to_fit_width(3)
        missing_piece.move_to(RIGHT * 2)
        missing_piece.set_opacity(0.5)
        self.play(Create(missing_piece))
        self.wait(5)

        explanation2 = Text("Existing methods couldn't provide the missing piece.\nA fundamental innovation was required.", font_size=24)
        explanation2.scale_to_fit_width(10)
        explanation2.next_to(puzzle_pieces, DOWN, buff=0.5)
        self.play(Write(explanation2))
        self.wait(15)

        self.play(FadeOut(puzzle_title, *puzzle_pieces, missing_piece, explanation2))

        # --- Summary ---
        summary_title = Text("The Need for a New Approach", font_size=32)
        summary_title.scale_to_fit_width(10)
        self.play(Write(summary_title))
        self.wait(3)

        summary_text = Text("Previous methods faced limitations in speed, memory, accuracy, and scalability.\nIncremental improvements were insufficient.\nA fundamental innovation was necessary to overcome these challenges.", font_size=24)
        summary_text.scale_to_fit_width(10)
        summary_text.next_to(summary_title, DOWN, buff=0.5)
        self.play(Write(summary_text))
        self.wait(20)

        self.play(FadeOut(summary_title, summary_text))