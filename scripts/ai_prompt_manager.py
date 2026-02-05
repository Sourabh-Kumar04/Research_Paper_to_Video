"""
AI Prompt Manager for RASO Platform

This module provides specialized AI prompts and templates for different types
of content generation, including Manim code generation and educational content.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class PromptType(Enum):
    """Types of AI prompts."""
    MANIM_CODE = "manim_code"
    EDUCATIONAL_CONTENT = "educational_content"
    SCRIPT_GENERATION = "script_generation"
    CONTENT_ANALYSIS = "content_analysis"
    VISUAL_SUGGESTIONS = "visual_suggestions"
    CODE_VALIDATION = "code_validation"


class ContentDifficulty(Enum):
    """Content difficulty levels."""
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class AnimationType(Enum):
    """Types of animations for Manim."""
    EQUATION = "equation"
    GRAPH = "graph"
    GEOMETRIC = "geometric"
    TRANSFORMATION = "transformation"
    TEXT_ANIMATION = "text_animation"
    COMPLEX_SCENE = "complex_scene"


@dataclass
class PromptTemplate:
    """Template for AI prompts."""
    name: str
    prompt_type: PromptType
    template: str
    variables: List[str]
    examples: List[Dict[str, str]]
    model_preferences: List[str]  # Preferred models for this prompt
    temperature: float = 0.3
    max_tokens: int = 2048
    description: str = ""
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


@dataclass
class FewShotExample:
    """Few-shot learning example."""
    input_text: str
    expected_output: str
    explanation: str
    difficulty: ContentDifficulty
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class AIPromptManager:
    """Manages AI prompts and templates for content generation."""
    
    def __init__(self):
        self.prompt_templates: Dict[str, PromptTemplate] = {}
        self.few_shot_examples: Dict[PromptType, List[FewShotExample]] = {}
        self.prompt_cache: Dict[str, str] = {}
        self._initialize_templates()
        self._initialize_few_shot_examples()
    
    def _initialize_templates(self):
        """Initialize default prompt templates."""
        
        # Manim Code Generation Templates
        self.prompt_templates["manim_equation"] = PromptTemplate(
            name="Manim Equation Animation",
            prompt_type=PromptType.MANIM_CODE,
            template="""You are an expert Manim developer. Generate clean, well-commented Manim code for animating mathematical equations.

REQUIREMENTS:
- Use Manim Community Edition (latest version)
- Follow Python best practices
- Include proper imports
- Add meaningful comments
- Ensure the animation is educational and clear
- Use appropriate colors and styling
- Animation duration should be around {duration} seconds

CONTENT TO ANIMATE:
Title: {title}
Equation/Formula: {equation}
Context: {context}
Difficulty Level: {difficulty}

ANIMATION TYPE: {animation_type}

STYLE PREFERENCES:
- Background: {background_color}
- Primary Color: {primary_color}
- Text Color: {text_color}
- Font Size: {font_size}

Generate complete Manim code that creates an educational animation. Include:
1. Proper class definition inheriting from Scene
2. Clear step-by-step animation
3. Appropriate timing and transitions
4. Educational explanations as text

EXAMPLE OUTPUT FORMAT:
```python
from manim import *

class EquationAnimation(Scene):
    def construct(self):
        # Your animation code here
        pass
```

Generate the Manim code now:""",
            variables=["title", "equation", "context", "difficulty", "animation_type", "duration", 
                      "background_color", "primary_color", "text_color", "font_size"],
            examples=[],
            model_preferences=["codeqwen1.5-7b", "deepseek-coder-6.7b", "qwen2.5-7b"],
            temperature=0.2,
            max_tokens=2048,
            description="Generate Manim code for equation animations",
            tags=["manim", "equations", "mathematics", "animation"]
        )
        
        self.prompt_templates["manim_graph"] = PromptTemplate(
            name="Manim Graph Animation",
            prompt_type=PromptType.MANIM_CODE,
            template="""You are an expert Manim developer. Generate clean, well-commented Manim code for animating mathematical graphs and functions.

REQUIREMENTS:
- Use Manim Community Edition
- Create smooth, educational animations
- Include axis labels and grid if appropriate
- Show function transformation step by step
- Use appropriate colors and styling
- Animation duration should be around {duration} seconds

