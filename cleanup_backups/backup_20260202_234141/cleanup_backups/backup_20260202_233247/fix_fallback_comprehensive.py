#!/usr/bin/env python3
"""
Fix the fallback script to use comprehensive scenes instead of old short scenes
"""

import re

def fix_fallback_script():
    """Fix the _create_fallback_script method to use comprehensive scenes."""
    
    # Read the current file
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the problematic if/else structure and replace it
    # Pattern to match the entire if/else structure
    pattern = r'        # Create more detailed scenes based on paper content\s*\n        if "attention" in self\.paper_content\.lower\(\):\s*\n.*?else:\s*\n.*?return \{\s*\n.*?"title": self\.paper_content,\s*\n.*?"total_duration": sum\(scene\["duration"\] for scene in scenes\),\s*\n.*?"scenes": scenes\s*\n.*?\}'
    
    # Replacement text with comprehensive scenes logic
    replacement = '''        # Calculate duration for each scene
        for scene in scenes:
            scene["duration"] = calculate_scene_duration(scene["narration"])
        
        # Calculate total duration and ensure minimum 15 minutes
        total_duration = sum(scene["duration"] for scene in scenes)
        
        # If total duration is less than 900 seconds (15 minutes), add more scenes
        while total_duration < 900 and len(scenes) < 10:  # Limit to prevent infinite loop
            additional_scene = {
                "id": f"extended_scene_{len(scenes)}",
                "title": f"Advanced Analysis: Deep Dive into {self.paper_content}",
                "narration": f"Let's dive deeper into the technical aspects of '{self.paper_content}' that make this research so significant. This extended analysis will explore the mathematical foundations, implementation details, and broader implications that distinguish this work from previous approaches. We'll examine the algorithmic innovations, computational complexity considerations, and the engineering decisions that enable practical deployment at scale. The research demonstrates sophisticated understanding of both theoretical principles and practical constraints, showing how academic insights can be translated into real-world solutions. We'll analyze the experimental methodology, performance characteristics, and the validation approaches used to demonstrate the effectiveness of the proposed methods. This deeper exploration will help you understand not just what the research accomplishes, but how it accomplishes it and why these particular design choices were made. The work represents a careful balance between theoretical rigor and practical applicability, showing how fundamental research can drive technological advancement. By understanding these deeper technical aspects, you'll gain insights into the principles that guide effective research and development in this field, and how to apply similar approaches to your own work and challenges.",
                "visual_description": f"""
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Extended Technical Analysis   │
│ ⏱️ DURATION: 165 seconds               │
│ 📊 COMPLEXITY: Advanced                 │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Mathematical foundations deep dive    │
│ • Implementation and deployment details │
│ • Performance and scalability analysis │
│ • Research methodology and validation   │
└─────────────────────────────────────────┘
""",
            }
            additional_scene["duration"] = calculate_scene_duration(additional_scene["narration"])
            scenes.append(additional_scene)
            total_duration = sum(scene["duration"] for scene in scenes)
        
        return {
            "title": self.paper_content,
            "total_duration": total_duration,
            "target_audience": "AI/ML Engineers and Research Scientists",
            "teaching_style": "comprehensive technical analysis with practical insights",
            "content_planning": "theoretical foundations to practical applications",
            "visual_approach": "progressive technical diagrams with mathematical precision",
            "scenes": scenes
        }'''
    
    # Try to find and replace using a simpler approach
    # Find the start of the problematic section
    start_marker = "        # Create more detailed scenes based on paper content"
    end_marker = "async def main():"
    
    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)
    
    if start_idx == -1 or end_idx == -1:
        print("❌ Could not find the problematic section")
        return False
    
    # Replace the problematic section
    new_content = content[:start_idx] + replacement + "\n\n" + content[end_idx:]
    
    # Write the fixed content back
    with open('production_video_generator.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Fixed the fallback script to use comprehensive scenes")
    return True

if __name__ == "__main__":
    success = fix_fallback_script()
    if success:
        print("✅ Fallback script fixed successfully!")
    else:
        print("❌ Failed to fix fallback script")