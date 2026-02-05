#!/usr/bin/env python3
"""
Debug the while loop to see why it's running when it shouldn't
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def debug_while_loop():
    """Debug the while loop behavior."""
    
    print("🔍 Debugging While Loop Behavior")
    print("=" * 50)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('test-job', 'Test Paper Title', 'output/test')
    
    # Manually replicate the _create_fallback_script logic to debug
    analysis = generator._create_fallback_analysis()
    
    # Helper function to calculate scene duration based on narration word count
    def calculate_scene_duration(narration_text: str) -> float:
        word_count = len(narration_text.split())
        # 120 words per minute reading pace + time for visuals and pauses
        base_duration = (word_count / 120) * 60  # Convert to seconds
        # Ensure minimum 60s, maximum 300s (5 minutes)
        return max(60.0, min(300.0, base_duration * 1.5))  # 1.5x for pauses and visuals
    
    field = analysis.get("field", "Research")
    key_concepts = analysis.get("key_concepts", ["Innovation", "Analysis"])
    
    # Create the initial 3 scenes
    scenes = [
        {
            "id": "intro",
            "title": "The Big Picture: Why This Research Matters",
            "narration": f"Welcome to this comprehensive masterclass on 'Test Paper Title'. Imagine you're completely new to this field - that's exactly where we'll start. This research paper addresses a fundamental problem that affects millions of people and countless applications in our digital world. Think of it like this: before this work existed, researchers and engineers were trying to solve complex problems with tools that were like using a hammer when they needed a precision screwdriver. This paper introduced that precision screwdriver. We're going to explore not just what this research accomplished, but why it was needed, how it works from the ground up, and why it has transformed entire fields of study. By the end of this journey, you'll understand not only the technical details but also the broader implications and why this work has become so influential. We'll build your understanding step by step, defining every technical term, using real-world analogies, and connecting each concept to things you already know. No background knowledge is assumed - we'll start from the very beginning and build a complete understanding together. Think of this as your personal guide through one of the most important research breakthroughs in recent years, explained in a way that makes complex ideas accessible and engaging. The work represents a significant advance in {field}, with practical implications that extend far beyond academic research into real-world applications that impact how we build and deploy systems at scale. For example, the principles from this research have been incorporated into systems that process billions of transactions daily, enabling services that millions of people rely on every day. The methodology introduced here has become a standard approach in the field, influencing how researchers and engineers approach similar problems. What makes this work particularly remarkable is how it bridges the gap between theoretical innovation and practical implementation, providing both rigorous mathematical foundations and concrete solutions that work in real-world scenarios. Consider this analogy: if traditional approaches were like trying to navigate a complex city with only a basic map, this research provided GPS navigation with real-time traffic updates and optimal route planning.",
        },
        {
            "id": "historical_context",
            "title": "Historical Context: What Came Before and Why It Wasn't Enough",
            "narration": f"To understand why this research in {field} was revolutionary, we need to understand what came before it. Imagine the field before this paper as a bustling city with traffic jams everywhere - people were trying to get where they needed to go, but the roads weren't designed for the volume of traffic. The previous methods and approaches were like having only narrow, winding roads when what was needed was a modern highway system. Let's walk through the timeline of approaches that researchers tried before this breakthrough. Each previous method solved some problems but created others, like fixing a leak in one part of a pipe only to have it burst somewhere else. We'll explore the specific limitations that frustrated researchers for years: computational bottlenecks that made solutions impractically slow, memory requirements that exceeded what was available, and accuracy problems that made results unreliable. Think of these challenges as puzzle pieces that didn't quite fit together - until this research showed how to redesign the puzzle itself. Understanding this historical context is crucial because it shows us not just what this paper accomplished, but why it was such a significant leap forward. The researchers didn't just make incremental improvements; they fundamentally changed how we think about the entire problem domain. This historical perspective will help you appreciate the true innovation when we dive into the technical details. The evolution of approaches in {field} shows a clear progression from simple heuristics to sophisticated algorithmic solutions, with this work representing a major milestone in that journey. For example, early approaches in the field were like trying to solve a complex jigsaw puzzle by examining each piece in isolation, without considering how pieces might fit together. Researchers would develop specialized solutions for specific sub-problems, but these solutions often failed when combined or scaled to larger datasets. The computational complexity of these early methods grew exponentially with problem size, making them impractical for real-world applications. Consider the analogy of trying to organize a massive library using only manual card catalogs - it works for small collections but becomes completely unmanageable at scale.",
        },
        {
            "id": "prerequisites",
            "title": "Essential Foundations: Building Your Knowledge From Scratch",
            "narration": f"Before we dive into the exciting innovations in {field}, let's build a solid foundation of understanding. Think of this like learning to cook a complex dish - we need to understand the basic ingredients and techniques before we can appreciate the chef's masterpiece. We'll start with the most fundamental concepts and build up systematically. First, let's understand what we mean by key terms that will appear throughout our discussion. When we say 'algorithm,' think of it as a recipe - a step-by-step set of instructions that tells a computer exactly what to do. When we mention 'data structures,' imagine these as different ways of organizing information, like choosing between a filing cabinet, a library catalog system, or a digital database depending on what you need to store and how you need to access it. We'll explore the mathematical concepts that underpin this work, but don't worry - we'll focus on the intuitive meaning first, then show how the math captures these ideas precisely. Think of mathematical formulas as a precise language for describing relationships, like how a musical score precisely captures a melody. We'll also cover the computational concepts that are essential for understanding how these methods work in practice, using analogies to everyday processes you already understand. The key concepts we'll build include {', '.join(key_concepts[:4])}, each of which plays a crucial role in the overall approach. By the end of this section, you'll have all the building blocks needed to understand the revolutionary approach this paper introduces. To illustrate the importance of these foundations, consider how a skyscraper requires a solid foundation before construction can begin. Similarly, understanding these core concepts will enable you to grasp the sophisticated innovations that follow. We'll define technical terms as we encounter them, always providing intuitive explanations alongside formal definitions. This approach ensures that even complex mathematical concepts become accessible and meaningful.",
        }
    ]
    
    print(f"📊 Initial state:")
    print(f"   Scenes: {len(scenes)}")
    
    # Calculate duration for each scene BEFORE the while loop
    for scene in scenes:
        scene["duration"] = calculate_scene_duration(scene["narration"])
        print(f"   Scene '{scene['title'][:30]}...': {scene['duration']}s ({len(scene['narration'].split())} words)")
    
    # Calculate total duration
    total_duration = sum(scene["duration"] for scene in scenes)
    print(f"   Total duration: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    # Check while loop condition
    condition1 = total_duration < 900
    condition2 = len(scenes) < 20
    overall_condition = condition1 and condition2
    
    print(f"\n🔍 While loop condition analysis:")
    print(f"   total_duration < 900: {total_duration} < 900 = {condition1}")
    print(f"   len(scenes) < 20: {len(scenes)} < 20 = {condition2}")
    print(f"   Overall condition (AND): {overall_condition}")
    
    if overall_condition:
        print(f"   ✅ While loop WILL run (condition is True)")
        print(f"   🔄 Need to add scenes to reach minimum 900s or 10 scenes")
    else:
        print(f"   ❌ While loop will NOT run (condition is False)")
    
    return overall_condition

if __name__ == "__main__":
    will_run = asyncio.run(debug_while_loop())
    print(f"\n🎯 Result: While loop will {'run' if will_run else 'not run'}")