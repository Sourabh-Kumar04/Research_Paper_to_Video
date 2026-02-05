#!/usr/bin/env python3
"""
Verify that font size changes are in place
"""

import re

def check_file(filepath, expected_values):
    """Check if file contains expected font size values."""
    print(f"\n{'='*60}")
    print(f"Checking: {filepath}")
    print(f"{'='*60}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    all_found = True
    for value, description in expected_values:
        if value in content:
            print(f"✅ FOUND: {description}")
            print(f"   Value: {value}")
        else:
            print(f"❌ NOT FOUND: {description}")
            print(f"   Expected: {value}")
            all_found = False
    
    # Find all content_font_size assignments
    pattern = r'content_font_size\s*=\s*(\d+)'
    matches = re.findall(pattern, content)
    if matches:
        print(f"\n📊 All content_font_size values found: {matches}")
        print(f"   Minimum: {min(map(int, matches))}")
        print(f"   Maximum: {max(map(int, matches))}")
    
    return all_found

# Expected values in production_video_generator.py
prod_expected = [
    ("content_font_size = 24", "Very long content: 24px"),
    ("content_font_size = 26", "Long content: 26px"),
    ("content_font_size = 28", "Medium content: 28px"),
    ("content_font_size = 32", "Short content: 32px"),
    ("content_font_size = max(content_font_size, 22)", "Minimum: 22px"),
    ("scene['paper_title'] = self.paper_content", "Paper title injection"),
]

# Expected values in gemini_client.py
gemini_expected = [
    ("content_font_size = 24", "Very long content: 24px"),
    ("content_font_size = 26", "Long content: 26px"),
    ("content_font_size = 28", "Medium content: 28px"),
    ("content_font_size = 32", "Short content: 32px"),
    ("content_font_size = max(content_font_size, 22)", "Minimum: 22px"),
    ("Content (22-32)", "Gemini prompt updated"),
]

print("\n" + "="*60)
print("FONT SIZE VERIFICATION SCRIPT")
print("="*60)

prod_ok = check_file("production_video_generator.py", prod_expected)
gemini_ok = check_file("src/llm/gemini_client.py", gemini_expected)

print("\n" + "="*60)
print("SUMMARY")
print("="*60)

if prod_ok and gemini_ok:
    print("✅ ALL CHANGES VERIFIED!")
    print("\n⚠️  IMPORTANT:")
    print("   The changes are in place, but you need to:")
    print("   1. Make sure backend is running (port 8000)")
    print("   2. Generate a NEW video job")
    print("   3. OLD videos will still have old font sizes")
    print("\n   The backend will use the new code for NEW videos only!")
else:
    print("❌ SOME CHANGES MISSING!")
    print("   Please review the output above.")

print("="*60)
