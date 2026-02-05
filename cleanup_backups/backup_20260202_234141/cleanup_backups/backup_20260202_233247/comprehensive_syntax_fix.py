#!/usr/bin/env python3
"""
Comprehensive syntax fix for production_video_generator.py
"""

from pathlib import Path
import re

def comprehensive_syntax_fix():
    """Fix all syntax issues in the file."""
    
    print("🔧 Comprehensive syntax fix for production_video_generator.py")
    
    file_path = Path("production_video_generator.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix 1: Remove stray commas after visual descriptions
    content = re.sub(r'""",\s*\n\s*,\s*\n', '""",\n', content)
    
    # Fix 2: Fix any missing commas before new dictionary entries
    content = re.sub(r'(\s*"audience_level": "[^"]*")\s*\n(\s*"video_structure")', r'\1,\n\2', content)
    content = re.sub(r'(\s*"significance": "[^"]*")\s*\n(\s*"audience_level")', r'\1,\n\2', content)
    
    # Fix 3: Fix any trailing commas before closing braces/brackets
    content = re.sub(r',(\s*[}\]])', r'\1', content)
    
    # Fix 4: Fix double commas
    content = re.sub(r',,+', ',', content)
    
    # Fix 5: Fix any orphaned commas at the beginning of lines
    content = re.sub(r'\n\s*,\s*\n', '\n', content)
    
    # Fix 6: Ensure proper comma placement in dictionaries
    content = re.sub(r'(\]\s*)\n(\s*"key_concepts")', r'\1,\n\2', content)
    content = re.sub(r'(\}\s*)\n(\s*"key_concepts")', r'\1,\n\2', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Comprehensive syntax fix applied")

if __name__ == "__main__":
    comprehensive_syntax_fix()