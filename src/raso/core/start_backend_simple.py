#!/usr/bin/env python3
"""
Simple backend startup script without auto-reload.
"""

import sys
import os
from pathlib import Path

# Set up Python path
src_path = str(Path.cwd() / "src")
config_path = str(Path.cwd() / "config")
current_path = os.environ.get('PYTHONPATH', '')
if current_path:
    new_path = os.pathsep.join([src_path, config_path, current_path])
else:
    new_path = os.pathsep.join([src_path, config_path])
os.environ['PYTHONPATH'] = new_path

# Set environment variables
os.environ['RASO_ENV'] = 'development'
os.environ['RASO_API_HOST'] = '0.0.0.0'
os.environ['RASO_API_PORT'] = '8000'
os.environ['RASO_DEBUG'] = 'true'
os.environ['RASO_LOG_LEVEL'] = 'INFO'
os.environ['RASO_LLM_PROVIDER'] = 'google'

print("🚀 Starting RASO Backend (Simple Mode)")
print("📊 Backend API: http://localhost:8000")
print("📚 API Docs: http://localhost:8000/docs")
print("🔍 Health Check: http://localhost:8000/health")

# Start uvicorn without reload
import uvicorn
uvicorn.run(
    "config.backend.main:app",
    host="0.0.0.0",
    port=8000,
    reload=False  # Disable auto-reload
)