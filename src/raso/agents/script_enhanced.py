"""
Enhanced Script Generation Agent for the RASO platform.

Converts paper understanding into narration scripts using latest AI models
with educational tone and YouTube-friendly language.
"""

import re
import json
import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from config.backend.models import AgentType, RASOMasterState
from config.backend.models.understanding import PaperUnderstanding
from config.backend.models.script import NarrationScript, Scene
from config.backend.services.llm import llm_service, LLMRequest
from agents.retry import retry
from scripts.utils.ai_model_manager import ai_model_manager, ModelType


class EnhancedScriptPrompts:
    """Enhanced prompt templates for AI-powered script generation."""
    
    ENHANCED_SCENE_PLANNING = """
    You are an expert educational content creator using the latest AI capabilities to plan engaging video content.
    
    Create a comprehensive scene-by-scene plan for an educational video about this research paper.
    
    Paper Title: {title}
    Problem Statement: {problem}
    Key Insight: {intuition}
    
    Major Contributions:
    {contributions}
    
    Create 4-6 scenes that tell a compelling story:
    1. **Hook & Context**: Start with a relatable problem or intriguing question
    2. **Problem Deep Dive**: Explain why this problem matters and what makes it challenging
    3. **The Breakthrough**: Present the key insight that makes the solution possible
    4. **Technical Innovation**: Detail the main contributions and how they work
    5. **Real-World Impact**: Connect to practical applications and significance
    
    For each scene, provide:
    - Compelling scene title that hooks viewers
    - Core concepts to explain (2-4 key ideas)
    - Optimal visual type: "manim" for math, "motion-canvas" for concepts, "remotion" for UI
    - Target duration (30-90 seconds based on complexity)
    - Engagement strategy (question, analogy, example)
    
    Format as JSON:
    {{
        "scenes": [
            {{
                "title": "The Challenge That Changed Everything",
                "concepts": ["problem context", "motivation"],
                "visual_type": "motion-canvas",
                "duration": 45,
                "engagement_strategy": "Start with relatable analogy"
            }}
        ]
    }}
    """
    
    ENHANCED_NARRATION_GENERATION = """
    You are an expert educational narrator creating engaging content for a technical audience.
    
    Generate compelling narration for this video scene using advanced storytelling techniques.
    
    Scene Context:
    - Title: {scene_title}
    - Core Concepts: {concepts}
    - Target Duration: {duration} seconds (~{word_count} words)
    - Visual Type: {visual_type}
    
    Paper Background:
    - Title: {paper_title}
    - Problem: {problem}
    - Key Insight: {intuition}
    
    Narration Guidelines:
    1. **Opening Hook**: Start with attention-grabbing statement or question
    2. **Conversational Tone**: Use "we", "let's explore", "imagine if" to involve viewers
    3. **Technical Clarity**: Explain complex concepts through analogies and examples
    4. **Engagement**: Include rhetorical questions and "aha moments"
    5. **Transitions**: Smooth connections between ideas
    
    Write engaging, educational narration that transforms complex research into compelling content.
    Output only the narration text - no stage directions or formatting.
    """


