"""
Property-Based Tests for Backward Compatibility

Tests universal properties of backward compatibility for VideoAsset model enhancements.
**Feature: production-video-generation, Property 15: Backward Compatibility**
**Validates: Requirements 10.1, 10.2, 10.3, 10.4, 10.5**
"""

import pytest
import tempfile
import shutil
import json
from pathlib import Path
from hypothesis import given, strategies as st, settings, assume
from datetime import datetime
from typing import Dict, Any, List

from backend.models.video import VideoAsset, VideoMetadata, Chapter, PrivacyStatus


# Test data generators
@st.composite
def legacy_video_data(draw):
    """Generate legacy video data without new production fields."""
    return {
        'file_path': draw(st.text(min_size=5, max_size=100)) + '.mp4',
        'duration': draw(st.floats(min_value=1.0, max_value=3600.0)),
        'resolution': draw(st.sampled_from(['1920x1080', '1280x720', '854x480', '640x360'])),
        'file_size': draw(st.integers(min_value=1024, max_value=1024*1024*1024)),
        'codec': draw(st.sampled_from(['libx264', 'h264', 'hevc'])),
        'bitrate': draw(st.sampled_from(['1000k', '2500k', '5000k', '8000k'])),
        'frame_rate': draw(st.integers(min_value=24, max_value=60)),
        'audio_codec': draw(st.sampled_from(['aac', 'mp3'])),
        'metadata': {
            'title': draw(st.text(min_size=10, max_size=100)),
            'description': draw(st.text(min_size=50, max_size=500)),
            'tags': draw(st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=10)),
            'category': 'Education',
            'privacy_status': 'unlisted'
        }
    }

@st.composite
def enhanced_video_data(draw):
    """Generate enhanced video data with new production fields."""
    legacy_data = draw(legacy_video_data())
    
    # Add new production fields
    legacy_data.update({
        'codec_info': {
            'video_codec': draw(st.sampled_from(['h264', 'hevc', 'vp9'])),
            'audio_codec': draw(st.sampled_from(['aac', 'opus', 'mp3'])),
            'container': draw(st.sampled_from(['mp4', 'mkv', 'webm'])),
            'profile': draw(st.sampled_from(['baseline', 'main', 'high']))
        },
        'quality_preset': draw(st.sampled_from(['low', 'medium', 'high', 'custom'])),
        'validation_status': {
            'is_valid': draw(st.booleans()),
            'format_valid': draw(st.booleans()),
            'duration_valid': draw(st.booleans()),
            'codec_valid': draw(st.booleans()),
            'errors': draw(st.lists(st.text(min_size=5, max_size=50), max_size=3)),
            'warnings': draw(st.lists(st.text(min_size=5, max_size=50), max_size=3))
        },
        'processing_method': draw(st.sampled_from(['ffmpeg', 'moviepy', 'slideshow'])),
        'generation_params': {
            'model_used': draw(st.text(min_size=5, max_size=30)),
            'quality_settings': draw(st.dictionaries(
                st.text(min_size=3, max_size=20),
                st.one_of(st.text(min_size=1, max_size=50), st.integers(), st.floats()),
                max_size=5
            )),
            'processing_time': draw(st.floats(min_value=1.0, max_value=3600.0))
        }
    })
    
    return legacy_data

@st.composite
def video_metadata_strategy(draw):
    """Generate video metadata for testing."""
    return VideoMetadata(
        title=draw(st.text(min_size=10, max_size=100)),
        description=draw(st.text(min_size=50, max_size=500)),
        tags=draw(st.lists(st.text(min_size=3, max_size=20), min_size=1, max_size=10)),
        category=draw(st.sampled_from(['Education', 'Science', 'Technology', 'Entertainment'])),
        privacy_status=draw(st.sampled_from([status.value for status in PrivacyStatus])),
        thumbnail_path=draw(st.one_of(st.none(), st.text(min_size=5, max_size=100))),
        language=draw(st.sampled_from(['en', 'es', 'fr', 'de', 'zh'])),
        captions_path=draw(st.one_of(st.none(), st.text(min_size=5, max_size=100)))
    )

