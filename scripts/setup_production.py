#!/usr/bin/env python3
"""
Production Setup Script for RASO Platform

This script sets up the RASO platform for production use by:
1. Installing required dependencies
2. Setting up external services
3. Configuring production settings
4. Verifying system requirements
"""

import os
import sys
import subprocess
import platform
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and handle errors."""
    print(f"🔧 {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed: {e.stderr}")
        return False


def check_system_requirements():
    """Check system requirements for production."""
    print("🔍 Checking system requirements...")
    
    requirements = {
        "Python": sys.version_info >= (3, 8),
        "Platform": platform.system() in ["Windows", "Darwin", "Linux"],
    }
    
    # Check for ffmpeg
    try:
        subprocess.run(["ffmpeg", "-version"], capture_output=True, check=True)
        requirements["FFmpeg"] = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        requirements["FFmpeg"] = False
        print("⚠️  FFmpeg not found. Please install FFmpeg for video processing.")
        print("   Windows: Download from https://ffmpeg.org/download.html")
        print("   macOS: brew install ffmpeg")
        print("   Linux: sudo apt install ffmpeg")
    
    # Check for system TTS
    system = platform.system().lower()
    if system == "windows":
        requirements["System TTS"] = True  # Windows SAPI always available
    elif system == "darwin":
        try:
            subprocess.run(["say", "--version"], capture_output=True, check=True)
            requirements["System TTS"] = True
        except:
            requirements["System TTS"] = False
    elif system == "linux":
        try:
            subprocess.run(["espeak", "--version"], capture_output=True, check=True)
            requirements["System TTS"] = True
        except:
            requirements["System TTS"] = False
            print("⚠️  espeak not found. Install with: sudo apt install espeak espeak-data")
    
    # Print results
    all_good = True
    for req, status in requirements.items():
        status_icon = "✅" if status else "❌"
        print(f"  {status_icon} {req}")
        if not status:
            all_good = False
    
    return all_good


def install_python_dependencies():
    """Install Python dependencies for production."""
    print("📦 Installing Python dependencies...")
    
    # Upgrade pip first
    if not run_command(f"{sys.executable} -m pip install --upgrade pip", "Upgrading pip"):
        return False
    
    # Install production requirements
    if not run_command(f"{sys.executable} -m pip install -r requirements.txt", "Installing requirements"):
        return False
    
    # Try to install TTS (might fail on some systems)
    print("🎤 Installing TTS (Coqui TTS)...")
    tts_success = run_command(f"{sys.executable} -m pip install TTS", "Installing TTS")
    if not tts_success:
        print("⚠️  TTS installation failed. System TTS will be used as fallback.")
    
    return True


def setup_directories():
    """Create necessary directories for production."""
    print("📁 Setting up directories...")
    
    directories = [
        "data/videos",
        "data/audio", 
        "data/animations",
        "temp/audio",
        "temp/video_composition",
        "logs",
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"  ✅ Created {directory}")
    
    return True


def create_production_config():
    """Create production configuration template."""
    print("⚙️  Creating production configuration...")
    
    env_template = """# RASO Production Configuration

# Environment
RASO_ENV=production
RASO_DEBUG=false
RASO_LOG_LEVEL=INFO

# API Configuration
RASO_API_HOST=0.0.0.0
RASO_API_PORT=8000
RASO_API_WORKERS=4

# Database
RASO_DATABASE_URL=redis://localhost:6379/0
# RASO_REDIS_PASSWORD=your_redis_password

# Paths
RASO_DATA_PATH=./data
RASO_TEMP_PATH=./temp
RASO_LOG_PATH=./logs

# Security
RASO_SECRET_KEY=your_production_secret_key_here
RASO_CORS_ORIGINS=["https://yourdomain.com"]

# LLM Configuration
RASO_LLM_PROVIDER=ollama
RASO_OLLAMA_URL=http://localhost:11434
RASO_OLLAMA_MODEL=deepseek-coder:6.7b

# OpenAI (optional)
# RASO_OPENAI_API_KEY=your_openai_key

# Audio Configuration
RASO_AUDIO_TTS_PROVIDER=coqui
RASO_AUDIO_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
RASO_AUDIO_SAMPLE_RATE=22050
RASO_AUDIO_VOICE_SPEED=1.0

# Video Configuration
RASO_VIDEO_CODEC=libx264
RASO_VIDEO_BITRATE=5000k
RASO_VIDEO_PRESET=medium

# YouTube Integration (optional)
# RASO_YOUTUBE_CLIENT_ID=your_youtube_client_id
# RASO_YOUTUBE_CLIENT_SECRET=your_youtube_client_secret
# RASO_YOUTUBE_REFRESH_TOKEN=your_youtube_refresh_token

