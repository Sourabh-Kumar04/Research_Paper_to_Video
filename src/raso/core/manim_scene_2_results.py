
from manim import *

class ResultsScene(Scene):
    def construct(self):
        self.camera.background_color = "#0f0f23"
        
        title = Text(
            "Results", 
            font_size=64,
            color=BLUE, 
            weight=BOLD
        )
        title.to_edge(UP, buff=0.3)
        if title.width > 14:
            title.scale_to_fit_width(14)
        
        subtitle = Text(
            "Key Concepts & Analysis", 
            font_size=48,
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.2)
        
        top_line = Line(LEFT * 7, RIGHT * 7, color=BLUE, stroke_width=2)
        top_line.next_to(subtitle, DOWN, buff=0.15)
        
        content_text = Paragraph(
            "Results visualization",
            font_size=42,
            color=WHITE,
            line_spacing=1.2,
            alignment="left",
            width=13  # Fixed width for wrapping - NO SCALING
        )
        content_text.next_to(top_line, DOWN, buff=0.3)
        
        # NO SCALING - keep text at full size for maximum readability
        
        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(subtitle), run_time=0.4)
        self.play(Create(top_line), run_time=0.2)
        self.play(FadeIn(content_text, shift=UP*0.1), run_time=0.8)
        
        reading_time = max(4, min(10, len("Results visualization") / 60))
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.2)
