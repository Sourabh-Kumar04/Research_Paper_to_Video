# RASO Platform - Production Setup Guide

This guide will help you set up the RASO platform for production use with real TTS, video composition, and YouTube integration.

## 🚀 Quick Start

1. **Run the production setup script:**
   ```bash
   python setup_production.py
   ```

2. **Configure your environment:**
   ```bash
   cp .env.production .env
   # Edit .env with your actual configuration
   ```

3. **Start the services:**
   ```bash
   # Option 1: Direct
   python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000
   
   # Option 2: Docker
   docker-compose -f docker-compose.prod.yml up -d
   ```

## 📋 System Requirements

### Required Software
- **Python 3.8+**
- **FFmpeg** - For video and audio processing
- **Redis** - For job queue and caching
- **Node.js 16+** - For frontend (if running separately)

### Platform-Specific Requirements

#### Windows
- **FFmpeg**: Download from https://ffmpeg.org/download.html
- **System TTS**: Built-in (Windows SAPI)

#### macOS
- **FFmpeg**: `brew install ffmpeg`
- **System TTS**: Built-in (`say` command)

#### Linux
- **FFmpeg**: `sudo apt install ffmpeg`
- **System TTS**: `sudo apt install espeak espeak-data`

## 🔧 Production Dependencies

The production version includes these additional dependencies:

### Audio Processing
- **TTS (Coqui)** - High-quality text-to-speech
- **soundfile** - Audio file I/O
- **System TTS fallback** - Windows SAPI, macOS say, Linux espeak

### Video Processing
- **moviepy** - Video composition and editing
- **pillow** - Image processing for thumbnails and overlays

### YouTube Integration
- **google-api-python-client** - YouTube Data API v3
- **google-auth** - OAuth2 authentication

## ⚙️ Configuration

### Environment Variables

Copy `.env.production` to `.env` and configure:

```bash
# Core Settings
RASO_ENV=production
RASO_DEBUG=false
RASO_SECRET_KEY=your_secure_secret_key

# API Configuration
RASO_API_HOST=0.0.0.0
RASO_API_PORT=8000
RASO_API_WORKERS=4

# Database
RASO_DATABASE_URL=redis://localhost:6379/0

# Audio Settings
RASO_AUDIO_TTS_PROVIDER=coqui
RASO_AUDIO_TTS_MODEL=tts_models/en/ljspeech/tacotron2-DDC
RASO_AUDIO_VOICE_SPEED=1.0

# Video Settings
RASO_VIDEO_CODEC=libx264
RASO_VIDEO_BITRATE=5000k
RASO_ANIMATION_RESOLUTION=1920x1080

# YouTube Integration (Optional)
RASO_YOUTUBE_CLIENT_ID=your_client_id
RASO_YOUTUBE_CLIENT_SECRET=your_client_secret
RASO_YOUTUBE_REFRESH_TOKEN=your_refresh_token
```

### YouTube API Setup (Optional)

1. **Create a Google Cloud Project:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing one

2. **Enable YouTube Data API v3:**
   - Go to APIs & Services > Library
   - Search for "YouTube Data API v3"
   - Click Enable

3. **Create OAuth2 Credentials:**
   - Go to APIs & Services > Credentials
   - Click "Create Credentials" > "OAuth 2.0 Client IDs"
   - Choose "Desktop application"
   - Download the JSON file

4. **Get Refresh Token:**
   ```bash
   python scripts/youtube_auth.py
   ```

## 🐳 Docker Deployment

### Using Docker Compose (Recommended)

```bash
# Build and start all services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Stop services
docker-compose -f docker-compose.prod.yml down
```

### Manual Docker Build

```bash
# Build the image
docker build -t raso-platform .

# Run with Redis
docker run -d --name redis redis:7-alpine
docker run -d --name raso -p 8000:8000 --link redis:redis raso-platform
```

## 🐧 Linux Systemd Service

1. **Install the service:**
   ```bash
   sudo cp raso.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable raso
   ```

2. **Start the service:**
   ```bash
   sudo systemctl start raso
   sudo systemctl status raso
   ```

3. **View logs:**
   ```bash
   sudo journalctl -u raso -f
   ```

