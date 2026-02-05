# Enhanced Visual Content Generation Setup Guide

## Overview

The RASO platform now includes advanced AI-powered visual content generation using multiple frameworks:

- **Manim**: Mathematical animations, equations, and proofs
- **Motion Canvas**: Concept diagrams, flowcharts, and process visualizations  
- **AI Model Manager**: Latest open-source models optimized for 16GB RAM systems
- **Visual Content Manager**: Unified interface coordinating all generators

## System Requirements

### Hardware Requirements (Optimized for Your System)
- **RAM**: 16GB (system is optimized for this configuration)
- **CPU**: 4+ cores (your 4-core system is supported)
- **Storage**: 500GB SSD (system includes cleanup automation)
- **GPU**: Optional (NVIDIA/AMD GPU will accelerate AI inference)

### Software Dependencies

#### Core Dependencies
```bash
# Python packages (already installed)
pip install psutil aiohttp

# Node.js (for Motion Canvas)
# Download from: https://nodejs.org/
node --version  # Should be v18+ 

# FFmpeg (for video processing)
# Already configured in your system
```

#### AI Model Infrastructure
```bash
# Install Ollama for local AI models
# Windows: Download from https://ollama.ai/
# Linux/Mac: curl -fsSL https://ollama.ai/install.sh | sh

# Verify installation
ollama version
```

#### Visual Generation Tools

**Manim (Mathematical Animations)**
```bash
# Install Manim Community Edition
pip install manim

# Verify installation
manim --version

# Test with sample scene
manim -pql scene.py SquareToCircle
```

**Motion Canvas (Concept Visualizations)**
```bash
# Install Motion Canvas CLI globally
npm install -g @motion-canvas/cli

# Verify installation
motion-canvas --version

# Create test project
npx @motion-canvas/cli create test-project
```

## AI Model Configuration

### Recommended Models for 16GB RAM

The system is pre-configured with models optimized for your hardware:

#### FAST Preset (Recommended for 16GB)
- **Coding**: CodeQwen1.5-7B (4.0GB) - Python/Manim code generation
- **Reasoning**: Qwen2.5-7B (4.1GB) - Content analysis and scripts
- **Lightweight**: Llama-3.2-3B (2.0GB) - Basic tasks
- **Vision**: Qwen2-VL-7B (4.5GB) - Image and diagram analysis

#### Model Installation
```bash
# The system will automatically download models when needed
# Or pre-install recommended models:

ollama pull qwen2.5:7b-instruct
ollama pull codeqwen:7b-chat  
ollama pull llama3.2:3b-instruct
ollama pull qwen2-vl:7b-instruct
```

### Memory Management
The system includes intelligent memory management:
- **Dynamic Loading**: Models loaded on-demand
- **Automatic Cleanup**: Unused models unloaded
- **Memory Monitoring**: Prevents out-of-memory errors
- **Quantization**: Uses Q4_0 quantization for efficiency

## Configuration

### Model Preset Selection
```python
from utils.ai_model_manager import ai_model_manager, ModelPreset

# Set preset (FAST recommended for 16GB)
ai_model_manager.set_preset(ModelPreset.FAST)

# Get system recommendations
recommendations = ai_model_manager.get_system_recommendations()
print(recommendations)
```

### Visual Content Manager Setup
```python
from utils.visual_content_manager import visual_content_manager

# Initialize all generators
results = await visual_content_manager.initialize()
print(f"Available generators: {results}")

# Check system status
status = visual_content_manager.get_available_generators()
print(f"Generator status: {status}")
```

## Usage Examples

### 1. Mathematical Animation with Manim
```python
from utils.manim_generator import manim_generator

# Generate equation animation
scene = await manim_generator.generate_equation_animation(
    equation="f(x) = x^2 + 2x + 1",
    context="Quadratic function analysis",
    duration=30.0,
    scene_id="quadratic_demo"
)

# Render to video
output_file = await manim_generator.render_scene(
    scene=scene,
    output_dir="./output",
    quality="medium_quality"
)
```

### 2. Concept Visualization with Motion Canvas
```python
from utils.motion_canvas_generator import motion_canvas_generator

# Generate concept diagram
scene = await motion_canvas_generator.generate_concept_visualization(
    concept="Neural Networks",
    description="Interconnected nodes processing information",
    duration=45.0,
    scene_id="neural_network_concept"
)

# Render to video
output_file = await motion_canvas_generator.render_scene(
    scene=scene,
    output_dir="./output",
    quality="1080p"
)
```

