# RASO Video Generation Platform

🎬 **Professional Cinematic Video Generation with AI-Powered Content Creation**

A unified platform combining TypeScript web services with Python-powered cinematic video generation to create professional, broadcast-quality educational content automatically. RASO transforms research papers into engaging videos with professional camera work, color grading, sound design, and 4K/8K cinematic quality.

## 🎬 NEW: Cinematic Production Features

### Professional Video Production
- **4K/8K Cinematic Quality**: Professional broadcast standards with 24fps cinematic frame rates
- **Dynamic Camera Movements**: Content-aware pans, zooms, dollies, and crane shots
- **Professional Color Grading**: Film emulation (Kodak, Fuji, Cinema) with mood-based adjustments
- **Advanced Sound Design**: Multi-layer audio with ambient sound, music scoring, and professional mixing
- **Sophisticated Compositing**: Professional transitions, visual effects, and advanced editing
- **Film-Style Effects**: Film grain, dynamic lighting, depth of field, and motion blur

### Intelligent Content Analysis
- **Mood-Based Cinematography**: Camera movements adapt to content (welcoming, serious, exciting, analytical)
- **Technical Depth Control**: Professional explanations for AI/ML engineers and software engineers
- **Scene-Aware Processing**: Different cinematic treatment for introductions, problems, solutions, and conclusions
- **Quality Optimization**: Automatic quality settings based on content complexity and target audience

## ✅ Current Status

- **🎬 CINEMATIC PRODUCTION**: Complete professional video generation with cinema-quality features
- **Advanced Video Template Engine**: Complete TypeScript microservices architecture
- **Python Video Generation**: Real TTS audio, animations, and video composition  
- **Unified Pipeline**: Working integration generating actual MP4 videos (1-3GB cinematic output)
- **Project Structure**: Organized and clean codebase
- **Production Ready**: Scalable architecture with monitoring and error handling

## 🚀 Quick Start - Cinematic Production

### 1. Install Dependencies
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install FFmpeg (required for cinematic features)
# Windows: Download from https://ffmpeg.org/
# macOS: brew install ffmpeg  
# Linux: apt-get install ffmpeg
```

### 2. Configure Environment
```bash
# Copy and edit environment configuration
cp .env.example .env

# Set your Google Gemini API key for intelligent content generation
RASO_GOOGLE_API_KEY="your_google_api_key_here"

# Enable cinematic features
RASO_CINEMATIC_MODE=true
RASO_CINEMATIC_QUALITY=cinematic_4k
```

### 3. Generate Cinematic Video
```bash
# Run the cinematic production system
python start_cinematic_production.py

# Or use the standard production system
python start_production.py

# Or run the complete demo
python main.py
```

### 4. Example Cinematic Output
The system generates professional videos with:
- **Duration**: 3-5 minutes of technical content
- **Quality**: 4K (3840x2160) at 24fps cinematic frame rate
- **File Size**: 1-3GB for high-quality cinematic content
- **Features**: Camera movements, color grading, professional audio, transitions

## 📊 System Requirements

### Minimum Requirements (Standard Quality)
- **RAM**: 8GB for HD processing
- **CPU**: Modern multi-core processor (4+ cores)
- **Storage**: 10GB free space
- **Software**: FFmpeg with basic codecs

### Recommended Requirements (Cinematic 4K)
- **RAM**: 16GB for 4K processing
- **CPU**: High-end processor (8+ cores recommended)
- **Storage**: 50GB free space for temporary files
- **Software**: FFmpeg with libx264/libx265 support

### Professional Requirements (Cinematic 8K)
- **RAM**: 32GB for 8K processing
- **CPU**: High-end processor (16+ cores)
- **Storage**: SSD for temporary files
- **GPU**: Hardware acceleration (NVENC/QuickSync) for faster encoding

## 📁 Project Structure

```
raso-platform/
├── src/
│   ├── backend/          # TypeScript API and services
│   ├── agents/           # Python video generation
│   ├── frontend/         # React frontend
│   └── [assets]/         # Animation, audio, video assets
├── docs/                 # All documentation
├── scripts/              # Utility and demo scripts
├── output/               # Generated videos and assets
└── config/               # Configuration files
```

See [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) for detailed structure.

## 🎯 Features

### 🎬 Cinematic Production (NEW)
- ✅ **4K/8K Cinematic Quality**: Professional broadcast standards (3840x2160, 7680x4320)
- ✅ **Dynamic Camera Movements**: Content-aware pans, zooms, dollies, crane shots
- ✅ **Professional Color Grading**: Film emulation with mood-based adjustments
- ✅ **Advanced Sound Design**: Multi-layer audio with ambient sound and music
- ✅ **Sophisticated Compositing**: Professional transitions and visual effects
- ✅ **Film-Style Effects**: Film grain, dynamic lighting, depth of field
- ✅ **Intelligent Content Analysis**: Mood-based cinematography and scene adaptation

### Template Engine (TypeScript)
- ✅ Template creation and management
- ✅ Dynamic content processing  
- ✅ Multi-format video rendering
- ✅ Real-time progress tracking
- ✅ Queue management with Redis
- ✅ MongoDB data persistence
- ✅ Interactive elements support
- ✅ Version control and rollback

### Video Generation (Python)
- ✅ **Professional TTS Audio**: 5 engines with sample rate optimization (44.1kHz/48kHz)
- ✅ **Real Video Content**: FFmpeg-based animations and overlays (no placeholders)
- ✅ **Advanced Composition**: MoviePy high-quality video composition with effects
- ✅ **Multiple Quality Presets**: From HD to 8K cinematic with appropriate bitrates
- ✅ **Automatic Capability Detection**: System optimization and fallback handling
- ✅ **Professional Output**: Broadcast-quality MP4 with perfect audio sync

### Integration Features
- ✅ TypeScript ↔ Python bridge
- ✅ **Real cinematic video output** (1-3GB professional files)
- ✅ System health monitoring
- ✅ Error handling and recovery
- ✅ Batch processing capabilities
- ✅ **Google Gemini LLM integration** for intelligent content generation

## 📚 Documentation

- [System Architecture](docs/UNIFIED_VIDEO_PIPELINE.md)
- [Success Report](docs/PIPELINE_SUCCESS_REPORT.md)
- [Project Structure](docs/PROJECT_STRUCTURE.md)
- [Setup Guides](docs/)
- [API Reference](src/backend/README.md)

## 🛠️ Installation

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- FFmpeg (optional, for enhanced animations)

### Quick Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Install TypeScript dependencies
cd src/backend && npm install

# Run the demo
python main.py
```

