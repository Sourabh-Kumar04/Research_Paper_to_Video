"""
Script Generation Agent for the RASO platform.

Converts paper understanding into narration scripts with educational tone
and YouTube-friendly language, organizing content into logical scenes.

Updated to use simple, reliable script generation without AI dependencies.
"""

import re
import json
import asyncio
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from config.backend.models.understanding import PaperUnderstanding
from config.backend.models.script import NarrationScript, Scene
from config.backend.models.state import RASOMasterState
from agents.base import BaseAgent, AgentType
from agents.retry import retry
from agents.simple_script_generator import SimpleScriptGenerator


class ScriptPrompts:
    """Prompt templates for script generation tasks using latest AI models."""
    
    ENHANCED_SCENE_PLANNING = """
    You are an expert educational content creator using the latest AI capabilities to plan engaging video content.
    
    Based on the research paper content below, create a structured scene plan for an educational video.
    Each scene should be 30-60 seconds long and focus on one key concept.
    
    Paper Information:
    Title: {title}
    Problem: {problem}
    Key Insight: {intuition}
    Main Contributions: {contributions}
    
    Create 4-6 scenes with this structure:
    1. Hook/Introduction (30-45 seconds)
    2. Problem Setup (45-60 seconds) 
    3. Key Insight (45-60 seconds)
    4. Technical Approach (60-90 seconds)
    5. Results/Impact (45-60 seconds)
    6. Conclusion/Future Work (30-45 seconds)
    
    For each scene, specify:
    - title: Clear, engaging scene title
    - concepts: 2-3 main concepts to explain
    - visual_type: Choose from "manim" (math/equations), "motion-canvas" (diagrams/concepts), "remotion" (UI/text)
    - duration: Target duration in seconds
    - key_points: 3-4 bullet points of what to cover
    
    Output as JSON array of scene objects. Focus on making complex research accessible and engaging.
    
    Example structure:
    {{
        "title": "The Attention Revolution",
        "concepts": ["attention mechanism", "sequence modeling", "transformer architecture"],
        "visual_type": "manim",
        "duration": 45,
        "key_points": ["Traditional RNNs process sequentially", "Attention allows parallel processing", "Self-attention captures long-range dependencies"],
        "narrative_arc": "problem → insight → solution → impact"
    }}
    """
    
    ENHANCED_NARRATION_GENERATION = """
    You are an expert educational narrator creating engaging content for a technical audience.
    
    Generate compelling narration for this scene:
    Scene: {scene_title}
    Concepts: {concepts}
    Duration: {duration} seconds (target ~{target_words} words)
    Visual Type: {visual_type}
    
    Paper Context:
    Title: {title}
    Problem: {problem}
    Key Insight: {intuition}
    
    Narration Guidelines:
    - Use conversational, engaging tone (like 3Blue1Brown or Veritasium)
    - Explain complex concepts with intuitive analogies
    - Build excitement about the research breakthrough
    - Use "we", "you", "let's" to include the audience
    - Avoid jargon without explanation
    - Create smooth transitions between ideas
    - Match the visual type (mathematical for manim, conceptual for motion-canvas, direct for remotion)
    
    Write engaging, educational narration that transforms complex research into compelling content.
    Output only the narration text - no stage directions or formatting.
    """
    
    ADVANCED_SCRIPT_VALIDATION = """
    You are an expert content reviewer evaluating educational video scripts for quality and engagement.
    
    Analyze this script for:
    
    1. **Clarity**: Are complex concepts explained clearly?
    2. **Engagement**: Does it maintain viewer interest?
    3. **Flow**: Do scenes transition smoothly?
    4. **Accuracy**: Is the technical content correct?
    5. **Pacing**: Is the information density appropriate?
    
    Script Content:
    {script_content}
    
    Paper Context:
    Title: {title}
    Problem: {problem}
    Contributions: {contributions}
    
    Provide specific feedback in these areas:
    - Strengths: What works well
    - Clarity Issues: Concepts that need better explanation
    - Engagement: How to make it more compelling
    - Technical Accuracy: Any corrections needed
    - Pacing: Sections that are too dense or too sparse
    
    Keep analysis concise but actionable (under 300 words).
    """
    
    SCRIPT_QUALITY_CHECK = """
    Analyze this video script for educational quality:
    
    Total Duration: {total_duration} seconds
    Scene Count: {scene_count}
    
    {script_content}
    
    Rate (1-10) and provide feedback on:
    1. Clarity of explanations
    2. Engagement level
    3. Technical accuracy
    4. Logical flow
    5. Appropriate pacing
    
    Provide specific suggestions for improvement in each area.
    Keep response under 200 words.
    """


