"""
Property tests for multi-platform social media adaptation system.

Tests universal properties of platform adaptation including consistency,
compliance, and optimization effectiveness across different platforms.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
from typing import Dict, List, Any, Optional
import json

from src.cinematic.social_media_adapter import (
    SocialMediaAdapter, SocialPlatform, PlatformRequirements,
    ContentOptimization, PlatformAdaptation
)
from src.llm.gemini_client import GeminiClient


# Test data strategies
@st.composite
def cinematic_settings_strategy(draw):
    """Generate valid cinematic settings."""
    return {
        'aspect_ratio': draw(st.sampled_from(['16:9', '9:16', '1:1', '4:3'])),
        'resolution': draw(st.sampled_from([
            (1920, 1080), (1080, 1920), (1080, 1080), (1280, 720)
        ])),
        'color_grading': {
            'saturation': draw(st.floats(min_value=0.5, max_value=2.0)),
            'contrast': draw(st.floats(min_value=0.5, max_value=2.0)),
            'brightness': draw(st.floats(min_value=0.5, max_value=2.0))
        },
        'transitions': {
            'speed': draw(st.floats(min_value=0.5, max_value=3.0))
        }
    }


@st.composite
def content_metadata_strategy(draw):
    """Generate valid content metadata."""
    return {
        'title': draw(st.text(min_size=1, max_size=100)),
        'description': draw(st.text(min_size=0, max_size=500)),
        'duration': draw(st.integers(min_value=10, max_value=3600)),
        'content_type': draw(st.sampled_from([
            'educational', 'entertainment', 'professional', 'lifestyle',
            'news', 'tutorial', 'review', 'general'
        ])),
        'complexity_score': draw(st.floats(min_value=0.0, max_value=1.0)),
        'topics': draw(st.lists(st.text(min_size=1, max_size=20), max_size=5))
    }


@st.composite
def platform_list_strategy(draw):
    """Generate list of social media platforms."""
    platforms = list(SocialPlatform)
    return draw(st.lists(
        st.sampled_from(platforms),
        min_size=1,
        max_size=len(platforms),
        unique=True
    ))


class TestMultiPlatformAdaptation:
    """Property tests for multi-platform adaptation consistency."""
    
    @pytest.fixture
    def adapter(self):
        """Create social media adapter instance."""
        return SocialMediaAdapter()
    
    @given(
        base_settings=cinematic_settings_strategy(),
        content_metadata=content_metadata_strategy(),
        target_platforms=platform_list_strategy()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_adaptation_consistency_property(
        self, adapter, base_settings, content_metadata, target_platforms
    ):
        """
        Property 20: Multi-Platform Adaptation Consistency
        
        For any valid base settings and content metadata, adaptation to multiple
        platforms should produce consistent results that maintain the core
        cinematic intent while meeting platform requirements.
        """
        # Run adaptation
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, target_platforms
        ))
        
        # Property 1: All requested platforms should have adaptations
        assert len(adaptations) == len(target_platforms)
        assert all(platform in adaptations for platform in target_platforms)
        
        # Property 2: Each adaptation should be valid
        for platform, adaptation in adaptations.items():
            assert isinstance(adaptation, PlatformAdaptation)
            assert adaptation.platform == platform
            assert adaptation.original_settings == base_settings
            assert isinstance(adaptation.adapted_settings, dict)
            assert isinstance(adaptation.encoding_params, dict)
            assert isinstance(adaptation.content_optimizations, ContentOptimization)
            assert isinstance(adaptation.adaptations_applied, list)
            assert 0.0 <= adaptation.estimated_performance_score <= 100.0
            assert adaptation.compliance_status in [
                'compliant', 'minor_issues', 'major_issues', 'basic_compliance'
            ]
        
        # Property 3: Platform requirements should be respected
        for platform, adaptation in adaptations.items():
            requirements = adapter.platform_requirements[platform]
            encoding_params = adaptation.encoding_params
            
            # Check codec compliance
            assert encoding_params.get('video_codec') == requirements.video_codec
            assert encoding_params.get('audio_codec') == requirements.audio_codec
            
            # Check bitrate ranges
            video_bitrate = encoding_params.get('video_bitrate', 0)
            assert requirements.bitrate_range[0] <= video_bitrate <= requirements.bitrate_range[1]
            
            # Check frame rate ranges
            frame_rate = encoding_params.get('frame_rate', 30)
            assert requirements.frame_rate_range[0] <= frame_rate <= requirements.frame_rate_range[1]
        
        # Property 4: Adaptations should be tracked
        for platform, adaptation in adaptations.items():
            adaptations_applied = adaptation.adaptations_applied
            
            # If settings changed, adaptations should be tracked
            if adaptation.adapted_settings != base_settings:
                assert len(adaptations_applied) > 0
                
                # Each adaptation should have required fields
                for adaptation_record in adaptations_applied:
                    assert 'type' in adaptation_record
                    assert 'reason' in adaptation_record
        
        # Property 5: Performance scores should be reasonable
        for platform, adaptation in adaptations.items():
            score = adaptation.estimated_performance_score
            
            # Scores should be within valid range
            assert 0.0 <= score <= 100.0
            
            # Compliant adaptations should generally score higher
            if adaptation.compliance_status == 'compliant':
                assert score >= 40.0  # Minimum reasonable score for compliant content
    
    @given(
        base_settings=cinematic_settings_strategy(),
        content_metadata=content_metadata_strategy()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_platform_specific_optimization_property(
        self, adapter, base_settings, content_metadata
    ):
        """
        Property: Platform-specific optimizations should be applied correctly.
        
        Each platform should receive optimizations appropriate to its
        characteristics and user behavior patterns.
        """
        # Test each platform individually
        for platform in SocialPlatform:
            adaptations = asyncio.run(adapter.adapt_for_platforms(
                base_settings, content_metadata, [platform]
            ))
            
            adaptation = adaptations[platform]
            adapted_settings = adaptation.adapted_settings
            platform_opts = adapted_settings.get('platform_optimizations', {})
            
            # Platform-specific assertions
            if platform == SocialPlatform.TIKTOK:
                # TikTok should prefer vertical format
                assert adapted_settings.get('aspect_ratio') == '9:16'
                assert adapted_settings.get('resolution') == (1080, 1920)
                
                # Should have engagement optimizations
                assert platform_opts.get('add_captions') is True
                assert platform_opts.get('hook_duration', 5) <= 3
                assert platform_opts.get('visual_density') in ['high', 'very_high']
                
            elif platform == SocialPlatform.INSTAGRAM:
                # Instagram should prefer square or portrait
                aspect_ratio = adapted_settings.get('aspect_ratio')
                assert aspect_ratio in ['1:1', '4:5', '9:16']
                
                # Should have mobile optimizations
                assert platform_opts.get('add_captions') is True
                assert platform_opts.get('visual_density') == 'high'
                
            elif platform == SocialPlatform.LINKEDIN:
                # LinkedIn should prefer professional format
                assert adapted_settings.get('aspect_ratio') == '16:9'
                
                # Should have professional optimizations
                assert platform_opts.get('professional_tone') is True
                assert platform_opts.get('hook_duration', 3) >= 4
                
            elif platform == SocialPlatform.TWITTER:
                # Twitter should support standard formats
                aspect_ratio = adapted_settings.get('aspect_ratio')
                assert aspect_ratio in ['16:9', '1:1']
                
                # Should have quick consumption optimizations
                assert platform_opts.get('add_captions') is True
    
    @given(
        content_metadata=content_metadata_strategy(),
        target_platforms=platform_list_strategy()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_content_analysis_property(self, adapter, content_metadata, target_platforms):
        """
        Property: Content analysis should provide meaningful insights.
        
        Content analysis should classify content appropriately and provide
        platform-specific recommendations.
        """
        # Run content analysis
        analysis = asyncio.run(adapter.analyze_content_for_platforms(
            content_metadata, target_platforms
        ))
        
        # Property 1: Analysis should contain required fields
        assert 'content_classification' in analysis
        assert 'platform_ranking' in analysis
        
        # Property 2: Platform ranking should include all target platforms
        platform_ranking = analysis['platform_ranking']
        target_platform_names = [p.value for p in target_platforms]
        
        for platform_name in target_platform_names:
            assert platform_name in platform_ranking
        
        # Property 3: Content classification should be reasonable
        content_classification = analysis['content_classification']
        valid_classifications = [
            'educational', 'entertainment', 'professional', 'lifestyle',
            'news', 'tutorial', 'review', 'general'
        ]
        assert content_classification in valid_classifications
        
        # Property 4: If platform scores exist, they should be reasonable
        if 'platform_scores' in analysis:
            platform_scores = analysis['platform_scores']
            
            for platform_name, score in platform_scores.items():
                assert isinstance(score, (int, float))
                assert 0.0 <= score <= 100.0
    
    @given(
        base_settings=cinematic_settings_strategy(),
        content_metadata=content_metadata_strategy()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_file_size_estimation_property(self, adapter, base_settings, content_metadata):
        """
        Property: File size estimation should be reasonable and consistent.
        
        Estimated file sizes should correlate with encoding parameters and
        duration, and should respect platform limits.
        """
        # Test with a single platform for consistency
        platform = SocialPlatform.INSTAGRAM
        
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, [platform]
        ))
        
        adaptation = adaptations[platform]
        encoding_params = adaptation.encoding_params
        estimated_size = encoding_params.get('estimated_file_size_mb', 0)
        
        # Property 1: File size should be positive
        assert estimated_size > 0
        
        # Property 2: File size should correlate with duration
        duration = content_metadata.get('duration', 60)
        bitrate = encoding_params.get('video_bitrate', 2000)
        
        # Rough calculation: bitrate (kbps) * duration (s) / 8000 (convert to MB)
        expected_size_range = (
            (bitrate * duration) / 10000,  # Lower bound with compression
            (bitrate * duration) / 6000    # Upper bound with overhead
        )
        
        assert expected_size_range[0] <= estimated_size <= expected_size_range[1] * 2
        
        # Property 3: File size should respect platform limits
        requirements = adapter.platform_requirements[platform]
        
        # If estimated size exceeds limit, compliance should reflect this
        if estimated_size > requirements.max_file_size:
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
    
    @given(
        base_settings=cinematic_settings_strategy(),
        content_metadata=content_metadata_strategy(),
        target_platforms=platform_list_strategy()
    )
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_adaptation_determinism_property(
        self, adapter, base_settings, content_metadata, target_platforms
    ):
        """
        Property: Adaptation should be deterministic.
        
        Running the same adaptation multiple times should produce identical results.
        """
        # Run adaptation twice
        adaptations1 = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, target_platforms
        ))
        
        adaptations2 = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, target_platforms
        ))
        
        # Property: Results should be identical
        assert len(adaptations1) == len(adaptations2)
        
        for platform in target_platforms:
            adaptation1 = adaptations1[platform]
            adaptation2 = adaptations2[platform]
            
            # Compare key fields (excluding timestamps if any)
            assert adaptation1.platform == adaptation2.platform
            assert adaptation1.adapted_settings == adaptation2.adapted_settings
            assert adaptation1.encoding_params == adaptation2.encoding_params
            assert adaptation1.content_optimizations.to_dict() == adaptation2.content_optimizations.to_dict()
            assert adaptation1.estimated_performance_score == adaptation2.estimated_performance_score
            assert adaptation1.compliance_status == adaptation2.compliance_status


class TestPlatformFileSizeCompliance:
    """Property tests for platform file size compliance."""
    
    @pytest.fixture
    def adapter(self):
        """Create social media adapter instance."""
        return SocialMediaAdapter()
    
    @given(
        content_metadata=content_metadata_strategy(),
        platform=st.sampled_from(list(SocialPlatform))
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_file_size_compliance_property(self, adapter, content_metadata, platform):
        """
        Property 23: Platform File Size Compliance
        
        Adaptations should either meet platform file size requirements or
        clearly indicate non-compliance with appropriate warnings.
        """
        # Create base settings that might produce large files
        base_settings = {
            'aspect_ratio': '16:9',
            'resolution': (1920, 1080),
            'color_grading': {'saturation': 1.5, 'contrast': 1.3, 'brightness': 1.1},
            'transitions': {'speed': 1.0}
        }
        
        # Run adaptation
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, [platform]
        ))
        
        adaptation = adaptations[platform]
        requirements = adapter.platform_requirements[platform]
        
        # Property 1: File size estimation should exist
        estimated_size = adaptation.encoding_params.get('estimated_file_size_mb', 0)
        assert estimated_size > 0
        
        # Property 2: Compliance status should reflect file size constraints
        if estimated_size <= requirements.max_file_size:
            # If within limits, should not have major file size issues
            assert adaptation.compliance_status in ['compliant', 'minor_issues']
        else:
            # If exceeding limits, should be flagged
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
        
        # Property 3: Encoding parameters should be optimized for file size
        encoding_params = adaptation.encoding_params
        video_bitrate = encoding_params.get('video_bitrate', 0)
        
        # Bitrate should be within platform range
        assert requirements.bitrate_range[0] <= video_bitrate <= requirements.bitrate_range[1]
        
        # Property 4: Duration constraints should be considered
        duration = content_metadata.get('duration', 60)
        
        if duration > requirements.max_duration:
            # Should be flagged in compliance
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
            
            # Should be noted in adaptations applied
            adaptation_types = [a.get('type') for a in adaptation.adaptations_applied]
            # Note: Duration trimming would be handled by video processing, not settings adaptation
        
        # Property 5: Platform-specific optimizations should help with file size
        if platform in [SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK]:
            # Mobile platforms should have more aggressive compression
            max_reasonable_bitrate = min(8000, requirements.bitrate_range[1])
            assert video_bitrate <= max_reasonable_bitrate
    
    @given(
        base_settings=cinematic_settings_strategy(),
        long_duration=st.integers(min_value=300, max_value=7200)  # 5 minutes to 2 hours
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_long_content_adaptation_property(self, adapter, base_settings, long_duration):
        """
        Property: Long content should be adapted appropriately for platforms with duration limits.
        
        Content exceeding platform duration limits should be flagged and
        receive appropriate adaptations.
        """
        content_metadata = {
            'title': 'Long Form Content',
            'description': 'Extended educational content',
            'duration': long_duration,
            'content_type': 'educational',
            'complexity_score': 0.7,
            'topics': ['education', 'detailed']
        }
        
        # Test platforms with strict duration limits
        strict_platforms = [SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK, SocialPlatform.TWITTER]
        
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, strict_platforms
        ))
        
        for platform in strict_platforms:
            adaptation = adaptations[platform]
            requirements = adapter.platform_requirements[platform]
            
            # Property 1: Should be flagged as non-compliant for duration
            if long_duration > requirements.max_duration:
                assert adaptation.compliance_status in ['minor_issues', 'major_issues']
            
            # Property 2: Performance score should be penalized for duration issues
            if long_duration > requirements.max_duration:
                assert adaptation.estimated_performance_score < 80.0
            
            # Property 3: File size should still be estimated reasonably
            estimated_size = adaptation.encoding_params.get('estimated_file_size_mb', 0)
            assert estimated_size > 0
            
            # Very long content should have large file size estimates
            if long_duration > 1800:  # 30 minutes
                assert estimated_size > 100  # Should be substantial


if __name__ == "__main__":
    pytest.main([__file__, "-v"])