"""
Visual planning models for the RASO platform.

Models for visual planning, animation templates, and scene organization
for coordinated video production across multiple animation frameworks.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, validator


class AnimationFramework(str, Enum):
    """Animation frameworks supported by RASO."""
    MANIM = "manim"
    MOTION_CANVAS = "motion-canvas"
    REMOTION = "remotion"


class TransitionType(str, Enum):
    """Types of transitions between scenes."""
    FADE = "fade"
    SLIDE = "slide"
    ZOOM = "zoom"
    MORPH = "morph"
    CUT = "cut"


class TemplateCategory(str, Enum):
    """Categories of animation templates."""
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    UI_ELEMENTS = "ui_elements"
    TEXT_ANIMATION = "text_animation"
    DATA_VISUALIZATION = "data_visualization"


class SafetyLevel(str, Enum):
    """Safety levels for animation templates."""
    SAFE = "safe"
    RESTRICTED = "restricted"
    UNSAFE = "unsafe"


class ValidationRule(BaseModel):
    """Validation rule for template parameters."""
    
    pattern: Optional[str] = Field(default=None, description="Regex pattern for strings")
    min_value: Optional[float] = Field(default=None, description="Minimum value for numbers")
    max_value: Optional[float] = Field(default=None, description="Maximum value for numbers")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Allowed enum values")
    required: bool = Field(default=True, description="Whether parameter is required")


class TemplateParameter(BaseModel):
    """Parameter definition for animation templates."""
    
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: str = Field(..., description="Parameter description")
    default_value: Optional[Any] = Field(default=None, description="Default parameter value")
    validation: Optional[ValidationRule] = Field(default=None, description="Validation rules")
    
    @validator("type")
    def validate_type(cls, v):
        """Validate parameter type."""
        valid_types = ["string", "number", "boolean", "array", "object", "color", "position"]
        if v not in valid_types:
            raise ValueError(f"Parameter type must be one of {valid_types}")
        return v


class AnimationTemplate(BaseModel):
    """Template for safe animation generation."""
    
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable template name")
    framework: AnimationFramework = Field(..., description="Target animation framework")
    category: TemplateCategory = Field(..., description="Template category")
    description: str = Field(..., description="Template description")
    
    # Template definition
    parameters: List[TemplateParameter] = Field(..., description="Template parameters")
    code_template: str = Field(..., description="Code template with parameter placeholders")
    safety_level: SafetyLevel = Field(default=SafetyLevel.SAFE, description="Template safety level")
    
    # Metadata
    estimated_render_time: float = Field(default=10.0, description="Estimated render time in seconds")
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Template complexity (0-1)")
    tags: List[str] = Field(default_factory=list, description="Template tags for search")
    
    @validator("code_template")
    def validate_code_template(cls, v):
        """Validate code template."""
        if len(v.strip()) < 50:
            raise ValueError("Code template must be at least 50 characters")
        
        # Check for dangerous patterns
        dangerous_patterns = ["exec(", "eval(", "import os", "subprocess", "__import__"]
        for pattern in dangerous_patterns:
            if pattern in v:
                raise ValueError(f"Code template contains dangerous pattern: {pattern}")
        
        return v.strip()
    
    def get_parameter_by_name(self, name: str) -> Optional[TemplateParameter]:
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None
    
    def validate_parameters(self, param_values: Dict[str, Any]) -> Dict[str, str]:
        """Validate parameter values against template definition."""
        errors = {}
        
        for param in self.parameters:
            value = param_values.get(param.name)
            
            # Check required parameters
            if param.validation and param.validation.required and value is None:
                errors[param.name] = "Required parameter is missing"
                continue
            
            if value is None:
                continue
            
            # Type validation
            if param.type == "number" and not isinstance(value, (int, float)):
                errors[param.name] = "Parameter must be a number"
            elif param.type == "string" and not isinstance(value, str):
                errors[param.name] = "Parameter must be a string"
            elif param.type == "boolean" and not isinstance(value, bool):
                errors[param.name] = "Parameter must be a boolean"
            elif param.type == "array" and not isinstance(value, list):
                errors[param.name] = "Parameter must be an array"
            
            # Validation rules
            if param.validation:
                if param.validation.min_value is not None and isinstance(value, (int, float)):
                    if value < param.validation.min_value:
                        errors[param.name] = f"Value must be >= {param.validation.min_value}"
                
                if param.validation.max_value is not None and isinstance(value, (int, float)):
                    if value > param.validation.max_value:
                        errors[param.name] = f"Value must be <= {param.validation.max_value}"
                
                if param.validation.allowed_values and value not in param.validation.allowed_values:
                    errors[param.name] = f"Value must be one of {param.validation.allowed_values}"
        
        return errors


class StyleGuide(BaseModel):
    """Visual style guide for consistent video appearance."""
    
    # Color scheme
    primary_color: str = Field(default="#2E86AB", description="Primary brand color")
    secondary_color: str = Field(default="#A23B72", description="Secondary accent color")
    background_color: str = Field(default="#F18F01", description="Background color")
    text_color: str = Field(default="#C73E1D", description="Primary text color")
    
    # Typography
    primary_font: str = Field(default="Arial", description="Primary font family")
    secondary_font: str = Field(default="Times New Roman", description="Secondary font family")
    font_sizes: Dict[str, int] = Field(default_factory=lambda: {
        "title": 48,
        "subtitle": 36,
        "body": 24,
        "caption": 18
    }, description="Font size definitions")
    
    # Animation settings
    animation_speed: float = Field(default=1.0, description="Global animation speed multiplier")
    transition_duration: float = Field(default=0.5, description="Default transition duration")
    
    @validator("primary_color", "secondary_color", "background_color", "text_color")
    def validate_color(cls, v):
        """Validate color format."""
        if not v.startswith("#") or len(v) != 7:
            raise ValueError("Color must be in hex format (#RRGGBB)")
        return v


class TransitionPlan(BaseModel):
    """Plan for transitions between scenes."""
    
    from_scene: str = Field(..., description="Source scene ID")
    to_scene: str = Field(..., description="Target scene ID")
    transition_type: TransitionType = Field(..., description="Type of transition")
    duration: float = Field(default=0.5, gt=0.0, description="Transition duration in seconds")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Transition-specific parameters")


class ScenePlan(BaseModel):
    """Detailed plan for a single scene."""
    
    scene_id: str = Field(..., description="Reference to scene ID")
    framework: AnimationFramework = Field(..., description="Animation framework to use")
    template_id: str = Field(..., description="Template ID to use")
    parameters: Dict[str, Any] = Field(..., description="Template parameters")
    duration: float = Field(..., gt=0.0, description="Scene duration in seconds")
    
    # Rendering settings
    resolution: str = Field(default="1920x1080", description="Render resolution")
    frame_rate: int = Field(default=30, description="Frame rate")
    quality: str = Field(default="high", description="Render quality")
    
    @validator("resolution")
    def validate_resolution(cls, v):
        """Validate resolution format."""
        if "x" not in v:
            raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        width, height = v.split("x")
        if not (width.isdigit() and height.isdigit()):
            raise ValueError("Resolution dimensions must be numeric")
        return v


class VisualPlan(BaseModel):
    """Complete visual plan for video production."""
    
    scenes: List[ScenePlan] = Field(..., description="Scene plans in order")
    transitions: List[TransitionPlan] = Field(default_factory=list, description="Transition plans")
    style_guide: StyleGuide = Field(default_factory=StyleGuide, description="Visual style guide")
    
    # Production metadata
    total_duration: float = Field(..., gt=0.0, description="Total video duration")
    estimated_render_time: float = Field(default=0.0, description="Estimated total render time")
    complexity_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Overall complexity")
    
    @validator("scenes")
    def validate_scenes(cls, v):
        """Validate scene plans."""
        if not v:
            raise ValueError("At least one scene plan is required")
        
        # Check for duplicate scene IDs
        scene_ids = [scene.scene_id for scene in v]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique")
        
        return v
    
    @validator("transitions")
    def validate_transitions(cls, v, values):
        """Validate transition plans."""
        scenes = values.get("scenes", [])
        scene_ids = {scene.scene_id for scene in scenes}
        
        for transition in v:
            if transition.from_scene not in scene_ids:
                raise ValueError(f"Transition references unknown scene: {transition.from_scene}")
            if transition.to_scene not in scene_ids:
                raise ValueError(f"Transition references unknown scene: {transition.to_scene}")
        
        return v
    
    def get_scene_plan_by_id(self, scene_id: str) -> Optional[ScenePlan]:
        """Get a scene plan by ID."""
        for scene in self.scenes:
            if scene.scene_id == scene_id:
                return scene
        return None
    
    def get_scenes_by_framework(self, framework: AnimationFramework) -> List[ScenePlan]:
        """Get all scenes using a specific framework."""
        return [scene for scene in self.scenes if scene.framework == framework]
    
    def get_framework_distribution(self) -> Dict[AnimationFramework, int]:
        """Get distribution of animation frameworks."""
        distribution = {framework: 0 for framework in AnimationFramework}
        for scene in self.scenes:
            distribution[scene.framework] += 1
        return distribution
    
    def calculate_estimated_render_time(self) -> float:
        """Calculate total estimated render time."""
        # Base time estimates per framework (minutes per scene)
        framework_times = {
            AnimationFramework.MANIM: 15,
            AnimationFramework.MOTION_CANVAS: 10,
            AnimationFramework.REMOTION: 5
        }
        
        total_time = 0.0
        for scene in self.scenes:
            base_time = framework_times.get(scene.framework, 10)
            complexity_multiplier = 1.0 + (self.complexity_score * 0.5)
            total_time += base_time * complexity_multiplier
        
        return total_time
    
    class Config:
        schema_extra = {
            "example": {
                "scenes": [
                    {
                        "scene_id": "scene1",
                        "framework": "motion-canvas",
                        "template_id": "intro_template",
                        "parameters": {
                            "title": "Introduction to Transformers",
                            "background_color": "#2E86AB"
                        },
                        "duration": 30.0,
                        "resolution": "1920x1080",
                        "frame_rate": 30
                    }
                ],
                "transitions": [
                    {
                        "from_scene": "scene1",
                        "to_scene": "scene2", 
                        "transition_type": "fade",
                        "duration": 0.5
                    }
                ],
                "total_duration": 75.0,
                "complexity_score": 0.6
            }
        }