"""
RASO Master Workflow using LangGraph.

Orchestrates the complete video generation pipeline from paper input to final output.
"""

import asyncio
from typing import Dict, Any, AsyncGenerator
from datetime import datetime

from langgraph import StateGraph, END
from langgraph.graph import CompiledGraph

from backend.models.state import RASOMasterState
from agents.ingest import IngestAgent
from agents.understanding import UnderstandingAgent
from agents.script import ScriptAgent
from agents.visual_planning import VisualPlanningAgent
from agents.rendering import RenderingCoordinator
from agents.audio import AudioAgent
from agents.video_composition import VideoCompositionAgent
from agents.metadata import MetadataAgent
from agents.youtube import YouTubeAgent
from backend.config import get_config


class RASOMasterWorkflow:
    """Master workflow for RASO platform."""
    
    def __init__(self):
        """Initialize the workflow."""
        self.config = get_config()
        self.graph = self._build_graph()
    
    def _build_graph(self) -> CompiledGraph:
        """Build the LangGraph workflow."""
        # Create state graph
        workflow = StateGraph(RASOMasterState)
        
        # Add nodes (agents)
        workflow.add_node("ingest", IngestAgent().execute)
        workflow.add_node("understanding", UnderstandingAgent().execute)
        workflow.add_node("script", ScriptAgent().execute)
        workflow.add_node("visual_planning", VisualPlanningAgent().execute)
        workflow.add_node("rendering", RenderingCoordinator().execute)
        workflow.add_node("audio", AudioAgent().execute)
        workflow.add_node("video_composition", VideoCompositionAgent().execute)
        workflow.add_node("metadata", MetadataAgent().execute)
        workflow.add_node("youtube", YouTubeAgent().execute)
        
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
                state_dict = state.dict()
                state_dict["progress"] = current_progress
                state_dict["current_agent"] = stage_name
                
                yield state_dict
                
                # Execute the stage
                if stage_name == "ingest":
                    result = await IngestAgent().execute(state_dict)
                elif stage_name == "understanding":
                    result = await UnderstandingAgent().execute(state_dict)
                elif stage_name == "script":
                    result = await ScriptAgent().execute(state_dict)
                elif stage_name == "visual_planning":
                    result = await VisualPlanningAgent().execute(state_dict)
                elif stage_name == "rendering":
                    result = await RenderingCoordinator().execute(state_dict)
                elif stage_name == "audio":
                    result = await AudioAgent().execute(state_dict)
                elif stage_name == "video_composition":
                    result = await VideoCompositionAgent().execute(state_dict)
                elif stage_name == "metadata":
                    result = await MetadataAgent().execute(state_dict)
                elif stage_name == "youtube":
                    result = await YouTubeAgent().execute(state_dict)
                
                # Update state with results
                state_dict.update(result)
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