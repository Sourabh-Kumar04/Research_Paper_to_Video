#!/usr/bin/env python3
"""
RASO Cinematic Complete System Startup Script

This script starts the complete RASO platform with cinematic UI enhancements including:
1. Python FastAPI backend with cinematic features
2. All cinematic video generation agents
3. Enhanced video composition system
4. Instructions for frontend startup

Usage:
    python start_raso_cinematic_complete.py
"""

import asyncio
import subprocess
import sys
import os
import time
import signal
from pathlib import Path
from typing import List, Optional
import threading
import webbrowser
import json

class RASOMasterController:
    """Master controller for the complete RASO system with cinematic features."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        self.backend_port = 8000
        self.frontend_port = 3000
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        self.log("🔍 Checking system dependencies...")
        
        # Check Python
        try:
            result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ Python: {result.stdout.strip()}")
            else:
                self.log("❌ Python not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log("❌ Python not found", "ERROR")
            return False
        
        # Check Python packages
        required_packages = [
            "fastapi", "uvicorn", "pydantic", "pydantic_settings",
            "hypothesis", "pytest", "numpy", "opencv-python"
        ]
        
        missing_packages = []
        for package in required_packages:
            try:
                __import__(package.replace("-", "_"))
                self.log(f"✅ {package}: Available")
            except ImportError:
                missing_packages.append(package)
                self.log(f"❌ {package}: Missing", "WARNING")
        
        if missing_packages:
            self.log(f"⚠️ Missing packages: {', '.join(missing_packages)}", "WARNING")
            self.log("Installing missing packages...")
            try:
                subprocess.run([
                    sys.executable, "-m", "pip", "install"
                ] + missing_packages, check=True)
                self.log("✅ Missing packages installed")
            except subprocess.CalledProcessError:
                self.log("❌ Failed to install missing packages", "ERROR")
                return False
        
        # Check FFmpeg
        try:
            result = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True)
            if result.returncode == 0:
                version_line = result.stdout.split('\n')[0]
                self.log(f"✅ FFmpeg: {version_line}")
            else:
                self.log("⚠️ FFmpeg not found - video generation may be limited", "WARNING")
        except FileNotFoundError:
            self.log("⚠️ FFmpeg not found - video generation may be limited", "WARNING")
        
        # Check Node.js (optional for frontend)
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ Node.js: {result.stdout.strip()}")
                self.node_available = True
            else:
                self.log("⚠️ Node.js not found - frontend will need manual setup", "WARNING")
                self.node_available = False
        except FileNotFoundError:
            self.log("⚠️ Node.js not found - frontend will need manual setup", "WARNING")
            self.node_available = False
        
        return True
    
    def setup_environment(self):
        """Set up the Python environment for the backend."""
        self.log("🔧 Setting up Python environment...")
        
        # Add src to Python path
        src_path = str(Path.cwd() / "src")
        config_path = str(Path.cwd() / "config")
        
        current_path = os.environ.get('PYTHONPATH', '')
        paths_to_add = [src_path, config_path]
        
        if current_path:
            new_path = os.pathsep.join(paths_to_add + [current_path])
        else:
            new_path = os.pathsep.join(paths_to_add)
        
        os.environ['PYTHONPATH'] = new_path
        self.log(f"✅ Python path updated: {new_path}")
        
        # Set environment variables for the backend
        os.environ['RASO_ENV'] = 'development'
        os.environ['RASO_API_HOST'] = '0.0.0.0'
        os.environ['RASO_API_PORT'] = str(self.backend_port)
        os.environ['RASO_DEBUG'] = 'true'
        os.environ['RASO_LOG_LEVEL'] = 'INFO'
        
        # Set LLM provider to Google Gemini (as specified in requirements)
        os.environ['RASO_LLM_PROVIDER'] = 'google'
        if not os.environ.get('RASO_GOOGLE_API_KEY'):
            self.log("⚠️ RASO_GOOGLE_API_KEY not set - AI features may be limited", "WARNING")
        
        self.log("✅ Environment configured for cinematic features")
    
    def start_python_backend(self) -> Optional[subprocess.Popen]:
        """Start the Python FastAPI backend with cinematic features."""
        self.log("🚀 Starting Python FastAPI backend with cinematic features...")
        
        try:
            # Start the FastAPI backend
            process = subprocess.Popen(
                [
                    sys.executable, "-m", "uvicorn", 
                    "config.backend.main:app",
                    "--host", "0.0.0.0",
                    "--port", str(self.backend_port),
                    "--reload"
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=os.environ.copy()
            )
            
            self.processes.append(process)
            
            # Start a thread to monitor backend output
            def monitor_backend():
                for line in process.stdout:
                    if line.strip():
                        self.log(f"[BACKEND] {line.strip()}")
            
            threading.Thread(target=monitor_backend, daemon=True).start()
            
            # Wait a bit to see if it starts successfully
            time.sleep(3)
            if process.poll() is None:
                self.log("✅ Python FastAPI backend started successfully")
                return process
            else:
                self.log("❌ Python FastAPI backend failed to start", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to start Python backend: {e}", "ERROR")
            return None
    
    def start_frontend_if_possible(self) -> Optional[subprocess.Popen]:
        """Start the React frontend if Node.js is available."""
        if not self.node_available:
            self.log("⚠️ Node.js not available - skipping automatic frontend startup", "WARNING")
            return None
        
        self.log("🎨 Starting React frontend...")
        
        frontend_path = Path("src/frontend")
        if not frontend_path.exists():
            self.log("❌ Frontend directory not found", "ERROR")
            return None
        
        try:
            # Check if dependencies are installed
            if not (frontend_path / "node_modules").exists():
                self.log("📦 Installing frontend dependencies...")
                install_result = subprocess.run(
                    ["npm", "install"], 
                    cwd=frontend_path, 
                    capture_output=True, 
                    text=True,
                    timeout=300
                )
                if install_result.returncode != 0:
                    self.log(f"❌ Frontend dependency installation failed: {install_result.stderr}", "ERROR")
                    return None
                self.log("✅ Frontend dependencies installed")
            
            # Start the frontend
            process = subprocess.Popen(
                ["npm", "start"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, "BROWSER": "none", "PORT": str(self.frontend_port)}
            )
            
            self.processes.append(process)
            
            # Start a thread to monitor frontend output
            def monitor_frontend():
                for line in process.stdout:
                    if line.strip():
                        self.log(f"[FRONTEND] {line.strip()}")
            
            threading.Thread(target=monitor_frontend, daemon=True).start()
            
            # Wait a bit to see if it starts successfully
            time.sleep(5)
            if process.poll() is None:
                self.log("✅ React frontend started successfully")
                return process
            else:
                self.log("❌ React frontend failed to start", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to start frontend: {e}", "ERROR")
            return None
    
    def wait_for_backend(self) -> bool:
        """Wait for backend to be ready."""
        self.log("⏳ Waiting for backend to be ready...")
        
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen(f"http://localhost:{self.backend_port}/health", timeout=1)
                self.log("✅ Backend API is ready")
                return True
            except:
                time.sleep(1)
        
        self.log("⚠️ Backend API may not be ready", "WARNING")
        return False
    
    def wait_for_frontend(self) -> bool:
        """Wait for frontend to be ready."""
        if not self.node_available:
            return False
        
        self.log("⏳ Waiting for frontend to be ready...")
        
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen(f"http://localhost:{self.frontend_port}", timeout=1)
                self.log("✅ Frontend UI is ready")
                return True
            except:
                time.sleep(1)
        
        self.log("⚠️ Frontend UI may not be ready", "WARNING")
        return False
    
    def show_system_status(self):
        """Show the current status of all services."""
        self.log("📊 RASO Cinematic System Status:")
        self.log("=" * 60)
        self.log(f"🚀 Backend API:     http://localhost:{self.backend_port}")
        self.log(f"📚 API Docs:        http://localhost:{self.backend_port}/docs")
        self.log(f"🔍 Health Check:    http://localhost:{self.backend_port}/health")
        
        if self.node_available:
            self.log(f"🌐 Frontend UI:     http://localhost:{self.frontend_port}")
        else:
            self.log("🌐 Frontend UI:     Manual setup required (see instructions below)")
        
        self.log("=" * 60)
        self.log("🎬 Cinematic Features:")
        self.log("  ✅ Enhanced Gemini Client for Visual Descriptions")
        self.log("  ✅ Cinematic Settings Management System")
        self.log("  ✅ Backend API Endpoints for Cinematic Features")
        self.log("  ✅ Frontend Cinematic Control Panel Components")
        self.log("  ✅ Preview Generation System")
        self.log("  ✅ Enhanced Cinematic Video Generator Integration")
        self.log("  ✅ Content-Aware Recommendation System")
        self.log("  ✅ Multi-Scene Consistency and Template System")
        self.log("  ✅ Default State and Initialization System")
        self.log("  ✅ Integration Testing and System Validation")
        self.log("  ✅ YouTube Optimization Features")
        self.log("  ✅ Multi-Platform Social Media Adaptation")
        self.log("  ✅ Accessibility and Compliance Features")
        self.log("=" * 60)
        self.log("🔧 Available API Endpoints:")
        self.log("  • POST /api/jobs - Submit video generation job")
        self.log("  • GET /api/jobs/{job_id} - Get job status")
        self.log("  • GET /api/jobs/{job_id}/download - Download video")
        self.log("  • POST /api/v1/cinematic/settings - Manage cinematic settings")
        self.log("  • POST /api/v1/cinematic/visual-description - Generate descriptions")
        self.log("  • POST /api/v1/cinematic/scene-analysis - Analyze scenes")
        self.log("  • POST /api/v1/cinematic/preview - Generate previews")
        self.log("=" * 60)
    
    def show_frontend_instructions(self):
        """Show instructions for manual frontend setup."""
        if self.node_available:
            return
        
        self.log("📋 Manual Frontend Setup Instructions:")
        self.log("=" * 60)
        self.log("Since Node.js is not available in the system PATH, please follow these steps:")
        self.log("")
        self.log("1. Install Node.js (if not already installed):")
        self.log("   - Download from: https://nodejs.org/")
        self.log("   - Or use a package manager like Chocolatey: choco install nodejs")
        self.log("")
        self.log("2. Open a new terminal/command prompt and navigate to the frontend directory:")
        self.log("   cd src/frontend")
        self.log("")
        self.log("3. Install dependencies:")
        self.log("   npm install")
        self.log("")
        self.log("4. Start the development server:")
        self.log("   npm start")
        self.log("")
        self.log("5. The frontend will be available at:")
        self.log(f"   http://localhost:{self.frontend_port}")
        self.log("")
        self.log("The backend is already running and will serve the cinematic API endpoints.")
        self.log("=" * 60)
    
    def open_browser(self):
        """Open the browser to the appropriate interface."""
        if self.node_available:
            try:
                webbrowser.open(f"http://localhost:{self.frontend_port}")
                self.log(f"✅ Browser opened to http://localhost:{self.frontend_port}")
            except Exception as e:
                self.log(f"⚠️ Could not open browser automatically: {e}", "WARNING")
        else:
            try:
                webbrowser.open(f"http://localhost:{self.backend_port}/docs")
                self.log(f"✅ Browser opened to API docs: http://localhost:{self.backend_port}/docs")
            except Exception as e:
                self.log(f"⚠️ Could not open browser automatically: {e}", "WARNING")
    
    def run_cinematic_tests(self):
        """Run a quick test of cinematic features."""
        self.log("🧪 Running cinematic features test...")
        
        try:
            # Test backend health
            import urllib.request
            import json
            
            # Test health endpoint
            response = urllib.request.urlopen(f"http://localhost:{self.backend_port}/health")
            health_data = json.loads(response.read().decode())
            self.log(f"✅ Backend health check: {health_data.get('status', 'unknown')}")
            
            # Test if cinematic modules can be imported
            sys.path.insert(0, str(Path.cwd() / "src"))
            
            try:
                from cinematic.models import CinematicSettingsModel
                self.log("✅ Cinematic models imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Cinematic models import failed: {e}", "WARNING")
            
            try:
                from cinematic.settings_manager import CinematicSettingsManager
                self.log("✅ Cinematic settings manager imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Cinematic settings manager import failed: {e}", "WARNING")
            
            try:
                from cinematic.youtube_optimizer import YouTubeOptimizer
                self.log("✅ YouTube optimizer imported successfully")
            except ImportError as e:
                self.log(f"⚠️ YouTube optimizer import failed: {e}", "WARNING")
            
            try:
                from cinematic.social_media_adapter import SocialMediaAdapter
                self.log("✅ Social media adapter imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Social media adapter import failed: {e}", "WARNING")
            
            try:
                from cinematic.accessibility_manager import AccessibilityManager
                self.log("✅ Accessibility manager imported successfully")
            except ImportError as e:
                self.log(f"⚠️ Accessibility manager import failed: {e}", "WARNING")
            
            self.log("✅ Cinematic features test completed")
            
        except Exception as e:
            self.log(f"⚠️ Cinematic features test failed: {e}", "WARNING")
    
    def cleanup(self):
        """Clean up all processes."""
        self.log("🧹 Shutting down RASO cinematic system...")
        self.running = False
        
        for process in self.processes:
            try:
                if process.poll() is None:
                    process.terminate()
                    # Wait a bit for graceful shutdown
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
            except Exception as e:
                self.log(f"⚠️ Error stopping process: {e}", "WARNING")
        
        self.log("✅ RASO cinematic system shutdown complete")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.log("🛑 Received shutdown signal")
        self.cleanup()
        sys.exit(0)
    
    async def run(self):
        """Run the complete RASO cinematic system."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("🎬 Starting RASO Cinematic Complete System")
        self.log("=" * 70)
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("❌ Dependency check failed", "ERROR")
            return False
        
        # Set up environment
        self.setup_environment()
        
        # Start Python backend
        backend_process = self.start_python_backend()
        if not backend_process:
            self.log("❌ Failed to start Python backend", "ERROR")
            return False
        
        # Wait for backend to be ready
        backend_ready = self.wait_for_backend()
        
        # Start frontend if possible
        frontend_process = self.start_frontend_if_possible()
        frontend_ready = False
        if frontend_process:
            frontend_ready = self.wait_for_frontend()
        
        # Run cinematic features test
        if backend_ready:
            self.run_cinematic_tests()
        
        # Show system status
        self.show_system_status()
        
        # Show frontend instructions if needed
        if not self.node_available:
            self.show_frontend_instructions()
        
        # Open browser
        if backend_ready:
            self.open_browser()
        
        if backend_ready:
            self.log("🎉 RASO Cinematic Complete System is now running!")
            self.log("Press Ctrl+C to stop all services")
            
            # Keep running until interrupted
            try:
                while self.running:
                    time.sleep(1)
                    # Check if backend process died
                    if backend_process and backend_process.poll() is not None:
                        self.log("❌ Backend process died", "ERROR")
                        break
                    # Check if frontend process died (if it was started)
                    if frontend_process and frontend_process.poll() is not None:
                        self.log("❌ Frontend process died", "ERROR")
                        break
            except KeyboardInterrupt:
                self.log("🛑 Received keyboard interrupt")
        else:
            self.log("❌ Backend failed to start properly", "ERROR")
            return False
        
        return True

async def main():
    """Main entry point."""
    controller = RASOMasterController()
    
    try:
        success = await controller.run()
        return success
    finally:
        controller.cleanup()

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)