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

from backend.config import get_config
from backend.models.paper import PaperInput
from graph.master_workflow import RASOMasterWorkflow


# Configuration
config = get_config()

# FastAPI app
app = FastAPI(
    title="RASO Platform API",
    description="Research paper Automated Simulation & Orchestration Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.cors_origins,
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
    
    if not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found on disk")
    
    return FileResponse(
        video_path,
        media_type="video/mp4",
        filename=f"raso_video_{job_id}.mp4",
    )


async def process_job(job_id: str):
    """Process a job in the background."""
    try:
        job_data = jobs[job_id]
        job_data["status"] = "processing"
        job_data["updated_at"] = datetime.now()
        
        # Create workflow
        workflow = RASOMasterWorkflow()
        
        # Initialize state
        initial_state = {
            "paper_input": job_data["paper_input"],
            "options": job_data["options"],
            "job_id": job_id,
        }
        
        # Execute workflow with progress tracking
        async for state in workflow.execute_with_progress(initial_state):
            # Update job progress
            job_data["current_agent"] = state.get("current_agent")
            job_data["progress"] = state.get("progress", 0.0)
            job_data["updated_at"] = datetime.now()
        
        # Job completed successfully
        job_data["status"] = "completed"
        job_data["progress"] = 100.0
        job_data["result"] = {
            "video": state.get("video"),
            "metadata": state.get("metadata"),
            "youtube_url": state.get("youtube_url"),
        }
        job_data["updated_at"] = datetime.now()
        
    except Exception as e:
        # Job failed
        job_data["status"] = "failed"
        job_data["error_message"] = str(e)
        job_data["updated_at"] = datetime.now()


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=config.api_host,
        port=config.api_port,
        reload=config.is_development,
    )