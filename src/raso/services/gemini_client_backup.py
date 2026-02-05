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
        """Generate video script from research paper using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.script_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_script_prompt(paper_title, paper_content, paper_type)
            
            logger.info(f"Generating script for paper: {paper_title}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                script_data = self._parse_script_response(response.text)
                logger.info(f"Generated script with {len(script_data.get('scenes', []))} scenes")
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
                return self._create_fallback_manim_code(scene_title, scene_description)
                
        except Exception as e:
            logger.error(f"Error generating Manim code with Gemini: {e}")
            return self._create_fallback_manim_code(scene_title, scene_description)
    
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

Create a COMPREHENSIVE, DETAILED video script (5-10 minutes) that explains this research paper like a senior engineer teaching students.

TEACHING STYLE:
- Start from BASICS and build to ADVANCED concepts
- Use analogies and real-world examples
- Explain WHY things work, not just WHAT they are
- Show mathematical intuition before formulas
- Connect concepts to practical applications
- Anticipate and answer student questions

VIDEO STRUCTURE (10-15 scenes for 5-10 minute video):
1. Hook & Context (30-45s) - Why this paper matters, real-world impact
2. Prerequisites (45-60s) - What you need to know first
3. Problem Statement (60-90s) - What problem does this solve? Why is it hard?
4. Intuition (60-90s) - High-level idea before diving into details
5. Core Concept 1 (60-90s) - First major idea with examples
6. Mathematical Foundation (60-90s) - Key formulas with intuition
7. Core Concept 2 (60-90s) - Second major idea
8. Architecture/Method (90-120s) - How it actually works
9. Key Innovation (60-90s) - What makes this special/different
10. Implementation Details (60-90s) - Practical considerations
11. Results & Analysis (60-90s) - What did they achieve?
12. Applications (45-60s) - Where is this used today?
13. Limitations (30-45s) - What doesn't work well?
14. Future Directions (30-45s) - Where is this going?
15. Summary & Takeaways (45-60s) - Key points to remember

For EACH scene, provide:
- Scene ID (short identifier)
- Title (descriptive, engaging)
- Duration (45-120 seconds per scene)
- Narration (DETAILED explanation, 200-400 words)
  * Explain concepts from first principles
  * Use analogies and examples
  * Show step-by-step reasoning
  * Include "imagine this..." or "think of it like..." explanations
- Visual Description (what to show)
  * Specific formulas to display
  * Diagrams to draw
  * Key concepts to highlight
  * Animations to create

NARRATION REQUIREMENTS:
- 200-400 words per scene (detailed explanations)
- Conversational, engaging tone
- Use "we", "let's", "imagine" to involve viewers
- Explain mathematical intuition before showing formulas
- Give concrete examples
- Connect to things students already know

VISUAL REQUIREMENTS:
- Show KEY FORMULAS from the paper
- Draw DIAGRAMS to illustrate concepts
- Highlight IMPORTANT TERMS
- Use STEP-BY-STEP animations
- Display COMPARISONS (before/after, old vs new)

Format as JSON:
{{
  "title": "{paper_title}",
  "total_duration": 300-600,
  "target_audience": "students and engineers",
  "teaching_style": "senior engineer explaining from basics to advanced",
  "scenes": [
    {{
      "id": "hook",
      "title": "Why This Paper Changed Everything",
      "duration": 45.0,
      "narration": "Detailed 200-400 word explanation starting from basics...",
      "visual_description": "Show specific formula: [formula], diagram of [concept], highlight [key term]",
      "key_concepts": ["concept1", "concept2"],
      "formulas": ["formula1 if applicable"],
      "diagrams": ["diagram description if applicable"]
    }}
  ]
}}

Make it feel like a REAL LECTURE from an expert teacher who deeply understands the material and can explain it clearly.
"""
    
    def _create_manim_prompt(self, scene_title: str, scene_description: str, scene_duration: float) -> str:
        """Create prompt for Manim code generation."""
        return f"""
You are an expert Manim animator specializing in educational content. Generate Python code using Manim to create a compelling educational animation.

Scene: {scene_title}
Description: {scene_description}
Duration: {scene_duration} seconds

CRITICAL TEXT SIZING REQUIREMENTS:
- ALL text MUST fit within the screen boundaries (max width: 12 units)
- Use scale_to_fit_width(12) for any text that might be too wide
- Font sizes: Title (48px), Subtitle (36px), Content (28px) - READABLE AND BALANCED
- ALWAYS check and scale text to fit: if text.width > 12: text.scale_to_fit_width(12)
- Content should be readable but not overwhelming

TIMING REQUIREMENTS:
- Use the FULL {scene_duration} seconds effectively
- Allow sufficient reading time (8-20 seconds based on content length)
- Don't rush through content - viewers need time to read and understand
- Calculate reading time: max(8, min(20, content_length / 40))

Create a Manim Scene class that creates engaging educational content with:

VISUAL ELEMENTS:
- Clear, readable text with proper hierarchy
- Diagrams, charts, or mathematical visualizations when relevant
- Smooth animations that guide viewer attention
- Professional color scheme (blues, whites, greens for highlights)
- Proper spacing and layout
- **ALL TEXT MUST FIT ON SCREEN** - use scaling as needed

ANIMATION TECHNIQUES:
- Use Write() for text that should appear gradually
- Use Create() for diagrams and shapes
- Use Transform() for concept transitions
- Use FadeIn/FadeOut for smooth transitions
- Use AnimationGroup for coordinated animations
- Time animations to fit the {scene_duration} second duration

EDUCATIONAL BEST PRACTICES:
- Start with a clear title (max 50 characters)
- Build concepts progressively
- Use visual metaphors when appropriate
- Highlight key points with color or movement
- End with a summary or transition

TECHNICAL REQUIREMENTS:
- Class name should be descriptive (e.g., IntroductionScene, MethodologyScene)
- Use Manim Community Edition syntax
- Include proper imports
- Add brief comments for complex animations
- Ensure all text is readable (minimum font size 36px)
- **CRITICAL**: Scale all text to fit screen boundaries
- Use self.wait() appropriately for pacing

TEXT FITTING EXAMPLE:
```python
title = Text("Your Title", font_size=32)
if title.width > 12:
    title.scale_to_fit_width(12)
```

Return ONLY the complete Python code:

```python
from manim import *

class YourSceneClass(Scene):
    def construct(self):
        # Create engaging educational animation here
        # ENSURE ALL TEXT FITS ON SCREEN
        # Use the full {scene_duration} seconds effectively
        pass
```

Make it educational, visually appealing, and perfectly timed for the duration.
**MOST IMPORTANT: Ensure all text elements fit within screen boundaries!**
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
            return self._create_fallback_manim_code("Scene", "Animation")
    
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
        """Create fallback script when Gemini fails - professional educational format (5-10 minutes)."""
        return {
            "title": paper_title,
            "total_duration": 360.0,  # 6 minutes (5-10 minute range)
            "target_audience": "students and engineers",
            "teaching_style": "senior engineer explaining from basics to advanced",
            "scenes": [
                {
                    "id": "hook",
                    "title": "Why This Research Matters",
                    "duration": 35.0,
                    "narration": f"Welcome to this comprehensive technical analysis of '{paper_title}'. This research represents a significant contribution to the field, addressing fundamental challenges through innovative methodologies and rigorous theoretical foundations. As professional engineers and researchers, we'll examine this work from first principles, building from basic concepts to advanced implementations. We'll explore the mathematical foundations, analyze the algorithmic innovations, and discuss practical implications for real-world systems. This paper introduces novel approaches that advance the state-of-the-art, providing insights directly applicable to modern software engineering and system architecture. Throughout this analysis, we'll connect theoretical concepts to practical applications, ensuring you understand not just what the research does, but why it works and how you can apply these principles in your own projects.",
                    "visual_description": "Professional title slide with paper citation, research field context, and key impact areas",
                    "key_concepts": ["Research significance", "Real-world impact", "Technical innovation"],
                    "formulas": [],
                    "diagrams": ["Impact overview diagram"]
                },
                {
                    "id": "prerequisites",
                    "title": "Essential Background and Prerequisites",
                    "duration": 45.0,
                    "narration": "Before diving into the core contributions, let's establish the foundational concepts you'll need to fully understand this work. We'll start with the basic principles and mathematical tools that underpin the research. Think of this as building a solid foundation before constructing a complex structure - each concept we cover here will be essential for understanding the innovations that follow. We'll review relevant algorithms, data structures, and theoretical frameworks from computer science and mathematics. If you're familiar with these concepts, this will serve as a refresher and establish our notation. If these ideas are new to you, don't worry - we'll explain each concept clearly with examples and intuition before moving forward. The key is to ensure everyone has the same baseline understanding, so we can explore the advanced concepts together without gaps in knowledge. We'll use analogies and real-world examples to make abstract concepts concrete and relatable.",
                    "visual_description": "Concept map showing prerequisite knowledge, mathematical notation guide, and foundational algorithms",
                    "key_concepts": ["Foundational concepts", "Mathematical prerequisites", "Algorithm basics"],
                    "formulas": ["Basic mathematical notation"],
                    "diagrams": ["Prerequisite concept map", "Notation guide"]
                },
                {
                    "id": "problem",
                    "title": "Problem Statement and Challenges",
                    "duration": 50.0,
                    "narration": "Now let's examine the specific problem this research addresses. What makes this problem challenging? Why haven't previous approaches solved it effectively? Understanding the problem deeply is crucial for appreciating the solution's elegance and innovation. We'll analyze the limitations of existing methods, identifying specific bottlenecks in computational complexity, memory efficiency, or scalability. Consider the real-world scenarios where these limitations become critical - perhaps in large-scale distributed systems, real-time processing pipelines, or resource-constrained environments. The problem often involves trade-offs between competing objectives: speed versus accuracy, memory versus computation, or simplicity versus expressiveness. We'll formalize the problem mathematically, defining objective functions, constraint sets, and optimization criteria. This rigorous formulation allows us to precisely characterize what makes the problem hard and what properties an ideal solution should possess. By the end of this section, you'll understand not just what problem we're solving, but why it's important and what makes it technically challenging.",
                    "visual_description": "Problem visualization with existing method limitations, bottleneck analysis, and mathematical problem formulation",
                    "key_concepts": ["Problem definition", "Existing limitations", "Technical challenges"],
                    "formulas": ["Problem formulation", "Constraint definitions"],
                    "diagrams": ["Bottleneck analysis", "Trade-off visualization"]
                },
                {
                    "id": "method",
                    "title": "Detailed Methodology and Algorithm",
                    "duration": 60.0,
                    "narration": "Now we'll examine the detailed methodology, translating our intuition into precise algorithms and mathematical formulations. The approach consists of several key components that work together to achieve the desired properties. First, we'll look at the data structures and representations used - these choices are crucial for efficiency and correctness. Next, we'll walk through the algorithm step-by-step, explaining the purpose of each operation and how it contributes to the overall solution. Pay attention to the invariants maintained throughout execution - these guarantee correctness and provide insight into why the algorithm works. We'll analyze the computational complexity, showing how the approach achieves better performance than previous methods. The mathematical formulation provides rigorous guarantees about convergence, optimality, or approximation quality. We'll discuss implementation considerations: how to handle edge cases, numerical stability concerns, and practical optimizations that improve performance without sacrificing correctness.",
                    "visual_description": "Algorithm flowcharts, pseudocode, data structure diagrams, and complexity analysis",
                    "key_concepts": ["Algorithm design", "Data structures", "Implementation details"],
                    "formulas": ["Core algorithm equations", "Complexity bounds"],
                    "diagrams": ["Algorithm flowchart", "Data structure visualization"]
                },
                {
                    "id": "results",
                    "title": "Experimental Results and Performance Analysis",
                    "duration": 50.0,
                    "narration": "Now let's examine the experimental validation and performance analysis. The authors evaluate their approach on standard benchmarks and real-world datasets, comparing against state-of-the-art baselines. We'll look at the experimental setup: what datasets were used, how were hyperparameters chosen, and what metrics measure success. The results demonstrate significant improvements across multiple dimensions - perhaps better accuracy, faster runtime, lower memory usage, or improved scalability. Pay attention to the statistical significance of the results and the confidence intervals provided. We'll analyze performance across different problem sizes and characteristics, identifying where the method excels and where it faces limitations. The ablation studies reveal which components contribute most to performance, helping us understand what makes the approach effective.",
                    "visual_description": "Performance charts, comparison tables, ablation study results, and scalability analysis",
                    "key_concepts": ["Experimental validation", "Performance metrics", "Comparative analysis"],
                    "formulas": ["Performance metrics"],
                    "diagrams": ["Performance comparison charts", "Scalability plots"]
                },
                {
                    "id": "impact",
                    "title": "Impact and Future Directions",
                    "duration": 40.0,
                    "narration": "This research establishes new benchmarks while opening multiple avenues for future investigation and system development. The impact extends beyond immediate performance improvements to influence fundamental approaches in algorithm design and software engineering practices. Future directions include extensions to distributed computing environments, integration with emerging hardware architectures, and adaptation to evolving data characteristics. The work provides foundation for next-generation systems leveraging cloud-native architectures, edge computing deployments, and hybrid cloud environments, with significant implications for industry standards and open-source framework development. We'll discuss the broader implications for the field and how this work might influence future research directions.",
                    "visual_description": "Impact analysis, future research roadmap, and application domains",
                    "key_concepts": ["Research impact", "Future directions", "Practical applications"],
                    "formulas": [],
                    "diagrams": ["Impact timeline", "Future research map"]
                }
            ]
        }


    def construct(self):
        self.camera.background_color = "#0f0f23"
        
        title = Text(
            "{title_escaped}", 
            font_size={title_font_size},
            color=BLUE, 
            weight=BOLD
        )
        title.to_edge(UP, buff=0.3)
        if title.width > 14:
            title.scale_to_fit_width(14)
        
        subtitle = Text(
            "Key Concepts & Analysis", 
            font_size={subtitle_font_size},
            color=GREEN
        )
        subtitle.next_to(title, DOWN, buff=0.2)
        
        top_line = Line(LEFT * 7, RIGHT * 7, color=BLUE, stroke_width=2)
        top_line.next_to(subtitle, DOWN, buff=0.15)
        
        # Split content into lines for better display (max 80 chars per line)
        words = "{desc_escaped}".split()
        lines = []
        current_line = ""
        for word in words:
            if len(current_line) + len(word) + 1 <= 80:
                current_line += word + " "
            else:
                lines.append(current_line.strip())
                current_line = word + " "
        if current_line:
            lines.append(current_line.strip())
        
        # Take first 6 lines to fit on screen
        display_text = "\\n".join(lines[:6])
        if len(lines) > 6:
            display_text += "..."
        
        content_text = Text(
            display_text,
            font_size={content_font_size},
            color=WHITE,
            line_spacing=1.3
        )
        content_text.next_to(top_line, DOWN, buff=0.3)
        
        # Ensure content fits on screen
        if content_text.width > 13:
            content_text.scale_to_fit_width(13)
        if content_text.height > 4.5:
            content_text.scale_to_fit_height(4.5)
        
        self.play(Write(title), run_time=0.6)
        self.play(FadeIn(subtitle), run_time=0.4)
        self.play(Create(top_line), run_time=0.2)
        self.play(FadeIn(content_text, shift=UP*0.1), run_time=0.8)
        
        # Longer reading time for better comprehension
        reading_time = max(8, min(20, len("{desc_escaped}") / 40))
        self.wait(reading_time)
        
        everything = VGroup(title, subtitle, top_line, content_text)
        self.play(FadeOut(everything), run_time=0.2)
"""

    def _create_fallback_analysis(self, paper_input: str) -> Dict[str, Any]:
        """Create fallback analysis when Gemini fails."""
        return {
            "title": paper_input[:100] if len(paper_input) > 100 else paper_input,
            "field": "Research",
            "contributions": ["Novel approach", "Improved methodology"],
            "methodology": "Advanced computational methods",
            "significance": "Contributes to the advancement of the field",
            "audience_level": "intermediate",
            "video_structure": ["Introduction", "Methodology", "Results", "Conclusion"],
            "key_concepts": ["Innovation", "Analysis", "Results"],
            "estimated_duration": 60
        }

