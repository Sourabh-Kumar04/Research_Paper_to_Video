#!/usr/bin/env python3
"""
Test the working Gemma model for video generation
"""

import os
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

async def test_working_model():
    """Test video generation with working Gemma model."""
    
    print("🧪 TESTING WORKING GEMMA MODEL")
    print("=" * 60)
    
    from production_video_generator import ProductionVideoGenerator
    
    # Test with a unique job ID
    job_id = f"gemma_test_{int(time.time())}"
    paper_title = "Testing Gemma Model for Video Generation"
    output_dir = f"output/gemma_test_{job_id}"
    
    print(f"Job ID: {job_id}")
    print(f"Paper: {paper_title}")
    print(f"Output: {output_dir}")
    print(f"Model: models/gemma-3-27b-it")
    print()
    
    generator = ProductionVideoGenerator(job_id, paper_title, output_dir)
    
    try:
        print("⏳ Generating video with Gemma model...")
        print("🎬 This should use Gemma-generated Manim code")
        print()
        
        result = await generator.generate_video()
        
        if result:
            output_file = Path(result)
            if output_file.exists():
                file_size = output_file.stat().st_size
                duration_mb = file_size / 1024 / 1024
                
                print("✅ SUCCESS: Video generation completed!")
                print(f"📁 File: {output_file.name}")
                print(f"📊 Size: {duration_mb:.1f} MB")
                print("🎬 Video generated using Gemma-generated Manim code")
                
                # Check if Manim code files were created
                manim_files = list(Path(output_dir).glob("manim_scene_*.py"))
                print(f"📄 Gemma-generated Manim files: {len(manim_files)}")
                
                return True, str(output_file), duration_mb
            else:
                print("❌ ERROR: Output file not found")
                return False, None, 0
        else:
            print("❌ ERROR: Video generation returned None")
            return False, None, 0
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False, str(e), 0

async def main():
    """Main test function."""
    
    print("🔍 CHECKING SYSTEM STATUS WITH GEMMA")
    print("=" * 50)
    
    try:
        from llm.gemini_client import get_gemini_client
        client = get_gemini_client()
        print("✅ Gemma client available - proceeding with test")
        print()
    except Exception as e:
        print(f"❌ Gemma client error: {e}")
        print()
    
    # Test video generation
    success, result, size = await test_working_model()
    
    print()
    print("📋 TEST RESULTS")
    print("=" * 50)
    
    if success is True:
        print("✅ SUCCESS: Gemma model video generation worked!")
        print(f"✅ Generated: {size:.1f} MB video using Gemma Manim code")
        print("✅ System is now operational with Gemma models")
    else:
        print("❌ FAILURE: Video generation failed")
        print(f"❌ Error: {result}")
    
    print()
    print("🎯 GEMMA MODEL TEST COMPLETE")

if __name__ == "__main__":
    asyncio.run(main())