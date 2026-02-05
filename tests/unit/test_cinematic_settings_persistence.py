"""
Property tests for cinematic settings persistence.
Tests the round-trip persistence of settings and profiles.
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
import json
from datetime import datetime

from src.cinematic.models import (
    CinematicSettingsModel, CinematicProfileModel, VisualDescriptionModel,
    CameraMovementSettings, ColorGradingSettings, SoundDesignSettings,
    AdvancedCompositingSettings, CameraMovementType, FilmEmulationType,
    QualityPresetType, get_system_profiles
)
from src.cinematic.settings_manager import CinematicSettingsManager, FileStorageBackend


# Hypothesis strategies for generating test data
@st.composite
def camera_movement_settings(draw):
    """Generate valid camera movement settings."""
    return CameraMovementSettings(
        enabled=draw(st.booleans()),
        allowed_types=draw(st.lists(st.sampled_from(CameraMovementType), min_size=1, unique=True)),
        intensity=draw(st.integers(min_value=0, max_value=100)),
        auto_select=draw(st.booleans())
    )


@st.composite
def color_grading_settings(draw):
    """Generate valid color grading settings."""
    return ColorGradingSettings(
        enabled=draw(st.booleans()),
        film_emulation=draw(st.sampled_from(FilmEmulationType)),
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
    """Generate valid sound design settings."""
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
    """Generate valid advanced compositing settings."""
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
    """Generate valid cinematic settings."""
    return CinematicSettingsModel(
        camera_movements=draw(camera_movement_settings()),
        color_grading=draw(color_grading_settings()),
        sound_design=draw(sound_design_settings()),
        advanced_compositing=draw(advanced_compositing_settings()),
        quality_preset=draw(st.sampled_from(QualityPresetType)),
        auto_recommendations=draw(st.booleans())
    )


@st.composite
def valid_profile_name(draw):
    """Generate valid profile names."""
    return draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip()))


@st.composite
def valid_profile_description(draw):
    """Generate valid profile descriptions."""
    return draw(st.text(max_size=500))


@st.composite
def cinematic_profile(draw):
    """Generate valid cinematic profiles."""
    return CinematicProfileModel(
        name=draw(valid_profile_name()),
        description=draw(valid_profile_description()),
        settings=draw(cinematic_settings()),
        user_id=draw(st.text(min_size=1, max_size=50).filter(lambda x: x.strip())),
        is_default=draw(st.booleans()),
        is_system=False  # Only generate user profiles for testing
    )


@st.composite
def visual_description(draw):
    """Generate valid visual descriptions."""
    return VisualDescriptionModel(
        scene_id=draw(st.text(min_size=1, max_size=100).filter(lambda x: x.strip())),
        content=draw(st.text(min_size=1)),
        description=draw(st.text(min_size=1)),
        generated_by=draw(st.sampled_from(["user", "gemini", "template"])),
        cinematic_settings=draw(st.dictionaries(st.text(), st.text())),
        scene_analysis=draw(st.dictionaries(st.text(), st.text())),
        suggestions=draw(st.lists(st.text())),
        confidence=draw(st.floats(min_value=0.0, max_value=1.0))
    )


class TestSettingsPersistence:
    """Test settings persistence round-trip operations."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def storage_backend(self, temp_storage_dir):
        """Create file storage backend with temporary directory."""
        return FileStorageBackend(temp_storage_dir)
    
    @pytest.fixture
    def settings_manager(self, temp_storage_dir):
        """Create settings manager with temporary storage."""
        manager = CinematicSettingsManager()
        manager.storage = FileStorageBackend(temp_storage_dir)
        return manager
    
    @given(cinematic_settings())
    @settings(max_examples=50, deadline=5000)
    def test_settings_serialization_round_trip(self, settings_data):
        """Property: Settings can be serialized and deserialized without loss."""
        # Convert to dict and back
        settings_dict = settings_data.to_dict()
        restored_settings = CinematicSettingsModel.from_dict(settings_dict)
        
        # Should be identical
        assert restored_settings.to_dict() == settings_dict
        
        # Validate both are valid
        original_errors = settings_data.validate()
        restored_errors = restored_settings.validate()
        assert original_errors == restored_errors
    
    @given(cinematic_profile())
    @settings(max_examples=50, deadline=5000)
    def test_profile_serialization_round_trip(self, profile_data):
        """Property: Profiles can be serialized and deserialized without loss."""
        assume(not profile_data.validate())  # Only test valid profiles
        
        # Convert to dict and back
        profile_dict = profile_data.to_dict()
        restored_profile = CinematicProfileModel.from_dict(profile_dict)
        
        # Should be identical (except for generated timestamps)
        original_dict = profile_data.to_dict()
        restored_dict = restored_profile.to_dict()
        
        # Compare all fields except timestamps which might differ slightly
        for key in original_dict:
            if key not in ['created_at', 'last_used']:
                assert original_dict[key] == restored_dict[key]
    
    def test_profile_file_persistence_round_trip(self, storage_backend):
        """Property: Profiles persist correctly to file storage."""
        @given(cinematic_profile())
        @settings(max_examples=30, deadline=10000)
        def run_test(profile_data):
            assume(not profile_data.validate())  # Only test valid profiles
            
            async def test_persistence():
                # Save profile
                save_success = await storage_backend.save_profile(profile_data)
                assert save_success
                
                # Load profile
                loaded_profile = await storage_backend.load_profile(profile_data.id, profile_data.user_id)
                assert loaded_profile is not None
                
                # Compare essential data (excluding timestamps)
                assert loaded_profile.id == profile_data.id
                assert loaded_profile.name == profile_data.name
                assert loaded_profile.description == profile_data.description
                assert loaded_profile.user_id == profile_data.user_id
                assert loaded_profile.is_default == profile_data.is_default
                assert loaded_profile.is_system == profile_data.is_system
                
                # Settings should be identical
                assert loaded_profile.settings.to_dict() == profile_data.settings.to_dict()
            
            asyncio.run(test_persistence())
        
        run_test()
    
    def test_visual_description_persistence_round_trip(self, storage_backend):
        """Property: Visual descriptions persist correctly to file storage."""
        @given(visual_description())
        @settings(max_examples=30, deadline=10000)
        def run_test(desc_data):
            async def test_persistence():
                # Save description
                save_success = await storage_backend.save_visual_description(desc_data)
                assert save_success
                
                # Load description
                loaded_desc = await storage_backend.load_visual_description(desc_data.scene_id)
                assert loaded_desc is not None
                
                # Should be identical
                assert loaded_desc.to_dict() == desc_data.to_dict()
            
            asyncio.run(test_persistence())
        
        run_test()
    
    def test_multiple_profiles_persistence(self, storage_backend):
        """Property: Multiple profiles can be saved and retrieved correctly."""
        @given(st.lists(cinematic_profile(), min_size=1, max_size=10))
        @settings(max_examples=20, deadline=15000)
        def run_test(profiles_list):
            # Filter to valid profiles and ensure unique IDs
            valid_profiles = []
            seen_ids = set()
            for profile in profiles_list:
                if not profile.validate() and profile.id not in seen_ids:
                    valid_profiles.append(profile)
                    seen_ids.add(profile.id)
            
            assume(len(valid_profiles) > 0)
            
            async def test_multiple_persistence():
                # Save all profiles
                for profile in valid_profiles:
                    save_success = await storage_backend.save_profile(profile)
                    assert save_success
                
                # Group by user_id
                users = {}
                for profile in valid_profiles:
                    if profile.user_id not in users:
                        users[profile.user_id] = []
                    users[profile.user_id].append(profile)
                
                # Test listing profiles for each user
                for user_id, user_profiles in users.items():
                    loaded_profiles = await storage_backend.list_profiles(user_id)
                    
                    # Should include system profiles plus user profiles
                    system_count = len(get_system_profiles())
                    expected_count = system_count + len(user_profiles)
                    assert len(loaded_profiles) == expected_count
                    
                    # Check that all user profiles are present
                    loaded_ids = {p.id for p in loaded_profiles if not p.is_system}
                    expected_ids = {p.id for p in user_profiles}
                    assert loaded_ids == expected_ids
            
            asyncio.run(test_multiple_persistence())
        
        run_test()
    
    def test_profile_deletion_persistence(self, storage_backend):
        """Property: Profile deletion works correctly and persists."""
        @given(cinematic_profile())
        @settings(max_examples=20, deadline=10000)
        def run_test(profile_data):
            assume(not profile_data.validate())  # Only test valid profiles
            assume(not profile_data.is_system)  # Cannot delete system profiles
            
            async def test_deletion():
                # Save profile
                save_success = await storage_backend.save_profile(profile_data)
                assert save_success
                
                # Verify it exists
                loaded_profile = await storage_backend.load_profile(profile_data.id, profile_data.user_id)
                assert loaded_profile is not None
                
                # Delete profile
                delete_success = await storage_backend.delete_profile(profile_data.id, profile_data.user_id)
                assert delete_success
                
                # Verify it's gone
                loaded_profile = await storage_backend.load_profile(profile_data.id, profile_data.user_id)
                assert loaded_profile is None
                
                # Should not appear in listings
                profiles = await storage_backend.list_profiles(profile_data.user_id)
                profile_ids = {p.id for p in profiles}
                assert profile_data.id not in profile_ids
            
            asyncio.run(test_deletion())
        
        run_test()
    
    def test_settings_manager_export_import_round_trip(self, settings_manager):
        """Property: Profile export/import maintains data integrity."""
        @given(cinematic_profile())
        @settings(max_examples=20, deadline=10000)
        def run_test(profile_data):
            assume(not profile_data.validate())  # Only test valid profiles
            
            async def test_export_import():
                # Save original profile
                profile_id = await settings_manager.save_profile(
                    profile_data.name,
                    profile_data.settings,
                    profile_data.user_id,
                    profile_data.description
                )
                
                # Export profile
                exported_data = await settings_manager.export_profile(profile_id, profile_data.user_id)
                assert exported_data is not None
                
                # Import profile (will get new ID)
                imported_id = await settings_manager.import_profile(exported_data, profile_data.user_id)
                assert imported_id is not None
                assert imported_id != profile_id  # Should get new ID
                
                # Load both profiles
                original_settings = await settings_manager.load_profile(profile_id, profile_data.user_id)
                imported_settings = await settings_manager.load_profile(imported_id, profile_data.user_id)
                
                # Settings should be identical
                assert original_settings.to_dict() == imported_settings.to_dict()
            
            asyncio.run(test_export_import())
        
        run_test()


