#!/usr/bin/env python3
"""
Fix the while loop condition to ensure 10+ scenes
"""

def fix_while_loop():
    """Fix the while loop condition."""
    
    # Read the current file
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find and replace the while loop line
    for i, line in enumerate(lines):
        if 'while total_duration < 900 and len(scenes) < 10:' in line:
            # Replace with the new condition
            lines[i] = line.replace(
                'while total_duration < 900 and len(scenes) < 10:',
                'while (total_duration < 900 or len(scenes) < 10) and len(scenes) < 20:'
            )
            print(f"✅ Fixed while loop condition at line {i+1}")
            break
    else:
        print("❌ Could not find the while loop to fix")
        return False
    
    # Write the fixed content back
    with open('production_video_generator.py', 'w', encoding='utf-8') as f:
        f.writelines(lines)
    
    return True

if __name__ == "__main__":
    success = fix_while_loop()
    if success:
        print("✅ While loop condition fixed successfully!")
    else:
        print("❌ Failed to fix while loop condition")