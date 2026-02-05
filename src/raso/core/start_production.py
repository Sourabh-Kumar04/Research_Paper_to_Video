#!/usr/bin/env python3
"""
RASO Platform - Production Startup Script
Starts the complete RASO platform in production mode with Google Gemini integration.
"""

import os
import sys
import subprocess
import time
import signal
import asyncio
from pathlib import Path
from typing import List, Dict, Any

class ProductionLauncher:
    """Production launcher for RASO platform."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
        self.root_dir = Path(__file__).parent
        self.setup_environment()
    
    def setup_environment(self):
        """Setup production environment variables."""
        # Load production environment
        env_file = self.root_dir / ".env"
        if env_file.exists():
            print("✅ Loading production environment configuration...")
            # Environment will be loaded by the applications
        else:
            print("⚠️ No .env file found, using default configuration")
        
        # Set production mode
        os.environ['RASO_ENV'] = 'production'
        os.environ['NODE_ENV'] = 'production'
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available."""
        print("🔍 Checking production dependencies...")
        
        dependencies = {
            'python': ['python', '--version'],
            'node': ['node', '--version'],
            'npm': ['npm', '--version'],
            'ffmpeg': ['ffmpeg', '-version'],
            'redis': ['redis-cli', '--version']
        }
        
        missing = []
        for name, cmd in dependencies.items():
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    version = result.stdout.split('\n')[0] if result.stdout else result.stderr.split('\n')[0]
                    print(f"   ✅ {name}: {version}")
                else:
                    missing.append(name)
                    print(f"   ❌ {name}: Not available")
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
                missing.append(name)
                print(f"   ❌ {name}: Not found")
        
        if missing:
            print(f"\n❌ Missing dependencies: {', '.join(missing)}")
            print("Please install missing dependencies before starting production.")
            return False
        
        print("✅ All dependencies available")
        return True
    
    def check_google_gemini_config(self) -> bool:
        """Check Google Gemini API configuration."""
        print("🔍 Checking Google Gemini configuration...")
        
        api_key = os.getenv('RASO_GOOGLE_API_KEY')
        if not api_key:
            print("❌ RASO_GOOGLE_API_KEY not found in environment")
            print("Please set your Google Gemini API key in .env file")
            return False
        
        if api_key.startswith('AIza') and len(api_key) > 30:
            print("✅ Google Gemini API key configured")
            return True
        else:
            print("❌ Invalid Google Gemini API key format")
            return False
    
    def start_redis(self) -> bool:
        """Start Redis server if not running."""
        print("🔄 Starting Redis server...")
        
        try:
            # Check if Redis is already running
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("✅ Redis server already running")
                return True
        except:
            pass
        
        try:
            # Try to start Redis server
            redis_process = subprocess.Popen(
                ['redis-server', '--daemonize', 'yes'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment and check if it started
            time.sleep(2)
            result = subprocess.run(['redis-cli', 'ping'], capture_output=True, text=True, timeout=5)
            if result.returncode == 0 and 'PONG' in result.stdout:
                print("✅ Redis server started successfully")
                return True
            else:
                print("⚠️ Redis server may not be running, continuing anyway...")
                return True
                
        except Exception as e:
            print(f"⚠️ Could not start Redis server: {e}")
            print("Continuing without Redis (some features may be limited)")
            return True
    
    def build_frontend(self) -> bool:
        """Build frontend for production."""
        print("🏗️ Building frontend for production...")
        
        frontend_dir = self.root_dir / "src" / "frontend"
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            return False
        
        try:
            # Install dependencies
            print("   📦 Installing frontend dependencies...")
            result = subprocess.run(
                ['npm', 'install'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                print(f"❌ Frontend dependency installation failed: {result.stderr}")
                return False
            
            # Build for production
            print("   🔨 Building frontend...")
            result = subprocess.run(
                ['npm', 'run', 'build'],
                cwd=frontend_dir,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                print("✅ Frontend built successfully")
                return True
            else:
                print(f"❌ Frontend build failed: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            print("❌ Frontend build timed out")
            return False
        except Exception as e:
            print(f"❌ Frontend build error: {e}")
            return False
    
    def start_backend(self) -> subprocess.Popen:
        """Start the Node.js backend server."""
        print("🚀 Starting backend server...")
        
        backend_dir = self.root_dir / "src" / "backend"
        
        try:
            # Install dependencies
            print("   📦 Installing backend dependencies...")
            subprocess.run(
                ['npm', 'install'],
                cwd=backend_dir,
                check=True,
                capture_output=True,
                timeout=120
            )
            
            # Start backend server
            env = os.environ.copy()
            env['PORT'] = '8000'
            env['NODE_ENV'] = 'production'
            
            process = subprocess.Popen(
                ['npm', 'run', 'dev'],  # Use dev for hot reload, change to 'start' for production build
                cwd=backend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(process)
            print("✅ Backend server started")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start backend server: {e}")
            return None
    
    def start_frontend_server(self) -> subprocess.Popen:
        """Start the frontend development server."""
        print("🌐 Starting frontend server...")
        
        frontend_dir = self.root_dir / "src" / "frontend"
        
        try:
            env = os.environ.copy()
            env['PORT'] = '3000'
            
            process = subprocess.Popen(
                ['npm', 'start'],
                cwd=frontend_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.processes.append(process)
            print("✅ Frontend server started")
            return process
            
        except Exception as e:
            print(f"❌ Failed to start frontend server: {e}")
            return None
    
    def monitor_processes(self):
        """Monitor running processes and display logs."""
        print("\n🔍 Monitoring RASO Platform (Press Ctrl+C to stop)...")
        print("=" * 70)
        
        try:
            while True:
                # Check process health
                for i, process in enumerate(self.processes):
                    if process.poll() is not None:
                        print(f"⚠️ Process {i} exited with code {process.returncode}")
                
                # Display recent logs
                time.sleep(5)
                
        except KeyboardInterrupt:
            print("\n🛑 Shutdown requested...")
            self.cleanup()
    
    def cleanup(self):
        """Clean up all processes."""
        print("🧹 Cleaning up processes...")
        
        for i, process in enumerate(self.processes):
            try:
                if process.poll() is None:
                    print(f"   Stopping process {i}...")
                    process.terminate()
                    
                    # Wait for graceful shutdown
                    try:
                        process.wait(timeout=10)
                    except subprocess.TimeoutExpired:
                        print(f"   Force killing process {i}...")
                        process.kill()
                        process.wait()
                        
            except Exception as e:
                print(f"   Error stopping process {i}: {e}")
        
        print("✅ Cleanup completed")
    
    def run(self):
        """Run the complete production startup sequence."""
        print("🚀 RASO Platform - Production Startup")
        print("=" * 50)
        
        # Check dependencies
        if not self.check_dependencies():
            sys.exit(1)
        
        # Check Gemini configuration
        if not self.check_google_gemini_config():
            sys.exit(1)
        
        # Start Redis
        if not self.start_redis():
            print("⚠️ Continuing without Redis...")
        
        # Build frontend
        if not self.build_frontend():
            print("❌ Frontend build failed, exiting...")
            sys.exit(1)
        
        # Start backend
        backend_process = self.start_backend()
        if not backend_process:
            print("❌ Backend startup failed, exiting...")
            sys.exit(1)
        
        # Wait for backend to start
        print("⏳ Waiting for backend to initialize...")
        time.sleep(10)
        
        # Start frontend
        frontend_process = self.start_frontend_server()
        if not frontend_process:
            print("❌ Frontend startup failed, exiting...")
            self.cleanup()
            sys.exit(1)
        
        # Wait for frontend to start
        print("⏳ Waiting for frontend to initialize...")
        time.sleep(5)
        
        print("\n🎉 RASO Platform started successfully!")
        print("=" * 50)
        print("🌐 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📊 Health Check: http://localhost:8000/health")
        print("🎬 Jobs API: http://localhost:8000/api/v1/jobs")
        print("🤖 LLM Provider: Google Gemini")
        print("=" * 50)
        
        # Monitor processes
        self.monitor_processes()

def main():
    """Main entry point."""
    launcher = ProductionLauncher()
    
    # Handle signals for graceful shutdown
    def signal_handler(signum, frame):
        print(f"\n🛑 Received signal {signum}, shutting down...")
        launcher.cleanup()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        launcher.run()
    except Exception as e:
        print(f"❌ Production startup failed: {e}")
        launcher.cleanup()
        sys.exit(1)

if __name__ == "__main__":
    main()