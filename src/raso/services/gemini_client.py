"""
Google Gemini LLM Client for RASO Platform
Provides integration with Google's Gemini models for script generation, Manim code generation, and content analysis.
"""

import os
import asyncio
import logging
from typing import Dict, List, Optional, Any
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

logger = logging.getLogger(__name__)

class GeminiClient:
    """Google Gemini LLM client for RASO platform."""
    
    def __init__(self):
        """Initialize Gemini client with API key and configuration."""
        self.api_key = os.getenv('RASO_GOOGLE_API_KEY')
        if not self.api_key:
            raise ValueError("RASO_GOOGLE_API_KEY environment variable is required")
        
        # Clean up API key (remove quotes if present)
        self.api_key = self.api_key.strip('"\'')
        
        # Configure Gemini
        genai.configure(api_key=self.api_key)
        
        # Model configurations
        self.default_model = os.getenv('RASO_GOOGLE_MODEL', 'gemini-2.0-flash-exp')
        self.script_model = os.getenv('RASO_SCRIPT_LLM_MODEL', 'gemini-2.0-flash-exp')
        self.manim_model = os.getenv('RASO_MANIM_LLM_MODEL', 'gemini-2.0-flash-exp')
        self.analysis_model = os.getenv('RASO_ANALYSIS_LLM_MODEL', 'gemini-2.0-flash-exp')
        
        # Generation configuration
        self.generation_config = {
            'temperature': float(os.getenv('RASO_GOOGLE_TEMPERATURE', '0.7')),
            'max_output_tokens': int(os.getenv('RASO_GOOGLE_MAX_TOKENS', '8192')),
            'top_p': 0.8,
            'top_k': 40
        }
        
        # Safety settings - Allow creative content for educational videos
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info(f"Initialized Gemini client with model: {self.default_model}")
        logger.info(f"API key configured: {self.api_key[:10]}...")
    
    async def generate_script(self, paper_title: str, paper_content: str, paper_type: str = "title") -> Dict[str, Any]:
        """Generate video script from research paper using Gemini - ALWAYS COMPREHENSIVE FORMAT."""
        try:
            model = genai.GenerativeModel(
                model_name=self.script_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_script_prompt(paper_title, paper_content, paper_type)
            
            logger.info(f"Generating comprehensive script for paper: {paper_title}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                script_data = self._parse_script_response(response.text)
                
                # FORCE COMPREHENSIVE FORMAT: Check if script is too short
                scenes = script_data.get('scenes', [])
                total_duration = sum(scene.get('duration', 0) for scene in scenes)
                
                logger.info(f"Gemini generated script: {len(scenes)} scenes, {total_duration:.1f}s")
                
                # If Gemini generated a short script (< 15 minutes), use comprehensive fallback instead
                if total_duration < 900 or len(scenes) < 8:
                    logger.warning(f"Gemini script too short ({total_duration:.1f}s, {len(scenes)} scenes), using comprehensive fallback")
                    return self._create_fallback_script(paper_title, paper_content)
                
                logger.info(f"Using Gemini comprehensive script: {len(scenes)} scenes, {total_duration:.1f}s")
                return script_data
            else:
                logger.error("Empty response from Gemini for script generation")
                return self._create_fallback_script(paper_title, paper_content)
                
        except Exception as e:
            logger.error(f"Error generating script with Gemini: {e}")
            return self._create_fallback_script(paper_title, paper_content)
    
    async def generate_manim_code(self, scene_title: str, scene_description: str, scene_duration: float) -> str:
        """Generate Manim animation code using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.manim_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_manim_prompt(scene_title, scene_description, scene_duration)
            
            logger.info(f"Generating Manim code for scene: {scene_title}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                manim_code = self._extract_manim_code(response.text)
                logger.info(f"Generated Manim code ({len(manim_code)} characters)")
                return manim_code
            else:
                logger.error("Empty response from Gemini for Manim code generation")
                raise Exception("Gemini AI service failed - no fallback available")
                
        except Exception as e:
            logger.error(f"Error generating Manim code with Gemini: {e}")
            raise Exception("Gemini AI service failed - no fallback available")
    
    async def analyze_paper_content(self, paper_input: str, paper_type: str) -> Dict[str, Any]:
        """Analyze research paper content using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_analysis_prompt(paper_input, paper_type)
            
            logger.info(f"Analyzing paper content: {paper_input[:100]}...")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                analysis = self._parse_analysis_response(response.text)
                logger.info("Paper analysis completed successfully")
                return analysis
            else:
                logger.error("Empty response from Gemini for paper analysis")
                return self._create_fallback_analysis(paper_input)
                
        except Exception as e:
            logger.error(f"Error analyzing paper with Gemini: {e}")
            return self._create_fallback_analysis(paper_input)
    
    def _create_script_prompt(self, paper_title: str, paper_content: str, paper_type: str) -> str:
        """Create prompt for script generation."""
        return f"""
You are a SENIOR AI ENGINEER and EXPERT EDUCATOR creating an in-depth educational video for YouTube/classroom teaching.

Paper Title: {paper_title}
Paper Type: {paper_type}
Content: {paper_content}

MANDATORY: Create a COMPREHENSIVE, DETAILED video script with MINIMUM 15-20 scenes and MINIMUM 20-30 minutes duration.

CRITICAL DURATION REQUIREMENTS (NON-NEGOTIABLE):
- MINIMUM total video duration: 1200 seconds (20 minutes) - SHORTER SCRIPTS WILL BE REJECTED
- TARGET total video duration: 1500-1800 seconds (25-30 minutes)
- MINIMUM scene count: 15 scenes - FEWER SCENES WILL BE REJECTED
- Each scene MINIMUM duration: 60 seconds
- Each scene MAXIMUM duration: 180 seconds
- Scene duration MUST match narration length - calculate as: max(60, min(180, word_count * 0.5))
- For 300-600 word narrations, this gives 150-300 second scenes (2.5-5 minutes each)
- ENSURE scene duration allows full narration reading at comfortable pace (120 words/minute)

TEACHING STYLE:
- ASSUME ZERO BACKGROUND KNOWLEDGE - build from absolute basics
- Start with the big picture problem and why it matters
- Break down complex concepts into foundational building blocks
- Define ALL technical terms and jargon when first introduced
- Use analogies and real-world examples to make abstract concepts concrete
- Present methodology in simplified, logical steps
- Use logical narrative flow that answers "WHY" before "HOW"
- Include transition statements between sections
- Repeat key concepts in different ways
- Show concrete examples before generalizations
- Break complex equations into conceptual meaning first, math second
- Add pauses at key moments for comprehension
- End with summary that connects everything together

VIDEO STRUCTURE (15-20 scenes for MINIMUM 15-25 minute video):
1. Opening & Big Picture (90-120s) - Why this paper matters, real-world impact
2. Historical Context (90-120s) - What came before? What wasn't working?
3. Prerequisites & Foundations (120-150s) - Essential background knowledge from scratch
4. Problem Definition (120-150s) - Precise problem statement with real examples
5. Intuitive Overview (120-150s) - High-level solution approach with analogies
6. Core Concept 1 (120-150s) - First major building block explained simply
7. Core Concept 2 (120-150s) - Second major building block with examples
8. Mathematical Foundation (150-180s) - Key formulas with intuitive meaning first
9. Technical Details 1 (120-150s) - How it actually works (simplified)
10. Technical Details 2 (120-150s) - Implementation considerations
11. Architecture/Method (150-180s) - Complete system overview
12. Key Innovation (120-150s) - What makes this special/different
13. Step-by-Step Process (150-180s) - Detailed walkthrough with examples
14. Results & Analysis (120-150s) - What did they achieve? Why does it work?
15. Comparison with Previous Methods (120-150s) - Before vs After analysis
16. Real-World Applications (90-120s) - Where is this used today?
17. Practical Implementation (90-120s) - How to actually use this
18. Limitations & Challenges (90-120s) - What doesn't work well?
19. Future Directions (90-120s) - Where is this going?
20. Complete Summary (120-150s) - Connecting all concepts together

For EACH scene, provide:
- Scene ID (short identifier)
- Title (descriptive, engaging)
- Duration (CALCULATED from narration length: max(60, min(180, word_count * 0.5)) seconds)
- Narration (COMPREHENSIVE explanation, 300-800 words)
  * Start from absolute basics - assume zero knowledge
  * Define every technical term when first used
  * Use analogies and real-world examples extensively
  * Explain conceptual meaning before showing math
  * Include "imagine this..." or "think of it like..." explanations
  * Add transition statements to connect ideas
  * Repeat key concepts in different ways
  * ENSURE narration length matches the calculated scene duration (120 words/minute reading pace)
- Visual Description (STRUCTURED FORMAT - clearly readable)
  * VISUAL LAYOUT:
    ┌─────────────────────────────────────────┐
    │ 🎬 SCENE: [Descriptive Title]          │
    │ ⏱️ DURATION: [X] seconds               │
    │ 📊 COMPLEXITY: [Beginner/Intermediate] │
    └─────────────────────────────────────────┘
    
    📋 MAIN CONCEPTS TO VISUALIZE:
    ┌─ PRIMARY CONCEPTS ──────────────────────┐
    │ • Concept 1: [Clear description]        │
    │ • Concept 2: [Clear description]        │
    │ • Concept 3: [Clear description]        │
    └─────────────────────────────────────────┘
    
    🔢 MATHEMATICAL FORMULAS (if applicable):
    ┌─ FORMULA DISPLAY ───────────────────────┐
    │ Formula 1: [Mathematical expression]    │
    │ ├─ Meaning: [Conceptual explanation]    │
    │ ├─ Variables: [What each symbol means]  │
    │ └─ Intuition: [Why this formula works] │
    │                                         │
    │ Formula 2: [Mathematical expression]    │
    │ ├─ Meaning: [Conceptual explanation]    │
    │ └─ Connection: [How it relates to F1]   │
    └─────────────────────────────────────────┘
    
    📈 VISUAL ELEMENTS TO CREATE:
    ┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
    │ Step 1: [Initial concept visualization] │
    │ Step 2: [Building on step 1]           │
    │ Step 3: [Adding complexity]            │
    │ Step 4: [Complete understanding]       │
    └─────────────────────────────────────────┘
    
    🎨 COLOR CODING SCHEME:
    ┌─ VISUAL ORGANIZATION ───────────────────┐
    │ 🔵 Blue: [Primary concepts/main ideas]  │
    │ 🟢 Green: [Supporting details/examples] │
    │ 🟠 Orange: [Key innovations/highlights] │
    │ 🔴 Red: [Warnings/limitations/errors]   │
    │ 🟣 Purple: [Mathematical elements]      │
    └─────────────────────────────────────────┘
    
    📊 COMPARISON TABLES (when applicable):
    ┌─ BEFORE vs AFTER ───────────────────────┐
    │ Aspect      │ Before    │ After        │
    │ ─────────── │ ───────── │ ──────────── │
    │ Speed       │ Slow      │ Fast         │
    │ Accuracy    │ Low       │ High         │
    │ Complexity  │ High      │ Manageable   │
    └─────────────────────────────────────────┘

NARRATION REQUIREMENTS:
- 300-800 words per scene (comprehensive, detailed explanations)
- Conversational, engaging tone for complete beginners
- Define every technical term immediately when introduced
- Use "imagine", "think of it like", "for example" frequently
- Explain mathematical intuition before showing any formulas
- Give multiple concrete examples for each concept
- Connect to things everyone already knows
- Include transition phrases between ideas
- Add natural pause points for comprehension
- ENSURE narration length requires the full scene duration to read properly

VISUAL REQUIREMENTS:
- Opening title slide with paper name and context
- Show KEY FORMULAS with conceptual meaning explained first
- Draw PROGRESSIVE DIAGRAMS that build step-by-step
- Use COLOR CODING to distinguish different concepts
- Create ANIMATIONS showing processes and transformations
- Display VISUAL METAPHORS for abstract ideas
- Show COMPARISON VISUALS (before/after, old vs new)
- Include GRAPHS AND CHARTS with clear labels and annotations
- Use TEXT HIGHLIGHTS to emphasize key points
- Clean, readable fonts large enough for viewing
- Consistent color scheme throughout
- Clear visual hierarchy with strategic focus

Format as JSON:
{{
  "title": "{paper_title}",
  "total_duration": 1200-1800,
  "target_audience": "complete beginners with zero background",
  "teaching_style": "world-class educator explaining from absolute scratch",
  "content_planning": "big picture first, build foundations, define all terms, use analogies",
  "visual_approach": "progressive diagrams, color coding, step-by-step animations",
  "scenes": [
    {{
      "id": "opening",
      "title": "The Big Picture: Why This Research Matters",
      "duration": 75.0,
      "narration": "Comprehensive 300-600 word explanation starting from absolute basics, defining all terms, using analogies...",
      "visual_description": "Opening title slide with paper context, progressive diagrams, color-coded concepts, step-by-step animations",
      "key_concepts": ["concept1", "concept2"],
      "formulas": ["formula1 with conceptual explanation"],
      "diagrams": ["progressive diagram description"],
      "analogies": ["real-world analogy used"],
      "transitions": ["how this connects to next section"]
    }}
  ]
}}

Make it feel like a MASTERCLASS from a world-renowned educator who can explain the most complex ideas to complete beginners.
"""
    
    def _create_manim_prompt(self, scene_title: str, scene_description: str, scene_duration: float) -> str:
        """Create prompt for Manim code generation."""
        return f"""
You are an expert Manim animator specializing in educational content for complete beginners. Generate Python code using Manim to create a comprehensive educational animation that builds understanding from scratch.

Scene: {scene_title}
Description: {scene_description}
Duration: {scene_duration} seconds

EDUCATIONAL VISUAL REQUIREMENTS:
- ASSUME ZERO BACKGROUND KNOWLEDGE - make everything crystal clear
- Use PROGRESSIVE DIAGRAMS that build step-by-step rather than appearing all at once
- Implement COLOR CODING to distinguish different concepts or components
- Create ANIMATIONS that show processes or transformations step-by-step
- Include VISUAL METAPHORS for abstract ideas
- Design COMPARISON VISUALS (before/after, with/without the proposed method)
- Add TEXT HIGHLIGHTS to emphasize key points
- Use clean, readable fonts large enough for viewing (minimum 32px)
- Maintain consistent color scheme throughout
- Create clear visual hierarchy with strategic focus (highlighting, zooming)

TIMING REQUIREMENTS:
- Use the FULL {scene_duration} seconds effectively (minimum 60 seconds per scene)
- Allow EXTENDED reading time (30-60 seconds based on content complexity)
- Add LONG pauses at key moments for comprehension (10-15 seconds)
- NEVER rush through content - viewers need time to absorb complex ideas
- Calculate reading time: max(30, min(60, content_length / 120)) for 120 words/minute pace
- ENSURE scene duration matches the narration length completely
- If narration is long (400+ words), extend scene duration to match (minimum 120s, maximum 300s)
- Use remaining time for visual emphasis, pauses, and concept reinforcement

Create a Manim Scene class that creates comprehensive educational content with:

VISUAL ELEMENTS:
- Opening title slide with paper name and context (if first scene)
- Progressive diagrams that build up step-by-step
- Color-coded elements to distinguish concepts
- Step-by-step animations showing processes
- Visual metaphors for abstract concepts
- Comparison charts and before/after visuals
- Mathematical formulas with conceptual explanations
- Clear labels and annotations on all elements
- Text highlights for key terminology
- Professional color scheme (blues, whites, greens, oranges for highlights)

ANIMATION TECHNIQUES:
- Use Write() for text that should appear gradually
- Use Create() for diagrams and shapes that build progressively
- Use Transform() for concept transitions and comparisons
- Use FadeIn/FadeOut for smooth transitions between ideas
- Use AnimationGroup for coordinated multi-element animations
- Use Indicate() or Circumscribe() to highlight key points
- Use progressive revelation - show one concept, then build on it
- Time animations to fit the {scene_duration} second duration with proper pacing

EDUCATIONAL BEST PRACTICES:
- Start with a clear, descriptive title
- Build concepts progressively from simple to complex
- Use visual metaphors and analogies when appropriate
- Highlight key points with color, movement, or emphasis
- Show concrete examples before abstract generalizations
- Include visual transitions between related concepts
- End with a summary or connection to the next topic
- Make every element serve the educational narrative

TECHNICAL REQUIREMENTS:
- Class name should be descriptive (e.g., OpeningScene, FoundationsScene, etc.)
- Use Manim Community Edition syntax
- Include proper imports
- Add brief comments explaining complex animations
- Ensure all text is readable (minimum font size 32px for main content, 28px for details)
- **CRITICAL**: Scale all text to fit screen boundaries
- Use self.wait() appropriately for pacing and comprehension
- Create smooth, professional animations

TEXT FITTING AND SIZING:
```python
title = Text("Your Title", font_size=36)
if title.width > 12:
    title.scale_to_fit_width(12)
```

PROGRESSIVE DIAGRAM EXAMPLE:
```python
# Build diagram step by step
step1 = Rectangle(color=BLUE)
self.play(Create(step1))
self.wait(1)

step2 = Circle(color=GREEN).next_to(step1, RIGHT)
self.play(Create(step2))
self.wait(1)

# Connect them
arrow = Arrow(step1.get_right(), step2.get_left())
self.play(Create(arrow))
```

Return ONLY the complete Python code:

```python
from manim import *

class YourSceneClass(Scene):
    def construct(self):
        # Create comprehensive educational animation here
        # Build understanding progressively from basics
        # Use color coding and step-by-step reveals
        # Include visual metaphors and comparisons
        # ENSURE ALL TEXT FITS ON SCREEN
        # Use the full {scene_duration} seconds effectively
        pass
```

Make it educational, visually compelling, and perfectly paced for complete beginners learning complex concepts.
**MOST IMPORTANT: Build understanding progressively and ensure all visual elements serve the educational narrative!**
"""
    
    def _create_analysis_prompt(self, paper_input: str, paper_type: str) -> str:
        """Create prompt for paper analysis."""
        return f"""
You are an expert research paper analyzer. Analyze the following research paper and extract key information.

Input Type: {paper_type}
Content: {paper_input}

Extract and provide:
1. Paper title (if available)
2. Main research area/field
3. Key contributions
4. Methodology overview
5. Significance and impact
6. Target audience level (beginner/intermediate/advanced)
7. Suggested video structure
8. Key concepts to visualize

Format as JSON:
{{
  "title": "Paper title",
  "field": "Research area",
  "contributions": ["Key contribution 1", "Key contribution 2"],
  "methodology": "Brief methodology description",
  "significance": "Why this paper matters",
  "audience_level": "beginner|intermediate|advanced",
  "video_structure": ["Section 1", "Section 2", "Section 3"],
  "key_concepts": ["Concept 1", "Concept 2"],
  "estimated_duration": 60
}}

Provide accurate, educational analysis suitable for video creation.
"""
    
    def _parse_script_response(self, response_text: str) -> Dict[str, Any]:
        """Parse script generation response."""
        try:
            import json
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing script response: {e}")
            return self._create_fallback_script("Unknown Paper", response_text[:500])
    
    def _extract_manim_code(self, response_text: str) -> str:
        """Extract Manim code from response."""
        try:
            # Look for code blocks
            if '```python' in response_text:
                start_idx = response_text.find('```python') + 9
                end_idx = response_text.find('```', start_idx)
                if end_idx > start_idx:
                    return response_text[start_idx:end_idx].strip()
            
            # Look for class definitions
            if 'class ' in response_text and 'Scene' in response_text:
                lines = response_text.split('\n')
                code_lines = []
                in_code = False
                
                for line in lines:
                    if 'from manim import' in line or 'import manim' in line:
                        in_code = True
                    if in_code:
                        code_lines.append(line)
                
                if code_lines:
                    return '\n'.join(code_lines)
            
            # Fallback: return the whole response if it looks like code
            if 'def construct' in response_text:
                return response_text.strip()
            
            raise ValueError("No valid Manim code found in response")
            
        except Exception as e:
            logger.error(f"Error extracting Manim code: {e}")
            raise Exception("Gemini AI service failed - no fallback available")
    
    def _parse_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse analysis response."""
        try:
            import json
            # Extract JSON from response
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing analysis response: {e}")
            return self._create_fallback_analysis("Unknown content")
    
    def _create_fallback_script(self, paper_title: str, paper_content: str) -> Dict[str, Any]:
        """Create fallback script when Gemini fails - comprehensive 20+ minute educational format."""
        
        # Helper function to calculate scene duration based on narration word count
        def calculate_scene_duration(narration_text: str) -> float:
            word_count = len(narration_text.split())
            # 120 words per minute reading pace + time for visuals and pauses
            base_duration = (word_count / 120) * 60  # Convert to seconds
            # Ensure minimum 60s, maximum 300s (5 minutes)
            return max(60.0, min(300.0, base_duration * 1.5))  # 1.5x for pauses and visuals
        
        # Create comprehensive scenes with proper duration calculation
        scenes = [
            {
                "id": "opening",
                "title": "The Big Picture: Why This Research Matters",
                "narration": f"Welcome to this comprehensive masterclass on '{paper_title}'. Imagine you're completely new to this field - that's exactly where we'll start. This research paper addresses a fundamental problem that affects millions of people and countless applications in our digital world. Think of it like this: before this work existed, researchers and engineers were trying to solve complex problems with tools that were like using a hammer when they needed a precision screwdriver. This paper introduced that precision screwdriver. We're going to explore not just what this research accomplished, but why it was needed, how it works from the ground up, and why it has transformed entire fields of study. By the end of this journey, you'll understand not only the technical details but also the broader implications and why this work has become so influential. We'll build your understanding step by step, defining every technical term, using real-world analogies, and connecting each concept to things you already know. No background knowledge is assumed - we'll start from the very beginning and build a complete understanding together. Think of this as your personal guide through one of the most important research breakthroughs in recent years, explained in a way that makes complex ideas accessible and engaging.",
                "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Opening & Big Picture        │
│ ⏱️ DURATION: 120 seconds               │
│ 📊 COMPLEXITY: Beginner                │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Research significance and impact      │
│ • Problem landscape before this work    │
│ • Learning journey roadmap             │
│ • Why this matters to everyone         │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Title slide with paper context │
│ Step 2: Problem landscape visualization │
│ Step 3: Impact areas and applications   │
│ Step 4: Learning roadmap preview        │
└─────────────────────────────────────────┘

🎨 COLOR CODING SCHEME:
┌─ VISUAL ORGANIZATION ───────────────────┐
│ 🔵 Blue: Main research topic           │
│ 🟢 Green: Positive impacts/benefits     │
│ 🟠 Orange: Key innovations              │
│ 🟣 Purple: Learning pathway             │
└─────────────────────────────────────────┘
""",
                "key_concepts": ["Research significance", "Problem context", "Learning journey"],
                "formulas": [],
                "diagrams": ["Problem landscape overview", "Learning roadmap"],
                "analogies": ["Hammer vs precision screwdriver"],
                "transitions": ["This sets up our exploration of the historical context"]
            }
        ]
        
        # Calculate duration for each scene and add more scenes to reach 20+ minutes
        for scene in scenes:
            scene["duration"] = calculate_scene_duration(scene["narration"])
        
        # Add more comprehensive scenes to reach target duration
        additional_scenes = [
            {
                "id": "prerequisites",
                "title": "Essential Foundations: Building Your Knowledge From Scratch",
                "narration": "Before we dive into the exciting innovations, let's build a solid foundation of understanding. Think of this like learning to cook a complex dish - we need to understand the basic ingredients and techniques before we can appreciate the chef's masterpiece. We'll start with the most fundamental concepts and build up systematically. First, let's understand what we mean by key terms that will appear throughout our discussion. When we say 'algorithm,' think of it as a recipe - a step-by-step set of instructions that tells a computer exactly what to do. When we mention 'data structures,' imagine these as different ways of organizing information, like choosing between a filing cabinet, a library catalog system, or a digital database depending on what you need to store and how you need to access it. We'll explore the mathematical concepts that underpin this work, but don't worry - we'll focus on the intuitive meaning first, then show how the math captures these ideas precisely. Think of mathematical formulas as a precise language for describing relationships, like how a musical score precisely captures a melody. We'll also cover the computational concepts that are essential for understanding how these methods work in practice, using analogies to everyday processes you already understand. By the end of this section, you'll have all the building blocks needed to understand the revolutionary approach this paper introduces.",
                "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Essential Foundations         │
│ ⏱️ DURATION: 180 seconds               │
│ 📊 COMPLEXITY: Beginner to Intermediate │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Algorithms as recipes                 │
│ • Data structures as organization       │
│ • Mathematical precision language       │
│ • Computational building blocks         │
└─────────────────────────────────────────┘

🔢 MATHEMATICAL FORMULAS:
┌─ FORMULA DISPLAY ───────────────────────┐
│ Basic Notation: f(x) = y               │
│ ├─ Meaning: Function maps input to output│
│ ├─ Variables: x=input, y=output, f=rule │
│ └─ Intuition: Like a recipe transformer │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Cooking recipe analogy          │
│ Step 2: Filing system comparisons       │
│ Step 3: Musical score to math parallel  │
│ Step 4: Complete foundation overview    │
└─────────────────────────────────────────┘
""",
                "key_concepts": ["Algorithms", "Data structures", "Mathematical foundations", "Computational concepts"],
                "formulas": ["Basic mathematical notation with explanations"],
                "diagrams": ["Concept map", "Algorithm flowchart", "Data structure comparisons"],
                "analogies": ["Cooking recipes", "Filing systems", "Musical scores"],
                "transitions": ["With these foundations in place, we can now precisely define the problem"]
            }
        ]
        
        # Calculate durations for additional scenes
        for scene in additional_scenes:
            scene["duration"] = calculate_scene_duration(scene["narration"])
        
        scenes.extend(additional_scenes)
        
        # Calculate total duration
        total_duration = sum(scene["duration"] for scene in scenes)
        
        # If total duration is less than 15 minutes (900s), add more scenes
        if total_duration < 900:
            # Add more detailed scenes to reach minimum duration
            extended_scenes = [
                {
                    "id": "problem_definition",
                    "title": "The Problem Defined: What Exactly Needed Solving",
                    "narration": "Now that we have our foundations, let's precisely define the problem this research tackles. Imagine you're trying to translate a conversation between two people who speak different languages, but you need to do it in real-time, with perfect accuracy, and for thousands of conversations simultaneously. This gives you a sense of the complexity and scale of challenges that researchers were facing. The problem has several interconnected dimensions that make it particularly challenging. First, there's the accuracy dimension - solutions need to be correct, not just approximately right. Think of this like the difference between a GPS that gets you to the right neighborhood versus one that gets you to the exact address. Second, there's the efficiency dimension - solutions need to work fast enough to be practical. Imagine having a calculator that gives perfect answers but takes an hour to compute 2+2. Third, there's the scalability dimension - solutions need to work not just for small test cases but for real-world problems with massive amounts of data. It's like the difference between a recipe that works for cooking dinner for your family versus one that works for feeding a stadium full of people. We'll explore each of these dimensions in detail, showing concrete examples of where previous approaches fell short and why finding a solution required fundamental innovations rather than just incremental improvements.",
                    "visual_description": """
┌─────────────────────────────────────────┐
│ 🎬 SCENE: Problem Definition            │
│ ⏱️ DURATION: 165 seconds               │
│ 📊 COMPLEXITY: Intermediate             │
└─────────────────────────────────────────┘

📋 MAIN CONCEPTS TO VISUALIZE:
┌─ PRIMARY CONCEPTS ──────────────────────┐
│ • Multi-dimensional problem space      │
│ • Accuracy vs approximation trade-offs │
│ • Efficiency and speed requirements    │
│ • Scalability from small to massive    │
└─────────────────────────────────────────┘

📊 COMPARISON TABLES:
┌─ PROBLEM DIMENSIONS ────────────────────┐
│ Dimension   │ Requirement │ Challenge    │
│ ─────────── │ ─────────── │ ──────────── │
│ Accuracy    │ Perfect     │ Approximation│
│ Speed       │ Real-time   │ Slow compute │
│ Scale       │ Massive     │ Small tests  │
│ Complexity  │ Multi-task  │ Single focus │
└─────────────────────────────────────────┘

📈 VISUAL ELEMENTS TO CREATE:
┌─ PROGRESSIVE DIAGRAMS ──────────────────┐
│ Step 1: Translation challenge setup     │
│ Step 2: GPS accuracy comparison         │
│ Step 3: Calculator speed analogy        │
│ Step 4: Family to stadium scaling      │
└─────────────────────────────────────────┘
""",
                    "key_concepts": ["Problem dimensions", "Accuracy requirements", "Efficiency constraints", "Scalability challenges"],
                    "formulas": ["Problem formulation with visual interpretation"],
                    "diagrams": ["Problem space visualization", "Constraint diagram", "Scale comparison"],
                    "analogies": ["Real-time translation", "GPS accuracy", "Slow calculator", "Family vs stadium cooking"],
                    "transitions": ["Understanding the problem precisely, let's explore the intuitive solution approach"]
                }
            ]
            
            for scene in extended_scenes:
                scene["duration"] = calculate_scene_duration(scene["narration"])
            
            scenes.extend(extended_scenes)
            total_duration = sum(scene["duration"] for scene in scenes)
        
        return {
            "title": paper_title,
            "total_duration": total_duration,
            "target_audience": "complete beginners with zero background",
            "teaching_style": "world-class educator explaining from absolute scratch",
            "content_planning": "big picture first, build foundations, define all terms, use analogies",
            "visual_approach": "progressive diagrams, color coding, step-by-step animations",
            "scenes": scenes
        }
    
    def _create_fallback_manim_code(self, scene_title: str, scene_description: str) -> str:
        """Create fallback Manim code when Gemini fails."""
        return f"""
from manim import *

class FallbackScene(Scene):
    def construct(self):
        # Create title
        title = Text("{scene_title}", font_size=36, color=BLUE)
        title.to_edge(UP)
        
        # Create description
        description = Text("{scene_description}", font_size=24, color=WHITE)
        description.next_to(title, DOWN, buff=1)
        
        # Animate
        self.play(Write(title))
        self.wait(1)
        self.play(Write(description))
        self.wait(3)
        self.play(FadeOut(title), FadeOut(description))
"""
    
    def _create_fallback_analysis(self, paper_input: str) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails."""
        return {
            "title": paper_input[:100] if len(paper_input) > 100 else paper_input,
            "field": "Research",
            "contributions": ["Novel approach", "Improved performance"],
            "methodology": "Advanced computational methods",
            "significance": "Advances the state of the art",
            "audience_level": "intermediate",
            "video_structure": ["Introduction", "Methodology", "Results", "Conclusion"],
            "key_concepts": ["Innovation", "Analysis", "Implementation"],
            "estimated_duration": 300
        }


# Global Gemini client instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client