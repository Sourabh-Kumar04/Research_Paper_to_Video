"""
Cinematic Settings Manager for RASO Platform
Manages cinematic settings, profiles, and validation.
"""

import os
import json
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
from datetime import datetime

from .models import (
    CinematicSettingsModel, CinematicProfileModel, VisualDescriptionModel,
    get_system_profiles
)

logger = logging.getLogger(__name__)


class CinematicSettingsValidator:
    """Validator for cinematic settings."""
    
    @staticmethod
    def validate_settings(settings: CinematicSettingsModel) -> Dict[str, Any]:
        """Validate cinematic settings and return validation result."""
        errors = settings.validate()
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": CinematicSettingsValidator._get_warnings(settings)
        }
    
    @staticmethod
    def _get_warnings(settings: CinematicSettingsModel) -> List[str]:
        """Get warnings for settings that might cause issues."""
        warnings = []
        
        # Check for potentially problematic combinations
        if settings.camera_movements.intensity > 80 and settings.advanced_compositing.motion_blur:
            warnings.append("High camera movement intensity with motion blur may cause excessive blur")
        
        if settings.color_grading.saturation > 50:
            warnings.append("Very high saturation may cause unnatural colors")
        
        if settings.color_grading.contrast > 50:
            warnings.append("Very high contrast may reduce detail visibility")
        
        if not settings.camera_movements.enabled and not settings.advanced_compositing.enabled:
            warnings.append("Disabling both camera movements and compositing may result in static video")
        
        return warnings


class StorageBackend:
    """Abstract storage backend for cinematic settings."""
    
    async def save_profile(self, profile: CinematicProfileModel) -> bool:
        """Save a profile."""
        raise NotImplementedError
    
    async def load_profile(self, profile_id: str, user_id: str) -> Optional[CinematicProfileModel]:
        """Load a profile by ID."""
        raise NotImplementedError
    
    async def list_profiles(self, user_id: str) -> List[CinematicProfileModel]:
        """List all profiles for a user."""
        raise NotImplementedError
    
    async def delete_profile(self, profile_id: str, user_id: str) -> bool:
        """Delete a profile."""
        raise NotImplementedError
    
    async def save_visual_description(self, description: VisualDescriptionModel) -> bool:
        """Save a visual description."""
        raise NotImplementedError
    
    async def load_visual_description(self, scene_id: str) -> Optional[VisualDescriptionModel]:
        """Load a visual description by scene ID."""
        raise NotImplementedError


