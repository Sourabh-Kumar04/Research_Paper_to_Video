"""
RASO Platform Data Models

Pydantic models for type-safe data handling throughout the RASO platform.
All models include proper validation, serialization, and JSON schema generation.
"""

from .paper import (
    PaperInput,
    PaperContent,
    Section,
    Equation,
    Figure,
    Reference,
)
from .understanding import (
    PaperUnderstanding,
    KeyEquation,
    VisualizableConcept,
)
from .script import (
    NarrationScript,
    Scene,
    TimingMarker,
)
from .visual import (
    VisualPlan,
    ScenePlan,
    TransitionPlan,
    StyleGuide,
    AnimationTemplate,
    TemplateParameter,
    ValidationRule,
)
from .animation import (
    AnimationAssets,
    RenderedScene,
    SceneMetadata,
    VideoResolution,
)
from .audio import (
    AudioAssets,
    AudioScene,
    VoiceOption,
)
from .video import (
    VideoAsset,
    VideoMetadata,
    Chapter,
)
from .state import (
    RASOMasterState,
    WorkflowStatus,
    AgentError,
    ProcessingOptions,
)

__all__ = [
    # Paper Models
    "PaperInput",
    "PaperContent", 
    "Section",
    "Equation",
    "Figure",
    "Reference",
    # Understanding Models
    "PaperUnderstanding",
    "KeyEquation",
    "VisualizableConcept",
    # Script Models
    "NarrationScript",
    "Scene",
    "TimingMarker",
    # Visual Models
    "VisualPlan",
    "ScenePlan",
    "TransitionPlan",
    "StyleGuide",
    "AnimationTemplate",
    "TemplateParameter",
    "ValidationRule",
    # Animation Models
    "AnimationAssets",
    "RenderedScene",
    "SceneMetadata",
    "VideoResolution",
    # Audio Models
    "AudioAssets",
    "AudioScene",
    "VoiceOption",
    # Video Models
    "VideoAsset",
    "VideoMetadata",
    "Chapter",
    # State Models
    "RASOMasterState",
    "WorkflowStatus",
    "AgentError",
    "ProcessingOptions",
]