"""
API models for cinematic features.
Pydantic models for request/response validation.
"""

from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any, Union
from datetime import datetime


class CinematicSettingsRequest(BaseModel):
    """Request model for cinematic settings validation."""
    settings: Dict[str, Any] = Field(..., description="Cinematic settings dictionary")
    
    class Config:
        schema_extra = {
            "example": {
                "settings": {
                    "camera_movements": {
                        "enabled": True,
                        "allowed_types": ["pan", "zoom"],
                        "intensity": 70,
                        "auto_select": True
                    },
                    "color_grading": {
                        "enabled": True,
                        "film_emulation": "kodak",
                        "temperature": 10,
                        "contrast": 15
                    },
                    "quality_preset": "cinematic_4k"
                }
            }
        }


class CinematicSettingsResponse(BaseModel):
    """Response model for cinematic settings."""
    settings: Dict[str, Any] = Field(..., description="Cinematic settings dictionary")
    profile_id: str = Field(..., description="Profile ID")
    user_id: str = Field(..., description="User ID")
    
    class Config:
        schema_extra = {
            "example": {
                "settings": {
                    "camera_movements": {
                        "enabled": True,
                        "allowed_types": ["pan", "zoom"],
                        "intensity": 70
                    }
                },
                "profile_id": "profile_123",
                "user_id": "user_456"
            }
        }


class CinematicProfileRequest(BaseModel):
    """Request model for creating/updating cinematic profiles."""
    name: str = Field(..., min_length=1, max_length=100, description="Profile name")
    description: str = Field("", max_length=500, description="Profile description")
    settings: Dict[str, Any] = Field(..., description="Cinematic settings dictionary")
    user_id: str = Field("default", description="User ID")
    set_as_default: bool = Field(False, description="Set as default profile")
    
    @validator('name')
    def name_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Profile name cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Cinematic 4K",
                "description": "High-quality cinematic production settings",
                "settings": {
                    "camera_movements": {"enabled": True, "intensity": 70},
                    "color_grading": {"enabled": True, "film_emulation": "kodak"},
                    "quality_preset": "cinematic_4k"
                },
                "user_id": "user_123",
                "set_as_default": False
            }
        }


class CinematicProfileResponse(BaseModel):
    """Response model for cinematic profiles."""
    id: str = Field(..., description="Profile ID")
    name: str = Field(..., description="Profile name")
    description: str = Field(..., description="Profile description")
    settings: Dict[str, Any] = Field(..., description="Cinematic settings")
    user_id: str = Field(..., description="User ID")
    is_default: bool = Field(..., description="Is default profile")
    is_system: bool = Field(..., description="Is system profile")
    created_at: str = Field(..., description="Creation timestamp")
    last_used: str = Field(..., description="Last used timestamp")
    usage_count: int = Field(..., description="Usage count")
    validation: Dict[str, Any] = Field(..., description="Validation results")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "profile_123",
                "name": "Cinematic 4K",
                "description": "High-quality settings",
                "settings": {"quality_preset": "cinematic_4k"},
                "user_id": "user_123",
                "is_default": False,
                "is_system": False,
                "created_at": "2024-01-01T00:00:00Z",
                "last_used": "2024-01-01T00:00:00Z",
                "usage_count": 5,
                "validation": {"valid": True, "errors": [], "warnings": []}
            }
        }


class VisualDescriptionRequest(BaseModel):
    """Request model for visual description generation."""
    scene_id: str = Field(..., min_length=1, description="Scene identifier")
    content: str = Field(..., min_length=1, description="Content to describe")
    scene_context: Optional[Dict[str, Any]] = Field(None, description="Scene context information")
    style_preferences: Optional[Dict[str, Any]] = Field(None, description="Style preferences")
    
    @validator('scene_id', 'content')
    def fields_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "scene_id": "scene_001",
                "content": "A mathematical equation explaining quantum mechanics",
                "scene_context": {
                    "subject": "physics",
                    "complexity": "advanced",
                    "audience": "university"
                },
                "style_preferences": {
                    "mood": "analytical",
                    "pacing": "medium"
                }
            }
        }


class VisualDescriptionResponse(BaseModel):
    """Response model for visual descriptions."""
    scene_id: str = Field(..., description="Scene identifier")
    description: str = Field(..., description="Generated visual description")
    scene_analysis: Dict[str, Any] = Field(..., description="Scene analysis results")
    cinematic_recommendations: Dict[str, Any] = Field(..., description="Recommended cinematic settings")
    suggestions: List[str] = Field(..., description="Improvement suggestions")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    generated_by: str = Field(..., description="Generation method")
    
    class Config:
        schema_extra = {
            "example": {
                "scene_id": "scene_001",
                "description": "A clean, well-lit scene showing mathematical equations...",
                "scene_analysis": {
                    "mood": "analytical",
                    "complexity": "high",
                    "focus_type": "mathematical"
                },
                "cinematic_recommendations": {
                    "camera_movements": {"intensity": 30},
                    "color_grading": {"contrast": 30}
                },
                "suggestions": [
                    "Use high contrast for equation clarity",
                    "Minimize camera movement for focus"
                ],
                "confidence": 0.9,
                "generated_by": "gemini"
            }
        }


