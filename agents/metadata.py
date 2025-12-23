"""
Metadata Generation Agent for the RASO platform.

Generates YouTube-optimized metadata including titles, descriptions, tags, and chapters.
"""

import re
from typing import Dict, List, Any

from agents.base import BaseAgent
from backend.models.understanding import PaperUnderstanding
from backend.models.video import VideoAsset, VideoMetadata
from backend.services.llm import llm_service
from agents.retry import retry


class MetadataAgent(BaseAgent):
    """Agent responsible for generating video metadata."""
    
    name = "MetadataAgent"
    description = "Generates YouTube-optimized metadata for videos"
    
    def __init__(self):
        """Initialize metadata agent."""
        super().__init__()
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Execute metadata generation."""
        self.validate_input(state)
        
        try:
            understanding = PaperUnderstanding(**state["understanding"])
            video = VideoAsset(**state["video"])
            paper_content = state.get("paper_content", {})
            
            self.log_progress("Generating video metadata", state)
            
            # Generate metadata components
            title = await self._generate_title(understanding, paper_content)
            description = await self._generate_description(understanding, paper_content)
            tags = await self._generate_tags(understanding, paper_content)
            
            # Create metadata
            metadata = VideoMetadata(
                title=title,
                description=description,
                tags=tags,
                chapters=video.chapters,
                category="Education",
            )
            
            # Update state
            state["metadata"] = metadata.dict()
            state["current_agent"] = "YouTubeAgent"
            
            self.log_progress("Metadata generation completed", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state."""
        required_keys = ["understanding", "video"]
        for key in required_keys:
            if key not in state:
                raise ValueError(f"{key} not found in state")
    
    async def _generate_title(self, understanding: PaperUnderstanding, paper_content: Dict) -> str:
        """Generate SEO-optimized title."""
        paper_title = paper_content.get("title", "Research Paper")
        
        prompt = f"""
        Create a YouTube-optimized title for a research paper explanation video.
        
        Paper Title: {paper_title}
        Main Problem: {understanding.problem}
        Key Contributions: {understanding.contributions[:2]}
        
        Requirements:
        - 60 characters or less
        - Engaging and educational
        - Include key concepts
        - YouTube-friendly language
        
        Generate only the title, no explanation.
        """
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.3,
            max_tokens=100,
        )
        
        title = response.content.strip().strip('"')
        
        # Ensure title length
        if len(title) > 60:
            title = title[:57] + "..."
        
        return title
    
    async def _generate_description(self, understanding: PaperUnderstanding, paper_content: Dict) -> str:
        """Generate comprehensive description."""
        paper_title = paper_content.get("title", "Research Paper")
        authors = paper_content.get("authors", [])
        
        prompt = f"""
        Create a YouTube description for a research paper explanation video.
        
        Paper: {paper_title}
        Authors: {', '.join(authors[:3])}
        Problem: {understanding.problem}
        Contributions: {understanding.contributions}
        
        Include:
        - Brief summary (2-3 sentences)
        - Key findings
        - Educational value
        - Relevant hashtags
        
        Keep it engaging and informative.
        """
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=500,
        )
        
        return response.content.strip()
    
    async def _generate_tags(self, understanding: PaperUnderstanding, paper_content: Dict) -> List[str]:
        """Generate relevant tags."""
        paper_title = paper_content.get("title", "")
        
        prompt = f"""
        Generate YouTube tags for a research paper video.
        
        Paper: {paper_title}
        Problem: {understanding.problem}
        Contributions: {understanding.contributions[:3]}
        
        Generate 10-15 relevant tags including:
        - Research domain keywords
        - Technical terms
        - Educational keywords
        
        Return as comma-separated list.
        """
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=200,
        )
        
        # Parse tags
        tags_text = response.content.strip()
        tags = [tag.strip() for tag in tags_text.split(',')]
        
        # Clean and validate tags
        clean_tags = []
        for tag in tags:
            tag = re.sub(r'[^\w\s-]', '', tag).strip()
            if tag and len(tag) <= 30:
                clean_tags.append(tag)
        
        return clean_tags[:15]  # YouTube limit