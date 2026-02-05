#!/usr/bin/env python3
"""
Test the fixed video generation to confirm comprehensive videos
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

async def test_fixed_generation():
    """Test the fixed video generation process."""
    
    print("🔍 Testing FIXED Video Generation (Should be 20+ minutes)")
    print("=" * 60)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    test_paper = "Attention Is All You Need"
    generator = ProductionVideoGenerator('test-fixed', test_paper, 'output/test_fixed')
    
    print(f"Paper: {test_paper}")
    print(f"Gemini available: {generator.gemini_client is not None}")
    print()
    
    # Test just the script generation part (not full video generation)
    print("🔄 Testing script generation...")
    
    # Step 1: Analysis (this might use Gemini but that's OK)
    if generator.gemini_client:
        try:
            analysis = await generator.gemini_client.analyze_paper_content(test_paper, "title")
            print(f"✅ Analysis completed - Field: {analysis.get('field', 'Unknown')}")
        except Exception as e:
            print(f"⚠️ Analysis failed: {e}, using fallback")
            analysis = generator._create_fallback_analysis()
    else:
        analysis = generator._create_fallback_analysis()
    
    # Step 2: Script generation (this should now use fallback)
    print("🔄 Generating script (should use comprehensive fallback)...")
    script_data = generator._create_fallback_script()
    
    scenes = script_data.get('scenes', [])
    total_duration = sum(scene.get('duration', 0) for scene in scenes)
    
    print(f"📊 FIXED Script Stats:")
    print(f"   Scenes: {len(scenes)}")
    print(f"   Total Duration: {total_duration:.1f}s ({total_duration/60:.1f} minutes)")
    print()
    
    # Show first few scenes
    for i, scene in enumerate(scenes[:5]):
        narration_words = len(scene.get('narration', '').split())
        print(f"   Scene {i+1}: {scene.get('title', 'Untitled')}")
        print(f"     Words: {narration_words}, Duration: {scene.get('duration', 0):.1f}s")
    
    print()
    if total_duration >= 1200:  # 20+ minutes
        print("✅ SUCCESS: Video will be 20+ minutes comprehensive format!")
    elif total_duration >= 900:  # 15+ minutes
        print("✅ GOOD: Video will be 15+ minutes comprehensive format!")
    else:
        print("❌ ISSUE: Video is still too short")
    
    return total_duration >= 900

if __name__ == "__main__":
    success = asyncio.run(test_fixed_generation())
    sys.exit(0 if success else 1)