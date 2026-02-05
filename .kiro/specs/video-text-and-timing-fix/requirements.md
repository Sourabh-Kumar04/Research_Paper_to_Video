# Requirements Document: Video Text Size and Timing Fix

## Introduction

Fix the video generation system to produce videos with large, readable text and smooth transitions without black screens.

## Glossary

- **Manim**: Animation engine used to generate video scenes
- **Paragraph**: Manim text object that supports multi-line wrapping
- **Scene Transition**: The change from one video scene to another
- **Content Text**: The main explanatory text in each scene (narration)

## Requirements

### Requirement 1: Large Readable Text

**User Story:** As a viewer, I want all text in the video to be large and readable, so that I can easily read the content without straining.

#### Acceptance Criteria

1. THE System SHALL render title text at minimum 56 pixels font size
2. THE System SHALL render subtitle text at minimum 40 pixels font size  
3. THE System SHALL render content text at minimum 36 pixels font size
4. THE System SHALL use Paragraph objects for multi-line text wrapping
5. THE System SHALL scale text to fit screen width while maintaining minimum font sizes

### Requirement 2: Smooth Scene Transitions

**User Story:** As a viewer, I want smooth transitions between scenes, so that I don't see black screens or delays.

#### Acceptance Criteria

1. WHEN transitioning between scenes, THE System SHALL NOT display black screens
2. THE System SHALL complete fade-out animations in maximum 0.3 seconds
3. THE System SHALL start next scene immediately after previous scene fade-out
4. THE System SHALL NOT add wait times between scene transitions
5. THE System SHALL maintain continuous video playback throughout

### Requirement 3: Verified Download Functionality

**User Story:** As a user, I want to download generated videos, so that I can save and share them.

#### Acceptance Criteria

1. WHEN a video generation completes, THE System SHALL make the video available for download
2. WHEN user clicks download, THE System SHALL serve the correct video file
3. THE System SHALL set correct content-type headers for video files
4. THE System SHALL handle download errors gracefully
5. THE Frontend SHALL trigger browser download with correct filename

### Requirement 4: Working UI Integration

**User Story:** As a user, I want the UI to work correctly, so that I can generate and download videos easily.

#### Acceptance Criteria

1. THE Frontend SHALL display job status correctly
2. THE Frontend SHALL show download button when video is ready
3. THE Frontend SHALL handle API errors gracefully
4. THE Frontend SHALL provide user feedback during video generation
5. THE System SHALL maintain consistent state between frontend and backend
