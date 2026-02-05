import re

# Read the file
with open('production_video_generator.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Replace font sizes with MUCH larger values
content = content.replace('title_font_size = 48', 'title_font_size = 56')
content = content.replace('subtitle_font_size = 32', 'subtitle_font_size = 40')
content = content.replace('content_font_size = 28', 'content_font_size = 36')

# Remove the final wait that causes black screen
content = content.replace('self.play(FadeOut(everything), run_time=0.5)', 'self.play(FadeOut(everything), run_time=0.2)')

# Write back
with open('production_video_generator.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Font sizes increased: Title=56px, Subtitle=40px, Content=36px')
print('✅ Fade-out time reduced: 0.5s → 0.2s')

# Do the same for gemini_client.py
with open('src/llm/gemini_client.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace('title_font_size = 48', 'title_font_size = 56')
content = content.replace('subtitle_font_size = 32', 'subtitle_font_size = 40')
content = content.replace('content_font_size = 28', 'content_font_size = 36')
content = content.replace('self.play(FadeOut(everything), run_time=0.5)', 'self.play(FadeOut(everything), run_time=0.2)')

with open('src/llm/gemini_client.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ Gemini client also updated')
