#!/usr/bin/env python3
"""
Test for fallback script duration - Task 4.1
Tests that fallback generates minimum 15-minute videos with various paper titles and content types
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

class TestFallbackScriptDuration:
    """Test suite for fallback script duration requirements."""
    
    def setup_method(self):
        """Set up test environment."""
        from production_video_generator import ProductionVideoGenerator
        self.generator_class = ProductionVideoGenerator
    
    def test_minimum_duration_attention_paper(self):
        """Test that attention paper generates minimum 15-minute video."""
        generator = self.generator_class('test-job', 'Attention Is All You Need', 'output/test')
        script = generator._create_fallback_script()
        
        total_duration = script['total_duration']
        assert total_duration >= 900, f"Duration {total_duration}s is less than minimum 900s (15 minutes)"
        print(f"✅ Attention paper: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    def test_minimum_duration_generic_paper(self):
        """Test that generic paper generates minimum 15-minute video."""
        generator = self.generator_class('test-job', 'Novel Machine Learning Approach', 'output/test')
        script = generator._create_fallback_script()
        
        total_duration = script['total_duration']
        assert total_duration >= 900, f"Duration {total_duration}s is less than minimum 900s (15 minutes)"
        print(f"✅ Generic paper: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    def test_minimum_duration_computer_vision_paper(self):
        """Test that computer vision paper generates minimum 15-minute video."""
        generator = self.generator_class('test-job', 'ResNet: Deep Residual Learning for Image Recognition', 'output/test')
        script = generator._create_fallback_script()
        
        total_duration = script['total_duration']
        assert total_duration >= 900, f"Duration {total_duration}s is less than minimum 900s (15 minutes)"
        print(f"✅ Computer vision paper: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    def test_minimum_duration_nlp_paper(self):
        """Test that NLP paper generates minimum 15-minute video."""
        generator = self.generator_class('test-job', 'BERT: Pre-training of Deep Bidirectional Transformers', 'output/test')
        script = generator._create_fallback_script()
        
        total_duration = script['total_duration']
        assert total_duration >= 900, f"Duration {total_duration}s is less than minimum 900s (15 minutes)"
        print(f"✅ NLP paper: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    def test_minimum_duration_optimization_paper(self):
        """Test that optimization paper generates minimum 15-minute video."""
        generator = self.generator_class('test-job', 'Adam: A Method for Stochastic Optimization', 'output/test')
        script = generator._create_fallback_script()
        
        total_duration = script['total_duration']
        assert total_duration >= 900, f"Duration {total_duration}s is less than minimum 900s (15 minutes)"
        print(f"✅ Optimization paper: {total_duration}s ({total_duration/60:.1f} minutes)")
    
    def test_duration_consistency_across_papers(self):
        """Test that different paper types generate consistent comprehensive durations."""
        paper_titles = [
            'Attention Is All You Need',
            'ResNet: Deep Residual Learning',
            'BERT: Bidirectional Transformers',
            'GPT: Generative Pre-Training',
            'Novel Algorithm for Optimization'
        ]
        
        durations = []
        for title in paper_titles:
            generator = self.generator_class('test-job', title, 'output/test')
            script = generator._create_fallback_script()
            duration = script['total_duration']
            durations.append(duration)
            
            # Each should meet minimum requirement
            assert duration >= 900, f"Paper '{title}' duration {duration}s < 900s"
        
        # All should be in comprehensive range (15-40 minutes)
        for i, duration in enumerate(durations):
            assert 900 <= duration <= 2400, f"Paper '{paper_titles[i]}' duration {duration}s not in comprehensive range"
        
        print(f"✅ All papers generate comprehensive durations: {[f'{d/60:.1f}min' for d in durations]}")
    
    def test_scene_count_supports_duration(self):
        """Test that scene count is sufficient to support minimum duration."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scene_count = len(scenes)
        total_duration = script['total_duration']
        
        # Should have at least 10 scenes for comprehensive coverage
        assert scene_count >= 10, f"Scene count {scene_count} < minimum 10 scenes"
        
        # Average scene duration should be reasonable (60-300 seconds)
        avg_duration = total_duration / scene_count
        assert 60 <= avg_duration <= 300, f"Average scene duration {avg_duration}s not in range 60-300s"
        
        print(f"✅ Scene count: {scene_count}, Total: {total_duration/60:.1f}min, Avg: {avg_duration:.1f}s/scene")

def run_duration_tests():
    """Run all duration tests."""
    print("🧪 Testing Fallback Script Duration Requirements")
    print("=" * 60)
    
    test_suite = TestFallbackScriptDuration()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_minimum_duration_attention_paper,
        test_suite.test_minimum_duration_generic_paper,
        test_suite.test_minimum_duration_computer_vision_paper,
        test_suite.test_minimum_duration_nlp_paper,
        test_suite.test_minimum_duration_optimization_paper,
        test_suite.test_duration_consistency_across_papers,
        test_suite.test_scene_count_supports_duration
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
        print("🎉 All duration tests passed! Fallback script meets requirements.")
        return True
    else:
        print("⚠️ Some duration tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = run_duration_tests()
    sys.exit(0 if success else 1)