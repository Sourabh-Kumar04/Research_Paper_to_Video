#!/usr/bin/env python3
"""
Debug the fallback script generation to see what's happening
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

async def debug_fallback_script():
    """Debug the fallback script generation."""
    
    print("🔍 Debugging Fallback Script Generation")
    print("=" * 50)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('debug-job', 'Debug Paper Title', 'output/debug')
    
    # Get the fallback script
    script = generator._create_fallback_script()
    
    print(f"Total scenes: {len(script['scenes'])}")
    print(f"Total duration: {script['total_duration']:.1f}s ({script['total_duration']/60:.1f} minutes)")
    print()
    
    # Check each scene
    for i, scene in enumerate(script['scenes']):
        narration_words = len(scene['narration'].split())
        print(f"Scene {i+1}: {scene['title']}")
        print(f"  Words: {narration_words}")
        print(f"  Duration: {scene['duration']:.1f}s")
        print(f"  First 100 chars: {scene['narration'][:100]}...")
        print()
    
    return True

if __name__ == "__main__":
    success = asyncio.run(debug_fallback_script())
    sys.exit(0 if success else 1)