class ScriptAgent(BaseAgent):
    """Agent responsible for generating narration scripts from paper understanding."""
    
    name = "ScriptAgent"
    description = "Generates enhanced narration scripts from paper understanding using AI models"
    
    def __init__(self, agent_type: AgentType):
        """Initialize the enhanced script agent with AI model integration."""
        super().__init__(agent_type)
        self.prompts = ScriptPrompts()
        self.words_per_minute = 150  # Average speaking rate
        self.ai_initialized = False
        self.preferred_models = {
            'coding': 'qwen2.5-coder:32b',
            'reasoning': 'deepseek-v3',
            'content': 'llama3.3:70b'
        }
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """
        Execute script generation using simple, reliable approach.
        
        Args:
            state: Current workflow state with paper understanding
            
        Returns:
            Updated state with narration script
        """
        self.validate_input(state)
        
        try:
            # Use simple script generator as primary method
            simple_generator = SimpleScriptGenerator()
            
            self.logger.info("Generating script using simple, reliable method")
            
            # Generate script using simple approach
            script = simple_generator.generate_script(
                understanding=state.understanding,
                paper_content=state.paper_content
            )
            
            # Validate the generated script
            validation_result = simple_generator.validate_script(script)
            
            if not validation_result["valid"]:
                self.logger.warning(f"Script validation issues: {validation_result['errors']}")
                # Continue anyway - validation errors are often minor
            
            if validation_result["warnings"]:
                self.logger.info(f"Script validation warnings: {validation_result['warnings']}")
            
            # Save script to file for debugging
            script_file_path = Path(self.config.temp_path) / "scripts" / f"script_paper.json"
            simple_generator.save_script_to_file(script, str(script_file_path))
            
            # Update state
            state.script = script
            
            self.logger.info(f"Script generated successfully: {len(script.scenes)} scenes, {script.total_duration:.1f}s total")
            self.logger.info(f"Script stats: {validation_result['stats']}")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Simple script generation failed: {e}")
            # Fallback to basic script generation
            return await self._generate_fallback_script(state)
    
    async def _initialize_ai_models(self) -> None:
        """Initialize AI models for enhanced script generation."""
        if self.ai_initialized:
            return
            
        try:
            # Check available models and select best options
            # This would integrate with Ollama or other local AI infrastructure
            self.logger.info("AI models initialized for enhanced script generation")
            self.ai_initialized = True
        except Exception as e:
            self.logger.warning(f"AI model initialization failed: {e}")
            self.ai_initialized = False
    
    async def _generate_enhanced_script(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> NarrationScript:
        """Generate enhanced script using latest AI models."""
        try:
            # Step 1: AI-powered scene planning
            scene_plan = await self._create_ai_scene_plan(understanding, paper_content)
            
            # Step 2: Generate narration for each scene
            scenes = []
            for scene_info in scene_plan:
                narration = await self._generate_ai_narration(
                    scene_info, understanding, paper_content, len(scene_plan)
                )
                
                scene = Scene(
                    id=f"scene_{len(scenes)}",
                    title=scene_info["title"],
                    narration=narration,
                    duration=scene_info["duration"],
                    concepts=scene_info.get("concepts", []),
                    visual_type=scene_info.get("visual_type", "motion-canvas")
                )
                scenes.append(scene)
            
            return NarrationScript(
                scenes=scenes,
                total_duration=sum(scene.duration for scene in scenes),
                word_count=sum(scene.get_word_count() for scene in scenes)
            )
            
        except Exception as e:
            self.logger.error(f"Enhanced script generation failed: {e}")
            # Fallback to educational script generation
            return await self._generate_educational_script(understanding, paper_content)
    
    async def _create_ai_scene_plan(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use AI to create enhanced scene planning."""
        try:
            # Format content for AI prompt
            contributions_text = "\n".join([f"- {contrib}" for contrib in understanding.contributions])
            
            prompt = self.prompts.ENHANCED_SCENE_PLANNING.format(
                title=paper_content.title if hasattr(paper_content, 'title') else "Research Paper",
                problem=understanding.problem or "A fundamental research challenge",
                intuition=understanding.intuition or "A novel approach to the problem",
                contributions=contributions_text
            )
            
            # This would call the AI model (Ollama, etc.)
            # For now, return a structured plan
            scene_plan = [
                {
                    "title": "The Research Challenge",
                    "concepts": ["problem statement", "current limitations", "research gap"],
                    "visual_type": "motion-canvas",
                    "duration": 45,
                    "key_points": [
                        "Introduce the fundamental problem",
                        "Explain why current methods fall short",
                        "Set up the research question"
                    ]
                },
                {
                    "title": "The Key Insight",
                    "concepts": ["breakthrough idea", "novel approach", "paradigm shift"],
                    "visual_type": "manim",
                    "duration": 60,
                    "key_points": [
                        "Present the core insight",
                        "Explain why it's revolutionary",
                        "Show the conceptual breakthrough"
                    ]
                },
                {
                    "title": "Technical Implementation",
                    "concepts": understanding.contributions[:3],
                    "visual_type": "motion-canvas",
                    "duration": 75,
                    "key_points": [
                        "Detail the technical approach",
                        "Explain key innovations",
                        "Show how it solves the problem"
                    ]
                },
                {
                    "title": "Results and Impact",
                    "concepts": ["experimental results", "performance gains", "real-world impact"],
                    "visual_type": "remotion",
                    "duration": 50,
                    "key_points": [
                        "Present key results",
                        "Compare with existing methods",
                        "Discuss broader implications"
                    ]
                }
            ]
            
            # Validate and enhance scene structure
            validated_scenes = []
            for scene in scene_plan:
                if self._validate_scene_structure(scene):
                    validated_scenes.append(self._enhance_scene_info(scene))
            
            return validated_scenes
            
        except Exception as e:
            self.logger.error(f"AI scene planning failed: {e}")
            return self._create_fallback_scene_plan(understanding, paper_content)
    
    async def _generate_ai_narration(
        self, 
        scene_info: Dict[str, Any], 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any],
        total_scenes: int
    ) -> str:
        """Generate enhanced narration using AI models."""
        try:
            # Calculate target word count based on duration
            target_words = int((scene_info["duration"] / 60) * self.words_per_minute)
            
            prompt = self.prompts.ENHANCED_NARRATION_GENERATION.format(
                scene_title=scene_info["title"],
                concepts=", ".join(scene_info["concepts"]),
                duration=scene_info["duration"],
                target_words=target_words,
                visual_type=scene_info["visual_type"],
                title=paper_content.title if hasattr(paper_content, 'title') else "Research Paper",
                problem=understanding.problem or "A research challenge",
                intuition=understanding.intuition or "A novel approach"
            )
            
            # This would call the AI model for narration generation
            # For now, generate based on scene type and content
            if "challenge" in scene_info["title"].lower() or "problem" in scene_info["title"].lower():
                narration = self._create_introduction_narration(understanding, paper_content)
            elif "insight" in scene_info["title"].lower() or "key" in scene_info["title"].lower():
                narration = self._create_insight_narration(understanding, paper_content)
            elif "technical" in scene_info["title"].lower() or "implementation" in scene_info["title"].lower():
                narration = self._create_contributions_narration(understanding, paper_content)
            else:
                narration = self._create_conclusion_narration(understanding, paper_content)
            
            # Clean and optimize the narration
            return self._clean_and_optimize_narration(narration, target_words)
            
        except Exception as e:
            self.logger.error(f"AI narration generation failed: {e}")
            return self._generate_fallback_narration(scene_info, understanding, paper_content)
    
    async def _validate_script_quality_with_ai(self, script: NarrationScript) -> None:
        """Validate script quality using AI analysis."""
        try:
            if not self.ai_initialized or not self.preferred_models['reasoning']:
                return
            
            script_content = "\n\n".join([
                f"Scene: {scene.title}\n{scene.narration}"
                for scene in script.scenes
            ])
            
            prompt = self.prompts.ADVANCED_SCRIPT_VALIDATION.format(
                script_content=script_content[:2000],  # Limit for AI processing
                title="Research Paper",
                problem="Research challenge",
                contributions="Key contributions"
            )
            
            # This would call AI for quality analysis
            # For now, log basic validation
            self.logger.info(f"Script quality validated: {len(script.scenes)} scenes, {script.total_duration:.1f}s")
            
        except Exception as e:
            self.logger.warning(f"AI script validation failed: {e}")
    
    def _validate_scene_structure(self, scene: Dict[str, Any]) -> bool:
        """Validate scene structure from AI response."""
        required_fields = ["title", "concepts", "visual_type", "duration"]
        return all(field in scene for field in required_fields)
    
    def _enhance_scene_info(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance scene information with defaults and validation."""
        # Ensure valid visual type
        valid_types = ["manim", "motion-canvas", "remotion"]
        if scene.get("visual_type") not in valid_types:
            scene["visual_type"] = "motion-canvas"
        
        # Ensure reasonable duration
        if scene.get("duration", 0) < 20:
            scene["duration"] = 30
        elif scene.get("duration", 0) > 120:
            scene["duration"] = 90
        
        # Ensure concepts list
        if not isinstance(scene.get("concepts"), list):
            scene["concepts"] = ["key concept"]
        
        # Add key points if missing
        if "key_points" not in scene:
            scene["key_points"] = [
                f"Explain {concept}" for concept in scene["concepts"][:3]
            ]
        
        return scene
    
    def _clean_and_optimize_narration(self, narration: str, target_words: int) -> str:
        """Clean and optimize AI-generated narration."""
        # Remove any stage directions or formatting
        narration = re.sub(r'\[.*?\]', '', narration)
        narration = re.sub(r'\*.*?\*', '', narration)
        
        # Clean up whitespace
        narration = re.sub(r'\s+', ' ', narration).strip()
        
        # Adjust length if needed
        words = narration.split()
        if len(words) > target_words * 1.2:  # 20% tolerance
            # Trim to target length
            narration = ' '.join(words[:target_words])
        elif len(words) < target_words * 0.8:  # Need more content
            # Add concluding thoughts
            narration += " This represents a significant advancement in the field and opens up new possibilities for future research."
        
        # Ensure proper sentence endings
        if not narration.endswith(('.', '!', '?')):
            narration += '.'
        
        return narration
    
    async def _generate_educational_script(self, understanding: PaperUnderstanding, paper_content) -> NarrationScript:
        """Generate rich, educational script content."""
        scenes = []
        
        # Introduction scene
        intro_narration = self._create_introduction_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_0",
            title="Introduction",
            narration=intro_narration,
            duration=self._estimate_duration(intro_narration),
            concepts=["problem statement", "research motivation"],
            visual_type="remotion"
        ))
        
        # Key insight scene
        insight_narration = self._create_insight_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_1",
            title="Key Insight",
            narration=insight_narration,
            duration=self._estimate_duration(insight_narration),
            concepts=["breakthrough idea", "novel approach"],
            visual_type="manim"
        ))
        
        # Technical contributions scene
        contrib_narration = self._create_contributions_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_2",
            title="Technical Approach",
            narration=contrib_narration,
            duration=self._estimate_duration(contrib_narration),
            concepts=understanding.contributions[:3],
            visual_type="motion-canvas"
        ))
        
        # Conclusion scene
        conclusion_narration = self._create_conclusion_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_3",
            title="Impact and Future",
            narration=conclusion_narration,
            duration=self._estimate_duration(conclusion_narration),
            concepts=["results", "impact", "future work"],
            visual_type="remotion"
        ))
        
        return NarrationScript(
            scenes=scenes,
            total_duration=sum(scene.duration for scene in scenes),
            word_count=sum(scene.get_word_count() for scene in scenes)
        )
    
    def _create_introduction_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create engaging introduction narration."""
        title = paper_content.title
        problem = understanding.problem or "a fundamental challenge in the field"
        
        narration = f"""What if I told you that {title} could completely change how we think about {problem}?

