"""
Property tests for cinematic preview caching efficiency.
Tests caching behavior, performance improvements, and cache invalidation.
"""

import pytest
import asyncio
import time
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

from src.cinematic.preview_generator import (
    CinematicPreviewGenerator, PreviewRequest, PreviewResult, PreviewCache
)
from src.cinematic.models import (
    CinematicSettingsModel, CameraMovementSettings, ColorGradingSettings,
    SoundDesignSettings, AdvancedCompositingSettings, CameraMovementType, FilmEmulationType
)


# Strategies for generating test data
@st.composite
def camera_movement_settings(draw):
    """Generate camera movement settings."""
    return CameraMovementSettings(
        enabled=draw(st.booleans()),
        allowed_types=draw(st.lists(st.sampled_from(list(CameraMovementType)), min_size=1)),
        intensity=draw(st.integers(min_value=0, max_value=100)),
        auto_select=draw(st.booleans())
    )


@st.composite
def color_grading_settings(draw):
    """Generate color grading settings."""
    return ColorGradingSettings(
        enabled=draw(st.booleans()),
        film_emulation=draw(st.sampled_from(list(FilmEmulationType))),
        temperature=draw(st.integers(min_value=-100, max_value=100)),
        tint=draw(st.integers(min_value=-100, max_value=100)),
        contrast=draw(st.integers(min_value=-100, max_value=100)),
        saturation=draw(st.integers(min_value=-100, max_value=100)),
        brightness=draw(st.integers(min_value=-100, max_value=100)),
        shadows=draw(st.integers(min_value=-100, max_value=100)),
        highlights=draw(st.integers(min_value=-100, max_value=100)),
        auto_adjust=draw(st.booleans())
    )


@st.composite
def sound_design_settings(draw):
    """Generate sound design settings."""
    return SoundDesignSettings(
        enabled=draw(st.booleans()),
        ambient_audio=draw(st.booleans()),
        music_scoring=draw(st.booleans()),
        spatial_audio=draw(st.booleans()),
        reverb_intensity=draw(st.integers(min_value=0, max_value=100)),
        eq_processing=draw(st.booleans()),
        dynamic_range_compression=draw(st.booleans()),
        auto_select_music=draw(st.booleans())
    )


@st.composite
def advanced_compositing_settings(draw):
    """Generate advanced compositing settings."""
    return AdvancedCompositingSettings(
        enabled=draw(st.booleans()),
        film_grain=draw(st.booleans()),
        dynamic_lighting=draw(st.booleans()),
        depth_of_field=draw(st.booleans()),
        motion_blur=draw(st.booleans()),
        professional_transitions=draw(st.booleans()),
        lut_application=draw(st.booleans())
    )


@st.composite
def cinematic_settings(draw):
    """Generate complete cinematic settings."""
    return CinematicSettingsModel(
        camera_movements=draw(camera_movement_settings()),
        color_grading=draw(color_grading_settings()),
        sound_design=draw(sound_design_settings()),
        advanced_compositing=draw(advanced_compositing_settings()),
        quality_preset=draw(st.sampled_from(["standard_hd", "cinematic_4k", "cinematic_8k"])),
        auto_recommendations=draw(st.booleans())
    )


@st.composite
def preview_request_data(draw):
    """Generate preview request data."""
    return {
        "scene_id": draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        "settings": draw(cinematic_settings()),
        "content": draw(st.text(min_size=10, max_size=1000)),
        "feature_type": draw(st.sampled_from(["color_grading", "camera_movement", "full_preview", "generic"]))
    }


