#!/usr/bin/env python3
"""
Fix the missing scenes definition in the fallback script
"""

def fix_scenes_definition():
    """Add the missing scenes definition."""
    
    # Read the current file
    with open('production_video_generator.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Find the line where we need to insert the scenes definition
    target_line = "        # Calculate duration for each scene"
    
    # The scenes definition to insert
    scenes_definition = '''        # Helper function to calculate scene duration based on narration word count
        def calculate_scene_duration(narration_text: str) -> float:
            word_count = len(narration_text.split())
            # 120 words per minute reading pace + time for visuals and pauses
            base_duration = (word_count / 120) * 60  # Convert to seconds
            # Ensure minimum 60s, maximum 300s (5 minutes)
            return max(60.0, min(300.0, base_duration * 1.5))  # 1.5x for pauses and visuals
        
        # Use comprehensive scenes for ALL papers (not just attention papers)
        field = analysis.get("field", "Research")
        key_concepts = analysis.get("key_concepts", ["Innovation", "Analysis"])
        
        # Create comprehensive educational scenes for ALL paper types
        scenes = [
            {
                "id": "intro",
                "title": "The Big Picture: Why This Research Matters",
                "narration": f"Welcome to this comprehensive masterclass on '{self.paper_content}'. Imagine you're completely new to this field - that's exactly where we'll start. This research paper addresses a fundamental problem that affects millions of people and countless applications in our digital world. Think of it like this: before this work existed, researchers and engineers were trying to solve complex problems with tools that were like using a hammer when they needed a precision screwdriver. This paper introduced that precision screwdriver. We're going to explore not just what this research accomplished, but why it was needed, how it works from the ground up, and why it has transformed entire fields of study. By the end of this journey, you'll understand not only the technical details but also the broader implications and why this work has become so influential. We'll build your understanding step by step, defining every technical term, using real-world analogies, and connecting each concept to things you already know. No background knowledge is assumed - we'll start from the very beginning and build a complete understanding together. Think of this as your personal guide through one of the most important research breakthroughs in recent years, explained in a way that makes complex ideas accessible and engaging. The work represents a significant advance in {field}, with practical implications that extend far beyond academic research into real-world applications that impact how we build and deploy systems at scale.",
                "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Opening & Big Picture        │
│ ⏱️ DURATION: 180 seconds               │
│ 📊 COMPLEXITY: Beginner                │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Research significance and impact      │
│ • Problem landscape before this work    │
│ • Learning journey roadmap             │
│ • Why this matters to everyone         │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Title slide with paper context │
│ Step 2: Problem landscape visualization │
│ Step 3: Impact areas and applications   │
│ Step 4: Learning roadmap preview        │
└─────────────────────────────────────────┘

🎨 COLOR CODING SCHEME:
┌─ VISUAL ORGANIZATION ───────────────────┐
│ 🔵 Blue: Main research topic           │
│ 🟢 Green: Positive impacts/benefits     │
│ 🟠 Orange: Key innovations              │
│ 🟣 Purple: Learning pathway             │
└─────────────────────────────────────────┘
""",
            },
            {
                "id": "historical_context",
                "title": "Historical Context: What Came Before and Why It Wasn't Enough",
                "narration": f"To understand why this research in {field} was revolutionary, we need to understand what came before it. Imagine the field before this paper as a bustling city with traffic jams everywhere - people were trying to get where they needed to go, but the roads weren't designed for the volume of traffic. The previous methods and approaches were like having only narrow, winding roads when what was needed was a modern highway system. Let's walk through the timeline of approaches that researchers tried before this breakthrough. Each previous method solved some problems but created others, like fixing a leak in one part of a pipe only to have it burst somewhere else. We'll explore the specific limitations that frustrated researchers for years: computational bottlenecks that made solutions impractically slow, memory requirements that exceeded what was available, and accuracy problems that made results unreliable. Think of these challenges as puzzle pieces that didn't quite fit together - until this research showed how to redesign the puzzle itself. Understanding this historical context is crucial because it shows us not just what this paper accomplished, but why it was such a significant leap forward. The researchers didn't just make incremental improvements; they fundamentally changed how we think about the entire problem domain. This historical perspective will help you appreciate the true innovation when we dive into the technical details. The evolution of approaches in {field} shows a clear progression from simple heuristics to sophisticated algorithmic solutions, with this work representing a major milestone in that journey.",
                "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Historical Context            │
│ ⏱️ DURATION: 195 seconds               │
│ 📊 COMPLEXITY: Beginner                │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Timeline of previous approaches       │
│ • Limitations of existing methods       │
│ • Why incremental fixes weren't enough  │
│ • The need for fundamental innovation   │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Timeline of research evolution  │
│ Step 2: Traffic jam analogy animation   │
│ Step 3: Limitation comparison charts    │
│ Step 4: Puzzle pieces not fitting      │
└─────────────────────────────────────────┘

📊 COMPARISON TABLES:
┌─ BEFORE vs NEEDED ──────────────────────┐
│ Aspect      │ Before    │ Needed       │
│ ─────────── │ ───────── │ ──────────── │
│ Speed       │ Slow      │ Fast         │
│ Memory      │ Excessive │ Efficient    │
│ Accuracy    │ Limited   │ High         │
│ Scalability │ Poor      │ Excellent    │
└─────────────────────────────────────────┘
""",
            },
            {
                "id": "prerequisites",
                "title": "Essential Foundations: Building Your Knowledge From Scratch",
                "narration": f"Before we dive into the exciting innovations in {field}, let's build a solid foundation of understanding. Think of this like learning to cook a complex dish - we need to understand the basic ingredients and techniques before we can appreciate the chef's masterpiece. We'll start with the most fundamental concepts and build up systematically. First, let's understand what we mean by key terms that will appear throughout our discussion. When we say 'algorithm,' think of it as a recipe - a step-by-step set of instructions that tells a computer exactly what to do. When we mention 'data structures,' imagine these as different ways of organizing information, like choosing between a filing cabinet, a library catalog system, or a digital database depending on what you need to store and how you need to access it. We'll explore the mathematical concepts that underpin this work, but don't worry - we'll focus on the intuitive meaning first, then show how the math captures these ideas precisely. Think of mathematical formulas as a precise language for describing relationships, like how a musical score precisely captures a melody. We'll also cover the computational concepts that are essential for understanding how these methods work in practice, using analogies to everyday processes you already understand. The key concepts we'll build include {', '.join(key_concepts[:4])}, each of which plays a crucial role in the overall approach. By the end of this section, you'll have all the building blocks needed to understand the revolutionary approach this paper introduces.",
                "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Essential Foundations         │
│ ⏱️ DURATION: 210 seconds               │
│ 📊 COMPLEXITY: Beginner to Intermediate │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Algorithms as recipes                 │
│ • Data structures as organization       │
│ • Mathematical precision language       │
│ • Computational building blocks         │
└─────────────────────────────────────────┘

🔢 MATHEMATICAL FORMULAS:
┌─ FORMULA DISPLAY ───────────────────────┐
│ Basic Notation: f(x) = y               │
│ ├─ Meaning: Function maps input to output│
│ ├─ Variables: x=input, y=output, f=rule │
│ └─ Intuition: Like a recipe transformer │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Cooking recipe analogy          │
│ Step 2: Filing system comparisons       │
│ Step 3: Musical score to math parallel  │
│ Step 4: Complete foundation overview    │
└─────────────────────────────────────────┘
""",
            }
        ]
        
'''
    
    # Replace the target line with the scenes definition + target line
    new_content = content.replace(target_line, scenes_definition + target_line)
    
    # Write the fixed content back
    with open('production_video_generator.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Added missing scenes definition")
    return True

if __name__ == "__main__":
    success = fix_scenes_definition()
    if success:
        print("✅ Scenes definition added successfully!")
    else:
        print("❌ Failed to add scenes definition")