CONTENT TO ANIMATE:
Title: {title}
Function/Graph: {function}
Context: {context}
Difficulty Level: {difficulty}
Graph Type: {graph_type}

ANIMATION FEATURES:
- Show axes: {show_axes}
- Show grid: {show_grid}
- Animate drawing: {animate_drawing}
- Show transformations: {show_transformations}

STYLE PREFERENCES:
- Background: {background_color}
- Function Color: {function_color}
- Axes Color: {axes_color}

Generate complete Manim code for the graph animation:""",
            variables=["title", "function", "context", "difficulty", "graph_type", "duration",
                      "show_axes", "show_grid", "animate_drawing", "show_transformations",
                      "background_color", "function_color", "axes_color"],
            examples=[],
            model_preferences=["codeqwen1.5-7b", "deepseek-coder-6.7b"],
            temperature=0.2,
            max_tokens=2048,
            description="Generate Manim code for graph animations",
            tags=["manim", "graphs", "functions", "mathematics"]
        )
        
        self.prompt_templates["manim_geometric"] = PromptTemplate(
            name="Manim Geometric Animation",
            prompt_type=PromptType.MANIM_CODE,
            template="""You are an expert Manim developer. Generate clean, well-commented Manim code for geometric animations and transformations.

REQUIREMENTS:
- Use Manim Community Edition
- Create clear geometric visualizations
- Show step-by-step transformations
- Include proper labeling
- Use educational pacing
- Animation duration should be around {duration} seconds

CONTENT TO ANIMATE:
Title: {title}
Geometric Concept: {concept}
Context: {context}
Shapes Involved: {shapes}
Transformations: {transformations}

ANIMATION STYLE:
- Show construction: {show_construction}
- Highlight properties: {highlight_properties}
- Use colors: {use_colors}

Generate complete Manim code for the geometric animation:""",
            variables=["title", "concept", "context", "shapes", "transformations", "duration",
                      "show_construction", "highlight_properties", "use_colors"],
            examples=[],
            model_preferences=["codeqwen1.5-7b", "deepseek-coder-6.7b"],
            temperature=0.2,
            max_tokens=2048,
            description="Generate Manim code for geometric animations",
            tags=["manim", "geometry", "shapes", "transformations"]
        )
        
        # Educational Content Templates
        self.prompt_templates["educational_script"] = PromptTemplate(
            name="Educational Script Generation",
            prompt_type=PromptType.EDUCATIONAL_CONTENT,
            template="""You are an expert educational content creator. Generate engaging, clear, and pedagogically sound educational scripts.

CONTENT REQUIREMENTS:
- Target Audience: {audience_level}
- Subject: {subject}
- Topic: {topic}
- Duration: {duration} minutes
- Learning Objectives: {learning_objectives}

SCRIPT STRUCTURE:
1. Hook/Introduction (10-15% of time)
2. Main Content (70-80% of time)
3. Summary/Conclusion (10-15% of time)

PEDAGOGICAL PRINCIPLES:
- Start with what students know
- Use clear, simple language appropriate for {audience_level} level
- Include concrete examples and analogies
- Build concepts progressively
- Include interactive elements or questions
- Provide clear transitions between concepts

CONTENT CONTEXT:
{content_context}

STYLE PREFERENCES:
- Tone: {tone}
- Engagement Level: {engagement_level}
- Include Examples: {include_examples}
- Use Analogies: {use_analogies}

Generate a complete educational script that is engaging, clear, and pedagogically effective:""",
            variables=["audience_level", "subject", "topic", "duration", "learning_objectives",
                      "content_context", "tone", "engagement_level", "include_examples", "use_analogies"],
            examples=[],
            model_preferences=["qwen2.5-7b", "qwen2.5-14b", "llama3.2-3b"],
            temperature=0.4,
            max_tokens=3000,
            description="Generate educational scripts for video content",
            tags=["education", "script", "pedagogy", "learning"]
        )
        
        self.prompt_templates["content_analysis"] = PromptTemplate(
            name="Content Analysis and Enhancement",
            prompt_type=PromptType.CONTENT_ANALYSIS,
            template="""You are an expert content analyst and educational designer. Analyze the given content and provide detailed insights and recommendations.

CONTENT TO ANALYZE:
Title: {title}
Content: {content}
Target Audience: {target_audience}
Subject Area: {subject_area}

