"""
Property tests for platform file size compliance.

Tests that social media adaptations properly handle file size constraints
and provide accurate compliance reporting across different platforms.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from typing import Dict, List, Any
import math

from src.cinematic.social_media_adapter import (
    SocialMediaAdapter, SocialPlatform, PlatformRequirements
)


# Test data strategies
@st.composite
def high_bitrate_settings_strategy(draw):
    """Generate settings that might produce large files."""
    return {
        'aspect_ratio': draw(st.sampled_from(['16:9', '4:3'])),  # Higher resolution formats
        'resolution': draw(st.sampled_from([
            (1920, 1080), (2560, 1440), (3840, 2160)  # HD to 4K
        ])),
        'color_grading': {
            'saturation': draw(st.floats(min_value=1.2, max_value=2.0)),  # High saturation
            'contrast': draw(st.floats(min_value=1.2, max_value=2.0)),    # High contrast
            'brightness': draw(st.floats(min_value=1.0, max_value=1.5))
        },
        'transitions': {
            'speed': draw(st.floats(min_value=0.5, max_value=1.0))  # Slower = more detail
        }
    }


@st.composite
def variable_duration_content_strategy(draw):
    """Generate content with varying durations."""
    duration = draw(st.integers(min_value=5, max_value=3600))  # 5 seconds to 1 hour
    
    return {
        'title': draw(st.text(min_size=1, max_size=50)),
        'description': draw(st.text(min_size=0, max_size=200)),
        'duration': duration,
        'content_type': draw(st.sampled_from([
            'educational', 'entertainment', 'professional'
        ])),
        'complexity_score': draw(st.floats(min_value=0.3, max_value=1.0)),  # Higher complexity
        'topics': draw(st.lists(st.text(min_size=1, max_size=15), max_size=3))
    }


class TestPlatformFileSizeCompliance:
    """Comprehensive tests for platform file size compliance."""
    
    @pytest.fixture
    def adapter(self):
        """Create social media adapter instance."""
        return SocialMediaAdapter()
    
    @given(
        base_settings=high_bitrate_settings_strategy(),
        content_metadata=variable_duration_content_strategy(),
        platform=st.sampled_from(list(SocialPlatform))
    )
    @settings(max_examples=50, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_file_size_estimation_accuracy_property(
        self, adapter, base_settings, content_metadata, platform
    ):
        """
        Property: File size estimation should be mathematically sound.
        
        File size estimates should correlate with bitrate, duration, and
        encoding parameters in a predictable way.
        """
        # Run adaptation
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, [platform]
        ))
        
        adaptation = adaptations[platform]
        encoding_params = adaptation.encoding_params
        
        # Extract parameters
        video_bitrate = encoding_params.get('video_bitrate', 2000)  # kbps
        audio_bitrate = encoding_params.get('audio_bitrate', 128)   # kbps
        duration = content_metadata.get('duration', 60)             # seconds
        estimated_size = encoding_params.get('estimated_file_size_mb', 0)
        
        # Property 1: File size should be positive
        assert estimated_size > 0
        
        # Property 2: Mathematical relationship should hold
        # File size (MB) ≈ (video_bitrate + audio_bitrate) * duration / 8000
        total_bitrate = video_bitrate + audio_bitrate
        theoretical_size = (total_bitrate * duration) / 8000.0  # Convert to MB
        
        # Allow for container overhead (10-30%) and compression variations
        min_expected = theoretical_size * 0.8
        max_expected = theoretical_size * 1.5
        
        assert min_expected <= estimated_size <= max_expected, (
            f"File size {estimated_size}MB outside expected range "
            f"[{min_expected:.1f}, {max_expected:.1f}]MB for "
            f"{total_bitrate}kbps * {duration}s"
        )
        
        # Property 3: Longer content should generally mean larger files
        if duration > 300:  # 5 minutes
            assert estimated_size > 20  # Should be substantial
        
        if duration > 1800:  # 30 minutes
            assert estimated_size > 100  # Should be very substantial
    
    @given(
        content_metadata=variable_duration_content_strategy(),
        platform=st.sampled_from([
            SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK, 
            SocialPlatform.TWITTER  # Platforms with strict limits
        ])
    )
    @settings(max_examples=40, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_strict_platform_compliance_property(
        self, adapter, content_metadata, platform
    ):
        """
        Property: Strict platforms should enforce file size limits aggressively.
        
        Platforms with strict file size limits should optimize encoding
        parameters to stay within bounds when possible.
        """
        # Use settings that might produce large files
        base_settings = {
            'aspect_ratio': '16:9',
            'resolution': (1920, 1080),
            'color_grading': {'saturation': 1.8, 'contrast': 1.6, 'brightness': 1.2},
            'transitions': {'speed': 0.8}
        }
        
        # Run adaptation
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, [platform]
        ))
        
        adaptation = adaptations[platform]
        requirements = adapter.platform_requirements[platform]
        encoding_params = adaptation.encoding_params
        
        # Property 1: Bitrate should be constrained for strict platforms
        video_bitrate = encoding_params.get('video_bitrate', 0)
        
        # Strict platforms should use conservative bitrates
        if platform == SocialPlatform.INSTAGRAM:
            assert video_bitrate <= 6000  # Instagram's practical limit
        elif platform == SocialPlatform.TIKTOK:
            assert video_bitrate <= 8000  # TikTok's practical limit
        elif platform == SocialPlatform.TWITTER:
            assert video_bitrate <= 5000  # Twitter's practical limit
        
        # Property 2: File size estimation should consider platform limits
        estimated_size = encoding_params.get('estimated_file_size_mb', 0)
        duration = content_metadata.get('duration', 60)
        
        # If content is within duration limits, file size should be optimized
        if duration <= requirements.max_duration:
            # Should attempt to stay within reasonable bounds
            reasonable_limit = min(requirements.max_file_size, 500)  # Cap at 500MB
            
            # If estimated size is way over, bitrate should be reduced
            if estimated_size > reasonable_limit * 2:
                # Bitrate should be at the lower end of the range
                assert video_bitrate <= (requirements.bitrate_range[0] + requirements.bitrate_range[1]) / 2
        
        # Property 3: Compliance status should reflect actual constraints
        if estimated_size > requirements.max_file_size:
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
        
        if duration > requirements.max_duration:
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
    
    @given(
        base_settings=high_bitrate_settings_strategy(),
        short_duration=st.integers(min_value=5, max_value=60),
        long_duration=st.integers(min_value=300, max_value=1800)
    )
    @settings(max_examples=30, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_duration_impact_on_file_size_property(
        self, adapter, base_settings, short_duration, long_duration
    ):
        """
        Property: Duration should have predictable impact on file size.
        
        Longer content should result in proportionally larger file sizes,
        and this should be reflected in compliance status.
        """
        platform = SocialPlatform.INSTAGRAM  # Use consistent platform
        
        # Test short content
        short_content = {
            'title': 'Short Content',
            'duration': short_duration,
            'content_type': 'entertainment',
            'complexity_score': 0.5
        }
        
        # Test long content
        long_content = {
            'title': 'Long Content', 
            'duration': long_duration,
            'content_type': 'entertainment',
            'complexity_score': 0.5
        }
        
        # Run adaptations
        short_adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, short_content, [platform]
        ))
        
        long_adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, long_content, [platform]
        ))
        
        short_adaptation = short_adaptations[platform]
        long_adaptation = long_adaptations[platform]
        
        # Property 1: Longer content should have larger estimated file size
        short_size = short_adaptation.encoding_params.get('estimated_file_size_mb', 0)
        long_size = long_adaptation.encoding_params.get('estimated_file_size_mb', 0)
        
        assert long_size > short_size
        
        # Property 2: File size should scale roughly with duration
        duration_ratio = long_duration / short_duration
        size_ratio = long_size / short_size if short_size > 0 else float('inf')
        
        # Size ratio should be somewhat proportional to duration ratio
        # Allow for compression efficiency variations
        assert 0.5 * duration_ratio <= size_ratio <= 1.5 * duration_ratio
        
        # Property 3: Compliance should be worse for longer content
        requirements = adapter.platform_requirements[platform]
        
        if long_duration > requirements.max_duration:
            # Long content should have worse compliance
            compliance_order = ['compliant', 'minor_issues', 'major_issues', 'basic_compliance']
            
            short_compliance_idx = compliance_order.index(short_adaptation.compliance_status)
            long_compliance_idx = compliance_order.index(long_adaptation.compliance_status)
            
            assert long_compliance_idx >= short_compliance_idx
        
        # Property 4: Performance scores should reflect duration appropriateness
        if long_duration > requirements.max_duration:
            assert long_adaptation.estimated_performance_score <= short_adaptation.estimated_performance_score
    
    @given(
        content_metadata=variable_duration_content_strategy(),
        platforms=st.lists(
            st.sampled_from(list(SocialPlatform)),
            min_size=2,
            max_size=4,
            unique=True
        )
    )
    @settings(max_examples=25, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_cross_platform_file_size_consistency_property(
        self, adapter, content_metadata, platforms
    ):
        """
        Property: File size adaptations should be consistent across platforms.
        
        Similar platforms should produce similar file size estimates,
        while platforms with different constraints should show appropriate variations.
        """
        base_settings = {
            'aspect_ratio': '16:9',
            'resolution': (1920, 1080),
            'color_grading': {'saturation': 1.3, 'contrast': 1.2, 'brightness': 1.1},
            'transitions': {'speed': 1.0}
        }
        
        # Run adaptation for all platforms
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, content_metadata, platforms
        ))
        
        # Group platforms by file size constraints
        strict_platforms = [SocialPlatform.INSTAGRAM, SocialPlatform.TIKTOK, SocialPlatform.TWITTER]
        lenient_platforms = [SocialPlatform.YOUTUBE, SocialPlatform.LINKEDIN]
        
        strict_adaptations = {p: adaptations[p] for p in platforms if p in strict_platforms}
        lenient_adaptations = {p: adaptations[p] for p in platforms if p in lenient_platforms}
        
        # Property 1: Strict platforms should have more conservative bitrates
        if strict_adaptations and lenient_adaptations:
            strict_bitrates = [
                a.encoding_params.get('video_bitrate', 0) 
                for a in strict_adaptations.values()
            ]
            lenient_bitrates = [
                a.encoding_params.get('video_bitrate', 0) 
                for a in lenient_adaptations.values()
            ]
            
            avg_strict_bitrate = sum(strict_bitrates) / len(strict_bitrates)
            avg_lenient_bitrate = sum(lenient_bitrates) / len(lenient_bitrates)
            
            # Strict platforms should generally use lower bitrates
            assert avg_strict_bitrate <= avg_lenient_bitrate * 1.2
        
        # Property 2: File size estimates should correlate with platform limits
        for platform, adaptation in adaptations.items():
            requirements = adapter.platform_requirements[platform]
            estimated_size = adaptation.encoding_params.get('estimated_file_size_mb', 0)
            
            # Platforms with smaller limits should generally produce smaller estimates
            # (when duration is within limits)
            duration = content_metadata.get('duration', 60)
            if duration <= requirements.max_duration:
                # File size should be reasonable relative to platform limit
                if requirements.max_file_size < 1000:  # Strict platforms
                    assert estimated_size <= requirements.max_file_size * 2  # Allow some overage
        
        # Property 3: Compliance status should reflect platform constraints
        for platform, adaptation in adaptations.items():
            requirements = adapter.platform_requirements[platform]
            duration = content_metadata.get('duration', 60)
            estimated_size = adaptation.encoding_params.get('estimated_file_size_mb', 0)
            
            # Check if compliance status makes sense
            has_duration_issue = duration > requirements.max_duration
            has_size_issue = estimated_size > requirements.max_file_size
            
            if has_duration_issue or has_size_issue:
                assert adaptation.compliance_status in ['minor_issues', 'major_issues']
            else:
                # Should be compliant or have only minor issues
                assert adaptation.compliance_status in ['compliant', 'minor_issues']
    
    @given(
        extreme_duration=st.integers(min_value=1800, max_value=7200),  # 30 minutes to 2 hours
        platform=st.sampled_from(list(SocialPlatform))
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_extreme_content_handling_property(
        self, adapter, extreme_duration, platform
    ):
        """
        Property: Extreme content should be handled gracefully.
        
        Very long content should receive appropriate adaptations and
        clear compliance warnings.
        """
        base_settings = {
            'aspect_ratio': '16:9',
            'resolution': (1920, 1080),
            'color_grading': {'saturation': 1.0, 'contrast': 1.0, 'brightness': 1.0},
            'transitions': {'speed': 1.0}
        }
        
        extreme_content = {
            'title': 'Extreme Duration Content',
            'duration': extreme_duration,
            'content_type': 'educational',
            'complexity_score': 0.8
        }
        
        # Run adaptation
        adaptations = asyncio.run(adapter.adapt_for_platforms(
            base_settings, extreme_content, [platform]
        ))
        
        adaptation = adaptations[platform]
        requirements = adapter.platform_requirements[platform]
        
        # Property 1: Should handle extreme duration gracefully
        assert adaptation is not None
        assert isinstance(adaptation.estimated_performance_score, (int, float))
        assert 0.0 <= adaptation.estimated_performance_score <= 100.0
        
        # Property 2: Should flag duration issues for most platforms
        if extreme_duration > requirements.max_duration:
            assert adaptation.compliance_status in ['minor_issues', 'major_issues']
            
            # Performance score should be penalized
            assert adaptation.estimated_performance_score < 70.0
        
        # Property 3: File size should be estimated reasonably even for extreme content
        estimated_size = adaptation.encoding_params.get('estimated_file_size_mb', 0)
        assert estimated_size > 0
        
        # Very long content should have substantial file size
        if extreme_duration > 3600:  # 1 hour
            assert estimated_size > 500  # Should be very large
        
        # Property 4: Encoding parameters should be optimized for extreme content
        video_bitrate = adaptation.encoding_params.get('video_bitrate', 0)
        
        # Should use conservative bitrate for extreme duration
        assert requirements.bitrate_range[0] <= video_bitrate <= requirements.bitrate_range[1]
        
        # For very long content, should prefer lower bitrates
        if extreme_duration > 3600:
            midpoint_bitrate = (requirements.bitrate_range[0] + requirements.bitrate_range[1]) / 2
            assert video_bitrate <= midpoint_bitrate * 1.2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])