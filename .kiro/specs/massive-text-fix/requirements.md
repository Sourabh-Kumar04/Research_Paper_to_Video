# Requirements: Massive Text Size Fix

## Introduction
Fix video text to be MASSIVE and fill the entire screen area, making it easily readable.

## Glossary
- **Manim**: Animation engine for video generation
- **Paragraph**: Multi-line text object
- **Screen Units**: Manim coordinate system (typically -7 to +7 for width)

## Requirements

### Requirement 1: Massive Text Sizes

**User Story:** As a viewer, I want text to fill the entire screen, so that I can easily read all content.

#### Acceptance Criteria
1. THE System SHALL use minimum 72 pixels for title text
2. THE System SHALL use minimum 56 pixels for subtitle text
3. THE System SHALL use minimum 48 pixels for content text
4. THE System SHALL NOT scale text below these minimum sizes
5. THE System SHALL allow text to fill maximum available screen area

### Requirement 2: No Excessive Scaling

**User Story:** As a viewer, I want text to remain large, so that scaling doesn't make it unreadable.

#### Acceptance Criteria
1. THE System SHALL NOT scale text below 80% of original size
2. WHEN text is too wide, THE System SHALL wrap to multiple lines instead of scaling
3. THE System SHALL prioritize readability over fitting all text on one line
4. THE System SHALL use Paragraph for automatic line wrapping
5. THE System SHALL maintain minimum font sizes after scaling
