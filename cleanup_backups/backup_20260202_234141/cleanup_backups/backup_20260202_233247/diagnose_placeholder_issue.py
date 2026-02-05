#!/usr/bin/env python3
"""
Diagnose placeholder video issue - why are we getting placeholders instead of real Manim videos?
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

async def diagnose_placeholder_issue():
    """Diagnose why we're getting placeholder videos instead of real Manim videos."""
    
    print("🔍 DIAGNOSING PLACEHOLDER VIDEO ISSUE")
    print("=" * 60)
    
    # Import the production video generator
    from production_video_generator import ProductionVideoGenerator
    
    # Create generator instance
    generator = ProductionVideoGenerator('diagnose-job', 'Test Paper for Diagnosis', 'output/diagnose')
    
    print(f"📊 SYSTEM STATUS:")
    print(f"   Gemini Available: {generator.gemini_client is not None}")
    print(f"   Job ID: {generator.job_id}")
    print(f"   Paper: {generator.paper_content}")
    print()
    
    # Test script generation
    print("🧪 TESTING SCRIPT GENERATION:")
    script = generator._create_fallback_script()
    scenes = script['scenes']
    print(f"   Generated Scenes: {len(scenes)}")
    print(f"   Total Duration: {script['total_duration']/60:.1f} minutes")
    print()
    
    # Test individual scene video generation
    print("🎬 TESTING INDIVIDUAL SCENE VIDEO GENERATION:")
    test_scene = scenes[0]  # Test first scene
    
    assets_dir = Path(generator.output_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)
    
    video_file = assets_dir / "test_scene_video.mp4"
    
    print(f"   Testing scene: {test_scene['title']}")
    print(f"   Output path: {video_file}")
    
    # Test the video generation method directly
    try:
        success = await generator._generate_real_video_content(test_scene, str(video_file), 0)
        
        if success and video_file.exists():
            file_size = video_file.stat().st_size
            print(f"   ✅ Video generated: {file_size} bytes")
            
            # Check if it's a placeholder or real video
            if file_size < 100000:  # Less than 100KB is likely placeholder
                print(f"   ⚠️ WARNING: File size {file_size} bytes suggests placeholder")
            else:
                print(f"   ✅ File size {file_size} bytes suggests real video")
                
        else:
            print(f"   ❌ Video generation failed")
            
    except Exception as e:
        print(f"   ❌ Video generation error: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    
    # Test audio generation
    print("🔊 TESTING AUDIO GENERATION:")
    audio_file = assets_dir / "test_scene_audio.wav"
    
    try:
        success = await generator._generate_real_audio_content(test_scene, str(audio_file), 0)
        
        if success and audio_file.exists():
            file_size = audio_file.stat().st_size
            print(f"   ✅ Audio generated: {file_size} bytes")
        else:
            print(f"   ❌ Audio generation failed")
            
    except Exception as e:
        print(f"   ❌ Audio generation error: {e}")
    
    print()
    
    # Check if Manim is working
    print("🎨 TESTING MANIM AVAILABILITY:")
    try:
        import manim
        print(f"   ✅ Manim imported successfully: {manim.__version__}")
    except ImportError as e:
        print(f"   ❌ Manim import failed: {e}")
    
    # Check video composition agent
    print("🎬 TESTING VIDEO COMPOSITION AGENT:")
    try:
        video_agent = generator.video_agent
        print(f"   ✅ Video agent available: {type(video_agent).__name__}")
    except Exception as e:
        print(f"   ❌ Video agent error: {e}")
    
    print()
    
    # Test full video generation pipeline
    print("🚀 TESTING FULL VIDEO GENERATION PIPELINE:")
    try:
        result = await generator.generate_video()
        
        if result:
            output_file = Path(result)
            if output_file.exists():
                file_size = output_file.stat().st_size
                print(f"   ✅ Full video generated: {output_file.name}")
                print(f"   📊 File size: {file_size} bytes ({file_size/1024/1024:.1f} MB)")
                
                # Analyze if it's placeholder or real
                if file_size < 1000000:  # Less than 1MB
                    print(f"   ⚠️ WARNING: Small file size suggests placeholder content")
                else:
                    print(f"   ✅ Large file size suggests real video content")
            else:
                print(f"   ❌ Output file not found: {result}")
        else:
            print(f"   ❌ Video generation returned None")
            
    except Exception as e:
        print(f"   ❌ Full pipeline error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(diagnose_placeholder_issue())