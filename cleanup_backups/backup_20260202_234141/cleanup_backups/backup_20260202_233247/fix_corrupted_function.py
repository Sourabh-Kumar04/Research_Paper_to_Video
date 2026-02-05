#!/usr/bin/env python3
"""
Fix the corrupted _create_fallback_script function by removing unreachable code after return statement
"""

def fix_corrupted_function():
    """Fix the corrupted function by removing unreachable code."""
    
    # Read the current file
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the return statement and remove everything after it until the next function
    lines = content.split('\n')
    
    # Find the _create_fallback_script function
    in_fallback_function = False
    function_start = -1
    return_found = False
    
    for i, line in enumerate(lines):
        if 'def _create_fallback_script(self):' in line:
            in_fallback_function = True
            function_start = i
            print(f"✅ Found _create_fallback_script function at line {i+1}")
            continue
        
        if in_fallback_function:
            # Look for the return statement
            if line.strip().startswith('return {') and not return_found:
                return_found = True
                print(f"✅ Found return statement at line {i+1}")
                continue
            
            # If we found the return statement and we're still in the function
            if return_found:
                # Look for the closing brace of the return statement
                if line.strip() == '}':
                    print(f"✅ Found end of return statement at line {i+1}")
                    # Remove all lines after this until the next function
                    j = i + 1
                    while j < len(lines):
                        next_line = lines[j].strip()
                        # Stop when we find the next function or class
                        if (next_line.startswith('def ') or 
                            next_line.startswith('class ') or
                            next_line.startswith('async def ')):
                            break
                        # Mark this line for removal
                        lines[j] = '# REMOVED: ' + lines[j]
                        j += 1
                    
                    print(f"✅ Marked {j - i - 1} lines for removal after return statement")
                    break
    
    # Remove the marked lines
    cleaned_lines = []
    for line in lines:
        if not line.strip().startswith('# REMOVED:'):
            cleaned_lines.append(line)
    
    # Write the cleaned content back
    with open('production_video_generator.py', 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))
    
    print("✅ Fixed corrupted function by removing unreachable code")
    return True

if __name__ == "__main__":
    success = fix_corrupted_function()
    if success:
        print("✅ Function corruption fix completed!")
    else:
        print("❌ Failed to fix function corruption")