class FileStorageBackend(StorageBackend):
    """File-based storage backend."""
    
    def __init__(self, storage_dir: str = ".kiro/cinematic"):
        self.storage_dir = Path(storage_dir)
        self.profiles_dir = self.storage_dir / "profiles"
        self.descriptions_dir = self.storage_dir / "descriptions"
        
        # Create directories if they don't exist
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.descriptions_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized file storage backend at {self.storage_dir}")
    
    async def save_profile(self, profile: CinematicProfileModel) -> bool:
        """Save a profile to file."""
        try:
            profile_file = self.profiles_dir / f"{profile.user_id}_{profile.id}.json"
            
            with open(profile_file, 'w') as f:
                json.dump(profile.to_dict(), f, indent=2)
            
            logger.info(f"Saved profile {profile.id} for user {profile.user_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving profile {profile.id}: {e}")
            return False
    
    async def load_profile(self, profile_id: str, user_id: str) -> Optional[CinematicProfileModel]:
        """Load a profile from file."""
        try:
            profile_file = self.profiles_dir / f"{user_id}_{profile_id}.json"
            
            if not profile_file.exists():
                # Check if it's a system profile
                system_profiles = get_system_profiles()
                for profile in system_profiles:
                    if profile.id == profile_id:
                        return profile
                return None
            
            with open(profile_file, 'r') as f:
                data = json.load(f)
            
            profile = CinematicProfileModel.from_dict(data)
            logger.info(f"Loaded profile {profile_id} for user {user_id}")
            return profile
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_id}: {e}")
            return None
    
    async def list_profiles(self, user_id: str) -> List[CinematicProfileModel]:
        """List all profiles for a user."""
        try:
            profiles = []
            
            # Add system profiles
            profiles.extend(get_system_profiles())
            
            # Add user profiles
            pattern = f"{user_id}_*.json"
            for profile_file in self.profiles_dir.glob(pattern):
                try:
                    with open(profile_file, 'r') as f:
                        data = json.load(f)
                    
                    profile = CinematicProfileModel.from_dict(data)
                    profiles.append(profile)
                    
                except Exception as e:
                    logger.error(f"Error loading profile file {profile_file}: {e}")
            
            # Sort by last used (most recent first)
            profiles.sort(key=lambda p: p.last_used, reverse=True)
            
            logger.info(f"Listed {len(profiles)} profiles for user {user_id}")
            return profiles
            
        except Exception as e:
            logger.error(f"Error listing profiles for user {user_id}: {e}")
            return []
    
    async def delete_profile(self, profile_id: str, user_id: str) -> bool:
        """Delete a profile."""
        try:
            # Cannot delete system profiles
            system_profile_ids = [p.id for p in get_system_profiles()]
            if profile_id in system_profile_ids:
                logger.warning(f"Cannot delete system profile {profile_id}")
                return False
            
            profile_file = self.profiles_dir / f"{user_id}_{profile_id}.json"
            
            if profile_file.exists():
                profile_file.unlink()
                logger.info(f"Deleted profile {profile_id} for user {user_id}")
                return True
            else:
                logger.warning(f"Profile {profile_id} not found for user {user_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False
    
    async def save_visual_description(self, description: VisualDescriptionModel) -> bool:
        """Save a visual description to file."""
        try:
            desc_file = self.descriptions_dir / f"{description.scene_id}.json"
            
            with open(desc_file, 'w') as f:
                json.dump(description.to_dict(), f, indent=2)
            
            logger.info(f"Saved visual description for scene {description.scene_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving visual description for scene {description.scene_id}: {e}")
            return False
    
    async def load_visual_description(self, scene_id: str) -> Optional[VisualDescriptionModel]:
        """Load a visual description from file."""
        try:
            desc_file = self.descriptions_dir / f"{scene_id}.json"
            
            if not desc_file.exists():
                return None
            
            with open(desc_file, 'r') as f:
                data = json.load(f)
            
            description = VisualDescriptionModel.from_dict(data)
            logger.info(f"Loaded visual description for scene {scene_id}")
            return description
            
        except Exception as e:
            logger.error(f"Error loading visual description for scene {scene_id}: {e}")
            return None


class CinematicSettingsManager:
    """Manages cinematic settings, profiles, and validation."""
    
    def __init__(self, storage_backend: str = "file"):
        self.validator = CinematicSettingsValidator()
        
        # Initialize storage backend
        if storage_backend == "file":
            self.storage = FileStorageBackend()
        else:
            raise ValueError(f"Unknown storage backend: {storage_backend}")
        
        logger.info(f"Initialized CinematicSettingsManager with {storage_backend} backend")
    
    async def save_profile(
        self,
        profile_name: str,
        settings: CinematicSettingsModel,
        user_id: str = "default",
        description: str = "",
        set_as_default: bool = False
    ) -> str:
        """Save cinematic settings profile."""
        try:
            # Validate settings first
            validation = self.validator.validate_settings(settings)
            if not validation["valid"]:
                raise ValueError(f"Invalid settings: {validation['errors']}")
            
            # Create profile
            profile = CinematicProfileModel(
                name=profile_name,
                description=description,
                settings=settings,
                user_id=user_id,
                is_default=set_as_default
            )
            
            # Validate profile
            profile_errors = profile.validate()
            if profile_errors:
                raise ValueError(f"Invalid profile: {profile_errors}")
            
            # If setting as default, unset other defaults
            if set_as_default:
                await self._unset_default_profiles(user_id)
            
            # Save profile
            success = await self.storage.save_profile(profile)
            if not success:
                raise RuntimeError("Failed to save profile to storage")
            
            logger.info(f"Saved profile '{profile_name}' with ID {profile.id}")
            return profile.id
            
        except Exception as e:
            logger.error(f"Error saving profile '{profile_name}': {e}")
            raise
    
    async def load_profile(
        self,
        profile_id: str,
        user_id: str = "default"
    ) -> Optional[CinematicSettingsModel]:
        """Load cinematic settings profile."""
        try:
            profile = await self.storage.load_profile(profile_id, user_id)
            if not profile:
                logger.warning(f"Profile {profile_id} not found for user {user_id}")
                return None
            
            # Mark as used
            profile.mark_used()
            await self.storage.save_profile(profile)
            
            logger.info(f"Loaded profile {profile_id} for user {user_id}")
            return profile.settings
            
        except Exception as e:
            logger.error(f"Error loading profile {profile_id}: {e}")
            return None
    
    async def get_user_profiles(
        self,
        user_id: str = "default"
    ) -> List[Dict[str, Any]]:
        """Get all profiles for a user."""
        try:
            profiles = await self.storage.list_profiles(user_id)
            
            # Convert to dict format with metadata
            profile_list = []
            for profile in profiles:
                profile_dict = profile.to_dict()
                profile_dict["validation"] = self.validator.validate_settings(profile.settings)
                profile_list.append(profile_dict)
            
            logger.info(f"Retrieved {len(profile_list)} profiles for user {user_id}")
            return profile_list
            
        except Exception as e:
            logger.error(f"Error getting profiles for user {user_id}: {e}")
            return []
    
    async def delete_profile(
        self,
        profile_id: str,
        user_id: str = "default"
    ) -> bool:
        """Delete a profile."""
        try:
            success = await self.storage.delete_profile(profile_id, user_id)
            if success:
                logger.info(f"Deleted profile {profile_id} for user {user_id}")
            return success
            
        except Exception as e:
            logger.error(f"Error deleting profile {profile_id}: {e}")
            return False
    
    async def export_profile(
        self,
        profile_id: str,
        user_id: str = "default"
    ) -> Optional[str]:
        """Export profile as JSON string."""
        try:
            profile = await self.storage.load_profile(profile_id, user_id)
            if not profile:
                return None
            
            # Create export data with metadata
            export_data = {
                "format_version": "1.0",
                "exported_at": datetime.utcnow().isoformat(),
                "profile": profile.to_dict()
            }
            
            return json.dumps(export_data, indent=2)
            
        except Exception as e:
            logger.error(f"Error exporting profile {profile_id}: {e}")
            return None
    
    async def import_profile(
        self,
        profile_data: str,
        user_id: str = "default"
    ) -> Optional[str]:
        """Import profile from JSON string."""
        try:
            data = json.loads(profile_data)
            
            # Validate format
            if "profile" not in data:
                raise ValueError("Invalid profile format: missing 'profile' field")
            
            # Create profile from imported data
            profile_dict = data["profile"]
            profile_dict["user_id"] = user_id  # Override user ID
            profile_dict["id"] = None  # Generate new ID
            profile_dict["is_system"] = False  # Imported profiles are not system profiles
            
            profile = CinematicProfileModel.from_dict(profile_dict)
            
            # Validate profile
            profile_errors = profile.validate()
            if profile_errors:
                raise ValueError(f"Invalid imported profile: {profile_errors}")
            
            # Save profile
            success = await self.storage.save_profile(profile)
            if not success:
                raise RuntimeError("Failed to save imported profile")
            
            logger.info(f"Imported profile '{profile.name}' with ID {profile.id}")
            return profile.id
            
        except Exception as e:
            logger.error(f"Error importing profile: {e}")
            return None
    
    async def get_default_profile(self, user_id: str = "default") -> CinematicSettingsModel:
        """Get the default profile for a user."""
        try:
            profiles = await self.storage.list_profiles(user_id)
            
            # Look for user's default profile
            for profile in profiles:
                if profile.is_default and profile.user_id == user_id:
                    return profile.settings
            
            # Look for system default profile
            for profile in profiles:
                if profile.is_default and profile.is_system:
                    return profile.settings
            
            # Return system default if no default found
            system_profiles = get_system_profiles()
            if system_profiles:
                return system_profiles[0].settings
            
            # Fallback to new default settings
            return CinematicSettingsModel()
            
        except Exception as e:
            logger.error(f"Error getting default profile for user {user_id}: {e}")
            return CinematicSettingsModel()
    
    async def validate_settings(
        self,
        settings: CinematicSettingsModel
    ) -> Dict[str, Any]:
        """Validate cinematic settings and return validation result."""
        return self.validator.validate_settings(settings)
    
    async def get_recommendations(
        self,
        scene_analysis: Dict[str, Any]
    ) -> CinematicSettingsModel:
        """Get cinematic setting recommendations based on scene analysis."""
        try:
            # Start with default settings
            settings = CinematicSettingsModel()
            
            # Adjust based on scene analysis
            mood = scene_analysis.get("mood", "neutral")
            complexity = scene_analysis.get("complexity", "medium")
            pacing = scene_analysis.get("pacing", "medium")
            focus_type = scene_analysis.get("focus_type", "general")
            
            # Adjust camera movement based on analysis
            if mood == "exciting":
                settings.camera_movements.intensity = 80
                settings.camera_movements.allowed_types = [
                    CameraMovementType.CRANE, CameraMovementType.DOLLY, CameraMovementType.ZOOM
                ]
            elif mood == "analytical":
                settings.camera_movements.intensity = 40
                settings.camera_movements.allowed_types = [
                    CameraMovementType.PAN, CameraMovementType.DOLLY
                ]
            elif complexity == "high":
                settings.camera_movements.intensity = 30  # Less movement for complex content
            
            # Adjust color grading based on analysis
            if mood == "serious":
                settings.color_grading.film_emulation = FilmEmulationType.CINEMA
                settings.color_grading.temperature = -10  # Cooler
                settings.color_grading.contrast = 20
            elif mood == "welcoming":
                settings.color_grading.film_emulation = FilmEmulationType.KODAK
                settings.color_grading.temperature = 20  # Warmer
                settings.color_grading.brightness = 10
            elif focus_type == "mathematical":
                settings.color_grading.contrast = 30  # High contrast for clarity
                settings.color_grading.saturation = -20  # Desaturated
            
            # Adjust sound design
            if complexity == "high":
                settings.sound_design.music_scoring = False  # Less distraction
                settings.sound_design.reverb_intensity = 20
            elif mood == "exciting":
                settings.sound_design.reverb_intensity = 50
            
            logger.info(f"Generated recommendations for {mood} mood, {complexity} complexity")
            return settings
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {e}")
            return CinematicSettingsModel()  # Return default on error
    
    async def save_visual_description(
        self,
        scene_id: str,
        content: str,
        description: str,
        generated_by: str,
        cinematic_settings: Dict[str, Any],
        scene_analysis: Dict[str, Any],
        suggestions: List[str] = None,
        confidence: float = 1.0
    ) -> bool:
        """Save a visual description."""
        try:
            visual_desc = VisualDescriptionModel(
                scene_id=scene_id,
                content=content,
                description=description,
                generated_by=generated_by,
                cinematic_settings=cinematic_settings,
                scene_analysis=scene_analysis,
                suggestions=suggestions or [],
                confidence=confidence
            )
            
            return await self.storage.save_visual_description(visual_desc)
            
        except Exception as e:
            logger.error(f"Error saving visual description for scene {scene_id}: {e}")
            return False
    
    async def load_visual_description(self, scene_id: str) -> Optional[VisualDescriptionModel]:
        """Load a visual description."""
        return await self.storage.load_visual_description(scene_id)
    
    async def _unset_default_profiles(self, user_id: str):
        """Unset default flag for all user profiles."""
        try:
            profiles = await self.storage.list_profiles(user_id)
            for profile in profiles:
                if profile.is_default and profile.user_id == user_id:
                    profile.is_default = False
                    await self.storage.save_profile(profile)
        except Exception as e:
            logger.error(f"Error unsetting default profiles for user {user_id}: {e}")


# Global settings manager instance
_settings_manager = None

def get_settings_manager() -> CinematicSettingsManager:
    """Get global settings manager instance."""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = CinematicSettingsManager()
    return _settings_manager