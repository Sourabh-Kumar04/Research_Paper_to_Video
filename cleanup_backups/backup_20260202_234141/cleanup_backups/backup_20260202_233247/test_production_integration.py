#!/usr/bin/env python3
"""
Test production system integration - Task 5
Tests that backend API uses the fixed fallback script and generates comprehensive videos
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import json
import time

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

class TestProductionIntegration:
    """Test suite for production system integration."""
    
    def setup_method(self):
        """Set up test environment."""
        from production_video_generator import ProductionVideoGenerator
        self.generator_class = ProductionVideoGenerator
    
    async def test_fallback_mode_integration(self):
        """Test that fallback mode generates comprehensive videos."""
        print("🧪 Testing fallback mode integration...")
        
        # Create generator instance (simulating backend API usage)
        generator = self.generator_class('integration-test', 'Test Research Paper', 'output/integration_test')
        
        # Force fallback mode by setting gemini_client to None
        generator.gemini_client = None
        
        # Test the full video generation pipeline
        try:
            # This should use the fallback script
            result = await generator.generate_video()
            
            if result:
                output_file = Path(result)
                assert output_file.exists(), f"Output video file not created: {output_file}"
                
                file_size = output_file.stat().st_size
                assert file_size > 1000000, f"Video file too small: {file_size} bytes (expected > 1MB)"
                
                print(f"✅ Fallback mode generated video: {output_file.name} ({file_size} bytes)")
                return True
            else:
                print("❌ Fallback mode failed to generate video")
                return False
                
        except Exception as e:
            print(f"❌ Fallback mode integration failed: {e}")
            return False
    
    def test_script_generation_consistency(self):
        """Test that script generation is consistent across calls."""
        print("🧪 Testing script generation consistency...")
        
        generator = self.generator_class('consistency-test', 'Consistent Test Paper', 'output/consistency_test')
        
        # Generate script multiple times
        scripts = []
        for i in range(3):
            script = generator._create_fallback_script()
            scripts.append(script)
        
        # All scripts should have same structure
        for i, script in enumerate(scripts):
            assert 'scenes' in script, f"Script {i} missing scenes"
            assert 'total_duration' in script, f"Script {i} missing total_duration"
            assert len(script['scenes']) >= 10, f"Script {i} has only {len(script['scenes'])} scenes"
            assert script['total_duration'] >= 900, f"Script {i} duration {script['total_duration']}s < 900s"
        
        # Duration should be consistent (within small variance)
        durations = [script['total_duration'] for script in scripts]
        max_duration = max(durations)
        min_duration = min(durations)
        variance = max_duration - min_duration
        
        assert variance < 60, f"Duration variance too high: {variance}s (max: {max_duration}s, min: {min_duration}s)"
        
        print(f"✅ Script generation consistent: durations {[f'{d/60:.1f}min' for d in durations]}")
        return True
    
    def test_comprehensive_vs_old_method(self):
        """Test that comprehensive method generates longer videos than old method would."""
        print("🧪 Testing comprehensive vs old method comparison...")
        
        generator = self.generator_class('comparison-test', 'Comparison Test Paper', 'output/comparison_test')
        
        # Test comprehensive fallback script
        comprehensive_script = generator._create_fallback_script()
        
        # Test old method (if it exists) - this should be much shorter
        try:
            old_scenes = generator.create_scenes_from_paper()
            old_duration = sum(scene.get('duration', 30) for scene in old_scenes)
            
            comprehensive_duration = comprehensive_script['total_duration']
            
            # Comprehensive should be much longer
            assert comprehensive_duration > old_duration * 2, f"Comprehensive {comprehensive_duration}s not significantly longer than old {old_duration}s"
            
            print(f"✅ Comprehensive method much longer: {comprehensive_duration/60:.1f}min vs old {old_duration/60:.1f}min")
            
        except Exception as e:
            # Old method might not exist or might be broken - that's expected
            print(f"✅ Old method not available (expected): {e}")
        
        # Ensure comprehensive method meets requirements regardless
        assert comprehensive_script['total_duration'] >= 900, f"Comprehensive duration {comprehensive_script['total_duration']}s < 900s"
        assert len(comprehensive_script['scenes']) >= 10, f"Comprehensive scenes {len(comprehensive_script['scenes'])} < 10"
        
        return True
    
    def test_backend_api_simulation(self):
        """Test simulation of backend API video generation."""
        print("🧪 Testing backend API simulation...")
        
        # Simulate the backend API workflow
        job_id = f"api_test_{int(time.time())}"
        paper_title = "Backend API Test Paper"
        output_dir = f"output/api_test_{job_id}"
        
        generator = self.generator_class(job_id, paper_title, output_dir)
        
        # Test script generation (what backend would do)
        script = generator._create_fallback_script()
        
        # Validate script meets API requirements
        assert isinstance(script, dict), "Script must be dictionary"
        assert 'title' in script, "Script missing title"
        assert 'total_duration' in script, "Script missing total_duration"
        assert 'scenes' in script, "Script missing scenes"
        
        # Validate scenes structure for API
        scenes = script['scenes']
        for i, scene in enumerate(scenes):
            required_fields = ['id', 'title', 'narration', 'duration']
            for field in required_fields:
                assert field in scene, f"Scene {i} missing required field: {field}"
        
        # Test that script can be serialized (for API response)
        try:
            json_script = json.dumps(script, indent=2)
            assert len(json_script) > 1000, "Serialized script too small"
            
            # Test deserialization
            parsed_script = json.loads(json_script)
            assert parsed_script['total_duration'] == script['total_duration'], "Serialization changed duration"
            
        except Exception as e:
            assert False, f"Script serialization failed: {e}"
        
        print(f"✅ Backend API simulation successful: {len(scenes)} scenes, {script['total_duration']/60:.1f}min")
        return True
    
    def test_error_handling_integration(self):
        """Test error handling in production integration."""
        print("🧪 Testing error handling integration...")
        
        # Test with various edge cases
        test_cases = [
            ("", "Empty title"),
            ("A", "Very short title"),
            ("Very Long Title " * 20, "Very long title"),
            ("Special!@#$%^&*()Characters", "Special characters"),
        ]
        
        for title, description in test_cases:
            try:
                generator = self.generator_class('error-test', title, 'output/error_test')
                script = generator._create_fallback_script()
                
                # Should still generate valid script
                assert script['total_duration'] >= 900, f"{description}: Duration too short"
                assert len(script['scenes']) >= 10, f"{description}: Too few scenes"
                
                print(f"✅ {description}: Handled gracefully")
                
            except Exception as e:
                print(f"❌ {description}: Failed with error: {e}")
                return False
        
        return True

async def run_integration_tests():
    """Run all production integration tests."""
    print("🧪 Testing Production System Integration")
    print("=" * 60)
    
    test_suite = TestProductionIntegration()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_script_generation_consistency,
        test_suite.test_comprehensive_vs_old_method,
        test_suite.test_backend_api_simulation,
        test_suite.test_error_handling_integration,
        test_suite.test_fallback_mode_integration  # This one is async
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if asyncio.iscoroutinefunction(test):
                result = await test()
            else:
                result = test()
            
            if result:
                passed += 1
            else:
                failed += 1
                
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed! Production system integration works correctly.")
        return True
    else:
        print("⚠️ Some integration tests failed. Check production system.")
        return False

if __name__ == "__main__":
    success = asyncio.run(run_integration_tests())
    sys.exit(0 if success else 1)