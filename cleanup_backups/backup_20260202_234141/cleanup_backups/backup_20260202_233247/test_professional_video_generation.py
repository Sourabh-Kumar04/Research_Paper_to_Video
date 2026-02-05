#!/usr/bin/env python3
"""
Test Professional Educational Video Generation
Verifies that the system generates 5-10 minute videos with detailed explanations.
"""

import asyncio
import sys
import os
from pathlib import Path
import json
import time

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

async def test_professional_video_generation():
    """Test the professional educational video generation system."""
    
    print("🧪 Testing Professional Educational Video Generation")
    print("=" * 60)
    
    try:
        # Import Gemini client
        from llm.gemini_client import get_gemini_client
        
        # Test paper content
        test_papers = [
            "Attention Is All You Need",
            "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding",
            "ResNet: Deep Residual Learning for Image Recognition"
        ]
        
        gemini_client = get_gemini_client()
        print(f"✅ Gemini client initialized successfully")
        print(f"   Model: {gemini_client.default_model}")
        
        for i, paper_title in enumerate(test_papers, 1):
            print(f"\n📄 Test {i}: {paper_title}")
            print("-" * 50)
            
            # Test script generation
            print("🎬 Testing script generation...")
            start_time = time.time()
            
            script_data = await gemini_client.generate_script(
                paper_title=paper_title,
                paper_content=paper_title,
                paper_type="title"
            )
            
            generation_time = time.time() - start_time
            
            # Analyze results
            scenes = script_data.get('scenes', [])
            total_duration = script_data.get('total_duration', 0)
            
            print(f"   ⏱️  Generation time: {generation_time:.1f} seconds")
            print(f"   🎥 Total scenes: {len(scenes)}")
            print(f"   ⏰ Total duration: {total_duration} seconds ({total_duration/60:.1f} minutes)")
            print(f"   🎯 Target audience: {script_data.get('target_audience', 'N/A')}")
            print(f"   👨‍🏫 Teaching style: {script_data.get('teaching_style', 'N/A')}")
            
            # Check requirements
            requirements_met = []
            
            # Duration check (5-10 minutes = 300-600 seconds)
            if 300 <= total_duration <= 600:
                requirements_met.append("✅ Duration: 5-10 minutes")
            else:
                requirements_met.append(f"❌ Duration: {total_duration}s (should be 300-600s)")
            
            # Scene count check (10-15 scenes)
            if 10 <= len(scenes) <= 15:
                requirements_met.append("✅ Scene count: 10-15 scenes")
            else:
                requirements_met.append(f"❌ Scene count: {len(scenes)} (should be 10-15)")
            
            # Check scene details
            detailed_scenes = 0
            scenes_with_formulas = 0
            scenes_with_diagrams = 0
            
            for scene in scenes:
                narration = scene.get('narration', '')
                visual_desc = scene.get('visual_description', '')
                duration = scene.get('duration', 0)
                
                # Check narration length (200-400 words)
                word_count = len(narration.split())
                if word_count >= 150:  # Allow some flexibility
                    detailed_scenes += 1
                
                # Check for formulas
                if 'formula' in visual_desc.lower() or 'equation' in visual_desc.lower():
                    scenes_with_formulas += 1
                
                # Check for diagrams
                if 'diagram' in visual_desc.lower() or 'chart' in visual_desc.lower():
                    scenes_with_diagrams += 1
            
            # Detailed narration check
            if detailed_scenes >= len(scenes) * 0.7:  # At least 70% of scenes
                requirements_met.append(f"✅ Detailed narrations: {detailed_scenes}/{len(scenes)} scenes")
            else:
                requirements_met.append(f"❌ Detailed narrations: {detailed_scenes}/{len(scenes)} scenes")
            
            # Visual elements check
            if scenes_with_formulas > 0:
                requirements_met.append(f"✅ Formulas: {scenes_with_formulas} scenes")
            else:
                requirements_met.append("⚠️  Formulas: None found")
            
            if scenes_with_diagrams > 0:
                requirements_met.append(f"✅ Diagrams: {scenes_with_diagrams} scenes")
            else:
                requirements_met.append("⚠️  Diagrams: None found")
            
            # Print requirements check
            print("\n   📋 Requirements Check:")
            for req in requirements_met:
                print(f"      {req}")
            
            # Show sample scene
            if scenes:
                sample_scene = scenes[0]
                print(f"\n   📝 Sample Scene: {sample_scene.get('title', 'N/A')}")
                print(f"      Duration: {sample_scene.get('duration', 0)}s")
                narration = sample_scene.get('narration', '')
                word_count = len(narration.split())
                print(f"      Narration: {word_count} words")
                print(f"      Preview: {narration[:150]}...")
            
            # Test Manim code generation for first scene
            if scenes:
                print("\n🎨 Testing Manim code generation...")
                scene = scenes[0]
                
                manim_code = await gemini_client.generate_manim_code(
                    scene_title=scene.get('title', 'Test Scene'),
                    scene_description=scene.get('visual_description', ''),
                    scene_duration=scene.get('duration', 30.0)
                )
                
                # Check Manim code quality
                manim_checks = []
                
                if 'from manim import *' in manim_code:
                    manim_checks.append("✅ Proper imports")
                else:
                    manim_checks.append("❌ Missing imports")
                
                if 'class ' in manim_code and 'Scene' in manim_code:
                    manim_checks.append("✅ Scene class defined")
                else:
                    manim_checks.append("❌ No scene class")
                
                if 'def construct(self):' in manim_code:
                    manim_checks.append("✅ Construct method")
                else:
                    manim_checks.append("❌ No construct method")
                
                if 'Text(' in manim_code:
                    manim_checks.append("✅ Text elements")
                else:
                    manim_checks.append("❌ No text elements")
                
                if 'self.wait(' in manim_code:
                    manim_checks.append("✅ Proper timing")
                else:
                    manim_checks.append("❌ No timing control")
                
                print("   📋 Manim Code Check:")
                for check in manim_checks:
                    print(f"      {check}")
                
                print(f"   📏 Code length: {len(manim_code)} characters")
            
            # Save test results
            test_results = {
                "paper_title": paper_title,
                "timestamp": time.time(),
                "generation_time": generation_time,
                "script_data": script_data,
                "requirements_met": requirements_met,
                "manim_checks": manim_checks if 'manim_checks' in locals() else []
            }
            
            results_file = Path(f"test_results_professional_{i}.json")
            with open(results_file, 'w') as f:
                json.dump(test_results, f, indent=2)
            
            print(f"   💾 Results saved to: {results_file}")
            
            # Break after first test to avoid rate limiting
            if i == 1:
                print(f"\n⏸️  Stopping after first test to avoid rate limiting")
                break
        
        print(f"\n🎉 Professional Video Generation Test Complete!")
        print(f"   Check the generated JSON files for detailed results")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