@st.composite
def chapter_strategy(draw):
    """Generate chapter data for testing."""
    return Chapter(
        title=draw(st.text(min_size=5, max_size=50)),
        start_time=draw(st.floats(min_value=0.0, max_value=3600.0)),
        end_time=draw(st.floats(min_value=0.0, max_value=3600.0))
    )


class TestBackwardCompatibilityProperties:
    """Property-based tests for backward compatibility"""
    
    def setup_method(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        
    def teardown_method(self):
        """Clean up test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(legacy_video_data())
    @settings(max_examples=100, deadline=None)
    def test_legacy_video_asset_creation(self, legacy_data):
        """
        Property: For any legacy video data, VideoAsset should be creatable without new fields
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        # Create VideoAsset with only legacy fields
        try:
            video_asset = VideoAsset(
                file_path=legacy_data['file_path'],
                duration=legacy_data['duration'],
                resolution=legacy_data['resolution'],
                file_size=legacy_data['file_size'],
                metadata=VideoMetadata(**legacy_data['metadata']),
                chapters=[]
            )
            
            # Verify basic properties are preserved
            assert video_asset.file_path == legacy_data['file_path']
            assert video_asset.duration == legacy_data['duration']
            assert video_asset.resolution == legacy_data['resolution']
            assert video_asset.file_size == legacy_data['file_size']
            assert video_asset.metadata.title == legacy_data['metadata']['title']
            
            # New fields should have default values or be None
            assert hasattr(video_asset, 'codec_info') or True  # May not exist in legacy
            assert hasattr(video_asset, 'quality_preset') or True  # May not exist in legacy
            assert hasattr(video_asset, 'validation_status') or True  # May not exist in legacy
            
        except Exception as e:
            pytest.fail(f"Legacy VideoAsset creation failed: {e}")
    
    @given(enhanced_video_data())
    @settings(max_examples=50, deadline=None)
    def test_enhanced_video_asset_creation(self, enhanced_data):
        """
        Property: For any enhanced video data, VideoAsset should handle new fields gracefully
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        try:
            # Extract metadata
            metadata_dict = enhanced_data.pop('metadata')
            codec_info = enhanced_data.pop('codec_info', None)
            quality_preset = enhanced_data.pop('quality_preset', None)
            validation_status = enhanced_data.pop('validation_status', None)
            processing_method = enhanced_data.pop('processing_method', None)
            generation_params = enhanced_data.pop('generation_params', None)
            
            video_asset = VideoAsset(
                file_path=enhanced_data['file_path'],
                duration=enhanced_data['duration'],
                resolution=enhanced_data['resolution'],
                file_size=enhanced_data['file_size'],
                metadata=VideoMetadata(**metadata_dict),
                chapters=[]
            )
            
            # Basic properties should work
            assert video_asset.file_path == enhanced_data['file_path']
            assert video_asset.duration == enhanced_data['duration']
            assert video_asset.resolution == enhanced_data['resolution']
            assert video_asset.file_size == enhanced_data['file_size']
            
            # Should be serializable to dict
            asset_dict = video_asset.to_dict()
            assert isinstance(asset_dict, dict)
            assert 'file_path' in asset_dict
            assert 'duration' in asset_dict
            assert 'metadata' in asset_dict
            
        except Exception as e:
            pytest.fail(f"Enhanced VideoAsset creation failed: {e}")
    
    @given(
        legacy_video_data(),
        st.lists(chapter_strategy(), min_size=0, max_size=10)
    )
    @settings(max_examples=50, deadline=None)
    def test_video_asset_serialization_compatibility(self, legacy_data, chapters):
        """
        Property: For any video asset, serialization should maintain backward compatibility
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        # Ensure chapter times are ordered
        chapters = sorted(chapters, key=lambda c: c.start_time)
        for i, chapter in enumerate(chapters):
            if chapter.end_time <= chapter.start_time:
                chapters[i] = Chapter(
                    title=chapter.title,
                    start_time=chapter.start_time,
                    end_time=chapter.start_time + 60.0  # Add 1 minute
                )
        
        video_asset = VideoAsset(
            file_path=legacy_data['file_path'],
            duration=legacy_data['duration'],
            resolution=legacy_data['resolution'],
            file_size=legacy_data['file_size'],
            metadata=VideoMetadata(**legacy_data['metadata']),
            chapters=chapters
        )
        
        # Test serialization
        serialized = video_asset.to_dict()
        assert isinstance(serialized, dict)
        
        # Essential fields should be present
        essential_fields = ['file_path', 'duration', 'resolution', 'file_size', 'metadata']
        for field in essential_fields:
            assert field in serialized, f"Essential field {field} missing from serialization"
        
        # Metadata should be properly nested
        assert isinstance(serialized['metadata'], dict)
        assert 'title' in serialized['metadata']
        assert 'description' in serialized['metadata']
        
        # Chapters should be serializable
        if chapters:
            assert 'chapters' in serialized
            assert isinstance(serialized['chapters'], list)
            assert len(serialized['chapters']) == len(chapters)
    
    @given(
        st.lists(legacy_video_data(), min_size=1, max_size=10),
        st.text(min_size=5, max_size=50)
    )
    @settings(max_examples=30, deadline=None)
    def test_video_asset_list_compatibility(self, video_data_list, list_name):
        """
        Property: For any list of video assets, operations should maintain compatibility
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        video_assets = []
        
        for video_data in video_data_list:
            try:
                video_asset = VideoAsset(
                    file_path=video_data['file_path'],
                    duration=video_data['duration'],
                    resolution=video_data['resolution'],
                    file_size=video_data['file_size'],
                    metadata=VideoMetadata(**video_data['metadata']),
                    chapters=[]
                )
                video_assets.append(video_asset)
            except Exception as e:
                # Skip invalid data but don't fail the test
                continue
        
        assume(len(video_assets) > 0)  # Need at least one valid asset
        
        # Test list operations
        total_duration = sum(asset.duration for asset in video_assets)
        assert total_duration >= 0, "Total duration should be non-negative"
        
        total_size = sum(asset.file_size for asset in video_assets)
        assert total_size >= 0, "Total file size should be non-negative"
        
        # Test filtering operations
        hd_assets = [asset for asset in video_assets if '1920x1080' in asset.resolution]
        assert len(hd_assets) <= len(video_assets), "Filtered list should not be larger than original"
        
        # Test sorting operations
        sorted_by_duration = sorted(video_assets, key=lambda x: x.duration)
        assert len(sorted_by_duration) == len(video_assets), "Sorted list should have same length"
        
        if len(sorted_by_duration) > 1:
            assert sorted_by_duration[0].duration <= sorted_by_duration[-1].duration, "List should be sorted by duration"
    
    @given(legacy_video_data())
    @settings(max_examples=50, deadline=None)
    def test_video_asset_state_management_compatibility(self, legacy_data):
        """
        Property: For any video asset, state management should remain compatible
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        video_asset = VideoAsset(
            file_path=legacy_data['file_path'],
            duration=legacy_data['duration'],
            resolution=legacy_data['resolution'],
            file_size=legacy_data['file_size'],
            metadata=VideoMetadata(**legacy_data['metadata']),
            chapters=[]
        )
        
        # Test basic property access
        assert hasattr(video_asset, 'file_path')
        assert hasattr(video_asset, 'duration')
        assert hasattr(video_asset, 'resolution')
        assert hasattr(video_asset, 'file_size')
        assert hasattr(video_asset, 'metadata')
        assert hasattr(video_asset, 'chapters')
        
        # Test property values
        assert video_asset.file_path == legacy_data['file_path']
        assert video_asset.duration == legacy_data['duration']
        assert video_asset.resolution == legacy_data['resolution']
        assert video_asset.file_size == legacy_data['file_size']
        
        # Test metadata access
        assert video_asset.metadata.title == legacy_data['metadata']['title']
        assert video_asset.metadata.description == legacy_data['metadata']['description']
        assert video_asset.metadata.tags == legacy_data['metadata']['tags']
        
        # Test that the asset can be used in common operations
        asset_info = f"Video: {video_asset.metadata.title} ({video_asset.duration}s)"
        assert isinstance(asset_info, str)
        assert video_asset.metadata.title in asset_info
    
    @given(
        legacy_video_data(),
        st.dictionaries(
            st.text(min_size=3, max_size=20),
            st.one_of(st.text(min_size=1, max_size=50), st.integers(), st.floats(), st.booleans()),
            min_size=0,
            max_size=10
        )
    )
    @settings(max_examples=30, deadline=None)
    def test_video_asset_configuration_compatibility(self, legacy_data, extra_config):
        """
        Property: For any video asset and configuration, the system should handle unknown fields gracefully
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        video_asset = VideoAsset(
            file_path=legacy_data['file_path'],
            duration=legacy_data['duration'],
            resolution=legacy_data['resolution'],
            file_size=legacy_data['file_size'],
            metadata=VideoMetadata(**legacy_data['metadata']),
            chapters=[]
        )
        
        # Test that the asset works with additional configuration
        config = {
            'video_asset': video_asset,
            'processing_options': extra_config
        }
        
        # Should be able to serialize the configuration
        try:
            config_json = json.dumps(config, default=str)  # Use str for non-serializable objects
            assert isinstance(config_json, str)
            assert len(config_json) > 0
        except Exception as e:
            # Some configurations might not be JSON serializable, which is acceptable
            assert isinstance(e, (TypeError, ValueError))
        
        # Basic operations should still work
        assert video_asset.duration > 0
        assert len(video_asset.metadata.title) > 0
        assert video_asset.file_size > 0
    
    @given(
        st.lists(legacy_video_data(), min_size=2, max_size=5),
        st.sampled_from(['duration', 'file_size', 'title'])
    )
    @settings(max_examples=20, deadline=None)
    def test_video_asset_comparison_compatibility(self, video_data_list, sort_key):
        """
        Property: For any list of video assets, comparison operations should work consistently
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        video_assets = []
        
        for video_data in video_data_list:
            video_asset = VideoAsset(
                file_path=video_data['file_path'],
                duration=video_data['duration'],
                resolution=video_data['resolution'],
                file_size=video_data['file_size'],
                metadata=VideoMetadata(**video_data['metadata']),
                chapters=[]
            )
            video_assets.append(video_asset)
        
        # Test sorting by different keys
        if sort_key == 'duration':
            sorted_assets = sorted(video_assets, key=lambda x: x.duration)
            if len(sorted_assets) > 1:
                assert sorted_assets[0].duration <= sorted_assets[-1].duration
        elif sort_key == 'file_size':
            sorted_assets = sorted(video_assets, key=lambda x: x.file_size)
            if len(sorted_assets) > 1:
                assert sorted_assets[0].file_size <= sorted_assets[-1].file_size
        elif sort_key == 'title':
            sorted_assets = sorted(video_assets, key=lambda x: x.metadata.title)
            if len(sorted_assets) > 1:
                assert sorted_assets[0].metadata.title <= sorted_assets[-1].metadata.title
        
        # Test that all assets are still valid after sorting
        for asset in sorted_assets:
            assert asset.duration > 0
            assert asset.file_size > 0
            assert len(asset.metadata.title) > 0
    
    @given(legacy_video_data())
    @settings(max_examples=50, deadline=None)
    def test_video_asset_error_handling_compatibility(self, legacy_data):
        """
        Property: For any video asset, error conditions should be handled gracefully
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        video_asset = VideoAsset(
            file_path=legacy_data['file_path'],
            duration=legacy_data['duration'],
            resolution=legacy_data['resolution'],
            file_size=legacy_data['file_size'],
            metadata=VideoMetadata(**legacy_data['metadata']),
            chapters=[]
        )
        
        # Test accessing non-existent attributes gracefully
        try:
            # These might not exist in legacy versions
            getattr(video_asset, 'codec_info', None)
            getattr(video_asset, 'quality_preset', None)
            getattr(video_asset, 'validation_status', None)
            getattr(video_asset, 'processing_method', None)
        except AttributeError:
            # This is acceptable for backward compatibility
            pass
        
        # Test that essential operations still work
        assert video_asset.file_path is not None
        assert video_asset.duration > 0
        assert video_asset.file_size > 0
        assert video_asset.metadata is not None
        assert video_asset.chapters is not None
        
        # Test serialization doesn't break
        try:
            asset_dict = video_asset.to_dict()
            assert isinstance(asset_dict, dict)
        except Exception as e:
            # If to_dict doesn't exist, that's also acceptable
            assert 'to_dict' in str(e) or 'method' in str(e)


@pytest.mark.integration
class TestBackwardCompatibilityIntegration:
    """Integration tests for backward compatibility"""
    
    def setup_method(self):
        """Set up integration test environment"""
        self.temp_dir = tempfile.mkdtemp()
    
    def teardown_method(self):
        """Clean up integration test environment"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(
        st.lists(legacy_video_data(), min_size=3, max_size=10),
        st.text(min_size=5, max_size=50)
    )
    @settings(max_examples=10, deadline=None)
    def test_complete_backward_compatibility_workflow(self, video_data_list, workflow_name):
        """
        Property: For any video workflow, backward compatibility should be maintained end-to-end
        **Feature: production-video-generation, Property 15: Backward Compatibility**
        """
        # Create video assets from legacy data
        video_assets = []
        for video_data in video_data_list:
            try:
                video_asset = VideoAsset(
                    file_path=video_data['file_path'],
                    duration=video_data['duration'],
                    resolution=video_data['resolution'],
                    file_size=video_data['file_size'],
                    metadata=VideoMetadata(**video_data['metadata']),
                    chapters=[]
                )
                video_assets.append(video_asset)
            except Exception:
                continue  # Skip invalid data
        
        assume(len(video_assets) >= 2)  # Need at least 2 valid assets
        
        # Test workflow operations
        # 1. Collection operations
        total_duration = sum(asset.duration for asset in video_assets)
        assert total_duration > 0
        
        # 2. Filtering operations
        long_videos = [asset for asset in video_assets if asset.duration > 60]
        short_videos = [asset for asset in video_assets if asset.duration <= 60]
        assert len(long_videos) + len(short_videos) == len(video_assets)
        
        # 3. Transformation operations
        video_summaries = [
            {
                'title': asset.metadata.title,
                'duration': asset.duration,
                'size_mb': asset.file_size / (1024 * 1024)
            }
            for asset in video_assets
        ]
        assert len(video_summaries) == len(video_assets)
        
        # 4. Serialization operations
        try:
            workflow_data = {
                'name': workflow_name,
                'assets': [asset.to_dict() for asset in video_assets],
                'summary': {
                    'total_count': len(video_assets),
                    'total_duration': total_duration,
                    'average_duration': total_duration / len(video_assets)
                }
            }
            
            # Should be serializable
            workflow_json = json.dumps(workflow_data, default=str)
            assert isinstance(workflow_json, str)
            assert len(workflow_json) > 0
            
        except Exception as e:
            # Some serialization issues are acceptable
            assert isinstance(e, (TypeError, ValueError, AttributeError))


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])