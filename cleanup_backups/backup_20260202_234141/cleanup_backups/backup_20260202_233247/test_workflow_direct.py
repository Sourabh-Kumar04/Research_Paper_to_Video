#!/usr/bin/env python3
"""
Direct workflow test to see full error traceback
"""

import asyncio
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path.cwd() / "src"))
sys.path.insert(0, str(Path.cwd() / "config"))

from config.backend.models.paper import PaperInput
from graph.master_workflow import RASOMasterWorkflow

async def test_workflow():
    """Test workflow directly"""
    print("Testing workflow directly...")
    
    # Create workflow
    workflow = RASOMasterWorkflow()
    
    # Create initial state
    paper_input = PaperInput(
        type="title",
        content="Attention Is All You Need"
    )
    
    initial_state = {
        "paper_input": paper_input,
        "options": {"quality": "medium", "duration": 120},
        "job_id": "test-direct",
    }
    
    # Execute workflow with progress tracking
    try:
        async for state in workflow.execute_with_progress(initial_state):
            progress = state.get("progress", 0)
            current_agent = state.get("current_agent", "unknown")
            status = state.get("status", "processing")
            
            print(f"Progress: {progress}% | Agent: {current_agent} | Status: {status}")
            
            if status == "failed":
                print(f"ERROR: Workflow failed: {state.get('error')}")
                return False
        
        print("SUCCESS: Workflow completed successfully!")
        return True
        
    except Exception as e:
        print(f"EXCEPTION occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(test_workflow())
    sys.exit(0 if success else 1)
