"""
RASO Platform FastAPI Backend

Main API application for job submission, status tracking, and asset management.
"""

import asyncio
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from config.backend.config import get_config
from config.backend.models.paper import PaperInput
from graph.master_workflow import RASOMasterWorkflow


# Configuration
config = get_config()

# FastAPI app
app = FastAPI(
    title="RASO Platform API",
    description="Research paper Automated Simulation & Orchestration Platform",
    version="1.0.0",
)

# CORS middleware - Allow all origins for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage (would use Redis/database in production)
jobs: Dict[str, Dict] = {}


class JobRequest(BaseModel):
    """Job submission request."""
    paper_input: PaperInput
    options: Optional[Dict] = None


class JobResponse(BaseModel):
    """Job submission response."""
    job_id: str
    status: str
    created_at: datetime


class JobStatus(BaseModel):
    """Job status response."""
    job_id: str
    status: str
    progress: float
    current_agent: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    result: Optional[Dict] = None


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "RASO Platform API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now()}


@app.post("/api/jobs", response_model=JobResponse)
async def submit_job(job_request: JobRequest, background_tasks: BackgroundTasks):
    """Submit a new video generation job."""
    import uuid
    
    job_id = str(uuid.uuid4())
    
    # Create job record
    job_data = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "current_agent": None,
        "created_at": datetime.now(),
        "updated_at": datetime.now(),
        "paper_input": job_request.paper_input.dict(),
        "options": job_request.options or {},
        "error_message": None,
        "result": None,
    }
    
    jobs[job_id] = job_data
    
    # Start processing in background
    background_tasks.add_task(process_job, job_id)
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        created_at=job_data["created_at"],
    )


@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    """Get job status."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs[job_id]
    
    return JobStatus(**job_data)


@app.get("/api/jobs")
async def list_jobs():
    """List all jobs."""
    return {"jobs": list(jobs.values())}


@app.get("/api/jobs/{job_id}/download")
async def download_video(job_id: str):
    """Download generated video."""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job_data = jobs[job_id]
    
    if job_data["status"] != "completed":
        raise HTTPException(status_code=400, detail="Job not completed")
    
    if not job_data.get("result", {}).get("video", {}).get("file_path"):
        raise HTTPException(status_code=404, detail="Video file not found")
    
    video_path = job_data["result"]["video"]["file_path"]
    
    # Handle mock video files for testing (backward compatibility)
    if video_path.startswith("/tmp/mock_"):
        return {
            "message": "Mock video download - file would be served in production",
            "video_path": video_path,
            "job_id": job_id,
            "note": "This is a mock response for testing the RASO pipeline"
        }
    
    # Check if real video file exists
    if not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    
    # Get video metadata for proper filename
    video_metadata = job_data.get("result", {}).get("video", {}).get("metadata", {})
    title = video_metadata.get("title", "raso_video")
    
    # Create safe filename
    safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '-', '_')).rstrip()
    safe_title = safe_title.replace(' ', '_')[:50]
    filename = f"{safe_title}_{job_id[:8]}.mp4"
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f"attachment; filename={filename}",
            "Cache-Control": "no-cache"
        }
    )


async def process_job(job_id: str):
    """Process a job in the background."""
    try:
        job_data = jobs[job_id]
        job_data["status"] = "processing"
        job_data["updated_at"] = datetime.now()
        
        # Create workflow
        workflow = RASOMasterWorkflow()
        
        # Initialize state with proper object conversion
        paper_input_data = job_data["paper_input"]
        paper_input = PaperInput(**paper_input_data)
        
        initial_state = {
            "paper_input": paper_input,
            "options": job_data.get("options", {}),
            "job_id": job_id,
        }
        
        # Execute workflow with progress tracking
        final_state = {}
        async for state in workflow.execute_with_progress(initial_state):
            final_state = state
            # Update job progress
            job_data["current_agent"] = state.get("current_agent")
            job_data["progress"] = state.get("progress", 0.0)
            job_data["updated_at"] = datetime.now()
        
        if final_state.get("status") == "failed":
            # Job failed
            job_data["status"] = "failed"
            job_data["error_message"] = final_state.get("error")
            # Log detailed error for debugging
            import traceback
            print(f"❌ Job {job_id} failed: {final_state.get('error')}")
            if "traceback" in final_state:
                print(f"Traceback: {final_state.get('traceback')}")
        else:
            # Job completed successfully
            job_data["status"] = "completed"
            job_data["progress"] = 100.0
            job_data["result"] = {
                "video": final_state.get("video"),
                "metadata": final_state.get("metadata"),
                "youtube_url": final_state.get("youtube_url"),
            }
        
        job_data["updated_at"] = datetime.now()
        
    except Exception as e:
        # Unexpected error - log full traceback
        import traceback
        error_traceback = traceback.format_exc()
        print(f"❌ Unexpected error in job {job_id}:")
        print(error_traceback)
        
        job_data["status"] = "failed"
        job_data["error_message"] = f"{str(e)}\n\nTraceback:\n{error_traceback}"
        job_data["updated_at"] = datetime.now()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.is_development,
    )