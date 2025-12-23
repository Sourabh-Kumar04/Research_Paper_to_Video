"""
Script Generation Agent for the RASO platform.

Converts paper understanding into narration scripts with educational tone
and YouTube-friendly language, organizing content into logical scenes.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from backend.models.understanding import PaperUnderstanding
from backend.models.script import NarrationScript, Scene
from backend.services.llm import llm_service, LLMRequest
from agents.retry import retry


class ScriptPrompts:
    """Prompt templates for script generation tasks."""
    
    SCENE_PLANNING = """
    Create a scene-by-scene plan for an educational video about this research paper.
    
    Paper Title: {title}
    Problem: {problem}
    Intuition: {intuition}
    
    Key Contributions:
    {contributions}
    
    Visualizable Concepts:
    {concepts}
    
    Create 4-6 scenes that:
    1. Start with an engaging introduction to the problem
    2. Explain the intuition behind the solution
    3. Detail the key contributions and methods
    4. Show visualizable concepts with clear explanations
    5. Conclude with impact and significance
    
    For each scene, provide:
    - Scene title (engaging and descriptive)
    - Main concepts to cover
    - Suggested visual type (manim for math, motion-canvas for concepts, remotion for UI)
    - Estimated duration in seconds (20-60 seconds per scene)
    
    Format as JSON:
    {{
        "scenes": [
            {{
                "title": "The Challenge of...",
                "concepts": ["problem", "motivation"],
                "visual_type": "motion-canvas",
                "duration": 30
            }}
        ]
    }}
    """
    
    NARRATION_GENERATION = """
    Write engaging narration for this video scene about a research paper.
    
    Scene Title: {scene_title}
    Main Concepts: {concepts}
    Duration: {duration} seconds
    Visual Type: {visual_type}
    
    Paper Context:
    - Title: {paper_title}
    - Problem: {problem}
    - Key Insight: {intuition}
    
    Write narration that:
    1. Uses conversational, YouTube-friendly language
    2. Explains technical concepts clearly for a general audience
    3. Maintains educational tone while being engaging
    4. Fits the estimated duration (aim for ~150 words per minute)
    5. Includes smooth transitions and natural pacing
    6. Avoids jargon without losing technical accuracy
    
    Guidelines:
    - Start scenes with engaging hooks
    - Use "we", "let's", and "imagine" to involve the audience
    - Break down complex ideas into digestible parts
    - Include rhetorical questions to maintain engagement
    - End with clear takeaways or transitions to next concepts
    
    Write only the narration text, no stage directions or formatting.
    """
    
    SCRIPT_VALIDATION = """
    Review this video script for educational quality and YouTube optimization.
    
    Full Script:
    {script_content}
    
    Total Duration: {total_duration} seconds
    Word Count: {word_count}
    
    Evaluate:
    1. Educational clarity - Are concepts explained clearly?
    2. Engagement level - Will it hold viewer attention?
    3. Pacing - Is the timing appropriate for each concept?
    4. Transitions - Do scenes flow smoothly together?
    5. YouTube optimization - Is it suitable for the platform?
    
    Provide specific suggestions for improvement in each area.
    Keep response under 200 words.
    """


class ScriptAgent(BaseAgent):
    """Agent responsible for generating narration scripts from paper understanding."""
    
    name = "ScriptAgent"
    description = "Converts paper understanding into educational video scripts"
    
    def __init__(self):
        """Initialize the script agent."""
        super().__init__()
        self.prompts = ScriptPrompts()
        self.words_per_minute = 150  # Average speaking rate
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute script generation from paper understanding.
        
        Args:
            state: Current workflow state containing understanding
            
        Returns:
            Updated state with narration script
        """
        self.validate_input(state)
        
        try:
            understanding = PaperUnderstanding(**state["understanding"])
            paper_content = state["paper_content"]
            
            self.log_progress("Starting script generation", state)
            
            # Plan scenes based on understanding
            scene_plan = await self._plan_scenes(understanding, paper_content)
            
            # Generate narration for each scene
            scenes = []
            for scene_info in scene_plan:
                narration = await self._generate_narration(
                    scene_info, understanding, paper_content
                )
                
                scene = Scene(
                    id=f"scene_{len(scenes)}",
                    title=scene_info["title"],
                    narration=narration,
                    duration=scene_info["duration"],
                    visual_type=scene_info["visual_type"],
                    concepts=scene_info["concepts"],
                )
                scenes.append(scene)
            
            # Create script object
            script = NarrationScript(
                scenes=scenes,
                total_duration=sum(scene.duration for scene in scenes),
                word_count=sum(len(scene.narration.split()) for scene in scenes),
            )
            
            # Validate and optimize script
            await self._validate_script(script)
            
            # Update state
            state["script"] = script.dict()
            state["current_agent"] = "VisualPlanningAgent"
            
            self.log_progress("Script generation completed", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state for script generation."""
        if "understanding" not in state:
            raise ValueError("Paper understanding not found in state")
        
        if "paper_content" not in state:
            raise ValueError("Paper content not found in state")
        
        understanding = state["understanding"]
        
        if not understanding.get("problem"):
            raise ValueError("Problem statement is required for script generation")
        
        if not understanding.get("contributions"):
            raise ValueError("Contributions are required for script generation")
    
    async def _plan_scenes(
        self, 
        understanding: PaperUnderstanding, 
        paper_content: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Plan the scene structure for the video."""
        # Format contributions and concepts for prompt
        contributions_text = "\n".join([f"- {contrib}" for contrib in understanding.contributions])
        
        concepts_text = ""
        if understanding.visualizable_concepts:
            concepts_text = "\n".join([
                f"- {concept.name}: {concept.description} ({concept.visualization_type})"
                for concept in understanding.visualizable_concepts
            ])
        
        prompt = self.prompts.SCENE_PLANNING.format(
            title=paper_content.get("title", "Research Paper"),
            problem=understanding.problem,
            intuition=understanding.intuition,
            contributions=contributions_text,
            concepts=concepts_text,
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=1000,
        )
        
        # Parse JSON response
        try:
            import json
            result = json.loads(response.content)
            scenes = result.get("scenes", [])
            
            # Validate and clean scene data
            cleaned_scenes = []
            for scene in scenes:
                if all(key in scene for key in ["title", "concepts", "visual_type", "duration"]):
                    # Ensure valid visual type
                    if scene["visual_type"] not in ["manim", "motion-canvas", "remotion"]:
                        scene["visual_type"] = "motion-canvas"
                    
                    # Ensure reasonable duration
                    if not isinstance(scene["duration"], (int, float)) or scene["duration"] < 10:
                        scene["duration"] = 30
                    elif scene["duration"] > 120:
                        scene["duration"] = 60
                    
                    cleaned_scenes.append(scene)
            
            if cleaned_scenes:
                return cleaned_scenes
                
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse scene planning JSON: {e}")
        
        # Fallback: create default scene structure
        return self._create_default_scenes(understanding, paper_content)
    
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
        
        # Add scenes for each major contribution
        for i, contribution in enumerate(understanding.contributions[:3]):
            scenes.append({
                "title": f"Key Innovation {i+1}",
                "concepts": [f"contribution_{i}"],
                "visual_type": "manim" if understanding.key_equations else "motion-canvas",
                "duration": 50
            })
        
        # Add conclusion scene
        scenes.append({
            "title": "Impact and Significance",
            "concepts": ["impact", "future"],
            "visual_type": "motion-canvas", 
            "duration": 35
        })
        
        return scenes
    
    async def _generate_narration(
        self,
        scene_info: Dict[str, Any],
        understanding: PaperUnderstanding,
        paper_content: Dict[str, Any]
    ) -> str:
        """Generate narration for a specific scene."""
        concepts_text = ", ".join(scene_info["concepts"])
        
        prompt = self.prompts.NARRATION_GENERATION.format(
            scene_title=scene_info["title"],
            concepts=concepts_text,
            duration=scene_info["duration"],
            visual_type=scene_info["visual_type"],
            paper_title=paper_content.get("title", "Research Paper"),
            problem=understanding.problem,
            intuition=understanding.intuition,
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.4,
            max_tokens=int(scene_info["duration"] * 3),  # ~3 tokens per second
        )
        
        narration = response.content.strip()
        
        # Clean up narration
        narration = self._clean_narration(narration)
        
        # Adjust length if needed
        target_words = int(scene_info["duration"] * self.words_per_minute / 60)
        narration = self._adjust_narration_length(narration, target_words)
        
        return narration
    
    def _clean_narration(self, narration: str) -> str:
        """Clean and format narration text."""
        # Remove stage directions or formatting
        narration = re.sub(r'\[.*?\]', '', narration)
        narration = re.sub(r'\(.*?\)', '', narration)
        
        # Fix common issues
        narration = re.sub(r'\s+', ' ', narration)  # Multiple spaces
        narration = re.sub(r'\.{2,}', '.', narration)  # Multiple periods
        
        # Ensure proper sentence endings
        if narration and not narration.endswith(('.', '!', '?')):
            narration += '.'
        
        return narration.strip()
    
    def _adjust_narration_length(self, narration: str, target_words: int) -> str:
        """Adjust narration length to match target duration."""
        words = narration.split()
        current_words = len(words)
        
        # If too long, truncate at sentence boundary
        if current_words > target_words * 1.2:
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
            
            if truncated:
                return truncated.strip()
        
        # If too short, could add transition phrases (for now, return as-is)
        return narration
    
    async def _validate_script(self, script: NarrationScript) -> None:
        """Validate and provide feedback on the generated script."""
        script_content = "\n\n".join([
            f"Scene: {scene.title}\n{scene.narration}"
            for scene in script.scenes
        ])
        
        prompt = self.prompts.SCRIPT_VALIDATION.format(
            script_content=script_content[:2000],  # Limit length
            total_duration=script.total_duration,
            word_count=script.word_count,
        )
        
        try:
            response = await llm_service.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=300,
            )
            
            # Log validation feedback
            self.logger.info(f"Script validation feedback: {response.content}")
            
        except Exception as e:
            self.logger.warning(f"Script validation failed: {e}")
    
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
        """
        Estimate speaking duration for given text.
        
        Args:
            text: Text to analyze
            
        Returns:
            Estimated duration in seconds
        """
        word_count = len(text.split())
        return (word_count / self.words_per_minute) * 60
    
    def validate_script_structure(self, script: NarrationScript) -> List[str]:
        """
        Validate script structure and return issues.
        
        Args:
            script: Script to validate
            
        Returns:
            List of validation issues
        """
        issues = []
        
        if not script.scenes:
            issues.append("Script has no scenes")
            return issues
        
        if script.total_duration < 60:
            issues.append("Script is too short (< 1 minute)")
        elif script.total_duration > 600:
            issues.append("Script is too long (> 10 minutes)")
        
        for i, scene in enumerate(script.scenes):
            if not scene.narration or len(scene.narration.strip()) < 10:
                issues.append(f"Scene {i+1} has insufficient narration")
            
            if scene.duration < 10:
                issues.append(f"Scene {i+1} is too short (< 10 seconds)")
            elif scene.duration > 120:
                issues.append(f"Scene {i+1} is too long (> 2 minutes)")
            
            estimated_duration = self.estimate_duration(scene.narration)
            if abs(estimated_duration - scene.duration) > scene.duration * 0.3:
                issues.append(f"Scene {i+1} duration mismatch (estimated: {estimated_duration:.1f}s, target: {scene.duration}s)")
        
        return issues