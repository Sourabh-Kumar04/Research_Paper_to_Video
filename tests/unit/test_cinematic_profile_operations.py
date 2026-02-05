"""
Property tests for cinematic profile operations.
Tests profile import/export, recommendations, and advanced operations.
"""

import pytest
import asyncio
import tempfile
import shutil
import json
from pathlib import Path
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from datetime import datetime

from src.cinematic.models import (
    CinematicSettingsModel, CinematicProfileModel, VisualDescriptionModel,
    CameraMovementType, FilmEmulationType, QualityPresetType
)
from src.cinematic.settings_manager import CinematicSettingsManager, FileStorageBackend

# Import strategies from other test files
from tests.test_cinematic_settings_persistence import (
    cinematic_settings, cinematic_profile, visual_description
)


class TestProfileOperations:
    """Test advanced profile operations like import/export and recommendations."""
    
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
    
    @given(cinematic_profile())
    @settings(max_examples=20, deadline=10000)
    def test_export_import_data_integrity(self, profile_data, settings_manager):
        """Property: Export/import preserves all profile data except metadata."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def test_integrity():
            # Save original profile
            original_id = await settings_manager.save_profile(
                profile_data.name,
                profile_data.settings,
                profile_data.user_id,
                profile_data.description
            )
            
            # Export profile
            exported_json = await settings_manager.export_profile(original_id, profile_data.user_id)
            assert exported_json is not None
            
            # Verify export format
            export_data = json.loads(exported_json)
            assert "format_version" in export_data
            assert "exported_at" in export_data
            assert "profile" in export_data
            
            # Import to different user
            new_user_id = "imported_user"
            imported_id = await settings_manager.import_profile(exported_json, new_user_id)
            assert imported_id is not None
            assert imported_id != original_id  # Should get new ID
            
            # Load both profiles
            original_settings = await settings_manager.load_profile(original_id, profile_data.user_id)
            imported_settings = await settings_manager.load_profile(imported_id, new_user_id)
            
            # Settings should be identical
            assert original_settings.to_dict() == imported_settings.to_dict()
            
            # Verify imported profile metadata
            imported_profiles = await settings_manager.get_user_profiles(new_user_id)
            imported_profile = next(p for p in imported_profiles if p["id"] == imported_id)
            
            assert imported_profile["name"] == profile_data.name
            assert imported_profile["description"] == profile_data.description
            assert imported_profile["user_id"] == new_user_id
            assert imported_profile["is_system"] == False
            assert imported_profile["usage_count"] == 0
        
        asyncio.run(test_integrity())
    
    @given(st.text())
    @settings(max_examples=10, deadline=5000)
    def test_invalid_import_rejection(self, invalid_json, settings_manager):
        """Property: Invalid import data is rejected gracefully."""
        assume(invalid_json.strip() != "")  # Not empty
        
        async def test_rejection():
            # Should return None for invalid data
            result = await settings_manager.import_profile(invalid_json, "test_user")
            assert result is None
        
        asyncio.run(test_rejection())
    
    @given(st.dictionaries(
        st.sampled_from(["mood", "complexity", "pacing", "focus_type"]),
        st.sampled_from(["exciting", "analytical", "serious", "welcoming", "neutral", 
                        "high", "medium", "low", "mathematical", "architectural", "general"])
    ))
    @settings(max_examples=30, deadline=10000)
    def test_recommendation_consistency(self, scene_analysis, settings_manager):
        """Property: Recommendations are consistent for identical scene analysis."""
        async def test_consistency():
            # Get recommendations multiple times
            recommendations = []
            for _ in range(3):
                rec = await settings_manager.get_recommendations(scene_analysis)
                recommendations.append(rec)
            
            # All recommendations should be identical
            first_rec = recommendations[0].to_dict()
            for rec in recommendations[1:]:
                assert rec.to_dict() == first_rec
            
            # Recommendations should be valid
            validation = await settings_manager.validate_settings(recommendations[0])
            assert validation["valid"] == True
        
        asyncio.run(test_consistency())
    
    @given(st.dictionaries(
        st.sampled_from(["mood", "complexity", "pacing", "focus_type"]),
        st.text()
    ))
    @settings(max_examples=20, deadline=10000)
    def test_recommendation_robustness(self, invalid_analysis, settings_manager):
        """Property: Recommendation system handles invalid analysis gracefully."""
        async def test_robustness():
            # Should return valid settings even with invalid analysis
            recommendations = await settings_manager.get_recommendations(invalid_analysis)
            assert recommendations is not None
            
            # Should be valid settings
            validation = await settings_manager.validate_settings(recommendations)
            assert validation["valid"] == True
        
        asyncio.run(test_robustness())
    
    @given(visual_description())
    @settings(max_examples=20, deadline=10000)
    def test_visual_description_operations(self, desc_data, settings_manager):
        """Property: Visual description save/load operations preserve data."""
        async def test_visual_desc():
            # Save visual description
            save_success = await settings_manager.save_visual_description(
                desc_data.scene_id,
                desc_data.content,
                desc_data.description,
                desc_data.generated_by,
                desc_data.cinematic_settings,
                desc_data.scene_analysis,
                desc_data.suggestions,
                desc_data.confidence
            )
            assert save_success == True
            
            # Load visual description
            loaded_desc = await settings_manager.load_visual_description(desc_data.scene_id)
            assert loaded_desc is not None
            
            # Verify all data is preserved
            assert loaded_desc.scene_id == desc_data.scene_id
            assert loaded_desc.content == desc_data.content
            assert loaded_desc.description == desc_data.description
            assert loaded_desc.generated_by == desc_data.generated_by
            assert loaded_desc.cinematic_settings == desc_data.cinematic_settings
            assert loaded_desc.scene_analysis == desc_data.scene_analysis
            assert loaded_desc.suggestions == desc_data.suggestions
            assert loaded_desc.confidence == desc_data.confidence
        
        asyncio.run(test_visual_desc())
    
    @given(cinematic_profile())
    @settings(max_examples=15, deadline=10000)
    def test_profile_export_format_compliance(self, profile_data, settings_manager):
        """Property: Exported profiles follow the expected JSON format."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def test_format():
            # Save profile
            profile_id = await settings_manager.save_profile(
                profile_data.name,
                profile_data.settings,
                profile_data.user_id,
                profile_data.description
            )
            
            # Export profile
            exported_json = await settings_manager.export_profile(profile_id, profile_data.user_id)
            assert exported_json is not None
            
            # Parse and validate format
            export_data = json.loads(exported_json)
            
            # Required top-level fields
            assert "format_version" in export_data
            assert "exported_at" in export_data
            assert "profile" in export_data
            
            # Validate format version
            assert export_data["format_version"] == "1.0"
            
            # Validate timestamp format
            exported_at = export_data["exported_at"]
            datetime.fromisoformat(exported_at.replace('Z', '+00:00'))  # Should not raise
            
            # Validate profile structure
            profile = export_data["profile"]
            required_profile_fields = [
                "id", "name", "description", "settings", "user_id",
                "is_default", "is_system", "created_at", "last_used", "usage_count"
            ]
            for field in required_profile_fields:
                assert field in profile
            
            # Validate settings structure
            settings = profile["settings"]
            required_settings_fields = [
                "camera_movements", "color_grading", "sound_design",
                "advanced_compositing", "quality_preset", "auto_recommendations"
            ]
            for field in required_settings_fields:
                assert field in settings
        
        asyncio.run(test_format())
    
    @given(st.lists(cinematic_profile(), min_size=2, max_size=5))
    @settings(max_examples=10, deadline=15000)
    def test_bulk_export_import_operations(self, profiles_list, settings_manager):
        """Property: Multiple profiles can be exported and imported correctly."""
        valid_profiles = [p for p in profiles_list if not p.validate()]
        assume(len(valid_profiles) >= 2)
        
        # Ensure unique names
        for i, profile in enumerate(valid_profiles):
            profile.name = f"profile_{i}_{profile.name}"
            profile.user_id = "source_user"
        
        async def test_bulk_operations():
            # Save all profiles
            original_ids = []
            for profile in valid_profiles:
                profile_id = await settings_manager.save_profile(
                    profile.name,
                    profile.settings,
                    profile.user_id,
                    profile.description
                )
                original_ids.append(profile_id)
            
            # Export all profiles
            exported_data = []
            for profile_id in original_ids:
                exported_json = await settings_manager.export_profile(profile_id, "source_user")
                assert exported_json is not None
                exported_data.append(exported_json)
            
            # Import all profiles to new user
            target_user = "target_user"
            imported_ids = []
            for exported_json in exported_data:
                imported_id = await settings_manager.import_profile(exported_json, target_user)
                assert imported_id is not None
                imported_ids.append(imported_id)
            
            # Verify all profiles imported correctly
            target_profiles = await settings_manager.get_user_profiles(target_user)
            imported_profiles = [p for p in target_profiles if not p["is_system"]]
            
            assert len(imported_profiles) == len(valid_profiles)
            
            # Verify settings match
            for i, profile in enumerate(valid_profiles):
                imported_settings = await settings_manager.load_profile(imported_ids[i], target_user)
                assert imported_settings.to_dict() == profile.settings.to_dict()
        
        asyncio.run(test_bulk_operations())
    
    @given(cinematic_profile())
    @settings(max_examples=15, deadline=10000)
    def test_profile_validation_during_operations(self, profile_data, settings_manager):
        """Property: Profile validation is enforced during all operations."""
        # Make profile invalid
        profile_data.settings.camera_movements.intensity = 150  # Invalid
        
        async def test_validation():
            # Save should fail
            with pytest.raises(ValueError):
                await settings_manager.save_profile(
                    profile_data.name,
                    profile_data.settings,
                    profile_data.user_id,
                    profile_data.description
                )
            
            # Create valid profile for export test
            valid_settings = CinematicSettingsModel()
            profile_id = await settings_manager.save_profile(
                "valid_profile",
                valid_settings,
                profile_data.user_id,
                "Valid profile"
            )
            
            # Export valid profile
            exported_json = await settings_manager.export_profile(profile_id, profile_data.user_id)
            
            # Corrupt the exported data
            export_data = json.loads(exported_json)
            export_data["profile"]["settings"]["camera_movements"]["intensity"] = 150
            corrupted_json = json.dumps(export_data)
            
            # Import should fail
            imported_id = await settings_manager.import_profile(corrupted_json, "test_user")
            assert imported_id is None
        
        asyncio.run(test_validation())


