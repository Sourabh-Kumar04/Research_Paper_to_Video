# RASO Platform - Setup & Usage Guide

## 🚀 Quick Start

### Prerequisites

**System Requirements:**
- Python 3.9+ 
- Node.js 18+
- Docker & Docker Compose
- Git

**Required System Dependencies:**
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install -y ffmpeg python3-dev build-essential curl

# macOS (with Homebrew)
brew install ffmpeg python node

# Windows (with Chocolatey)
choco install ffmpeg python nodejs
```

### 1. Clone and Setup

```bash
# Clone the repository
git clone <your-repo-url>
cd raso

# Copy environment configuration
cp .env.example .env

# Edit configuration (see Configuration section below)
nano .env
```

### 2. Quick Start with Docker (Recommended)

```bash
# Start all services
docker-compose up -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

**Services will be available at:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Ollama: http://localhost:11434

### 3. Local Development Setup

```bash
# Install Python dependencies
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Install Ollama (for local LLM)
# Visit: https://ollama.ai/download
ollama pull deepseek-coder:6.7b

# Start services
make dev  # Or use individual commands below
```

## 🔧 Configuration

### Environment Variables (.env)

```bash
# Core Configuration
RASO_ENV=development
RASO_LOG_LEVEL=INFO
RASO_API_HOST=0.0.0.0
RASO_API_PORT=8000

# Storage Paths
RASO_DATA_PATH=./data
RASO_TEMP_PATH=./temp
RASO_LOG_PATH=./logs

# LLM Configuration (Local by default)
RASO_LLM_PROVIDER=ollama
RASO_OLLAMA_URL=http://localhost:11434
RASO_OLLAMA_MODEL=deepseek-coder:6.7b

# Optional: Cloud LLM APIs
RASO_OPENAI_API_KEY=your-openai-key
RASO_ANTHROPIC_API_KEY=your-anthropic-key

# Animation Settings
RASO_ANIMATION_RESOLUTION=1920x1080
RASO_ANIMATION_FPS=30
RASO_ANIMATION_QUALITY=high

# Audio Settings
RASO_TTS_PROVIDER=coqui
RASO_AUDIO_SAMPLE_RATE=22050

# Optional: YouTube Integration
RASO_YOUTUBE_CLIENT_ID=your-youtube-client-id
RASO_YOUTUBE_CLIENT_SECRET=your-youtube-client-secret
RASO_YOUTUBE_REFRESH_TOKEN=your-refresh-token
```

### LLM Provider Setup

**Option 1: Ollama (Local, Default)**
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Pull recommended model
ollama pull deepseek-coder:6.7b

# Alternative models
ollama pull llama2:7b
ollama pull mistral:7b
```

**Option 2: OpenAI (Cloud)**
```bash
# Get API key from https://platform.openai.com/
export RASO_LLM_PROVIDER=openai
export RASO_OPENAI_API_KEY=sk-your-key-here
```

**Option 3: Anthropic Claude (Cloud)**
```bash
# Get API key from https://console.anthropic.com/
export RASO_LLM_PROVIDER=anthropic
export RASO_ANTHROPIC_API_KEY=your-key-here
```

## 🎬 Usage

### Web Interface

1. **Open Browser:** http://localhost:3000
2. **Enter Paper:** Title, arXiv URL, or upload PDF
3. **Generate Video:** Click "Generate Video" 
4. **Monitor Progress:** Real-time progress updates
5. **Download:** Get your YouTube-ready MP4

### API Usage

```python
import requests

# Submit job
response = requests.post("http://localhost:8000/api/jobs", json={
    "paper_input": {
        "type": "arxiv",
        "content": "https://arxiv.org/abs/1706.03762"  # Attention Is All You Need
    },
    "options": {
        "animation_quality": "high",
        "voice_speed": 1.0
    }
})

job_id = response.json()["job_id"]
print(f"Job submitted: {job_id}")

# Check status
status = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
print(f"Status: {status.json()['status']}")

# Download when complete
if status.json()["status"] == "completed":
    video = requests.get(f"http://localhost:8000/api/jobs/{job_id}/download")
    with open("research_video.mp4", "wb") as f:
        f.write(video.content)
```

### Command Line Usage

```bash
# Using the Makefile
make run-backend    # Start API server
make run-frontend   # Start web interface
make test          # Run all tests
make lint          # Code quality checks

# Direct Python usage
python -m backend.main  # Start API server
python -c "
from graph.master_workflow import RASOMasterWorkflow
import asyncio

