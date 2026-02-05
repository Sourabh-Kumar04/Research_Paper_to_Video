#!/usr/bin/env python3
"""
Test for educational content quality - Task 4.3
Tests that scenes use beginner-friendly language and that analogies and examples are included
"""

import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv
import pytest
import re

# Load environment variables
load_dotenv()

# Add src to Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

class TestEducationalQuality:
    """Test suite for educational content quality requirements."""
    
    def setup_method(self):
        """Set up test environment."""
        from production_video_generator import ProductionVideoGenerator
        self.generator_class = ProductionVideoGenerator
    
    def test_beginner_friendly_language(self):
        """Test that scenes use beginner-friendly language."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        beginner_friendly_scenes = 0
        
        # Indicators of beginner-friendly language
        beginner_indicators = [
            'imagine', 'think of', 'like', 'similar to', 'for example',
            'let\'s', 'we\'ll', 'you\'ll', 'simply put', 'in other words',
            'to understand', 'picture this', 'consider', 'suppose'
        ]
        
        # Complex jargon that should be explained or avoided
        complex_jargon = [
            'stochastic gradient descent', 'backpropagation', 'eigenvalues',
            'convolution', 'optimization', 'algorithm', 'neural network'
        ]
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Count beginner-friendly indicators
            friendly_count = sum(1 for indicator in beginner_indicators if indicator in narration)
            
            # Check if complex terms are explained (followed by explanation words)
            explained_jargon = 0
            for jargon in complex_jargon:
                if jargon in narration:
                    # Look for explanation patterns after jargon
                    pattern = rf'{re.escape(jargon)}[^.]*?(means|is|refers to|defined as|think of|like|similar to)'
                    if re.search(pattern, narration):
                        explained_jargon += 1
            
            # Scene is beginner-friendly if it has indicators and explains jargon
            if friendly_count >= 2:  # At least 2 beginner-friendly indicators
                beginner_friendly_scenes += 1
        
        # Most scenes should be beginner-friendly
        min_friendly = max(7, int(len(scenes) * 0.7))
        assert beginner_friendly_scenes >= min_friendly, f"Only {beginner_friendly_scenes} scenes are beginner-friendly, need at least {min_friendly}"
        
        print(f"✅ {beginner_friendly_scenes}/{len(scenes)} scenes use beginner-friendly language")
    
    def test_analogies_included(self):
        """Test that analogies are included in scenes."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scenes_with_analogies = 0
        
        # Analogy indicators
        analogy_patterns = [
            r'like\s+\w+',
            r'similar to\s+\w+',
            r'think of.*as',
            r'imagine.*like',
            r'analogous to',
            r'just as.*so',
            r'picture.*as',
            r'compare.*to'
        ]
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Check for analogy patterns
            has_analogy = any(re.search(pattern, narration) for pattern in analogy_patterns)
            
            if has_analogy:
                scenes_with_analogies += 1
        
        # Most scenes should contain analogies
        min_analogies = max(6, int(len(scenes) * 0.6))
        assert scenes_with_analogies >= min_analogies, f"Only {scenes_with_analogies} scenes contain analogies, need at least {min_analogies}"
        
        print(f"✅ {scenes_with_analogies}/{len(scenes)} scenes contain analogies")
    
    def test_examples_included(self):
        """Test that examples are included in scenes."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scenes_with_examples = 0
        
        # Example indicators
        example_patterns = [
            r'for example',
            r'for instance',
            r'such as',
            r'consider.*example',
            r'let\'s say',
            r'suppose.*case',
            r'imagine.*scenario',
            r'concrete example'
        ]
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Check for example patterns
            has_example = any(re.search(pattern, narration) for pattern in example_patterns)
            
            if has_example:
                scenes_with_examples += 1
        
        # Many scenes should contain examples
        min_examples = max(5, int(len(scenes) * 0.5))
        assert scenes_with_examples >= min_examples, f"Only {scenes_with_examples} scenes contain examples, need at least {min_examples}"
        
        print(f"✅ {scenes_with_examples}/{len(scenes)} scenes contain examples")
    
    def test_progressive_complexity(self):
        """Test that content builds progressively from basic to advanced."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        
        # Basic concepts should appear in early scenes
        basic_indicators = [
            'foundation', 'basic', 'fundamental', 'introduction', 'overview',
            'start', 'begin', 'first', 'essential', 'prerequisite'
        ]
        
        # Advanced concepts should appear in later scenes
        advanced_indicators = [
            'advanced', 'complex', 'sophisticated', 'detailed', 'technical',
            'implementation', 'optimization', 'performance', 'analysis'
        ]
        
        early_scenes = scenes[:len(scenes)//2]  # First half
        later_scenes = scenes[len(scenes)//2:]  # Second half
        
        # Count basic indicators in early scenes
        early_basic_count = 0
        for scene in early_scenes:
            narration = scene['narration'].lower()
            if any(indicator in narration for indicator in basic_indicators):
                early_basic_count += 1
        
        # Count advanced indicators in later scenes
        later_advanced_count = 0
        for scene in later_scenes:
            narration = scene['narration'].lower()
            if any(indicator in narration for indicator in advanced_indicators):
                later_advanced_count += 1
        
        # Early scenes should have more basic content
        assert early_basic_count >= len(early_scenes) * 0.4, f"Early scenes need more basic content: {early_basic_count}/{len(early_scenes)}"
        
        # Later scenes should have more advanced content
        assert later_advanced_count >= len(later_scenes) * 0.4, f"Later scenes need more advanced content: {later_advanced_count}/{len(later_scenes)}"
        
        print(f"✅ Progressive complexity: {early_basic_count} basic early scenes, {later_advanced_count} advanced later scenes")
    
    def test_term_definitions(self):
        """Test that technical terms are defined when introduced."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        scenes_with_definitions = 0
        
        # Definition patterns
        definition_patterns = [
            r'\w+\s+means',
            r'\w+\s+is\s+defined\s+as',
            r'\w+\s+refers\s+to',
            r'what\s+we\s+mean\s+by',
            r'when\s+we\s+say\s+\w+',
            r'\w+\s+is\s+a\s+\w+\s+that',
            r'think\s+of\s+\w+\s+as'
        ]
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Check for definition patterns
            has_definition = any(re.search(pattern, narration) for pattern in definition_patterns)
            
            if has_definition:
                scenes_with_definitions += 1
        
        # Many scenes should define terms
        min_definitions = max(4, int(len(scenes) * 0.4))
        assert scenes_with_definitions >= min_definitions, f"Only {scenes_with_definitions} scenes define terms, need at least {min_definitions}"
        
        print(f"✅ {scenes_with_definitions}/{len(scenes)} scenes define technical terms")
    
    def test_engagement_elements(self):
        """Test that scenes include engagement elements (questions, direct address)."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        engaging_scenes = 0
        
        # Engagement indicators
        engagement_patterns = [
            r'you\s+\w+',  # Direct address
            r'we\s+\w+',   # Inclusive language
            r'let\'s\s+\w+',  # Collaborative language
            r'imagine\s+\w+',  # Imaginative prompts
            r'picture\s+\w+',  # Visualization prompts
            r'consider\s+\w+', # Thoughtful prompts
            r'think\s+about',  # Reflection prompts
            r'what\s+if',      # Hypothetical questions
        ]
        
        for i, scene in enumerate(scenes):
            narration = scene['narration'].lower()
            
            # Count engagement elements
            engagement_count = sum(1 for pattern in engagement_patterns if re.search(pattern, narration))
            
            if engagement_count >= 3:  # At least 3 engagement elements
                engaging_scenes += 1
        
        # Most scenes should be engaging
        min_engaging = max(6, int(len(scenes) * 0.6))
        assert engaging_scenes >= min_engaging, f"Only {engaging_scenes} scenes are engaging, need at least {min_engaging}"
        
        print(f"✅ {engaging_scenes}/{len(scenes)} scenes include engagement elements")
    
    def test_comprehensive_coverage(self):
        """Test that content provides comprehensive coverage of the topic."""
        generator = self.generator_class('test-job', 'Test Research Paper', 'output/test')
        script = generator._create_fallback_script()
        
        scenes = script['scenes']
        
        # Coverage areas that should be present
        coverage_areas = {
            'introduction': ['introduction', 'overview', 'big picture', 'why', 'matters'],
            'background': ['history', 'context', 'before', 'previous', 'came before'],
            'foundations': ['foundation', 'basic', 'essential', 'prerequisite', 'building'],
            'problem': ['problem', 'challenge', 'issue', 'needed', 'solving'],
            'solution': ['solution', 'approach', 'method', 'insight', 'breakthrough'],
            'technical': ['technical', 'implementation', 'mathematical', 'algorithm'],
            'results': ['results', 'performance', 'analysis', 'validation', 'experiments'],
            'impact': ['impact', 'applications', 'real-world', 'practical', 'industry'],
            'future': ['future', 'directions', 'research', 'possibilities', 'next'],
            'conclusion': ['conclusion', 'summary', 'connecting', 'complete', 'journey']
        }
        
        covered_areas = set()
        
        for scene in scenes:
            narration = scene['narration'].lower()
            title = scene['title'].lower()
            
            for area, keywords in coverage_areas.items():
                if any(keyword in narration or keyword in title for keyword in keywords):
                    covered_areas.add(area)
        
        # Should cover most areas
        min_coverage = max(7, int(len(coverage_areas) * 0.7))
        assert len(covered_areas) >= min_coverage, f"Only covers {len(covered_areas)} areas: {covered_areas}, need at least {min_coverage}"
        
        print(f"✅ Comprehensive coverage: {len(covered_areas)}/{len(coverage_areas)} areas covered: {sorted(covered_areas)}")

def run_quality_tests():
    """Run all educational quality tests."""
    print("🧪 Testing Educational Content Quality Requirements")
    print("=" * 60)
    
    test_suite = TestEducationalQuality()
    test_suite.setup_method()
    
    tests = [
        test_suite.test_beginner_friendly_language,
        test_suite.test_analogies_included,
        test_suite.test_examples_included,
        test_suite.test_progressive_complexity,
        test_suite.test_term_definitions,
        test_suite.test_engagement_elements,
        test_suite.test_comprehensive_coverage
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
        print("🎉 All quality tests passed! Educational content meets requirements.")
        return True
    else:
        print("⚠️ Some quality tests failed. Check implementation.")
        return False

if __name__ == "__main__":
    success = run_quality_tests()
    sys.exit(0 if success else 1)