# Design Document

## Overview

The current RASO video generation system produces placeholder videos because it uses mock content generation instead of real video creation. This design addresses the core issues and implements a production-ready video generation pipeline that creates actual visual content using Google Gemini LLM integration and proper animation generators.

## Architecture

### Current Problems Identified

1. **Mock Content Generation**: The `production_video_generator.py` creates intentionally small mock files to test placeholder detection
2. **Missing Real Generators**: Video generators create basic text overlays instead of rich visual content
3. **Broken Method Calls**: Audio generator calls non-existent methods causing fallbacks to silent audio
4. **No Gemini Integration**: The system doesn't properly use Gemini LLM for content generation

### New Architecture Components

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gemini LLM    │    │  Content         │    │  Video          │
│   Integration   │───▶│  Generation      │───▶│  Composition    │
│                 │    │  Pipeline        │    │  Engine         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Script & Code  │    │  Real Animation  │    │  Final Video    │
│  Generation     │    │  Generation      │    │  Output         │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components and Interfaces

### 1. Enhanced Production Video Generator

**Purpose**: Replace mock content generation with real content creation
**Key Changes**:
- Remove mock file creation
- Integrate with Gemini LLM for script generation
- Use real animation generators
- Implement proper error handling

### 2. Gemini LLM Content Generator

**Purpose**: Generate intelligent, contextual content for research papers
**Capabilities**:
- Analyze paper content and extract key concepts
- Generate educational scene scripts
- Create Manim animation code for mathematical content
- Provide fallback content when API is unavailable

### 3. Multi-Method Video Generation Pipeline

**Purpose**: Ensure video content is always generated using best available method
**Generation Methods** (in priority order):
1. **Manim Mathematical Animations**: For papers with mathematical content
2. **Enhanced Text Overlay Videos**: For conceptual content with rich visuals
3. **Basic FFmpeg Videos**: As reliable fallback

### 4. Fixed Audio Generation System

**Purpose**: Generate real TTS audio without infinite loops
**Key Fixes**:
- Correct method names in `_generate_scene_audio_simple`
- Add proper timeouts to prevent hanging
- Implement retry logic with limits
- Ensure fallback to silent audio works properly

## Data Models

### Enhanced Scene Data Structure

```python
@dataclass
class EnhancedScene:
    id: str
    title: str
    narration: str
    duration: float
    visual_description: str
    manim_code: Optional[str] = None
    concepts: List[str] = field(default_factory=list)
    visual_type: str = "auto"  # "manim", "text_overlay", "basic"
```

### Video Generation Request

```python
@dataclass
class VideoGenerationRequest:
    paper_content: str
    paper_type: str  # "title", "abstract", "full_text"
    output_directory: str
    quality: str = "medium"
    use_gemini: bool = True
    max_duration: int = 300  # 5 minutes max
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Real Content Generation
*For any* video generation request, the system should produce video files larger than 1MB with actual visual content, not placeholder mock files
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Gemini Integration Success
*For any* paper content when Gemini API is available, the system should successfully generate contextual scene scripts and visual descriptions
**Validates: Requirements 2.1, 2.2, 2.3**

### Property 3: Fallback Content Generation
*For any* video generation request when Gemini is unavailable, the system should still produce meaningful content using enhanced fallback methods
**Validates: Requirements 2.5, 6.2**

### Property 4: Audio Generation Completion
*For any* scene with text content, the audio generation should complete within timeout limits without infinite loops
**Validates: Requirements 4.1, 4.2, 7.1, 7.4**

### Property 5: Multi-Method Video Generation
*For any* scene content, if the primary video generation method fails, the system should automatically try secondary methods until success
**Validates: Requirements 3.1, 3.2, 3.3, 3.4**

### Property 6: Video Composition Success
*For any* set of generated scene assets, the final video composition should produce a valid MP4 file with synchronized audio and video
**Validates: Requirements 5.1, 5.2, 5.4**

### Property 7: Timeout Enforcement
*For any* video generation operation, the system should enforce timeout limits and never exceed maximum generation time
**Validates: Requirements 7.1, 7.2, 7.4**

### Property 8: Error Recovery
*For any* generation failure, the system should log the error, attempt recovery methods, and still produce usable output
**Validates: Requirements 6.1, 6.3, 6.5**

## Error Handling

### Timeout Management
- Set 60-second timeout for audio generation
- Set 5-minute timeout for video generation per scene
- Set 10-minute maximum for entire video generation process
- Cancel operations that exceed limits

### Retry Logic
- Maximum 3 retry attempts for video generation
- Maximum 2 retry attempts for audio generation
- Exponential backoff between retries
- Different methods tried on each retry

### Fallback Strategies
1. **Gemini Unavailable**: Use enhanced template-based content generation
2. **Manim Fails**: Fall back to enhanced text overlay videos
3. **All Video Generation Fails**: Create basic FFmpeg video with text
4. **Audio Generation Fails**: Create properly formatted silent audio

## Testing Strategy

### Unit Tests
- Test individual video generation methods
- Test audio generation with different TTS engines
- Test Gemini LLM integration with mock responses
- Test timeout and retry mechanisms

### Property-Based Tests
- Generate random paper content and verify real video output
- Test fallback behavior with simulated failures
- Verify timeout enforcement across different scenarios
- Test error recovery with various failure conditions

### Integration Tests
- End-to-end video generation with real paper content
- Test with and without Gemini API availability
- Verify final video quality and synchronization
- Test cleanup of temporary files

### Performance Tests
- Measure generation time for different content types
- Test memory usage during video composition
- Verify timeout limits are enforced
- Test concurrent video generation requests