ANALYSIS REQUIREMENTS:
1. Content Type Classification
2. Complexity Level Assessment
3. Key Concepts Identification
4. Learning Objectives Extraction
5. Visual Elements Suggestions
6. Engagement Opportunities
7. Improvement Recommendations

ANALYSIS FRAMEWORK:
- Pedagogical Effectiveness
- Content Clarity
- Audience Appropriateness
- Visual Learning Opportunities
- Interactive Elements Potential

Provide a comprehensive analysis in JSON format:
{{
    "content_type": "...",
    "complexity_level": "...",
    "key_concepts": [...],
    "learning_objectives": [...],
    "visual_suggestions": [...],
    "engagement_opportunities": [...],
    "improvement_recommendations": [...],
    "estimated_duration": "...",
    "prerequisite_knowledge": [...],
    "assessment_suggestions": [...]
}}

Analyze the content now:""",
            variables=["title", "content", "target_audience", "subject_area"],
            examples=[],
            model_preferences=["qwen2.5-7b", "qwen2.5-14b"],
            temperature=0.3,
            max_tokens=2048,
            description="Analyze content for educational effectiveness",
            tags=["analysis", "education", "content", "assessment"]
        )
        
        self.prompt_templates["visual_suggestions"] = PromptTemplate(
            name="Visual Content Suggestions",
            prompt_type=PromptType.VISUAL_SUGGESTIONS,
            template="""You are an expert visual learning designer. Analyze the content and suggest specific visual elements that would enhance learning.

CONTENT TO ANALYZE:
Title: {title}
Content: {content}
Subject: {subject}
Audience Level: {audience_level}
Duration: {duration} minutes

VISUAL ANALYSIS REQUIREMENTS:
1. Identify concepts that benefit from visualization
2. Suggest specific animation types
3. Recommend visual metaphors and analogies
4. Propose interactive elements
5. Consider cognitive load and visual hierarchy

AVAILABLE VISUAL TOOLS:
- Manim (mathematical animations)
- Motion Canvas (concept diagrams, flowcharts)
- Charts and Graphs (data visualization)
- 3D Visualizations (molecular, network, geometric)

Provide detailed visual suggestions in JSON format:
{{
    "visual_concepts": [
        {{
            "concept": "...",
            "visual_type": "manim|motion_canvas|chart|3d",
            "animation_type": "...",
            "description": "...",
            "timing": "...",
            "importance": "high|medium|low"
        }}
    ],
    "visual_metaphors": [...],
    "color_scheme_suggestions": {{...}},
    "layout_recommendations": [...],
    "interactive_elements": [...],
    "accessibility_considerations": [...]
}}

Generate visual suggestions now:""",
            variables=["title", "content", "subject", "audience_level", "duration"],
            examples=[],
            model_preferences=["qwen2.5-7b", "qwen2-vl-7b"],
            temperature=0.4,
            max_tokens=2048,
            description="Generate visual content suggestions for educational material",
            tags=["visual", "design", "animation", "learning"]
        )
        
        self.prompt_templates["code_validation"] = PromptTemplate(
            name="Code Validation and Improvement",
            prompt_type=PromptType.CODE_VALIDATION,
            template="""You are an expert code reviewer specializing in Manim and educational animation code. Review and improve the given code.

CODE TO REVIEW:
```python
{code}
```

REVIEW CRITERIA:
1. Syntax and Runtime Correctness
2. Manim Best Practices
3. Code Clarity and Comments
4. Educational Effectiveness
5. Performance Optimization
6. Visual Appeal

CONTEXT:
- Purpose: {purpose}
- Target Audience: {target_audience}
- Animation Duration: {duration} seconds

REVIEW REQUIREMENTS:
- Check for common Manim errors
- Suggest improvements for educational clarity
- Optimize animation timing
- Improve code structure and readability
- Ensure proper imports and dependencies

Provide review results in JSON format:
{{
    "is_valid": true/false,
    "syntax_errors": [...],
    "warnings": [...],
    "suggestions": [...],
    "improved_code": "...",
    "educational_improvements": [...],
    "performance_notes": [...]
}}

