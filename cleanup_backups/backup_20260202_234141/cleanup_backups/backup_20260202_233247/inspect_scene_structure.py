#!/usr/bin/env python3
"""
Inspect the scene structure to verify it meets requirements
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def inspect_scene_structure():
    """Inspect the scene structure in detail."""
    
    print("🔍 Inspecting Scene Structure for Requirements Compliance")
    print("=" * 60)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('test-job', 'Test Paper Title', 'output/test')
    
    # Test fallback script
    script = generator._create_fallback_script()
    
    scenes = script['scenes']
    
    print(f"📊 OVERALL METRICS:")
    print(f"   Total Scenes: {len(scenes)}")
    print(f"   Total Duration: {script['total_duration']:.1f}s ({script['total_duration']/60:.1f} minutes)")
    print()
    
    # Check each scene for requirements compliance
    for i, scene in enumerate(scenes):
        print(f"🎬 SCENE {i+1}: {scene['title']}")
        print(f"   Duration: {scene['duration']}s")
        
        # Check narration length (should be 300-600 words for comprehensive)
        narration_words = len(scene['narration'].split())
        print(f"   Narration: {narration_words} words", end="")
        if narration_words >= 300:
            print(" ✅ (meets 300+ word requirement)")
        elif narration_words >= 200:
            print(" ⚠️ (close to 300 word requirement)")
        else:
            print(" ❌ (below 300 word requirement)")
        
        # Check if visual description exists and is structured
        if 'visual_description' in scene:
            visual_desc = scene['visual_description']
            has_structure = any(marker in visual_desc for marker in ['┌─', '│', '└─', '📋', '📈', '🎨', '🔢'])
            print(f"   Visual Description: {'✅ Structured' if has_structure else '❌ Not structured'}")
            
            # Check for specific elements
            has_concepts = '📋 MAIN CONCEPTS' in visual_desc
            has_visuals = '📈 VISUAL ELEMENTS' in visual_desc
            has_colors = '🎨 COLOR CODING' in visual_desc
            has_formulas = '🔢 MATHEMATICAL FORMULAS' in visual_desc or '📊 COMPARISON TABLES' in visual_desc
            
            print(f"   - Main Concepts: {'✅' if has_concepts else '❌'}")
            print(f"   - Visual Elements: {'✅' if has_visuals else '❌'}")
            print(f"   - Color Coding: {'✅' if has_colors else '❌'}")
            print(f"   - Formulas/Tables: {'✅' if has_formulas else '❌'}")
        else:
            print("   Visual Description: ❌ Missing")
        
        # Check for educational elements in narration
        narration = scene['narration'].lower()
        has_analogies = any(word in narration for word in ['like', 'imagine', 'think of', 'similar to', 'analogy'])
        has_examples = any(word in narration for word in ['example', 'for instance', 'such as', 'consider'])
        has_definitions = any(word in narration for word in ['means', 'defined as', 'refers to', 'is a'])
        
        print(f"   Educational Elements:")
        print(f"   - Analogies: {'✅' if has_analogies else '❌'}")
        print(f"   - Examples: {'✅' if has_examples else '❌'}")
        print(f"   - Definitions: {'✅' if has_definitions else '❌'}")
        
        print()
    
    # Overall compliance check
    print("📋 REQUIREMENTS COMPLIANCE SUMMARY:")
    
    # Task 3.1: Comprehensive narration (300-600 words)
    long_scenes = sum(1 for scene in scenes if len(scene['narration'].split()) >= 300)
    print(f"   3.1 Comprehensive Narration: {long_scenes}/{len(scenes)} scenes ≥300 words")
    
    # Task 3.2: Structured visual descriptions
    structured_scenes = sum(1 for scene in scenes if 'visual_description' in scene and any(marker in scene['visual_description'] for marker in ['┌─', '│', '└─']))
    print(f"   3.2 Structured Visual Descriptions: {structured_scenes}/{len(scenes)} scenes")
    
    # Task 3.3: Educational metadata
    educational_scenes = sum(1 for scene in scenes if any(word in scene['narration'].lower() for word in ['like', 'imagine', 'example', 'means']))
    print(f"   3.3 Educational Metadata: {educational_scenes}/{len(scenes)} scenes with educational elements")
    
    print()
    
    # Check if all requirements are met
    all_comprehensive = long_scenes == len(scenes)
    all_structured = structured_scenes == len(scenes)
    all_educational = educational_scenes >= len(scenes) * 0.8  # 80% threshold
    
    if all_comprehensive and all_structured and all_educational:
        print("✅ ALL TASK 3 REQUIREMENTS MET!")
        return True
    else:
        print("❌ Some Task 3 requirements need improvement:")
        if not all_comprehensive:
            print(f"   - Need {len(scenes) - long_scenes} more scenes with 300+ words")
        if not all_structured:
            print(f"   - Need {len(scenes) - structured_scenes} more scenes with structured visual descriptions")
        if not all_educational:
            print(f"   - Need more educational elements in scenes")
        return False

if __name__ == "__main__":
    success = asyncio.run(inspect_scene_structure())
    sys.exit(0 if success else 1)