class EnhancedScriptAgent(BaseAgent):
    """Enhanced script agent using latest AI models for content generation."""
    
    name = "EnhancedScriptAgent"
    description = "Generates enhanced educational video scripts using latest AI models"
    
    def __init__(self, agent_type: AgentType):
        """Initialize the enhanced script agent."""
        super().__init__(agent_type)
        self.prompts = EnhancedScriptPrompts()
        self.words_per_minute = 150
        from agents.logging import AgentLogger
        self.logger = AgentLogger(agent_type)
        
        # AI model configuration
        self.ai_initialized = False
        self.preferred_models = {
            'reasoning': None,
            'coding': None,
        }
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """Execute enhanced script generation using latest AI models."""
        self.validate_input(state)
        
        try:
            understanding = state.understanding
            paper_content = state.paper_content
            
            self.log_progress("Starting enhanced script generation with AI models", state)
            
            # Initialize AI models
            await self._initialize_ai_models()
            
            # Generate enhanced script
            scenes = await self._generate_enhanced_script(understanding, paper_content)
            
            # Create script object
            script = NarrationScript(
                scenes=scenes,
                total_duration=sum(scene.duration for scene in scenes),
                word_count=sum(len(scene.narration.split()) for scene in scenes),
            )
            
            # Update state
            state.script = script
            state.current_agent = AgentType.VISUAL_PLANNING
            state.update_timestamp()
            
            self.log_progress(f"Enhanced script generation completed with {len(scenes)} scenes", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    async def _initialize_ai_models(self) -> None:
        """Initialize AI models for enhanced script generation."""
        if self.ai_initialized:
            return
            
        try:
            await ai_model_manager.initialize_ollama()
            
            self.preferred_models['reasoning'] = ai_model_manager.get_model_for_task('script_generation')
            self.preferred_models['coding'] = ai_model_manager.get_model_for_task('code_generation')
            
            if self.preferred_models['reasoning']:
                self.logger.info(f"Using reasoning model: {self.preferred_models['reasoning'].name}")
                
            self.ai_initialized = True
            
        except Exception as e:
            self.logger.warning(f"AI model initialization failed: {e}")
            self.ai_initialized = False
    
    async def _generate_enhanced_script(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Scene]:
        """Generate enhanced script using AI models."""
        try:
            # AI-powered scene planning
            scene_plan = await self._ai_scene_planning(understanding, paper_content)
            
            # Generate narration for each scene
            scenes = []
            for i, scene_info in enumerate(scene_plan):
                narration = await self._ai_narration_generation(
                    scene_info, understanding, paper_content
                )
                
                scene = Scene(
                    id=f"scene_{i}",
                    title=scene_info["title"],
                    narration=narration,
                    duration=scene_info["duration"],
                    visual_type=scene_info["visual_type"],
                    concepts=scene_info["concepts"],
                )
                
                scenes.append(scene)
                self.logger.info(f"Generated scene {i+1}/{len(scene_plan)}: {scene.title}")
            
            return scenes
            
        except Exception as e:
            self.logger.warning(f"AI-enhanced generation failed: {e}, using fallback")
            return await self._generate_fallback_script(understanding, paper_content)
    
    async def _ai_scene_planning(
        self,
        understanding: PaperUnderstanding,
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Use AI for enhanced scene planning."""
        try:
            contributions_text = "\n".join([f"- {contrib}" for contrib in understanding.contributions])
            
            prompt = self.prompts.ENHANCED_SCENE_PLANNING.format(
                title=paper_content.get("title", "Research Paper"),
                problem=understanding.problem,
                intuition=understanding.intuition,
                contributions=contributions_text,
            )
            
            # Use AI model if available
            model = self.preferred_models['reasoning']
            if model and self.ai_initialized:
                response = await ai_model_manager.generate_with_model(
                    model_info=model,
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=1500
                )
            else:
                response_obj = await llm_service.generate(
                    prompt=prompt,
                    temperature=0.3,
                    max_tokens=1500,
                )
                response = response_obj.content
            
            if response:
                try:
                    result = json.loads(response)
                    scenes = result.get("scenes", [])
                    
                    enhanced_scenes = []
                    for scene in scenes:
                        if self._validate_scene_structure(scene):
                            enhanced_scenes.append(self._enhance_scene_info(scene))
                    
                    if enhanced_scenes:
                        return enhanced_scenes
                        
                except json.JSONDecodeError:
                    self.logger.warning("Failed to parse AI scene planning response")
            
        except Exception as e:
            self.logger.warning(f"AI scene planning failed: {e}")
        
        return self._create_default_scenes(understanding, paper_content)
    
    async def _ai_narration_generation(
        self,
        scene_info: Dict[str, Any],
        understanding: PaperUnderstanding,
        paper_content: Dict[str, Any]
    ) -> str:
        """Generate enhanced narration using AI models."""
        try:
            target_words = int(scene_info["duration"] * self.words_per_minute / 60)
            
            prompt = self.prompts.ENHANCED_NARRATION_GENERATION.format(
                scene_title=scene_info["title"],
                concepts=", ".join(scene_info["concepts"]),
                duration=scene_info["duration"],
                word_count=target_words,
                visual_type=scene_info["visual_type"],
                paper_title=paper_content.get("title", "Research Paper"),
                problem=understanding.problem,
                intuition=understanding.intuition,
            )
            
            model = self.preferred_models['reasoning']
            if model and self.ai_initialized:
                response = await ai_model_manager.generate_with_model(
                    model_info=model,
                    prompt=prompt,
                    temperature=0.4,
                    max_tokens=target_words * 2
                )
            else:
                response_obj = await llm_service.generate(
                    prompt=prompt,
                    temperature=0.4,
                    max_tokens=target_words * 2,
                )
                response = response_obj.content
            
            if response:
                return self._clean_and_optimize_narration(response, target_words)
            
        except Exception as e:
            self.logger.warning(f"AI narration generation failed: {e}")
        
        return self._create_fallback_narration(scene_info, understanding)
    
    def _validate_scene_structure(self, scene: Dict[str, Any]) -> bool:
        """Validate scene structure from AI response."""
        required_fields = ["title", "concepts", "visual_type", "duration"]
        return all(field in scene for field in required_fields)
    
    def _enhance_scene_info(self, scene: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance scene information with defaults and validation."""
        valid_types = ["manim", "motion-canvas", "remotion"]
        if scene["visual_type"] not in valid_types:
            scene["visual_type"] = "motion-canvas"
        
        duration = scene.get("duration", 30)
        if not isinstance(duration, (int, float)) or duration < 15:
            scene["duration"] = 30
        elif duration > 120:
            scene["duration"] = 90
        
        if isinstance(scene.get("concepts"), str):
            scene["concepts"] = [scene["concepts"]]
        elif not isinstance(scene.get("concepts"), list):
            scene["concepts"] = ["general"]
        
        return scene
    
    def _clean_and_optimize_narration(self, narration: str, target_words: int) -> str:
        """Clean and optimize AI-generated narration."""
        # Remove stage directions and formatting
        narration = re.sub(r'\[.*?\]', '', narration)
        narration = re.sub(r'\(.*?\)', '', narration)
        
        # Clean up whitespace
        narration = re.sub(r'\s+', ' ', narration.strip())
        narration = re.sub(r'\.{2,}', '.', narration)
        
        # Ensure proper sentence endings
        if narration and not narration.endswith(('.', '!', '?')):
            narration += '.'
        
        # Optimize length if too long
        words = narration.split()
        if len(words) > target_words * 1.3:
            sentences = narration.split('.')
            truncated = ""
            word_count = 0
            
            for sentence in sentences:
                sentence_words = len(sentence.split())
                if word_count + sentence_words <= target_words:
                    truncated += sentence + "."
                    word_count += sentence_words
                else:
                    break
            
            if truncated and len(truncated.strip()) > 50:
                narration = truncated.strip()
        
        return narration
    
    def _create_default_scenes(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Create default scene structure as fallback."""
        scenes = [
            {
                "title": "The Problem",
                "concepts": ["problem", "motivation"],
                "visual_type": "motion-canvas",
                "duration": 45
            },
            {
                "title": "The Insight", 
                "concepts": ["intuition", "approach"],
                "visual_type": "motion-canvas",
                "duration": 40
            }
        ]
        
        for i, contribution in enumerate(understanding.contributions[:3]):
            scenes.append({
                "title": f"Key Innovation {i+1}",
                "concepts": [f"contribution_{i}"],
                "visual_type": "manim" if understanding.key_equations else "motion-canvas",
                "duration": 50
            })
        
        scenes.append({
            "title": "Impact and Significance",
            "concepts": ["impact", "future"],
            "visual_type": "motion-canvas", 
            "duration": 35
        })
        
        return scenes
    
    async def _generate_fallback_script(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Scene]:
        """Generate fallback script without AI enhancement."""
        scenes = []
        
        # Introduction scene
        intro_narration = self._create_introduction_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_0",
            title="The Challenge We're Tackling",
            narration=intro_narration,
            duration=self._estimate_duration(intro_narration),
            visual_type="motion-canvas",
            concepts=["problem", "motivation"],
        ))
        
        # Insight scene
        if understanding.intuition:
            insight_narration = self._create_insight_narration(understanding, paper_content)
            scenes.append(Scene(
                id="scene_1",
                title="The Breakthrough Insight",
                narration=insight_narration,
                duration=self._estimate_duration(insight_narration),
                visual_type="motion-canvas",
                concepts=["intuition", "approach"],
            ))
        
        # Contributions scene
        if understanding.contributions:
            contributions_narration = self._create_contributions_narration(understanding, paper_content)
            scenes.append(Scene(
                id="scene_2",
                title="How It Works",
                narration=contributions_narration,
                duration=self._estimate_duration(contributions_narration),
                visual_type="manim",
                concepts=["contributions", "methods"],
            ))
        
        # Conclusion scene
        conclusion_narration = self._create_conclusion_narration(understanding, paper_content)
        scenes.append(Scene(
            id="scene_3",
            title="Why This Matters",
            narration=conclusion_narration,
            duration=self._estimate_duration(conclusion_narration),
            visual_type="motion-canvas",
            concepts=["impact", "significance"],
        ))
        
        return scenes
    
    def _create_introduction_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create engaging introduction narration."""
        title = paper_content.get("title", "Research Paper")
        problem = understanding.problem or "a fundamental challenge in the field"
        
        narration = f"""Have you ever wondered how we could solve {problem.lower()}? 
        
Today, we are diving into groundbreaking research that tackles exactly this challenge. 
The paper '{title}' introduces a revolutionary approach that is changing how we think about this problem.

Let me walk you through why this matters and how the researchers cracked this tough nut. 
By the end of this video, you will understand not just what they did, but why it is such a big deal for the field.

So, what exactly is the problem we are trying to solve here?"""
        
        return self._clean_narration(narration)
    
    def _create_insight_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create insight explanation narration."""
        intuition = understanding.intuition or "a novel approach to the problem"
        
        narration = f"""Here is where things get really interesting. The key breakthrough came from a simple but powerful insight: {intuition}

Think about it this way - while everyone else was approaching the problem from one angle, these researchers stepped back and asked: What if we looked at this completely differently?

This shift in perspective is what makes their solution so elegant. Instead of fighting against the complexity, they found a way to work with it. 

Let me show you exactly how this insight translates into their actual method."""
        
        return self._clean_narration(narration)
    
    def _create_contributions_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create technical contributions narration."""
        contributions = understanding.contributions or ["a novel methodology", "improved performance"]
        main_contributions = contributions[:3]
        
        narration = f"""Now, let us get into the technical meat of what they actually built. 

The researchers made several key contributions that work together beautifully:

First, {main_contributions[0] if len(main_contributions) > 0 else 'they developed a new approach'}. This is crucial because it addresses the core limitation that previous methods struggled with."""
        
        if len(main_contributions) > 1:
            narration += f"\n\nSecond, {main_contributions[1]}. This builds on the first contribution and makes the whole system much more robust."
        
        if len(main_contributions) > 2:
            narration += f"\n\nAnd third, {main_contributions[2]}. This is what really sets their work apart from everything that came before."
        
        narration += "\n\nWhat is brilliant about their approach is how these pieces fit together. Each contribution reinforces the others, creating a solution that is greater than the sum of its parts."
        
        return self._clean_narration(narration)
    
    def _create_conclusion_narration(self, understanding: PaperUnderstanding, paper_content) -> str:
        """Create conclusion and impact narration."""
        title = paper_content.get("title", "Research Paper")
        
        narration = f"""So, why should you care about this research? 

The work in '{title}' is not just another incremental improvement - it is a fundamental shift in how we approach this problem. The implications go far beyond the immediate application.

Think about it: if we can solve this challenge more effectively, it opens up possibilities we could not even consider before. This could impact everything from practical applications to future research directions.

The researchers have essentially given us a new lens through which to view this entire problem space. And that is the kind of breakthrough that tends to spark a whole wave of follow-up innovations.

What excites me most is thinking about where this could lead next. The foundation they have laid here could be the starting point for discoveries we can not even imagine yet.

That is the power of truly innovative research - it does not just solve today's problems, it creates tomorrow's possibilities."""
        
        return self._clean_narration(narration)
    
    def _create_fallback_narration(self, scene_info: Dict[str, Any], understanding: PaperUnderstanding) -> str:
        """Create fallback narration when AI generation fails."""
        title = scene_info["title"]
        concepts = scene_info["concepts"]
        
        narration = f"""In this section, we explore {title.lower()}. 

The key concepts we need to understand are: {', '.join(concepts)}.

This is an important part of the research because it addresses fundamental challenges in the field. The researchers approach this systematically, building on established principles while introducing innovative solutions.

Let's examine how this contributes to the overall solution."""
        
        return self._clean_narration(narration)
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate narration duration based on word count."""
        words = len(text.split())
        duration = (words / self.words_per_minute) * 60
        return max(20.0, min(90.0, duration))
    
    def _clean_narration(self, text: str) -> str:
        """Clean and format narration text."""
        text = re.sub(r'\s+', ' ', text.strip())
        text = re.sub(r'\.(\w)', r'. \1', text)
        text = re.sub(r'\?(\w)', r'? \1', text)
        text = re.sub(r'!(\w)', r'! \1', text)
        return text
    
    def validate_input(self, state: RASOMasterState) -> None:
        """Validate input state for script generation."""
        if not state.understanding:
            raise ValueError("Paper understanding not found in state")
        
        if not state.paper_content:
            raise ValueError("Paper content not found in state")
        
        if not state.understanding.problem:
            raise ValueError("Problem statement is required for script generation")
        
        if not state.understanding.contributions:
            raise ValueError("Contributions are required for script generation")