## 🔍 Production Features

### Real Audio Generation
- **Coqui TTS**: High-quality neural text-to-speech
- **System TTS Fallback**: Windows SAPI, macOS say, Linux espeak
- **Audio Processing**: Normalization, speed adjustment, format conversion

### Real Video Composition
- **FFmpeg Integration**: Professional video processing
- **MoviePy Fallback**: Python-based video editing
- **Multiple Formats**: MP4, WebM, AVI support
- **Chapter Support**: Automatic chapter generation

### YouTube Integration
- **Automatic Upload**: Direct upload to YouTube
- **Metadata Optimization**: SEO-friendly titles and descriptions
- **Chapter Integration**: Automatic chapter timestamps
- **Privacy Controls**: Public, unlisted, or private uploads

### Performance Optimizations
- **Concurrent Processing**: Multiple jobs in parallel
- **Resumable Uploads**: Large video upload reliability
- **Caching**: Redis-based caching for improved performance
- **Resource Management**: Memory and CPU optimization

## 📊 Monitoring and Logging

### Log Files
- **Application Logs**: `logs/service.log`
- **Agent Logs**: Individual agent logging
- **Error Tracking**: Structured error logging

### Health Checks
- **API Health**: `GET /health`
- **Service Status**: `GET /api/status`
- **Job Monitoring**: `GET /api/jobs/{job_id}`

### Metrics (Optional)
- **Prometheus Integration**: Available on port 9090
- **Custom Metrics**: Job completion rates, processing times
- **Resource Usage**: CPU, memory, disk usage

## 🔒 Security Considerations

### API Security
- **CORS Configuration**: Restrict allowed origins
- **Rate Limiting**: Prevent API abuse
- **Input Validation**: Sanitize all inputs

### File Security
- **Temporary Files**: Automatic cleanup
- **Upload Limits**: File size restrictions
- **Path Validation**: Prevent directory traversal

### YouTube Security
- **OAuth2 Flow**: Secure authentication
- **Token Refresh**: Automatic token renewal
- **Scope Limitation**: Minimal required permissions

## 🚨 Troubleshooting

### Common Issues

#### TTS Not Working
```bash
# Check TTS installation
python -c "from TTS.api import TTS; print('TTS OK')"

# Fallback to system TTS
export RASO_AUDIO_TTS_PROVIDER=system
```

#### Video Composition Fails
```bash
# Check FFmpeg
ffmpeg -version

# Check MoviePy
python -c "import moviepy; print('MoviePy OK')"
```

#### YouTube Upload Fails
```bash
# Check credentials
python -c "from googleapiclient.discovery import build; print('YouTube API OK')"

# Verify token
python scripts/test_youtube_auth.py
```

### Performance Issues

#### High Memory Usage
- Reduce concurrent jobs: `RASO_MAX_CONCURRENT_JOBS=1`
- Lower video quality: `RASO_VIDEO_BITRATE=2000k`
- Enable cleanup: Check temp directory cleanup

#### Slow Processing
- Use faster TTS model: `RASO_AUDIO_TTS_MODEL=tts_models/en/ljspeech/fast_pitch`
- Reduce video resolution: `RASO_ANIMATION_RESOLUTION=1280x720`
- Enable parallel processing: `RASO_PARALLEL_PROCESSING=true`

## 📈 Scaling for Production

### Horizontal Scaling
- **Load Balancer**: Nginx or HAProxy
- **Multiple Workers**: Scale API workers
- **Distributed Queue**: Redis Cluster

### Vertical Scaling
- **CPU**: More cores for video processing
- **Memory**: 8GB+ recommended for large videos
- **Storage**: SSD for temporary files

### Cloud Deployment
- **AWS**: ECS, Lambda, S3 integration
- **Google Cloud**: GKE, Cloud Run, Cloud Storage
- **Azure**: Container Instances, Blob Storage

## 📞 Support

For production support and enterprise features:
- **Documentation**: Check the `/docs` endpoint
- **Issues**: GitHub Issues for bug reports
- **Enterprise**: Contact for custom deployments

---

**🎉 Congratulations!** Your RASO platform is now ready for production use with real TTS, video composition, and YouTube integration.