### 3. Unified Visual Content Generation
```python
from utils.visual_content_manager import visual_content_manager, VisualRequest, VisualType

# Create visual request
request = VisualRequest(
    scene_id="demo_scene",
    title="Machine Learning Concepts",
    content="Supervised learning uses labeled data to train models",
    visual_type=VisualType.AUTO,  # Automatically choose best type
    duration=40.0,
    metadata={'concepts': ['machine learning', 'supervised learning']}
)

# Generate visual content
result = await visual_content_manager.generate_visual_content(
    request=request,
    output_dir="./output",
    quality="medium"
)

if result.success:
    print(f"Generated: {result.file_path}")
    print(f"Type: {result.visual_type}")
else:
    print(f"Error: {result.error_message}")
```

## Integration with Video Pipeline

The enhanced visual content generation is automatically integrated into the video composition pipeline:

```python
# In VideoCompositionAgent.execute()
# 1. Initialize visual content manager
await visual_content_manager.initialize()

# 2. Enhance scenes with AI-generated visuals
enhanced_animations = await self._enhance_visual_content(animations, state)

# 3. Compose final video with enhanced content
success = await self._compose_video_production(enhanced_animations, audio, output_path, quality)
```

## Performance Optimization

### For 16GB RAM Systems
1. **Use FAST Preset**: Optimized model selection
2. **Enable Quantization**: Q4_0 quantization reduces memory usage
3. **Sequential Processing**: Process scenes one at a time
4. **Automatic Cleanup**: Models unloaded when not needed

### Storage Management (500GB SSD)
1. **Model Cleanup**: Remove unused models automatically
2. **Video Compression**: Efficient encoding settings
3. **Temporary File Cleanup**: Automatic cleanup of intermediate files
4. **Cache Management**: Intelligent caching with size limits

## Troubleshooting

### Common Issues

#### 1. Ollama Not Found
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve
```

#### 2. Manim Installation Issues
```bash
# Install system dependencies (Linux)
sudo apt-get install ffmpeg

# Install Manim
pip install manim[dependencies]
```

#### 3. Motion Canvas Node.js Issues
```bash
# Update Node.js to v18+
# Install Motion Canvas CLI
npm install -g @motion-canvas/cli@latest
```

#### 4. Memory Issues
```bash
# Check system memory
python -c "from utils.ai_model_manager import ai_model_manager; print(ai_model_manager.get_system_recommendations())"

# Use lighter models
ai_model_manager.set_preset(ModelPreset.FAST)
```

#### 5. GPU Not Detected
```bash
# Check GPU status
nvidia-smi  # For NVIDIA GPUs
rocm-smi    # For AMD GPUs

# GPU is optional - system works with CPU-only
```

## Testing

### Run Enhanced Visual Generation Tests
```bash
# Test AI Model Manager
python -m pytest tests/test_enhanced_visual_generation.py::TestAIModelManager -v

# Test Manim Generator
python -m pytest tests/test_enhanced_visual_generation.py::TestManimGenerator -v

# Test Motion Canvas Generator  
python -m pytest tests/test_enhanced_visual_generation.py::TestMotionCanvasGenerator -v

# Test Visual Content Manager
python -m pytest tests/test_enhanced_visual_generation.py::TestVisualContentManager -v

# Run all tests
python -m pytest tests/test_enhanced_visual_generation.py -v
```

### Manual Testing
```bash
# Test AI model availability
python -c "
import asyncio
from utils.ai_model_manager import ai_model_manager

async def test():
    await ai_model_manager.initialize_ollama()
    models = ai_model_manager.get_available_models_info()
    for model in models:
        print(f'{model[\"name\"]}: Compatible={model[\"compatible\"]}, Recommended={model[\"recommended\"]}')

asyncio.run(test())
"

# Test visual content generation
python -c "
import asyncio
from utils.visual_content_manager import visual_content_manager

async def test():
    results = await visual_content_manager.initialize()
    print(f'Initialization results: {results}')
    
    available = visual_content_manager.get_available_generators()
    print(f'Available generators: {available}')

asyncio.run(test())
"
```

## Next Steps

After setting up the enhanced visual content generation:

1. **Install Dependencies**: Follow the installation steps above
2. **Configure Models**: Set appropriate model preset for your system
3. **Test Generators**: Run the test suite to verify functionality
4. **Generate Content**: Use the examples to create your first enhanced videos
5. **Monitor Performance**: Check memory usage and adjust settings as needed

The system is now ready to generate rich, AI-powered educational videos with mathematical animations, concept diagrams, and professional visual content!

## Hardware-Specific Recommendations

### Your System (16GB RAM, 4-core CPU, 500GB SSD)
- ✅ **Recommended Preset**: FAST (optimized for your hardware)
- ✅ **Model Selection**: 7B parameter models with quantization
- ✅ **Processing**: Sequential scene processing to manage memory
- ✅ **Storage**: Automatic cleanup and compression enabled
- ⚠️ **Avoid**: QUALITY preset (requires 32GB+ RAM)
- ⚠️ **Monitor**: Memory usage during large model operations

The system is specifically optimized for your hardware configuration and will provide excellent performance with the recommended settings.