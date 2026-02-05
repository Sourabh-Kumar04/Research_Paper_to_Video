# Design: Massive Text Size Fix

## Overview
Redesign Manim text rendering to use MASSIVE font sizes (72/56/48px) and prevent excessive scaling that makes text unreadable.

## Root Cause Analysis
Current text appears tiny because:
1. Font sizes (56/40/36px) are scaled down by `scale_to_fit_width(12)` and `scale_to_fit_height(4)`
2. Long text gets scaled to 20-30% of original size
3. Paragraph wrapping isn't working effectively
4. Screen area isn't being fully utilized

## Solution

### 1. Increase Base Font Sizes
- Title: 72px (was 56px)
- Subtitle: 56px (was 40px)
- Content: 48px (was 36px)

### 2. Remove Aggressive Scaling
- Remove `scale_to_fit_width()` for content text
- Let Paragraph handle wrapping naturally
- Only scale if text is >150% of screen width

### 3. Maximize Screen Usage
- Reduce top/bottom margins
- Use full width (13 units instead of 12)
- Increase content area height to 5 units

### 4. Better Text Wrapping
- Set explicit width for Paragraph (width=12)
- Use smaller line_spacing (1.2 instead of 1.5)
- Allow more vertical space

## Implementation

### Manim Code Template
```python
# MASSIVE font sizes
title_font_size = 72
subtitle_font_size = 56  
content_font_size = 48

# Title - minimal scaling
title = Text(text, font_size=72, color=BLUE, weight=BOLD)
title.to_edge(UP, buff=0.3)  # Less margin
# Only scale if REALLY necessary
if title.width > 14:
    title.scale_to_fit_width(14)

# Content - use Paragraph with explicit width
content = Paragraph(
    text,
    font_size=48,
    color=WHITE,
    line_spacing=1.2,
    alignment="left",
    width=12  # Explicit width for wrapping
)
# NO scaling - let Paragraph wrap naturally
```

## Testing Strategy
Generate test video and verify:
- Text fills most of screen
- Font sizes remain large (>40px after any scaling)
- Content is easily readable
- Multi-line wrapping works correctly
