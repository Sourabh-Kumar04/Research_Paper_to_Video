# Design Document

## Overview

This design fixes the production video generator's fallback script to create comprehensive 20+ minute educational videos instead of short technical videos. The current implementation has a bug where it calls an old scene creation method that only generates 6-7 short scenes, resulting in 5-minute videos instead of the intended 20+ minute comprehensive educational content.

## Architecture

### Current Problem
The `_create_fallback_script()` method in `ProductionVideoGenerator` is not using the comprehensive scene generation logic that was implemented. Instead, it's falling back to the old `create_scenes_from_paper()` method which creates short technical scenes.

### Solution Architecture
1. **Remove Old Method Dependency**: Eliminate the call to `create_scenes_from_paper()` 
2. **Use Comprehensive Logic**: Ensure `_create_fallback_script()` uses the comprehensive scene generation
3. **Consistent Scene Structure**: Apply the same comprehensive approach to all paper types
4. **Duration Validation**: Add validation to ensure minimum duration requirements are met

## Components and Interfaces

### ProductionVideoGenerator Class
- **Method**: `_create_fallback_script()` - Main fallback script generation
- **Method**: `_create_fallback_analysis()` - Enhanced paper analysis for better scene generation
- **Helper**: `calculate_scene_duration()` - Duration calculation based on narration word count

### Scene Structure
```python
{
    "id": "scene_identifier",
    "title": "Descriptive Scene Title",
    "narration": "300-600 word comprehensive explanation...",
    "visual_description": "Structured format with tables and diagrams",
    "duration": 120.0,  # Calculated from narration length
    "key_concepts": ["concept1", "concept2"],
    "formulas": ["formula explanations"],
    "diagrams": ["diagram descriptions"],
    "analogies": ["real-world analogies"],
    "transitions": ["connection to next scene"]
}
```

## Data Models

### Comprehensive Scene Template
- **Minimum Narration**: 300 words (results in ~150 second scene)
- **Maximum Narration**: 600 words (results in ~300 second scene)
- **Reading Pace**: 120 words per minute
- **Visual Time**: 1.5x multiplier for pauses and visual processing
- **Duration Formula**: `max(60, min(300, (word_count / 120) * 60 * 1.5))`

### Scene Categories for All Papers
1. **Opening & Big Picture** (180s) - Why research matters
2. **Historical Context** (195s) - What came before
3. **Essential Foundations** (210s) - Building knowledge from scratch
4. **Problem Definition** (225s) - What needed solving
5. **Intuitive Solution** (240s) - Core insight explained simply
6. **Foundation Component** (255s) - First building block
7. **Processing Engine** (270s) - Second building block
8. **Mathematical Framework** (285s) - Making it precise
9. **Technical Implementation** (300s) - Theory to practice
10. **Performance Analysis** (315s) - Experimental validation
11. **Real-World Impact** (330s) - Modern applications
12. **Future Directions** (345s) - Ongoing research
13. **Complete Summary** (360s) - Connecting all pieces

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system-essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

### Property 1: Minimum Duration Guarantee
*For any* paper input, the fallback script should generate a video with total duration of at least 900 seconds (15 minutes)
**Validates: Requirements 1.1, 4.1**

### Property 2: Comprehensive Scene Count
*For any* paper input, the fallback script should generate at least 10 comprehensive scenes
**Validates: Requirements 1.2**

### Property 3: Scene Duration Calculation
*For any* scene with narration, the duration should be calculated as max(60, min(300, (word_count / 120) * 60 * 1.5))
**Validates: Requirements 1.3, 4.4, 4.5**

### Property 4: Educational Content Structure
*For any* generated scene, it should include comprehensive narration (300+ words), structured visual descriptions, and beginner-friendly explanations
**Validates: Requirements 3.1, 3.2, 3.4**

### Property 5: No Old Method Usage
*For any* fallback script execution, it should not call the create_scenes_from_paper method
**Validates: Requirements 2.1**

## Error Handling

### Insufficient Duration Handling
- If total duration < 900 seconds, add additional comprehensive scenes
- Limit maximum scenes to 20 to prevent excessive length
- Each additional scene should be substantial (150+ seconds)

### Scene Generation Failures
- Ensure all scenes have required fields (id, title, narration, duration)
- Provide default values for missing optional fields
- Validate narration length meets minimum requirements

## Testing Strategy

### Unit Tests
- Test scene duration calculation with various narration lengths
- Test comprehensive scene generation for different paper types
- Test duration validation and additional scene generation
- Test that old method is not called

### Property Tests
- **Property 1**: Generate random paper titles and verify minimum duration
- **Property 2**: Generate random inputs and verify scene count ≥ 10
- **Property 3**: Generate random narrations and verify duration calculation
- **Property 4**: Generate random scenes and verify comprehensive structure
- **Property 5**: Monitor method calls to ensure old method not used

Each property test should run minimum 100 iterations and be tagged with:
**Feature: comprehensive-video-fallback-fix, Property {number}: {property_text}**