"""
Property tests for YouTube optimization features.

Tests Property 19: YouTube Optimization Compliance
Tests Property 22: SEO Metadata Generation Quality
"""

import pytest
import asyncio
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from hypothesis.stateful import RuleBasedStateMachine, rule, initialize, invariant
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock
import json

from src.cinematic.youtube_optimizer import (
    YouTubeOptimizer,
    YouTubeOptimizationSettings,
    YouTubeContentType,
    YouTubeAspectRatio,
    YouTubeEncodingParams,
    SEOMetadata,
    ThumbnailSuggestion,
    ChapterMarker
)
from src.llm.gemini_client import GeminiClient


# Test data generators
@st.composite
def youtube_content_type(draw):
    """Generate valid YouTube content types."""
    return draw(st.sampled_from(list(YouTubeContentType)))


@st.composite
def youtube_aspect_ratio(draw):
    """Generate valid YouTube aspect ratios."""
    return draw(st.sampled_from(list(YouTubeAspectRatio)))


@st.composite
def youtube_optimization_settings(draw):
    """Generate valid YouTube optimization settings."""
    return YouTubeOptimizationSettings(
        content_type=draw(youtube_content_type()),
        target_audience=draw(st.sampled_from(['general', 'technical', 'academic'])),
        aspect_ratio=draw(youtube_aspect_ratio()),
        target_duration_range=(
            draw(st.integers(min_value=60, max_value=300)),
            draw(st.integers(min_value=600, max_value=1800))
        ),
        enable_shorts_optimization=draw(st.booleans()),
        enable_thumbnail_generation=draw(st.booleans()),
        enable_seo_optimization=draw(st.booleans()),
        enable_chapter_markers=draw(st.booleans()),
        enable_intro_outro=draw(st.booleans()),
        branding_elements=draw(st.booleans())
    )


@st.composite
def content_metadata(draw):
    """Generate valid content metadata."""
    title_words = draw(st.lists(
        st.text(min_size=1, max_size=10, alphabet=st.characters(whitelist_categories=('Lu', 'Ll'))),
        min_size=2,
        max_size=8
    ))
    
    return {
        'title': ' '.join(title_words),
        'description': draw(st.text(min_size=10, max_size=500)),
        'duration': draw(st.integers(min_value=60, max_value=3600)),
        'content_type': draw(st.sampled_from(['educational', 'tutorial', 'review', 'entertainment'])),
        'language': 'en'
    }


@st.composite
def cinematic_settings(draw):
    """Generate valid cinematic settings."""
    return {
        'camera_movements': {
            'enabled': draw(st.booleans()),
            'allowed_types': draw(st.lists(
                st.sampled_from(['static', 'pan', 'zoom', 'dolly', 'crane', 'handheld']),
                min_size=1,
                max_size=6,
                unique=True
            )),
            'intensity': draw(st.integers(min_value=0, max_value=100)),
            'auto_select': draw(st.booleans())
        },
        'color_grading': {
            'enabled': draw(st.booleans()),
            'film_emulation': draw(st.sampled_from(['none', 'kodak', 'fuji', 'cinema'])),
            'temperature': draw(st.integers(min_value=-100, max_value=100)),
            'contrast': draw(st.integers(min_value=-100, max_value=100)),
            'saturation': draw(st.integers(min_value=-100, max_value=100))
        },
        'sound_design': {
            'enabled': draw(st.booleans()),
            'ambient_audio': draw(st.booleans()),
            'music_scoring': draw(st.booleans()),
            'spatial_audio': draw(st.booleans())
        },
        'quality_preset': draw(st.sampled_from(['standard_hd', 'cinematic_4k', 'cinematic_8k']))
    }


