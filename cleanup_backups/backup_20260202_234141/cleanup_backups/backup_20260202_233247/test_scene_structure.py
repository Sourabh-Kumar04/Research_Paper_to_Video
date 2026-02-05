#!/usr/bin/env python3
"""
Test for scene count and structure - Task 4.2
Tests that minimum 10 comprehensive scenes are generated and scene structure includes all required fields
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

class TestSceneStructure:
    """Test suite for scene count and structure requirements."""
    
    def setup_method(self):
        """Set up test environment."""
        from production_video_generator import ProductionVideoGenerator
        self.generator_class = ProductionVideoGenerator
    
    def test_minimum_scene_count(self):
        """Test that fallback generates minimum 10 comprehensive scenes."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scene_count = len(scenes)
        
        assert scene_count >= 10, f"Scene count {scene_count} is less than minimum 10 scenes"
        print(f"✅ Scene count: {scene_count} scenes (meets minimum 10)")
    
    def test_scene_required_fields(self):
        """Test that all scenes have required fields."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        required_fields = ['id', 'title', 'narration', 'duration']
        
        for i, scene in enumerate(scenes):
            for field in required_fields:
                assert field in scene, f"Scene {i+1} missing required field: {field}"
            
            # Validate field types and content
            assert isinstance(scene['id'], str), f"Scene {i+1} 'id' must be string"
            assert isinstance(scene['title'], str), f"Scene {i+1} 'title' must be string"
            assert isinstance(scene['narration'], str), f"Scene {i+1} 'narration' must be string"
            assert isinstance(scene['duration'], (int, float)), f"Scene {i+1} 'duration' must be number"
            
            # Validate content is not empty
            assert len(scene['id']) > 0, f"Scene {i+1} 'id' cannot be empty"
            assert len(scene['title']) > 0, f"Scene {i+1} 'title' cannot be empty"
            assert len(scene['narration']) > 0, f"Scene {i+1} 'narration' cannot be empty"
            assert scene['duration'] > 0, f"Scene {i+1} 'duration' must be positive"
        
        print(f"✅ All {len(scenes)} scenes have required fields with valid content")
    
    def test_scene_comprehensive_narration(self):
        """Test that scenes have comprehensive narration (300+ words for most scenes)."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        comprehensive_scenes = 0
        
        for i, scene in enumerate(scenes):
            word_count = len(scene['narration'].split())
            
            if word_count >= 300:
                comprehensive_scenes += 1
            
            # Each scene should have at least 200 words (reasonable minimum)
            assert word_count >= 200, f"Scene {i+1} has only {word_count} words (minimum 200)"
        
        # At least 60% of scenes should be comprehensive (300+ words)
        min_comprehensive = max(6, int(len(scenes) * 0.6))
        assert comprehensive_scenes >= min_comprehensive, f"Only {comprehensive_scenes} comprehensive scenes, need at least {min_comprehensive}"
        
        print(f"✅ {comprehensive_scenes}/{len(scenes)} scenes are comprehensive (300+ words)")
    
    def test_scene_duration_calculation(self):
        """Test that scene duration is properly calculated from narration."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        
        for i, scene in enumerate(scenes):
            word_count = len(scene['narration'].split())
            duration = scene['duration']
            
            # Duration should be calculated as: max(60, min(300, (word_count / 120) * 60 * 1.5))
            expected_duration = max(60.0, min(300.0, (word_count / 120) * 60 * 1.5))
            
            # Allow small floating point differences
            assert abs(duration - expected_duration) < 1.0, f"Scene {i+1} duration {duration}s doesn't match expected {expected_duration}s for {word_count} words"
            
            # Duration should be in reasonable range
            assert 60 <= duration <= 300, f"Scene {i+1} duration {duration}s not in range 60-300s"
        
        print(f"✅ All {len(scenes)} scenes have properly calculated durations")
    
    def test_scene_visual_descriptions(self):
        """Test that scenes have structured visual descriptions."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scenes_with_visuals = 0
        
        for i, scene in enumerate(scenes):
            if 'visual_description' in scene:
                visual_desc = scene['visual_description']
                
                # Should be a non-empty string
                assert isinstance(visual_desc, str), f"Scene {i+1} visual_description must be string"
                assert len(visual_desc) > 0, f"Scene {i+1} visual_description cannot be empty"
                
                # Should contain structured elements (at least some formatting)
                has_structure = any(marker in visual_desc for marker in ['┌─', '│', '└─', '📋', '📈', '🎨', '🔢'])
                if has_structure:
                    scenes_with_visuals += 1
        
        # Most scenes should have visual descriptions
        min_visual_scenes = max(5, int(len(scenes) * 0.5))
        assert scenes_with_visuals >= min_visual_scenes, f"Only {scenes_with_visuals} scenes have structured visuals, need at least {min_visual_scenes}"
        
        print(f"✅ {scenes_with_visuals}/{len(scenes)} scenes have structured visual descriptions")
    
    def test_scene_educational_elements(self):
        """Test that scenes contain educational elements (analogies, examples, definitions)."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        educational_scenes = 0
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Check for educational elements
            has_analogies = any(word in narration for word in ['like', 'imagine', 'think of', 'similar to', 'analogy'])
            has_examples = any(word in narration for word in ['example', 'for instance', 'such as', 'consider'])
            has_definitions = any(word in narration for word in ['means', 'defined as', 'refers to', 'is a'])
            
            if has_analogies or has_examples or has_definitions:
                educational_scenes += 1
        
        # Most scenes should have educational elements
        min_educational = max(8, int(len(scenes) * 0.8))
        assert educational_scenes >= min_educational, f"Only {educational_scenes} scenes have educational elements, need at least {min_educational}"
        
        print(f"✅ {educational_scenes}/{len(scenes)} scenes contain educational elements")
    
    def test_script_metadata(self):
        """Test that script contains proper metadata."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        # Check required script fields
        required_script_fields = ['title', 'total_duration', 'scenes']
        for field in required_script_fields:
            assert field in script, f"Script missing required field: {field}"
        
        # Validate script metadata
        assert isinstance(script['title'], str), "Script title must be string"
        assert isinstance(script['total_duration'], (int, float)), "Script total_duration must be number"
        assert isinstance(script['scenes'], list), "Script scenes must be list"
        
        assert len(script['title']) > 0, "Script title cannot be empty"
        assert script['total_duration'] > 0, "Script total_duration must be positive"
        assert len(script['scenes']) > 0, "Script scenes cannot be empty"
        
        print(f"✅ Script metadata is valid: '{script['title']}', {script['total_duration']/60:.1f} minutes, {len(script['scenes'])} scenes")

def run_structure_tests():
    """Run all scene structure tests."""
    print("🧪 Testing Scene Count and Structure Requirements")
    print("=" * 60)
    
    test_suite = TestSceneStructure()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_minimum_scene_count,
        test_suite.test_scene_required_fields,
        test_suite.test_scene_comprehensive_narration,
        test_suite.test_scene_duration_calculation,
        test_suite.test_scene_visual_descriptions,
        test_suite.test_scene_educational_elements,
        test_suite.test_script_metadata
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
    
    print(f"\n📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All structure tests passed! Scene structure meets requirements.")
        return True
    else:
        print("⚠️ Some structure tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = run_structure_tests()
    sys.exit(0 if success else 1)