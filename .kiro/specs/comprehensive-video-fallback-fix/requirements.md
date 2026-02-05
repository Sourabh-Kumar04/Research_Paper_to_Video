# Requirements Document

## Introduction

Fix the production video generator fallback script to create comprehensive 20+ minute educational videos instead of short 5-minute technical videos.

## Glossary

- **Production_Video_Generator**: The main video generation system that creates educational videos from research papers
- **Fallback_Script**: The backup script generation system used when Gemini API is unavailable or fails
- **Comprehensive_Scenes**: Detailed educational scenes with 300-600 word narrations designed for complete beginners
- **Scene_Duration**: The length of each video scene, calculated based on narration word count and visual complexity

## Requirements

### Requirement 1: Fix Fallback Script Logic

**User Story:** As a user generating videos when Gemini is unavailable, I want comprehensive 20+ minute educational videos, so that I get the same quality experience regardless of API availability.

#### Acceptance Criteria

1. WHEN the fallback script is used, THE Production_Video_Generator SHALL create videos with minimum 15 minutes duration
2. WHEN generating scenes, THE Production_Video_Generator SHALL create minimum 10 comprehensive scenes
3. WHEN calculating scene duration, THE Production_Video_Generator SHALL use narration word count with 120 words/minute reading pace
4. THE Production_Video_Generator SHALL target complete beginners with zero background knowledge
5. THE Production_Video_Generator SHALL use world-class educator teaching style with analogies and examples

### Requirement 2: Remove Old Scene Creation Method

**User Story:** As a developer maintaining the system, I want the fallback script to use only the comprehensive scene generation logic, so that there's no confusion between old and new implementations.

#### Acceptance Criteria

1. THE Production_Video_Generator SHALL NOT call the old create_scenes_from_paper method
2. THE Production_Video_Generator SHALL use only the comprehensive scene generation logic in _create_fallback_script
3. WHEN any paper type is processed, THE Production_Video_Generator SHALL create comprehensive educational content
4. THE Production_Video_Generator SHALL ensure consistent scene structure across all paper types

### Requirement 3: Comprehensive Scene Structure

**User Story:** As a complete beginner learning from videos, I want detailed explanations with visual descriptions, so that I can understand complex research papers from scratch.

#### Acceptance Criteria

1. WHEN creating scenes, THE Production_Video_Generator SHALL include 300-600 word narrations per scene
2. WHEN generating visual descriptions, THE Production_Video_Generator SHALL use structured format with tables, diagrams, and formulas
3. THE Production_Video_Generator SHALL include progressive concept building from basic to advanced
4. THE Production_Video_Generator SHALL use analogies and real-world examples in every scene
5. THE Production_Video_Generator SHALL define all technical terms when first introduced

### Requirement 4: Duration Validation

**User Story:** As a user, I want videos that meet the promised duration, so that I get comprehensive coverage of the research topic.

#### Acceptance Criteria

1. WHEN the fallback script completes, THE Production_Video_Generator SHALL validate total duration is minimum 900 seconds
2. IF total duration is less than 900 seconds, THE Production_Video_Generator SHALL add additional comprehensive scenes
3. THE Production_Video_Generator SHALL limit maximum scenes to 20 to prevent excessive length
4. WHEN calculating scene duration, THE Production_Video_Generator SHALL ensure minimum 60 seconds per scene
5. THE Production_Video_Generator SHALL ensure maximum 300 seconds per scene to maintain engagement