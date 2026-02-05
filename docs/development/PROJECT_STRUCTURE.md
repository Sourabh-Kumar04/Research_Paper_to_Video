# RASO Video Generation Platform - Project Structure

## Overview
The RASO platform has been reorganized into a clean, scalable structure that separates concerns and improves maintainability.

## Directory Structure

```
raso-platform/
├── README.md                           # Main project documentation
├── main.py                            # Main entry point
├── requirements.txt                   # Python dependencies
├── package.json                       # Node.js dependencies (root level)
├── docker-compose.yml                 # Container orchestration
├── Dockerfile                         # Main container build
├── Makefile                          # Build and deployment commands
├── .env.example                      # Environment template
│
├── src/                              # Main application source
│   ├── backend/                      # TypeScript backend (formerly video-template-engine/)
│   │   ├── src/
│   │   │   ├── services/            # Core business logic
│   │   │   │   ├── template-service.ts
│   │   │   │   ├── content-service.ts
│   │   │   │   ├── rendering-service.ts
│   │   │   │   └── python-bridge.ts
│   │   │   ├── routes/              # API endpoints
│   │   │   ├── config/              # Configuration
│   │   │   ├── types/               # TypeScript definitions
│   │   │   └── utils/               # Utility functions
│   │   ├── package.json
│   │   └── tsconfig.json
│   │
│   ├── agents/                       # Python video generation agents
│   │   ├── simple_script_generator.py
│   │   ├── simple_audio_generator.py
│   │   ├── simple_animation_generator.py
│   │   ├── python_video_composer.py
│   │   ├── moviepy_composer.py
│   │   ├── generate_audio_bridge.py
│   │   ├── generate_animation_bridge.py
│   │   ├── compose_video_bridge.py
│   │   └── check_capabilities.py
│   │
│   ├── frontend/                     # React/TypeScript frontend
│   ├── animation/                    # Animation assets and templates
│   ├── audio/                        # Audio assets and templates
│   ├── video/                        # Video assets and templates
│   ├── graph/                        # Graph and visualization components
│   ├── asset_relationships/          # Asset relationship management
│   └── content_versions/             # Content versioning system
│
├── docs/                             # All documentation
│   ├── PROJECT_STRUCTURE.md          # This file
│   ├── UNIFIED_VIDEO_PIPELINE.md     # System architecture
│   ├── PIPELINE_SUCCESS_REPORT.md    # Success metrics
│   ├── AI_MODEL_INTEGRATION_GUIDE.md
│   ├── FFMPEG_SETUP_GUIDE.md
│   ├── DATABASE_STORAGE_GUIDE.md
│   ├── ENHANCED_PRODUCTION_SETUP.md
│   ├── ENHANCED_VISUAL_SETUP.md
│   ├── SYSTEM_STATUS.md
│   ├── SYSTEM_STATUS_REPORT.md
│   └── VIDEO_COMPOSITION_FIXED.md
│
├── scripts/                          # Build and utility scripts
│   ├── demo_unified_pipeline.py      # Main demo script
│   ├── unified_video_pipeline.py     # Pipeline orchestrator
│   ├── setup_production.py           # Production setup
│   ├── setup_windows.ps1             # Windows setup
│   ├── comprehensive_system_check.py # System diagnostics
│   ├── debug_*.py                    # Debug utilities
│   ├── fix_*.py                      # Fix utilities
│   ├── simple_*.py                   # Simple test scripts
│   └── utils/                        # Utility modules
│       ├── export_integration_system.py
│       ├── collaboration_system.py
│       └── manim_generator.py
│
├── config/                           # Configuration files
│   ├── docker/                       # Docker configurations
│   ├── infra/                        # Infrastructure configs
│   └── ffmpeg/                       # FFmpeg configurations
│
├── output/                           # Generated content
│   ├── demo/                         # Demo outputs
│   ├── raso/                         # RASO outputs
│   ├── test/                         # Test outputs
│   ├── test_video/                   # Test video outputs
│   ├── data/                         # Data files
│   ├── temp/                         # Temporary files
│   ├── logs/                         # Log files
│   ├── python_video_test/            # Python video tests
│   └── current_system_test/          # System test outputs
│
└── .kiro/                           # Kiro IDE configuration
    └── specs/                       # Project specifications
        ├── advanced-video-template-engine/
        └── production-video-generation/
```

## Key Changes Made

### 1. Source Code Organization
- **TypeScript Backend**: Moved from `video-template-engine/` to `src/backend/`
- **Python Agents**: Moved from `agents/` to `src/agents/`
- **Frontend**: Moved from `frontend/` to `src/frontend/`
- **Assets**: Organized into `src/animation/`, `src/audio/`, `src/video/`

### 2. Documentation Consolidation
- All documentation moved to `docs/` directory
- Guides, setup instructions, and reports organized
- Clear separation of user docs vs technical docs

### 3. Scripts and Utilities
- All utility scripts moved to `scripts/` directory
- Debug, setup, and maintenance scripts organized
- Utils modules properly structured

### 4. Output Organization
- All generated content moved to `output/` directory
- Separate subdirectories for different output types
- Temporary files and logs properly contained

### 5. Configuration Management
- Infrastructure configs moved to `config/` directory
- Docker, FFmpeg, and deployment configs organized
- Environment templates at root level

## Updated Import Paths

### Python Imports
```python
# Old
from agents.simple_audio_generator import SimpleAudioGenerator

# New
import sys
sys.path.append('src')
from agents.simple_audio_generator import SimpleAudioGenerator
```

### TypeScript Imports
```typescript
// Python bridge now points to src/agents/
this.scriptsPath = path.join(process.cwd(), 'src', 'agents');
```

## Running the System

### Main Entry Point
```bash
python main.py
```

### Demo Script
```bash
python scripts/demo_unified_pipeline.py
```

### TypeScript Backend
```bash
cd src/backend
npm install
npm start
```

## Benefits of New Structure

1. **Clear Separation of Concerns**: Frontend, backend, agents, and utilities are clearly separated
2. **Scalability**: Easy to add new components without cluttering the root directory
3. **Maintainability**: Related files are grouped together logically
4. **Documentation**: All docs in one place with clear organization
5. **Output Management**: Generated files are contained and organized
6. **Development Experience**: Cleaner workspace, easier navigation

## Migration Notes

- All import paths have been updated to reflect new structure
- The main demo script (`main.py`) provides a clean entry point
- Original functionality is preserved - only organization has changed
- All generated outputs are preserved in the `output/` directory

## Next Steps

1. Update any remaining hardcoded paths in configuration files
2. Update CI/CD pipelines to use new structure
3. Create development setup scripts for new structure
4. Update deployment scripts to use new paths