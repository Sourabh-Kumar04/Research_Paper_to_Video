#!/usr/bin/env python3
"""
Minimal RASO Backend for API Testing
"""

import sys
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Set up Python path
src_path = str(Path.cwd() / "src")
config_path = str(Path.cwd() / "config")
sys.path.insert(0, src_path)
sys.path.insert(0, config_path)

# Import models
try:
    from config.backend.models.paper import PaperInput
except ImportError:
    # Fallback minimal model
    from pydantic import BaseModel, Field
    from enum import Enum
    
    class PaperInputType(str, Enum):
        TITLE = "title"
        ARXIV = "arxiv"
        PDF = "pdf"
    
    class PaperInput(BaseModel):
        type: PaperInputType = Field(..., description="Type of paper input")
        content: str = Field(..., description="Paper content")
        options: Optional[Dict] = Field(default=None, description="Processing options")

# FastAPI app
app = FastAPI(
    title="RASO Platform API",
    description="Research paper Automated Simulation & Orchestration Platform",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory job storage
jobs: Dict[str, Dict] = {}

class JobRequest(BaseModel):
    paper_input: PaperInput
    options: Optional[Dict] = None

class JobResponse(BaseModel):
    job_id: str
    status: str
    created_at: datetime

class JobStatus(BaseModel):
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
    return {"message": "RASO Platform API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now(),
        "features": {
            "cinematic_video_generation": "active",
            "youtube_optimization": "active",
            "social_media_adaptation": "active",
            "accessibility_compliance": "active",
            "ai_powered_recommendations": "active"
        }
    }

@app.post("/api/jobs", response_model=JobResponse)
async def submit_job(job_request: JobRequest, background_tasks: BackgroundTasks):
    job_id = str(uuid.uuid4())
    
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
    
    # Start mock processing
    background_tasks.add_task(mock_process_job, job_id)
    
    return JobResponse(
        job_id=job_id,
        status="queued",
        created_at=job_data["created_at"],
    )

@app.get("/api/jobs/{job_id}", response_model=JobStatus)
async def get_job_status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatus(**jobs[job_id])

@app.get("/api/jobs")
async def list_jobs():
    return {"jobs": list(jobs.values())}

async def mock_process_job(job_id: str):
    """Mock job processing for demonstration."""
    import asyncio
    
    job_data = jobs[job_id]
    
    # Simulate processing stages
    stages = [
        ("Understanding Agent", 20),
        ("Script Generation", 40),
        ("Visual Planning", 60),
        ("Cinematic Enhancement", 80),
        ("Final Composition", 100)
    ]
    
    for agent, progress in stages:
        await asyncio.sleep(2)  # Simulate processing time
        job_data["current_agent"] = agent
        job_data["progress"] = progress
        job_data["status"] = "processing"
        job_data["updated_at"] = datetime.now()
    
    # Complete the job
    job_data["status"] = "completed"
    job_data["current_agent"] = None
    job_data["result"] = {
        "video": {
            "file_path": f"/tmp/mock_video_{job_id[:8]}.mp4",
            "duration": 180,
            "resolution": "1920x1080",
            "metadata": {
                "title": job_data["paper_input"]["content"],
                "cinematic_features": ["color_grading", "camera_movements", "sound_design"],
                "platforms_optimized": ["youtube", "instagram", "tiktok"],
                "accessibility_features": ["captions", "audio_descriptions"]
            }
        },
        "youtube_url": None,
        "social_media_variants": {
            "instagram": f"/tmp/mock_instagram_{job_id[:8]}.mp4",
            "tiktok": f"/tmp/mock_tiktok_{job_id[:8]}.mp4"
        }
    }
    job_data["updated_at"] = datetime.now()

# Cinematic API endpoints
@app.post("/api/v1/cinematic/settings")
async def manage_cinematic_settings(settings: Dict):
    return {
        "status": "success",
        "message": "Cinematic settings updated",
        "settings": settings,
        "features_enabled": [
            "enhanced_camera_movements",
            "professional_color_grading", 
            "spatial_audio_design",
            "film_grain_effects"
        ]
    }

@app.post("/api/v1/cinematic/visual-description")
async def generate_visual_description(request: Dict):
    return {
        "status": "success",
        "description": "A cinematic sequence featuring smooth camera movements and professional color grading, with warm golden hour lighting that creates depth and visual interest. The composition uses rule of thirds and leading lines to guide the viewer's attention.",
        "cinematic_techniques": [
            "Golden hour lighting",
            "Rule of thirds composition",
            "Smooth camera pans",
            "Depth of field effects"
        ],
        "confidence": 0.92
    }

@app.post("/api/v1/cinematic/scene-analysis")
async def analyze_scene(request: Dict):
    return {
        "status": "success",
        "analysis": {
            "content_type": "educational",
            "recommended_style": "documentary",
            "camera_movements": ["slow_pan", "zoom_in"],
            "color_palette": "warm_professional",
            "pacing": "moderate"
        },
        "recommendations": [
            "Use warm color grading for educational content",
            "Implement slow camera movements for clarity",
            "Add subtle background music"
        ]
    }

@app.post("/api/v1/cinematic/preview")
async def generate_preview(request: Dict):
    return {
        "status": "success",
        "preview_url": f"/tmp/preview_{uuid.uuid4().hex[:8]}.mp4",
        "thumbnail_url": f"/tmp/thumb_{uuid.uuid4().hex[:8]}.jpg",
        "duration": 30,
        "effects_applied": [
            "color_grading",
            "camera_movement",
            "audio_enhancement"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting RASO Minimal Backend")
    print("📊 Backend API: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print("🎬 Cinematic Features: Enabled")
    
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)