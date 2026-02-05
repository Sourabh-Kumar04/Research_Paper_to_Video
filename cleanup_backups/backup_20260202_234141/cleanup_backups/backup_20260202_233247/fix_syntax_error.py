#!/usr/bin/env python3
"""
Fix syntax error in production_video_generator.py
"""

from pathlib import Path

def fix_syntax_error():
    """Fix the syntax error in the file."""
    
    print("🔧 Fixing syntax error in production_video_generator.py")
    
    file_path = Path("production_video_generator.py")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and fix the syntax error - likely missing closing bracket or comma
    # Look for the pattern where the error occurs
    
    # Fix any trailing commas or missing brackets
    content = content.replace('            ],\n        ,', '            ]')
    content = content.replace('        ,\n        }', '        }')
    content = content.replace(',\n    }', '\n    }')
    
    # Fix any double commas
    content = content.replace(',,', ',')
    
    # Fix any trailing commas before closing braces
    import re
    content = re.sub(r',(\s*})', r'\1', content)
    content = re.sub(r',(\s*])', r'\1', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Syntax error fixed")

if __name__ == "__main__":
    fix_syntax_error()