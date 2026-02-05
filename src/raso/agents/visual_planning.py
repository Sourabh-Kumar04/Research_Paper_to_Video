"""
Visual Planning Agent for the RASO platform.

Assigns animation frameworks to content types and creates detailed scene plans
with templates, parameters, and transition coordination.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from config.backend.models import AgentType, RASOMasterState
from config.backend.models.script import NarrationScript, Scene
from config.backend.models.understanding import PaperUnderstanding
from config.backend.models.visual import VisualPlan, ScenePlan, TransitionPlan, StyleGuide
from config.backend.services.llm import llm_service
from agents.retry import retry


class AnimationFramework(str, Enum):
    """Supported animation frameworks."""
    MANIM = "manim"
    MOTION_CANVAS = "motion-canvas"
    REMOTION = "remotion"


class ContentType(str, Enum):
    """Types of content for framework assignment."""
    MATHEMATICAL = "mathematical"
    CONCEPTUAL = "conceptual"
    UI_ELEMENTS = "ui_elements"
    INTRODUCTION = "introduction"
    CONCLUSION = "conclusion"
    TRANSITION = "transition"


class FrameworkAssignmentRules:
    """Rules for assigning animation frameworks to content types."""
    
    FRAMEWORK_MAPPING = {
        ContentType.MATHEMATICAL: AnimationFramework.MANIM,
        ContentType.CONCEPTUAL: AnimationFramework.MOTION_CANVAS,
        ContentType.UI_ELEMENTS: AnimationFramework.REMOTION,
        ContentType.INTRODUCTION: AnimationFramework.REMOTION,
        ContentType.CONCLUSION: AnimationFramework.REMOTION,
        ContentType.TRANSITION: AnimationFramework.MOTION_CANVAS,
    }
    
    MATHEMATICAL_KEYWORDS = [
        "equation", "formula", "theorem", "proof", "calculation",
        "matrix", "vector", "derivative", "integral", "algorithm",
        "optimization", "function", "variable", "parameter"
    ]
    
    CONCEPTUAL_KEYWORDS = [
        "concept", "idea", "approach", "method", "process",
        "workflow", "architecture", "system", "model", "framework",
        "mechanism", "principle", "strategy", "technique"
    ]
    
    UI_KEYWORDS = [
        "interface", "dashboard", "menu", "button", "form",
        "layout", "design", "user", "interaction", "navigation",
        "title", "header", "footer", "sidebar"
    ]


class VisualPlanningPrompts:
    """Prompt templates for visual planning tasks."""
    
    SCENE_ANALYSIS = """
    Analyze the following narration script and determine the optimal animation framework for each scene.
    
    Paper Title: {title}
    
    Scenes:
    {scenes_text}
    
    Key Equations: {equations_text}
    
    Visualizable Concepts: {concepts_text}
    
    For each scene, determine:
    1. Primary content type (mathematical, conceptual, ui_elements, introduction, conclusion)
    2. Recommended animation framework (manim for math, motion-canvas for concepts, remotion for UI)
    3. Visual complexity level (simple, medium, complex)
    4. Key visual elements needed
    5. Transition requirements
    
    Assignment Rules:
    - Use Manim for mathematical equations, proofs, and calculations
    - Use Motion Canvas for conceptual diagrams, processes, and abstract ideas
    - Use Remotion for titles, introductions, conclusions, and UI elements
    
    Format as JSON:
    {{
        "scene_assignments": [
            {{
                "scene_id": "scene1",
                "content_type": "mathematical",
                "framework": "manim",
                "complexity": "medium",
                "visual_elements": ["equation animation", "step-by-step derivation"],
                "transition_in": "fade",
                "transition_out": "slide"
            }}
        ]
    }}
    """
    
    TEMPLATE_SELECTION = """
    Select appropriate animation templates for the following scene plan.
    
    Scene: {scene_title}
    Framework: {framework}
    Content Type: {content_type}
    Complexity: {complexity}
    
    Narration: {narration}
    
    Visual Elements: {visual_elements}
    
    Available Templates for {framework}:
    {available_templates}
    
    Select the most appropriate template and specify parameters:
    
    Format as JSON:
    {{
        "template_id": "equation_derivation",
        "parameters": {{
            "equation": "attention_formula",
            "steps": 4,
            "highlight_color": "blue",
            "animation_speed": "medium"
        }},
        "safety_level": "safe"
    }}
    """


class VisualPlanningAgent(BaseAgent):
    """Agent responsible for visual planning and framework assignment."""
    
    name = "VisualPlanningAgent"
    description = "Assigns animation frameworks and creates detailed scene plans"
    
    def __init__(self, agent_type: AgentType):
        """Initialize the visual planning agent."""
        super().__init__(agent_type)
        self.prompts = VisualPlanningPrompts()
        self.assignment_rules = FrameworkAssignmentRules()
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute visual planning and framework assignment.
        
        Args:
            state: Current workflow state containing script and understanding
            
        Returns:
            Updated state with visual plan
        """
        self.validate_input(state)
        
        try:
            script = state.script
            understanding = state.understanding
            
            self.log_progress("Starting visual planning", state)
            
            # For now, create a simple visual plan without LLM to test the pipeline
            # TODO: Replace with actual LLM-based planning when LLM service is configured
            
            # Create simple scene plans
            scene_plans = []
            for i, scene in enumerate(script.scenes):
                # Simple framework assignment based on scene content
                if "equation" in scene.narration.lower() or "formula" in scene.narration.lower():
                    framework = AnimationFramework.MANIM
                elif "concept" in scene.narration.lower() or "approach" in scene.narration.lower():
                    framework = AnimationFramework.MOTION_CANVAS
                else:
                    framework = AnimationFramework.REMOTION
                
                scene_plan = ScenePlan(
                    scene_id=scene.id,
                    framework=framework,
                    template_id=f"{framework.value}_simple_template",
                    parameters={
                        "title": scene.title,
                        "content": scene.narration[:100] + "...",  # Truncated content
                    },
                    duration=scene.duration,
                )
                scene_plans.append(scene_plan)
            
            # Create simple transition plans
            transition_plans = []
            for i in range(len(scene_plans) - 1):
                transition_plan = TransitionPlan(
                    from_scene=scene_plans[i].scene_id,
                    to_scene=scene_plans[i + 1].scene_id,
                    transition_type="fade",
                    duration=0.5,
                    parameters={"fade_color": "black"}
                )
                transition_plans.append(transition_plan)
            
            # Create style guide
            style_guide = StyleGuide(
                primary_color="#2E86AB",
                secondary_color="#A23B72", 
                background_color="#F18F01",
                font_family="Arial",
                font_sizes={"title": 24, "body": 16, "caption": 12}
            )
            
            # Create visual plan
            visual_plan = VisualPlan(
                scenes=scene_plans,
                transitions=transition_plans,
                style_guide=style_guide,
                total_duration=sum(scene.duration for scene in script.scenes),
            )
            
            # Update state
            state.visual_plan = visual_plan
            state.current_agent = AgentType.MANIM  # Next agent
            state.update_timestamp()
            
            self.log_progress("Visual planning completed", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state for visual planning."""
        if not state.script:
            raise ValueError("Narration script not found in state")
        
        if not state.understanding:
            raise ValueError("Paper understanding not found in state")
        
        if not state.script.scenes:
            raise ValueError("Script must contain scenes for visual planning")
    
    async def _analyze_scenes(
        self, 
        script: NarrationScript, 
        understanding: PaperUnderstanding
    ) -> List[Dict[str, Any]]:
        """Analyze scenes and assign animation frameworks."""
        # Prepare context for LLM
        scenes_text = ""
        for scene in script.scenes:
            scenes_text += f"\nScene {scene.id}: {scene.title}\n"
            scenes_text += f"Narration: {scene.narration[:200]}...\n"
            scenes_text += f"Duration: {scene.duration}s\n"
            scenes_text += f"Concepts: {', '.join(scene.concepts)}\n"
        
        equations_text = ""
        for eq in understanding.key_equations:
            equations_text += f"- {eq.equation_id}: {eq.visualization_hint}\n"
        
        concepts_text = ""
        for concept in understanding.visualizable_concepts:
            concepts_text += f"- {concept.name}: {concept.description} ({concept.visualization_type})\n"
        
        prompt = self.prompts.SCENE_ANALYSIS.format(
            title=state.get("paper_content", {}).get("title", "Research Paper"),
            scenes_text=scenes_text,
            equations_text=equations_text,
            concepts_text=concepts_text,
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=1500,
        )
        
        # Parse JSON response
        try:
            result = json.loads(response.content)
            return result.get("scene_assignments", [])
        except json.JSONDecodeError:
            # Fallback: use rule-based assignment
            return self._fallback_scene_assignment(script, understanding)
    
    def _fallback_scene_assignment(
        self, 
        script: NarrationScript, 
        understanding: PaperUnderstanding
    ) -> List[Dict[str, Any]]:
        """Fallback scene assignment using rule-based approach."""
        assignments = []
        
        for scene in script.scenes:
            content_type = self._classify_content_type(scene, understanding)
            framework = self.assignment_rules.FRAMEWORK_MAPPING[content_type]
            
            assignments.append({
                "scene_id": scene.id,
                "content_type": content_type.value,
                "framework": framework.value,
                "complexity": "medium",
                "visual_elements": self._suggest_visual_elements(content_type, scene),
                "transition_in": "fade",
                "transition_out": "fade",
            })
        
        return assignments
    
    def _classify_content_type(
        self, 
        scene: Scene, 
        understanding: PaperUnderstanding
    ) -> ContentType:
        """Classify scene content type based on narration and concepts."""
        narration_lower = scene.narration.lower()
        title_lower = scene.title.lower()
        
        # Check for mathematical content
        if any(keyword in narration_lower or keyword in title_lower 
               for keyword in self.assignment_rules.MATHEMATICAL_KEYWORDS):
            return ContentType.MATHEMATICAL
        
        # Check for UI elements
        if any(keyword in narration_lower or keyword in title_lower 
               for keyword in self.assignment_rules.UI_KEYWORDS):
            return ContentType.UI_ELEMENTS
        
        # Check for introduction/conclusion
        if any(keyword in title_lower for keyword in ["introduction", "intro", "welcome"]):
            return ContentType.INTRODUCTION
        
        if any(keyword in title_lower for keyword in ["conclusion", "summary", "end"]):
            return ContentType.CONCLUSION
        
        # Check if scene relates to key equations
        for eq in understanding.key_equations:
            if any(concept in narration_lower for concept in eq.related_concepts):
                return ContentType.MATHEMATICAL
        
        # Default to conceptual
        return ContentType.CONCEPTUAL
    
    def _suggest_visual_elements(self, content_type: ContentType, scene: Scene) -> List[str]:
        """Suggest visual elements based on content type."""
        if content_type == ContentType.MATHEMATICAL:
            return ["equation animation", "step-by-step derivation", "mathematical notation"]
        elif content_type == ContentType.CONCEPTUAL:
            return ["concept diagram", "process flow", "abstract visualization"]
        elif content_type == ContentType.UI_ELEMENTS:
            return ["title animation", "text overlay", "interface elements"]
        elif content_type == ContentType.INTRODUCTION:
            return ["title card", "author information", "topic introduction"]
        elif content_type == ContentType.CONCLUSION:
            return ["summary points", "key takeaways", "closing animation"]
        else:
            return ["smooth transition", "connecting elements"]
    
    async def _create_scene_plans(
        self, 
        assignments: List[Dict[str, Any]], 
        script: NarrationScript
    ) -> List[ScenePlan]:
        """Create detailed scene plans with templates and parameters."""
        scene_plans = []
        
        for assignment in assignments:
            scene_id = assignment["scene_id"]
            
            # Find corresponding scene in script
            scene = next((s for s in script.scenes if s.id == scene_id), None)
            if not scene:
                continue
            
            # Create scene plan
            scene_plan = ScenePlan(
                scene_id=scene_id,
                framework=assignment["framework"],
                template=self._select_template(assignment),
                parameters=self._generate_parameters(assignment, scene),
                duration=scene.duration,
            )
            
            scene_plans.append(scene_plan)
        
        return scene_plans
    
    def _select_template(self, assignment: Dict[str, Any]) -> str:
        """Select appropriate template based on assignment."""
        framework = assignment["framework"]
        content_type = assignment["content_type"]
        complexity = assignment["complexity"]
        
        # Template selection logic
        if framework == "manim":
            if content_type == "mathematical":
                if complexity == "simple":
                    return "simple_equation"
                elif complexity == "complex":
                    return "complex_derivation"
                else:
                    return "equation_animation"
            else:
                return "manim_basic"
        
        elif framework == "motion-canvas":
            if content_type == "conceptual":
                if complexity == "simple":
                    return "simple_diagram"
                elif complexity == "complex":
                    return "complex_animation"
                else:
                    return "concept_visualization"
            else:
                return "motion_canvas_basic"
        
        elif framework == "remotion":
            if content_type == "introduction":
                return "title_sequence"
            elif content_type == "conclusion":
                return "summary_card"
            elif content_type == "ui_elements":
                return "interface_animation"
            else:
                return "text_overlay"
        
        return "default_template"
    
    def _generate_parameters(self, assignment: Dict[str, Any], scene: Scene) -> Dict[str, Any]:
        """Generate template parameters based on assignment and scene."""
        base_parameters = {
            "duration": scene.duration,
            "title": scene.title,
            "narration_length": len(scene.narration.split()),
        }
        
        framework = assignment["framework"]
        content_type = assignment["content_type"]
        
        if framework == "manim":
            base_parameters.update({
                "equation_count": len([c for c in scene.concepts if "equation" in c.lower()]),
                "animation_speed": "medium",
                "color_scheme": "blue_theme",
            })
        
        elif framework == "motion-canvas":
            base_parameters.update({
                "concept_count": len(scene.concepts),
                "transition_style": "smooth",
                "background_color": "#f8f9fa",
            })
        
        elif framework == "remotion":
            base_parameters.update({
                "text_size": "large" if content_type == "introduction" else "medium",
                "font_family": "Inter",
                "background_gradient": True,
            })
        
        return base_parameters
    
    def _plan_transitions(self, scene_plans: List[ScenePlan]) -> List[TransitionPlan]:
        """Plan transitions between scenes."""
        transitions = []
        
        for i in range(len(scene_plans) - 1):
            current_scene = scene_plans[i]
            next_scene = scene_plans[i + 1]
            
            # Determine transition type based on framework change
            if current_scene.framework == next_scene.framework:
                transition_type = "smooth"
            else:
                transition_type = "cross_fade"
            
            transition = TransitionPlan(
                from_scene=current_scene.scene_id,
                to_scene=next_scene.scene_id,
                type=transition_type,
                duration=0.5,  # Default transition duration
                parameters={
                    "easing": "ease-in-out",
                    "fade_overlap": 0.2,
                }
            )
            
            transitions.append(transition)
        
        return transitions
    
    def _create_style_guide(self, understanding: PaperUnderstanding) -> StyleGuide:
        """Create overall style guide for the video."""
        # Determine theme based on research domain
        theme = "academic"
        if any("machine learning" in contrib.lower() or "ai" in contrib.lower() 
               for contrib in understanding.contributions):
            theme = "tech"
        elif any("math" in contrib.lower() or "theorem" in contrib.lower()
                 for contrib in understanding.contributions):
            theme = "mathematical"
        
        return StyleGuide(
            theme=theme,
            primary_color="#2563eb",  # Blue
            secondary_color="#64748b",  # Gray
            accent_color="#f59e0b",  # Amber
            font_family="Inter",
            background_color="#ffffff",
            text_color="#1e293b",
        )
    
    async def assign_framework_to_scene(
        self, 
        scene: Scene, 
        understanding: PaperUnderstanding
    ) -> AnimationFramework:
        """
        Public method to assign animation framework to a single scene.
        
        Args:
            scene: Scene to analyze
            understanding: Paper understanding context
            
        Returns:
            Recommended animation framework
        """
        content_type = self._classify_content_type(scene, understanding)
        return self.assignment_rules.FRAMEWORK_MAPPING[content_type]
    
    def get_framework_capabilities(self) -> Dict[AnimationFramework, List[str]]:
        """
        Get capabilities of each animation framework.
        
        Returns:
            Dictionary mapping frameworks to their capabilities
        """
        return {
            AnimationFramework.MANIM: [
                "Mathematical equations",
                "Step-by-step derivations", 
                "Geometric animations",
                "Graph plotting",
                "Theorem proofs",
            ],
            AnimationFramework.MOTION_CANVAS: [
                "Conceptual diagrams",
                "Process flows",
                "Abstract visualizations",
                "System architectures",
                "Data transformations",
            ],
            AnimationFramework.REMOTION: [
                "Title sequences",
                "Text overlays",
                "UI animations",
                "Intro/outro cards",
                "Interface elements",
            ],
        }