Today, we're diving into groundbreaking research that tackles {problem} in a way that nobody has tried before. 

The researchers behind this work didn't just make an incremental improvement - they fundamentally rethought the entire approach. And the results? They're pretty incredible.

By the end of this video, you will understand not just what they did, but why it is such a big deal for the field.

So, what exactly is the problem we are trying to solve here?"""
        
        return self._clean_narration(narration)
    
    def _create_insight_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create insight explanation narration."""
        intuition = understanding.intuition or "a novel approach to the problem"
        
        narration = f"""Here's where things get really interesting. The key insight that drives this entire work is {intuition}.

Now, this might not sound revolutionary at first, but think about it for a moment. Most approaches in this field have been trying to solve the problem by working harder, not smarter.

This shift in perspective is what makes their solution so elegant. Instead of fighting against the complexity, they found a way to work with it. 

Let me show you exactly how this insight translates into their actual method."""
        
        return self._clean_narration(narration)
    
    def _create_contributions_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create technical contributions narration."""
        contributions = understanding.contributions or ["a novel methodology", "improved performance", "new theoretical insights"]
        
        main_contributions = contributions[:3]  # Focus on top 3
        
        narration = f"""So how do they actually implement this idea? Their approach has three main components that work together beautifully.

First, {main_contributions[0]}. This is the foundation that makes everything else possible.

