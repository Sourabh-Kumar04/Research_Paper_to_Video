#!/usr/bin/env python3
"""
Test the production video generator fallback script
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

async def test_production_fallback():
    """Test the production video generator fallback script."""
    
    print("🔄 Testing Production Video Generator Fallback Script")
    print("=" * 60)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('test-job', 'Test Paper Title', 'output/test')
    
    # Test fallback script
    script = generator._create_fallback_script()
    
    print(f"Title: {script['title']}")
    print(f"Total Duration: {script['total_duration']} seconds ({script['total_duration']/60:.1f} minutes)")
    print(f"Scene Count: {len(script['scenes'])}")
    
    # Check what keys are available
    print(f"Available keys: {list(script.keys())}")
    
    if 'target_audience' in script:
        print(f"Target Audience: {script['target_audience']}")
    if 'teaching_style' in script:
        print(f"Teaching Style: {script['teaching_style']}")
    
    scenes = script['scenes']
    print(f"\nFirst 5 Scenes:")
    for i, scene in enumerate(scenes[:5]):
        print(f"  Scene {i+1}: {scene['title']}")
        print(f"    Duration: {scene['duration']}s")
        print(f"    Narration: {len(scene['narration'].split())} words")
        print(f"    First 50 chars: {scene['narration'][:50]}...")
        print()
    
    # Check if it meets requirements
    duration = script['total_duration']
    scene_count = len(scenes)
    
    if duration >= 900 and scene_count >= 10:  # 15+ minutes, 10+ scenes
        print(f"✅ SUCCESS: Comprehensive format detected!")
        print(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
        print(f"   Scenes: {scene_count}")
        return True
    else:
        print(f"❌ ISSUE: Not comprehensive enough")
        print(f"   Duration: {duration}s (should be 900+)")
        print(f"   Scenes: {scene_count} (should be 10+)")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_production_fallback())
    sys.exit(0 if success else 1)