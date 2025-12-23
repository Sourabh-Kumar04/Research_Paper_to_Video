"""
LangGraph workflow orchestration for the RASO platform.

Defines the main workflow graph for coordinating agents in the video generation process.
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from backend.models import RASOMasterState, WorkflowStatus, AgentType, ErrorSeverity
from backend.config import get_config
from agents.base import agent_registry, BaseAgent, AgentExecutionError


class WorkflowOrchestrator:
    """Orchestrates the RASO video generation workflow using LangGraph."""
    
    def __init__(self):
        """Initialize the workflow orchestrator."""
        self.config = get_config()
        self.graph = self._build_graph()
        self.checkpointer = MemorySaver()
    
    def _build_graph(self) -> StateGraph:
        """
        Build the LangGraph workflow.
        
        Returns:
            Configured StateGraph instance
        """
        # Create the graph
        workflow = StateGraph(RASOMasterState)
        
        # Add nodes for each agent
        workflow.add_node("ingest", self._create_agent_node(AgentType.INGEST))
        workflow.add_node("understand", self._create_agent_node(AgentType.UNDERSTANDING))
        workflow.add_node("script", self._create_agent_node(AgentType.SCRIPT))
        workflow.add_node("visual_plan", self._create_agent_node(AgentType.VISUAL_PLANNING))
        workflow.add_node("animate_manim", self._create_agent_node(AgentType.MANIM))
        workflow.add_node("animate_motion", self._create_agent_node(AgentType.MOTION_CANVAS))
        workflow.add_node("animate_remotion", self._create_agent_node(AgentType.REMOTION))
        workflow.add_node("generate_voice", self._create_agent_node(AgentType.VOICE))
        workflow.add_node("compose_video", self._create_agent_node(AgentType.TRANSITION))
        workflow.add_node("generate_metadata", self._create_agent_node(AgentType.METADATA))
        workflow.add_node("upload_youtube", self._create_agent_node(AgentType.YOUTUBE))
        
        # Define the workflow edges
        workflow.set_entry_point("ingest")
        
        # Linear workflow with conditional branches
        workflow.add_edge("ingest", "understand")
        workflow.add_edge("understand", "script")
        workflow.add_edge("script", "visual_plan")
        
        # Conditional routing for animation
        workflow.add_conditional_edges(
            "visual_plan",
            self._route_animation,
            {
                "manim": "animate_manim",
                "motion_canvas": "animate_motion", 
                "remotion": "animate_remotion",
                "parallel": "animate_manim",  # Start with Manim for parallel
            }
        )
        
        # Animation completion routing
        workflow.add_conditional_edges(
            "animate_manim",
            self._check_animation_complete,
            {
                "continue_motion": "animate_motion",
                "continue_remotion": "animate_remotion",
                "voice": "generate_voice",
            }
        )
        
        workflow.add_conditional_edges(
            "animate_motion",
            self._check_animation_complete,
            {
                "continue_remotion": "animate_remotion",
                "voice": "generate_voice",
            }
        )
        
        workflow.add_conditional_edges(
            "animate_remotion",
            self._check_animation_complete,
            {
                "voice": "generate_voice",
            }
        )
        
        # Continue with audio and video processing
        workflow.add_edge("generate_voice", "compose_video")
        workflow.add_edge("compose_video", "generate_metadata")
        
        # Conditional YouTube upload
        workflow.add_conditional_edges(
            "generate_metadata",
            self._should_upload_youtube,
            {
                "upload": "upload_youtube",
                "end": END,
            }
        )
        
        workflow.add_edge("upload_youtube", END)
        
        return workflow
    
    def _create_agent_node(self, agent_type: AgentType) -> Callable:
        """
        Create a node function for an agent.
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Node function for the graph
        """
        async def agent_node(state: RASOMasterState) -> RASOMasterState:
            """Execute agent with retry logic and error handling."""
            agent = agent_registry.get_agent(agent_type)
            
            # Update workflow status
            status_map = {
                AgentType.INGEST: WorkflowStatus.INGESTING,
                AgentType.UNDERSTANDING: WorkflowStatus.UNDERSTANDING,
                AgentType.SCRIPT: WorkflowStatus.SCRIPTING,
                AgentType.VISUAL_PLANNING: WorkflowStatus.PLANNING,
                AgentType.MANIM: WorkflowStatus.ANIMATING,
                AgentType.MOTION_CANVAS: WorkflowStatus.ANIMATING,
                AgentType.REMOTION: WorkflowStatus.ANIMATING,
                AgentType.VOICE: WorkflowStatus.AUDIO_PROCESSING,
                AgentType.TRANSITION: WorkflowStatus.VIDEO_COMPOSING,
                AgentType.METADATA: WorkflowStatus.METADATA_GENERATING,
                AgentType.YOUTUBE: WorkflowStatus.UPLOADING,
            }
            
            new_status = status_map.get(agent_type, state.progress.current_step)
            state.progress.update_progress(new_status, 0.0, f"Starting {agent.name}")
            
            # Execute with retry logic
            for attempt in range(self.config.system.retry_attempts + 1):
                try:
                    # Execute agent
                    result_state = await agent.safe_execute(state)
                    
                    # Mark step as completed
                    state.progress.complete_step(new_status)
                    state.progress.update_progress(new_status, 1.0, f"Completed {agent.name}")
                    
                    return result_state
                    
                except Exception as error:
                    # Handle retry logic
                    if attempt < self.config.system.retry_attempts and agent.should_retry(error, attempt):
                        delay = agent.get_retry_delay(attempt)
                        state.progress.update_progress(
                            new_status, 
                            0.0, 
                            f"Retrying {agent.name} in {delay:.1f}s (attempt {attempt + 1})"
                        )
                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Final failure
                        state = agent.handle_error(error, state)
                        state.progress.update_progress(
                            WorkflowStatus.FAILED,
                            0.0,
                            f"Failed: {agent.name} - {str(error)}"
                        )
                        raise
            
            return state
        
        return agent_node
    
    def _route_animation(self, state: RASOMasterState) -> str:
        """
        Route to appropriate animation agents based on visual plan.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if not state.visual_plan or not state.visual_plan.scenes:
            return "voice"  # Skip animation if no visual plan
        
        # Check which frameworks are needed
        frameworks = set()
        for scene in state.visual_plan.scenes:
            frameworks.add(scene.framework.value)
        
        # Route based on frameworks needed
        if len(frameworks) == 1:
            framework = list(frameworks)[0]
            if framework == "manim":
                return "manim"
            elif framework == "motion-canvas":
                return "motion_canvas"
            elif framework == "remotion":
                return "remotion"
        
        # Multiple frameworks needed - start with parallel processing
        return "parallel"
    
    def _check_animation_complete(self, state: RASOMasterState) -> str:
        """
        Check if all required animations are complete.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        if not state.visual_plan or not state.visual_plan.scenes:
            return "voice"
        
        # Get required frameworks
        required_frameworks = set()
        for scene in state.visual_plan.scenes:
            required_frameworks.add(scene.framework.value)
        
        # Check completed frameworks
        completed_frameworks = set()
        if state.animations:
            for scene in state.animations.scenes:
                if scene.is_completed:
                    completed_frameworks.add(scene.framework)
        
        # Determine next framework to process
        remaining = required_frameworks - completed_frameworks
        
        if "motion-canvas" in remaining:
            return "continue_motion"
        elif "remotion" in remaining:
            return "continue_remotion"
        else:
            return "voice"
    
    def _should_upload_youtube(self, state: RASOMasterState) -> str:
        """
        Determine if YouTube upload should be performed.
        
        Args:
            state: Current workflow state
            
        Returns:
            Next node name
        """
        # Check if auto-upload is enabled and YouTube is configured
        if (state.options.auto_upload and 
            self.config.youtube and 
            self.config.youtube.is_configured):
            return "upload"
        else:
            return "end"
    
    async def execute_workflow(self, initial_state: RASOMasterState, 
                             config: Optional[Dict[str, Any]] = None) -> RASOMasterState:
        """
        Execute the complete workflow.
        
        Args:
            initial_state: Initial workflow state
            config: Optional execution configuration
            
        Returns:
            Final workflow state
        """
        try:
            # Set up execution configuration
            exec_config = {
                "configurable": {
                    "thread_id": initial_state.job_id,
                    "checkpoint_ns": "raso_workflow",
                }
            }
            if config:
                exec_config.update(config)
            
            # Compile the graph with checkpointing
            compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
            
            # Execute the workflow
            final_state = None
            async for state in compiled_graph.astream(initial_state, config=exec_config):
                final_state = state
                
                # Check for timeout
                if self._is_timeout_exceeded(initial_state):
                    raise AgentExecutionError(
                        "Workflow execution timeout exceeded",
                        "WORKFLOW_TIMEOUT",
                        ErrorSeverity.CRITICAL
                    )
                
                # Check for abort conditions
                if state.should_abort():
                    raise AgentExecutionError(
                        "Workflow aborted due to critical errors",
                        "WORKFLOW_ABORTED",
                        ErrorSeverity.CRITICAL
                    )
            
            # Mark as completed if successful
            if final_state and not final_state.has_critical_errors():
                final_state.progress.update_progress(
                    WorkflowStatus.COMPLETED,
                    1.0,
                    "Workflow completed successfully"
                )
            
            return final_state or initial_state
            
        except Exception as error:
            # Handle workflow-level errors
            initial_state.add_error(
                agent_type=AgentType.INGEST,  # Use a default agent type
                error_code="WORKFLOW_ERROR",
                message=f"Workflow execution failed: {str(error)}",
                severity=ErrorSeverity.CRITICAL,
            )
            
            initial_state.progress.update_progress(
                WorkflowStatus.FAILED,
                0.0,
                f"Workflow failed: {str(error)}"
            )
            
            return initial_state
    
    def _is_timeout_exceeded(self, initial_state: RASOMasterState) -> bool:
        """
        Check if workflow execution has exceeded timeout.
        
        Args:
            initial_state: Initial workflow state
            
        Returns:
            True if timeout exceeded
        """
        elapsed = datetime.now() - initial_state.created_at
        timeout = timedelta(minutes=initial_state.options.timeout_minutes)
        return elapsed > timeout
    
    async def get_workflow_status(self, job_id: str) -> Optional[RASOMasterState]:
        """
        Get current workflow status by job ID.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Current state or None if not found
        """
        try:
            # Get state from checkpointer
            config = {
                "configurable": {
                    "thread_id": job_id,
                    "checkpoint_ns": "raso_workflow",
                }
            }
            
            compiled_graph = self.graph.compile(checkpointer=self.checkpointer)
            state_snapshot = compiled_graph.get_state(config)
            
            if state_snapshot and state_snapshot.values:
                return state_snapshot.values
            
            return None
            
        except Exception:
            return None
    
    async def cancel_workflow(self, job_id: str) -> bool:
        """
        Cancel a running workflow.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if cancelled successfully
        """
        try:
            # Get current state
            current_state = await self.get_workflow_status(job_id)
            if not current_state:
                return False
            
            # Update state to cancelled
            current_state.progress.update_progress(
                WorkflowStatus.CANCELLED,
                0.0,
                "Workflow cancelled by user"
            )
            
            # Note: LangGraph doesn't have built-in cancellation,
            # so we rely on agents checking the state status
            return True
            
        except Exception:
            return False


# Global workflow orchestrator instance
workflow_orchestrator = WorkflowOrchestrator()