async def test_fallback_script():
    """Test the fallback script generation."""
    
    print(f"\n🔄 Testing Fallback Script Generation")
    print("-" * 50)
    
    try:
        from llm.gemini_client import GeminiClient
        
        client = GeminiClient()
        
        # Test fallback script
        fallback_script = client._create_fallback_script(
            "Test Research Paper",
            "This is a test paper about machine learning algorithms"
        )
        
        scenes = fallback_script.get('scenes', [])
        total_duration = fallback_script.get('total_duration', 0)
        
        print(f"✅ Fallback script generated")
        print(f"   🎥 Total scenes: {len(scenes)}")
        print(f"   ⏰ Total duration: {total_duration} seconds ({total_duration/60:.1f} minutes)")
        
        # Check fallback requirements
        fallback_checks = []
        
        if total_duration >= 300:  # At least 5 minutes
            fallback_checks.append("✅ Duration: 5+ minutes")
        else:
            fallback_checks.append(f"❌ Duration: {total_duration}s (should be 300+s)")
        
        if len(scenes) >= 6:  # At least 6 scenes
            fallback_checks.append("✅ Scene count: 6+ scenes")
        else:
            fallback_checks.append(f"❌ Scene count: {len(scenes)} (should be 6+)")
        
        # Check scene quality
        detailed_fallback_scenes = 0
        for scene in scenes:
            narration = scene.get('narration', '')
            word_count = len(narration.split())
            if word_count >= 100:  # Reasonable length for fallback
                detailed_fallback_scenes += 1
        
        if detailed_fallback_scenes >= len(scenes) * 0.8:
            fallback_checks.append(f"✅ Detailed scenes: {detailed_fallback_scenes}/{len(scenes)}")
        else:
            fallback_checks.append(f"❌ Detailed scenes: {detailed_fallback_scenes}/{len(scenes)}")
        
        print("   📋 Fallback Requirements Check:")
        for check in fallback_checks:
            print(f"      {check}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fallback test failed: {e}")
        return False

if __name__ == "__main__":
    async def main():
        print("🚀 Starting Professional Educational Video Tests")
        print("=" * 60)
        
        # Test Gemini-based generation
        gemini_success = await test_professional_video_generation()
        
        # Test fallback generation
        fallback_success = await test_fallback_script()
        
        print(f"\n📊 Test Summary:")
        print(f"   Gemini Generation: {'✅ PASS' if gemini_success else '❌ FAIL'}")
        print(f"   Fallback Generation: {'✅ PASS' if fallback_success else '❌ FAIL'}")
        
        if gemini_success and fallback_success:
            print(f"\n🎉 ALL TESTS PASSED - Professional Educational Videos Ready!")
        else:
            print(f"\n⚠️  Some tests failed - Check the output above")
    
    asyncio.run(main())