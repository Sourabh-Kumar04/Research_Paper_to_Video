# Troubleshooting Guide for Enhanced Production Video Generation (2024)

This comprehensive troubleshooting guide covers the latest AI models, animation frameworks, and enhanced features implemented in the production video generation system.

## Table of Contents

1. [Latest AI Model Issues](#latest-ai-model-issues)
2. [Animation Framework Problems](#animation-framework-problems)
3. [Memory and Performance Issues](#memory-and-performance-issues)
4. [Database and Storage Problems](#database-and-storage-problems)
5. [Audio Generation Issues](#audio-generation-issues)
6. [System Integration Problems](#system-integration-problems)
7. [Quick Fixes and Emergency Solutions](#quick-fixes-and-emergency-solutions)

## Latest AI Model Issues

### DeepSeek-V3 Specific Problems

#### Issue: Model fails to load due to memory constraints
**Symptoms:**
- "Out of memory" errors during model loading
- System becomes unresponsive
- Ollama service crashes

**Solutions:**
```bash
# Use quantized version optimized for 16GB systems
ollama pull deepseek-v3:67b-q4_K_M

# Enable CPU offloading for memory efficiency
export OLLAMA_CPU_OFFLOAD=true
export OLLAMA_GPU_LAYERS=20

# Increase swap space if needed
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Test functionality
ollama run deepseek-v3:67b-q4_K_M "Explain quantum computing briefly"
```

#### Issue: Slow inference times on 16GB systems
**Solutions:**
```bash
# Optimize Ollama configuration
export OLLAMA_LOAD_TIMEOUT=600
export OLLAMA_REQUEST_TIMEOUT=300
export OLLAMA_KEEP_ALIVE=10m

# Use lighter model for development
ollama pull qwen2.5:14b-instruct-q4_K_M

# Monitor memory usage during inference
python scripts/monitor_system.py
```

### Qwen2.5-Coder-32B Optimization Issues

#### Issue: Code generation timeouts
**Solutions:**
```bash
# Increase timeout settings
export OLLAMA_LOAD_TIMEOUT=600
export OLLAMA_REQUEST_TIMEOUT=300

# Use optimized variant for 16GB systems
ollama pull qwen2.5-coder:7b-instruct-q4_K_M

# Test code generation capability
ollama run qwen2.5-coder:7b-instruct-q4_K_M "Generate a simple Manim scene for a sine wave animation"
```

#### Issue: Generated code has syntax errors
**Solutions:**
```python
# Add code validation step
def validate_generated_code(code: str) -> bool:
    """Validate generated Python/Manim code."""
    try:
        compile(code, '<string>', 'exec')
        return True
    except SyntaxError as e:
        print(f"Syntax error in generated code: {e}")
        return False

# Use with retry mechanism
def generate_code_with_validation(prompt: str, max_retries: int = 3):
    for attempt in range(max_retries):
        code = ollama_generate(prompt)
        if validate_generated_code(code):
            return code
        print(f"Attempt {attempt + 1} failed, retrying...")
    
    raise Exception("Failed to generate valid code after retries")
```

### Vision Model Memory Issues

#### Issue: Qwen2-VL crashes with large images
**Solutions:**
```bash
# Use quantized model
ollama pull qwen2-vl:7b-q4_K_M

# Optimize image processing
export MAX_IMAGE_SIZE=2048
export VISION_BATCH_SIZE=1

# Resize images before processing
python -c "
from PIL import Image
import sys

def resize_image(input_path, output_path, max_size=2048):
    with Image.open(input_path) as img:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        img.save(output_path, optimize=True, quality=85)

resize_image(sys.argv[1], sys.argv[2])
" input.jpg resized.jpg
```

## Animation Framework Problems

### Manim Issues (Version 0.18+)

#### Issue: LaTeX rendering failures
**Solutions:**
```bash
# Update LaTeX installation
# Windows: Update MiKTeX to latest version
# macOS: 
brew upgrade mactex

# Linux:
sudo apt-get update && sudo apt-get upgrade texlive-full

# Test LaTeX functionality
python -c "
from manim import *
class TestLatex(Scene):
    def construct(self):
        tex = MathTex(r'\int_0^1 x^2 dx = \frac{1}{3}')
        self.add(tex)
"

# Run test
manim test_latex.py TestLatex --preview
```

#### Issue: GPU rendering problems
**Solutions:**
```bash
# Test GPU acceleration
manim --renderer=opengl --write_to_movie test_scene.py TestScene

# If GPU fails, use CPU rendering
manim --renderer=cairo test_scene.py TestScene

# Check GPU availability
python -c "
import torch
print(f'CUDA available: {torch.cuda.is_available()}')
if torch.cuda.is_available():
    print(f'GPU: {torch.cuda.get_device_name(0)}')
"
```

### Motion Canvas Issues (Version 3.15+)

#### Issue: TypeScript compilation errors
**Solutions:**
```bash
# Clear cache and reinstall
npm cache clean --force
rm -rf node_modules package-lock.json
npm install @motion-canvas/core@latest @motion-canvas/2d@latest

# Update TypeScript
npm install typescript@latest @types/node@latest

# Test compilation
npx tsc --noEmit

# Run Motion Canvas project
npx @motion-canvas/cli render src/project.ts
```

#### Issue: Animation rendering failures
**Solutions:**
```bash
# Check Node.js version (requires 18+)
node --version

# Update Motion Canvas CLI
npm uninstall -g @motion-canvas/cli
npm install -g @motion-canvas/cli@latest

# Test with simple scene
echo 'import {makeScene2D} from "@motion-canvas/2d";
import {createRef} from "@motion-canvas/core";
import {Circle} from "@motion-canvas/2d/lib/components";

export default makeScene2D(function* (view) {
  const circle = createRef<Circle>();
  view.add(<Circle ref={circle} size={100} fill="red" />);
  yield* circle().scale(2, 1);
});' > test_scene.tsx

npx @motion-canvas/cli render test_scene.tsx
```

### Remotion Issues (Version 4.0+)

#### Issue: React 18 compatibility problems
**Solutions:**
```bash
# Update to latest versions with React 18 support
npm uninstall -g @remotion/cli
npm install -g @remotion/cli@latest

# Update project dependencies
npm update remotion @remotion/player react react-dom

# Clear Remotion cache
npx remotion clear-cache

# Test with React 18 features
npx remotion render src/index.ts HelloWorld out/video.mp4 --gl=angle
```

## Memory and Performance Issues

### Out of Memory Prevention for 16GB Systems

#### Advanced Memory Monitoring
```python
#!/usr/bin/env python3
"""Advanced memory monitoring for 16GB systems."""

import psutil
import gc
import time
import subprocess
from typing import Dict, List

class MemoryManager:
    def __init__(self, memory_threshold: float = 0.85):
        self.threshold = memory_threshold
        self.total_memory = psutil.virtual_memory().total
        self.process_whitelist = ['ollama', 'python', 'node']
        
    def monitor_and_optimize(self):
        """Continuous memory monitoring with optimization."""
        while True:
            memory_percent = psutil.virtual_memory().percent / 100
            
            if memory_percent > self.threshold:
                print(f"⚠️  Memory usage: {memory_percent:.1%}")
                self._emergency_cleanup()
            
            # Log top memory consumers
            self._log_memory_usage()
            time.sleep(30)
    
    def _emergency_cleanup(self):
        """Emergency memory cleanup procedures."""
        print("🧹 Starting emergency memory cleanup...")
        
        # Python garbage collection
        collected = gc.collect()
        print(f"  Collected {collected} Python objects")
        
        # Clear PyTorch cache if available
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                print("  Cleared PyTorch GPU cache")
        except ImportError:
            pass
        
        # Kill non-essential processes
        self._kill_memory_hogs()
        
        # Force swap usage if available
        self._optimize_swap_usage()
    
    def _log_memory_usage(self):
        """Log memory usage by process."""
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if proc.info['memory_percent'] > 1.0:  # > 1% memory usage
                    processes.append(proc.info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort by memory usage
        processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        
        print("Top memory consumers:")
        for proc in processes[:5]:
            print(f"  {proc['name']}: {proc['memory_percent']:.1f}%")

if __name__ == "__main__":
    manager = MemoryManager()
    manager.monitor_and_optimize()
```

#### Swap Optimization
```bash
# Linux: Optimize swap for AI workloads
sudo sysctl vm.swappiness=10          # Reduce swap usage
sudo sysctl vm.vfs_cache_pressure=50  # Balance file cache
sudo sysctl vm.dirty_ratio=15         # Reduce dirty page ratio

# Create optimized swap file
sudo fallocate -l 16G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
```

### CPU Optimization

#### Performance Mode Setup
```bash
# Linux: Set CPU governor to performance
echo performance | sudo tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor

# Set CPU affinity for Ollama (use first 4 cores)
taskset -c 0-3 ollama serve

# Monitor CPU usage
htop -d 1
```

## Database and Storage Problems

### PostgreSQL Performance Issues

#### Connection Problems
```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Reset user password
sudo -u postgres psql -c "ALTER USER raso_user PASSWORD 'new_secure_password';"

# Optimize for video generation workload
sudo -u postgres psql -c "
  ALTER SYSTEM SET shared_buffers = '4GB';
  ALTER SYSTEM SET effective_cache_size = '12GB';
  ALTER SYSTEM SET work_mem = '256MB';
  ALTER SYSTEM SET maintenance_work_mem = '1GB';
  ALTER SYSTEM SET checkpoint_completion_target = 0.9;
  ALTER SYSTEM SET wal_buffers = '64MB';
  SELECT pg_reload_conf();
"

# Test connection
PGPASSWORD=new_secure_password psql -h localhost -U raso_user -d raso_production -c "SELECT 1;"
```

#### Storage Performance Issues
```bash
# Check disk I/O
iostat -x 1 5

# Enable SSD optimizations (Linux)
echo 'deadline' | sudo tee /sys/block/sda/queue/scheduler
echo 'mq-deadline' | sudo tee /sys/block/nvme0n1/queue/scheduler

# Optimize file system for large files
sudo tune2fs -o journal_data_writeback /dev/sda1

# Monitor disk usage
df -h
du -sh data/* | sort -hr
```

### Redis Caching Issues

#### Memory Optimization
```bash
# Configure Redis for 16GB systems
echo 'maxmemory 2gb' | sudo tee -a /etc/redis/redis.conf
echo 'maxmemory-policy allkeys-lru' | sudo tee -a /etc/redis/redis.conf

# Restart Redis
sudo systemctl restart redis-server

# Test Redis connection
redis-cli ping
```

## Audio Generation Issues

### Coqui TTS Problems

#### Model Loading Failures
```bash
# Clear TTS cache
rm -rf ~/.local/share/tts/

# Reinstall with latest version
pip uninstall coqui-tts
pip install coqui-tts>=0.15.0

# Download models manually
tts --list_models
tts --model_name "tts_models/en/ljspeech/tacotron2-DDC" --text "Test" --out_path test.wav

# Test with different models
tts --model_name "tts_models/en/ljspeech/fast_pitch" --text "Fast test" --out_path fast_test.wav
```

#### Audio Quality Issues
```python
# Audio post-processing for better quality
import librosa
import soundfile as sf
import numpy as np

def enhance_audio(input_path: str, output_path: str):
    """Enhance generated audio quality."""
    # Load audio
    audio, sr = librosa.load(input_path, sr=44100)
    
    # Normalize audio
    audio = librosa.util.normalize(audio)
    
    # Apply noise reduction (simple high-pass filter)
    audio = librosa.effects.preemphasis(audio)
    
    # Save enhanced audio
    sf.write(output_path, audio, sr, subtype='PCM_24')

# Usage
enhance_audio('generated_audio.wav', 'enhanced_audio.wav')
```

## System Integration Problems

### Service Communication Issues

#### Ollama Service Problems
```bash
# Check Ollama service status
ollama list

# Restart Ollama service
sudo systemctl restart ollama  # Linux
# Or kill and restart on other platforms
pkill ollama
ollama serve &

# Test API connectivity
curl http://localhost:11434/api/tags

# Check logs
journalctl -u ollama -f  # Linux
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :11434  # Ollama
netstat -tulpn | grep :5432   # PostgreSQL
netstat -tulpn | grep :6379   # Redis

# Kill processes using ports
sudo lsof -ti:11434 | xargs kill -9
```

## Quick Fixes and Emergency Solutions

### Emergency Memory Recovery
```bash
#!/bin/bash
# Emergency memory recovery script

echo "🚨 Emergency memory recovery starting..."

# Clear system caches
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches

# Kill memory-heavy processes (be careful!)
pkill -f "chrome|firefox|code"

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete

# Clear npm cache
npm cache clean --force

# Force garbage collection in Python processes
python -c "import gc; gc.collect()"

echo "✅ Emergency recovery completed"
```

### Quick Model Switch for 16GB Systems
```bash
#!/bin/bash
# Quick switch to lightweight models

echo "🔄 Switching to lightweight models for 16GB systems..."

# Stop current models
ollama stop

# Pull lightweight models
ollama pull codellama:7b-instruct-q4_K_M
ollama pull qwen2.5:7b-instruct-q4_K_M
ollama pull llava:7b-q4_K_M

# Update configuration
cat > config/emergency_config.json << EOF
{
  "ai_models": {
    "coding": "codellama:7b-instruct-q4_K_M",
    "reasoning": "qwen2.5:7b-instruct-q4_K_M",
    "vision": "llava:7b-q4_K_M",
    "audio": "piper-tts-fast"
  },
  "memory_limit": "12GB",
  "concurrent_models": 1
}
EOF

echo "✅ Switched to emergency lightweight configuration"
```

### System Health Check
```python
#!/usr/bin/env python3
"""Comprehensive system health check."""

import psutil
import shutil
import subprocess
import json
from pathlib import Path

def health_check():
    """Run comprehensive system health check."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "system": {},
        "services": {},
        "models": {},
        "storage": {}
    }
    
    # System resources
    results["system"] = {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": psutil.disk_usage("/").percent,
        "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else None
    }
    
    # Service status
    services = ["ollama", "postgresql", "redis-server"]
    for service in services:
        try:
            result = subprocess.run(
                ["systemctl", "is-active", service],
                capture_output=True, text=True
            )
            results["services"][service] = result.stdout.strip()
        except:
            results["services"][service] = "unknown"
    
    # Model availability
    try:
        result = subprocess.run(
            ["ollama", "list"], capture_output=True, text=True
        )
        results["models"]["available"] = len(result.stdout.split('\n')) - 2
    except:
        results["models"]["available"] = 0
    
    # Storage check
    data_path = Path("data")
    if data_path.exists():
        results["storage"]["data_size_gb"] = sum(
            f.stat().st_size for f in data_path.rglob('*') if f.is_file()
        ) / (1024**3)
    
    # Generate report
    print("🏥 System Health Check Report")
    print("=" * 40)
    
    # System status
    memory_status = "🟢" if results["system"]["memory_percent"] < 80 else "🟡" if results["system"]["memory_percent"] < 90 else "🔴"
    cpu_status = "🟢" if results["system"]["cpu_percent"] < 70 else "🟡" if results["system"]["cpu_percent"] < 90 else "🔴"
    disk_status = "🟢" if results["system"]["disk_usage"] < 80 else "🟡" if results["system"]["disk_usage"] < 90 else "🔴"
    
    print(f"Memory: {memory_status} {results['system']['memory_percent']:.1f}%")
    print(f"CPU: {cpu_status} {results['system']['cpu_percent']:.1f}%")
    print(f"Disk: {disk_status} {results['system']['disk_usage']:.1f}%")
    
    # Service status
    print("\nServices:")
    for service, status in results["services"].items():
        status_icon = "🟢" if status == "active" else "🔴"
        print(f"  {service}: {status_icon} {status}")
    
    # Models
    print(f"\nAI Models: {results['models']['available']} available")
    
    # Recommendations
    print("\n💡 Recommendations:")
    if results["system"]["memory_percent"] > 85:
        print("  - Consider switching to lightweight model preset")
        print("  - Enable swap if not already active")
    
    if results["system"]["disk_usage"] > 85:
        print("  - Clean up old generated content")
        print("  - Enable automatic cleanup")
    
    # Save report
    with open("health_check_report.json", "w") as f:
        json.dump(results, f, indent=2)
    
    return results

if __name__ == "__main__":
    from datetime import datetime
    health_check()
```

This comprehensive troubleshooting guide should help resolve most issues encountered with the enhanced production video generation system. For persistent problems, check the logs in the `logs/` directory and consider running the health check script to identify system bottlenecks.