class TestYouTubeOptimization:
    """Property tests for YouTube optimization features."""
    
    @pytest.fixture
    def mock_gemini_client(self):
        """Create mock Gemini client for testing."""
        client = AsyncMock(spec=GeminiClient)
        
        # Mock SEO response
        seo_response = json.dumps({
            "optimized_title": "Learn Advanced Mathematics - Complete Guide for Beginners",
            "optimized_description": "Master advanced mathematical concepts with this comprehensive guide. Perfect for students and professionals looking to enhance their skills.",
            "tags": ["mathematics", "education", "tutorial", "learning", "guide", "advanced", "concepts"],
            "category": "Education",
            "keywords": ["mathematics", "advanced math", "tutorial"],
            "hook_suggestions": ["Ready to master advanced math?", "Let's explore complex mathematical concepts"],
            "cta_suggestions": ["Subscribe for more math tutorials!", "Like if this helped you learn!"]
        })
        
        client.generate_content.return_value = seo_response
        return client
    
    @given(
        optimization_settings=youtube_optimization_settings(),
        content_meta=content_metadata(),
        cinematic_set=cinematic_settings()
    )
    @settings(max_examples=50, deadline=5000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_19_youtube_optimization_compliance(self, optimization_settings, content_meta, cinematic_set):
        """
        Property 19: YouTube Optimization Compliance
        
        For any content type and target audience, YouTube optimization should produce 
        settings that comply with YouTube's technical requirements and best practices.
        
        Validates: Requirements 9.1, 9.2, 9.5
        """
        async def run_test():
            # Create YouTube optimizer
            mock_gemini = AsyncMock(spec=GeminiClient)
            mock_gemini.generate_content.return_value = json.dumps({
                "optimized_title": "Test Video Title",
                "optimized_description": "Test video description with relevant content",
                "tags": ["test", "video", "content"],
                "category": "Education"
            })
            
            optimizer = YouTubeOptimizer(gemini_client=mock_gemini)
            
            # Perform optimization
            result = await optimizer.optimize_for_youtube(
                content_meta, cinematic_set, optimization_settings
            )
            
            # Property assertions for compliance
            assert isinstance(result, dict)
            assert 'encoding_params' in result
            assert 'seo_metadata' in result
            assert 'optimization_summary' in result
            
            # Verify encoding parameters compliance
            encoding_params = result['encoding_params']
            assert encoding_params['video_codec'] == 'H.264'
            assert encoding_params['audio_codec'] == 'AAC'
            assert encoding_params['pixel_format'] == 'yuv420p'
            
            # Verify video bitrate is reasonable
            bitrate_str = encoding_params['video_bitrate']
            assert bitrate_str.endswith('k')
            bitrate_value = int(bitrate_str[:-1])
            assert 1000 <= bitrate_value <= 50000  # Reasonable range
            
            # Verify audio bitrate is reasonable
            audio_bitrate_str = encoding_params['audio_bitrate']
            assert audio_bitrate_str.endswith('k')
            audio_bitrate_value = int(audio_bitrate_str[:-1])
            assert 64 <= audio_bitrate_value <= 320  # Standard audio bitrates
            
            # Verify frame rate is valid
            frame_rate = encoding_params['frame_rate']
            assert isinstance(frame_rate, (int, float))
            assert 24.0 <= frame_rate <= 60.0
            
            # Verify resolution is valid
            resolution = encoding_params['resolution']
            assert isinstance(resolution, (list, tuple))
            assert len(resolution) == 2
            width, height = resolution
            assert isinstance(width, int) and isinstance(height, int)
            assert width > 0 and height > 0
            assert width >= 640 and height >= 360  # Minimum YouTube resolution
            
            # Verify SEO metadata compliance
            seo_metadata = result['seo_metadata']
            assert isinstance(seo_metadata['title'], str)
            assert len(seo_metadata['title']) <= 100  # YouTube title limit
            assert len(seo_metadata['title']) > 0
            
            assert isinstance(seo_metadata['description'], str)
            assert len(seo_metadata['description']) <= 5000  # YouTube description limit
            
            assert isinstance(seo_metadata['tags'], list)
            assert len(seo_metadata['tags']) <= 15  # YouTube tags limit
            
            # Verify all tags are strings
            for tag in seo_metadata['tags']:
                assert isinstance(tag, str)
                assert len(tag) > 0
            
            # Verify compliance status
            compliance_status = result['optimization_summary']['compliance_status']
            assert isinstance(compliance_status, dict)
            assert 'overall_status' in compliance_status
            assert compliance_status['overall_status'] in ['compliant', 'compliant_with_warnings', 'non_compliant', 'basic_compliant']
            
            # Verify performance score is reasonable
            performance_score = result['optimization_summary']['estimated_performance_score']
            assert isinstance(performance_score, (int, float))
            assert 0.0 <= performance_score <= 100.0
            
            # Verify aspect ratio compliance
            if optimization_settings.aspect_ratio == YouTubeAspectRatio.LANDSCAPE:
                assert width >= height  # Landscape should be wider than tall
            elif optimization_settings.aspect_ratio == YouTubeAspectRatio.VERTICAL:
                assert height > width  # Vertical should be taller than wide
            elif optimization_settings.aspect_ratio == YouTubeAspectRatio.SQUARE:
                # Square should have similar dimensions (allowing small variance)
                ratio = width / height
                assert 0.9 <= ratio <= 1.1
        
        # Run the async test
        import asyncio
        asyncio.run(run_test())
    
    @given(
        content_meta=content_metadata(),
        optimization_settings=youtube_optimization_settings()
    )
    @settings(max_examples=30, deadline=3000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_property_22_seo_metadata_generation_quality(self, content_meta, optimization_settings):
        """
        Property 22: SEO Metadata Generation Quality
        
        For any video content analysis, generated SEO metadata (titles, descriptions, tags) 
        should be relevant, engaging, and optimized for search discovery.
        
        Validates: Requirements 9.6
        """
        async def run_test():
            # Create YouTube optimizer with mock Gemini
            mock_gemini = AsyncMock(spec=GeminiClient)
            
            # Create realistic SEO response based on content
            content_title = content_meta['title']
            main_topic = content_title.split()[0] if content_title else "topic"
            
            seo_response = json.dumps({
                "optimized_title": f"Learn {main_topic} - Complete Guide for {optimization_settings.target_audience.title()}",
                "optimized_description": f"Master {main_topic} with this comprehensive guide. Perfect for {optimization_settings.target_audience} learners. Includes examples, explanations, and practical applications.",
                "tags": [main_topic.lower(), "education", "tutorial", "guide", optimization_settings.target_audience, "learning"],
                "category": "Education",
                "keywords": [main_topic.lower(), "tutorial", "guide"],
                "hook_suggestions": [f"Ready to learn {main_topic}?"],
                "cta_suggestions": ["Subscribe for more tutorials!"]
            })
            
            mock_gemini.generate_content.return_value = seo_response
            optimizer = YouTubeOptimizer(gemini_client=mock_gemini)
            
            # Generate SEO metadata
            result = await optimizer.optimize_for_youtube(
                content_meta, {}, optimization_settings
            )
            
            seo_metadata = result['seo_metadata']
            
            # Property assertions for SEO quality
            
            # Title quality checks
            title = seo_metadata['title']
            assert isinstance(title, str)
            assert len(title) > 0
            assert len(title) <= 100  # YouTube limit
            
            # Title should be engaging (not just the original title)
            original_title = content_meta['title']
            if len(original_title) > 10:  # Only check if original title is substantial
                # Should either be different or enhanced
                title_similarity = len(set(title.lower().split()) & set(original_title.lower().split()))
                total_words = len(set(title.lower().split()) | set(original_title.lower().split()))
                similarity_ratio = title_similarity / max(total_words, 1)
                # Should have some similarity but also enhancement
                assert similarity_ratio < 1.0 or len(title) > len(original_title)
            
            # Description quality checks
            description = seo_metadata['description']
            assert isinstance(description, str)
            assert len(description) > 0
            assert len(description) <= 5000  # YouTube limit
            
            # Description should be substantial for SEO
            if optimization_settings.enable_seo_optimization:
                assert len(description) >= 50  # Minimum for good SEO
            
            # Tags quality checks
            tags = seo_metadata['tags']
            assert isinstance(tags, list)
            assert len(tags) > 0
            assert len(tags) <= 15  # YouTube limit
            
            # All tags should be valid strings
            for tag in tags:
                assert isinstance(tag, str)
                assert len(tag) > 0
                assert len(tag) <= 50  # Reasonable tag length
                # Tags should not contain special characters that break YouTube
                assert not any(char in tag for char in ['<', '>', '"', "'", '&'])
            
            # Tags should be relevant to content
            content_words = set(content_meta['title'].lower().split())
            tag_words = set(' '.join(tags).lower().split())
            
            if content_words:  # Only check if we have content words
                # At least some overlap between content and tags
                overlap = len(content_words & tag_words)
                assert overlap > 0 or len(tags) >= 3  # Either relevant or sufficient quantity
            
            # Category should be appropriate
            category = seo_metadata['category']
            assert isinstance(category, str)
            assert len(category) > 0
            
            # Verify content type alignment
            if optimization_settings.content_type == YouTubeContentType.EDUCATIONAL:
                # Educational content should have educational indicators
                educational_indicators = ['learn', 'guide', 'tutorial', 'education', 'explain', 'how']
                title_lower = title.lower()
                desc_lower = description.lower()
                tags_lower = ' '.join(tags).lower()
                
                combined_text = f"{title_lower} {desc_lower} {tags_lower}"
                has_educational_indicators = any(indicator in combined_text for indicator in educational_indicators)
                assert has_educational_indicators
            
            # Verify target audience alignment
            if optimization_settings.target_audience in ['technical', 'academic']:
                # Should have appropriate complexity indicators
                complexity_indicators = ['advanced', 'detailed', 'comprehensive', 'in-depth', 'professional']
                combined_text = f"{title.lower()} {description.lower()}"
                # Either has complexity indicators or is appropriately detailed
                has_complexity = any(indicator in combined_text for indicator in complexity_indicators)
                is_detailed = len(description) > 200
                assert has_complexity or is_detailed
        
        # Run the async test
        import asyncio
        asyncio.run(run_test())
    
    @given(
        content_type=youtube_content_type(),
        quality=st.sampled_from(['720p', '1080p', '4k', '8k'])
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_encoding_params_generation(self, content_type, quality):
        """Test encoding parameters generation for different content types and qualities."""
        
        # Generate encoding params
        encoding_params = YouTubeEncodingParams.from_content_type(content_type, quality)
        
        # Verify basic structure
        assert isinstance(encoding_params, YouTubeEncodingParams)
        assert encoding_params.video_codec == "H.264"
        assert encoding_params.audio_codec == "AAC"
        assert encoding_params.pixel_format == "yuv420p"
        
        # Verify resolution matches quality
        width, height = encoding_params.resolution
        if quality == "8k":
            assert width == 7680 and height == 4320
        elif quality == "4k":
            assert width == 3840 and height == 2160
        elif quality == "1080p":
            assert width == 1920 and height == 1080
        else:  # 720p
            assert width == 1280 and height == 720
        
        # Verify bitrate is reasonable for quality
        bitrate_value = int(encoding_params.video_bitrate.rstrip('k'))
        if quality == "8k":
            assert bitrate_value >= 30000
        elif quality == "4k":
            assert bitrate_value >= 10000
        elif quality == "1080p":
            assert bitrate_value >= 5000
        else:  # 720p
            assert bitrate_value >= 2000
        
        # Verify content type specific adjustments
        if content_type == YouTubeContentType.GAMING:
            assert encoding_params.frame_rate == 60.0
        elif content_type == YouTubeContentType.MUSIC:
            assert encoding_params.audio_bitrate == "320k"
    
    @given(
        duration=st.integers(min_value=60, max_value=3600),
        content_type=youtube_content_type()
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_chapter_markers_generation(self, duration, content_type):
        """Test chapter markers generation for different durations and content types."""
        
        async def run_test():
            optimizer = YouTubeOptimizer()
            
            content_metadata = {
                'title': 'Test Video',
                'description': 'Test description',
                'duration': duration
            }
            
            optimization_settings = YouTubeOptimizationSettings(
                content_type=content_type,
                enable_chapter_markers=True
            )
            
            chapter_markers = await optimizer._generate_chapter_markers(
                content_metadata, optimization_settings
            )
            
            # Verify basic structure
            assert isinstance(chapter_markers, list)
            
            if duration >= 180:  # Only expect chapters for longer videos
                assert len(chapter_markers) >= 2  # At least intro and one content chapter
                
                # Verify first marker is always intro at 0:00
                first_marker = chapter_markers[0]
                assert first_marker.timestamp == 0.0
                assert first_marker.category == "intro"
                
                # Verify markers are in chronological order
                timestamps = [marker.timestamp for marker in chapter_markers]
                assert timestamps == sorted(timestamps)
                
                # Verify all timestamps are within video duration
                for marker in chapter_markers:
                    assert 0.0 <= marker.timestamp <= duration
                    assert isinstance(marker.title, str)
                    assert len(marker.title) > 0
                    assert isinstance(marker.description, str)
                    assert marker.category in ['intro', 'content', 'outro', 'transition']
                
                # Verify educational content has appropriate structure
                if content_type == YouTubeContentType.EDUCATIONAL and duration > 300:
                    marker_titles = [m.title.lower() for m in chapter_markers]
                    # Should have structured educational content
                    educational_terms = ['introduction', 'concept', 'example', 'summary', 'conclusion']
                    has_educational_structure = any(
                        any(term in title for term in educational_terms)
                        for title in marker_titles
                    )
                    assert has_educational_structure
        
        # Run the async test
        import asyncio
        asyncio.run(run_test())
    
    def test_youtube_format_conversion(self):
        """Test conversion to YouTube-specific formats."""
        
        # Test chapter marker YouTube format
        marker = ChapterMarker(
            timestamp=125.5,  # 2:05.5
            title="Main Concept",
            description="Explaining the main concept"
        )
        
        youtube_format = marker.to_youtube_format()
        assert youtube_format == "02:05 Main Concept"
        
        # Test with different timestamps
        marker2 = ChapterMarker(timestamp=3661.0, title="Advanced Topics", description="")  # 1:01:01
        youtube_format2 = marker2.to_youtube_format()
        assert youtube_format2 == "61:01 Advanced Topics"  # YouTube uses MM:SS format
    
    @given(
        title=st.text(min_size=5, max_size=200),
        description=st.text(min_size=10, max_size=1000)
    )
    @settings(max_examples=20, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_seo_metadata_validation(self, title, description):
        """Test SEO metadata validation and limits."""
        
        # Create SEO metadata
        seo_metadata = SEOMetadata(
            title=title,
            description=description,
            tags=['test', 'video', 'content']
        )
        
        # Convert to dict and verify structure
        seo_dict = seo_metadata.to_dict()
        
        assert isinstance(seo_dict, dict)
        assert 'title' in seo_dict
        assert 'description' in seo_dict
        assert 'tags' in seo_dict
        assert 'category' in seo_dict
        assert 'language' in seo_dict
        
        # Verify data types
        assert isinstance(seo_dict['title'], str)
        assert isinstance(seo_dict['description'], str)
        assert isinstance(seo_dict['tags'], list)
        assert isinstance(seo_dict['category'], str)
        assert isinstance(seo_dict['language'], str)
        
        # Verify lists are properly structured
        assert isinstance(seo_dict['thumbnail_suggestions'], list)
        assert isinstance(seo_dict['chapter_markers'], list)


class YouTubeOptimizerStateMachine(RuleBasedStateMachine):
    """Stateful testing for YouTube optimizer operations."""
    
    def __init__(self):
        super().__init__()
        self.optimizer = YouTubeOptimizer()
        self.generated_metadata = {}
        self.encoding_params = {}
    
    @rule(
        content_type=st.sampled_from(list(YouTubeContentType)),
        quality=st.sampled_from(['720p', '1080p', '4k'])
    )
    def generate_encoding_params(self, content_type, quality):
        """Generate encoding parameters."""
        params = YouTubeEncodingParams.from_content_type(content_type, quality)
        
        key = f"{content_type.value}_{quality}"
        self.encoding_params[key] = params
        
        # Verify consistency
        assert params.video_codec == "H.264"
        assert params.audio_codec == "AAC"
        assert params.pixel_format == "yuv420p"
    
    @rule(
        title=st.text(min_size=5, max_size=100),
        tags=st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10)
    )
    def create_seo_metadata(self, title, tags):
        """Create SEO metadata."""
        metadata = SEOMetadata(
            title=title,
            description=f"Description for {title}",
            tags=tags
        )
        
        self.generated_metadata[title] = metadata
        
        # Verify metadata structure
        assert len(metadata.title) <= 100
        assert len(metadata.tags) <= 15
        assert isinstance(metadata.to_dict(), dict)
    
    @invariant()
    def encoding_params_consistency(self):
        """Invariant: All encoding params should maintain YouTube compliance."""
        for key, params in self.encoding_params.items():
            assert params.video_codec == "H.264"
            assert params.audio_codec == "AAC"
            assert params.pixel_format == "yuv420p"
            assert isinstance(params.resolution, tuple)
            assert len(params.resolution) == 2
            assert all(isinstance(dim, int) and dim > 0 for dim in params.resolution)
    
    @invariant()
    def seo_metadata_consistency(self):
        """Invariant: All SEO metadata should be within YouTube limits."""
        for title, metadata in self.generated_metadata.items():
            assert len(metadata.title) <= 100
            assert len(metadata.description) <= 5000
            assert len(metadata.tags) <= 15
            assert isinstance(metadata.category, str)
            assert len(metadata.category) > 0


# Run stateful tests
TestYouTubeOptimizerState = YouTubeOptimizerStateMachine.TestCase


if __name__ == "__main__":
    # Run async tests
    async def run_async_tests():
        print("Testing YouTube optimization...")
        
        # Create mock Gemini client
        mock_gemini = AsyncMock(spec=GeminiClient)
        mock_gemini.generate_content.return_value = json.dumps({
            "optimized_title": "Learn Mathematics - Complete Guide",
            "optimized_description": "Master mathematical concepts with this comprehensive guide",
            "tags": ["mathematics", "education", "tutorial"],
            "category": "Education"
        })
        
        optimizer = YouTubeOptimizer(gemini_client=mock_gemini)
        
        # Test basic optimization
        content_metadata = {
            'title': 'Introduction to Linear Algebra',
            'description': 'Learn the fundamentals of linear algebra',
            'duration': 600
        }
        
        optimization_settings = YouTubeOptimizationSettings(
            content_type=YouTubeContentType.EDUCATIONAL,
            target_audience='general'
        )
        
        result = await optimizer.optimize_for_youtube(
            content_metadata, {}, optimization_settings
        )
        
        print(f"✓ Optimization result: {result is not None}")
        print(f"✓ Encoding params: {result['encoding_params']['video_codec']}")
        print(f"✓ SEO title: {result['seo_metadata']['title']}")
        print(f"✓ Performance score: {result['optimization_summary']['estimated_performance_score']}")
        
        # Test encoding params generation
        encoding_params = YouTubeEncodingParams.from_content_type(
            YouTubeContentType.EDUCATIONAL, "4k"
        )
        print(f"✓ Encoding params generated: {encoding_params.video_codec}")
        
        # Test chapter markers
        chapter_markers = await optimizer._generate_chapter_markers(
            content_metadata, optimization_settings
        )
        print(f"✓ Chapter markers generated: {len(chapter_markers)}")
        
        print("All YouTube optimization tests completed successfully!")
    
    asyncio.run(run_async_tests())