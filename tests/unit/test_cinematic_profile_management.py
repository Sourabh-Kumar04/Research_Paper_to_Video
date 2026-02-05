"""
Property tests for cinematic profile management.
Tests profile CRUD operations, validation, and management workflows.
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
    CinematicSettingsModel, CinematicProfileModel, 
    CameraMovementType, FilmEmulationType, QualityPresetType,
    get_system_profiles
)
from src.cinematic.settings_manager import CinematicSettingsManager, FileStorageBackend


# Import strategies from persistence tests
from tests.test_cinematic_settings_persistence import (
    cinematic_settings, cinematic_profile, valid_profile_name, valid_profile_description
)


class TestProfileManagement:
    """Test profile management operations and workflows."""
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory."""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def settings_manager(self, temp_storage_dir):
        """Create settings manager with temporary storage."""
        manager = CinematicSettingsManager()
        manager.storage = FileStorageBackend(temp_storage_dir)
        return manager
    
    @given(valid_profile_name(), cinematic_settings(), valid_profile_description())
    @settings(max_examples=30, deadline=10000)
    def test_profile_creation_completeness(self, name, settings_data, description, settings_manager):
        """Property: Profile creation includes all required metadata and validation."""
        assume(not settings_data.validate())  # Only valid settings
        
        async def test_creation():
            user_id = "test_user"
            
            # Create profile
            profile_id = await settings_manager.save_profile(
                name, settings_data, user_id, description, set_as_default=False
            )
            assert profile_id is not None
            
            # Load and verify completeness
            profiles = await settings_manager.get_user_profiles(user_id)
            created_profile = None
            for profile in profiles:
                if profile["id"] == profile_id:
                    created_profile = profile
                    break
            
            assert created_profile is not None
            
            # Verify all required fields are present
            required_fields = [
                "id", "name", "description", "settings", "user_id",
                "is_default", "is_system", "created_at", "last_used", "usage_count"
            ]
            for field in required_fields:
                assert field in created_profile
            
            # Verify field values
            assert created_profile["name"] == name
            assert created_profile["description"] == description
            assert created_profile["user_id"] == user_id
            assert created_profile["is_system"] == False
            assert created_profile["usage_count"] == 0
            
            # Verify settings match
            assert created_profile["settings"] == settings_data.to_dict()
            
            # Verify validation is included
            assert "validation" in created_profile
            assert "valid" in created_profile["validation"]
            assert "errors" in created_profile["validation"]
            assert "warnings" in created_profile["validation"]
        
        asyncio.run(test_creation())
    
    @given(st.lists(cinematic_profile(), min_size=2, max_size=5))
    @settings(max_examples=20, deadline=15000)
    def test_default_profile_management(self, profiles_list, settings_manager):
        """Property: Only one profile can be default per user."""
        # Filter to valid profiles with same user_id
        valid_profiles = [p for p in profiles_list if not p.validate()]
        assume(len(valid_profiles) >= 2)
        
        # Use same user_id for all profiles
        user_id = "test_user"
        for profile in valid_profiles:
            profile.user_id = user_id
        
        async def test_default_management():
            profile_ids = []
            
            # Save all profiles, setting each as default
            for i, profile in enumerate(valid_profiles):
                profile_id = await settings_manager.save_profile(
                    profile.name,
                    profile.settings,
                    user_id,
                    profile.description,
                    set_as_default=True  # Each one becomes default
                )
                profile_ids.append(profile_id)
            
            # Only the last one should be default
            profiles = await settings_manager.get_user_profiles(user_id)
            default_count = sum(1 for p in profiles if p["is_default"] and p["user_id"] == user_id)
            assert default_count == 1
            
            # The last saved profile should be the default
            last_profile = None
            for profile in profiles:
                if profile["id"] == profile_ids[-1]:
                    last_profile = profile
                    break
            
            assert last_profile is not None
            assert last_profile["is_default"] == True
        
        asyncio.run(test_default_management())
    
    @given(cinematic_profile())
    @settings(max_examples=20, deadline=10000)
    def test_profile_usage_tracking(self, profile_data, settings_manager):
        """Property: Profile usage is tracked correctly."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def test_usage_tracking():
            # Save profile
            profile_id = await settings_manager.save_profile(
                profile_data.name,
                profile_data.settings,
                profile_data.user_id,
                profile_data.description
            )
            
            # Initial usage should be 0
            profiles = await settings_manager.get_user_profiles(profile_data.user_id)
            initial_profile = next(p for p in profiles if p["id"] == profile_id)
            assert initial_profile["usage_count"] == 0
            
            # Load profile multiple times
            load_count = 3
            for _ in range(load_count):
                loaded_settings = await settings_manager.load_profile(profile_id, profile_data.user_id)
                assert loaded_settings is not None
            
            # Usage count should be incremented
            profiles = await settings_manager.get_user_profiles(profile_data.user_id)
            used_profile = next(p for p in profiles if p["id"] == profile_id)
            assert used_profile["usage_count"] == load_count
            
            # last_used should be updated
            assert used_profile["last_used"] != initial_profile["last_used"]
        
        asyncio.run(test_usage_tracking())
    
    @given(st.lists(cinematic_profile(), min_size=1, max_size=8))
    @settings(max_examples=15, deadline=15000)
    def test_profile_listing_ordering(self, profiles_list, settings_manager):
        """Property: Profile listings are ordered by last_used (most recent first)."""
        # Filter to valid profiles with same user_id
        valid_profiles = [p for p in profiles_list if not p.validate()]
        assume(len(valid_profiles) >= 2)
        
        user_id = "test_user"
        for profile in valid_profiles:
            profile.user_id = user_id
        
        async def test_ordering():
            profile_ids = []
            
            # Save all profiles
            for profile in valid_profiles:
                profile_id = await settings_manager.save_profile(
                    profile.name,
                    profile.settings,
                    user_id,
                    profile.description
                )
                profile_ids.append(profile_id)
                
                # Small delay to ensure different timestamps
                await asyncio.sleep(0.01)
            
            # Load profiles in reverse order to change last_used
            for profile_id in reversed(profile_ids):
                await settings_manager.load_profile(profile_id, user_id)
                await asyncio.sleep(0.01)
            
            # Get profile listing
            profiles = await settings_manager.get_user_profiles(user_id)
            user_profiles = [p for p in profiles if not p["is_system"]]
            
            # Should be ordered by last_used (most recent first)
            # The last loaded profile should be first
            assert len(user_profiles) == len(valid_profiles)
            
            # Verify ordering by checking that last_used timestamps are in descending order
            last_used_times = [p["last_used"] for p in user_profiles]
            assert last_used_times == sorted(last_used_times, reverse=True)
        
        asyncio.run(test_ordering())
    
    @given(cinematic_profile())
    @settings(max_examples=20, deadline=10000)
    def test_system_profile_protection(self, profile_data, settings_manager):
        """Property: System profiles cannot be deleted or modified."""
        async def test_system_protection():
            # Get system profiles
            system_profiles = get_system_profiles()
            assume(len(system_profiles) > 0)
            
            system_profile = system_profiles[0]
            
            # Try to delete system profile - should fail
            delete_success = await settings_manager.delete_profile(
                system_profile.id, profile_data.user_id
            )
            assert delete_success == False
            
            # System profile should still be in listings
            profiles = await settings_manager.get_user_profiles(profile_data.user_id)
            system_ids = {p["id"] for p in profiles if p["is_system"]}
            assert system_profile.id in system_ids
        
        asyncio.run(test_system_protection())
    
    @given(cinematic_profile())
    @settings(max_examples=20, deadline=10000)
    def test_profile_validation_enforcement(self, profile_data, settings_manager):
        """Property: Invalid profiles are rejected during creation."""
        # Create invalid settings
        invalid_settings = profile_data.settings
        invalid_settings.camera_movements.intensity = 150  # Invalid: > 100
        
        async def test_validation():
            # Should raise ValueError for invalid settings
            with pytest.raises(ValueError, match="Invalid settings"):
                await settings_manager.save_profile(
                    profile_data.name,
                    invalid_settings,
                    profile_data.user_id,
                    profile_data.description
                )
        
        asyncio.run(test_validation())
    
    @given(st.text(min_size=0, max_size=0))  # Empty name
    @settings(max_examples=10, deadline=5000)
    def test_empty_profile_name_rejection(self, empty_name, settings_manager):
        """Property: Profiles with empty names are rejected."""
        async def test_empty_name():
            settings_data = CinematicSettingsModel()
            
            # Should raise ValueError for empty name
            with pytest.raises(ValueError, match="Invalid profile"):
                await settings_manager.save_profile(
                    empty_name,
                    settings_data,
                    "test_user",
                    "Test description"
                )
        
        asyncio.run(test_empty_name())
    
    @given(cinematic_profile())
    @settings(max_examples=15, deadline=10000)
    def test_default_profile_retrieval(self, profile_data, settings_manager):
        """Property: Default profile retrieval always returns valid settings."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def test_default_retrieval():
            user_id = "test_user"
            
            # Get default before any profiles exist
            default_settings = await settings_manager.get_default_profile(user_id)
            assert default_settings is not None
            assert not default_settings.validate()  # Should be valid
            
            # Save a profile as default
            profile_id = await settings_manager.save_profile(
                profile_data.name,
                profile_data.settings,
                user_id,
                profile_data.description,
                set_as_default=True
            )
            
            # Default should now be the saved profile
            new_default = await settings_manager.get_default_profile(user_id)
            assert new_default.to_dict() == profile_data.settings.to_dict()
        
        asyncio.run(test_default_retrieval())
    
    @given(st.lists(cinematic_profile(), min_size=1, max_size=5))
    @settings(max_examples=15, deadline=15000)
    def test_multi_user_profile_isolation(self, profiles_list, settings_manager):
        """Property: Profiles are isolated between different users."""
        valid_profiles = [p for p in profiles_list if not p.validate()]
        assume(len(valid_profiles) >= 1)
        
        async def test_isolation():
            user1_id = "user1"
            user2_id = "user2"
            
            user1_profile_ids = []
            user2_profile_ids = []
            
            # Save profiles for user1
            for i, profile in enumerate(valid_profiles):
                profile_id = await settings_manager.save_profile(
                    f"user1_profile_{i}",
                    profile.settings,
                    user1_id,
                    f"User 1 profile {i}"
                )
                user1_profile_ids.append(profile_id)
            
            # Save profiles for user2
            for i, profile in enumerate(valid_profiles):
                profile_id = await settings_manager.save_profile(
                    f"user2_profile_{i}",
                    profile.settings,
                    user2_id,
                    f"User 2 profile {i}"
                )
                user2_profile_ids.append(profile_id)
            
            # Get profiles for each user
            user1_profiles = await settings_manager.get_user_profiles(user1_id)
            user2_profiles = await settings_manager.get_user_profiles(user2_id)
            
            # Filter out system profiles
            user1_custom = [p for p in user1_profiles if not p["is_system"]]
            user2_custom = [p for p in user2_profiles if not p["is_system"]]
            
            # Each user should only see their own profiles
            assert len(user1_custom) == len(valid_profiles)
            assert len(user2_custom) == len(valid_profiles)
            
            user1_ids = {p["id"] for p in user1_custom}
            user2_ids = {p["id"] for p in user2_custom}
            
            # No overlap between user profiles
            assert user1_ids.isdisjoint(user2_ids)
            
            # User1 cannot load user2's profiles
            for profile_id in user2_profile_ids:
                loaded = await settings_manager.load_profile(profile_id, user1_id)
                assert loaded is None
            
            # User2 cannot load user1's profiles
            for profile_id in user1_profile_ids:
                loaded = await settings_manager.load_profile(profile_id, user2_id)
                assert loaded is None
        
        asyncio.run(test_isolation())