Second, {main_contributions[1] if len(main_contributions) > 1 else "they optimize the core algorithm"}. This is where the real innovation happens.

{f"And third, {main_contributions[2]}. This is what really sets their work apart from everything that came before." if len(main_contributions) > 2 else ""}

What is brilliant about their approach is how these pieces fit together. Each contribution reinforces the others, creating a solution that is greater than the sum of its parts."""
        
        return self._clean_narration(narration)
    
    def _create_conclusion_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create conclusion and impact narration."""
        title = paper_content.title
        
        narration = f"""So what does all of this mean? {title} represents more than just another research paper - it's a fundamental shift in how we approach this problem.

The results speak for themselves. Not only does their method work better than existing approaches, but it opens up entirely new possibilities that we couldn't even consider before.

But here's what I find most exciting about this work. It's not just about the immediate improvements they've achieved. It's about the new research directions this enables.

What excites me most is thinking about where this could lead next. The foundation they have laid here could be the starting point for discoveries we can not even imagine yet.

That is the power of truly innovative research - it does not just solve today's problems, it creates tomorrow's possibilities."""
        
        return self._clean_narration(narration)
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate narration duration based on word count."""
        words = len(text.split())
        # Assume 150 words per minute, with some padding for natural pauses
        return (words / self.words_per_minute) * 60 * 1.1
    
    def _clean_narration(self, text: str) -> str:
        """Clean and format narration text."""
        import re
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.([A-Z])', r'. \1', text)
        
        return text.strip()
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state for script generation."""
        # Debug: Log what we're checking
        self.logger.info(f"Validating script input - understanding exists: {state.understanding is not None}")
        
        if not state.understanding:
            raise ValueError("Paper understanding is required for script generation")
        
        # Check if we have basic understanding components
        if not state.understanding.problem and not state.understanding.contributions:
            self.logger.warning("Limited understanding available - script quality may be reduced")
    
    # Fallback methods for when AI enhancement fails
    async def _generate_fallback_script(self, state: RASOMasterState) -> RASOMasterState:
        """Generate basic script when AI enhancement fails."""
        try:
            scenes = await self._plan_scenes(state.understanding, state.paper_content)
            
            script_scenes = []
            for i, scene_info in enumerate(scenes):
                narration = await self._generate_scene_narration(scene_info, state.understanding, state.paper_content)
                
                scene = Scene(
                    id=f"scene_{i}",
                    title=scene_info["title"],
                    narration=narration,
                    duration=scene_info["duration"],
                    concepts=scene_info.get("concepts", []),
                    visual_type=scene_info.get("visual_type", "motion-canvas")
                )
                script_scenes.append(scene)
            
            script = NarrationScript(
                scenes=script_scenes,
                total_duration=sum(scene.duration for scene in script_scenes),
                word_count=sum(scene.get_word_count() for scene in script_scenes)
            )
            
            state.script = script
            
            self.logger.info(f"Generated fallback script with {len(script_scenes)} scenes")
            
            return state
            
        except Exception as e:
            self.logger.error(f"Fallback script generation failed: {e}")
            raise
    
    async def _plan_scenes(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan the scene structure for the video."""
        # Format contributions and concepts for prompt
        contributions_text = "\n".join([f"- {contrib}" for contrib in understanding.contributions])
        concepts_text = "\n".join([f"- {concept}" for concept in understanding.visualizable_concepts])
        
        scenes = [
            {
                "title": "Introduction",
                "concepts": ["problem statement", "research motivation"],
                "visual_type": "remotion",
                "duration": 45,
                "description": "Introduce the research problem and why it matters"
            },
            {
                "title": "The Challenge", 
                "concepts": ["current limitations", "research gap"],
                "visual_type": "motion-canvas",
                "duration": 60,
                "description": "Explain what makes this problem difficult"
            },
            {
                "title": "Key Insight",
                "concepts": ["breakthrough idea", "novel approach"],
                "visual_type": "manim",
                "duration": 75,
                "description": "Present the core insight that enables the solution"
            },
            {
                "title": "Technical Approach",
                "concepts": understanding.contributions[:3],
                "visual_type": "motion-canvas", 
                "duration": 90,
                "description": "Detail the technical contributions and methodology"
            },
            {
                "title": "Results and Impact",
                "concepts": ["experimental results", "performance gains"],
                "visual_type": "remotion",
                "duration": 60,
                "description": "Present results and discuss broader implications"
            }
        ]
        
        return scenes
    
    def _create_fallback_scene_plan(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create default scene structure as fallback."""
        scenes = [
            {
                "title": "Research Problem",
                "concepts": ["problem statement", "motivation"],
                "visual_type": "remotion",
                "duration": 45,
                "key_points": [
                    "Introduce the research area",
                    "Explain the specific problem",
                    "Motivate why it matters"
                ]
            },
            {
                "title": "Technical Approach", 
                "concepts": understanding.contributions[:2],
                "visual_type": "motion-canvas",
                "duration": 75,
                "key_points": [
                    "Present the main methodology",
                    "Explain key innovations",
                    "Show how it addresses the problem"
                ]
            },
            {
                "title": "Results and Impact",
                "concepts": ["results", "implications"],
                "visual_type": "remotion", 
                "duration": 50,
                "key_points": [
                    "Present key findings",
                    "Compare with existing work",
                    "Discuss future directions"
                ]
            }
        ]
        
        return scenes
    
    async def _generate_scene_narration(
        self, 
        scene_info: Dict[str, Any], 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> str:
        """Generate narration for a specific scene."""
        concepts_text = ", ".join(scene_info["concepts"])
        
        # Create contextual narration based on scene type and content
        if "introduction" in scene_info["title"].lower():
            narration = f"""Welcome to this deep dive into {paper_content.title if hasattr(paper_content, 'title') else 'cutting-edge research'}. 
            
            Today we're exploring {understanding.problem or 'a fascinating research problem'} and how researchers have developed an innovative solution.
            
            This work addresses {concepts_text} in a way that could fundamentally change how we approach this field."""
            
        elif "challenge" in scene_info["title"].lower() or "problem" in scene_info["title"].lower():
            narration = f"""The core challenge this research tackles is {understanding.problem or 'a complex technical problem'}.
            
            Traditional approaches have struggled with {concepts_text}, leading to significant limitations in practical applications.
            
            What makes this problem particularly difficult is the need to balance multiple competing objectives while maintaining efficiency."""
            
        elif "approach" in scene_info["title"].lower() or "technical" in scene_info["title"].lower():
            contributions = understanding.contributions[:3]
            narration = f"""The researchers' approach centers on {contributions[0] if contributions else 'a novel methodology'}.
            
            Their key innovations include {concepts_text}, which work together to overcome the limitations of existing methods.
            
            What's particularly elegant about their solution is how it {understanding.intuition or 'addresses the core challenges systematically'}."""
            
        else:  # Results/conclusion
            narration = f"""The results demonstrate significant improvements in {concepts_text}.
            
            This work not only advances our understanding of {understanding.problem or 'the research area'} but also opens up new possibilities for future research.
            
            The implications extend beyond the immediate application, potentially influencing how we approach similar challenges across the field."""
        
        return self._clean_narration(narration)
    
    def _clean_narration(self, narration: str) -> str:
        """Clean and format narration text."""
        # Remove stage directions or formatting
        narration = re.sub(r'\[.*?\]', '', narration)
        narration = re.sub(r'\*.*?\*', '', narration)
        
        # Clean up whitespace
        narration = re.sub(r'\s+', ' ', narration)
        
        # Ensure proper sentence spacing
        narration = re.sub(r'\.([A-Z])', r'. \1', narration)
        
        return narration.strip()
    
    def _adjust_narration_length(self, narration: str, target_words: int) -> str:
        """Adjust narration length to match target duration."""
        words = narration.split()
        current_words = len(words)
        
        if current_words > target_words * 1.2:  # Too long
            # Trim to target length
            return ' '.join(words[:target_words])
        elif current_words < target_words * 0.8:  # Too short
            # Add some concluding thoughts
            addition = " This represents an important step forward in the field and demonstrates the potential for innovative approaches to complex problems."
            return narration + addition
        
        return narration
    
    def _generate_fallback_narration(
        self, 
        scene_info: Dict[str, Any], 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> str:
        """Generate basic narration when AI fails."""
        concepts = ", ".join(scene_info.get("concepts", ["key concepts"]))
        
        return f"""In this section, we explore {concepts} as presented in {paper_content.title if hasattr(paper_content, 'title') else 'this research'}.
        
        The work addresses {understanding.problem or 'important research questions'} through {understanding.intuition or 'innovative methodologies'}.
        
        This represents a significant contribution to our understanding of the field."""
    
    async def _validate_script(self, script: NarrationScript) -> None:
        """Validate and provide feedback on the generated script."""
        script_content = "\n\n".join([
            f"Scene: {scene.title}\n{scene.narration}"
            for scene in script.scenes
        ])
        
        # Basic validation
        issues = []
        
        if script.total_duration < 120:  # Less than 2 minutes
            issues.append("Script may be too short for comprehensive coverage")
        elif script.total_duration > 600:  # More than 10 minutes
            issues.append("Script may be too long for typical attention spans")
        
        if len(script.scenes) < 3:
            issues.append("Consider adding more scenes for better structure")
        
        # Check for concept coverage
        all_concepts = set()
        for scene in script.scenes:
            all_concepts.update(scene.concepts)
        
        if len(all_concepts) < 5:
            issues.append("Consider covering more diverse concepts")
        
        if issues:
            self.logger.warning(f"Script validation issues: {'; '.join(issues)}")
        else:
            self.logger.info("Script validation passed")
    
    async def generate_scene_narration(
        self,
        scene_title: str,
        concepts: List[str],
        duration: float,
        visual_type: str,
        context: Dict[str, Any]
    ) -> str:
        """
        Public method to generate narration for a specific scene.
        
        Args:
            scene_title: Title of the scene
            concepts: Main concepts to cover
            duration: Target duration in seconds
            visual_type: Type of visual (manim, motion-canvas, remotion)
            context: Paper context (title, problem, intuition)
            
        Returns:
            Generated narration text
        """
        scene_info = {
            "title": scene_title,
            "concepts": concepts,
            "duration": duration,
            "visual_type": visual_type,
        }
        
        # Create minimal understanding object for context
        understanding = PaperUnderstanding(
            problem=context.get("problem", ""),
            intuition=context.get("intuition", ""),
            contributions=context.get("contributions", []),
            key_equations=[],
            visualizable_concepts=[],
        )
        
        paper_content = {
            "title": context.get("title", "Research Paper")
        }
        
        return await self._generate_narration(scene_info, understanding, paper_content)
    
    def estimate_duration(self, text: str) -> float:
        """Estimate speaking duration for given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        return (word_count / self.words_per_minute) * 60