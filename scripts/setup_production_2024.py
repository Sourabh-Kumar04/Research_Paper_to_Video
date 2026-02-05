#!/usr/bin/env python3
"""
Enhanced Production Setup Script for RASO Video Generation System (2024)
Optimized for 16GB RAM / 4-core systems with latest AI models and features.
"""

import os
import sys
import json
import subprocess
import platform
import psutil
import shutil
from pathlib import Path
from typing import Dict, List, Optional
import requests

class ProductionSetup2024:
    def __init__(self):
        self.system_info = self._get_system_info()
        self.config = self._load_config()
        self.setup_log = []
        
    def _get_system_info(self) -> Dict:
        """Get system information for optimization."""
        return {
            "platform": platform.system(),
            "architecture": platform.machine(),
            "cpu_count": psutil.cpu_count(),
            "memory_gb": round(psutil.virtual_memory().total / (1024**3)),
            "disk_free_gb": round(shutil.disk_usage("/").free / (1024**3)),
            "python_version": sys.version_info[:2]
        }
    
    def _load_config(self) -> Dict:
        """Load production configuration."""
        config_path = Path("config/production_config_2024.json")
        if config_path.exists():
            with open(config_path) as f:
                return json.load(f)
        return {}
    
    def run_setup(self):
        """Run complete production setup."""
        print("🚀 RASO Production Video Generation Setup 2024")
        print("=" * 60)
        
        self._print_system_info()
        self._check_prerequisites()
        
        # Core setup steps
        steps = [
            ("Installing Python dependencies", self._setup_python_dependencies),
            ("Setting up AI models (Ollama)", self._setup_ai_models),
            ("Installing animation frameworks", self._setup_animation_frameworks),
            ("Setting up database", self._setup_database),
            ("Configuring audio generation", self._setup_audio_generation),
            ("Optimizing system performance", self._optimize_system_performance),
            ("Setting up monitoring", self._setup_monitoring),
            ("Running system tests", self._run_system_tests)
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                step_func()
                self.setup_log.append(f"✅ {step_name}: SUCCESS")
                print(f"✅ {step_name} completed successfully")
            except Exception as e:
                self.setup_log.append(f"❌ {step_name}: FAILED - {str(e)}")
                print(f"❌ {step_name} failed: {str(e)}")
                
                if input("Continue with setup? (y/n): ").lower() != 'y':
                    break
        
        self._generate_setup_report()
    
    def _print_system_info(self):
        """Print system information and recommendations."""
        info = self.system_info
        print(f"System: {info['platform']} {info['architecture']}")
        print(f"CPU Cores: {info['cpu_count']}")
        print(f"Memory: {info['memory_gb']} GB")
        print(f"Free Disk: {info['disk_free_gb']} GB")
        print(f"Python: {info['python_version'][0]}.{info['python_version'][1]}")
        
        # Recommendations based on system specs
        if info['memory_gb'] <= 16:
            print("\n💡 16GB RAM detected - Using optimized configuration")
            self.recommended_preset = "fast_16gb"
        elif info['memory_gb'] <= 32:
            print("\n💡 32GB RAM detected - Using balanced configuration")
            self.recommended_preset = "balanced_16gb"
        else:
            print("\n💡 High-end system detected - Using quality configuration")
            self.recommended_preset = "quality_32gb"
    
    def _check_prerequisites(self):
        """Check system prerequisites."""
        print("\n🔍 Checking prerequisites...")
        
        # Check Python version
        if sys.version_info < (3, 9):
            raise Exception("Python 3.9+ required")
        
        # Check available disk space (minimum 50GB)
        if self.system_info['disk_free_gb'] < 50:
            print("⚠️  Warning: Less than 50GB free disk space")
        
        # Check for required system tools
        required_tools = ['git', 'curl']
        if self.system_info['platform'] != 'Windows':
            required_tools.extend(['wget', 'unzip'])
        
        for tool in required_tools:
            if not shutil.which(tool):
                raise Exception(f"Required tool not found: {tool}")
        
        print("✅ Prerequisites check passed")
    
    def _setup_python_dependencies(self):
        """Install Python dependencies with optimizations."""
        # Core dependencies
        core_deps = [
            "torch>=2.0.0",
            "transformers>=4.35.0",
            "ollama>=0.1.7",
            "manim>=0.18.0",
            "coqui-tts>=0.15.0",
            "psutil>=5.9.0",
            "redis>=4.5.0",
            "sqlalchemy>=2.0.0",
            "fastapi>=0.104.0",
            "uvicorn>=0.24.0"
        ]
        
        # Install with optimizations for 16GB systems
        pip_args = [
            sys.executable, "-m", "pip", "install", "--upgrade"
        ]
        
        # Use CPU-only PyTorch for memory efficiency if no GPU
        if not self._has_gpu():
            pip_args.extend(["--index-url", "https://download.pytorch.org/whl/cpu"])
        
        pip_args.extend(core_deps)
        
        subprocess.run(pip_args, check=True)
        
        # Install optional dependencies based on system capabilities
        if self.system_info['memory_gb'] >= 32:
            optional_deps = ["jupyter", "matplotlib", "seaborn", "plotly"]
            subprocess.run([sys.executable, "-m", "pip", "install"] + optional_deps)
    
    def _setup_ai_models(self):
        """Set up AI models with Ollama."""
        # Install Ollama if not present
        if not shutil.which('ollama'):
            self._install_ollama()
        
        # Start Ollama service
        self._start_ollama_service()
        
        # Get recommended models based on system specs
        preset = self.config['ai_models']['presets'][self.recommended_preset]
        models_to_install = list(preset['models'].values())
        
        print(f"Installing AI models for {preset['name']}...")
        for model in models_to_install:
            if model and not model.startswith('piper'):  # Skip non-Ollama models
                print(f"  Pulling {model}...")
                subprocess.run(['ollama', 'pull', model], check=True)
        
        # Test model functionality
        test_model = preset['models']['reasoning']
        if test_model:
            print(f"Testing {test_model}...")
            result = subprocess.run(
                ['ollama', 'run', test_model, 'Hello, world!'],
                capture_output=True, text=True, timeout=60
            )
            if result.returncode != 0:
                raise Exception(f"Model test failed: {result.stderr}")
    
    def _setup_animation_frameworks(self):
        """Set up animation frameworks."""
        # Manim setup
        print("Setting up Manim...")
        if self.system_info['platform'] == 'Windows':
            print("Please install MiKTeX from https://miktex.org/")
        elif self.system_info['platform'] == 'Darwin':  # macOS
            subprocess.run(['brew', 'install', '--cask', 'mactex'], check=False)
        else:  # Linux
            subprocess.run(['sudo', 'apt-get', 'install', '-y', 'texlive-full'], check=False)
        
        # Node.js frameworks setup
        if shutil.which('npm'):
            print("Setting up Motion Canvas and Remotion...")
            
            # Install global packages
            npm_globals = [
                '@motion-canvas/cli@latest',
                '@remotion/cli@latest'
            ]
            
            for package in npm_globals:
                subprocess.run(['npm', 'install', '-g', package], check=False)
        else:
            print("⚠️  Node.js not found - skipping Motion Canvas and Remotion setup")
    
    def _setup_database(self):
        """Set up database with optimizations."""
        # Check if PostgreSQL is installed
        if not shutil.which('psql'):
            print("PostgreSQL not found - please install PostgreSQL 15+")
            return
        
        # Create database and user
        db_commands = [
            "CREATE DATABASE raso_production;",
            "CREATE USER raso_user WITH PASSWORD 'secure_password';",
            "GRANT ALL PRIVILEGES ON DATABASE raso_production TO raso_user;"
        ]
        
        for cmd in db_commands:
            subprocess.run([
                'sudo', '-u', 'postgres', 'psql', '-c', cmd
            ], check=False)
        
        # Apply performance optimizations
        pg_config = self.config['database_storage']['postgresql']['optimizations']
        for setting, value in pg_config.items():
            subprocess.run([
                'sudo', '-u', 'postgres', 'psql', '-c',
                f"ALTER SYSTEM SET {setting} = '{value}';"
            ], check=False)
        
        # Reload configuration
        subprocess.run([
            'sudo', '-u', 'postgres', 'psql', '-c', 'SELECT pg_reload_conf();'
        ], check=False)
    
    def _setup_audio_generation(self):
        """Set up audio generation models."""
        # Install Coqui TTS models
        print("Setting up Coqui TTS...")
        subprocess.run([
            'tts', '--list_models'
        ], check=False)
        
        # Download default model
        subprocess.run([
            'tts', '--model_name', 'tts_models/en/ljspeech/tacotron2-DDC',
            '--text', 'Test', '--out_path', 'test_audio.wav'
        ], check=False)
        
        # Clean up test file
        if os.path.exists('test_audio.wav'):
            os.remove('test_audio.wav')
    
    def _optimize_system_performance(self):
        """Apply system performance optimizations."""
        # Create swap file if needed (Linux only)
        if (self.system_info['platform'] == 'Linux' and 
            self.system_info['memory_gb'] <= 16):
            
            swap_size = min(16, self.system_info['memory_gb'])  # GB
            self._create_swap_file(swap_size)
        
        # Set CPU governor to performance (Linux only)
        if self.system_info['platform'] == 'Linux':
            subprocess.run([
                'sudo', 'sh', '-c',
                'echo performance > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
            ], check=False)
        
        # Create performance monitoring script
        self._create_monitoring_script()
    
    def _setup_monitoring(self):
        """Set up system monitoring."""
        # Create logs directory
        os.makedirs('logs', exist_ok=True)
        
        # Create monitoring configuration
        monitoring_config = {
            "metrics": {
                "system_resources": True,
                "model_performance": True,
                "generation_quality": True
            },
            "alerts": {
                "memory_threshold": 90,
                "disk_threshold": 85,
                "cpu_threshold": 95
            }
        }
        
        with open('config/monitoring.json', 'w') as f:
            json.dump(monitoring_config, f, indent=2)
    
    def _run_system_tests(self):
        """Run system tests to verify setup."""
        print("Running system tests...")
        
        # Test Python imports
        test_imports = [
            'torch', 'transformers', 'manim', 'sqlalchemy', 'fastapi'
        ]
        
        for module in test_imports:
            try:
                __import__(module)
                print(f"  ✅ {module} import successful")
            except ImportError as e:
                print(f"  ❌ {module} import failed: {e}")
        
        # Test Ollama connection
        try:
            result = subprocess.run(
                ['ollama', 'list'], 
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                print("  ✅ Ollama connection successful")
            else:
                print("  ❌ Ollama connection failed")
        except Exception as e:
            print(f"  ❌ Ollama test failed: {e}")
        
        # Test database connection
        try:
            result = subprocess.run([
                'psql', '-h', 'localhost', '-U', 'raso_user', '-d', 'raso_production',
                '-c', 'SELECT 1;'
            ], capture_output=True, text=True, timeout=10, 
            env={**os.environ, 'PGPASSWORD': 'secure_password'})
            
            if result.returncode == 0:
                print("  ✅ Database connection successful")
            else:
                print("  ❌ Database connection failed")
        except Exception as e:
            print(f"  ❌ Database test failed: {e}")
    
    def _install_ollama(self):
        """Install Ollama based on platform."""
        if self.system_info['platform'] == 'Linux':
            subprocess.run([
                'curl', '-fsSL', 'https://ollama.ai/install.sh'
            ], stdout=subprocess.PIPE, check=True)
            subprocess.run(['sh'], input=subprocess.PIPE, check=True)
        elif self.system_info['platform'] == 'Darwin':  # macOS
            subprocess.run(['brew', 'install', 'ollama'], check=True)
        else:  # Windows
            print("Please download and install Ollama from https://ollama.ai/download")
            input("Press Enter after installing Ollama...")
    
    def _start_ollama_service(self):
        """Start Ollama service."""
        try:
            # Check if Ollama is already running
            result = subprocess.run(
                ['ollama', 'list'], 
                capture_output=True, timeout=5
            )
            if result.returncode == 0:
                return  # Already running
        except:
            pass
        
        # Start Ollama service
        if self.system_info['platform'] == 'Linux':
            subprocess.run(['sudo', 'systemctl', 'start', 'ollama'], check=False)
        else:
            # Start Ollama in background
            subprocess.Popen(['ollama', 'serve'], 
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
    
    def _has_gpu(self) -> bool:
        """Check if GPU is available."""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
    
    def _create_swap_file(self, size_gb: int):
        """Create swap file for memory optimization."""
        swap_path = '/swapfile'
        
        if os.path.exists(swap_path):
            return  # Swap file already exists
        
        commands = [
            f'sudo fallocate -l {size_gb}G {swap_path}',
            f'sudo chmod 600 {swap_path}',
            f'sudo mkswap {swap_path}',
            f'sudo swapon {swap_path}',
            f'echo "{swap_path} none swap sw 0 0" | sudo tee -a /etc/fstab'
        ]
        
        for cmd in commands:
            subprocess.run(cmd.split(), check=False)
    
    def _create_monitoring_script(self):
        """Create system monitoring script."""
        script_content = '''#!/usr/bin/env python3
import psutil
import time
import json
from datetime import datetime

def monitor_system():
    while True:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent
        }
        
        print(json.dumps(stats, indent=2))
        
        if stats['memory_percent'] > 90:
            print("WARNING: Memory usage above 90%")
        if stats['cpu_percent'] > 95:
            print("WARNING: CPU usage above 95%")
            
        time.sleep(5)

if __name__ == "__main__":
    monitor_system()
'''
        
        os.makedirs('scripts', exist_ok=True)
        with open('scripts/monitor_system.py', 'w') as f:
            f.write(script_content)
        
        # Make executable
        os.chmod('scripts/monitor_system.py', 0o755)
    
    def _generate_setup_report(self):
        """Generate setup completion report."""
        print("\n" + "=" * 60)
        print("🎉 SETUP COMPLETE!")
        print("=" * 60)
        
        print("\n📊 Setup Summary:")
        for log_entry in self.setup_log:
            print(f"  {log_entry}")
        
        print(f"\n🔧 Recommended Configuration: {self.recommended_preset}")
        preset = self.config['ai_models']['presets'][self.recommended_preset]
        print(f"  Memory Usage: {preset['memory_usage']}")
        print(f"  Inference Speed: {preset['inference_speed']}")
        print(f"  Quality: {preset['quality']}")
        
        print("\n🚀 Next Steps:")
        print("  1. Start the application: python start.py")
        print("  2. Monitor system: python scripts/monitor_system.py")
        print("  3. Check logs: tail -f logs/raso_production.log")
        
        print("\n📚 Documentation:")
        print("  - Setup Guide: ENHANCED_PRODUCTION_SETUP.md")
        print("  - AI Models: AI_MODEL_SETUP_GUIDE.md")
        print("  - Database: DATABASE_STORAGE_GUIDE.md")
        
        # Save setup report
        report = {
            "setup_date": datetime.now().isoformat(),
            "system_info": self.system_info,
            "recommended_preset": self.recommended_preset,
            "setup_log": self.setup_log
        }
        
        with open('setup_report_2024.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Setup report saved to: setup_report_2024.json")

if __name__ == "__main__":
    setup = ProductionSetup2024()
    setup.run_setup()