async def generate_video():
    workflow = RASOMasterWorkflow()
    result = await workflow.execute({
        'paper_input': {
            'type': 'title',
            'content': 'Attention Is All You Need'
        }
    })
    print(f'Video generated: {result}')

asyncio.run(generate_video())
"
```

## 🧪 Testing

```bash
# Run all tests
make test

# Run specific test types
make test-unit      # Unit tests only
make test-prop      # Property-based tests only
make test-cov       # With coverage report

# Run specific test files
pytest tests/test_llm_service_properties.py -v
pytest tests/test_animation_safety_properties.py -v
```

## 🔍 Troubleshooting

### Common Issues

**1. Ollama Connection Failed**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama service
ollama serve

# Pull required model
ollama pull deepseek-coder:6.7b
```

**2. Animation Dependencies Missing**
```bash
# Install system dependencies
sudo apt install -y ffmpeg python3-dev build-essential

# For Manim
pip install manim

# For Motion Canvas (requires Node.js)
npm install -g @motion-canvas/cli

# For Remotion
npm install -g @remotion/cli
```

**3. TTS Issues**
```bash
# Install Coqui TTS
pip install TTS

# Test TTS installation
python -c "from TTS.api import TTS; print('TTS installed successfully')"
```

**4. Memory Issues**
```bash
# Increase Docker memory limits in docker-compose.yml
# Or reduce concurrent jobs in .env
RASO_MAX_CONCURRENT_JOBS=1
```

**5. Port Conflicts**
```bash
# Change ports in .env
RASO_API_PORT=8001
# Update docker-compose.yml accordingly
```

### Debug Mode

```bash
# Enable debug logging
export RASO_LOG_LEVEL=DEBUG
export RASO_DEBUG=true

# Check logs
tail -f logs/raso.log

# Docker logs
docker-compose logs -f raso-api
```

## 📊 Monitoring

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Service status
curl http://localhost:8000/api/jobs

# Ollama status
curl http://localhost:11434/api/tags
```

### Performance Monitoring

```bash
# Check resource usage
docker stats

# Monitor job progress
watch -n 2 "curl -s http://localhost:8000/api/jobs | jq '.jobs[] | {id: .job_id, status: .status, progress: .progress}'"
```

## 🚀 Production Deployment

### Docker Production

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy with production settings
docker-compose -f docker-compose.prod.yml up -d

# Scale services
docker-compose -f docker-compose.prod.yml up -d --scale animation-worker=3
```

### Kubernetes Deployment

```bash
# Apply Kubernetes manifests (create these based on docker-compose.yml)
kubectl apply -f k8s/

# Check deployment
kubectl get pods
kubectl get services
```

### Environment-Specific Configuration

```bash
# Production environment
export RASO_ENV=production
export RASO_DEBUG=false
export RASO_LOG_LEVEL=INFO

# Staging environment  
export RASO_ENV=staging
export RASO_DEBUG=true
export RASO_LOG_LEVEL=DEBUG
```

## 📈 Scaling

### Horizontal Scaling

```bash
# Scale animation workers
docker-compose up -d --scale animation-worker=5

# Scale API instances (with load balancer)
docker-compose up -d --scale raso-api=3
```

### Performance Optimization

```bash
# Optimize for CPU-intensive workloads
export RASO_MAX_CONCURRENT_JOBS=4  # Match CPU cores

# Optimize for memory-constrained environments
export RASO_MAX_CONCURRENT_JOBS=1
export RASO_ANIMATION_QUALITY=medium
```

## 🔐 Security

### API Security

```bash
# Generate secure secret key
export RASO_SECRET_KEY=$(openssl rand -hex 32)

# Configure CORS
export RASO_CORS_ORIGINS="https://yourdomain.com,https://app.yourdomain.com"

# Enable rate limiting
export RASO_RATE_LIMIT_PER_MINUTE=30
```

### File System Security

```bash
# Set proper permissions
chmod 700 data/ temp/ logs/
chown -R app:app data/ temp/ logs/
```

## 📚 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **Architecture Guide:** See `.kiro/specs/raso-platform/design.md`
- **Requirements:** See `.kiro/specs/raso-platform/requirements.md`
- **Contributing:** See `CONTRIBUTING.md`
- **License:** See `LICENSE`

## 🆘 Support

- **Issues:** Create GitHub issues for bugs
- **Discussions:** Use GitHub Discussions for questions
- **Documentation:** Check README.md and design documents
- **Community:** Join our Discord server (if available)

---

**🎉 You're ready to transform research papers into amazing videos with RASO!**