Review the code now:""",
            variables=["code", "purpose", "target_audience", "duration"],
            examples=[],
            model_preferences=["codeqwen1.5-7b", "deepseek-coder-6.7b"],
            temperature=0.2,
            max_tokens=3000,
            description="Validate and improve Manim animation code",
            tags=["validation", "code_review", "manim", "improvement"]
        )
    
    def _initialize_few_shot_examples(self):
        """Initialize few-shot learning examples."""
        
        # Manim Code Examples
        manim_examples = [
            FewShotExample(
                input_text="Create a simple animation showing the quadratic formula: x = (-b ± √(b²-4ac)) / 2a",
                expected_output="""```python
from manim import *

class QuadraticFormulaAnimation(Scene):
    def construct(self):
        # Title
        title = Text("Quadratic Formula", font_size=48)
        title.to_edge(UP)
        self.play(Write(title))
        self.wait(1)
        
        # The quadratic equation
        equation = MathTex("ax^2 + bx + c = 0")
        equation.next_to(title, DOWN, buff=1)
        self.play(Write(equation))
        self.wait(1)
        
        # The quadratic formula
        formula = MathTex(
            "x = \\\\frac{-b \\\\pm \\\\sqrt{b^2 - 4ac}}{2a}"
        )
        formula.next_to(equation, DOWN, buff=1.5)
        
        # Animate the formula appearance
        self.play(Write(formula))
        self.wait(2)
        
        # Highlight parts of the formula
        discriminant = formula[0][8:13]  # b² - 4ac part
        self.play(Indicate(discriminant, color=YELLOW))
        self.wait(1)
        
        # Add explanation text
        explanation = Text(
            "The discriminant determines the nature of roots",
            font_size=24
        )
        explanation.next_to(formula, DOWN, buff=1)
        self.play(Write(explanation))
        self.wait(2)
```""",
                explanation="Simple equation animation with highlighting and explanation",
                difficulty=ContentDifficulty.BEGINNER,
                tags=["equation", "mathematics", "formula"]
            ),
            
            FewShotExample(
                input_text="Animate a sine wave function y = sin(x) being drawn from 0 to 2π",
                expected_output="""```python
from manim import *
import numpy as np

class SineWaveAnimation(Scene):
    def construct(self):
        # Set up axes
        axes = Axes(
            x_range=[0, 2*PI, PI/2],
            y_range=[-1.5, 1.5, 0.5],
            x_length=10,
            y_length=6,
            axis_config={"color": BLUE},
            x_axis_config={
                "numbers_to_include": np.arange(0, 2*PI + 0.1, PI/2),
                "numbers_with_elongated_ticks": np.arange(0, 2*PI + 0.1, PI),
            },
            tips=False,
        )
        
        # Labels
        axes_labels = axes.get_axis_labels(x_label="x", y_label="y")
        
        # Sine function
        sine_graph = axes.plot(lambda x: np.sin(x), color=RED, x_range=[0, 2*PI])
        sine_label = axes.get_graph_label(sine_graph, "y = \\\\sin(x)", x_val=PI, direction=UP)
        
        # Animation sequence
        self.play(Create(axes), Write(axes_labels))
        self.wait(1)
        
        # Draw the sine wave progressively
        self.play(Create(sine_graph), run_time=3)
        self.wait(1)
        
        # Add label
        self.play(Write(sine_label))
        self.wait(2)
        
        # Highlight key points
        key_points = [
            axes.coords_to_point(0, 0),
            axes.coords_to_point(PI/2, 1),
            axes.coords_to_point(PI, 0),
            axes.coords_to_point(3*PI/2, -1),
            axes.coords_to_point(2*PI, 0),
        ]
        
        dots = [Dot(point, color=YELLOW) for point in key_points]
        self.play(*[Create(dot) for dot in dots])
        self.wait(2)
```""",
                explanation="Graph animation with axes, progressive drawing, and key point highlighting",
                difficulty=ContentDifficulty.INTERMEDIATE,
                tags=["graph", "function", "sine", "animation"]
            ),
            
            FewShotExample(
                input_text="Show the geometric transformation of a square being rotated 45 degrees",
                expected_output="""```python
from manim import *

class SquareRotationAnimation(Scene):
    def construct(self):
        # Create a square
        square = Square(side_length=3, color=BLUE, fill_opacity=0.3)
        square.set_stroke(BLUE, width=3)
        
        # Title
        title = Text("Square Rotation: 45°", font_size=36)
        title.to_edge(UP)
        
        # Show initial square
        self.play(Write(title))
        self.play(Create(square))
        self.wait(1)
        
        # Add angle indicator
        angle_arc = Arc(
            start_angle=0,
            angle=PI/4,
            radius=1,
            color=YELLOW
        )
        angle_label = MathTex("45°", color=YELLOW, font_size=24)
        angle_label.next_to(angle_arc, RIGHT, buff=0.1)
        
        # Show rotation
        self.play(
            Rotate(square, PI/4),
            Create(angle_arc),
            Write(angle_label),
            run_time=2
        )
        self.wait(1)
        
        # Add explanation
        explanation = Text(
            "The square rotates 45° counterclockwise",
            font_size=24
        )
        explanation.to_edge(DOWN)
        self.play(Write(explanation))
        self.wait(2)
```""",
                explanation="Geometric transformation with visual angle indicator and explanation",
                difficulty=ContentDifficulty.BEGINNER,
                tags=["geometry", "transformation", "rotation", "square"]
            )
        ]
        
        self.few_shot_examples[PromptType.MANIM_CODE] = manim_examples
        
        # Educational Content Examples
        educational_examples = [
            FewShotExample(
                input_text="Create an introduction script for explaining photosynthesis to middle school students",
                expected_output="""**Introduction to Photosynthesis**

