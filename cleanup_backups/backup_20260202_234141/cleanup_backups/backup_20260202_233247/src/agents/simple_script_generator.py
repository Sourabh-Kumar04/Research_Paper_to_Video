"""
Simple Script Generator for RASO platform.

Creates working narration scripts from paper understanding using basic text processing.
No AI dependencies - focuses on reliable content extraction and script generation.
"""

import re
from typing import List, Optional
from pathlib import Path
import sys
import os

# Fix import paths to use config/backend/models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'backend'))

from models.understanding import PaperUnderstanding
from models.script import NarrationScript, Scene
from models.state import RASOMasterState
from models.paper import PaperContent


class SimpleScriptGenerator:
    """Simple, reliable script generator without AI dependencies."""
    
    def __init__(self):
        """Initialize the simple script generator."""
        self.words_per_minute = 150  # Average speaking rate
        self.min_scene_duration = 20.0  # Minimum scene duration in seconds
        self.max_scene_duration = 90.0  # Maximum scene duration in seconds
        
    def generate_script(self, understanding: PaperUnderstanding, paper_content: Optional[PaperContent] = None) -> NarrationScript:
        """
        Generate a narration script from paper understanding.
        
        Args:
            understanding: Paper understanding with key insights
            paper_content: Optional paper content for additional context
            
        Returns:
            Complete narration script with scenes
        """
        # Extract key information
        title = paper_content.title if paper_content and hasattr(paper_content, 'title') else "Research Paper"
        problem = understanding.problem or "This research addresses an important problem in the field."
        key_insight = understanding.intuition or "The authors present a novel approach to solve this problem."
        contributions = understanding.contributions or ["Novel methodology", "Experimental validation", "Practical applications"]
        
        # Create scenes based on paper structure
        scenes = []
        
        # Scene 1: Introduction and Problem
        intro_scene = self._create_introduction_scene(title, problem, understanding)
        scenes.append(intro_scene)
        
        # Scene 2: Key Insight and Approach
        insight_scene = self._create_insight_scene(key_insight, understanding)
        scenes.append(insight_scene)
        
        # Scene 3: Main Contributions
        contributions_scene = self._create_contributions_scene(contributions, understanding)
        scenes.append(contributions_scene)
        
        # Scene 4: Results and Impact (if we have visualizable concepts or equations)
        if understanding.visualizable_concepts or understanding.key_equations:
            results_scene = self._create_results_scene(understanding)
            scenes.append(results_scene)
        
        # Scene 5: Conclusion
        conclusion_scene = self._create_conclusion_scene(understanding, title)
        scenes.append(conclusion_scene)
        
        # Calculate total duration and word count
        total_duration = sum(scene.duration for scene in scenes)
        total_word_count = sum(len(scene.narration.split()) for scene in scenes)
        
        # Create and return the script
        script = NarrationScript(
            scenes=scenes,
            total_duration=total_duration,
            word_count=total_word_count,
            target_audience="general",
            language="en"
        )
        
        return script
    
    def _create_introduction_scene(self, title: str, problem: str, understanding: PaperUnderstanding) -> Scene:
        """Create an engaging introduction scene."""
        # Create narration text
        narration_parts = [
            f"Welcome to this explanation of '{title}'.",
            f"This research tackles an important challenge: {problem}",
        ]
        
        # Add context if available
        if understanding.visualizable_concepts:
            context_summary = f"exploring {len(understanding.visualizable_concepts)} key concepts"
            narration_parts.append(f"In {context_summary}, this work presents a significant advancement.")
        
        narration_parts.append("Let's dive into what makes this research so interesting.")
        
        narration = " ".join(narration_parts)
        duration = self._calculate_duration(narration)
        
        return Scene(
            id="intro",
            title="Introduction",
            narration=narration,
            duration=duration,
            concepts=["research problem", "motivation", "context"],
            visual_type="remotion"  # Good for text and titles
        )
    
    def _create_insight_scene(self, key_insight: str, understanding: PaperUnderstanding) -> Scene:
        """Create a scene explaining the key insight."""
        narration_parts = [
            "So what's the key breakthrough here?",
            key_insight,
        ]
        
        # Add technical approach if available
        if understanding.key_equations:
            approach_summary = f"{len(understanding.key_equations)} key mathematical formulations"
            narration_parts.append(f"The technical approach involves {approach_summary}")
        
        narration_parts.append("This insight opens up new possibilities for solving the problem.")
        
        narration = " ".join(narration_parts)
        duration = self._calculate_duration(narration)
        
        return Scene(
            id="insight",
            title="Key Insight",
            narration=narration,
            duration=duration,
            concepts=["key insight", "technical approach", "innovation"],
            visual_type="motion-canvas"  # Good for concepts and diagrams
        )
    
    def _create_contributions_scene(self, contributions: List[str], understanding: PaperUnderstanding) -> Scene:
        """Create a scene highlighting main contributions."""
        narration_parts = [
            "This research makes several important contributions to the field.",
        ]
        
        # Add each contribution
        for i, contribution in enumerate(contributions[:3]):  # Limit to 3 main contributions
            if i == 0:
                narration_parts.append(f"First, {contribution.lower()}.")
            elif i == 1:
                narration_parts.append(f"Second, {contribution.lower()}.")
            else:
                narration_parts.append(f"Finally, {contribution.lower()}.")
        
        narration_parts.append("These contributions represent significant advances in our understanding.")
        
        narration = " ".join(narration_parts)
        duration = self._calculate_duration(narration)
        
        return Scene(
            id="contributions",
            title="Main Contributions",
            narration=narration,
            duration=duration,
            concepts=["contributions", "advances", "methodology"],
            visual_type="remotion"  # Good for listing items
        )
    
    def _create_results_scene(self, understanding: PaperUnderstanding) -> Scene:
        """Create a scene about results and impact."""
        narration_parts = [
            "Let's look at what the results show us.",
        ]
        
        # Add experimental results if available
        if understanding.key_equations:
            results_summary = f"mathematical analysis with {len(understanding.key_equations)} key equations"
            narration_parts.append(f"The analysis demonstrates that {results_summary}")
        
        # Add practical applications if available
        if understanding.visualizable_concepts:
            applications_summary = f"{len(understanding.visualizable_concepts)} practical concepts"
            narration_parts.append(f"This has applications in {applications_summary}")
        
        narration_parts.append("These results validate the effectiveness of the proposed approach.")
        
        narration = " ".join(narration_parts)
        duration = self._calculate_duration(narration)
        
        return Scene(
            id="results",
            title="Results and Impact",
            narration=narration,
            duration=duration,
            concepts=["experimental results", "validation", "applications"],
            visual_type="manim"  # Good for showing data and results
        )
    
    def _create_conclusion_scene(self, understanding: PaperUnderstanding, title: str) -> Scene:
        """Create a concluding scene."""
        narration_parts = [
            f"To wrap up our exploration of '{title}':",
        ]
        
        # Summarize the impact
        if understanding.confidence_score > 0.7:
            significance_summary = "high-confidence research findings"
            narration_parts.append(f"This work is significant because it presents {significance_summary}")
        
        # Add future directions if available
        if understanding.visualizable_concepts:
            future_summary = f"the {len(understanding.visualizable_concepts)} concepts explored here open new research directions"
            narration_parts.append(f"Looking ahead, {future_summary}")
        
        narration_parts.extend([
            "This research opens new doors for future investigations.",
            "Thanks for joining me in exploring this fascinating work!"
        ])
        
        narration = " ".join(narration_parts)
        duration = self._calculate_duration(narration)
        
        return Scene(
            id="conclusion",
            title="Conclusion",
            narration=narration,
            duration=duration,
            concepts=["significance", "future work", "impact"],
            visual_type="remotion"  # Good for conclusions and text
        )
    
    def _calculate_duration(self, text: str) -> float:
        """Calculate speaking duration based on word count."""
        word_count = len(text.split())
        duration = (word_count / self.words_per_minute) * 60  # Convert to seconds
        
        # Ensure duration is within reasonable bounds
        duration = max(self.min_scene_duration, min(duration, self.max_scene_duration))
        
        return round(duration, 1)
    
    def _summarize_text(self, text: str, max_words: int = 30) -> str:
        """Create a simple summary by taking the first meaningful sentence or phrase."""
        if not text:
            return "the research findings"
        
        # Clean up the text
        text = re.sub(r'\s+', ' ', text.strip())
        
        # If text is short enough, return as is
        words = text.split()
        if len(words) <= max_words:
            return text.lower()
        
        # Try to find a complete sentence within the word limit
        sentences = re.split(r'[.!?]+', text)
        for sentence in sentences:
            sentence_words = sentence.strip().split()
            if 5 <= len(sentence_words) <= max_words:
                return sentence.strip().lower()
        
        # Fallback: take first max_words and try to end at a reasonable point
        truncated = ' '.join(words[:max_words])
        
        # Try to end at a comma or other natural break
        for punct in [',', ';', ' and ', ' or ', ' but ']:
            if punct in truncated:
                parts = truncated.split(punct)
                if len(parts) > 1 and len(parts[0].split()) >= 5:
                    return parts[0].strip().lower()
        
        return truncated.lower()
    
    def save_script_to_file(self, script: NarrationScript, output_path: str) -> bool:
        """
        Save the generated script to a file for debugging and reference.
        
        Args:
            script: The generated script
            output_path: Path to save the script file
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            script_data = {
                "total_duration": script.total_duration,
                "total_scenes": len(script.scenes),
                "target_audience": script.target_audience,
                "language": script.language,
                "word_count": script.word_count,
                "scenes": []
            }
            
            for scene in script.scenes:
                scene_data = {
                    "id": scene.id,
                    "title": scene.title,
                    "narration": scene.narration,
                    "duration": scene.duration,
                    "concepts": scene.concepts,
                    "visual_type": scene.visual_type,
                    "word_count": len(scene.narration.split())
                }
                script_data["scenes"].append(scene_data)
            
            # Save to file
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(script_data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Failed to save script to file: {e}")
            return False
    
    def validate_script(self, script: NarrationScript) -> dict:
        """
        Validate the generated script for completeness and quality.
        
        Args:
            script: The script to validate
            
        Returns:
            Dictionary with validation results
        """
        validation = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "stats": {
                "total_scenes": len(script.scenes),
                "total_duration": script.total_duration,
                "total_words": sum(len(scene.narration.split()) for scene in script.scenes),
                "average_scene_duration": script.total_duration / len(script.scenes) if script.scenes else 0
            }
        }
        
        # Check minimum requirements
        if len(script.scenes) < 3:
            validation["errors"].append("Script must have at least 3 scenes")
            validation["valid"] = False
        
        if script.total_duration < 60:
            validation["warnings"].append("Script duration is quite short (less than 1 minute)")
        
        if script.total_duration > 600:
            validation["warnings"].append("Script duration is quite long (more than 10 minutes)")
        
        # Check individual scenes
        for i, scene in enumerate(script.scenes):
            if not scene.narration.strip():
                validation["errors"].append(f"Scene {i+1} ({scene.id}) has empty narration")
                validation["valid"] = False
            
            if scene.duration < 10:
                validation["warnings"].append(f"Scene {i+1} ({scene.id}) is very short ({scene.duration}s)")
            
            if scene.duration > 120:
                validation["warnings"].append(f"Scene {i+1} ({scene.id}) is very long ({scene.duration}s)")
            
            if len(scene.narration.split()) < 10:
                validation["warnings"].append(f"Scene {i+1} ({scene.id}) has very few words")
        
        return validation