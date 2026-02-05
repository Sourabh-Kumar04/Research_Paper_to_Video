#!/usr/bin/env python3
"""
Fix stray commas in production_video_generator.py
"""

from pathlib import Path
import re

def fix_stray_commas():
    """Fix the stray commas after visual descriptions."""
    
    print("🔧 Fixing stray commas in production_video_generator.py")
    
    file_path = Path("production_video_generator.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Fix the pattern: """,\n            ,
    # Should be: """,
    content = re.sub(r'""",\s*,\s*\n', '""",\n', content)
    
    # Also fix any other stray comma patterns
    content = re.sub(r'(\s*),\s*\n(\s*"key_concepts")', r'\1\n\2', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Fixed stray commas")

if __name__ == "__main__":
    fix_stray_commas()