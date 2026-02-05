"""
State management models for the RASO platform.

Models for LangGraph workflow state, agent errors, and processing options
for coordinated multi-agent video generation.
"""

from enum import Enum
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
from uuid import uuid4

from pydantic import BaseModel, Field, validator

from .paper import PaperInput, PaperContent
from .understanding import PaperUnderstanding
from .script import NarrationScript
from .visual import VisualPlan
from .animation import AnimationAssets
from .audio import AudioAssets
from .video import VideoAsset, VideoMetadata


class WorkflowStatus(str, Enum):
    """Status of the RASO workflow."""
    PENDING = "pending"
    INGESTING = "ingesting"
    UNDERSTANDING = "understanding"
    SCRIPTING = "scripting"
    PLANNING = "planning"
    ANIMATING = "animating"
    AUDIO_PROCESSING = "audio_processing"
    VIDEO_COMPOSING = "video_composing"
    METADATA_GENERATING = "metadata_generating"
    UPLOADING = "uploading"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(str, Enum):
    """Types of agents in the RASO system."""
    INGEST = "ingest"
    UNDERSTANDING = "understanding"
    SCRIPT = "script"
    VISUAL_PLANNING = "visual_planning"
    MANIM = "manim"
    MOTION_CANVAS = "motion_canvas"
    REMOTION = "remotion"
    VOICE = "voice"
    AUDIO = "audio"  # Alias for VOICE
    VIDEO_COMPOSING = "video_composing"
    VIDEO_COMPOSITION = "video_composition"  # Alias for VIDEO_COMPOSING
    RENDERING = "rendering"
    TRANSITION = "transition"
    METADATA = "metadata"
    YOUTUBE = "youtube"


