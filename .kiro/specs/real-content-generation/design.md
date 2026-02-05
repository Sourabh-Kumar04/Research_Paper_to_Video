# Design Document

## Introduction

This design addresses the core issue where RASO generates placeholder videos without sound because the content generation agents (script, audio, animation) are failing to produce real content files. The current agents are over-engineered with complex AI integrations that are failing, causing fallback to empty placeholders.

## Overview

The current system has sophisticated agents that attempt to use advanced AI models and TTS services, but these dependencies are not properly configured or available, causing the entire content generation pipeline to fail silently. We need to implement a robust, working content generation system with proper fallbacks.

## Architecture

### Current Problem Analysis

1. **Script Agent**: Attempts to initialize complex AI models that aren't available
2. **Audio Agent**: Tries to use advanced TTS engines (Coqui, Bark) that aren't installed
3. **Animation Agents**: Depend on external frameworks (Manim, Motion Canvas) that aren't configured
4. **Fallback Failures**: Even fallback mechanisms are not working properly

### Proposed Solution Architecture

```
Paper Understanding
       ↓
Simple Script Generator (working baseline)
       ↓
Basic TTS Audio Generator (system TTS + offline options)
       ↓
Simple Animation Generator (text overlays + basic visuals)
       ↓
Video Composition (already working)
```

## Components and Interfaces

### 1. Simplified Script Generator

**Purpose**: Generate working narration scripts without complex AI dependencies

**Interface**:
```python
class SimpleScriptGenerator:
    def generate_script(self, understanding: PaperUnderstanding) -> NarrationScript
    def create_scene_from_section(self, section: str, content: str) -> ScriptScene
    def calculate_scene_duration(self, text: str) -> float
```

**Implementation**:
- Extract key sections from paper understanding
- Create 3-5 scenes covering: Introduction, Methods, Results, Conclusion
- Use simple text processing (no AI dependencies)
- Calculate duration based on word count and speaking rate

### 2. Basic TTS Audio Generator

**Purpose**: Generate actual audio files using available TTS systems

**Interface**:
```python
class BasicTTSGenerator:
    def generate_audio(self, text: str, output_path: str) -> bool
    def get_available_voices(self) -> List[str]
    def validate_audio_file(self, file_path: str) -> bool
```

**Implementation Priority**:
1. **Windows SAPI** (built-in, always available)
2. **pyttsx3** (Python TTS library)
3. **gTTS** (Google TTS, requires internet)
4. **Silent audio with timing** (final fallback)

### 3. Simple Animation Generator

**Purpose**: Create basic visual content without complex animation frameworks

**Interface**:
```python
class SimpleAnimationGenerator:
    def create_text_overlay_video(self, text: str, duration: float) -> str
    def create_paper_summary_slides(self, sections: List[str]) -> List[str]
    def generate_basic_diagrams(self, content: str) -> str
```

**Implementation**:
- Use FFmpeg to create text overlay videos
- Generate simple slide-style visuals with paper content
- Create basic diagrams using PIL/matplotlib
- No external animation framework dependencies

### 4. Content Validation System

**Purpose**: Ensure generated content is real and usable

**Interface**:
```python
class ContentValidator:
    def validate_script(self, script: NarrationScript) -> ValidationResult
    def validate_audio_files(self, audio_scenes: List[AudioScene]) -> ValidationResult
    def validate_animation_files(self, animation_scenes: List[RenderedScene]) -> ValidationResult
```

## Data Models

### Enhanced Script Scene
```python
@dataclass
class ScriptScene:
    id: str
    title: str
    narration: str
    duration: float
    section_type: str  # intro, methods, results, conclusion
    key_points: List[str]
    generated_method: str  # simple, ai, fallback
```

### Audio Generation Result
```python
@dataclass
class AudioGenerationResult:
    success: bool
    file_path: Optional[str]
    duration: float
    tts_engine: str
    quality_score: float
    error_message: Optional[str]
```

### Animation Generation Result
```python
@dataclass
class AnimationGenerationResult:
    success: bool
    file_path: Optional[str]
    duration: float
    animation_type: str  # text_overlay, slides, diagram
    resolution: str
    error_message: Optional[str]
```

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Script Generation Completeness
*For any* valid paper understanding input, the script generator should produce a script with at least 3 scenes and total duration greater than 30 seconds
**Validates: Requirements 1.1, 1.2, 1.3**

### Property 2: Audio File Creation
*For any* generated script scene, the audio generator should create a valid audio file with duration matching the script scene duration (±2 seconds tolerance)
**Validates: Requirements 2.1, 2.2, 2.5**

### Property 3: Audio Content Validation
*For any* generated audio file, the file should be non-empty, have proper audio format, and contain actual audio data (not silence)
**Validates: Requirements 2.5, 5.2**

### Property 4: Animation File Creation
*For any* script scene, the animation generator should create a valid video file with duration matching the corresponding audio scene
**Validates: Requirements 3.1, 3.4**

### Property 5: Content Integration Consistency
*For any* set of generated audio and animation files, the video composition should successfully combine them into a final video with both audio and visual tracks
**Validates: Requirements 4.1, 4.2**

### Property 6: Fallback Reliability
*For any* content generation failure, the system should produce fallback content rather than empty files or complete failure
**Validates: Requirements 6.1, 6.2, 6.3, 6.4**

### Property 7: File Existence Validation
*For all* generated content files (script, audio, animation), the files should exist on disk and be readable
**Validates: Requirements 5.1, 5.2, 5.3**

### Property 8: Duration Consistency
*For any* complete content generation, the total duration of audio files should match the total duration of animation files (±5 seconds tolerance)
**Validates: Requirements 4.2, 5.2, 5.3**

## Error Handling

### Error Categories
1. **Dependency Missing**: Required TTS or animation tools not available
2. **Content Generation Failed**: Specific content type failed to generate
3. **File System Error**: Cannot write or read generated files
4. **Validation Failed**: Generated content doesn't meet quality standards

### Recovery Strategies
1. **Graceful Degradation**: Use simpler methods when advanced ones fail
2. **Multiple Fallbacks**: Chain of fallback options for each content type
3. **Partial Success**: Accept partial content generation rather than complete failure
4. **Clear Error Reporting**: Detailed logs about what failed and what fallbacks were used

## Testing Strategy

### Unit Tests
- Test each content generator independently
- Verify file creation and validation
- Test fallback mechanisms
- Validate error handling

### Property Tests
- Generate random paper content and verify consistent output
- Test duration calculations across different content lengths
- Verify file format consistency
- Test fallback chains with various failure scenarios

### Integration Tests
- Test complete pipeline from paper to final video
- Verify content synchronization
- Test with real paper examples
- Validate final video quality

### Performance Tests
- Measure content generation time for typical papers
- Test with various paper lengths and complexities
- Verify memory usage during generation
- Test concurrent content generation

## Implementation Plan

### Phase 1: Basic Content Generation (Priority 1)
1. Implement SimpleScriptGenerator with paper section extraction
2. Implement BasicTTSGenerator with Windows SAPI and pyttsx3
3. Implement SimpleAnimationGenerator with FFmpeg text overlays
4. Add comprehensive content validation

### Phase 2: Enhanced Fallbacks (Priority 2)
1. Add multiple TTS engine support
2. Implement slide-style animation generation
3. Add content quality scoring
4. Improve error reporting and logging

### Phase 3: Quality Improvements (Priority 3)
1. Add voice selection options
2. Implement basic diagram generation
3. Add content enhancement features
4. Optimize generation performance

The goal is to have a working system that produces real content files first, then enhance quality and features incrementally.