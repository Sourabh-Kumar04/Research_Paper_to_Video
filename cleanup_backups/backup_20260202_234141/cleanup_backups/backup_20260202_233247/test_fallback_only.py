#!/usr/bin/env python3
"""
Test only the fallback script to isolate the issue
"""

import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def test_fallback_script_direct():
    """Test fallback script directly without imports cache."""
    
    print("🔄 Testing Fallback Script (Direct Import)")
    print("=" * 50)
    
    # Import fresh
    from llm.gemini_client import GeminiClient
    
    # Create client
    client = GeminiClient()
    
    # Test fallback script
    result = client._create_fallback_script(
        "Test Paper Title",
        "Test paper content about machine learning"
    )
    
    print(f"Title: {result.get('title')}")
    print(f"Total Duration: {result.get('total_duration')} seconds")
    print(f"Target Audience: {result.get('target_audience')}")
    print(f"Teaching Style: {result.get('teaching_style')}")
    
    scenes = result.get('scenes', [])
    print(f"Scene Count: {len(scenes)}")
    
    if scenes:
        first_scene = scenes[0]
        print(f"\nFirst Scene:")
        print(f"  ID: {first_scene.get('id')}")
        print(f"  Title: {first_scene.get('title')}")
        print(f"  Duration: {first_scene.get('duration')} seconds")
        
        narration = first_scene.get('narration', '')
        word_count = len(narration.split())
        print(f"  Narration: {word_count} words")
        print(f"  Preview: {narration[:100]}...")
    
    return result

if __name__ == "__main__":
    result = test_fallback_script_direct()
    
    # Check if it's the new format
    duration = result.get('total_duration', 0)
    scene_count = len(result.get('scenes', []))
    
    if duration >= 300 and scene_count >= 6:
        print(f"\n✅ SUCCESS: New professional format detected!")
        print(f"   Duration: {duration}s ({duration/60:.1f} minutes)")
        print(f"   Scenes: {scene_count}")
    else:
        print(f"\n❌ ISSUE: Still using old format")
        print(f"   Duration: {duration}s (should be 300+)")
        print(f"   Scenes: {scene_count} (should be 6+)")