class ErrorSeverity(str, Enum):
    """Severity levels for agent errors."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AgentError(BaseModel):
    """Error information from agent execution."""
    
    agent_type: AgentType = Field(..., description="Type of agent that encountered the error")
    error_code: str = Field(..., description="Unique error code")
    message: str = Field(..., description="Human-readable error message")
    severity: ErrorSeverity = Field(..., description="Error severity level")
    
    # Error context
    timestamp: datetime = Field(default_factory=datetime.now, description="When the error occurred")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional error details")
    stack_trace: Optional[str] = Field(default=None, description="Stack trace if available")
    
    # Recovery information
    is_recoverable: bool = Field(default=True, description="Whether the error is recoverable")
    suggested_action: Optional[str] = Field(default=None, description="Suggested recovery action")
    retry_count: int = Field(default=0, description="Number of retry attempts")
    
    @validator("message")
    def validate_message(cls, v):
        """Validate error message."""
        if len(v.strip()) < 5:
            raise ValueError("Error message must be at least 5 characters")
        return v.strip()
    
    def increment_retry(self) -> None:
        """Increment the retry count."""
        self.retry_count += 1
    
    def is_critical(self) -> bool:
        """Check if this is a critical error."""
        return self.severity == ErrorSeverity.CRITICAL
    
    def should_abort(self, max_retries: int = 3) -> bool:
        """Determine if processing should be aborted."""
        return self.is_critical() or (not self.is_recoverable) or (self.retry_count >= max_retries)


class ProcessingOptions(BaseModel):
    """Options for customizing the video generation process."""
    
    # Quality settings
    video_quality: str = Field(default="high", description="Video quality preset")
    animation_quality: str = Field(default="high", description="Animation quality preset")
    audio_quality: str = Field(default="high", description="Audio quality preset")
    
    # Content preferences
    target_duration: Optional[float] = Field(default=None, description="Target video duration in seconds")
    include_equations: bool = Field(default=True, description="Whether to include equation animations")
    include_figures: bool = Field(default=True, description="Whether to include figure animations")
    
    # Voice settings
    voice_id: Optional[str] = Field(default=None, description="Preferred voice ID for narration")
    voice_speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Voice speed multiplier")
    voice_pitch: float = Field(default=0.0, ge=-12.0, le=12.0, description="Voice pitch adjustment")
    
    # Animation preferences
    prefer_manim: bool = Field(default=False, description="Prefer Manim for all animations")
    animation_style: str = Field(default="modern", description="Animation style preference")
    color_scheme: str = Field(default="default", description="Color scheme preference")
    
    # YouTube settings
    auto_upload: bool = Field(default=False, description="Automatically upload to YouTube")
    privacy_status: str = Field(default="unlisted", description="YouTube privacy status")
    custom_thumbnail: Optional[str] = Field(default=None, description="Path to custom thumbnail")
    
    # Processing settings
    parallel_processing: bool = Field(default=True, description="Enable parallel processing")
    max_retries: int = Field(default=3, ge=0, le=10, description="Maximum retry attempts")
    timeout_minutes: int = Field(default=60, ge=5, le=300, description="Processing timeout")
    
    @validator("target_duration")
    def validate_target_duration(cls, v):
        """Validate target duration."""
        if v is not None and (v < 30 or v > 3600):  # 30 seconds to 1 hour
            raise ValueError("Target duration must be between 30 seconds and 1 hour")
        return v


class ProcessingProgress(BaseModel):
    """Progress tracking for the video generation process."""
    
    current_step: WorkflowStatus = Field(default=WorkflowStatus.PENDING, description="Current processing step")
    completed_steps: List[WorkflowStatus] = Field(default_factory=list, description="Completed steps")
    
    # Progress metrics
    overall_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Overall progress (0-1)")
    step_progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Current step progress (0-1)")
    
    # Timing information
    start_time: datetime = Field(default_factory=datetime.now, description="Processing start time")
    last_update: datetime = Field(default_factory=datetime.now, description="Last progress update")
    estimated_completion: Optional[datetime] = Field(default=None, description="Estimated completion time")
    
    # Status messages
    current_message: str = Field(default="Initializing...", description="Current status message")
    detailed_status: Dict[str, Any] = Field(default_factory=dict, description="Detailed status information")
    
    def update_progress(self, step: WorkflowStatus, progress: float, message: str) -> None:
        """Update progress information."""
        self.current_step = step
        self.step_progress = progress
        self.current_message = message
        self.last_update = datetime.now()
        
        # Update overall progress based on step weights
        step_weights = {
            WorkflowStatus.INGESTING: 0.1,
            WorkflowStatus.UNDERSTANDING: 0.15,
            WorkflowStatus.SCRIPTING: 0.15,
            WorkflowStatus.PLANNING: 0.1,
            WorkflowStatus.ANIMATING: 0.3,
            WorkflowStatus.AUDIO_PROCESSING: 0.1,
            WorkflowStatus.VIDEO_COMPOSING: 0.05,
            WorkflowStatus.METADATA_GENERATING: 0.03,
            WorkflowStatus.UPLOADING: 0.02,
        }
        
        completed_weight = sum(step_weights.get(s, 0) for s in self.completed_steps)
        current_weight = step_weights.get(step, 0) * progress
        self.overall_progress = min(1.0, completed_weight + current_weight)
    
    def complete_step(self, step: WorkflowStatus) -> None:
        """Mark a step as completed."""
        if step not in self.completed_steps:
            self.completed_steps.append(step)
        self.step_progress = 1.0
        self.last_update = datetime.now()
    
    @property
    def elapsed_time(self) -> float:
        """Get elapsed processing time in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def is_completed(self) -> bool:
        """Check if processing is completed."""
        return self.current_step in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]


