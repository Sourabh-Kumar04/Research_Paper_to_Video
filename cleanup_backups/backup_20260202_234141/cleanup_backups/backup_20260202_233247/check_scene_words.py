#!/usr/bin/env python3
"""
Check which scenes need word count enhancement
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

async def check_scenes():
    """Check scene word counts."""
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('test-job', 'Test Paper Title', 'output/test')
    
    # Test fallback script
    script = generator._create_fallback_script()
    
    scenes = script['scenes']
    
    print(f"Total Scenes: {len(scenes)}")
    print(f"Total Duration: {script['total_duration']:.1f}s")
    print()
    
    scenes_needing_enhancement = []
    
    for i, scene in enumerate(scenes):
        narration_words = len(scene['narration'].split())
        title = scene['title']
        
        print(f"Scene {i+1}: {title}")
        print(f"  Words: {narration_words}")
        
        if narration_words < 300:
            print(f"  Status: NEEDS ENHANCEMENT")
            scenes_needing_enhancement.append((i+1, title, narration_words))
        else:
            print(f"  Status: OK")
        print()
    
    print(f"Scenes needing enhancement: {len(scenes_needing_enhancement)}")
    for scene_num, title, words in scenes_needing_enhancement:
        print(f"  Scene {scene_num}: {title} ({words} words)")

if __name__ == "__main__":
    asyncio.run(check_scenes())