"""
Default State and Initialization System

This module provides system startup logic, default profile management, and
initialization functionality for the cinematic UI enhancement system.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from .models import CinematicSettingsModel, CinematicProfileModel
from .settings_manager import CinematicSettingsManager


logger = logging.getLogger(__name__)


@dataclass
class SystemProfile:
    """System-provided default profile."""
    id: str
    name: str
    description: str
    settings: Dict[str, Any]
    category: str  # 'standard', 'professional', 'cinematic'
    is_system: bool = True
    usage_priority: int = 0  # Higher = more likely to be default


@dataclass
class InitializationConfig:
    """Configuration for system initialization."""
    profiles_directory: str = "data/cinematic/profiles"
    analytics_directory: str = "data/cinematic/analytics"
    last_used_profile_file: str = "data/cinematic/last_used.json"
    system_profiles_file: str = "data/cinematic/system_profiles.json"
    enable_analytics: bool = True
    auto_create_directories: bool = True


@dataclass
class ProfileUsageAnalytics:
    """Analytics data for profile usage tracking."""
    profile_id: str
    usage_count: int
    last_used: str
    total_time_used: float  # seconds
    feature_usage: Dict[str, int]  # feature -> usage count
    created_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProfileUsageAnalytics':
        """Create from dictionary."""
        return cls(**data)


class DefaultStateManager:
    """Manages default states and system initialization."""
    
    def __init__(self, config: Optional[InitializationConfig] = None):
        self.config = config or InitializationConfig()
        self.settings_manager = None
        self.system_profiles = {}
        self.analytics_data = {}
        self._initialized = False
    
    async def initialize(self, settings_manager: CinematicSettingsManager):
        """
        Initialize the system with default profiles and settings.
        
        Args:
            settings_manager: CinematicSettingsManager instance
        """
        self.settings_manager = settings_manager
        
        try:
            # Create necessary directories
            if self.config.auto_create_directories:
                await self._create_directories()
            
            # Load system profiles
            await self._load_system_profiles()
            
            # Load analytics data
            if self.config.enable_analytics:
                await self._load_analytics_data()
            
            # Ensure system profiles exist
            await self._ensure_system_profiles_exist()
            
            self._initialized = True
            logger.info("Cinematic initialization system initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize cinematic system: {e}")
            raise
    
    async def _create_directories(self):
        """Create necessary directories for the system."""
        directories = [
            self.config.profiles_directory,
            self.config.analytics_directory,
            os.path.dirname(self.config.last_used_profile_file),
            os.path.dirname(self.config.system_profiles_file)
        ]
        
        for directory in directories:
            if directory:
                Path(directory).mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {directory}")
    
    async def _load_system_profiles(self):
        """Load system-provided profiles."""
        try:
            if os.path.exists(self.config.system_profiles_file):
                with open(self.config.system_profiles_file, 'r') as f:
                    data = json.load(f)
                    
                for profile_data in data.get('profiles', []):
                    profile = SystemProfile(**profile_data)
                    self.system_profiles[profile.id] = profile
                    
                logger.info(f"Loaded {len(self.system_profiles)} system profiles")
            else:
                logger.info("No existing system profiles file found, will create defaults")
                
        except Exception as e:
            logger.error(f"Failed to load system profiles: {e}")
            # Continue with empty profiles, will create defaults
    
    async def _load_analytics_data(self):
        """Load profile usage analytics."""
        analytics_file = os.path.join(self.config.analytics_directory, "profile_usage.json")
        
        try:
            if os.path.exists(analytics_file):
                with open(analytics_file, 'r') as f:
                    data = json.load(f)
                    
                for profile_id, analytics_dict in data.items():
                    self.analytics_data[profile_id] = ProfileUsageAnalytics.from_dict(analytics_dict)
                    
                logger.info(f"Loaded analytics for {len(self.analytics_data)} profiles")
            else:
                logger.info("No existing analytics data found")
                
        except Exception as e:
            logger.error(f"Failed to load analytics data: {e}")
            # Continue without analytics
    
    async def _ensure_system_profiles_exist(self):
        """Ensure all required system profiles exist."""
        required_profiles = [
            self._create_standard_profile(),
            self._create_professional_profile(),
            self._create_cinematic_profile()
        ]
        
        profiles_created = 0
        
        for system_profile in required_profiles:
            if system_profile.id not in self.system_profiles:
                # Create the profile in settings manager
                try:
                    profile_id = await self.settings_manager.save_profile(
                        profile_name=system_profile.name,
                        settings=system_profile.settings,
                        user_id="system",
                        set_as_default=False
                    )
                    
                    # Store system profile reference
                    self.system_profiles[system_profile.id] = system_profile
                    profiles_created += 1
                    
                    logger.info(f"Created system profile: {system_profile.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to create system profile {system_profile.name}: {e}")
        
        if profiles_created > 0:
            await self._save_system_profiles()
            logger.info(f"Created {profiles_created} new system profiles")
    
    def _create_standard_profile(self) -> SystemProfile:
        """Create the Standard HD profile."""
        return SystemProfile(
            id="standard_hd",
            name="Standard HD",
            description="Balanced settings for general content creation with good quality and reasonable processing time",
            category="standard",
            usage_priority=100,
            settings={
                "camera_movements": {
                    "enabled": True,
                    "allowed_types": ["static", "pan", "zoom"],
                    "intensity": 30,
                    "auto_select": True
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": "none",
                    "temperature": 0,
                    "tint": 0,
                    "contrast": 10,
                    "saturation": 0,
                    "brightness": 0,
                    "shadows": 0,
                    "highlights": 0,
                    "auto_adjust": True
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "spatial_audio": False,
                    "reverb_intensity": 20,
                    "eq_processing": True,
                    "dynamic_range_compression": True,
                    "auto_select_music": True
                },
                "advanced_compositing": {
                    "enabled": False,
                    "film_grain": False,
                    "dynamic_lighting": False,
                    "depth_of_field": False,
                    "motion_blur": False,
                    "professional_transitions": True,
                    "lut_application": False
                },
                "quality_preset": "standard_hd",
                "auto_recommendations": True
            }
        )
    
    def _create_professional_profile(self) -> SystemProfile:
        """Create the Professional profile."""
        return SystemProfile(
            id="professional",
            name="Professional",
            description="Enhanced settings for professional content with advanced features and higher quality output",
            category="professional",
            usage_priority=75,
            settings={
                "camera_movements": {
                    "enabled": True,
                    "allowed_types": ["static", "pan", "zoom", "dolly"],
                    "intensity": 50,
                    "auto_select": True
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": "cinema",
                    "temperature": 5,
                    "tint": 0,
                    "contrast": 15,
                    "saturation": 5,
                    "brightness": 5,
                    "shadows": -5,
                    "highlights": -5,
                    "auto_adjust": True
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "spatial_audio": True,
                    "reverb_intensity": 30,
                    "eq_processing": True,
                    "dynamic_range_compression": True,
                    "auto_select_music": True
                },
                "advanced_compositing": {
                    "enabled": True,
                    "film_grain": True,
                    "dynamic_lighting": True,
                    "depth_of_field": False,
                    "motion_blur": False,
                    "professional_transitions": True,
                    "lut_application": True
                },
                "quality_preset": "cinematic_4k",
                "auto_recommendations": True
            }
        )
    
    def _create_cinematic_profile(self) -> SystemProfile:
        """Create the Cinematic profile."""
        return SystemProfile(
            id="cinematic",
            name="Cinematic",
            description="Maximum quality settings for cinematic production with all advanced features enabled",
            category="cinematic",
            usage_priority=50,
            settings={
                "camera_movements": {
                    "enabled": True,
                    "allowed_types": ["static", "pan", "zoom", "dolly", "crane", "handheld"],
                    "intensity": 70,
                    "auto_select": True
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": "kodak",
                    "temperature": 10,
                    "tint": 2,
                    "contrast": 20,
                    "saturation": 10,
                    "brightness": 5,
                    "shadows": -10,
                    "highlights": -10,
                    "auto_adjust": False
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "spatial_audio": True,
                    "reverb_intensity": 40,
                    "eq_processing": True,
                    "dynamic_range_compression": False,
                    "auto_select_music": False
                },
                "advanced_compositing": {
                    "enabled": True,
                    "film_grain": True,
                    "dynamic_lighting": True,
                    "depth_of_field": True,
                    "motion_blur": True,
                    "professional_transitions": True,
                    "lut_application": True
                },
                "quality_preset": "cinematic_8k",
                "auto_recommendations": False
            }
        )
    
    async def _save_system_profiles(self):
        """Save system profiles to file."""
        try:
            profiles_data = {
                "profiles": [asdict(profile) for profile in self.system_profiles.values()],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            with open(self.config.system_profiles_file, 'w') as f:
                json.dump(profiles_data, f, indent=2)
                
            logger.debug("Saved system profiles to file")
            
        except Exception as e:
            logger.error(f"Failed to save system profiles: {e}")
    
    async def get_startup_profile(self, user_id: str = "default") -> Optional[str]:
        """
        Get the profile to load at system startup.
        
        Args:
            user_id: User identifier
            
        Returns:
            Profile ID to load, or None if no suitable profile found
        """
        if not self._initialized:
            raise RuntimeError("Initialization system not initialized")
        
        try:
            # Try to load last used profile
            last_used_profile = await self._get_last_used_profile(user_id)
            if last_used_profile:
                # Verify profile still exists
                try:
                    profile = await self.settings_manager.load_profile(last_used_profile, user_id)
                    if profile:
                        logger.info(f"Loading last used profile: {last_used_profile}")
                        return last_used_profile
                except Exception:
                    logger.warning(f"Last used profile {last_used_profile} no longer exists")
            
            # Fall back to most used profile based on analytics
            if self.config.enable_analytics:
                most_used_profile = await self._get_most_used_profile(user_id)
                if most_used_profile:
                    logger.info(f"Loading most used profile: {most_used_profile}")
                    return most_used_profile
            
            # Fall back to default system profile
            default_profile = await self._get_default_system_profile()
            if default_profile:
                logger.info(f"Loading default system profile: {default_profile}")
                return default_profile
            
            logger.warning("No suitable startup profile found")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get startup profile: {e}")
            return None
    
    async def _get_last_used_profile(self, user_id: str) -> Optional[str]:
        """Get the last used profile for a user."""
        try:
            if os.path.exists(self.config.last_used_profile_file):
                with open(self.config.last_used_profile_file, 'r') as f:
                    data = json.load(f)
                    return data.get(user_id)
        except Exception as e:
            logger.debug(f"Could not load last used profile: {e}")
        
        return None
    
    async def _get_most_used_profile(self, user_id: str) -> Optional[str]:
        """Get the most used profile for a user based on analytics."""
        user_analytics = {
            profile_id: analytics for profile_id, analytics in self.analytics_data.items()
            if profile_id.startswith(f"{user_id}_") or profile_id in self.system_profiles
        }
        
        if not user_analytics:
            return None
        
        # Sort by usage count and recency
        def sort_key(item):
            profile_id, analytics = item
            recency_score = self._calculate_recency_score(analytics.last_used)
            return analytics.usage_count * recency_score
        
        sorted_profiles = sorted(user_analytics.items(), key=sort_key, reverse=True)
        return sorted_profiles[0][0] if sorted_profiles else None
    
    def _calculate_recency_score(self, last_used_str: str) -> float:
        """Calculate recency score (higher = more recent)."""
        try:
            last_used = datetime.fromisoformat(last_used_str)
            days_ago = (datetime.utcnow() - last_used).days
            
            # Exponential decay: recent usage gets higher score
            return max(0.1, 1.0 / (1.0 + days_ago * 0.1))
        except Exception:
            return 0.1
    
    async def _get_default_system_profile(self) -> Optional[str]:
        """Get the default system profile with highest priority."""
        if not self.system_profiles:
            return None
        
        # Sort by usage priority (higher = better default)
        sorted_profiles = sorted(
            self.system_profiles.values(),
            key=lambda p: p.usage_priority,
            reverse=True
        )
        
        return sorted_profiles[0].id if sorted_profiles else None
    
    async def set_last_used_profile(self, profile_id: str, user_id: str = "default"):
        """
        Set the last used profile for a user.
        
        Args:
            profile_id: Profile that was used
            user_id: User identifier
        """
        try:
            # Load existing data
            data = {}
            if os.path.exists(self.config.last_used_profile_file):
                with open(self.config.last_used_profile_file, 'r') as f:
                    data = json.load(f)
            
            # Update last used profile
            data[user_id] = profile_id
            data['last_updated'] = datetime.utcnow().isoformat()
            
            # Save updated data
            with open(self.config.last_used_profile_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            # Update analytics if enabled
            if self.config.enable_analytics:
                await self._update_profile_analytics(profile_id, user_id)
            
            logger.debug(f"Set last used profile for {user_id}: {profile_id}")
            
        except Exception as e:
            logger.error(f"Failed to set last used profile: {e}")
    
    async def _update_profile_analytics(self, profile_id: str, user_id: str):
        """Update usage analytics for a profile."""
        try:
            # Get or create analytics entry
            if profile_id not in self.analytics_data:
                self.analytics_data[profile_id] = ProfileUsageAnalytics(
                    profile_id=profile_id,
                    usage_count=0,
                    last_used=datetime.utcnow().isoformat(),
                    total_time_used=0.0,
                    feature_usage={},
                    created_at=datetime.utcnow().isoformat()
                )
            
            # Update analytics
            analytics = self.analytics_data[profile_id]
            analytics.usage_count += 1
            analytics.last_used = datetime.utcnow().isoformat()
            
            # Save analytics periodically (every 10 uses or daily)
            if analytics.usage_count % 10 == 0:
                await self._save_analytics_data()
            
        except Exception as e:
            logger.error(f"Failed to update profile analytics: {e}")
    
    async def _save_analytics_data(self):
        """Save analytics data to file."""
        try:
            analytics_file = os.path.join(self.config.analytics_directory, "profile_usage.json")
            
            data = {
                profile_id: analytics.to_dict()
                for profile_id, analytics in self.analytics_data.items()
            }
            
            with open(analytics_file, 'w') as f:
                json.dump(data, f, indent=2)
            
            logger.debug("Saved profile analytics data")
            
        except Exception as e:
            logger.error(f"Failed to save analytics data: {e}")
    
    async def restore_default_settings(self, user_id: str = "default") -> str:
        """
        Restore system to recommended default settings.
        
        Args:
            user_id: User identifier
            
        Returns:
            Profile ID of the restored default profile
        """
        if not self._initialized:
            raise RuntimeError("Initialization system not initialized")
        
        try:
            # Get the highest priority system profile
            default_profile_id = await self._get_default_system_profile()
            if not default_profile_id:
                raise RuntimeError("No default system profile available")
            
            # Get the system profile settings
            system_profile = self.system_profiles[default_profile_id]
            
            # Create a new user profile based on system defaults
            restored_profile_id = await self.settings_manager.save_profile(
                profile_name=f"Restored Defaults ({datetime.now().strftime('%Y-%m-%d %H-%M')})",  # Use dash instead of colon for Windows compatibility
                settings=system_profile.settings,
                user_id=user_id,
                set_as_default=True
            )
            
            # Set as last used profile
            await self.set_last_used_profile(restored_profile_id, user_id)
            
            logger.info(f"Restored default settings for user {user_id}: {restored_profile_id}")
            return restored_profile_id
            
        except Exception as e:
            logger.error(f"Failed to restore default settings: {e}")
            raise
    
    async def get_system_profiles(self) -> List[SystemProfile]:
        """Get all available system profiles."""
        return list(self.system_profiles.values())
    
    async def get_profile_analytics(self, profile_id: str) -> Optional[ProfileUsageAnalytics]:
        """Get analytics data for a specific profile."""
        return self.analytics_data.get(profile_id)
    
    async def get_user_analytics_summary(self, user_id: str) -> Dict[str, Any]:
        """Get analytics summary for a user."""
        user_analytics = {
            profile_id: analytics for profile_id, analytics in self.analytics_data.items()
            if profile_id.startswith(f"{user_id}_") or profile_id in self.system_profiles
        }
        
        if not user_analytics:
            return {
                "total_profiles": 0,
                "total_usage": 0,
                "most_used_profile": None,
                "last_activity": None
            }
        
        total_usage = sum(analytics.usage_count for analytics in user_analytics.values())
        most_used = max(user_analytics.items(), key=lambda x: x[1].usage_count)
        last_activity = max(
            (analytics.last_used for analytics in user_analytics.values()),
            default=None
        )
        
        return {
            "total_profiles": len(user_analytics),
            "total_usage": total_usage,
            "most_used_profile": {
                "id": most_used[0],
                "usage_count": most_used[1].usage_count
            },
            "last_activity": last_activity
        }


# Global initialization system instance
_initialization_system = None


async def get_initialization_system(config: Optional[InitializationConfig] = None) -> DefaultStateManager:
    """Get or create the global initialization system instance."""
    global _initialization_system
    
    if _initialization_system is None:
        _initialization_system = DefaultStateManager(config)
    
    return _initialization_system


async def initialize_cinematic_system(
    settings_manager: CinematicSettingsManager,
    config: Optional[InitializationConfig] = None
) -> DefaultStateManager:
    """
    Initialize the complete cinematic system with defaults.
    
    Args:
        settings_manager: CinematicSettingsManager instance
        config: Optional initialization configuration
        
    Returns:
        Initialized DefaultStateManager
    """
    init_system = await get_initialization_system(config)
    await init_system.initialize(settings_manager)
    return init_system