# Global Gemini client instance
_gemini_client = None

def get_gemini_client() -> GeminiClient:
    """Get global Gemini client instance."""
    global _gemini_client
    if _gemini_client is None:
        _gemini_client = GeminiClient()
    return _gemini_client

class EnhancedGeminiClient(GeminiClient):
    """Enhanced Gemini client with cinematic visual description capabilities."""
    
    def __init__(self):
        """Initialize enhanced Gemini client."""
        super().__init__()
        
        # Additional model configurations for cinematic features
        self.visual_description_model = os.getenv('RASO_VISUAL_DESCRIPTION_MODEL', 'gemini-1.5-pro')
        self.scene_analysis_model = os.getenv('RASO_SCENE_ANALYSIS_MODEL', 'gemini-1.5-pro')
        
        logger.info("Enhanced Gemini client initialized with cinematic capabilities")
    
    async def generate_detailed_visual_description(
        self,
        scene_content: str,
        scene_type: str,
        cinematic_settings: Dict[str, Any],
        target_audience: str = "intermediate",
        previous_descriptions: List[str] = None
    ) -> Dict[str, Any]:
        """Generate detailed visual description for cinematic production."""
        try:
            model = genai.GenerativeModel(
                model_name=self.visual_description_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_visual_description_prompt(
                scene_content, scene_type, cinematic_settings, target_audience, previous_descriptions
            )
            
            logger.info(f"Generating visual description for scene type: {scene_type}")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                description_data = self._parse_visual_description_response(response.text)
                logger.info("Visual description generated successfully")
                return description_data
            else:
                logger.error("Empty response from Gemini for visual description")
                return self._create_fallback_visual_description(scene_content, scene_type)
                
        except Exception as e:
            logger.error(f"Error generating visual description with Gemini: {e}")
            return self._create_fallback_visual_description(scene_content, scene_type)
    
    async def analyze_scene_for_cinematics(
        self,
        content: str,
        content_type: str = "text"
    ) -> Dict[str, Any]:
        """Analyze scene content to recommend optimal cinematic settings."""
        try:
            model = genai.GenerativeModel(
                model_name=self.scene_analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_scene_analysis_prompt(content, content_type)
            
            logger.info(f"Analyzing scene content for cinematic recommendations")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                analysis_data = self._parse_scene_analysis_response(response.text)
                logger.info("Scene analysis completed successfully")
                return analysis_data
            else:
                logger.error("Empty response from Gemini for scene analysis")
                return self._create_fallback_scene_analysis(content)
                
        except Exception as e:
            logger.error(f"Error analyzing scene with Gemini: {e}")
            return self._create_fallback_scene_analysis(content)
    
    async def generate_visual_consistency_analysis(
        self,
        descriptions: List[str],
        overall_theme: str
    ) -> Dict[str, Any]:
        """Analyze visual descriptions for consistency across scenes."""
        try:
            model = genai.GenerativeModel(
                model_name=self.visual_description_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_consistency_analysis_prompt(descriptions, overall_theme)
            
            logger.info(f"Analyzing visual consistency across {len(descriptions)} descriptions")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                consistency_data = self._parse_consistency_analysis_response(response.text)
                logger.info("Visual consistency analysis completed successfully")
                return consistency_data
            else:
                logger.error("Empty response from Gemini for consistency analysis")
                return self._create_fallback_consistency_analysis(descriptions)
                
        except Exception as e:
            logger.error(f"Error analyzing visual consistency with Gemini: {e}")
            return self._create_fallback_consistency_analysis(descriptions)
    
    async def suggest_cinematic_improvements(
        self,
        current_description: str,
        cinematic_settings: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Suggest improvements to visual descriptions based on cinematic settings."""
        try:
            model = genai.GenerativeModel(
                model_name=self.visual_description_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_improvement_suggestions_prompt(current_description, cinematic_settings)
            
            logger.info("Generating cinematic improvement suggestions")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                suggestions_data = self._parse_improvement_suggestions_response(response.text)
                logger.info("Cinematic improvement suggestions generated successfully")
                return suggestions_data
            else:
                logger.error("Empty response from Gemini for improvement suggestions")
                return self._create_fallback_improvement_suggestions(current_description)
                
        except Exception as e:
            logger.error(f"Error generating improvement suggestions with Gemini: {e}")
            return self._create_fallback_improvement_suggestions(current_description)
    
    def _create_visual_description_prompt(
        self, 
        scene_content: str, 
        scene_type: str, 
        cinematic_settings: Dict[str, Any],
        target_audience: str,
        previous_descriptions: List[str] = None
    ) -> str:
        """Create prompt for detailed visual description generation."""
        consistency_context = ""
        if previous_descriptions:
            consistency_context = f"""
Previous scene descriptions for consistency:
{chr(10).join([f"- {desc[:200]}..." for desc in previous_descriptions[-3:]])}

Ensure visual consistency with previous scenes while maintaining narrative flow.
"""
        
        return f"""
You are an expert cinematic director and visual storytelling specialist. Create a detailed visual description for a video scene that will be used by a cinematic video generator.

Scene Content: {scene_content}
Scene Type: {scene_type}
Target Audience: {target_audience}
Cinematic Settings: {cinematic_settings}

{consistency_context}

Create a comprehensive visual description that includes:

1. **Camera Work**: Specific camera angles, movements, and framing
   - Opening shot composition and angle
   - Camera movement throughout the scene (pan, zoom, dolly, etc.)
   - Closing shot and transition preparation

2. **Lighting Design**: Mood and technical lighting specifications
   - Key lighting setup and mood
   - Color temperature and intensity
   - Shadow and highlight treatment
   - Special lighting effects if appropriate

3. **Visual Composition**: Layout and visual hierarchy
   - Foreground, midground, background elements
   - Text placement and typography treatment
   - Visual balance and focal points
   - Color palette and visual theme

4. **Cinematic Elements**: Professional production features
   - Film grain, depth of field, motion blur settings
   - Color grading approach and film emulation
   - Transition style to next scene
   - Visual effects and compositing needs

5. **Content-Specific Visuals**: Elements that support the narrative
   - Diagrams, charts, or visual aids needed
   - Animation style and pacing
   - Visual metaphors or symbolic elements
   - Text overlays and information hierarchy

Format as JSON:
{{
  "description": "Complete detailed visual description...",
  "camera_work": {{
    "opening_shot": "Description of opening camera position and framing",
    "movement": "Camera movement throughout scene",
    "closing_shot": "Final camera position and transition setup"
  }},
  "lighting": {{
    "mood": "Overall lighting mood and atmosphere",
    "setup": "Technical lighting specifications",
    "color_temperature": "Warm/cool/neutral with specific values",
    "effects": "Special lighting effects or treatments"
  }},
  "composition": {{
    "layout": "Visual layout and element positioning",
    "color_palette": "Primary and accent colors",
    "typography": "Text treatment and hierarchy",
    "focal_points": "Key visual emphasis areas"
  }},
  "cinematic_elements": {{
    "film_grain": "Film grain intensity and style",
    "depth_of_field": "DOF settings and focus areas",
    "color_grading": "Color grading approach and LUT style",
    "transitions": "Transition style and timing"
  }},
  "content_visuals": {{
    "diagrams": "Required diagrams or visual aids",
    "animations": "Animation style and timing",
    "text_overlays": "Text content and positioning",
    "visual_metaphors": "Symbolic or metaphorical elements"
  }},
  "technical_notes": "Additional technical requirements or considerations",
  "confidence": 0.95
}}

Make the description cinematic, professional, and perfectly suited for the content type and audience level.
"""
    
    def _create_scene_analysis_prompt(self, content: str, content_type: str) -> str:
        """Create prompt for scene analysis and cinematic recommendations."""
        return f"""
You are an expert cinematic analyst and content strategist. Analyze the following content to recommend optimal cinematic settings and approach.

Content Type: {content_type}
Content: {content}

Analyze the content and provide recommendations for:

1. **Content Analysis**:
   - Mood and emotional tone
   - Complexity level and technical depth
   - Pacing requirements
   - Focus type (mathematical, architectural, analytical, etc.)
   - Key themes and concepts

2. **Cinematic Recommendations**:
   - Optimal camera movement style and reasoning
   - Color grading approach and film emulation
   - Sound design strategy
   - Lighting mood and setup
   - Visual composition style

3. **Audience Considerations**:
   - Appropriate visual complexity
   - Engagement strategies
   - Accessibility considerations
   - Platform optimization suggestions

Format as JSON:
{{
  "analysis": {{
    "mood": "Primary emotional tone",
    "complexity": "low|medium|high",
    "pacing": "slow|medium|fast",
    "focus_type": "mathematical|architectural|analytical|procedural|general",
    "key_themes": ["theme1", "theme2", "theme3"],
    "technical_level": "beginner|intermediate|advanced"
  }},
  "recommendations": {{
    "camera_movement": {{
      "type": "static|pan|zoom|dolly|crane|handheld",
      "reasoning": "Why this movement type is optimal",
      "confidence": 0.9
    }},
    "color_grading": {{
      "film_emulation": "none|kodak|fuji|cinema",
      "adjustments": {{
        "temperature": 0.1,
        "contrast": 0.2,
        "saturation": 0.0
      }},
      "reasoning": "Why this grading approach works",
      "confidence": 0.85
    }},
    "sound_design": {{
      "approach": "minimal|standard|rich",
      "elements": ["ambient", "music", "effects"],
      "reasoning": "Sound design strategy explanation",
      "confidence": 0.8
    }},
    "lighting": {{
      "mood": "clinical|warm|dramatic|neutral",
      "setup": "high-key|low-key|natural|stylized",
      "reasoning": "Lighting choice explanation"
    }}
  }},
  "audience_optimization": {{
    "visual_complexity": "Appropriate visual density",
    "engagement_strategy": "How to maintain viewer attention",
    "accessibility_notes": "Considerations for inclusive design",
    "platform_suggestions": "Optimization for different platforms"
  }},
  "overall_confidence": 0.88
}}

Provide detailed, actionable recommendations based on content analysis.
"""
    
    def _create_consistency_analysis_prompt(self, descriptions: List[str], overall_theme: str) -> str:
        """Create prompt for visual consistency analysis."""
        descriptions_text = "\n\n".join([f"Scene {i+1}: {desc}" for i, desc in enumerate(descriptions)])
        
        return f"""
You are an expert cinematic continuity supervisor. Analyze the following visual descriptions for consistency and narrative flow.

Overall Theme: {overall_theme}

Visual Descriptions:
{descriptions_text}

Analyze for:

1. **Visual Consistency**:
   - Color palette consistency across scenes
   - Lighting mood and style continuity
   - Camera work coherence
   - Visual composition harmony

2. **Narrative Flow**:
   - Logical progression between scenes
   - Transition compatibility
   - Pacing consistency
   - Thematic coherence

3. **Technical Consistency**:
   - Film grain and quality settings
   - Color grading approach
   - Visual effects style
   - Typography and text treatment

4. **Recommendations**:
   - Adjustments needed for better consistency
   - Scenes that need revision
   - Overall improvements

Format as JSON:
{{
  "consistency_score": 0.85,
  "analysis": {{
    "visual_consistency": {{
      "color_palette": "Assessment of color consistency",
      "lighting": "Lighting continuity evaluation",
      "camera_work": "Camera style consistency",
      "score": 0.9
    }},
    "narrative_flow": {{
      "progression": "Scene progression assessment",
      "transitions": "Transition compatibility",
      "pacing": "Pacing consistency evaluation",
      "score": 0.8
    }},
    "technical_consistency": {{
      "quality_settings": "Technical settings consistency",
      "effects_style": "Visual effects coherence",
      "typography": "Text treatment consistency",
      "score": 0.85
    }}
  }},
  "issues": [
    {{
      "scene_index": 2,
      "issue": "Color temperature inconsistency",
      "severity": "medium",
      "suggestion": "Adjust to match previous scenes"
    }}
  ],
  "recommendations": [
    "Specific improvement suggestions",
    "Overall consistency enhancements"
  ],
  "revised_descriptions": {{
    "scene_2": "Revised description if needed"
  }}
}}

Provide detailed analysis and actionable recommendations for visual consistency.
"""
    
    def _create_improvement_suggestions_prompt(self, current_description: str, cinematic_settings: Dict[str, Any]) -> str:
        """Create prompt for cinematic improvement suggestions."""
        return f"""
You are an expert cinematic director and post-production specialist. Review the current visual description and suggest improvements based on the cinematic settings.

Current Description: {current_description}
Cinematic Settings: {cinematic_settings}

Analyze and suggest improvements for:

1. **Technical Enhancement**:
   - Better camera work integration
   - Improved lighting specifications
   - Enhanced color grading details
   - Professional composition techniques

2. **Cinematic Quality**:
   - Film-like visual treatments
   - Professional production values
   - Industry-standard techniques
   - Creative visual storytelling

3. **Settings Optimization**:
   - Better utilization of enabled features
   - Consistency with user preferences
   - Quality preset optimization
   - Platform-specific enhancements

Format as JSON:
{{
  "improvement_score": 0.75,
  "current_strengths": [
    "Existing strong points in the description"
  ],
  "improvement_areas": [
    {{
      "category": "camera_work",
      "current": "Current camera description",
      "suggested": "Improved camera description",
      "reasoning": "Why this improvement helps",
      "impact": "high|medium|low"
    }}
  ],
  "enhanced_description": "Complete improved visual description incorporating all suggestions",
  "technical_enhancements": {{
    "camera_work": "Specific camera improvements",
    "lighting": "Lighting enhancements",
    "color_grading": "Color grading improvements",
    "composition": "Composition refinements"
  }},
  "cinematic_upgrades": {{
    "film_quality": "Film-like enhancement suggestions",
    "professional_touches": "Professional production improvements",
    "creative_elements": "Creative storytelling enhancements"
  }},
  "settings_optimization": "How to better utilize current cinematic settings"
}}

Provide specific, actionable improvements that enhance cinematic quality.
"""
    
    def _parse_visual_description_response(self, response_text: str) -> Dict[str, Any]:
        """Parse visual description generation response."""
        try:
            import json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing visual description response: {e}")
            return self._create_fallback_visual_description("Unknown content", "general")
    
    def _parse_scene_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse scene analysis response."""
        try:
            import json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing scene analysis response: {e}")
            return self._create_fallback_scene_analysis("Unknown content")
    
    def _parse_consistency_analysis_response(self, response_text: str) -> Dict[str, Any]:
        """Parse consistency analysis response."""
        try:
            import json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing consistency analysis response: {e}")
            return self._create_fallback_consistency_analysis([])
    
    def _parse_improvement_suggestions_response(self, response_text: str) -> Dict[str, Any]:
        """Parse improvement suggestions response."""
        try:
            import json
            start_idx = response_text.find('{')
            end_idx = response_text.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response_text[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
                
        except Exception as e:
            logger.error(f"Error parsing improvement suggestions response: {e}")
            return self._create_fallback_improvement_suggestions("Unknown description")
    
    def _create_fallback_visual_description(self, scene_content: str, scene_type: str) -> Dict[str, Any]:
        """Create fallback visual description when Gemini fails."""
        return {
            "description": f"Professional cinematic presentation of {scene_type} content with clean composition, appropriate lighting, and engaging visual elements.",
            "camera_work": {
                "opening_shot": "Medium shot with slight zoom-in for engagement",
                "movement": "Subtle dolly movement to maintain visual interest",
                "closing_shot": "Hold on key visual element before transition"
            },
            "lighting": {
                "mood": "Professional and clear",
                "setup": "Three-point lighting with soft shadows",
                "color_temperature": "Neutral 5600K for clarity",
                "effects": "Subtle rim lighting for depth"
            },
            "composition": {
                "layout": "Rule of thirds with balanced visual hierarchy",
                "color_palette": "Professional blues and whites with accent colors",
                "typography": "Clean, readable sans-serif fonts",
                "focal_points": "Center-weighted with clear visual flow"
            },
            "cinematic_elements": {
                "film_grain": "Subtle grain for professional film look",
                "depth_of_field": "Moderate DOF to maintain focus",
                "color_grading": "Neutral with slight contrast enhancement",
                "transitions": "Smooth fade transition"
            },
            "content_visuals": {
                "diagrams": "Clean, professional diagrams as needed",
                "animations": "Smooth, purposeful animations",
                "text_overlays": "Clear, well-positioned text elements",
                "visual_metaphors": "Appropriate visual representations"
            },
            "technical_notes": "Standard professional video production settings",
            "confidence": 0.7
        }
    
    def _create_fallback_scene_analysis(self, content: str) -> Dict[str, Any]:
        """Create fallback scene analysis when Gemini fails."""
        return {
            "analysis": {
                "mood": "neutral",
                "complexity": "medium",
                "pacing": "medium",
                "focus_type": "general",
                "key_themes": ["information", "education", "presentation"],
                "technical_level": "intermediate"
            },
            "recommendations": {
                "camera_movement": {
                    "type": "dolly",
                    "reasoning": "Subtle movement maintains engagement without distraction",
                    "confidence": 0.7
                },
                "color_grading": {
                    "film_emulation": "none",
                    "adjustments": {
                        "temperature": 0.0,
                        "contrast": 0.1,
                        "saturation": 0.0
                    },
                    "reasoning": "Neutral grading for clear information presentation",
                    "confidence": 0.8
                },
                "sound_design": {
                    "approach": "standard",
                    "elements": ["ambient"],
                    "reasoning": "Clean audio focus on narration",
                    "confidence": 0.8
                },
                "lighting": {
                    "mood": "neutral",
                    "setup": "natural",
                    "reasoning": "Clear, professional lighting for information delivery"
                }
            },
            "audience_optimization": {
                "visual_complexity": "Moderate complexity appropriate for general audience",
                "engagement_strategy": "Clear visual hierarchy and smooth transitions",
                "accessibility_notes": "High contrast text and clear visual elements",
                "platform_suggestions": "Standard HD quality suitable for all platforms"
            },
            "overall_confidence": 0.75
        }
    
    def _create_fallback_consistency_analysis(self, descriptions: List[str]) -> Dict[str, Any]:
        """Create fallback consistency analysis when Gemini fails."""
        return {
            "consistency_score": 0.8,
            "analysis": {
                "visual_consistency": {
                    "color_palette": "Generally consistent color approach",
                    "lighting": "Consistent lighting mood across scenes",
                    "camera_work": "Coherent camera style maintained",
                    "score": 0.8
                },
                "narrative_flow": {
                    "progression": "Logical scene progression",
                    "transitions": "Compatible transition styles",
                    "pacing": "Consistent pacing approach",
                    "score": 0.8
                },
                "technical_consistency": {
                    "quality_settings": "Consistent technical approach",
                    "effects_style": "Coherent visual effects style",
                    "typography": "Consistent text treatment",
                    "score": 0.8
                }
            },
            "issues": [],
            "recommendations": [
                "Maintain current consistency approach",
                "Consider minor refinements for enhanced flow"
            ],
            "revised_descriptions": {}
        }
    
    def _create_fallback_improvement_suggestions(self, current_description: str) -> Dict[str, Any]:
        """Create fallback improvement suggestions when Gemini fails."""
        return {
            "improvement_score": 0.8,
            "current_strengths": [
                "Clear visual description",
                "Professional approach",
                "Appropriate technical details"
            ],
            "improvement_areas": [
                {
                    "category": "camera_work",
                    "current": "Basic camera description",
                    "suggested": "Enhanced camera movement with specific technical details",
                    "reasoning": "More detailed camera work improves cinematic quality",
                    "impact": "medium"
                }
            ],
            "enhanced_description": current_description + " Enhanced with professional cinematic techniques and improved visual storytelling elements.",
            "technical_enhancements": {
                "camera_work": "Add specific camera movement timing and framing details",
                "lighting": "Include precise lighting setup and mood specifications",
                "color_grading": "Specify color grading approach and film emulation",
                "composition": "Detail visual composition and element positioning"
            },
            "cinematic_upgrades": {
                "film_quality": "Add film grain and professional visual treatments",
                "professional_touches": "Include industry-standard production techniques",
                "creative_elements": "Enhance visual storytelling and creative composition"
            },
            "settings_optimization": "Utilize all enabled cinematic features for maximum visual impact"
        }

    # YouTube and Social Media Optimization Methods

    async def generate_youtube_seo_metadata(
        self,
        content: str,
        title: str,
        description: str
    ) -> Dict[str, Any]:
        """Generate SEO-optimized metadata for YouTube using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_youtube_seo_prompt(content, title, description)
            
            logger.info("Generating YouTube SEO metadata with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                seo_data = self._parse_seo_metadata_response(response.text)
                logger.info("YouTube SEO metadata generated successfully")
                return seo_data
            else:
                logger.error("Empty response from Gemini for YouTube SEO metadata")
                return self._create_fallback_seo_metadata(title, description)
                
        except Exception as e:
            logger.error(f"Error generating YouTube SEO metadata with Gemini: {e}")
            return self._create_fallback_seo_metadata(title, description)

    async def generate_audio_descriptions(
        self,
        content: str,
        title: str,
        cinematic_settings: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate audio descriptions for accessibility using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_audio_description_prompt(content, title, cinematic_settings)
            
            logger.info("Generating audio descriptions with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                audio_descriptions = self._parse_audio_descriptions_response(response.text)
                logger.info(f"Generated {len(audio_descriptions)} audio descriptions")
                return audio_descriptions
            else:
                logger.error("Empty response from Gemini for audio descriptions")
                return self._create_fallback_audio_descriptions(content)
                
        except Exception as e:
            logger.error(f"Error generating audio descriptions with Gemini: {e}")
            return self._create_fallback_audio_descriptions(content)

    async def generate_thumbnail_suggestions(
        self,
        content: str,
        title: str,
        style: str = "engaging"
    ) -> List[Dict[str, Any]]:
        """Generate thumbnail suggestions using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_thumbnail_suggestion_prompt(content, title, style)
            
            logger.info("Generating thumbnail suggestions with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                thumbnail_suggestions = self._parse_thumbnail_suggestions_response(response.text)
                logger.info(f"Generated {len(thumbnail_suggestions)} thumbnail suggestions")
                return thumbnail_suggestions
            else:
                logger.error("Empty response from Gemini for thumbnail suggestions")
                return self._create_fallback_thumbnail_suggestions(title)
                
        except Exception as e:
            logger.error(f"Error generating thumbnail suggestions with Gemini: {e}")
            return self._create_fallback_thumbnail_suggestions(title)

    async def generate_seo_metadata(
        self,
        content: str,
        title: str,
        description: str,
        target_keywords: List[str],
        platform: str = "youtube"
    ) -> Dict[str, Any]:
        """Generate SEO metadata for various platforms using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_seo_metadata_prompt(content, title, description, target_keywords, platform)
            
            logger.info(f"Generating SEO metadata for {platform} with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                seo_metadata = self._parse_seo_metadata_response(response.text)
                logger.info("SEO metadata generated successfully")
                return seo_metadata
            else:
                logger.error("Empty response from Gemini for SEO metadata")
                return self._create_fallback_seo_metadata(title, description)
                
        except Exception as e:
            logger.error(f"Error generating SEO metadata with Gemini: {e}")
            return self._create_fallback_seo_metadata(title, description)

    async def generate_hashtags(
        self,
        content: str,
        title: str,
        platform: str = "youtube"
    ) -> List[str]:
        """Generate relevant hashtags for content using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_hashtag_generation_prompt(content, title, platform)
            
            logger.info(f"Generating hashtags for {platform} with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                hashtags = self._parse_hashtags_response(response.text)
                logger.info(f"Generated {len(hashtags)} hashtags")
                return hashtags
            else:
                logger.error("Empty response from Gemini for hashtags")
                return self._create_fallback_hashtags(title)
                
        except Exception as e:
            logger.error(f"Error generating hashtags with Gemini: {e}")
            return self._create_fallback_hashtags(title)

    async def generate_title_variations(
        self,
        title: str,
        content: str,
        platform: str = "youtube"
    ) -> List[str]:
        """Generate title variations optimized for platform using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_title_variations_prompt(title, content, platform)
            
            logger.info(f"Generating title variations for {platform} with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                title_variations = self._parse_title_variations_response(response.text)
                logger.info(f"Generated {len(title_variations)} title variations")
                return title_variations
            else:
                logger.error("Empty response from Gemini for title variations")
                return self._create_fallback_title_variations(title)
                
        except Exception as e:
            logger.error(f"Error generating title variations with Gemini: {e}")
            return self._create_fallback_title_variations(title)

    async def generate_description_variations(
        self,
        description: str,
        content: str,
        platform: str = "youtube"
    ) -> List[str]:
        """Generate description variations optimized for platform using Gemini."""
        try:
            model = genai.GenerativeModel(
                model_name=self.analysis_model,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            prompt = self._create_description_variations_prompt(description, content, platform)
            
            logger.info(f"Generating description variations for {platform} with Gemini")
            response = await asyncio.to_thread(model.generate_content, prompt)
            
            if response.text:
                description_variations = self._parse_description_variations_response(response.text)
                logger.info(f"Generated {len(description_variations)} description variations")
                return description_variations
            else:
                logger.error("Empty response from Gemini for description variations")
                return self._create_fallback_description_variations(description)
                
        except Exception as e:
            logger.error(f"Error generating description variations with Gemini: {e}")
            return self._create_fallback_description_variations(description)

    # Prompt creation methods for new features

    def _create_youtube_seo_prompt(self, content: str, title: str, description: str) -> str:
        """Create prompt for YouTube SEO metadata generation."""
        return f"""
You are a YouTube SEO expert. Generate optimized metadata for a video to maximize discoverability and engagement.

Video Content: {content}
Current Title: {title}
Current Description: {description}

Generate SEO-optimized metadata including:
1. Optimized title (60 characters max, engaging, keyword-rich)
2. Optimized description (125 words, includes keywords naturally)
3. Relevant tags (10-15 tags, mix of broad and specific)
4. Category suggestion
5. Target keywords (5-8 primary keywords)
6. Engagement hooks (compelling opening lines)

Format as JSON:
{{
  "optimized_title": "SEO-optimized title here",
  "optimized_description": "SEO-optimized description here",
  "tags": ["tag1", "tag2", "tag3"],
  "category": "Education/Science/Technology",
  "target_keywords": ["keyword1", "keyword2"],
  "engagement_hooks": ["Hook 1", "Hook 2"],
  "seo_score": 85,
  "recommendations": ["Recommendation 1", "Recommendation 2"]
}}

Focus on educational content optimization, research paper topics, and academic engagement.
"""

    def _create_audio_description_prompt(self, content: str, title: str, cinematic_settings: Dict[str, Any]) -> str:
        """Create prompt for audio description generation."""
        return f"""
You are an accessibility expert specializing in audio descriptions for educational videos.

Video Content: {content}
Video Title: {title}
Cinematic Settings: {cinematic_settings}

Generate audio descriptions that:
1. Describe visual elements not conveyed through narration
2. Include camera movements, visual effects, and on-screen text
3. Describe mathematical equations, diagrams, and charts
4. Note color changes, animations, and transitions
5. Provide context for visual metaphors and illustrations

Each description should include:
- Start time (seconds)
- End time (seconds)
- Description text (concise, clear)
- Priority level (essential/important/supplementary)

Format as JSON array:
[
  {{
    "start_time": 5.0,
    "end_time": 8.0,
    "description": "A blue mathematical equation appears on screen showing E=mcÂ²",
    "priority": "essential"
  }}
]

Focus on educational content accessibility and WCAG 2.1 AA compliance.
"""

    def _create_thumbnail_suggestion_prompt(self, content: str, title: str, style: str) -> str:
        """Create prompt for thumbnail suggestion generation."""
        return f"""
You are a YouTube thumbnail design expert. Generate engaging thumbnail concepts for educational content.

Video Content: {content}
Video Title: {title}
Desired Style: {style}

Generate 5 thumbnail concepts that:
1. Are visually striking and clickable
2. Clearly represent the content
3. Include readable text elements
4. Use educational/professional color schemes
5. Appeal to academic and general audiences

For each concept, provide:
- Main visual element
- Text overlay (if any)
- Color scheme
- Composition layout
- Target emotion/reaction

Format as JSON array:
[
  {{
    "concept_id": 1,
    "main_visual": "Large mathematical equation with glowing effect",
    "text_overlay": "BREAKTHROUGH!",
    "color_scheme": ["#1E3A8A", "#FFFFFF", "#F59E0B"],
    "layout": "centered_equation_with_text_bottom",
    "target_emotion": "curiosity",
    "description": "Detailed description of the thumbnail concept"
  }}
]

Focus on educational content that attracts both academic and general audiences.
"""

    def _create_seo_metadata_prompt(self, content: str, title: str, description: str, target_keywords: List[str], platform: str) -> str:
        """Create prompt for SEO metadata generation."""
        return f"""
You are an SEO expert for {platform}. Generate optimized metadata for maximum discoverability.

Content: {content}
Title: {title}
Description: {description}
Target Keywords: {target_keywords}
Platform: {platform}

Generate platform-optimized metadata:
1. SEO title (platform character limits)
2. Meta description (engaging, keyword-rich)
3. Tags/hashtags (platform-appropriate)
4. Category/topic classification
5. Audience targeting suggestions
6. Content optimization recommendations

Format as JSON:
{{
  "seo_title": "Optimized title",
  "meta_description": "Optimized description",
  "tags": ["tag1", "tag2"],
  "category": "category",
  "audience_targeting": ["audience1", "audience2"],
  "optimization_score": 90,
  "recommendations": ["rec1", "rec2"]
}}

Optimize for {platform} algorithm and user behavior patterns.
"""

    def _create_hashtag_generation_prompt(self, content: str, title: str, platform: str) -> str:
        """Create prompt for hashtag generation."""
        return f"""
You are a social media expert for {platform}. Generate relevant hashtags for educational content.

Content: {content}
Title: {title}
Platform: {platform}

Generate hashtags that:
1. Are relevant to the content
2. Mix popular and niche tags
3. Include educational/academic tags
4. Follow platform best practices
5. Target appropriate audiences

Provide 15-20 hashtags in order of relevance.

Format as JSON array:
["#hashtag1", "#hashtag2", "#hashtag3"]

Focus on educational content discovery and academic engagement.
"""

    def _create_title_variations_prompt(self, title: str, content: str, platform: str) -> str:
        """Create prompt for title variations generation."""
        return f"""
You are a content optimization expert for {platform}. Generate engaging title variations.

Original Title: {title}
Content: {content}
Platform: {platform}

Generate 8 title variations that:
1. Maintain the core message
2. Use different engagement strategies
3. Optimize for platform algorithms
4. Appeal to different audience segments
5. Include power words and emotional triggers

Variation types:
- Question-based
- Benefit-focused
- Curiosity-driven
- Authority-based
- Problem-solution
- Number/list-based
- Urgency-creating
- Educational-focused

Format as JSON array:
["Title variation 1", "Title variation 2"]

Optimize for {platform} user behavior and engagement patterns.
"""

    def _create_description_variations_prompt(self, description: str, content: str, platform: str) -> str:
        """Create prompt for description variations generation."""
        return f"""
You are a content marketing expert for {platform}. Generate optimized description variations.

Original Description: {description}
Content: {content}
Platform: {platform}

Generate 5 description variations that:
1. Optimize for platform algorithms
2. Include relevant keywords naturally
3. Have strong opening hooks
4. Include calls-to-action
5. Appeal to target audiences

Variation focuses:
- SEO-optimized
- Engagement-focused
- Educational-formal
- Conversational-casual
- Benefit-driven

Format as JSON array:
["Description variation 1", "Description variation 2"]

Optimize for {platform} discovery and user engagement.
"""

    # Response parsing methods for new features

    def _parse_seo_metadata_response(self, response_text: str) -> Dict[str, Any]:
        """Parse SEO metadata generation response."""
        try:
            import json
            # Try to extract JSON from response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback parsing
                return self._create_fallback_seo_metadata("Unknown Title", "Unknown Description")
        except Exception as e:
            logger.error(f"Error parsing SEO metadata response: {e}")
            return self._create_fallback_seo_metadata("Unknown Title", "Unknown Description")

    def _parse_audio_descriptions_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse audio descriptions generation response."""
        try:
            import json
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return self._create_fallback_audio_descriptions("Unknown content")
        except Exception as e:
            logger.error(f"Error parsing audio descriptions response: {e}")
            return self._create_fallback_audio_descriptions("Unknown content")

    def _parse_thumbnail_suggestions_response(self, response_text: str) -> List[Dict[str, Any]]:
        """Parse thumbnail suggestions generation response."""
        try:
            import json
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                return self._create_fallback_thumbnail_suggestions("Unknown Title")
        except Exception as e:
            logger.error(f"Error parsing thumbnail suggestions response: {e}")
            return self._create_fallback_thumbnail_suggestions("Unknown Title")

    def _parse_hashtags_response(self, response_text: str) -> List[str]:
        """Parse hashtags generation response."""
        try:
            import json
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: extract hashtags from text
                hashtags = []
                for line in response_text.split('\n'):
                    if '#' in line:
                        tags = [tag.strip() for tag in line.split() if tag.startswith('#')]
                        hashtags.extend(tags)
                return hashtags[:20] if hashtags else self._create_fallback_hashtags("Unknown")
        except Exception as e:
            logger.error(f"Error parsing hashtags response: {e}")
            return self._create_fallback_hashtags("Unknown")

    def _parse_title_variations_response(self, response_text: str) -> List[str]:
        """Parse title variations generation response."""
        try:
            import json
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: extract titles from numbered list
                titles = []
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('â€¢')):
                        # Remove numbering and clean up
                        title = line.split('.', 1)[-1].strip()
                        if title:
                            titles.append(title)
                return titles[:8] if titles else self._create_fallback_title_variations("Unknown Title")
        except Exception as e:
            logger.error(f"Error parsing title variations response: {e}")
            return self._create_fallback_title_variations("Unknown Title")

    def _parse_description_variations_response(self, response_text: str) -> List[str]:
        """Parse description variations generation response."""
        try:
            import json
            # Try to extract JSON array from response
            json_start = response_text.find('[')
            json_end = response_text.rfind(']') + 1
            if json_start != -1 and json_end > json_start:
                json_str = response_text[json_start:json_end]
                return json.loads(json_str)
            else:
                # Fallback: extract descriptions from numbered list
                descriptions = []
                current_desc = ""
                for line in response_text.split('\n'):
                    line = line.strip()
                    if line and (line[0].isdigit() or line.startswith('-') or line.startswith('â€¢')):
                        if current_desc:
                            descriptions.append(current_desc.strip())
                        current_desc = line.split('.', 1)[-1].strip()
                    elif current_desc and line:
                        current_desc += " " + line
                if current_desc:
                    descriptions.append(current_desc.strip())
                return descriptions[:5] if descriptions else self._create_fallback_description_variations("Unknown Description")
        except Exception as e:
            logger.error(f"Error parsing description variations response: {e}")
            return self._create_fallback_description_variations("Unknown Description")

    # Fallback methods for new features

    def _create_fallback_seo_metadata(self, title: str, description: str) -> Dict[str, Any]:
        """Create fallback SEO metadata when Gemini fails."""
        return {
            "optimized_title": title[:60],
            "optimized_description": description[:125] if description else "Educational content about " + title,
            "tags": ["education", "research", "science", "learning"],
            "category": "Education",
            "target_keywords": ["education", "research"],
            "engagement_hooks": ["Learn about " + title, "Discover the science behind " + title],
            "seo_score": 60,
            "recommendations": ["Add more specific keywords", "Include call-to-action"]
        }

    def _create_fallback_audio_descriptions(self, content: str) -> List[Dict[str, Any]]:
        """Create fallback audio descriptions when Gemini fails."""
        return [
            {
                "start_time": 0.0,
                "end_time": 5.0,
                "description": "Educational content begins with visual elements on screen",
                "priority": "essential"
            },
            {
                "start_time": 5.0,
                "end_time": 10.0,
                "description": "Text and diagrams appear to illustrate key concepts",
                "priority": "important"
            }
        ]

    def _create_fallback_thumbnail_suggestions(self, title: str) -> List[Dict[str, Any]]:
        """Create fallback thumbnail suggestions when Gemini fails."""
        return [
            {
                "concept_id": 1,
                "main_visual": "Bold title text with educational background",
                "text_overlay": title[:20],
                "color_scheme": ["#1E3A8A", "#FFFFFF", "#F59E0B"],
                "layout": "centered_text",
                "target_emotion": "curiosity",
                "description": "Simple, clean design with focus on title"
            }
        ]

    def _create_fallback_hashtags(self, title: str) -> List[str]:
        """Create fallback hashtags when Gemini fails."""
        return [
            "#education", "#research", "#science", "#learning", "#academic",
            "#knowledge", "#study", "#educational", "#facts", "#discovery"
        ]

    def _create_fallback_title_variations(self, title: str) -> List[str]:
        """Create fallback title variations when Gemini fails."""
        return [
            f"Learn About {title}",
            f"Understanding {title}",
            f"The Science of {title}",
            f"Exploring {title}",
            f"{title} Explained"
        ]

    def _create_fallback_description_variations(self, description: str) -> List[str]:
        """Create fallback description variations when Gemini fails."""
        base_desc = description if description else "Educational content"
        return [
            f"{base_desc} - Learn more in this educational video.",
            f"Discover the fascinating world of {base_desc.lower()}.",
            f"Educational content about {base_desc.lower()} for students and researchers.",
            f"Explore {base_desc.lower()} with clear explanations and examples.",
            f"Understanding {base_desc.lower()} made simple and accessible."
        ]


# Global enhanced Gemini client instance
_enhanced_gemini_client = None

def get_enhanced_gemini_client() -> EnhancedGeminiClient:
    """Get global enhanced Gemini client instance."""
    global _enhanced_gemini_client
    if _enhanced_gemini_client is None:
        _enhanced_gemini_client = EnhancedGeminiClient()
    return _enhanced_gemini_client