class SceneAnalysisRequest(BaseModel):
    """Request model for scene analysis."""
    content: str = Field(..., min_length=1, description="Content to analyze")
    existing_description: Optional[str] = Field(None, description="Existing description if available")
    
    @validator('content')
    def content_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Content cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "content": "A presentation about renewable energy sources",
                "existing_description": "Professional presentation with charts and graphs"
            }
        }


class SceneAnalysisResponse(BaseModel):
    """Response model for scene analysis."""
    scene_analysis: Dict[str, Any] = Field(..., description="Analysis results")
    cinematic_recommendations: Dict[str, Any] = Field(..., description="Recommended settings")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Analysis confidence")
    
    class Config:
        schema_extra = {
            "example": {
                "scene_analysis": {
                    "mood": "professional",
                    "complexity": "medium",
                    "pacing": "medium",
                    "focus_type": "informational"
                },
                "cinematic_recommendations": {
                    "camera_movements": {"intensity": 50},
                    "color_grading": {"temperature": 0, "contrast": 10}
                },
                "confidence": 0.85
            }
        }


class PreviewRequest(BaseModel):
    """Request model for preview generation."""
    scene_id: str = Field(..., min_length=1, description="Scene identifier")
    content: str = Field(..., min_length=1, description="Content for preview")
    settings: Dict[str, Any] = Field(..., description="Cinematic settings to apply")
    
    @validator('scene_id', 'content')
    def fields_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "scene_id": "scene_001",
                "content": "Sample content for preview",
                "settings": {
                    "camera_movements": {"enabled": True, "intensity": 60},
                    "color_grading": {"enabled": True, "contrast": 20}
                }
            }
        }


class PreviewResponse(BaseModel):
    """Response model for preview generation."""
    scene_id: str = Field(..., description="Scene identifier")
    preview_data: Dict[str, Any] = Field(..., description="Preview information")
    status: str = Field(..., description="Generation status")
    estimated_completion: str = Field(..., description="Estimated completion time")
    
    class Config:
        schema_extra = {
            "example": {
                "scene_id": "scene_001",
                "preview_data": {
                    "preview_url": "/api/v1/cinematic/preview/scene_001/render",
                    "thumbnail_url": "/api/v1/cinematic/preview/scene_001/thumbnail",
                    "estimated_size": "2.5 MB",
                    "estimated_duration": "15 seconds"
                },
                "status": "generating",
                "estimated_completion": "2024-01-01T00:00:05Z"
            }
        }


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    
    class Config:
        schema_extra = {
            "example": {
                "error": "validation_error",
                "message": "Invalid settings provided",
                "details": {
                    "field": "camera_movements.intensity",
                    "issue": "Value must be between 0 and 100"
                }
            }
        }


class ProfileExportResponse(BaseModel):
    """Response model for profile export."""
    exported_data: str = Field(..., description="Exported profile JSON data")
    
    class Config:
        schema_extra = {
            "example": {
                "exported_data": '{"format_version": "1.0", "profile": {...}}'
            }
        }


class ProfileImportRequest(BaseModel):
    """Request model for profile import."""
    profile_data: str = Field(..., min_length=1, description="Profile JSON data to import")
    user_id: str = Field("default", description="Target user ID")
    
    @validator('profile_data')
    def profile_data_must_not_be_empty(cls, v):
        if not v.strip():
            raise ValueError('Profile data cannot be empty')
        return v.strip()
    
    class Config:
        schema_extra = {
            "example": {
                "profile_data": '{"format_version": "1.0", "profile": {...}}',
                "user_id": "user_123"
            }
        }


class ValidationResponse(BaseModel):
    """Response model for settings validation."""
    valid: bool = Field(..., description="Whether settings are valid")
    errors: List[str] = Field(..., description="Validation errors")
    warnings: List[str] = Field(..., description="Validation warnings")
    
    class Config:
        schema_extra = {
            "example": {
                "valid": False,
                "errors": ["Camera movement intensity must be between 0 and 100"],
                "warnings": ["High contrast may reduce detail visibility"]
            }
        }


class OperationResponse(BaseModel):
    """Generic operation response."""
    status: str = Field(..., description="Operation status")
    message: Optional[str] = Field(None, description="Status message")
    data: Optional[Dict[str, Any]] = Field(None, description="Additional data")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "success",
                "message": "Operation completed successfully",
                "data": {"profile_id": "profile_123"}
            }
        }