class ProfileManagementStateMachine(RuleBasedStateMachine):
    """Stateful property testing for profile management operations."""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CinematicSettingsManager()
        self.manager.storage = FileStorageBackend(self.temp_dir)
        self.user_profiles = {}  # user_id -> {profile_id -> profile_data}
        self.default_profiles = {}  # user_id -> profile_id
    
    profiles = Bundle('profiles')
    users = Bundle('users')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=users)
    def create_user(self):
        """Create a new user ID."""
        import uuid
        user_id = f"user_{uuid.uuid4().hex[:8]}"
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = {}
        return user_id
    
    @rule(target=profiles, user_id=users, profile_data=cinematic_profile())
    def save_profile(self, user_id, profile_data):
        """Save a profile for a user."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def save():
            try:
                profile_id = await self.manager.save_profile(
                    profile_data.name,
                    profile_data.settings,
                    user_id,
                    profile_data.description,
                    set_as_default=profile_data.is_default
                )
                
                if profile_id:
                    self.user_profiles[user_id][profile_id] = profile_data
                    if profile_data.is_default:
                        self.default_profiles[user_id] = profile_id
                
                return profile_id
            except Exception:
                return None
        
        return asyncio.run(save())
    
    @rule(user_id=users, profile_id=profiles)
    def load_profile(self, user_id, profile_id):
        """Load a profile and verify it matches saved data."""
        if (profile_id is None or 
            user_id not in self.user_profiles or 
            profile_id not in self.user_profiles[user_id]):
            return
        
        original_data = self.user_profiles[user_id][profile_id]
        
        async def load():
            loaded_settings = await self.manager.load_profile(profile_id, user_id)
            if loaded_settings is not None:
                assert loaded_settings.to_dict() == original_data.settings.to_dict()
        
        asyncio.run(load())
    
    @rule(user_id=users, profile_id=profiles)
    def delete_profile(self, user_id, profile_id):
        """Delete a profile."""
        if (profile_id is None or 
            user_id not in self.user_profiles or 
            profile_id not in self.user_profiles[user_id]):
            return
        
        async def delete():
            success = await self.manager.delete_profile(profile_id, user_id)
            if success:
                del self.user_profiles[user_id][profile_id]
                if user_id in self.default_profiles and self.default_profiles[user_id] == profile_id:
                    del self.default_profiles[user_id]
        
        asyncio.run(delete())
    
    @rule(user_id=users)
    def list_profiles(self, user_id):
        """List profiles for a user and verify completeness."""
        if user_id not in self.user_profiles:
            return
        
        async def list_and_verify():
            profiles = await self.manager.get_user_profiles(user_id)
            
            # Should include system profiles plus user profiles
            system_count = len(get_system_profiles())
            user_count = len(self.user_profiles[user_id])
            expected_count = system_count + user_count
            
            assert len(profiles) == expected_count
            
            # All user profiles should be present
            user_profile_ids = {p["id"] for p in profiles if not p["is_system"]}
            expected_ids = set(self.user_profiles[user_id].keys())
            assert user_profile_ids == expected_ids
        
        asyncio.run(list_and_verify())
    
    @invariant()
    def default_profile_uniqueness(self):
        """Invariant: Each user has at most one default profile."""
        async def check():
            for user_id in self.user_profiles:
                profiles = await self.manager.get_user_profiles(user_id)
                user_defaults = [p for p in profiles if p["is_default"] and p["user_id"] == user_id]
                assert len(user_defaults) <= 1
        
        asyncio.run(check())
    
    @invariant()
    def profile_isolation(self):
        """Invariant: Users can only access their own profiles."""
        async def check():
            for user_id in self.user_profiles:
                for other_user_id in self.user_profiles:
                    if user_id != other_user_id:
                        for profile_id in self.user_profiles[other_user_id]:
                            loaded = await self.manager.load_profile(profile_id, user_id)
                            assert loaded is None
        
        asyncio.run(check())
    
    def teardown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# Test the state machine
TestProfileManagementState = ProfileManagementStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])