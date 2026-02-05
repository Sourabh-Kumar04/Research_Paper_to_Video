# Unified Video Pipeline

## Overview

The Unified Video Pipeline combines the TypeScript Advanced Video Template Engine with Python-powered video generation agents to create real videos with TTS audio, animations, and professional composition.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    TypeScript Template Engine                   │
├─────────────────────────────────────────────────────────────────┤
│ • Template Management    • Content Processing                   │
│ • Queue Management      • API Endpoints                        │
│ • Progress Tracking     • Interactive Features                 │
└─────────────────┬───────────────────────────────────────────────┘
                  │ Python Bridge
                  ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Python Video Agents                         │
├─────────────────────────────────────────────────────────────────┤
│ • Script Generation     • Audio Generation (TTS)               │
│ • Animation Creation    • Video Composition                     │
│ • FFmpeg Integration    • Multiple Fallbacks                   │
└─────────────────────────────────────────────────────────────────┘
```

## Components

### TypeScript Template Engine
- **Location**: `video-template-engine/`
- **Purpose**: Template management, content processing, API endpoints
- **Key Files**:
  - `src/services/rendering-service.ts` - Main rendering orchestration
  - `src/services/python-bridge.ts` - Bridge to Python agents
  - `src/routes/system.ts` - System capability endpoints

### Python Video Agents
- **Location**: `agents/`
- **Purpose**: Real video generation with TTS and animations
- **Key Files**:
  - `python_video_composer.py` - Main video composition orchestrator
  - `simple_audio_generator.py` - TTS audio generation
  - `simple_animation_generator.py` - FFmpeg-based animations
  - `moviepy_composer.py` - High-quality video composition

### Bridge Scripts
- **Location**: `agents/`
- **Purpose**: Interface between TypeScript and Python
- **Key Files**:
  - `generate_audio_bridge.py` - Audio generation bridge
  - `generate_animation_bridge.py` - Animation generation bridge
  - `compose_video_bridge.py` - Video composition bridge
  - `check_capabilities.py` - System capability checker

## Features

### Template Engine Features
- ✅ Template creation and management
- ✅ Version control and rollback
- ✅ Dynamic content processing
- ✅ Multi-format video rendering
- ✅ Interactive elements support
- ✅ Batch processing
- ✅ Real-time progress tracking
- ✅ System capability monitoring

### Video Generation Features
- ✅ Text-to-Speech audio generation (multiple engines)
- ✅ FFmpeg-based animations and text overlays
- ✅ MoviePy high-quality video composition
- ✅ OpenCV and PIL fallback options
- ✅ Automatic dependency detection
- ✅ Graceful degradation with fallbacks

## Quick Start

### Prerequisites
- Node.js 16+ and npm
- Python 3.8+
- FFmpeg (optional, for animations)

### Installation & Startup
```bash
# Start the complete unified pipeline
python start_unified_pipeline.py
```

This script will:
1. Check prerequisites
2. Install dependencies
3. Start TypeScript service
4. Run integration tests
5. Keep service running

### Manual Setup
```bash
# Install TypeScript dependencies
cd video-template-engine
npm install
npm run build

# Start TypeScript service
npm start

# In another terminal, test the pipeline
python test_unified_video_pipeline.py
```

## API Endpoints

### Core Template Engine
- `POST /api/v1/templates` - Create template
- `GET /api/v1/templates/:id` - Get template
- `POST /api/v1/content` - Create content set
- `POST /api/v1/render` - Start video rendering
- `GET /api/v1/render/:jobId` - Check render progress

### System Monitoring
- `GET /api/v1/system/capabilities` - Check system capabilities
- `GET /api/v1/system/health` - System health check
- `GET /api/v1/health` - Basic service health

## Video Generation Pipeline

### 1. Template Processing
```typescript
// TypeScript processes template and content
const template = await templateService.getTemplate(templateId);
const contentSet = await contentService.getContentSet(contentName);
```

### 2. Script Generation
```python
# Python converts template to narration script
script = create_script_from_template(template, contentSet)
```

### 3. Audio Generation
```python
# TTS engines generate audio for each scene
audio_assets = await audio_generator.generate_audio_assets(script)
```

### 4. Animation Generation
```python
# FFmpeg creates animations and text overlays
animation_assets = await animation_generator.generate_animation_assets(script)
```

### 5. Video Composition
```python
# MoviePy/OpenCV/PIL compose final video
result = video_composer.compose_video(audio_assets, animation_assets, output_path)
```

## Configuration

### Environment Variables
```bash
# TypeScript Service
PORT=3000
NODE_ENV=development
MONGODB_URI=mongodb://localhost:27017/video-template-engine
REDIS_URL=redis://localhost:6379

# Python Bridge
PYTHON_PATH=python
FFMPEG_PATH=/usr/local/bin/ffmpeg
```

### Capability Detection
The system automatically detects available capabilities:
- TTS engines (pyttsx3, Windows SAPI, macOS say, Linux espeak)
- Video libraries (MoviePy, OpenCV, PIL)
- FFmpeg availability
- System dependencies

## Testing

### Integration Test
```bash
python test_unified_video_pipeline.py
```

Tests the complete pipeline:
1. System capability check
2. Template creation
3. Content creation
4. Video rendering
5. Output validation

### Individual Components
```bash
# Test TypeScript service
cd video-template-engine
npm test

# Test Python agents
python -m pytest tests/
```

## Troubleshooting

### Common Issues

**TypeScript service won't start**
- Check Node.js version: `node --version`
- Install dependencies: `npm install`
- Check port availability: `lsof -i :3000`

**Python bridge fails**
- Install TTS engine: `pip install pyttsx3`
- Install video libraries: `pip install moviepy opencv-python Pillow`
- Check FFmpeg: `ffmpeg -version`

**Video generation produces placeholders**
- Check system capabilities: `GET /api/v1/system/capabilities`
- Install missing Python dependencies
- Verify FFmpeg installation

### Logs and Debugging
- TypeScript logs: Console output from `npm start`
- Python logs: Output from bridge scripts
- System capabilities: `/api/v1/system/capabilities`
- Health status: `/api/v1/system/health`

## Development

### Adding New Features

**New Template Features**
1. Update TypeScript types in `src/types/index.ts`
2. Modify template service in `src/services/template-service.ts`
3. Update API routes in `src/routes/templates.ts`

**New Video Generation Features**
1. Extend Python agents in `agents/`
2. Update bridge scripts for new capabilities
3. Modify `python-bridge.ts` for new functionality

### Testing New Features
1. Add unit tests for TypeScript components
2. Add integration tests for Python agents
3. Update `test_unified_video_pipeline.py` for end-to-end testing

## Production Deployment

### Docker Setup
```dockerfile
# Multi-stage build for TypeScript + Python
FROM node:18-alpine AS typescript-builder
# ... TypeScript build steps

FROM python:3.11-slim AS python-runtime
# ... Python setup and dependencies

FROM python-runtime AS production
# ... Copy TypeScript build and start services
```

### Scaling Considerations
- Use Redis for queue management
- MongoDB for template/content storage
- Load balancer for multiple instances
- Separate Python workers for video generation

## License

MIT License - see LICENSE file for details.