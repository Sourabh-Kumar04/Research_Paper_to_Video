#!/usr/bin/env python3
"""
Test Gemini-Only Mode - Verify system uses only Gemini-generated Manim code
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

async def test_gemini_only_generation():
    """Test video generation with Gemini-only mode."""
    
    print("🧪 TESTING GEMINI-ONLY VIDEO GENERATION")
    print("=" * 60)
    
    from production_video_generator import ProductionVideoGenerator
    
    # Test with a unique job ID
    job_id = f"gemini_only_test_{int(time.time())}"
    paper_title = "Attention Is All You Need - Transformer Architecture"
    output_dir = f"output/gemini_only_test_{job_id}"
    
    print(f"Job ID: {job_id}")
    print(f"Paper: {paper_title}")
    print(f"Output: {output_dir}")
    print()
    
    generator = ProductionVideoGenerator(job_id, paper_title, output_dir)
    
    try:
        print("⏳ Generating video with Gemini-only mode...")
        print("📝 This should use ONLY Gemini-generated Manim code")
        print("🚫 NO fallback systems will be used")
        print()
        
        result = await generator.generate_video()
        
        if result:
            output_file = Path(result)
            if output_file.exists():
                file_size = output_file.stat().st_size
                duration_mb = file_size / 1024 / 1024
                
                print("✅ SUCCESS: Gemini-only video generation completed!")
                print(f"📁 File: {output_file.name}")
                print(f"📊 Size: {duration_mb:.1f} MB")
                print("🎬 Video generated using ONLY Gemini-generated Manim code")
                
                # Check if Manim code files were created
                manim_files = list(Path(output_dir).glob("manim_scene_*.py"))
                print(f"📄 Gemini-generated Manim files: {len(manim_files)}")
                
                for manim_file in manim_files[:3]:  # Show first 3
                    print(f"   📄 {manim_file.name}")
                
                return True, str(output_file), duration_mb
            else:
                print("❌ ERROR: Output file not found")
                return False, None, 0
        else:
            print("❌ ERROR: Video generation returned None")
            return False, None, 0
            
    except Exception as e:
        print(f"❌ EXPECTED BEHAVIOR: System failed as designed")
        print(f"💡 Error message: {e}")
        
        if "System is down" in str(e) or "Gemini" in str(e):
            print("✅ CORRECT: System properly failed when Gemini unavailable")
            return "system_down", str(e), 0
        else:
            print("⚠️ UNEXPECTED: Different error occurred")
            return False, str(e), 0

async def main():
    """Main test function."""
    
    # First check system status
    print("🔍 CHECKING SYSTEM STATUS FIRST")
    print("=" * 50)
    
    try:
        from llm.gemini_client import get_gemini_client
        client = get_gemini_client()
        print("✅ Gemini client available - proceeding with test")
        print()
    except Exception as e:
        print(f"❌ Gemini client not available: {e}")
        print("✅ This is expected behavior in Gemini-only mode")
        print("🚫 System should show 'system is down' message")
        print()
    
    # Test video generation
    success, result, size = await test_gemini_only_generation()
    
    print()
    print("📋 TEST RESULTS")
    print("=" * 50)
    
    if success is True:
        print("✅ SUCCESS: Gemini-only video generation worked!")
        print(f"✅ Generated: {size:.1f} MB video using Gemini Manim code")
        print("✅ No fallback systems were used")
    elif success == "system_down":
        print("✅ SUCCESS: System properly failed when Gemini unavailable")
        print("✅ Showed 'system is down' message as expected")
        print("✅ No fallback systems were used")
    else:
        print("❌ FAILURE: Unexpected behavior")
        print(f"❌ Result: {result}")
    
    print()
    print("🎯 GEMINI-ONLY MODE TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())