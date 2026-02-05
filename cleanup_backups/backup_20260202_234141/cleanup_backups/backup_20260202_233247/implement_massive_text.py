#!/usr/bin/env python3
"""Implement MASSIVE text sizes with minimal scaling."""

def create_massive_text_manim():
    """Create Manim template with MASSIVE text that fills screen."""
    return '''    def _create_fallback_manim_code(self, scene):
        """Create Manim code with MASSIVE text filling the screen."""
        title = scene.get('title', 'Scene')
        narration = scene.get('narration', 'Educational content')
        duration = scene.get('duration', 10.0)
        paper_title = scene.get('paper_title', title)
        
        # Clean title for class name
        class_name = ''.join(c for c in title if c.isalnum()) + 'Scene'
        if not class_name[0].isupper():
            class_name = 'Scene' + class_name
        
        # MASSIVE font sizes - fill the screen!
        title_font_size = 72  # MASSIVE
        subtitle_font_size = 56  # MASSIVE
        content_font_size = 48  # MASSIVE
        
        # Escape special characters
        title_escaped = title.replace('\\\\\\\\', '\\\\\\\\\\\\\\\\').replace('"', '\\\\\\\\"').replace("'", "\\\\\\\\'").replace('\\\\n', ' ')
        paper_title_escaped = paper_title.replace('\\\\\\\\', '\\\\\\\\\\\\\\\\').replace('"', '\\\\\\\\"').replace("'", "\\\\\\\\'").replace('\\\\n', ' ')
        narration_escaped = narration.replace('\\\\\\\\', '\\\\\\\\\\\\\\\\').replace('"', '\\\\\\\\"').replace("'", "\\\\\\\\'").replace('\\\\n', ' ')
        
        return f"""
from manim import *

class {class_name}(Scene):
    def construct(self):
        self.camera.background_color = "#0f0f23"
        
        # MASSIVE title - minimal margins
        title = Text(
            "{title_escaped}", 
            font_size={title_font_size},
            color=BLUE, 
            weight=BOLD
        )
        title.to_edge(UP, buff=0.3)
        # Only scale if REALLY too wide
        if title.width > 14:
            title.scale_to_fit_width(14)
        
        # MASSIVE subtitle
        subtitle = Text(
            "{paper_title_escaped}", 
            font_size={subtitle_font_size},
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.2)
        if subtitle.width > 14:
            subtitle.scale_to_fit_width(14)
        
        # Thin line
        top_line = Line(LEFT * 7, RIGHT * 7, color=BLUE, stroke_width=2)
        top_line.next_to(subtitle, DOWN, buff=0.15)
        
        # MASSIVE content - use Paragraph with explicit width for wrapping
        content_text = Paragraph(
            "{narration_escaped}",
            font_size={content_font_size},
            color=WHITE,
            line_spacing=1.2,
            alignment="left",
            width=13
        )
        content_text.next_to(top_line, DOWN, buff=0.3)
        
        # Only scale height if absolutely necessary
        if content_text.height > 5.5:
            scale_factor = 5.5 / content_text.height
            # Don't scale below 80% (keep text large)
            if scale_factor > 0.8:
                content_text.scale(scale_factor)
        
        # FAST animations
        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(subtitle), run_time=0.4)
        self.play(Create(top_line), run_time=0.2)
        self.play(FadeIn(content_text, shift=UP*0.1), run_time=0.8)
        
        # Reading time
        reading_time = max(4, min(10, len("{narration_escaped}") / 60))
        self.wait(reading_time)
        
        # Fast fade out
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.2)
"""
'''

# Read and update production_video_generator.py
with open('production_video_generator.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Find function start
start_idx = None
for i, line in enumerate(lines):
    if 'def _create_fallback_manim_code(self, scene):' in line:
        start_idx = i
        break

# Find function end
end_idx = None
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith('async def _generate_manim_video'):
        end_idx = i
        break

# Replace function
new_function = create_massive_text_manim()
new_lines = lines[:start_idx] + [new_function] + lines[end_idx:]

with open('production_video_generator.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ production_video_generator.py updated')
print('   Font sizes: Title=72px, Subtitle=56px, Content=48px')
print('   Minimal scaling, maximum screen usage')

# Update gemini_client.py similarly
with open('src/llm/gemini_client.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

start_idx = None
for i, line in enumerate(lines):
    if 'def _create_fallback_manim_code(self, scene_title: str, scene_description: str)' in line:
        start_idx = i
        break

end_idx = None
for i in range(start_idx + 1, len(lines)):
    if lines[i].strip().startswith('def _create_fallback_analysis'):
        end_idx = i
        break

# Create adapted version for gemini_client
gemini_function = '''    def _create_fallback_manim_code(self, scene_title: str, scene_description: str) -> str:
        """Create Manim code with MASSIVE text filling the screen."""
        class_name = f"{scene_title.replace(' ', '').replace('-', '').replace('_', '')}Scene"
        
        title_font_size = 72
        subtitle_font_size = 56
        content_font_size = 48
        
        title_escaped = scene_title.replace('\\\\\\\\', '\\\\\\\\\\\\\\\\').replace('"', '\\\\\\\\"').replace("'", "\\\\\\\\'").replace('\\\\n', ' ')
        desc_escaped = scene_description.replace('\\\\\\\\', '\\\\\\\\\\\\\\\\').replace('"', '\\\\\\\\"').replace("'", "\\\\\\\\'").replace('\\\\n', ' ')
        
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
        title.to_edge(UP, buff=0.3)
        if title.width > 14:
            title.scale_to_fit_width(14)
        
        subtitle = Text(
            "Key Concepts & Analysis", 
            font_size={subtitle_font_size},
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.2)
        
        top_line = Line(LEFT * 7, RIGHT * 7, color=BLUE, stroke_width=2)
        top_line.next_to(subtitle, DOWN, buff=0.15)
        
        content_text = Paragraph(
            "{desc_escaped}",
            font_size={content_font_size},
            color=WHITE,
            line_spacing=1.2,
            alignment="left",
            width=13
        )
        content_text.next_to(top_line, DOWN, buff=0.3)
        
        if content_text.height > 5.5:
            scale_factor = 5.5 / content_text.height
            if scale_factor > 0.8:
                content_text.scale(scale_factor)
        
        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(subtitle), run_time=0.4)
        self.play(Create(top_line), run_time=0.2)
        self.play(FadeIn(content_text, shift=UP*0.1), run_time=0.8)
        
        reading_time = max(4, min(10, len("{desc_escaped}") / 60))
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.2)
"""

'''

new_lines = lines[:start_idx] + [gemini_function] + lines[end_idx:]

with open('src/llm/gemini_client.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('✅ src/llm/gemini_client.py updated')
print('✅ MASSIVE text implementation complete!')
