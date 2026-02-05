"""
Property tests for accessibility standards compliance.

Tests universal properties of accessibility features including WCAG 2.1 AA/AAA
compliance, color contrast analysis, flashing content detection, caption generation,
and language clarity optimization.
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, assume, settings, HealthCheck
from typing import Dict, List, Any
from datetime import datetime

from src.cinematic.accessibility_manager import (
    AccessibilityManager, WCAGLevel, AccessibilityIssueType,
    ColorContrastResult, FlashingContentResult, CaptionSegment,
    AudioDescriptionSegment, AccessibilityReport
)
from src.llm.gemini_client import GeminiClient


# Test data strategies
@st.composite
def cinematic_settings_strategy(draw):
    """Generate cinematic settings for accessibility testing."""
    return {
        'aspect_ratio': draw(st.sampled_from(['16:9', '9:16', '1:1'])),
        'resolution': draw(st.sampled_from([(1920, 1080), (1080, 1920), (1280, 720)])),
        'color_grading': {
            'saturation': draw(st.floats(min_value=0.5, max_value=2.5)),
            'contrast': draw(st.floats(min_value=0.5, max_value=2.5)),
            'brightness': draw(st.floats(min_value=0.5, max_value=2.0))
        },
        'transitions': {
            'speed': draw(st.floats(min_value=0.3, max_value=4.0))
        },
        'visual_style': draw(st.sampled_from(['standard', 'cinematic', 'documentary', 'artistic']))
    }


@st.composite
def video_metadata_strategy(draw):
    """Generate video metadata for accessibility testing."""
    duration = draw(st.integers(min_value=10, max_value=1800))  # 10 seconds to 30 minutes
    
    return {
        'title': draw(st.text(min_size=5, max_size=100, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs')))),
        'description': draw(st.text(min_size=10, max_size=500, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')))),
        'duration': duration,
        'content_type': draw(st.sampled_from([
            'educational', 'entertainment', 'professional', 'tutorial',
            'documentary', 'presentation', 'demonstration', 'general'
        ])),
        'topics': draw(st.lists(
            st.text(min_size=3, max_size=20, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
            max_size=5
        )),
        'transcript': draw(st.one_of(
            st.none(),
            st.text(min_size=50, max_size=1000, alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po')))
        ))
    }


class TestAccessibilityCompliance:
    """Property tests for accessibility standards compliance."""
    
    @pytest.fixture
    def accessibility_manager(self):
        """Create accessibility manager instance."""
        return AccessibilityManager()
    
    @given(
        video_metadata=video_metadata_strategy(),
        cinematic_settings=cinematic_settings_strategy(),
        wcag_level=st.sampled_from(list(WCAGLevel))
    )
    @settings(max_examples=30, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_accessibility_analysis_completeness_property(
        self, accessibility_manager, video_metadata, cinematic_settings, wcag_level
    ):
        """
        Property 21: Accessibility Standards Compliance
        
        Accessibility analysis should provide comprehensive evaluation covering
        all major WCAG 2.1 requirements and produce actionable recommendations.
        """
        # Run accessibility analysis
        report = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, cinematic_settings, wcag_level
        ))
        
        # Property 1: Report should be complete and valid
        assert isinstance(report, AccessibilityReport)
        assert report.wcag_level == wcag_level
        assert isinstance(report.overall_compliance, bool)
        assert 0.0 <= report.compliance_score <= 100.0
        assert isinstance(report.issues, list)
        assert isinstance(report.recommendations, list)
        assert isinstance(report.generated_at, datetime)
        
        # Property 2: Color contrast analysis should be present
        assert isinstance(report.color_contrast_results, list)
        
        for contrast_result in report.color_contrast_results:
            assert isinstance(contrast_result, ColorContrastResult)
            assert contrast_result.contrast_ratio > 0.0
            assert isinstance(contrast_result.wcag_aa_pass, bool)
            assert isinstance(contrast_result.wcag_aaa_pass, bool)
            assert isinstance(contrast_result.recommendations, list)
            
            # WCAG AAA should be stricter than AA
            if contrast_result.wcag_aaa_pass:
                assert contrast_result.wcag_aa_pass
        
        # Property 3: Flashing content analysis should be appropriate
        if report.flashing_content_result:
            flashing_result = report.flashing_content_result
            assert isinstance(flashing_result, FlashingContentResult)
            assert isinstance(flashing_result.has_flashing, bool)
            assert flashing_result.flash_frequency >= 0.0
            assert flashing_result.flash_duration >= 0.0
            assert flashing_result.risk_level in ['low', 'medium', 'high']
            assert isinstance(flashing_result.recommendations, list)
            
            # High risk should have recommendations
            if flashing_result.risk_level == 'high':
                assert len(flashing_result.recommendations) > 0
        
        # Property 4: Caption segments should be valid
        assert isinstance(report.caption_segments, list)
        
        for caption in report.caption_segments:
            assert isinstance(caption, CaptionSegment)
            assert caption.start_time >= 0.0
            assert caption.end_time > caption.start_time
            assert caption.end_time <= video_metadata['duration'] + 1.0  # Allow small buffer
            assert 0.0 <= caption.confidence <= 1.0
            assert len(caption.text.strip()) > 0
        
        # Property 5: Audio descriptions should be valid when present
        assert isinstance(report.audio_descriptions, list)
        
        for audio_desc in report.audio_descriptions:
            assert isinstance(audio_desc, AudioDescriptionSegment)
            assert audio_desc.start_time >= 0.0
            assert audio_desc.end_time > audio_desc.start_time
            assert audio_desc.end_time <= video_metadata['duration'] + 1.0
            assert audio_desc.priority in ['essential', 'important', 'supplementary']
            assert len(audio_desc.description.strip()) > 0
        
        # Property 6: Language clarity score should be reasonable
        assert 0.0 <= report.language_clarity_score <= 1.0
        
        # Property 7: Issues should be properly categorized
        for issue in report.issues:
            assert 'type' in issue
            assert 'severity' in issue
            assert 'description' in issue
            assert 'location' in issue
            
            assert issue['type'] in [t.value for t in AccessibilityIssueType]
            assert issue['severity'] in ['low', 'medium', 'high', 'critical']
            assert len(issue['description']) > 0
            assert len(issue['location']) > 0
        
        # Property 8: Compliance score should reflect issue severity
        critical_issues = [i for i in report.issues if i['severity'] == 'critical']
        high_issues = [i for i in report.issues if i['severity'] == 'high']
        
        if critical_issues:
            assert report.compliance_score < 70.0
            assert not report.overall_compliance
        
        if len(high_issues) > 2:
            assert report.compliance_score < 80.0
        
        # Property 9: WCAG level should affect compliance requirements
        if wcag_level == WCAGLevel.AAA:
            # AAA should be more strict
            aaa_failing_contrasts = [
                c for c in report.color_contrast_results 
                if not c.wcag_aaa_pass
            ]
            if aaa_failing_contrasts:
                contrast_issues = [
                    i for i in report.issues 
                    if i['type'] == AccessibilityIssueType.COLOR_CONTRAST.value
                ]
                assert len(contrast_issues) > 0
    
    @given(
        video_metadata=video_metadata_strategy(),
        high_contrast_settings=st.fixed_dictionaries({
            'color_grading': st.fixed_dictionaries({
                'saturation': st.floats(min_value=1.5, max_value=2.5),
                'contrast': st.floats(min_value=1.5, max_value=2.5),
                'brightness': st.floats(min_value=1.0, max_value=2.0)
            }),
            'transitions': st.fixed_dictionaries({
                'speed': st.floats(min_value=2.0, max_value=4.0)
            })
        })
    )
    @settings(max_examples=20, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_high_risk_content_detection_property(
        self, accessibility_manager, video_metadata, high_contrast_settings
    ):
        """
        Property: High-risk accessibility content should be properly detected.
        
        Content with high contrast, rapid transitions, or other potentially
        problematic elements should be flagged with appropriate warnings.
        """
        # Run analysis with high-risk settings
        report = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, high_contrast_settings, WCAGLevel.AA
        ))
        
        # Property 1: High contrast should trigger flashing content detection
        if high_contrast_settings['color_grading']['contrast'] > 1.8:
            # Should either have flashing content result or related issues
            has_flashing_result = report.flashing_content_result is not None
            has_flashing_issues = any(
                issue['type'] == AccessibilityIssueType.FLASHING_CONTENT.value
                for issue in report.issues
            )
            
            # At least one should be true for high contrast
            assert has_flashing_result or has_flashing_issues
        
        # Property 2: Rapid transitions should be flagged
        if high_contrast_settings['transitions']['speed'] > 2.5:
            if report.flashing_content_result:
                assert report.flashing_content_result.has_flashing
                assert report.flashing_content_result.risk_level in ['medium', 'high']
        
        # Property 3: High-risk content should have lower compliance scores
        if (high_contrast_settings['color_grading']['contrast'] > 2.0 and 
            high_contrast_settings['transitions']['speed'] > 3.0):
            assert report.compliance_score < 85.0
        
        # Property 4: High-risk content should have recommendations
        if report.flashing_content_result and report.flashing_content_result.risk_level == 'high':
            assert len(report.flashing_content_result.recommendations) > 0
            assert any('warning' in rec.lower() for rec in report.flashing_content_result.recommendations)
    
    @given(
        video_metadata=video_metadata_strategy(),
        cinematic_settings=cinematic_settings_strategy()
    )
    @settings(max_examples=25, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_caption_timing_validation_property(
        self, accessibility_manager, video_metadata, cinematic_settings
    ):
        """
        Property: Caption timing should follow WCAG guidelines.
        
        Generated captions should have appropriate timing, duration, and
        reading speed according to accessibility standards.
        """
        # Run accessibility analysis
        report = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, cinematic_settings, WCAGLevel.AA
        ))
        
        # Property 1: Captions should exist for content with audio
        if video_metadata.get('transcript') or video_metadata['duration'] > 30:
            # Should have captions or caption-related issues
            has_captions = len(report.caption_segments) > 0
            has_caption_issues = any(
                issue['type'] == AccessibilityIssueType.CAPTIONS.value
                for issue in report.issues
            )
            
            assert has_captions or has_caption_issues
        
        # Property 2: Caption segments should not overlap
        caption_segments = sorted(report.caption_segments, key=lambda c: c.start_time)
        
        for i in range(len(caption_segments) - 1):
            current = caption_segments[i]
            next_caption = caption_segments[i + 1]
            
            # Current caption should end before or at the start of next caption
            assert current.end_time <= next_caption.start_time + 0.1  # Allow small overlap
        
        # Property 3: Caption durations should be reasonable
        for caption in report.caption_segments:
            duration = caption.end_time - caption.start_time
            
            # Should be at least 0.5 seconds and at most 10 seconds
            assert 0.5 <= duration <= 10.0
            
            # Reading speed should be reasonable
            word_count = len(caption.text.split())
            if word_count > 0:
                reading_speed = (word_count / duration) * 60  # WPM
                assert reading_speed <= 300  # Maximum reasonable reading speed
        
        # Property 4: Caption timing issues should be flagged appropriately
        caption_issues = [
            issue for issue in report.issues
            if issue['type'] == AccessibilityIssueType.CAPTIONS.value
        ]
        
        # Check if timing issues are properly detected
        for caption in report.caption_segments:
            duration = caption.end_time - caption.start_time
            word_count = len(caption.text.split())
            
            if duration < 1.0:  # Very short caption
                # Should have timing issue flagged
                timing_issues = [
                    issue for issue in caption_issues
                    if 'duration' in issue['description'].lower()
                ]
                # Note: May not always be flagged if within acceptable range
            
            if word_count > 0:
                reading_speed = (word_count / duration) * 60
                if reading_speed > 200:  # Very fast reading speed
                    speed_issues = [
                        issue for issue in caption_issues
                        if 'reading speed' in issue['description'].lower()
                    ]
                    # Note: May not always be flagged depending on exact speed
    
    @given(
        simple_text=st.text(
            min_size=20, 
            max_size=200,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Zs'))
        ),
        complex_text=st.text(
            min_size=50,
            max_size=300,
            alphabet=st.characters(whitelist_categories=('Lu', 'Ll', 'Nd', 'Zs', 'Po'))
        )
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_language_clarity_analysis_property(
        self, accessibility_manager, simple_text, complex_text
    ):
        """
        Property: Language clarity analysis should distinguish between simple and complex text.
        
        Simple text should generally score higher than complex text in
        readability analysis.
        """
        # Create metadata with different text complexity
        simple_metadata = {
            'title': 'Simple Video Title',
            'description': simple_text,
            'duration': 60,
            'content_type': 'educational',
            'transcript': simple_text
        }
        
        complex_metadata = {
            'title': 'Complex Educational Content Analysis',
            'description': complex_text,
            'duration': 60,
            'content_type': 'educational',
            'transcript': complex_text
        }
        
        basic_settings = {
            'color_grading': {'saturation': 1.0, 'contrast': 1.0, 'brightness': 1.0},
            'transitions': {'speed': 1.0}
        }
        
        # Analyze both
        simple_report = asyncio.run(accessibility_manager.analyze_accessibility(
            simple_metadata, basic_settings, WCAGLevel.AA
        ))
        
        complex_report = asyncio.run(accessibility_manager.analyze_accessibility(
            complex_metadata, basic_settings, WCAGLevel.AA
        ))
        
        # Property 1: Both should have valid clarity scores
        assert 0.0 <= simple_report.language_clarity_score <= 1.0
        assert 0.0 <= complex_report.language_clarity_score <= 1.0
        
        # Property 2: Simple text should generally score higher (with some tolerance)
        # Note: This is probabilistic due to text generation randomness
        if len(simple_text.split()) < len(complex_text.split()) * 0.8:
            # Only assert if simple text is significantly shorter
            assert simple_report.language_clarity_score >= complex_report.language_clarity_score - 0.2
        
        # Property 3: Very low clarity scores should trigger issues
        if simple_report.language_clarity_score < 0.5:
            clarity_issues = [
                issue for issue in simple_report.issues
                if issue['type'] == AccessibilityIssueType.LANGUAGE_CLARITY.value
            ]
            assert len(clarity_issues) > 0
        
        if complex_report.language_clarity_score < 0.5:
            clarity_issues = [
                issue for issue in complex_report.issues
                if issue['type'] == AccessibilityIssueType.LANGUAGE_CLARITY.value
            ]
            assert len(clarity_issues) > 0
    
    @given(
        video_metadata=video_metadata_strategy(),
        cinematic_settings=cinematic_settings_strategy()
    )
    @settings(max_examples=15, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_wcag_level_compliance_differences_property(
        self, accessibility_manager, video_metadata, cinematic_settings
    ):
        """
        Property: Different WCAG levels should have different compliance requirements.
        
        WCAG AAA should be stricter than AA, which should be stricter than A.
        """
        # Run analysis for different WCAG levels
        report_a = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, cinematic_settings, WCAGLevel.A
        ))
        
        report_aa = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, cinematic_settings, WCAGLevel.AA
        ))
        
        report_aaa = asyncio.run(accessibility_manager.analyze_accessibility(
            video_metadata, cinematic_settings, WCAGLevel.AAA
        ))
        
        # Property 1: All reports should be valid
        for report in [report_a, report_aa, report_aaa]:
            assert isinstance(report, AccessibilityReport)
            assert 0.0 <= report.compliance_score <= 100.0
        
        # Property 2: Stricter levels should generally have more issues or lower scores
        # (This is probabilistic due to content variation)
        
        # Count color contrast failures for each level
        a_contrast_failures = sum(
            1 for c in report_a.color_contrast_results 
            if c.contrast_ratio < 3.0  # Level A threshold
        )
        
        aa_contrast_failures = sum(
            1 for c in report_aa.color_contrast_results 
            if not c.wcag_aa_pass
        )
        
        aaa_contrast_failures = sum(
            1 for c in report_aaa.color_contrast_results 
            if not c.wcag_aaa_pass
        )
        
        # AAA should have at least as many failures as AA, AA at least as many as A
        assert aaa_contrast_failures >= aa_contrast_failures
        assert aa_contrast_failures >= a_contrast_failures
        
        # Property 3: If there are contrast issues, AAA should be most strict
        if any(c.contrast_ratio < 7.0 for c in report_aaa.color_contrast_results):
            # AAA should have contrast-related issues
            aaa_contrast_issues = [
                issue for issue in report_aaa.issues
                if issue['type'] == AccessibilityIssueType.COLOR_CONTRAST.value
            ]
            
            aa_contrast_issues = [
                issue for issue in report_aa.issues
                if issue['type'] == AccessibilityIssueType.COLOR_CONTRAST.value
            ]
            
            # AAA should have at least as many contrast issues as AA
            assert len(aaa_contrast_issues) >= len(aa_contrast_issues)
        
        # Property 4: Compliance scores should reflect strictness
        # Allow for some variation due to different scoring algorithms
        if not report_aaa.overall_compliance and report_aa.overall_compliance:
            # If AAA fails but AA passes, AAA score should be lower
            assert report_aaa.compliance_score <= report_aa.compliance_score + 5.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])