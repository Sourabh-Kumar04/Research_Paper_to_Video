# Enhanced Production Video Generation Setup Guide

This guide covers the complete setup for the enhanced production video generation system with all AI models, animation frameworks, and advanced features.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [AI Model Setup](#ai-model-setup)
3. [Animation Framework Setup](#animation-framework-setup)
4. [Database and Storage Setup](#database-and-storage-setup)
5. [Audio Generation Setup](#audio-generation-setup)
6. [Performance Optimization](#performance-optimization)
7. [Troubleshooting](#troubleshooting)

## System Requirements

### Hardware Requirements

#### Minimum Requirements (16GB RAM / 4-Core System)
- **CPU**: 4-core processor (Intel i5/AMD Ryzen 5 or better)
- **RAM**: 16GB DDR4 (optimized configurations provided)
- **Storage**: 500GB SSD (with intelligent cleanup)
- **GPU**: Optional but recommended (NVIDIA GTX 1060 or better)

#### Recommended Requirements
- **CPU**: 8-core processor (Intel i7/AMD Ryzen 7 or better)
- **RAM**: 32GB DDR4 or higher
- **Storage**: 1TB NVMe SSD
- **GPU**: NVIDIA RTX 3060 or better (for AI acceleration)

#### Optimal Requirements
- **CPU**: 12+ core processor (Intel i9/AMD Ryzen 9)
- **RAM**: 64GB DDR4 or higher
- **Storage**: 2TB+ NVMe SSD
- **GPU**: NVIDIA RTX 4070 or better

### Software Requirements

- **Operating System**: Windows 10/11, macOS 10.15+, or Linux (Ubuntu 20.04+)
- **Python**: 3.9 or higher
- **Node.js**: 18.0 or higher (for Motion Canvas and Remotion)
- **FFmpeg**: 4.4 or higher
- **Git**: Latest version
- **Docker**: Optional but recommended for containerized deployment

## AI Model Setup

### Ollama Installation and Configuration

#### 1. Install Ollama

**Windows:**
```powershell
# Download and install from https://ollama.ai/download
# Or use winget
winget install Ollama.Ollama
```

**macOS:**
```bash
# Download and install from https://ollama.ai/download
# Or use Homebrew
brew install ollama
```

**Linux:**
```bash
curl -fsSL https://ollama.ai/install.sh | sh
```

#### 2. Configure AI Models

**For 16GB RAM Systems (Recommended):**
```bash
# Lightweight models optimized for 16GB RAM
ollama pull qwen2.5:7b          # General reasoning (7B parameters)
ollama pull codellama:7b        # Code generation (7B parameters)
ollama pull llama3.2:3b         # Fast inference (3B parameters)
```

**For 32GB+ RAM Systems:**
```bash
# Full-featured models
ollama pull qwen2.5:32b         # Advanced reasoning (32B parameters)
ollama pull deepseek-coder:33b  # Advanced code generation
ollama pull llama3.1:70b        # High-quality text generation
```

#### 3. Model Configuration

Create `config/ai_models.json`:
```json
{
  "model_presets": {
    "fast": {
      "reasoning_model": "llama3.2:3b",
      "code_model": "codellama:7b",
      "memory_limit": "8GB",
      "recommended_for": "16GB RAM systems"
    },
    "balanced": {
      "reasoning_model": "qwen2.5:7b",
      "code_model": "qwen2.5-coder:7b",
      "memory_limit": "12GB",
      "recommended_for": "16GB-32GB RAM systems"
    },
    "quality": {
      "reasoning_model": "qwen2.5:32b",
      "code_model": "deepseek-coder:33b",
      "memory_limit": "24GB",
      "recommended_for": "32GB+ RAM systems"
    }
  },
  "default_preset": "balanced"
}
```

### Vision-Language Models

#### Qwen2-VL Setup
```bash
# Install Qwen2-VL for visual content understanding
pip install transformers torch torchvision
ollama pull qwen2-vl:7b
```

#### LLaVA-NeXT Setup
```bash
# Install LLaVA-NeXT for advanced visual analysis
pip install llava-next
ollama pull llava-next:13b
```

## Animation Framework Setup

### Manim Community Edition

#### Installation
```bash
# Install Manim for mathematical animations
pip install manim

# Install LaTeX for equation rendering (required)
# Windows: Install MiKTeX from https://miktex.org/
# macOS: brew install --cask mactex
# Linux: sudo apt-get install texlive-full
```

#### Configuration
Create `config/manim_config.cfg`:
```ini
[CLI]
quality = medium_quality
preview = False
write_to_movie = True
save_last_frame = False

[output]
directory = ./data/animations/manim/
video_dir = {output_directory}/videos/
images_dir = {output_directory}/images/
text_dir = {output_directory}/texts/

[ffmpeg]
executable = ffmpeg
```

#### Test Installation
```python
# test_manim.py
from manim import *

class TestScene(Scene):
    def construct(self):
        text = Text("Manim is working!")
        self.play(Write(text))
        self.wait(2)

# Run: manim test_manim.py TestScene
```

### Motion Canvas Setup

#### Installation
```bash
# Install Motion Canvas for concept visualizations
npm install -g @motion-canvas/cli
npm install @motion-canvas/core @motion-canvas/2d
```

#### Project Setup
```bash
# Create Motion Canvas project
npx @motion-canvas/cli create motion-canvas-project
cd motion-canvas-project
npm install
```

#### Configuration
Create `motion-canvas.config.ts`:
```typescript
import {Configuration} from '@motion-canvas/core';

const config: Configuration = {
  project: [
    './src/scenes/concept-visualization.ts',
    './src/scenes/process-flow.ts',
    './src/scenes/data-visualization.ts',
  ],
  settings: {
    quality: 'medium',
    format: 'mp4',
    fps: 30,
    resolution: [1920, 1080],
  },
  output: './output/',
};

export default config;
```

### Remotion Setup

#### Installation
```bash
# Install Remotion for UI and title sequences
npm install -g @remotion/cli
npm install remotion @remotion/player
```

#### Project Setup
```bash
# Create Remotion project
npx create-video remotion-project
cd remotion-project
npm install
```

#### Configuration
Create `remotion.config.ts`:
```typescript
import {Config} from '@remotion/cli/config';

Config.setVideoImageFormat('jpeg');
Config.setOverwriteOutput(true);
Config.setPixelFormat('yuv420p');
Config.setCodec('h264');
Config.setCrf(18);
Config.setOutputLocation('./output/');

export default Config;
```

## Database and Storage Setup

### PostgreSQL Setup

#### Installation

**Windows:**
```powershell
# Download and install from https://www.postgresql.org/download/windows/
# Or use Chocolatey
choco install postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Linux:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

#### Database Configuration

```sql
-- Create database and user
CREATE DATABASE raso_production;
CREATE USER raso_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE raso_production TO raso_user;

-- Connect to database
\c raso_production;

-- Create tables (run the schema from utils/database_schema.py)
```

#### Environment Configuration
Create `.env.production`:
```env
# Database Configuration
DATABASE_URL=postgresql://raso_user:secure_password@localhost:5432/raso_production
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=30

# Storage Configuration
DATA_PATH=./data/production/
TEMP_PATH=./temp/
BACKUP_PATH=./backups/

# AI Model Configuration
OLLAMA_HOST=http://localhost:11434
AI_MODEL_PRESET=balanced

# Performance Configuration
MAX_CONCURRENT_JOBS=4
MEMORY_LIMIT_GB=12
CLEANUP_INTERVAL_HOURS=24
```

### Redis Setup (for caching)

#### Installation
```bash
# Windows: Download from https://redis.io/download
# macOS:
brew install redis
brew services start redis

# Linux:
sudo apt-get install redis-server
sudo systemctl start redis-server
```

#### Configuration
Create `config/redis.conf`:
```conf
# Memory optimization for 16GB systems
maxmemory 2gb
maxmemory-policy allkeys-lru

# Persistence
save 900 1
save 300 10
save 60 10000

# Network
bind 127.0.0.1
port 6379
```

## Audio Generation Setup

### Coqui TTS Setup

#### Installation
```bash
# Install Coqui TTS for high-quality speech synthesis
pip install coqui-tts

# Download models
tts --list_models
tts --model_name "tts_models/en/ljspeech/tacotron2-DDC" --text "Test" --out_path test.wav
```

#### Configuration
Create `config/tts_config.json`:
```json
{
  "models": {
    "coqui_tts": {
      "model_name": "tts_models/en/ljspeech/tacotron2-DDC",
      "quality": "high",
      "speed": 1.0,
      "pitch": 1.0
    },
    "bark": {
      "model_name": "suno/bark",
      "voice_preset": "v2/en_speaker_6",
      "quality": "high"
    },
    "piper": {
      "model_name": "en_US-lessac-medium",
      "quality": "medium",
      "speed": "fast"
    }
  },
  "default_model": "coqui_tts",
  "fallback_model": "piper"
}
```

### Music Generation Setup

#### MusicGen Setup
```bash
# Install MusicGen for background music
pip install musicgen transformers torch torchaudio
```

#### AudioCraft Setup
```bash
# Install AudioCraft for sound effects
pip install audiocraft
```

## Performance Optimization

### Memory Optimization for 16GB Systems

#### 1. Model Loading Strategy
Create `config/memory_optimization.json`:
```json
{
  "model_loading": {
    "strategy": "on_demand",
    "max_models_in_memory": 2,
    "unload_after_minutes": 10,
    "use_quantization": true
  },
  "video_processing": {
    "max_concurrent_scenes": 2,
    "temp_file_cleanup": "immediate",
    "memory_limit_per_process": "4GB"
  },
  "caching": {
    "enable_model_cache": true,
    "cache_size_gb": 2,
    "cache_location": "./cache/"
  }
}
```

#### 2. System Configuration
```bash
# Increase swap space (Linux/macOS)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Add to /etc/fstab for persistence
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

### GPU Acceleration

#### NVIDIA GPU Setup
```bash
# Install CUDA toolkit
# Download from https://developer.nvidia.com/cuda-downloads

# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# Verify GPU availability
python -c "import torch; print(torch.cuda.is_available())"
```

#### Configuration
Create `config/gpu_config.json`:
```json
{
  "gpu_acceleration": {
    "enabled": true,
    "device": "cuda:0",
    "memory_fraction": 0.8,
    "allow_growth": true
  },
  "video_encoding": {
    "use_nvenc": true,
    "preset": "p4",
    "profile": "high"
  },
  "ai_inference": {
    "use_gpu": true,
    "batch_size": 4,
    "precision": "fp16"
  }
}
```

## Latest AI Model Integration Updates

### Cutting-Edge Models Added (2024)

#### New Coding Models
- **Qwen2.5-Coder-32B**: Advanced Python/Manim code generation with 95%+ accuracy
- **DeepSeek-Coder-V2-Instruct**: Complex algorithm implementation and debugging
- **CodeQwen1.5-7B**: Lightweight code completion and validation

#### New Reasoning Models  
- **DeepSeek-V3**: Cutting-edge reasoning with 98%+ accuracy on scientific content
- **Llama-3.3-70B-Instruct**: Exceptional text generation quality with 128K context
- **Mistral-Large-2**: Advanced multilingual support for 80+ languages

#### New Vision-Language Models
- **Qwen2-VL**: Advanced image and diagram understanding up to 4K resolution
- **LLaVA-NeXT**: Complex visual reasoning and multi-image analysis

### Model Selection Optimization for 16GB Systems

```json
{
  "optimized_16gb_config": {
    "fast_mode": {
      "coding": "codellama:7b",
      "reasoning": "qwen2.5:7b", 
      "vision": "llava:7b",
      "audio": "piper-tts",
      "memory_usage": "8-10GB",
      "concurrent_models": 2
    },
    "balanced_mode": {
      "coding": "qwen2.5-coder:7b",
      "reasoning": "qwen2.5:14b",
      "vision": "qwen2-vl:7b",
      "audio": "coqui-tts", 
      "memory_usage": "12-14GB",
      "concurrent_models": 1
    }
  }
}
```

### Enhanced Animation Framework Integration

#### Manim Community Edition (Latest)
```bash
# Updated installation with latest features
pip install manim[dependencies]==0.18.0

# New LaTeX packages for advanced mathematical rendering
# Windows: Update MiKTeX to latest version
# macOS: brew upgrade mactex
# Linux: sudo apt-get update && sudo apt-get upgrade texlive-full
```

#### Motion Canvas 3.15+ (Latest)
```bash
# Updated Motion Canvas with new features
npm install -g @motion-canvas/cli@latest
npm install @motion-canvas/core@latest @motion-canvas/2d@latest

# New TypeScript features for better animations
npm install typescript@latest @types/node@latest
```

#### Remotion 4.0+ (Latest)
```bash
# Updated Remotion with React 18 support
npm install -g @remotion/cli@latest
npm install remotion@latest @remotion/player@latest

# New React features for better UI animations
npm install react@latest react-dom@latest
```

## Troubleshooting

### Common Issues and Solutions

#### 1. Out of Memory Errors

**Symptoms:**
- Process killed with "Killed" message
- CUDA out of memory errors
- System becomes unresponsive

**Solutions:**
```bash
# Switch to lightweight model preset
export AI_MODEL_PRESET=fast

# Reduce concurrent processing
export MAX_CONCURRENT_JOBS=1

# Enable aggressive cleanup
export CLEANUP_INTERVAL_HOURS=1

# Use CPU-only mode
export FORCE_CPU_ONLY=true

# NEW: Enable model quantization for memory efficiency
export ENABLE_MODEL_QUANTIZATION=true
export QUANTIZATION_LEVEL=int8  # or int4 for more aggressive compression
```

#### 2. FFmpeg Issues

**Symptoms:**
- "ffmpeg not found" errors
- Video encoding failures
- Audio sync issues

**Solutions:**
```bash
# Install FFmpeg with all codecs
# Windows: choco install ffmpeg
# macOS: brew install ffmpeg
# Linux: sudo apt-get install ffmpeg

# Verify installation
ffmpeg -version
ffprobe -version

# Test encoding
ffmpeg -f lavfi -i testsrc=duration=10:size=1920x1080:rate=30 -c:v libx264 test.mp4
```

#### 3. AI Model Loading Issues

**Symptoms:**
- Model download failures
- Slow inference times
- Model compatibility errors

**Solutions:**
```bash
# Clear model cache
rm -rf ~/.ollama/models/

# Re-download models
ollama pull qwen2.5:7b

# Check model status
ollama list

# Test model
ollama run qwen2.5:7b "Hello, world!"
```

#### 4. Animation Framework Issues

**Manim Issues:**
```bash
# Reinstall with latest dependencies
pip uninstall manim
pip install manim[dependencies]==0.18.0

# Install latest LaTeX packages
# Windows: Update MiKTeX to latest version
# macOS: brew upgrade mactex  
# Linux: sudo apt-get update && sudo apt-get upgrade texlive-full

# Test installation with new features
manim --version
python -c "from manim import *; print('Manim working!')"

# NEW: Test GPU acceleration if available
manim --renderer=opengl --write_to_movie test_scene.py TestScene
```

**Motion Canvas Issues:**
```bash
# Clear npm cache and update
npm cache clean --force
npm uninstall -g @motion-canvas/cli
npm install -g @motion-canvas/cli@latest

# Update project dependencies
rm -rf node_modules package-lock.json
npm install @motion-canvas/core@latest @motion-canvas/2d@latest

# NEW: Test TypeScript compilation
npx tsc --noEmit
npx @motion-canvas/cli render src/project.ts
```

**Remotion Issues:**
```bash
# Update to latest version with React 18 support
npm uninstall -g @remotion/cli
npm install -g @remotion/cli@latest

# Update project dependencies
npm update remotion @remotion/player react react-dom

# Clear Remotion cache
npx remotion clear-cache

# NEW: Test with latest React features
npx remotion render src/index.ts HelloWorld out/video.mp4 --gl=angle
```

#### 5. Database and Storage Issues

**PostgreSQL Connection Issues:**
```bash
# Check PostgreSQL service status
sudo systemctl status postgresql  # Linux
brew services list | grep postgresql  # macOS

# Reset PostgreSQL configuration
sudo -u postgres psql -c "ALTER USER raso_user PASSWORD 'new_password';"

# NEW: Optimize for video generation workload
sudo -u postgres psql -c "
  ALTER SYSTEM SET shared_buffers = '4GB';
  ALTER SYSTEM SET effective_cache_size = '12GB';
  ALTER SYSTEM SET work_mem = '256MB';
  SELECT pg_reload_conf();
"
```

**Storage Performance Issues:**
```bash
# Check disk space and I/O
df -h
iostat -x 1 5

# NEW: Enable SSD optimizations
echo 'deadline' | sudo tee /sys/block/sda/queue/scheduler
echo 'mq-deadline' | sudo tee /sys/block/nvme0n1/queue/scheduler

# Optimize file system for large files
sudo tune2fs -o journal_data_writeback /dev/sda1
```

#### 6. AI Model Performance Issues

**Model Loading Failures:**
```bash
# Clear Ollama model cache
ollama list
ollama rm model_name  # Remove problematic models
ollama pull model_name  # Re-download

# NEW: Check model integrity
ollama show model_name --verbose
ollama run model_name "test prompt"

# Verify GPU acceleration
nvidia-smi  # Check GPU usage during inference
```

**Slow Inference Times:**
```bash
# Enable GPU acceleration
export CUDA_VISIBLE_DEVICES=0
export OLLAMA_GPU_LAYERS=35  # Adjust based on model size

# NEW: Enable model quantization
export OLLAMA_LOAD_TIMEOUT=300
export OLLAMA_KEEP_ALIVE=10m

# Use optimized model variants
ollama pull qwen2.5:7b-instruct-q4_K_M  # Quantized version
```

## Latest Features and Integrations (2024 Update)

### Advanced Content Understanding
- **Multi-modal PDF Processing**: Extract figures, equations, and tables automatically
- **LaTeX Equation Recognition**: Convert mathematical notation to Manim animations
- **Citation and Reference Linking**: Automatic cross-referencing in generated content
- **Table-to-Visualization**: Convert research data tables to animated charts

### Real-Time Collaboration Features
- **Multi-user Editing**: Collaborative content creation and review
- **Comment and Annotation System**: Review and feedback on generated content
- **Approval Workflows**: Content publication approval process
- **Real-time Preview**: Live editing and preview capabilities

### Advanced Analytics and Insights
- **Viewer Engagement Analytics**: Track video performance metrics
- **Content Performance Metrics**: Analyze which content performs best
- **A/B Testing**: Test different visual styles and approaches
- **Quality Assessment**: Automatic content quality scoring and recommendations

### Export and Integration Capabilities
- **Multiple Format Export**: MP4, WebM, GIF, PowerPoint presentations
- **Direct Platform Publishing**: YouTube, Vimeo, social media integration
- **API Endpoints**: Third-party integrations and webhook support
- **Automated Workflows**: Trigger-based content generation and publishing

### Security and Compliance Features
- **User Authentication**: Role-based access control (RBAC)
- **Content Encryption**: Secure storage for sensitive research content
- **Audit Logging**: Complete activity tracking and compliance reporting
- **GDPR Compliance**: Data privacy and retention policy management

### Mobile and Accessibility Features
- **Progressive Web App (PWA)**: Mobile-optimized interface with offline capabilities
- **Screen Reader Compatibility**: Full accessibility compliance
- **Closed Captions**: Automatic caption generation and editing
- **High Contrast Mode**: Accessibility-friendly visual options

### Enterprise Architecture Features
- **Microservices Architecture**: Scalable, fault-tolerant system design
- **Service Discovery**: Automatic load balancing and service management
- **Circuit Breaker Pattern**: Fault tolerance and graceful degradation
- **Distributed Tracing**: Complete observability and debugging capabilities

### Performance Monitoring

#### System Monitoring Script
Create `scripts/monitor_system.py`:
```python
#!/usr/bin/env python3
import psutil
import time
import json
from datetime import datetime

def monitor_system():
    """Monitor system resources during video generation."""
    while True:
        stats = {
            'timestamp': datetime.now().isoformat(),
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'gpu_memory': get_gpu_memory() if has_gpu() else None
        }
        
        print(json.dumps(stats, indent=2))
        
        # Alert if resources are high
        if stats['memory_percent'] > 90:
            print("WARNING: Memory usage above 90%")
        if stats['cpu_percent'] > 95:
            print("WARNING: CPU usage above 95%")
            
        time.sleep(5)

def has_gpu():
    try:
        import torch
        return torch.cuda.is_available()
    except ImportError:
        return False

def get_gpu_memory():
    try:
        import torch
        if torch.cuda.is_available():
            return {
                'allocated': torch.cuda.memory_allocated() / 1024**3,
                'cached': torch.cuda.memory_reserved() / 1024**3,
                'total': torch.cuda.get_device_properties(0).total_memory / 1024**3
            }
    except ImportError:
        pass
    return None

if __name__ == "__main__":
    monitor_system()
```

### Log Analysis

#### Log Configuration
Create `config/logging.json`:
```json
{
  "version": 1,
  "disable_existing_loggers": false,
  "formatters": {
    "detailed": {
      "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    }
  },
  "handlers": {
    "file": {
      "class": "logging.handlers.RotatingFileHandler",
      "filename": "logs/raso_production.log",
      "maxBytes": 10485760,
      "backupCount": 5,
      "formatter": "detailed"
    },
    "console": {
      "class": "logging.StreamHandler",
      "formatter": "detailed"
    }
  },
  "loggers": {
    "raso": {
      "level": "INFO",
      "handlers": ["file", "console"]
    }
  }
}
```

## Deployment Options

### Single Server Deployment

#### Docker Compose Setup
Create `docker-compose.production.yml`:
```yaml
version: '3.8'

services:
  raso-app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://raso_user:password@postgres:5432/raso_production
      - REDIS_URL=redis://redis:6379
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - postgres
      - redis
    deploy:
      resources:
        limits:
          memory: 12G
        reservations:
          memory: 8G

  postgres:
    image: postgres:15
    environment:
      - POSTGRES_DB=raso_production
      - POSTGRES_USER=raso_user
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data

volumes:
  postgres_data:
  redis_data:
```

### Multi-Server Cluster Deployment

#### Kubernetes Configuration
Create `k8s/deployment.yaml`:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: raso-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: raso-production
  template:
    metadata:
      labels:
        app: raso-production
    spec:
      containers:
      - name: raso-app
        image: raso:latest
        ports:
        - containerPort: 8000
        resources:
          requests:
            memory: "8Gi"
            cpu: "2"
          limits:
            memory: "12Gi"
            cpu: "4"
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: raso-secrets
              key: database-url
        volumeMounts:
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: data-volume
        persistentVolumeClaim:
          claimName: raso-data-pvc
```

## Security Considerations

### API Security
```python
# config/security.py
SECURITY_CONFIG = {
    'api_rate_limiting': {
        'requests_per_minute': 60,
        'burst_limit': 10
    },
    'authentication': {
        'jwt_secret_key': 'your-secret-key',
        'token_expiry_hours': 24
    },
    'content_filtering': {
        'enable_content_moderation': True,
        'blocked_keywords': ['spam', 'abuse']
    }
}
```

### Data Protection
```bash
# Encrypt sensitive data
gpg --symmetric --cipher-algo AES256 sensitive_config.json

# Set proper file permissions
chmod 600 .env.production
chmod 700 data/
chmod 700 logs/
```

This comprehensive setup guide covers all aspects of the enhanced production video generation system. Follow the sections relevant to your deployment scenario and hardware configuration.