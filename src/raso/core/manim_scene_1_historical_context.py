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

        approach1.next_to(timeline_title, DOWN, buff=0.5)
        approach2.next_to(approach1, DOWN, buff=0.5)
        approach3.next_to(approach2, DOWN, buff=0.5)

        # Create timeline markers
        marker1 = Line(LEFT, RIGHT, color=BLUE, stroke_width=2)
        marker2 = Line(LEFT, RIGHT, color=BLUE, stroke_width=2)
        marker3 = Line(LEFT, RIGHT, color=BLUE, stroke_width=2)

        marker1.next_to(approach1, LEFT, buff=0.2)
        marker2.next_to(approach2, LEFT, buff=0.2)
        marker3.next_to(approach3, LEFT, buff=0.2)

        self.play(Write(approach1), Create(marker1))
        self.wait(3)
        self.play(Write(approach2), Create(marker2))
        self.wait(3)
        self.play(Write(approach3), Create(marker3))
        self.wait(5)

        # --- Traffic Jam Analogy ---
        self.play(FadeOut(timeline_title, approach1, approach2, approach3, marker1, marker2, marker3))

        traffic_title = Text("The Traffic Jam Problem", font_size=32)
        traffic_title.scale_to_fit_width(10)
        self.play(Write(traffic_title))
        self.wait(3)

        # Create a simplified traffic jam visualization
        road = Line(LEFT, RIGHT, color=GRAY, stroke_width=4)
        road.shift(DOWN * 1)

        cars = [Rectangle(color=RED, width=0.5, height=0.5) for _ in range(10)]
        for i, car in enumerate(cars):
            car.move_to(road.get_start() + i * 0.5 * RIGHT)

        self.play(Create(road))
        self.wait(1)
        for car in cars:
            self.play(Create(car))
            self.wait(0.2)

        # Animate cars slowly moving and then getting stuck
        for i in range(len(cars) - 1):
            self.play(cars[i].animate.shift(0.1 * RIGHT))
            self.wait(0.1)
        
        self.play(cars[-1].animate.shift(0.1 * RIGHT))
        self.wait(2)

        jam_text = Text("Incremental fixes don't solve the root cause", font_size=24)
        jam_text.scale_to_fit_width(10)
        jam_text.next_to(road, DOWN, buff=0.5)
        self.play(Write(jam_text))
        self.wait(8)

        self.play(FadeOut(traffic_title, road, *cars, jam_text))

        # --- Limitation Comparison Charts ---
        comparison_title = Text("Limitations of Existing Methods", font_size=32)
        comparison_title.scale_to_fit_width(10)
        self.play(Write(comparison_title))
        self.wait(3)

        # Create a table
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
        self.wait(10)

        # Highlight key differences
        self.play(Indicate(table.get_cell((0, 1)), color=RED))
        self.play(Indicate(table.get_cell((0, 2)), color=GREEN))
        self.wait(5)

        self.play(FadeOut(comparison_title, table))

        # --- Puzzle Pieces Not Fitting ---
        puzzle_title = Text("Trying to Force a Fit", font_size=32)
        puzzle_title.scale_to_fit_width(10)
        self.play(Write(puzzle_title))
        self.wait(3)

        # Create puzzle pieces
        piece1 = Polygon([0, 0], [1, 0], [1, 1], [0, 1], color=BLUE)
        piece2 = Polygon([2, 0], [3, 0], [3, 1], [2, 1], color=RED)
        piece3 = Polygon([4, 0], [5, 0], [5, 1], [4, 1], color=GREEN)

        piece1.move_to(LEFT * 2)
        piece2.move_to(RIGHT * 0)
        piece3.move_to(RIGHT * 2)

        self.play(Create(piece1), Create(piece2), Create(piece3))
        self.wait(2)

        # Attempt to fit them together (they don't)
        self.play(piece1.animate.shift(RIGHT * 0.5))
        self.wait(2)
        self.play(piece1.animate.shift(LEFT * 0.5))
        self.wait(2)

        failure_text = Text("Existing approaches couldn't integrate seamlessly", font_size=24)
        failure_text.scale_to_fit_width(10)
        failure_text.next_to(piece1, DOWN, buff=0.5)
        self.play(Write(failure_text))
        self.wait(8)

        self.play(FadeOut(puzzle_title, piece1, piece2, piece3, failure_text))

        # --- The Need for Fundamental Innovation ---
        innovation_title = Text("A New Paradigm is Required", font_size=36)
        innovation_title.scale_to_fit_width(10)
        self.play(Write(innovation_title))
        self.wait(5)

        solution_text = Text("A fundamental shift in thinking is necessary to overcome these limitations.", font_size=28)
        solution_text.scale_to_fit_width(10)
        solution_text.next_to(innovation_title, DOWN, buff=0.5)
        self.play(Write(solution_text))
        self.wait(10)

        self.play(FadeOut(innovation_title, solution_text))

        # --- Final Pause ---
        final_pause_text = Text("This sets the stage for our new approach...", font_size=32)
        final_pause_text.scale_to_fit_width(10)
        self.play(Write(final_pause_text))
        self.wait(15)
        self.play(FadeOut(final_pause_text))