class RASOMasterState(BaseModel):
    """Master state for the RASO LangGraph workflow."""
    
    # Unique identifier
    job_id: str = Field(default_factory=lambda: str(uuid4()), description="Unique job identifier")
    
    # Input and processing options
    paper_input: PaperInput = Field(..., description="Original paper input")
    options: ProcessingOptions = Field(default_factory=ProcessingOptions, description="Processing options")
    
    # Processing state
    paper_content: Optional[PaperContent] = Field(default=None, description="Extracted paper content")
    understanding: Optional[PaperUnderstanding] = Field(default=None, description="AI understanding of paper")
    script: Optional[NarrationScript] = Field(default=None, description="Generated narration script")
    visual_plan: Optional[VisualPlan] = Field(default=None, description="Visual planning for animations")
    animations: Optional[AnimationAssets] = Field(default=None, description="Rendered animation assets")
    audio: Optional[AudioAssets] = Field(default=None, description="Generated audio assets")
    video: Optional[VideoAsset] = Field(default=None, description="Final video asset")
    metadata: Optional[VideoMetadata] = Field(default=None, description="Video metadata")
    
    # Workflow control
    current_agent: Optional[AgentType] = Field(default=None, description="Currently executing agent")
    progress: ProcessingProgress = Field(default_factory=ProcessingProgress, description="Processing progress")
    errors: List[AgentError] = Field(default_factory=list, description="Accumulated errors")
    
    # State metadata
    created_at: datetime = Field(default_factory=datetime.now, description="State creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.now, description="Last state update")
    
    def update_timestamp(self) -> None:
        """Update the last modified timestamp."""
        self.updated_at = datetime.now()
    
    def add_error(self, agent_type: AgentType, error_code: str, message: str, 
                  severity: ErrorSeverity = ErrorSeverity.ERROR, **kwargs) -> AgentError:
        """Add an error to the state."""
        error = AgentError(
            agent_type=agent_type,
            error_code=error_code,
            message=message,
            severity=severity,
            **kwargs
        )
        self.errors.append(error)
        self.update_timestamp()
        return error
    
    def get_errors_by_agent(self, agent_type: AgentType) -> List[AgentError]:
        """Get all errors for a specific agent type."""
        return [error for error in self.errors if error.agent_type == agent_type]
    
    def get_critical_errors(self) -> List[AgentError]:
        """Get all critical errors."""
        return [error for error in self.errors if error.is_critical()]
    
    def has_critical_errors(self) -> bool:
        """Check if there are any critical errors."""
        return len(self.get_critical_errors()) > 0
    
    def should_abort(self) -> bool:
        """Determine if processing should be aborted."""
        return any(error.should_abort(self.options.max_retries) for error in self.errors)
    
    def get_completion_percentage(self) -> float:
        """Get overall completion percentage."""
        return self.progress.overall_progress * 100
    
    def is_step_completed(self, step: WorkflowStatus) -> bool:
        """Check if a specific step is completed."""
        return step in self.progress.completed_steps
    
    def get_output_summary(self) -> Dict[str, Any]:
        """Get a summary of generated outputs."""
        summary = {
            "job_id": self.job_id,
            "status": self.progress.current_step,
            "progress": self.get_completion_percentage(),
            "has_errors": len(self.errors) > 0,
            "error_count": len(self.errors),
            "critical_errors": len(self.get_critical_errors()),
        }
        
        if self.paper_content:
            summary["paper_title"] = self.paper_content.title
            summary["paper_authors"] = self.paper_content.authors
        
        if self.script:
            summary["total_scenes"] = len(self.script.scenes)
            summary["script_duration"] = self.script.total_duration
        
        if self.video:
            summary["video_path"] = self.video.file_path
            summary["video_duration"] = self.video.duration
            summary["video_size_mb"] = self.video.file_size_mb
        
        return summary
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "paper_input": {
                    "type": "arxiv",
                    "content": "https://arxiv.org/abs/1706.03762"
                },
                "options": {
                    "video_quality": "high",
                    "voice_speed": 1.0,
                    "auto_upload": False
                },
                "progress": {
                    "current_step": "understanding",
                    "overall_progress": 0.25,
                    "current_message": "Analyzing paper content..."
                }
            }
        }