"""
Data models for cinematic settings management.
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Union, Any
from enum import Enum
import json
from datetime import datetime
import uuid


class CameraMovementType(Enum):
    """Camera movement types."""
    STATIC = "static"
    PAN = "pan"
    ZOOM = "zoom"
    DOLLY = "dolly"
    CRANE = "crane"
    HANDHELD = "handheld"


class FilmEmulationType(Enum):
    """Film emulation types."""
    NONE = "none"
    KODAK = "kodak"
    FUJI = "fuji"
    CINEMA = "cinema"


class QualityPresetType(Enum):
    """Quality preset types."""
    STANDARD_HD = "standard_hd"
    CINEMATIC_4K = "cinematic_4k"
    CINEMATIC_8K = "cinematic_8k"


@dataclass
class CameraMovementSettings:
    """Camera movement configuration."""
    enabled: bool = True
    allowed_types: List[CameraMovementType] = field(default_factory=lambda: list(CameraMovementType))
    intensity: int = 50  # 0-100
    auto_select: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "allowed_types": [t.value for t in self.allowed_types],
            "intensity": self.intensity,
            "auto_select": self.auto_select
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CameraMovementSettings':
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            allowed_types=[CameraMovementType(t) for t in data.get("allowed_types", [t.value for t in CameraMovementType])],
            intensity=data.get("intensity", 50),
            auto_select=data.get("auto_select", True)
        )


@dataclass
class ColorGradingSettings:
    """Color grading configuration."""
    enabled: bool = True
    film_emulation: FilmEmulationType = FilmEmulationType.NONE
    temperature: int = 0  # -100 to 100
    tint: int = 0  # -100 to 100
    contrast: int = 0  # -100 to 100
    saturation: int = 0  # -100 to 100
    brightness: int = 0  # -100 to 100
    shadows: int = 0  # -100 to 100
    highlights: int = 0  # -100 to 100
    auto_adjust: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "enabled": self.enabled,
            "film_emulation": self.film_emulation.value,
            "temperature": self.temperature,
            "tint": self.tint,
            "contrast": self.contrast,
            "saturation": self.saturation,
            "brightness": self.brightness,
            "shadows": self.shadows,
            "highlights": self.highlights,
            "auto_adjust": self.auto_adjust
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ColorGradingSettings':
        """Create from dictionary."""
        return cls(
            enabled=data.get("enabled", True),
            film_emulation=FilmEmulationType(data.get("film_emulation", "none")),
            temperature=data.get("temperature", 0),
            tint=data.get("tint", 0),
            contrast=data.get("contrast", 0),
            saturation=data.get("saturation", 0),
            brightness=data.get("brightness", 0),
            shadows=data.get("shadows", 0),
            highlights=data.get("highlights", 0),
            auto_adjust=data.get("auto_adjust", True)
        )


@dataclass
class SoundDesignSettings:
    """Sound design configuration."""
    enabled: bool = True
    ambient_audio: bool = True
    music_scoring: bool = True
    spatial_audio: bool = False
    reverb_intensity: int = 30  # 0-100
    eq_processing: bool = True
    dynamic_range_compression: bool = True
    auto_select_music: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SoundDesignSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class AdvancedCompositingSettings:
    """Advanced compositing configuration."""
    enabled: bool = True
    film_grain: bool = True
    dynamic_lighting: bool = True
    depth_of_field: bool = False
    motion_blur: bool = False
    professional_transitions: bool = True
    lut_application: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AdvancedCompositingSettings':
        """Create from dictionary."""
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class CinematicSettingsModel:
    """Complete cinematic settings configuration."""
    camera_movements: CameraMovementSettings = field(default_factory=CameraMovementSettings)
    color_grading: ColorGradingSettings = field(default_factory=ColorGradingSettings)
    sound_design: SoundDesignSettings = field(default_factory=SoundDesignSettings)
    advanced_compositing: AdvancedCompositingSettings = field(default_factory=AdvancedCompositingSettings)
    quality_preset: QualityPresetType = QualityPresetType.CINEMATIC_4K
    auto_recommendations: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "camera_movements": self.camera_movements.to_dict(),
            "color_grading": self.color_grading.to_dict(),
            "sound_design": self.sound_design.to_dict(),
            "advanced_compositing": self.advanced_compositing.to_dict(),
            "quality_preset": self.quality_preset.value,
            "auto_recommendations": self.auto_recommendations
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CinematicSettingsModel':
        """Create from dictionary."""
        return cls(
            camera_movements=CameraMovementSettings.from_dict(data.get("camera_movements", {})),
            color_grading=ColorGradingSettings.from_dict(data.get("color_grading", {})),
            sound_design=SoundDesignSettings.from_dict(data.get("sound_design", {})),
            advanced_compositing=AdvancedCompositingSettings.from_dict(data.get("advanced_compositing", {})),
            quality_preset=QualityPresetType(data.get("quality_preset", "cinematic_4k")),
            auto_recommendations=data.get("auto_recommendations", True)
        )
    
    def validate(self) -> List[str]:
        """Validate settings and return list of errors."""
        errors = []
        
        # Validate camera movement intensity
        if not (0 <= self.camera_movements.intensity <= 100):
            errors.append("Camera movement intensity must be between 0 and 100")
        
        # Validate color grading values
        color_fields = ["temperature", "tint", "contrast", "saturation", "brightness", "shadows", "highlights"]
        for field in color_fields:
            value = getattr(self.color_grading, field)
            if not (-100 <= value <= 100):
                errors.append(f"Color grading {field} must be between -100 and 100")
        
        # Validate sound design reverb intensity
        if not (0 <= self.sound_design.reverb_intensity <= 100):
            errors.append("Sound design reverb intensity must be between 0 and 100")
        
        return errors
    
    def get_default_settings() -> 'CinematicSettingsModel':
        """Get default cinematic settings."""
        return CinematicSettingsModel()


@dataclass
class VisualDescriptionModel:
    """Visual description data model."""
    scene_id: str
    content: str
    description: str
    generated_by: str  # "user", "gemini", "template"
    cinematic_settings: Dict[str, Any]
    scene_analysis: Dict[str, Any]
    suggestions: List[str]
    confidence: float
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'VisualDescriptionModel':
        """Create from dictionary."""
        return cls(**data)
    
    def update_description(self, new_description: str, generated_by: str = "user"):
        """Update the description and metadata."""
        self.description = new_description
        self.generated_by = generated_by
        self.updated_at = datetime.utcnow().isoformat()


@dataclass
class CinematicProfileModel:
    """Cinematic profile data model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    settings: CinematicSettingsModel = field(default_factory=CinematicSettingsModel)
    user_id: str = "default"
    is_default: bool = False
    is_system: bool = False  # System-provided profiles
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    last_used: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    usage_count: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "settings": self.settings.to_dict(),
            "user_id": self.user_id,
            "is_default": self.is_default,
            "is_system": self.is_system,
            "created_at": self.created_at,
            "last_used": self.last_used,
            "usage_count": self.usage_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CinematicProfileModel':
        """Create from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            settings=CinematicSettingsModel.from_dict(data.get("settings", {})),
            user_id=data.get("user_id", "default"),
            is_default=data.get("is_default", False),
            is_system=data.get("is_system", False),
            created_at=data.get("created_at", datetime.utcnow().isoformat()),
            last_used=data.get("last_used", datetime.utcnow().isoformat()),
            usage_count=data.get("usage_count", 0)
        )
    
    def mark_used(self):
        """Mark profile as used (update last_used and increment usage_count)."""
        self.last_used = datetime.utcnow().isoformat()
        self.usage_count += 1
    
    def validate(self) -> List[str]:
        """Validate profile data."""
        errors = []
        
        if not self.name or len(self.name.strip()) == 0:
            errors.append("Profile name cannot be empty")
        
        if len(self.name) > 100:
            errors.append("Profile name cannot exceed 100 characters")
        
        if len(self.description) > 500:
            errors.append("Profile description cannot exceed 500 characters")
        
        # Validate settings
        settings_errors = self.settings.validate()
        errors.extend(settings_errors)
        
        return errors


# System default profiles
def get_system_profiles() -> List[CinematicProfileModel]:
    """Get system-provided default profiles."""
    profiles = []
    
    # Standard Professional Profile
    standard_settings = CinematicSettingsModel()
    standard_settings.quality_preset = QualityPresetType.STANDARD_HD
    standard_settings.camera_movements.intensity = 30
    standard_settings.color_grading.film_emulation = FilmEmulationType.NONE
    
    profiles.append(CinematicProfileModel(
        id="system_standard",
        name="Standard Professional",
        description="Clean, professional video production with subtle cinematic elements",
        settings=standard_settings,
        is_system=True,
        is_default=True
    ))
    
    # Cinematic 4K Profile
    cinematic_settings = CinematicSettingsModel()
    cinematic_settings.quality_preset = QualityPresetType.CINEMATIC_4K
    cinematic_settings.camera_movements.intensity = 70
    cinematic_settings.color_grading.film_emulation = FilmEmulationType.KODAK
    cinematic_settings.color_grading.contrast = 15
    cinematic_settings.color_grading.saturation = 10
    cinematic_settings.advanced_compositing.film_grain = True
    
    profiles.append(CinematicProfileModel(
        id="system_cinematic",
        name="Cinematic 4K",
        description="Full cinematic production with film-like quality and professional color grading",
        settings=cinematic_settings,
        is_system=True
    ))
    
    # High-End 8K Profile
    premium_settings = CinematicSettingsModel()
    premium_settings.quality_preset = QualityPresetType.CINEMATIC_8K
    premium_settings.camera_movements.intensity = 80
    premium_settings.color_grading.film_emulation = FilmEmulationType.CINEMA
    premium_settings.color_grading.contrast = 20
    premium_settings.color_grading.saturation = 5
    premium_settings.advanced_compositing.film_grain = True
    premium_settings.advanced_compositing.depth_of_field = True
    premium_settings.advanced_compositing.motion_blur = True
    
    profiles.append(CinematicProfileModel(
        id="system_premium",
        name="Premium 8K",
        description="Ultra-high quality cinematic production with advanced visual effects",
        settings=premium_settings,
        is_system=True
    ))
    
    return profiles