# Animation Configuration
RASO_ANIMATION_RESOLUTION=1920x1080
RASO_ANIMATION_FPS=30
RASO_ANIMATION_QUALITY=high

# System Configuration
RASO_MAX_CONCURRENT_JOBS=2
RASO_JOB_TIMEOUT_MINUTES=120
RASO_RETRY_ATTEMPTS=3
"""
    
    env_file = Path(".env.production")
    if not env_file.exists():
        env_file.write_text(env_template)
        print(f"  ✅ Created {env_file}")
        print("  📝 Please edit .env.production with your actual configuration values")
    else:
        print(f"  ⚠️  {env_file} already exists, skipping")
    
    return True


def setup_systemd_service():
    """Create systemd service file for Linux."""
    if platform.system() != "Linux":
        return True
    
    print("🐧 Creating systemd service file...")
    
    service_content = f"""[Unit]
Description=RASO Research Paper Video Generation Platform
After=network.target

[Service]
Type=simple
User=raso
WorkingDirectory={Path.cwd()}
Environment=PATH={Path.cwd()}/.venv/bin
ExecStart={Path.cwd()}/.venv/bin/python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
"""
    
    service_file = Path("raso.service")
    service_file.write_text(service_content)
    print(f"  ✅ Created {service_file}")
    print("  📝 To install: sudo cp raso.service /etc/systemd/system/")
    print("  📝 To enable: sudo systemctl enable raso")
    print("  📝 To start: sudo systemctl start raso")
    
    return True


def create_docker_files():
    """Create Docker configuration for production deployment."""
    print("🐳 Creating Docker configuration...")
    
    dockerfile = """FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    ffmpeg \\
    espeak \\
    espeak-data \\
    libsndfile1 \\
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data/videos data/audio data/animations temp/audio temp/video_composition logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
"""
    
    docker_compose = """version: '3.8'

services:
  raso:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./temp:/app/temp
      - ./logs:/app/logs
    environment:
      - RASO_ENV=production
      - RASO_DATABASE_URL=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    environment:
      - REACT_APP_API_URL=http://localhost:8000
    restart: unless-stopped

volumes:
  redis_data:
"""
    
    Path("Dockerfile").write_text(dockerfile)
    Path("docker-compose.prod.yml").write_text(docker_compose)
    
    print("  ✅ Created Dockerfile")
    print("  ✅ Created docker-compose.prod.yml")
    print("  📝 To run: docker-compose -f docker-compose.prod.yml up -d")
    
    return True


def verify_installation():
    """Verify the production installation."""
    print("🔍 Verifying installation...")
    
    # Test imports
    try:
        import fastapi
        import uvicorn
        import pydantic
        print("  ✅ Core dependencies imported successfully")
    except ImportError as e:
        print(f"  ❌ Core dependency import failed: {e}")
        return False
    
    # Test TTS
    try:
        from TTS.api import TTS
        print("  ✅ TTS (Coqui) available")
    except ImportError:
        print("  ⚠️  TTS (Coqui) not available, will use system TTS")
    
    # Test video processing
    try:
        import cv2
        print("  ✅ OpenCV available")
    except ImportError:
        print("  ❌ OpenCV not available")
        return False
    
    # Test YouTube API
    try:
        from googleapiclient.discovery import build
        print("  ✅ YouTube API client available")
    except ImportError:
        print("  ⚠️  YouTube API client not available")
    
    return True


def main():
    """Main setup function."""
    print("🚀 RASO Production Setup")
    print("=" * 50)
    
    steps = [
        ("System Requirements", check_system_requirements),
        ("Python Dependencies", install_python_dependencies),
        ("Directory Setup", setup_directories),
        ("Production Config", create_production_config),
        ("Systemd Service", setup_systemd_service),
        ("Docker Files", create_docker_files),
        ("Installation Verification", verify_installation),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        print(f"\n📋 Step: {step_name}")
        print("-" * 30)
        
        if not step_func():
            failed_steps.append(step_name)
            print(f"❌ {step_name} failed")
        else:
            print(f"✅ {step_name} completed")
    
    print("\n" + "=" * 50)
    
    if failed_steps:
        print("❌ Setup completed with issues:")
        for step in failed_steps:
            print(f"  - {step}")
        print("\n📝 Please resolve the issues above before running in production.")
    else:
        print("🎉 Production setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env.production with your configuration")
        print("2. Set up external services (Redis, Ollama, etc.)")
        print("3. Configure YouTube API credentials (optional)")
        print("4. Start the service:")
        print("   - Direct: python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000")
        print("   - Docker: docker-compose -f docker-compose.prod.yml up -d")
        print("   - Systemd: sudo systemctl start raso")


if __name__ == "__main__":
    main()