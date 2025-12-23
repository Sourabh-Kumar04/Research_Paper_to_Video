#!/usr/bin/env python3
"""
RASO Platform Startup Script

Quick start script for the RASO platform with automatic dependency checking.
"""

import os
import sys
import subprocess
import asyncio
from pathlib import Path

def check_python_version():
    """Check Python version compatibility."""
    if sys.version_info < (3, 9):
        print("❌ Python 3.9+ required. Current version:", sys.version)
        return False
    print("✅ Python version:", sys.version.split()[0])
    return True

def check_dependencies():
    """Check system dependencies."""
    dependencies = {
        'ffmpeg': 'FFmpeg (video processing)',
        'node': 'Node.js (frontend)',
        'docker': 'Docker (containerization)',
    }
    
    missing = []
    for cmd, desc in dependencies.items():
        try:
            subprocess.run([cmd, '--version'], 
                         capture_output=True, check=True)
            print(f"✅ {desc}")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"⚠️  {desc} not found")
            missing.append(cmd)
    
    return missing

def setup_environment():
    """Set up environment configuration."""
    env_file = Path('.env')
    if not env_file.exists():
        print("📝 Creating .env file from template...")
        subprocess.run(['cp', '.env.example', '.env'])
        print("✅ Environment file created. Please edit .env with your settings.")
        return False
    
    print("✅ Environment file exists")
    return True

def install_python_deps():
    """Install Python dependencies."""
    print("📦 Installing Python dependencies...")
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      check=True)
        print("✅ Python dependencies installed")
        return True
    except subprocess.CalledProcessError:
        print("❌ Failed to install Python dependencies")
        return False

def check_ollama():
    """Check Ollama installation and model."""
    try:
        result = subprocess.run(['ollama', 'list'], 
                              capture_output=True, text=True)
        if 'deepseek-coder' in result.stdout:
            print("✅ Ollama with deepseek-coder model ready")
            return True
        else:
            print("📥 Downloading deepseek-coder model...")
            subprocess.run(['ollama', 'pull', 'deepseek-coder:6.7b'], check=True)
            print("✅ Ollama model downloaded")
            return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Ollama not found. Install from https://ollama.ai/")
        return False

def start_services():
    """Start RASO services."""
    print("\n🚀 Starting RASO Platform...")
    
    # Check if Docker Compose is available
    try:
        subprocess.run(['docker-compose', '--version'], 
                      capture_output=True, check=True)
        
        print("🐳 Starting with Docker Compose...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print("\n✅ RASO Platform started successfully!")
        print("🌐 Frontend: http://localhost:3000")
        print("🔧 API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("🐍 Starting with Python (development mode)...")
        
        # Start backend
        print("Starting backend server...")
        backend_process = subprocess.Popen([
            sys.executable, '-m', 'backend.main'
        ])
        
        print("✅ Backend started at http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\n💡 To start the frontend:")
        print("   cd frontend && npm install && npm start")
        
        return True

def main():
    """Main startup function."""
    print("🎬 RASO Platform Startup")
    print("=" * 40)
    
    # Check requirements
    if not check_python_version():
        return 1
    
    missing_deps = check_dependencies()
    if missing_deps:
        print(f"\n⚠️  Missing dependencies: {', '.join(missing_deps)}")
        print("Please install them and run again.")
        return 1
    
    # Setup environment
    if not setup_environment():
        print("\n💡 Please edit .env file and run again.")
        return 1
    
    # Install Python dependencies
    if not install_python_deps():
        return 1
    
    # Check Ollama (optional)
    check_ollama()
    
    # Start services
    if start_services():
        print("\n🎉 RASO Platform is ready!")
        print("\n📖 Next steps:")
        print("1. Open http://localhost:3000 in your browser")
        print("2. Enter a research paper title or arXiv URL")
        print("3. Click 'Generate Video' and wait for processing")
        print("4. Download your YouTube-ready video!")
        
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())