class ProfileOperationsStateMachine(RuleBasedStateMachine):
    """Stateful property testing for profile operations."""
    
    def __init__(self):
        super().__init__()
        self.temp_dir = tempfile.mkdtemp()
        self.manager = CinematicSettingsManager()
        self.manager.storage = FileStorageBackend(self.temp_dir)
        self.profiles = {}  # profile_id -> (user_id, profile_data)
        self.exported_data = {}  # export_id -> json_data
        self.visual_descriptions = {}  # scene_id -> description_data
    
    profiles = Bundle('profiles')
    exports = Bundle('exports')
    descriptions = Bundle('descriptions')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=profiles, profile_data=cinematic_profile())
    def save_profile(self, profile_data):
        """Save a profile."""
        assume(not profile_data.validate())  # Only valid profiles
        
        async def save():
            try:
                profile_id = await self.manager.save_profile(
                    profile_data.name,
                    profile_data.settings,
                    profile_data.user_id,
                    profile_data.description
                )
                if profile_id:
                    self.profiles[profile_id] = (profile_data.user_id, profile_data)
                return profile_id
            except Exception:
                return None
        
        return asyncio.run(save())
    
    @rule(target=exports, profile_id=profiles)
    def export_profile(self, profile_id):
        """Export a profile."""
        if profile_id is None or profile_id not in self.profiles:
            return None
        
        user_id, _ = self.profiles[profile_id]
        
        async def export():
            exported_json = await self.manager.export_profile(profile_id, user_id)
            if exported_json:
                export_id = f"export_{len(self.exported_data)}"
                self.exported_data[export_id] = exported_json
                return export_id
            return None
        
        return asyncio.run(export())
    
    @rule(target=profiles, export_id=exports)
    def import_profile(self, export_id):
        """Import a profile."""
        if export_id is None or export_id not in self.exported_data:
            return None
        
        exported_json = self.exported_data[export_id]
        target_user = "imported_user"
        
        async def import_profile():
            imported_id = await self.manager.import_profile(exported_json, target_user)
            if imported_id:
                # Extract original profile data from export
                export_data = json.loads(exported_json)
                profile_dict = export_data["profile"]
                profile_data = CinematicProfileModel.from_dict(profile_dict)
                profile_data.user_id = target_user  # Update user ID
                
                self.profiles[imported_id] = (target_user, profile_data)
            return imported_id
        
        return asyncio.run(import_profile())
    
    @rule(target=descriptions, desc_data=visual_description())
    def save_visual_description(self, desc_data):
        """Save a visual description."""
        async def save():
            success = await self.manager.save_visual_description(
                desc_data.scene_id,
                desc_data.content,
                desc_data.description,
                desc_data.generated_by,
                desc_data.cinematic_settings,
                desc_data.scene_analysis,
                desc_data.suggestions,
                desc_data.confidence
            )
            if success:
                self.visual_descriptions[desc_data.scene_id] = desc_data
                return desc_data.scene_id
            return None
        
        return asyncio.run(save())
    
    @rule(scene_id=descriptions)
    def load_visual_description(self, scene_id):
        """Load and verify a visual description."""
        if scene_id is None or scene_id not in self.visual_descriptions:
            return
        
        original_data = self.visual_descriptions[scene_id]
        
        async def load():
            loaded_desc = await self.manager.load_visual_description(scene_id)
            if loaded_desc:
                assert loaded_desc.scene_id == original_data.scene_id
                assert loaded_desc.content == original_data.content
                assert loaded_desc.description == original_data.description
        
        asyncio.run(load())
    
    @invariant()
    def exported_profiles_importable(self):
        """Invariant: All exported profiles should be importable."""
        async def check():
            for export_id, exported_json in self.exported_data.items():
                # Try importing to a test user
                test_user = "test_import_user"
                imported_id = await self.manager.import_profile(exported_json, test_user)
                assert imported_id is not None
        
        asyncio.run(check())
    
    @invariant()
    def visual_descriptions_loadable(self):
        """Invariant: All saved visual descriptions should be loadable."""
        async def check():
            for scene_id in self.visual_descriptions:
                loaded = await self.manager.load_visual_description(scene_id)
                assert loaded is not None
        
        asyncio.run(check())
    
    def teardown(self):
        """Clean up temporary directory."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)


# Test the state machine
TestProfileOperationsState = ProfileOperationsStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])