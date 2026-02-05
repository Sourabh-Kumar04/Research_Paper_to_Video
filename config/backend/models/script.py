"""
Script generation models for the RASO platform.

Models for narration scripts, scenes, and timing information
for educational video generation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import timedelta

from pydantic import BaseModel, Field, validator


class VisualType(str, Enum):
    """Types of visual frameworks for scenes."""
    MANIM = "manim"
    MOTION_CANVAS = "motion-canvas"
    REMOTION = "remotion"


class ScenePacing(str, Enum):
    """Pacing options for scenes."""
    SLOW = "slow"
    NORMAL = "normal"
    FAST = "fast"


class TimingMarker(BaseModel):
    """Timing marker for audio synchronization."""
    
    timestamp: float = Field(..., ge=0.0, description="Timestamp in seconds")
    marker_type: str = Field(..., description="Type of timing marker")
    content: str = Field(..., description="Content at this timestamp")
    
    @validator("marker_type")
    def validate_marker_type(cls, v):
        """Validate marker type."""
        valid_types = ["word", "sentence", "pause", "emphasis", "transition"]
        if v not in valid_types:
            raise ValueError(f"Marker type must be one of {valid_types}")
        return v


class Scene(BaseModel):
    """A single scene in the narration script."""
    
    id: str = Field(..., description="Unique scene identifier")
    title: str = Field(..., description="Scene title")
    narration: str = Field(..., description="Narration text for this scene")
    duration: float = Field(..., gt=0.0, description="Scene duration in seconds")
    visual_type: VisualType = Field(..., description="Visual framework to use")
    concepts: List[str] = Field(default_factory=list, description="Key concepts covered")
    
    # Timing and pacing
    pacing: ScenePacing = Field(default=ScenePacing.NORMAL, description="Scene pacing")
    timing_markers: List[TimingMarker] = Field(default_factory=list, description="Timing synchronization markers")
    
    # Content organization
    section_reference: Optional[str] = Field(default=None, description="Reference to paper section")
    equation_references: List[str] = Field(default_factory=list, description="Referenced equation IDs")
    figure_references: List[str] = Field(default_factory=list, description="Referenced figure IDs")
    
    @validator("title")
    def validate_title(cls, v):
        """Validate scene title."""
        if len(v.strip()) < 3:
            raise ValueError("Scene title must be at least 3 characters")
        return v.strip()
    
    @validator("narration")
    def validate_narration(cls, v):
        """Validate narration text."""
        if len(v.strip()) < 20:
            raise ValueError("Narration must be at least 20 characters")
        
        # Check for YouTube-friendly language (no excessive technical jargon)
        word_count = len(v.split())
        if word_count < 10:
            raise ValueError("Narration must contain at least 10 words")
        
        return v.strip()
    
    @validator("duration")
    def validate_duration(cls, v):
        """Validate scene duration."""
        if v > 300:  # 5 minutes max per scene
            raise ValueError("Scene duration cannot exceed 300 seconds")
        return v
    
    def get_word_count(self) -> int:
        """Get word count of narration."""
        return len(self.narration.split())
    
    def get_estimated_reading_time(self, words_per_minute: int = 150) -> float:
        """Estimate reading time based on word count."""
        return (self.get_word_count() / words_per_minute) * 60
    
    def add_timing_marker(self, timestamp: float, marker_type: str, content: str) -> None:
        """Add a timing marker to the scene."""
        marker = TimingMarker(
            timestamp=timestamp,
            marker_type=marker_type,
            content=content
        )
        self.timing_markers.append(marker)
        # Sort markers by timestamp
        self.timing_markers.sort(key=lambda x: x.timestamp)


class NarrationScript(BaseModel):
    """Complete narration script for a research paper video."""
    
    scenes: List[Scene] = Field(..., description="List of scenes in order")
    total_duration: float = Field(..., gt=0.0, description="Total script duration in seconds")
    word_count: int = Field(..., ge=0, description="Total word count")
    
    # Script metadata
    target_audience: str = Field(default="general", description="Target audience level")
    language: str = Field(default="en", description="Script language code")
    style_notes: List[str] = Field(default_factory=list, description="Style and tone notes")
    
    @validator("scenes")
    def validate_scenes(cls, v):
        """Validate scenes list."""
        if not v:
            raise ValueError("At least one scene is required")
        
        # Check for duplicate scene IDs
        scene_ids = [scene.id for scene in v]
        if len(scene_ids) != len(set(scene_ids)):
            raise ValueError("Scene IDs must be unique")
        
        return v
    
    @validator("total_duration")
    def validate_total_duration(cls, v, values):
        """Validate total duration matches scene durations."""
        scenes = values.get("scenes", [])
        if scenes:
            calculated_duration = sum(scene.duration for scene in scenes)
            if abs(v - calculated_duration) > 1.0:  # Allow 1 second tolerance
                raise ValueError("Total duration must match sum of scene durations")
        return v
    
    @validator("word_count")
    def validate_word_count(cls, v, values):
        """Validate word count matches scene word counts."""
        scenes = values.get("scenes", [])
        if scenes:
            calculated_count = sum(scene.get_word_count() for scene in scenes)
            if abs(v - calculated_count) > 10:  # Allow small tolerance
                raise ValueError("Word count must match sum of scene word counts")
        return v
    
    def get_scene_by_id(self, scene_id: str) -> Optional[Scene]:
        """Get a scene by its ID."""
        for scene in self.scenes:
            if scene.id == scene_id:
                return scene
        return None
    
    def get_scenes_by_visual_type(self, visual_type: VisualType) -> List[Scene]:
        """Get all scenes using a specific visual framework."""
        return [scene for scene in self.scenes if scene.visual_type == visual_type]
    
    def get_scenes_by_concept(self, concept: str) -> List[Scene]:
        """Get all scenes covering a specific concept."""
        return [scene for scene in self.scenes if concept.lower() in 
                [c.lower() for c in scene.concepts]]
    
    def get_average_scene_duration(self) -> float:
        """Get average duration per scene."""
        if not self.scenes:
            return 0.0
        return self.total_duration / len(self.scenes)
    
    def get_framework_distribution(self) -> Dict[VisualType, int]:
        """Get distribution of visual frameworks used."""
        distribution = {framework: 0 for framework in VisualType}
        for scene in self.scenes:
            distribution[scene.visual_type] += 1
        return distribution
    
    def estimate_production_time(self) -> Dict[str, float]:
        """Estimate production time for different phases."""
        manim_scenes = len(self.get_scenes_by_visual_type(VisualType.MANIM))
        motion_scenes = len(self.get_scenes_by_visual_type(VisualType.MOTION_CANVAS))
        remotion_scenes = len(self.get_scenes_by_visual_type(VisualType.REMOTION))
        
        # Estimated minutes per scene by framework
        time_estimates = {
            "manim_animation": manim_scenes * 15,  # 15 min per Manim scene
            "motion_canvas_animation": motion_scenes * 10,  # 10 min per Motion Canvas scene
            "remotion_animation": remotion_scenes * 5,  # 5 min per Remotion scene
            "audio_generation": len(self.scenes) * 2,  # 2 min per scene for TTS
            "video_composition": 10,  # 10 min for final composition
        }
        
        time_estimates["total"] = sum(time_estimates.values())
        return time_estimates
    
    class Config:
        schema_extra = {
            "example": {
                "scenes": [
                    {
                        "id": "scene1",
                        "title": "Introduction to Transformers",
                        "narration": "Today we'll explore the revolutionary Transformer architecture that changed the landscape of natural language processing...",
                        "duration": 30.0,
                        "visual_type": "motion-canvas",
                        "concepts": ["transformer", "attention", "neural networks"],
                        "pacing": "normal",
                        "section_reference": "intro"
                    },
                    {
                        "id": "scene2",
                        "title": "Attention Mechanism Deep Dive", 
                        "narration": "The key innovation of the Transformer is the attention mechanism, which allows the model to focus on different parts of the input...",
                        "duration": 45.0,
                        "visual_type": "manim",
                        "concepts": ["attention", "self-attention", "mathematics"],
                        "pacing": "slow",
                        "equation_references": ["eq1"]
                    }
                ],
                "total_duration": 75.0,
                "word_count": 150,
                "target_audience": "technical",
                "language": "en"
            }
        }