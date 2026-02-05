"""
Chapter Marker Generator for RASO Platform

This module generates chapter markers for videos based on scene boundaries
and content structure, ensuring YouTube compatibility and navigation support.
"""

import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from dataclasses import dataclass

from backend.models.video import Chapter
from backend.models.animation import RenderedScene
from backend.models.audio import AudioScene
from backend.models.script import Scene


@dataclass
class ChapterMetadata:
    """Extended chapter metadata for video files."""
    title: str
    start_time: float
    end_time: float
    duration: float
    scene_id: str
    description: Optional[str] = None
    keywords: Optional[List[str]] = None


class ChapterGenerator:
    """Generates chapter markers for video navigation."""
    
    def __init__(self):
        self.chapter_templates = self._initialize_chapter_templates()
    
    def _initialize_chapter_templates(self) -> Dict[str, str]:
        """Initialize chapter title templates based on content type."""
        return {
            "introduction": "Introduction",
            "problem": "The Problem",
            "background": "Background & Context", 
            "methodology": "Methodology",
            "approach": "Our Approach",
            "solution": "The Solution",
            "results": "Results & Findings",
            "evaluation": "Evaluation",
            "discussion": "Discussion",
            "conclusion": "Conclusion",
            "future_work": "Future Work",
            "summary": "Summary",
            "scene": "Scene {index}",
            "part": "Part {index}",
            "section": "Section {index}"
        }
    
    def generate_chapters_from_scenes(
        self,
        animation_scenes: List[RenderedScene],
        audio_scenes: List[AudioScene],
        script_scenes: Optional[List[Scene]] = None
    ) -> List[Chapter]:
        """
        Generate chapter markers from video scenes.
        
        Args:
            animation_scenes: List of rendered animation scenes
            audio_scenes: List of audio scenes
            script_scenes: Optional list of script scenes for better titles
            
        Returns:
            List of Chapter objects with timing and metadata
        """
        chapters = []
        current_time = 0.0
        
        # Create scene mapping for better chapter titles
        scene_map = {}
        if script_scenes:
            for scene in script_scenes:
                scene_map[scene.id] = scene
        
        # Generate chapters from scenes
        for i, (anim_scene, audio_scene) in enumerate(zip(animation_scenes, audio_scenes)):
            # Determine chapter duration (prefer audio duration for accuracy)
            duration = audio_scene.duration if audio_scene else anim_scene.duration
            
            # Generate intelligent chapter title
            chapter_title = self._generate_chapter_title(
                scene_index=i,
                scene_id=anim_scene.scene_id,
                script_scene=scene_map.get(anim_scene.scene_id),
                audio_scene=audio_scene
            )
            
            # Create chapter
            chapter = Chapter(
                title=chapter_title,
                start_time=current_time,
                end_time=current_time + duration
            )
            
            chapters.append(chapter)
            current_time += duration
        
        return chapters
    
    def _generate_chapter_title(
        self,
        scene_index: int,
        scene_id: str,
        script_scene: Optional[Scene] = None,
        audio_scene: Optional[AudioScene] = None
    ) -> str:
        """Generate intelligent chapter title based on scene content."""
        
        # Priority 1: Use script scene title if available
        if script_scene and script_scene.title:
            return self._clean_chapter_title(script_scene.title)
        
        # Priority 2: Analyze scene concepts for intelligent naming
        if script_scene and script_scene.concepts:
            title = self._generate_title_from_concepts(script_scene.concepts, scene_index)
            if title:
                return title
        
        # Priority 3: Analyze audio transcript for content-based title
        if audio_scene and audio_scene.transcript:
            title = self._generate_title_from_transcript(audio_scene.transcript, scene_index)
            if title:
                return title
        
        # Priority 4: Use scene ID if it's descriptive
        if scene_id and not scene_id.startswith("scene_"):
            return self._clean_chapter_title(scene_id.replace("_", " ").title())
        
        # Fallback: Generic scene numbering
        return f"Scene {scene_index + 1}"
    
    def _generate_title_from_concepts(self, concepts: List[str], scene_index: int) -> Optional[str]:
        """Generate title based on scene concepts."""
        if not concepts:
            return None
        
        # Map concepts to chapter templates
        concept_mappings = {
            "problem": "The Problem",
            "motivation": "Motivation & Background",
            "intuition": "Key Insight",
            "approach": "Our Approach", 
            "method": "Methodology",
            "methodology": "Methodology",
            "solution": "The Solution",
            "results": "Results",
            "evaluation": "Evaluation",
            "impact": "Impact & Significance",
            "conclusion": "Conclusion",
            "future": "Future Directions",
            "introduction": "Introduction",
            "background": "Background"
        }
        
        # Find best matching concept
        for concept in concepts:
            concept_lower = concept.lower()
            if concept_lower in concept_mappings:
                return concept_mappings[concept_lower]
        
        # Use first concept as title
        first_concept = concepts[0].replace("_", " ").title()
        return first_concept
    
    def _generate_title_from_transcript(self, transcript: str, scene_index: int) -> Optional[str]:
        """Generate title based on audio transcript content."""
        if not transcript or len(transcript.strip()) < 10:
            return None
        
        # Extract key phrases from transcript
        key_phrases = self._extract_key_phrases(transcript)
        
        if key_phrases:
            # Use the most relevant key phrase
            return key_phrases[0]
        
        # Fallback: Use first sentence as title (truncated)
        sentences = transcript.split('.')
        if sentences and len(sentences[0].strip()) > 5:
            first_sentence = sentences[0].strip()
            # Truncate if too long
            if len(first_sentence) > 50:
                first_sentence = first_sentence[:47] + "..."
            return first_sentence
        
        return None
    
    def _extract_key_phrases(self, text: str) -> List[str]:
        """Extract key phrases that could serve as chapter titles."""
        key_phrases = []
        
        # Common patterns for research paper sections
        patterns = [
            r"(?:let's|we'll|we're going to|today we)\s+([^.!?]{10,50})",
            r"(?:the|this)\s+(problem|challenge|issue|question)\s+(?:is|of)\s+([^.!?]{5,40})",
            r"(?:our|the)\s+(approach|method|solution|technique)\s+([^.!?]{5,40})",
            r"(?:we|they)\s+(found|discovered|showed|proved)\s+([^.!?]{5,40})",
            r"(?:in conclusion|to summarize|finally)\s*,?\s*([^.!?]{10,50})"
        ]
        
        import re
        for pattern in patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                phrase = match.group(1) if match.lastindex == 1 else match.group(2)
                if phrase and len(phrase.strip()) > 5:
                    cleaned_phrase = self._clean_chapter_title(phrase.strip())
                    if cleaned_phrase not in key_phrases:
                        key_phrases.append(cleaned_phrase)
        
        return key_phrases[:3]  # Return top 3 phrases
    
    def _clean_chapter_title(self, title: str) -> str:
        """Clean and format chapter title."""
        if not title:
            return "Untitled Chapter"
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Capitalize properly
        title = title.strip().capitalize()
        
        # Remove common prefixes
        prefixes_to_remove = [
            "scene:", "chapter:", "part:", "section:",
            "the scene", "this scene", "scene"
        ]
        
        title_lower = title.lower()
        for prefix in prefixes_to_remove:
            if title_lower.startswith(prefix):
                title = title[len(prefix):].strip()
                title = title.capitalize() if title else "Chapter"
                break
        
        # Ensure reasonable length
        if len(title) > 60:
            title = title[:57] + "..."
        
        # Ensure minimum length
        if len(title) < 3:
            title = "Chapter"
        
        return title
    
    def generate_youtube_chapters(self, chapters: List[Chapter]) -> str:
        """
        Generate YouTube-compatible chapter timestamps.
        
        Args:
            chapters: List of Chapter objects
            
        Returns:
            Formatted chapter string for YouTube description
        """
        if not chapters:
            return ""
        
        chapter_lines = []
        
        for chapter in chapters:
            # Format timestamp as MM:SS or HH:MM:SS
            timestamp = self._format_timestamp(chapter.start_time)
            chapter_lines.append(f"{timestamp} {chapter.title}")
        
        return "\n".join(chapter_lines)
    
    def _format_timestamp(self, seconds: float) -> str:
        """Format seconds as YouTube timestamp (MM:SS or HH:MM:SS)."""
        total_seconds = int(seconds)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def export_chapters_metadata(self, chapters: List[Chapter], output_path: str) -> None:
        """
        Export chapter metadata to JSON file.
        
        Args:
            chapters: List of Chapter objects
            output_path: Path to save the metadata file
        """
        metadata = {
            "chapters": [
                {
                    "title": chapter.title,
                    "start_time": chapter.start_time,
                    "end_time": chapter.end_time,
                    "duration": chapter.end_time - chapter.start_time,
                    "timestamp": self._format_timestamp(chapter.start_time)
                }
                for chapter in chapters
            ],
            "total_chapters": len(chapters),
            "total_duration": chapters[-1].end_time if chapters else 0,
            "youtube_format": self.generate_youtube_chapters(chapters)
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    def validate_chapters(self, chapters: List[Chapter]) -> List[str]:
        """
        Validate chapter structure and return any issues.
        
        Args:
            chapters: List of Chapter objects to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        if not chapters:
            issues.append("No chapters provided")
            return issues
        
        # Check chapter ordering and timing
        for i, chapter in enumerate(chapters):
            # Check title
            if not chapter.title or len(chapter.title.strip()) < 2:
                issues.append(f"Chapter {i+1} has invalid title: '{chapter.title}'")
            
            # Check timing
            if chapter.start_time < 0:
                issues.append(f"Chapter {i+1} has negative start time: {chapter.start_time}")
            
            if chapter.end_time <= chapter.start_time:
                issues.append(f"Chapter {i+1} has invalid duration: {chapter.end_time - chapter.start_time}")
            
            # Check ordering
            if i > 0:
                prev_chapter = chapters[i-1]
                if chapter.start_time < prev_chapter.end_time:
                    issues.append(f"Chapter {i+1} overlaps with previous chapter")
                
                # Allow small gaps but warn about large ones
                gap = chapter.start_time - prev_chapter.end_time
                if gap > 5.0:  # More than 5 seconds gap
                    issues.append(f"Large gap ({gap:.1f}s) between chapters {i} and {i+1}")
        
        # Check YouTube requirements
        if len(chapters) > 100:  # YouTube limit
            issues.append(f"Too many chapters ({len(chapters)}), YouTube limit is 100")
        
        # Check minimum duration (YouTube requires 10+ seconds per chapter)
        for i, chapter in enumerate(chapters):
            duration = chapter.end_time - chapter.start_time
            if duration < 10.0:
                issues.append(f"Chapter {i+1} too short ({duration:.1f}s), YouTube minimum is 10s")
        
        return issues


# Global instance for easy access
chapter_generator = ChapterGenerator()