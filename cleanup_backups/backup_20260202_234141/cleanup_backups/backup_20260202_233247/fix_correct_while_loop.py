#!/usr/bin/env python3
"""
Fix the correct while loop in _create_fallback_script function
"""

def fix_correct_while_loop():
    """Fix the while loop in _create_fallback_script with diverse scene templates."""
    
    # Read the current file
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find and replace the while loop in _create_fallback_script
    old_while_loop = '''        # If total duration is less than 900 seconds (15 minutes), add more scenes
        scene_count = 0
        while total_duration < 900 and len(scenes) < 20:  # Limit to prevent infinite loop
            scene_count += 1
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
            total_duration = sum(scene["duration"] for scene in scenes)'''
    
    new_while_loop = '''        # Create diverse additional comprehensive scenes with 300+ words each
        scene_templates = [
            {
                "title_suffix": "Problem Definition and Core Challenges",
                "narration": f"Now that we have our foundations, let's precisely define the problem this research in {field} tackles. Imagine you're trying to solve a complex puzzle where each piece affects every other piece, and you need to find the optimal arrangement among billions of possibil