### Full Setup
See [docs/ENHANCED_PRODUCTION_SETUP.md](docs/ENHANCED_PRODUCTION_SETUP.md) for complete installation.

## 🎬 Generated Output

The system generates professional cinematic content:

### Cinematic Quality (NEW)
- **4K/8K MP4 Videos**: Professional broadcast quality with cinematic frame rates (24fps)
- **File Sizes**: 1-3GB for 4K cinematic content, 3-6GB for 8K
- **Professional Audio**: 48kHz stereo with multi-layer sound design
- **Visual Effects**: Camera movements, color grading, film grain, transitions
- **Technical Content**: Professional explanations for AI/ML engineers and software engineers

### Standard Quality
- **HD MP4 Videos**: High-quality with audio sync (1280x720, 1920x1080)
- **TTS Audio**: Natural speech in multiple languages (44.1kHz)
- **Animations**: Text overlays and visual effects
- **Metadata**: Complete generation reports

Example outputs:
- **Cinematic 4K**: `output/cinematic_production/final_video_*.mp4` (1.5-3GB, 3-5 minutes)
- **Standard HD**: `output/demo/final_video.mp4` (383KB-50MB, variable duration)

## 🔧 System Requirements

### Minimum
- Python 3.8+ with basic libraries
- Node.js 16+ for TypeScript service
- 2GB RAM, 1GB disk space

### Recommended  
- Python with MoviePy, OpenCV, PIL
- FFmpeg for enhanced animations
- Redis for queue management
- MongoDB for data persistence

## 🚀 Production Deployment

```bash
# Docker deployment
docker-compose up -d

# Manual deployment
python scripts/setup_production.py
```

## 📊 Performance

- **Video Generation**: 30-60 seconds per minute of content
- **Audio Generation**: Real-time TTS processing
- **System Throughput**: Multiple concurrent jobs
- **Output Quality**: 1280x720 MP4, 44.1kHz audio

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install frontend dependencies
cd src/frontend && npm install

# Run tests
python -m pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🎉 Success Metrics

- ✅ **🎬 CINEMATIC PRODUCTION**: Professional camera work, color grading, and sound design
- ✅ **4K/8K Quality**: Broadcast-standard video generation with cinematic frame rates
- ✅ **Real Video Generation**: No more placeholders - substantial, high-quality content
- ✅ **Complete Integration**: TypeScript + Python working together seamlessly
- ✅ **Production Ready**: Scalable architecture with monitoring and error handling
- ✅ **Clean Codebase**: Organized structure for maintainability and extensibility
- ✅ **Professional Audio**: Multi-layer sound design with ambient audio and music
- ✅ **Intelligent Content**: Google Gemini LLM integration for technical depth

## 🙏 Acknowledgments

- **TypeScript/Node.js**: Modern web service architecture
- **Python Ecosystem**: MoviePy, OpenCV, PIL for video processing
- **FFmpeg**: Professional video processing capabilities
- **TTS Libraries**: pyttsx3 and platform-specific engines
- **Open Source Community**: Libraries and frameworks used

## 📞 Support

- **Documentation**: [docs/](docs/) directory
- **Issues**: GitHub Issues
- **Quick Start**: Run `python main.py` for automated demo

---

**The RASO platform is now generating real videos with professional quality!** 🎬✨