*[Duration: 2 minutes]*

**Hook (20 seconds):**
"Have you ever wondered how plants make their own food? Unlike us, they don't need to go to the grocery store or order takeout! Today, we're going to discover the amazing process that allows plants to create their own energy using just sunlight, water, and air. It's like having a solar-powered kitchen right inside every leaf!"

**Main Content (1 minute 20 seconds):**
"Photosynthesis is nature's way of converting sunlight into food energy. Let's break this down into simple steps:

First, plants collect sunlight through their leaves - think of leaves as tiny solar panels. The green color you see comes from chlorophyll, which is like the plant's solar collector.

Second, plants absorb water through their roots from the soil. This water travels up through the stem to the leaves, like drinking through a straw.

Third, plants take in carbon dioxide from the air through tiny pores in their leaves called stomata - these are like the plant's breathing holes.

Now here's where the magic happens: Inside the leaves, chlorophyll uses the energy from sunlight to combine water and carbon dioxide, creating glucose (plant sugar) and releasing oxygen as a bonus!"

**Conclusion (20 seconds):**
"So remember: Sunlight + Water + Carbon Dioxide = Plant Food + Oxygen. This process not only feeds the plant but also gives us the oxygen we breathe. Pretty amazing that plants are basically solar-powered food factories that also clean our air!"

