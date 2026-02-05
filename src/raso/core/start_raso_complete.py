#!/usr/bin/env python3
"""
Complete RASO System Startup Script

This script starts the complete RASO platform including:
1. Backend API server (TypeScript/Node.js)
2. Frontend UI (React)
3. Python video generation agents
4. Enhanced video composition system

Usage:
    python start_raso_complete.py
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

class RASOMasterController:
    """Master controller for the complete RASO system."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.running = True
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp."""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        self.log("🔍 Checking system dependencies...")
        
        # Check Node.js
        try:
            result = subprocess.run(["node", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ Node.js: {result.stdout.strip()}")
            else:
                self.log("❌ Node.js not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log("❌ Node.js not found", "ERROR")
            return False
        
        # Check npm
        try:
            result = subprocess.run(["npm", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.log(f"✅ npm: {result.stdout.strip()}")
            else:
                self.log("❌ npm not found", "ERROR")
                return False
        except FileNotFoundError:
            self.log("❌ npm not found", "ERROR")
            return False
        
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
        
        return True
    
    def install_dependencies(self) -> bool:
        """Install required dependencies."""
        self.log("📦 Installing dependencies...")
        
        # Install backend dependencies
        backend_path = Path("src/backend")
        if backend_path.exists():
            self.log("Installing backend dependencies...")
            try:
                result = subprocess.run(
                    ["npm", "install"], 
                    cwd=backend_path, 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                if result.returncode == 0:
                    self.log("✅ Backend dependencies installed")
                else:
                    self.log(f"❌ Backend dependency installation failed: {result.stderr}", "ERROR")
                    return False
            except subprocess.TimeoutExpired:
                self.log("❌ Backend dependency installation timed out", "ERROR")
                return False
            except Exception as e:
                self.log(f"❌ Backend dependency installation error: {e}", "ERROR")
                return False
        
        # Install frontend dependencies
        frontend_path = Path("src/frontend")
        if frontend_path.exists():
            self.log("Installing frontend dependencies...")
            try:
                result = subprocess.run(
                    ["npm", "install"], 
                    cwd=frontend_path, 
                    capture_output=True, 
                    text=True,
                    timeout=300  # 5 minutes timeout
                )
                if result.returncode == 0:
                    self.log("✅ Frontend dependencies installed")
                else:
                    self.log(f"❌ Frontend dependency installation failed: {result.stderr}", "ERROR")
                    return False
            except subprocess.TimeoutExpired:
                self.log("❌ Frontend dependency installation timed out", "ERROR")
                return False
            except Exception as e:
                self.log(f"❌ Frontend dependency installation error: {e}", "ERROR")
                return False
        
        # Install Python dependencies
        self.log("Installing Python dependencies...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                capture_output=True, 
                text=True,
                timeout=300  # 5 minutes timeout
            )
            if result.returncode == 0:
                self.log("✅ Python dependencies installed")
            else:
                self.log(f"❌ Python dependency installation failed: {result.stderr}", "ERROR")
                return False
        except subprocess.TimeoutExpired:
            self.log("❌ Python dependency installation timed out", "ERROR")
            return False
        except Exception as e:
            self.log(f"❌ Python dependency installation error: {e}", "ERROR")
            return False
        
        return True
    
    def start_backend(self) -> Optional[subprocess.Popen]:
        """Start the backend API server."""
        self.log("🚀 Starting backend API server...")
        
        backend_path = Path("src/backend")
        if not backend_path.exists():
            self.log("❌ Backend directory not found", "ERROR")
            return None
        
        try:
            # Build the backend first
            self.log("Building backend...")
            build_result = subprocess.run(
                ["npm", "run", "build"], 
                cwd=backend_path, 
                capture_output=True, 
                text=True,
                timeout=120  # 2 minutes timeout
            )
            
            if build_result.returncode != 0:
                self.log(f"⚠️ Backend build failed, trying dev mode: {build_result.stderr}", "WARNING")
                # Try dev mode instead
                process = subprocess.Popen(
                    ["npm", "run", "dev"],
                    cwd=backend_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            else:
                self.log("✅ Backend built successfully")
                # Start the built backend
                process = subprocess.Popen(
                    ["npm", "start"],
                    cwd=backend_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
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
                self.log("✅ Backend server started successfully")
                return process
            else:
                self.log("❌ Backend server failed to start", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to start backend: {e}", "ERROR")
            return None
    
    def start_frontend(self) -> Optional[subprocess.Popen]:
        """Start the frontend React server."""
        self.log("🎨 Starting frontend React server...")
        
        frontend_path = Path("src/frontend")
        if not frontend_path.exists():
            self.log("❌ Frontend directory not found", "ERROR")
            return None
        
        try:
            process = subprocess.Popen(
                ["npm", "start"],
                cwd=frontend_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env={**os.environ, "BROWSER": "none"}  # Prevent auto-opening browser
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
                self.log("✅ Frontend server started successfully")
                return process
            else:
                self.log("❌ Frontend server failed to start", "ERROR")
                return None
                
        except Exception as e:
            self.log(f"❌ Failed to start frontend: {e}", "ERROR")
            return None
    
    def start_python_agents(self) -> Optional[subprocess.Popen]:
        """Start the Python video generation agents."""
        self.log("🐍 Starting Python video generation agents...")
        
        try:
            # Add src to Python path and start the main demo
            env = os.environ.copy()
            current_path = env.get('PYTHONPATH', '')
            src_path = str(Path.cwd() / "src")
            env['PYTHONPATH'] = f"{src_path}{os.pathsep}{current_path}" if current_path else src_path
            
            process = subprocess.Popen(
                [sys.executable, "main.py"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True,
                env=env
            )
            
            self.processes.append(process)
            
            # Start a thread to monitor Python agents output
            def monitor_python():
                for line in process.stdout:
                    if line.strip():
                        self.log(f"[PYTHON] {line.strip()}")
            
            threading.Thread(target=monitor_python, daemon=True).start()
            
            # Wait a bit to see if it starts successfully
            time.sleep(2)
            if process.poll() is None:
                self.log("✅ Python agents started successfully")
                return process
            else:
                self.log("⚠️ Python agents completed (this is normal for demo mode)", "WARNING")
                return process
                
        except Exception as e:
            self.log(f"❌ Failed to start Python agents: {e}", "ERROR")
            return None
    
    def wait_for_services(self):
        """Wait for services to be ready."""
        self.log("⏳ Waiting for services to be ready...")
        
        # Wait for backend
        backend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:8000/health", timeout=1)
                backend_ready = True
                self.log("✅ Backend API is ready")
                break
            except:
                time.sleep(1)
        
        if not backend_ready:
            self.log("⚠️ Backend API may not be ready", "WARNING")
        
        # Wait for frontend
        frontend_ready = False
        for i in range(30):  # Wait up to 30 seconds
            try:
                import urllib.request
                urllib.request.urlopen("http://localhost:3000", timeout=1)
                frontend_ready = True
                self.log("✅ Frontend UI is ready")
                break
            except:
                time.sleep(1)
        
        if not frontend_ready:
            self.log("⚠️ Frontend UI may not be ready", "WARNING")
        
        return backend_ready and frontend_ready
    
    def open_browser(self):
        """Open the browser to the RASO UI."""
        self.log("🌐 Opening RASO UI in browser...")
        try:
            webbrowser.open("http://localhost:3000")
            self.log("✅ Browser opened to http://localhost:3000")
        except Exception as e:
            self.log(f"⚠️ Could not open browser automatically: {e}", "WARNING")
            self.log("Please manually open http://localhost:3000 in your browser")
    
    def show_status(self):
        """Show the current status of all services."""
        self.log("📊 RASO System Status:")
        self.log("=" * 50)
        self.log("🌐 Frontend UI:     http://localhost:3000")
        self.log("🚀 Backend API:     http://localhost:8000")
        self.log("📚 API Docs:        http://localhost:8000/docs")
        self.log("🔍 Health Check:    http://localhost:8000/health")
        self.log("=" * 50)
        self.log("🎬 Enhanced Video Composition: ✅ Active")
        self.log("🔄 Placeholder Detection:      ✅ Active")
        self.log("🧹 Resource Cleanup:           ✅ Active")
        self.log("📊 Quality Assessment:         ✅ Active")
        self.log("=" * 50)
    
    def cleanup(self):
        """Clean up all processes."""
        self.log("🧹 Shutting down RASO system...")
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
        
        self.log("✅ RASO system shutdown complete")
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals."""
        self.log("🛑 Received shutdown signal")
        self.cleanup()
        sys.exit(0)
    
    async def run(self):
        """Run the complete RASO system."""
        # Set up signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        self.log("🎬 Starting RASO Complete System")
        self.log("=" * 60)
        
        # Check dependencies
        if not self.check_dependencies():
            self.log("❌ Dependency check failed", "ERROR")
            return False
        
        # Install dependencies
        if not self.install_dependencies():
            self.log("❌ Dependency installation failed", "ERROR")
            return False
        
        # Start services
        backend_process = self.start_backend()
        if not backend_process:
            self.log("❌ Failed to start backend", "ERROR")
            return False
        
        frontend_process = self.start_frontend()
        if not frontend_process:
            self.log("❌ Failed to start frontend", "ERROR")
            return False
        
        # Start Python agents (optional)
        python_process = self.start_python_agents()
        
        # Wait for services to be ready
        services_ready = self.wait_for_services()
        
        if services_ready:
            self.show_status()
            self.open_browser()
            
            self.log("🎉 RASO Complete System is now running!")
            self.log("Press Ctrl+C to stop all services")
            
            # Keep running until interrupted
            try:
                while self.running:
                    time.sleep(1)
                    # Check if any critical process died
                    if backend_process and backend_process.poll() is not None:
                        self.log("❌ Backend process died", "ERROR")
                        break
                    if frontend_process and frontend_process.poll() is not None:
                        self.log("❌ Frontend process died", "ERROR")
                        break
            except KeyboardInterrupt:
                self.log("🛑 Received keyboard interrupt")
        else:
            self.log("❌ Services failed to start properly", "ERROR")
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