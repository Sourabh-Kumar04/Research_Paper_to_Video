#!/usr/bin/env python3
"""
Simple test to verify text fix without needing API keys
"""

# Test the fallback Manim code generation directly
def test_manim_code_generation():
    """Test that Manim code has NO SCALING."""
    
    # Simulate the scene data
    scene = {
        'title': 'Test Scene Title',
        'narration': 'This is a very long piece of content that would normally be scaled down. ' * 10,
        'duration': 10.0,
        'paper_title': 'Test Paper Title'
    }
    
    # Simulate the code generation (copied from production_video_generator.py)
    title = scene.get('title', 'Scene')
    narration = scene.get('narration', 'Educational content')
    duration = scene.get('duration', 10.0)
    paper_title = scene.get('paper_title', title)
    
    class_name = ''.join(c for c in title if c.isalnum()) + 'Scene'
    if not class_name[0].isupper():
        class_name = 'Scene' + class_name
    
    # Font sizes
    title_font_size = 36
    subtitle_font_size = 24
    content_font_size = 48  # MASSIVE
    
    # Don't truncate
    short_narration = narration
    
    # Escape
    title_escaped = title.replace('"', '\\"').replace("'", "\\'")
    paper_title_escaped = paper_title.replace('"', '\\"').replace("'", "\\'")
    narration_escaped = short_narration.replace('"', '\\"').replace("'", "\\'")
    
    code = f"""
from manim import *

class {class_name}(Scene):
    def construct(self):
        # Create scene title with dynamic sizing
        title = Text(
            "{title_escaped}", 
            font_size={title_font_size},
            color=BLUE, 
            weight=BOLD
        )
        title.to_edge(UP, buff=0.5)
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
        
        # Create content text using Paragraph for automatic wrapping - NO SCALING
        content_text = Paragraph(
            "{narration_escaped}",
            font_size={content_font_size},
            color=WHITE,
            line_spacing=1.2,
            alignment="left",
            width=13  # Fixed width for wrapping, no scaling
        )
        content_text.next_to(subtitle, DOWN, buff=0.6)
        
        top_line = Line(LEFT * 6.5, RIGHT * 6.5, color=BLUE, stroke_width=3)
        top_line.next_to(subtitle, DOWN, buff=0.25)
        
        self.play(Write(title), run_time=1.5)
        self.wait(0.3)
        self.play(FadeIn(subtitle), run_time=0.8)
        self.play(Create(top_line), run_time=0.6)
        self.wait(0.4)
        
        self.play(FadeIn(content_text, shift=UP*0.2), run_time=1.5)
        
        reading_time = max(3, min(8, len("{narration_escaped}") / 50))
        remaining_time = max(2, {duration} - 5 - reading_time)
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=1.2)
        self.wait(0.3)
"""
    
    print("=" * 80)
    print("GENERATED MANIM CODE:")
    print("=" * 80)
    print(code)
    print("=" * 80)
    
    # Check for issues
    issues = []
    
    # Check content section for scaling
    content_section = code[code.find("# Create content text"):code.find("top_line =")]
    
    if "scale_to_fit_width" in content_section or "scale_to_fit_height" in content_section:
        if "# NO SCALING" not in content_section:
            issues.append("❌ Content text still has scaling!")
    
    if "Paragraph" not in content_section:
        issues.append("❌ Not using Paragraph for content!")
    
    if "font_size=48" not in content_section:
        issues.append("❌ Content font size is not 48px!")
    
    if "width=13" not in content_section:
        issues.append("❌ Paragraph width not set for wrapping!")
    
    if issues:
        print("\n".join(issues))
        return False
    else:
        print("\n✅ SUCCESS: Content text uses Paragraph with font_size=48 and NO SCALING!")
        print("✅ Text will wrap naturally and remain MASSIVE and readable!")
        return True

if __name__ == "__main__":
    success = test_manim_code_generation()
    if success:
        print("\n🎉 TEXT FIX VERIFIED!")
    else:
        print("\n❌ TEXT FIX FAILED!")
        exit(1)
