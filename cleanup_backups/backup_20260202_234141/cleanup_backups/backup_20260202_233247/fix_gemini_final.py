import re

# Read the file
with open('src/llm/gemini_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find the function start
start_idx = None
for i, line in enumerate(lines):
    if 'def _create_fallback_manim_code(self, scene_title: str, scene_description: str)' in line:
        start_idx = i
        break

# Find the function end (next def)
end_idx = None
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith('def _create_fallback_analysis'):
        end_idx = i
        break

# Create the new function with LARGE text
new_function = '''    def _create_fallback_manim_code(self, scene_title: str, scene_description: str) -> str:
        """Create fallback Manim code with VERY LARGE text and no delays."""
        class_name = f"{scene_title.replace(' ', '').replace('-', '').replace('_', '')}Scene"
        
        # VERY LARGE font sizes for readability
        title_font_size = 56
        subtitle_font_size = 40
        content_font_size = 36
        
        # Escape special characters
        title_escaped = scene_title.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'").replace('\\n', ' ')
        desc_escaped = scene_description.replace('\\\\', '\\\\\\\\').replace('"', '\\\\"').replace("'", "\\\\'").replace('\\n', ' ')
        
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
            "Key Concepts & Analysis", 
            font_size={subtitle_font_size},
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.3)
        
        top_line = Line(LEFT * 6.5, RIGHT * 6.5, color=BLUE, stroke_width=3)
        top_line.next_to(subtitle, DOWN, buff=0.2)
        
        content_text = Paragraph(
            "{desc_escaped}",
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
        
        reading_time = max(4, min(10, len("{desc_escaped}") / 60))
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.2)
"""

'''

# Replace the function
new_lines = lines[:start_idx] + [new_function] + lines[end_idx:]

# Write back
with open('src/llm/gemini_client.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print(f'✅ Gemini function replaced: lines {start_idx} to {end_idx}')
print('✅ Font sizes: Title=56px, Subtitle=40px, Content=36px')
print('✅ Fade-out: 0.2s (no delays)')