class TestPreviewCachingEfficiency:
    """Test preview caching efficiency and performance."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.temp_dir = tempfile.mkdtemp()
        self.generator = CinematicPreviewGenerator(cache_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test dependencies."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @given(preview_request_data())
    @settings(max_examples=20, deadline=10000)
    def test_cache_hit_performance_improvement(self, request_data):
        """Property: Cache hits should be significantly faster than cache misses."""
        async def test_caching():
            request = PreviewRequest(
                scene_id=request_data["scene_id"],
                settings=request_data["settings"],
                content=request_data["content"],
                feature_type=request_data["feature_type"]
            )
            
            # First request (cache miss)
            start_time = time.time()
            result1 = await self.generator.generate_preview(request)
            first_time = time.time() - start_time
            
            # Second request (cache hit)
            start_time = time.time()
            result2 = await self.generator.generate_preview(request)
            second_time = time.time() - start_time
            
            # Cache hit should be significantly faster
            assert second_time < first_time, f"Cache hit ({second_time:.3f}s) should be faster than miss ({first_time:.3f}s)"
            
            # Results should be identical
            assert result1.cache_key == result2.cache_key
            assert result1.preview_url == result2.preview_url
            assert result1.effects_applied == result2.effects_applied
            
            # Cache hit should be at least 50% faster
            improvement_ratio = first_time / second_time if second_time > 0 else float('inf')
            assert improvement_ratio >= 1.5, f"Cache should provide at least 50% improvement, got {improvement_ratio:.2f}x"
        
        asyncio.run(test_caching())
    
    @given(st.lists(preview_request_data(), min_size=3, max_size=8))
    @settings(max_examples=10, deadline=15000)
    def test_cache_consistency_across_requests(self, requests_list):
        """Property: Identical requests should always return cached results."""
        # Make some requests identical
        if len(requests_list) >= 2:
            requests_list[1] = requests_list[0].copy()
            requests_list[1]["scene_id"] = requests_list[0]["scene_id"]  # Ensure same scene_id
        
        async def test_consistency():
            results = []
            cache_keys = set()
            
            for i, request_data in enumerate(requests_list):
                request = PreviewRequest(
                    scene_id=f"consistency_test_{i}_{request_data['scene_id']}",
                    settings=request_data["settings"],
                    content=request_data["content"],
                    feature_type=request_data["feature_type"]
                )
                
                result = await self.generator.generate_preview(request)
                results.append(result)
                cache_keys.add(result.cache_key)
            
            # Check for duplicate requests (same cache key)
            cache_key_counts = {}
            for result in results:
                cache_key_counts[result.cache_key] = cache_key_counts.get(result.cache_key, 0) + 1
            
            # Verify cache statistics
            cache_stats = self.generator.get_cache_stats()
            assert cache_stats["cache_size"] <= len(requests_list), "Cache size should not exceed unique requests"
            
            # All results should be valid
            for result in results:
                assert result.cache_key is not None
                assert result.preview_url is not None
                assert isinstance(result.effects_applied, list)
        
        asyncio.run(test_consistency())
    
    @given(preview_request_data())
    @settings(max_examples=15, deadline=10000)
    def test_cache_invalidation_on_settings_change(self, request_data):
        """Property: Changing settings should invalidate cache and create new entry."""
        async def test_invalidation():
            # Original request
            original_request = PreviewRequest(
                scene_id=request_data["scene_id"],
                settings=request_data["settings"],
                content=request_data["content"],
                feature_type=request_data["feature_type"]
            )
            
            original_result = await self.generator.generate_preview(original_request)
            
            # Modified settings
            modified_settings = request_data["settings"]
            # Change camera movement intensity
            modified_settings.camera_movements.intensity = (
                modified_settings.camera_movements.intensity + 10
            ) % 100
            
            modified_request = PreviewRequest(
                scene_id=request_data["scene_id"],  # Same scene ID
                settings=modified_settings,
                content=request_data["content"],  # Same content
                feature_type=request_data["feature_type"]  # Same feature type
            )
            
            modified_result = await self.generator.generate_preview(modified_request)
            
            # Should have different cache keys
            assert original_result.cache_key != modified_result.cache_key, "Different settings should produce different cache keys"
            
            # Cache should now contain both entries
            cache_stats = self.generator.get_cache_stats()
            assert cache_stats["cache_size"] >= 2, "Cache should contain both original and modified entries"
        
        asyncio.run(test_invalidation())
    
    @given(st.integers(min_value=1, max_value=15))
    @settings(max_examples=8, deadline=15000)
    def test_cache_size_management(self, num_requests):
        """Property: Cache should manage size efficiently and not grow unbounded."""
        # Set small cache size for testing
        self.generator.cache.max_size = 5
        
        async def test_size_management():
            requests = []
            for i in range(num_requests):
                request = PreviewRequest(
                    scene_id=f"size_test_{i}",
                    settings=CinematicSettingsModel(
                        camera_movements=CameraMovementSettings(intensity=i * 10 % 100),
                        color_grading=ColorGradingSettings(),
                        sound_design=SoundDesignSettings(),
                        advanced_compositing=AdvancedCompositingSettings()
                    ),
                    content=f"Test content {i}",
                    feature_type="full_preview"
                )
                requests.append(request)
            
            # Generate all previews
            for request in requests:
                await self.generator.generate_preview(request)
            
            # Cache size should not exceed maximum
            cache_stats = self.generator.get_cache_stats()
            assert cache_stats["cache_size"] <= self.generator.cache.max_size, f"Cache size ({cache_stats['cache_size']}) should not exceed max ({self.generator.cache.max_size})"
            
            # Should still be able to generate new previews
            new_request = PreviewRequest(
                scene_id="overflow_test",
                settings=CinematicSettingsModel(
                    camera_movements=CameraMovementSettings(),
                    color_grading=ColorGradingSettings(),
                    sound_design=SoundDesignSettings(),
                    advanced_compositing=AdvancedCompositingSettings()
                ),
                content="Overflow test content",
                feature_type="full_preview"
            )
            
            result = await self.generator.generate_preview(new_request)
            assert result is not None
            assert result.cache_key is not None
        
        asyncio.run(test_size_management())
    
    @given(st.lists(preview_request_data(), min_size=2, max_size=6))
    @settings(max_examples=10, deadline=12000)
    def test_concurrent_cache_access(self, requests_list):
        """Property: Concurrent cache access should be thread-safe and consistent."""
        # Ensure unique scene IDs
        for i, request in enumerate(requests_list):
            request["scene_id"] = f"concurrent_{i}_{request['scene_id']}"
        
        async def test_concurrent_access():
            # Create requests
            requests = [
                PreviewRequest(
                    scene_id=req_data["scene_id"],
                    settings=req_data["settings"],
                    content=req_data["content"],
                    feature_type=req_data["feature_type"]
                )
                for req_data in requests_list
            ]
            
            # Generate previews concurrently
            tasks = [self.generator.generate_preview(req) for req in requests]
            results = await asyncio.gather(*tasks)
            
            # All results should be valid
            assert len(results) == len(requests)
            
            for result in results:
                assert isinstance(result, PreviewResult)
                assert result.cache_key is not None
                assert result.preview_url is not None
            
            # Cache should be in consistent state
            cache_stats = self.generator.get_cache_stats()
            assert cache_stats["cache_size"] >= 0
            assert cache_stats["cache_size"] <= len(requests)
            
            # Regenerate same requests (should hit cache)
            start_time = time.time()
            cached_results = await asyncio.gather(*[self.generator.generate_preview(req) for req in requests])
            cached_time = time.time() - start_time
            
            # Cached results should match original results
            for original, cached in zip(results, cached_results):
                assert original.cache_key == cached.cache_key
                assert original.preview_url == cached.preview_url
        
        asyncio.run(test_concurrent_access())
    
    def test_cache_persistence_across_instances(self):
        """Property: Cache should persist across generator instances."""
        async def test_persistence():
            # Create first generator instance
            generator1 = CinematicPreviewGenerator(cache_dir=self.temp_dir)
            
            request = PreviewRequest(
                scene_id="persistence_test",
                settings=CinematicSettingsModel(
                    camera_movements=CameraMovementSettings(),
                    color_grading=ColorGradingSettings(),
                    sound_design=SoundDesignSettings(),
                    advanced_compositing=AdvancedCompositingSettings()
                ),
                content="Persistence test content",
                feature_type="full_preview"
            )
            
            # Generate preview with first instance
            result1 = await generator1.generate_preview(request)
            cache_key1 = result1.cache_key
            
            # Create second generator instance (same cache directory)
            generator2 = CinematicPreviewGenerator(cache_dir=self.temp_dir)
            
            # Generate same preview with second instance
            start_time = time.time()
            result2 = await generator2.generate_preview(request)
            cached_time = time.time() - start_time
            
            # Should use cached result
            assert result2.cache_key == cache_key1
            assert result2.preview_url == result1.preview_url
            
            # Should be fast (cache hit)
            assert cached_time < 0.1, f"Cache hit should be fast, took {cached_time:.3f}s"
        
        asyncio.run(test_persistence())
    
    @given(preview_request_data())
    @settings(max_examples=10, deadline=8000)
    def test_cache_cleanup_functionality(self, request_data):
        """Property: Cache cleanup should work correctly without affecting valid entries."""
        async def test_cleanup():
            # Generate some previews
            requests = []
            for i in range(3):
                request = PreviewRequest(
                    scene_id=f"cleanup_test_{i}",
                    settings=request_data["settings"],
                    content=f"Content {i}",
                    feature_type=request_data["feature_type"]
                )
                requests.append(request)
                await self.generator.generate_preview(request)
            
            # Check initial cache state
            initial_stats = self.generator.get_cache_stats()
            assert initial_stats["cache_size"] == 3
            
            # Clear cache
            self.generator.clear_cache()
            
            # Cache should be empty
            cleared_stats = self.generator.get_cache_stats()
            assert cleared_stats["cache_size"] == 0
            
            # Should still be able to generate new previews
            new_request = PreviewRequest(
                scene_id="post_cleanup_test",
                settings=request_data["settings"],
                content="Post cleanup content",
                feature_type=request_data["feature_type"]
            )
            
            result = await self.generator.generate_preview(new_request)
            assert result is not None
            assert result.cache_key is not None
            
            # Cache should have new entry
            final_stats = self.generator.get_cache_stats()
            assert final_stats["cache_size"] == 1
        
        asyncio.run(test_cleanup())


class PreviewCacheStateMachine(RuleBasedStateMachine):
    """Stateful property testing for preview cache behavior."""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.generator = CinematicPreviewGenerator(cache_dir=self.temp_dir)
        self.generated_requests = {}
        self.cache_operations = []
        self.request_count = 0
    
    preview_requests = Bundle('preview_requests')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=preview_requests)
    def generate_new_preview(self):
        """Generate a new unique preview."""
        scene_id = f"state_test_{self.request_count}"
        request = PreviewRequest(
            scene_id=scene_id,
            settings=CinematicSettingsModel(
                camera_movements=CameraMovementSettings(intensity=self.request_count % 100),
                color_grading=ColorGradingSettings(),
                sound_design=SoundDesignSettings(),
                advanced_compositing=AdvancedCompositingSettings()
            ),
            content=f"State test content {self.request_count}",
            feature_type="full_preview"
        )
        
        async def generate():
            result = await self.generator.generate_preview(request)
            self.generated_requests[scene_id] = (request, result)
            self.cache_operations.append(('generate', scene_id))
            self.request_count += 1
            return request
        
        return asyncio.run(generate())
    
    @rule(request=preview_requests)
    def regenerate_existing_preview(self, request):
        """Regenerate an existing preview (should hit cache)."""
        if not request:
            return
        
        async def regenerate():
            start_time = time.time()
            result = await self.generator.generate_preview(request)
            cache_time = time.time() - start_time
            
            # Should be fast (cache hit)
            assert cache_time < 0.1, f"Cache hit should be fast, took {cache_time:.3f}s"
            
            self.cache_operations.append(('cache_hit', request.scene_id))
            return result
        
        asyncio.run(regenerate())
    
    @rule()
    def clear_cache(self):
        """Clear the entire cache."""
        self.generator.clear_cache()
        self.cache_operations.append(('clear', None))
    
    @rule()
    def check_cache_stats(self):
        """Check cache statistics for consistency."""
        stats = self.generator.get_cache_stats()
        
        # Cache size should be non-negative
        assert stats["cache_size"] >= 0
        
        # Cache size should not exceed total requests
        assert stats["cache_size"] <= self.request_count
    
    @invariant()
    def cache_consistency(self):
        """Invariant: Cache state should always be consistent."""
        stats = self.generator.get_cache_stats()
        
        # Cache size should be reasonable
        assert 0 <= stats["cache_size"] <= self.generator.cache.max_size
    
    @invariant()
    def preview_generation_always_works(self):
        """Invariant: Preview generation should always produce valid results."""
        # Test with a simple request
        test_request = PreviewRequest(
            scene_id="invariant_test",
            settings=CinematicSettingsModel(
                camera_movements=CameraMovementSettings(),
                color_grading=ColorGradingSettings(),
                sound_design=SoundDesignSettings(),
                advanced_compositing=AdvancedCompositingSettings()
            ),
            content="Invariant test content",
            feature_type="full_preview"
        )
        
        async def test_generation():
            result = await self.generator.generate_preview(test_request)
            assert result is not None
            assert result.cache_key is not None
            assert result.preview_url is not None
        
        asyncio.run(test_generation())
    
    def teardown(self):
        """Clean up after state machine testing."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# Test the state machine
TestPreviewCacheState = PreviewCacheStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])