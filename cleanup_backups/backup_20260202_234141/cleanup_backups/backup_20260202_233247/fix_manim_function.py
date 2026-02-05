import re

# Read the file
with open('production_video_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function start
start_idx = None
for i, line in enumerate(lines):
    if 'def _create_fallback_manim_code(self, scene):' in line:
        start_idx = i
        break

# Find the function end (next async def)
end_idx = None
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith('async def _generate_manim_video'):
        end_idx = i
        break

# Create the new function
new_function = '''    def _create_fallback_manim_code(self, scene):
        """Create fallback Manim code with LARGE multi-line text and no delays."""
        title = scene.get('title', 'Scene')
        narration = scene.get('narration', 'Educational content')
        duration = scene.get('duration', 10.0)
        paper_title = scene.get('paper_title', title)
        
        # Clean title for class name
        class_name = ''.join(c for c in title if c.isalnum()) + 'Scene'
        if not class_name[0].isupper():
            class_name = 'Scene' + class_name
        
        # MUCH LARGER font sizes - responsive to screen
        title_font_size = 48  # Large title
        subtitle_font_size = 32  # Large subtitle
        content_font_size = 28  # LARGE content - readable
        
        # Escape special characters properly
        title_escaped = title.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'").replace('\\n', ' ')
        paper_title_escaped = paper_title.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'").replace('\\n', ' ')
        narration_escaped = narration.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'").replace('\\n', ' ')
        
        return f"""
from manim import *

class {class_name}(Scene):
    def construct(self):
        self.camera.background_color = "#0f0f23"
        
        title = Text(
            "{title_escaped}", 
            font_size={title_font_size},
            color=BLUE, 
            weight=BOLD
        )
        title.to_edge(UP, buff=0.4)
        if title.width > 13:
            title.scale_to_fit_width(13)
        
        subtitle = Text(
            "{paper_title_escaped}", 
            font_size={subtitle_font_size},
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.3)
        if subtitle.width > 13:
            subtitle.scale_to_fit_width(13)
        
        top_line = Line(LEFT * 6.5, RIGHT * 6.5, color=BLUE, stroke_width=3)
        top_line.next_to(subtitle, DOWN, buff=0.2)
        
        content_text = Paragraph(
            "{narration_escaped}",
            font_size={content_font_size},
            color=WHITE,
            line_spacing=1.5,
            alignment="left"
        )
        content_text.next_to(top_line, DOWN, buff=0.5)
        
        if content_text.width > 12:
            content_text.scale_to_fit_width(12)
        if content_text.height > 4:
            content_text.scale_to_fit_height(4)
        
        self.play(Write(title), run_time=0.8)
        self.play(FadeIn(subtitle), run_time=0.5)
        self.play(Create(top_line), run_time=0.3)
        self.play(FadeIn(content_text, shift=UP*0.1), run_time=1.0)
        
        reading_time = max(4, min(10, len("{narration_escaped}") / 60))
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.5)
"""

'''

# Replace the function
new_lines = lines[:start_idx] + [new_function] + lines[end_idx:]

# Write back
with open('production_video_generator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'Function replaced: lines {start_idx} to {end_idx}')
