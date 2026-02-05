#!/usr/bin/env python3
"""
Test actual video generation to see what's happening
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

async def test_actual_generation():
    """Test actual video generation process."""
    
    print("🔍 Testing Actual Video Generation Process")
    print("=" * 50)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance with a test paper
    test_paper = "Attention Is All You Need"
    generator = ProductionVideoGenerator('test-actual', test_paper, 'output/test_actual')
    
    print(f"Paper: {test_paper}")
    print(f"Gemini available: {generator.gemini_client is not None}")
    print()
    
    # Test the script generation process (same as in generate_video)
    if generator.gemini_client:
        print("🤖 Testing Gemini script generation...")
        try:
            # This is what happens in the actual generate_video method
            analysis = await generator.gemini_client.analyze_paper_content(test_paper, "title")
            print(f"✅ Gemini analysis completed - Field: {analysis.get('field', 'Unknown')}")
            
            script_data = await generator.gemini_client.generate_script(
                analysis.get('title', test_paper),
                test_paper,
                "title"
            )
            print(f"✅ Gemini generated script with {len(script_data.get('scenes', []))} scenes")
            
            # Calculate total duration
            scenes = script_data.get('scenes', [])
            total_duration = sum(scene.get('duration', 0) for scene in scenes)
            print(f"📊 Gemini Script Stats:")
            print(f"   Scenes: {len(scenes)}")
            print(f"   Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
            
            # Show first few scenes
            for i, scene in enumerate(scenes[:3]):
                narration_words = len(scene.get('narration', '').split())
                print(f"   Scene {i+1}: {scene.get('title', 'Untitled')} - {narration_words} words, {scene.get('duration', 0):.1f}s")
            
        except Exception as e:
            print(f"❌ Gemini script generation failed: {e}")
            print("🔄 Using fallback script...")
            script_data = generator._create_fallback_script()
            
            scenes = script_data.get('scenes', [])
            total_duration = sum(scene.get('duration', 0) for scene in scenes)
            print(f"📊 Fallback Script Stats:")
            print(f"   Scenes: {len(scenes)}")
            print(f"   Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    else:
        print("🔄 No Gemini available, using fallback script...")
        script_data = generator._create_fallback_script()
        
        scenes = script_data.get('scenes', [])
        total_duration = sum(scene.get('duration', 0) for scene in scenes)
        print(f"📊 Fallback Script Stats:")
        print(f"   Scenes: {len(scenes)}")
        print(f"   Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_actual_generation())
    sys.exit(0 if success else 1)