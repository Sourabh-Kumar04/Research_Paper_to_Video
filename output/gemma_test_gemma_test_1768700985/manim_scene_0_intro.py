from manim import *

class BigPictureScene(Scene):
    def construct(self):
        # --- Step 1: Title Slide (30 seconds) ---
        title = Text("The Power of Predictive Maintenance", font_size=48)
        title.scale_to_fit_width(10)
        subtitle = Text("Reducing Downtime and Optimizing Performance", font_size=32)
        subtitle.scale_to_fit_width(10)
        paper_context = Text("Based on research exploring machine learning for industrial applications.", font_size=24)
        paper_context.scale_to_fit_width(10)

        self.play(Write(title))
        self.wait(5)
        self.play(Write(subtitle))
        self.wait(5)
        self.play(Write(paper_context))
        self.wait(10)

        self.play(FadeOut(title, subtitle, paper_context))

        # --- Step 2: Problem Landscape (60 seconds) ---
        problem_title = Text("The Current Challenge: Reactive Maintenance", font_size=36)
        problem_title.scale_to_fit_width(10)
        problem_description = Text("Traditional maintenance relies on fixing issues *after* they occur.\nThis leads to unexpected downtime, high repair costs, and reduced efficiency.", font_size=28)
        problem_description.scale_to_fit_width(10)

        self.play(Write(problem_title))
        self.wait(3)
        self.play(Write(problem_description))
        self.wait(10)

        # Visual: Broken Machine
        broken_machine = ImageMobject("broken_machine.png").scale(0.5) # Replace with actual image path
        self.play(FadeIn(broken_machine))
        self.wait(10)

        # Visual: Timeline of Reactive Maintenance
        timeline = VGroup(
            Text("Time", font_size=24),
            Line(LEFT, RIGHT, buff=0.5),
            Dot(color=RED).move_to(LEFT + 0.5 * (RIGHT - LEFT)),
            Text("Failure", font_size=18).next_to(Dot(color=RED), UP)
        ).arrange(DOWN)
        timeline.scale(0.7)
        self.play(FadeIn(timeline))
        self.wait(10)

        self.play(FadeOut(problem_title, problem_description, broken_machine, timeline))

        # --- Step 3: Impact Areas & Applications (70 seconds) ---
        impact_title = Text("The Promise: Predictive Maintenance", font_size=36)
        impact_title.scale_to_fit_width(10)
        impact_description = Text("Using data and machine learning to *predict* failures before they happen.\nThis allows for proactive maintenance, minimizing downtime and maximizing efficiency.", font_size=28)
        impact_description.scale_to_fit_width(10)

        self.play(Write(impact_title))
        self.wait(3)
        self.play(Write(impact_description))
        self.wait(10)

        # Visual: Areas of Impact
        impact_areas = VGroup(
            Text("Reduced Downtime", font_size=24, color=GREEN),
            Text("Lower Repair Costs", font_size=24, color=GREEN),
            Text("Increased Efficiency", font_size=24, color=GREEN),
            Text("Optimized Resource Allocation", font_size=24, color=GREEN)
        ).arrange(DOWN, aligned_edge=LEFT)
        impact_areas.scale(0.6)
        self.play(FadeIn(impact_areas))
        self.wait(15)

        # Visual: Applications
        applications = VGroup(
            Text("Manufacturing", font_size=24, color=BLUE),
            Text("Energy Production", font_size=24, color=BLUE),
            Text("Transportation", font_size=24, color=BLUE),
            Text("Healthcare", font_size=24, color=BLUE)
        ).arrange(DOWN, aligned_edge=LEFT)
        applications.scale(0.6)
        applications.next_to(impact_areas, RIGHT)
        self.play(FadeIn(applications))
        self.wait(15)

        self.play(FadeOut(impact_title, impact_description, impact_areas, applications))

        # --- Step 4: Learning Roadmap (64 seconds) ---
        roadmap_title = Text("Our Learning Journey", font_size=36)
        roadmap_title.scale_to_fit_width(10)

        # Visual: Roadmap Steps
        step1 = Text("1. Data Collection & Preprocessing", font_size=24, color=ORANGE)
        step2 = Text("2. Feature Engineering", font_size=24, color=ORANGE)
        step3 = Text("3. Model Selection & Training", font_size=24, color=ORANGE)
        step4 = Text("4. Evaluation & Deployment", font_size=24, color=ORANGE)

        roadmap = VGroup(step1, step2, step3, step4).arrange(DOWN, aligned_edge=LEFT)
        roadmap.scale(0.6)

        self.play(Write(roadmap_title))
        self.wait(3)
        self.play(FadeIn(roadmap))
        self.wait(15)

        # Highlight each step
        for i in range(4):
            self.play(Indicate(roadmap[i], color=YELLOW, scale_factor=1.1))
            self.wait(5)

        final_message = Text("Let's begin!", font_size=32)
        final_message.scale_to_fit_width(10)
        self.play(Write(final_message))
        self.wait(10)

        self.play(FadeOut(roadmap_title, roadmap, final_message))