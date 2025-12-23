# RASO Platform

**Research paper Automated Simulation & Orchestration Platform**

RASO is a production-ready, open-source AI platform that transforms research papers into professional-quality animated videos. Using AI agents orchestrated through LangGraph, RASO automates the entire process from paper ingestion to YouTube-ready video generation.

## 🎯 Features

- **Multi-format Paper Ingestion**: Accept papers via title, arXiv URL, or PDF upload
- **AI-Powered Understanding**: Automatically analyze and extract key concepts from research papers
- **Professional Animation**: Generate high-quality animations using Manim CE, Motion Canvas, and Remotion
- **Synchronized Narration**: Create natural voiceover using Coqui TTS with perfect timing
- **YouTube Integration**: Automatically generate metadata and optionally upload to YouTube
- **Local-First**: Runs entirely on local hardware with optional cloud enhancements
- **Agent Architecture**: Modular, debuggable AI agents with single responsibilities

## 🚀 Quick Start

### Windows Setup

1. **Install Prerequisites**
   ```powershell
   # Install Python 3.9+
   winget install Python.Python.3.11
   
   # Install Node.js
   winget install OpenJS.NodeJS
   
   # Install Docker Desktop
   winget install Docker.DockerDesktop
   
   # Install FFmpeg
   winget install Gyan.FFmpeg
   ```

2. **Clone and Setup**
   ```powershell
   git clone <your-repo-url>
   cd raso
   copy .env.example .env
   # Edit .env with your configuration
   ```

3. **Quick Start with Docker (Recommended)**
   ```powershell
   docker-compose up -d
   ```

4. **Or use the startup script**
   ```powershell
   python start.py
   ```

### Access the Platform
- **Frontend**: http://localhost:3000
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 📖 Usage

### Web Interface

1. Open http://localhost:3000 in your browser
2. Enter a research paper title, arXiv URL, or upload a PDF
3. Click "Generate Video" 
4. Monitor real-time progress updates
5. Download your YouTube-ready MP4 when complete

### API Usage

```python
import requests

# Submit a paper for processing
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

# Check job status
status = requests.get(f"http://localhost:8000/api/jobs/{job_id}")
print(status.json())

# Download video when complete
if status.json()["status"] == "completed":
    video = requests.get(f"http://localhost:8000/api/jobs/{job_id}/download")
    with open("research_video.mp4", "wb") as f:
        f.write(video.content)
```

## 🔧 Configuration

### LLM Providers

**Local (Default)**
```env
RASO_LLM_PROVIDER=ollama
RASO_OLLAMA_URL=http://localhost:11434
RASO_OLLAMA_MODEL=deepseek-coder:6.7b
```

**OpenAI (Optional)**
```env
RASO_LLM_PROVIDER=openai
RASO_OPENAI_API_KEY=your-api-key
RASO_OPENAI_MODEL=gpt-4-turbo-preview
```

### Animation Settings

```env
RASO_ANIMATION_RESOLUTION=1920x1080
RASO_ANIMATION_FPS=30
RASO_ANIMATION_QUALITY=high
```

### YouTube Integration

```env
RASO_YOUTUBE_CLIENT_ID=your-client-id
RASO_YOUTUBE_CLIENT_SECRET=your-client-secret
RASO_YOUTUBE_REFRESH_TOKEN=your-refresh-token
```

## 🧪 Testing

```powershell
# Run all tests
python -m pytest

# Run property-based tests
python -m pytest tests/test_*_properties.py -v

# Run with coverage
python -m pytest --cov-report=html
```

## 📁 Project Structure

```
raso/
├── agents/              # AI agents for different tasks
├── graph/               # LangGraph workflow orchestration
├── backend/             # FastAPI backend services
├── frontend/            # React frontend application
├── animation/           # Animation generation services
├── audio/               # Audio processing and TTS
├── video/               # Video composition and rendering
├── tests/               # Comprehensive test suites
├── docker/              # Docker configurations
├── .kiro/specs/         # Design specifications
└── docs/                # Documentation
```

## 🎬 How It Works

1. **Paper Ingestion**: Accepts research papers via multiple input methods
2. **AI Understanding**: Analyzes paper content to extract key concepts
3. **Script Generation**: Creates educational narration with YouTube-friendly language
4. **Visual Planning**: Assigns appropriate animation frameworks to content types
5. **Animation Rendering**: Generates professional animations using multiple engines
6. **Audio Processing**: Creates synchronized voiceover with Coqui TTS
7. **Video Composition**: Combines scenes with smooth transitions
8. **Metadata Generation**: Creates YouTube-optimized titles, descriptions, and tags
9. **Optional Upload**: Automatically uploads to YouTube with proper metadata

## 🏗️ Architecture

The platform uses a **multi-agent architecture** with **LangGraph orchestration**:

- **Local-First**: Runs entirely on local hardware by default
- **Agent-Based**: 11 specialized agents with single responsibilities
- **Deterministic**: Reliable, reproducible video generation
- **Extensible**: Easy to add new animation frameworks or AI providers
- **Tested**: 13 correctness properties with 100+ test iterations each

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```powershell
# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd frontend
npm install
cd ..

# Run tests
python -m pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **LangGraph**: Agent orchestration framework
- **Manim Community Edition**: Mathematical animations
- **Motion Canvas**: Programmatic animations
- **Remotion**: React-based video creation
- **Coqui TTS**: Open-source text-to-speech
- **Ollama**: Local LLM inference

## 📞 Support

- **Documentation**: [SETUP.md](SETUP.md) and [PROJECT_STATUS.md](PROJECT_STATUS.md)
- **Issues**: [GitHub Issues](https://github.com/raso-platform/raso/issues)
- **Quick Start**: Run `python start.py` for automated setup

## 🗺️ Roadmap

- [x] **v1.0**: Core functionality with local LLMs ✅
- [ ] **v1.1**: Advanced animation templates
- [ ] **v1.2**: Multi-language support
- [ ] **v1.3**: Collaborative editing
- [ ] **v2.0**: Cloud deployment options

---

**🎉 Transform research papers into amazing videos with RASO!**

**Made with ❤️ by the RASO Community**