"""
RASO Master Workflow using LangGraph.

Orchestrates the complete video generation pipeline from paper input to final output.
"""

import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from langgraph.graph import StateGraph, END

from config.backend.models.state import RASOMasterState, AgentType
from agents.ingest import IngestAgent
from agents.understanding import UnderstandingAgent
from agents.script import ScriptAgent
from agents.visual_planning import VisualPlanningAgent
from agents.rendering import RenderingCoordinator
from agents.audio import AudioAgent
from agents.video_composition import VideoCompositionAgent
from agents.metadata import MetadataAgent
from agents.youtube import YouTubeAgent
from config.backend.config import get_config


class RASOMasterWorkflow:
    """Master workflow for RASO platform."""
    
    def __init__(self):
        """Initialize the workflow."""
        self.config = get_config()
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the LangGraph workflow."""
        # Create state graph
        workflow = StateGraph(RASOMasterState)
        
        # Add nodes (agents)
        workflow.add_node("ingest", IngestAgent(AgentType.INGEST).execute)
        workflow.add_node("understanding", UnderstandingAgent(AgentType.UNDERSTANDING).execute)
        workflow.add_node("script", ScriptAgent(AgentType.SCRIPT).execute)
        workflow.add_node("visual_planning", VisualPlanningAgent(AgentType.VISUAL_PLANNING).execute)
        workflow.add_node("rendering", RenderingCoordinator(AgentType.MANIM).execute)
        workflow.add_node("audio", AudioAgent(AgentType.VOICE).execute)
        workflow.add_node("video_composition", VideoCompositionAgent(AgentType.TRANSITION).execute)
        workflow.add_node("metadata", MetadataAgent(AgentType.METADATA).execute)
        workflow.add_node("youtube", YouTubeAgent(AgentType.YOUTUBE).execute)
        
        # Define the workflow edges
        workflow.set_entry_point("ingest")
        
        workflow.add_edge("ingest", "understanding")
        workflow.add_edge("understanding", "script")
        workflow.add_edge("script", "visual_planning")
        workflow.add_edge("visual_planning", "rendering")
        workflow.add_edge("rendering", "audio")
        workflow.add_edge("audio", "video_composition")
        workflow.add_edge("video_composition", "metadata")
        workflow.add_edge("metadata", "youtube")
        workflow.add_edge("youtube", END)
        
        # Compile the graph
        return workflow.compile()
    
    async def execute(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the complete workflow."""
        try:
            # Convert to RASOMasterState
            state = RASOMasterState(**initial_state)
            
            # Execute the graph
            result = await self.graph.ainvoke(state.dict())
            
            return result
            
        except Exception as e:
            return {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            }
    
    async def execute_with_progress(
        self, 
        initial_state: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute workflow with progress updates."""
        try:
            state = RASOMasterState(**initial_state)
            
            # Define progress stages
            stages = [
                ("ingest", 10),
                ("understanding", 20),
                ("script", 30),
                ("visual_planning", 40),
                ("rendering", 60),
                ("audio", 75),
                ("video_composition", 85),
                ("metadata", 95),
                ("youtube", 100),
            ]
            
            current_progress = 0
            
            # Execute each stage
            for stage_name, target_progress in stages:
                # Update progress
                state.progress.overall_progress = current_progress / 100.0
                state.current_agent = AgentType(stage_name) if stage_name in [e.value for e in AgentType] else None
                state.update_timestamp()
                
                # Yield current state as dict
                state_dict = state.dict()
                state_dict["progress"] = current_progress
                state_dict["current_agent"] = stage_name
                yield state_dict
                
                # Execute the stage with proper state object
                try:
                    if stage_name == "ingest":
                        state = await IngestAgent(AgentType.INGEST).execute(state)
                    elif stage_name == "understanding":
                        state = await UnderstandingAgent(AgentType.UNDERSTANDING).execute(state)
                    elif stage_name == "script":
                        state = await ScriptAgent(AgentType.SCRIPT).execute(state)
                    elif stage_name == "visual_planning":
                        state = await VisualPlanningAgent(AgentType.VISUAL_PLANNING).execute(state)
                    elif stage_name == "rendering":
                        state = await RenderingCoordinator(AgentType.MANIM).execute(state)
                    elif stage_name == "audio":
                        state = await AudioAgent(AgentType.VOICE).execute(state)
                    elif stage_name == "video_composition":
                        state = await VideoCompositionAgent(AgentType.TRANSITION).execute(state)
                    elif stage_name == "metadata":
                        print(f"🔍 Starting metadata stage...")
                        state = await MetadataAgent(AgentType.METADATA).execute(state)
                        print(f"✅ Metadata stage completed successfully")
                    elif stage_name == "youtube":
                        print(f"🔍 Starting youtube stage...")
                        state = await YouTubeAgent(AgentType.YOUTUBE).execute(state)
                        print(f"✅ YouTube stage completed successfully")
                except Exception as e:
                    # Log the specific error and stage with full traceback
                    print(f"❌ Error in stage {stage_name}: {str(e)}")
                    import traceback
                    error_traceback = traceback.format_exc()
                    print(f"Full traceback:\n{error_traceback}")
                    raise e
                
                current_progress = target_progress
            
            # Final result
            state_dict["progress"] = 100
            state_dict["status"] = "completed"
            yield state_dict
            
        except Exception as e:
            yield {
                "status": "failed",
                "error": str(e),
                "progress": current_progress,
                "timestamp": datetime.now().isoformat(),
            }