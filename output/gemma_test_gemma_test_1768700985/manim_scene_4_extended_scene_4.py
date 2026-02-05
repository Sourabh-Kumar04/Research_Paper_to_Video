from manim import *

class IntuitiveSolutionApproach(Scene):
    def construct(self):
        # --- Step 1: Conceptual Overview (60 seconds) ---
        title = Text("The Intuitive Solution Approach: Testing Gemma for Video Generation", font_size=36)
        title.scale_to_fit_width(12)
        self.play(Write(title))
        self.wait(5)

        library_analogy = VGroup(
            Text("Imagine a vast library...", font_size=32),
            Text("Each book represents a piece of knowledge.", font_size=28)
        ).arrange(DOWN, aligned_edge=LEFT)
        library_analogy.scale_to_fit_width(10)
        self.play(Write(library_analogy))
        self.wait(10)

        sequential_processing = Text("Sequential Processing: Reading books one by one.", font_size=32)
        sequential_processing.scale_to_fit_width(10)
        self.play(Write(sequential_processing))
        self.wait(5)

        parallel_processing = Text("Parallel Processing: Multiple people reading books simultaneously.", font_size=32)
        parallel_processing.scale_to_fit_width(10)
        self.play(Write(parallel_processing))
        self.wait(10)

        self.play(FadeOut(title, library_analogy, sequential_processing, parallel_processing))

        # --- Step 2: Detailed Component Analysis (60 seconds) ---
        maze_title = Text("Navigating Complexity: The Maze Analogy", font_size=36)
        maze_title.scale_to_fit_width(12)
        self.play(Write(maze_title))
        self.wait(5)

        maze = Maze(width=6, height=6)
        maze.set_color(BLUE)
        self.play(Create(maze))
        self.wait(5)

        start_point = Dot(maze.get_start(), color=GREEN)
        end_point = Dot(maze.get_end(), color=RED)
        self.play(Create(start_point), Create(end_point))
        self.wait(5)

        path = VMobject(color=ORANGE)
        path.set_points_as_corners([maze.get_start(), maze.get_end()])
        self.play(Create(path))
        self.wait(10)

        text_maze = VGroup(
            Text("Finding the optimal path requires exploration.", font_size=28),
            Text("Gemma explores possibilities like navigating a maze.", font_size=28)
        ).arrange(DOWN, aligned_edge=LEFT)
        text_maze.scale_to_fit_width(10)
        self.play(Write(text_maze))
        self.wait(10)

        self.play(FadeOut(maze_title, maze, start_point, end_point, path, text_maze))

        # --- Step 3: Integration and Relationships (60 seconds) ---
        system_title = Text("A Holistic System Perspective", font_size=36)
        system_title.scale_to_fit_width(12)
        self.play(Write(system_title))
        self.wait(5)

        components = VGroup(
            Rectangle(color=BLUE, width=2, height=1),
            Circle(color=GREEN, radius=1),
            Triangle(color=ORANGE, side_length=2)
        ).arrange(RIGHT, buff=1)
        components.scale_to_fit_width(10)
        self.play(Create(components))
        self.wait(5)

        connections = VGroup(
            Arrow(components[0].get_right(), components[1].get_left()),
            Arrow(components[1].get_right(), components[2].get_left())
        )
        self.play(Create(connections))
        self.wait(10)

        text_system = VGroup(
            Text("Each component plays a vital role.", font_size=28),
            Text("Their interactions define the system's behavior.", font_size=28)
        ).arrange(DOWN, aligned_edge=LEFT)
        text_system.scale_to_fit_width(10)
        self.play(Write(text_system))
        self.wait(10)

        self.play(FadeOut(system_title, components, connections, text_system))

        # --- Step 4: Practical Applications & Future (60 seconds) ---
        application_title = Text("Practical Applications & Future Possibilities", font_size=36)
        application_title.scale_to_fit_width(12)
        self.play(Write(application_title))
        self.wait(5)

        video_generation = Text("Gemma for Video Generation: Creating content from text prompts.", font_size=32)
        video_generation.scale_to_fit_width(10)
        self.play(Write(video_generation))
        self.wait(10)

        future_possibilities = VGroup(
            Text("Enhanced creativity and efficiency.", font_size=28),
            Text("Personalized content creation.", font_size=28),
            Text("Automated video production workflows.", font_size=28)
        ).arrange(DOWN, aligned_edge=LEFT)
        future_possibilities.scale_to_fit_width(10)
        self.play(Write(future_possibilities))
        self.wait(15)

        summary = Text("The Intuitive Solution Approach empowers us to tackle complex problems.", font_size=32)
        summary.scale_to_fit_width(10)
        self.play(Write(summary))
        self.wait(10)

        self.play(FadeOut(application_title, video_generation, future_possibilities, summary))