class CinematicSettingsStateMachine(RuleBasedStateMachine):
    """Stateful property testing for cinematic settings operations."""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CinematicSettingsManager()
        self.manager.storage = FileStorageBackend(self.temp_dir)
        self.saved_profiles = {}  # profile_id -> (user_id, profile_data)
    
    profiles = Bundle('profiles')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=profiles, profile_data=cinematic_profile())
    def save_profile(self, profile_data):
        """Save a profile and track it."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def save():
            try:
                profile_id = await self.manager.save_profile(
                    profile_data.name,
                    profile_data.settings,
                    profile_data.user_id,
                    profile_data.description
                )
                self.saved_profiles[profile_id] = (profile_data.user_id, profile_data)
                return profile_id
            except Exception:
                return None
        
        return asyncio.run(save())
    
    @rule(profile_id=profiles)
    def load_profile(self, profile_id):
        """Load a profile and verify it matches saved data."""
        if profile_id is None or profile_id not in self.saved_profiles:
            return
        
        user_id, original_data = self.saved_profiles[profile_id]
        
        async def load():
            loaded_settings = await self.manager.load_profile(profile_id, user_id)
            if loaded_settings is not None:
                # Settings should match original
                assert loaded_settings.to_dict() == original_data.settings.to_dict()
        
        asyncio.run(load())
    
    @rule(profile_id=profiles)
    def delete_profile(self, profile_id):
        """Delete a profile and verify it's gone."""
        if profile_id is None or profile_id not in self.saved_profiles:
            return
        
        user_id, _ = self.saved_profiles[profile_id]
        
        async def delete():
            success = await self.manager.delete_profile(profile_id, user_id)
            if success:
                # Remove from tracking
                del self.saved_profiles[profile_id]
                
                # Verify it's gone
                loaded = await self.manager.load_profile(profile_id, user_id)
                assert loaded is None
        
        asyncio.run(delete())
    
    @invariant()
    def all_saved_profiles_loadable(self):
        """Invariant: All saved profiles should be loadable."""
        async def check():
            for profile_id, (user_id, original_data) in self.saved_profiles.items():
                loaded_settings = await self.manager.load_profile(profile_id, user_id)
                assert loaded_settings is not None
                assert loaded_settings.to_dict() == original_data.settings.to_dict()
        
        asyncio.run(check())
    
    def teardown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# Test the state machine
TestCinematicSettingsState = CinematicSettingsStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])