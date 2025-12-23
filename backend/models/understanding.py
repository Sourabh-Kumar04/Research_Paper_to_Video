"""
Paper understanding models for the RASO platform.

Models for representing the AI's understanding of research papers,
including problem identification, contributions, and visualizable concepts.
"""

from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field, validator


class VisualizationType(str, Enum):
    """Types of visualizations for concepts."""
    ANIMATION = "animation"
    DIAGRAM = "diagram"
    CHART = "chart"
    SIMULATION = "simulation"
    FLOW = "flow"
    NETWORK = "network"


class ConceptComplexity(str, Enum):
    """Complexity levels for visualizable concepts."""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"


class KeyEquation(BaseModel):
    """A key equation identified for visualization."""
    
    equation_id: str = Field(..., description="Reference to equation ID in paper content")
    importance: int = Field(..., ge=1, le=10, description="Importance score (1-10)")
    visualization_hint: str = Field(..., description="Hint for how to visualize this equation")
    related_concepts: List[str] = Field(default_factory=list, description="Related concept names")
    
    @validator("visualization_hint")
    def validate_visualization_hint(cls, v):
        """Validate visualization hint."""
        if len(v.strip()) < 10:
            raise ValueError("Visualization hint must be at least 10 characters")
        return v.strip()


class VisualizableConcept(BaseModel):
    """A concept that can be visualized in the video."""
    
    name: str = Field(..., description="Concept name")
    description: str = Field(..., description="Detailed description of the concept")
    visualization_type: VisualizationType = Field(..., description="Type of visualization")
    complexity: ConceptComplexity = Field(..., description="Complexity level")
    related_equations: List[str] = Field(default_factory=list, description="Related equation IDs")
    animation_hints: List[str] = Field(default_factory=list, description="Hints for animation")
    
    @validator("name")
    def validate_name(cls, v):
        """Validate concept name."""
        if len(v.strip()) < 3:
            raise ValueError("Concept name must be at least 3 characters")
        return v.strip()
    
    @validator("description")
    def validate_description(cls, v):
        """Validate concept description."""
        if len(v.strip()) < 20:
            raise ValueError("Concept description must be at least 20 characters")
        return v.strip()


class PaperUnderstanding(BaseModel):
    """AI's understanding of a research paper."""
    
    problem: str = Field(..., description="Core problem statement and research motivation")
    intuition: str = Field(..., description="Intuitive explanation of the approach")
    contributions: List[str] = Field(..., description="Key contributions and novel insights")
    key_equations: List[KeyEquation] = Field(default_factory=list, description="Important equations for visualization")
    visualizable_concepts: List[VisualizableConcept] = Field(default_factory=list, description="Concepts that can be animated")
    
    # Analysis metadata
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence in understanding")
    analysis_notes: List[str] = Field(default_factory=list, description="Additional analysis notes")
    difficulty_level: ConceptComplexity = Field(default=ConceptComplexity.MEDIUM, description="Overall paper difficulty")
    
    @validator("problem")
    def validate_problem(cls, v):
        """Validate problem statement."""
        if len(v.strip()) < 50:
            raise ValueError("Problem statement must be at least 50 characters")
        return v.strip()
    
    @validator("intuition")
    def validate_intuition(cls, v):
        """Validate intuition explanation."""
        if len(v.strip()) < 50:
            raise ValueError("Intuition explanation must be at least 50 characters")
        return v.strip()
    
    @validator("contributions")
    def validate_contributions(cls, v):
        """Validate contributions list."""
        if not v:
            raise ValueError("At least one contribution is required")
        
        for i, contribution in enumerate(v):
            if len(contribution.strip()) < 20:
                raise ValueError(f"Contribution {i+1} must be at least 20 characters")
        
        return [contrib.strip() for contrib in v]
    
    def get_concept_by_name(self, name: str) -> Optional[VisualizableConcept]:
        """Get a visualizable concept by name."""
        for concept in self.visualizable_concepts:
            if concept.name.lower() == name.lower():
                return concept
        return None
    
    def get_concepts_by_type(self, viz_type: VisualizationType) -> List[VisualizableConcept]:
        """Get all concepts of a specific visualization type."""
        return [concept for concept in self.visualizable_concepts 
                if concept.visualization_type == viz_type]
    
    def get_concepts_by_complexity(self, complexity: ConceptComplexity) -> List[VisualizableConcept]:
        """Get all concepts of a specific complexity level."""
        return [concept for concept in self.visualizable_concepts 
                if concept.complexity == complexity]
    
    def get_high_importance_equations(self, min_importance: int = 7) -> List[KeyEquation]:
        """Get equations with importance score above threshold."""
        return [eq for eq in self.key_equations if eq.importance >= min_importance]
    
    def get_total_concepts(self) -> int:
        """Get total number of visualizable concepts."""
        return len(self.visualizable_concepts)
    
    def get_animation_complexity_score(self) -> float:
        """Calculate overall animation complexity score (0-1)."""
        if not self.visualizable_concepts:
            return 0.0
        
        complexity_weights = {
            ConceptComplexity.SIMPLE: 0.3,
            ConceptComplexity.MEDIUM: 0.6,
            ConceptComplexity.COMPLEX: 1.0
        }
        
        total_weight = sum(complexity_weights[concept.complexity] 
                          for concept in self.visualizable_concepts)
        return total_weight / len(self.visualizable_concepts)
    
    class Config:
        schema_extra = {
            "example": {
                "problem": "Sequential models are slow due to their inherent sequential nature, limiting parallelization during training",
                "intuition": "Attention mechanisms can replace recurrence entirely, allowing for more parallelizable architectures",
                "contributions": [
                    "Transformer architecture based solely on attention mechanisms",
                    "Parallelizable training process that significantly reduces training time",
                    "State-of-the-art results on machine translation tasks"
                ],
                "key_equations": [
                    {
                        "equation_id": "eq1",
                        "importance": 10,
                        "visualization_hint": "Show matrix multiplication and softmax operation with animated attention weights",
                        "related_concepts": ["attention", "transformer", "self-attention"]
                    }
                ],
                "visualizable_concepts": [
                    {
                        "name": "Self-Attention Mechanism",
                        "description": "How tokens in a sequence attend to other tokens to capture dependencies",
                        "visualization_type": "animation",
                        "complexity": "medium",
                        "related_equations": ["eq1"],
                        "animation_hints": ["Show attention weights as connections", "Animate query-key-value computation"]
                    }
                ],
                "confidence_score": 0.85,
                "difficulty_level": "medium"
            }
        }