*[Visual cues: Show leaf cross-section, water movement, sunlight rays, CO2 molecules, and oxygen bubbles]*""",
                explanation="Engaging educational script with clear structure, age-appropriate language, and visual cues",
                difficulty=ContentDifficulty.INTERMEDIATE,
                tags=["education", "biology", "middle_school", "script"]
            )
        ]
        
        self.few_shot_examples[PromptType.EDUCATIONAL_CONTENT] = educational_examples
    
    def get_prompt_template(self, template_name: str) -> Optional[PromptTemplate]:
        """Get a specific prompt template."""
        return self.prompt_templates.get(template_name)
    
    def list_templates(self, prompt_type: Optional[PromptType] = None) -> List[str]:
        """List available templates, optionally filtered by type."""
        if prompt_type:
            return [name for name, template in self.prompt_templates.items() 
                   if template.prompt_type == prompt_type]
        return list(self.prompt_templates.keys())
    
    def generate_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        include_examples: bool = True,
        num_examples: int = 2
    ) -> Optional[str]:
        """Generate a prompt from a template with variables."""
        template = self.prompt_templates.get(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return None
        
        try:
            # Fill in template variables
            prompt = template.template.format(**variables)
            
            # Add few-shot examples if requested
            if include_examples and template.prompt_type in self.few_shot_examples:
                examples = self.few_shot_examples[template.prompt_type][:num_examples]
                if examples:
                    examples_text = "\n\nHERE ARE SOME EXAMPLES:\n\n"
                    for i, example in enumerate(examples, 1):
                        examples_text += f"**Example {i}:**\n"
                        examples_text += f"Input: {example.input_text}\n"
                        examples_text += f"Output: {example.expected_output}\n"
                        examples_text += f"Explanation: {example.explanation}\n\n"
                    
                    # Insert examples before the final instruction
                    prompt = prompt.replace("Generate", examples_text + "Now generate")
            
            return prompt
            
        except KeyError as e:
            logger.error(f"Missing variable {e} for template '{template_name}'")
            return None
    
    def validate_prompt_variables(self, template_name: str, variables: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate that all required variables are provided."""
        template = self.prompt_templates.get(template_name)
        if not template:
            return False, [f"Template '{template_name}' not found"]
        
        missing_vars = []
        for var in template.variables:
            if var not in variables:
                missing_vars.append(var)
        
        return len(missing_vars) == 0, missing_vars
    
    def add_few_shot_example(
        self,
        prompt_type: PromptType,
        example: FewShotExample
    ) -> None:
        """Add a new few-shot example."""
        if prompt_type not in self.few_shot_examples:
            self.few_shot_examples[prompt_type] = []
        
        self.few_shot_examples[prompt_type].append(example)
        logger.info(f"Added few-shot example for {prompt_type.value}")
    
    def optimize_prompt(
        self,
        template_name: str,
        variables: Dict[str, Any],
        target_model: str
    ) -> Optional[str]:
        """Optimize prompt for a specific model."""
        template = self.prompt_templates.get(template_name)
        if not template:
            return None
        
        # Generate base prompt
        prompt = self.generate_prompt(template_name, variables)
        if not prompt:
            return None
        
        # Model-specific optimizations
        if "codeqwen" in target_model.lower() or "deepseek" in target_model.lower():
            # For coding models, emphasize code quality and best practices
            prompt = prompt.replace(
                "Generate", 
                "Generate high-quality, production-ready"
            )
            prompt += "\n\nIMPORTANT: Follow Python PEP 8 style guidelines and include comprehensive comments."
        
        elif "qwen2.5" in target_model.lower():
            # For reasoning models, emphasize clarity and explanation
            prompt += "\n\nIMPORTANT: Provide clear explanations and reasoning for your choices."
        
        elif "llama" in target_model.lower():
            # For Llama models, use more structured format
            prompt = prompt.replace("\n\n", "\n\n### ")
        
        return prompt
    
    def get_model_preferences(self, template_name: str) -> List[str]:
        """Get preferred models for a template."""
        template = self.prompt_templates.get(template_name)
        return template.model_preferences if template else []
    
    def save_templates(self, filepath: str) -> bool:
        """Save templates to a JSON file."""
        try:
            templates_data = {}
            for name, template in self.prompt_templates.items():
                templates_data[name] = asdict(template)
                # Convert enums to strings
                templates_data[name]['prompt_type'] = template.prompt_type.value
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(templates_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Templates saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save templates: {e}")
            return False
    
    def load_templates(self, filepath: str) -> bool:
        """Load templates from a JSON file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                templates_data = json.load(f)
            
            for name, data in templates_data.items():
                # Convert string back to enum
                data['prompt_type'] = PromptType(data['prompt_type'])
                
                # Create PromptTemplate object
                template = PromptTemplate(**data)
                self.prompt_templates[name] = template
            
            logger.info(f"Templates loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load templates: {e}")
            return False
    
    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template."""
        template = self.prompt_templates.get(template_name)
        if not template:
            return None
        
        return {
            "name": template.name,
            "type": template.prompt_type.value,
            "description": template.description,
            "variables": template.variables,
            "model_preferences": template.model_preferences,
            "temperature": template.temperature,
            "max_tokens": template.max_tokens,
            "tags": template.tags,
            "example_count": len(self.few_shot_examples.get(template.prompt_type, []))
        }
    
    def search_templates(self, query: str, tags: List[str] = None) -> List[str]:
        """Search templates by name, description, or tags."""
        results = []
        query_lower = query.lower()
        
        for name, template in self.prompt_templates.items():
            # Search in name and description
            if (query_lower in name.lower() or 
                query_lower in template.description.lower()):
                results.append(name)
                continue
            
            # Search in tags
            if tags:
                if any(tag in template.tags for tag in tags):
                    results.append(name)
                    continue
            
            # Search in template tags
            if any(query_lower in tag.lower() for tag in template.tags):
                results.append(name)
        
        return results


# Global instance for easy access
ai_prompt_manager = AIPromptManager()