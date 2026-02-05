"""
YouTube Optimization Features

This module provides YouTube-specific encoding parameter optimization, thumbnail generation,
SEO metadata generation, intro/outro sequence generation, and chapter marker creation
for optimal YouTube performance and engagement.
"""

import asyncio
import json
import logging
import re
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from datetime import datetime, timedelta
import hashlib
import base64

from ..llm.gemini_client import GeminiClient
from .models import CinematicSettingsModel


logger = logging.getLogger(__name__)


class YouTubeContentType(Enum):
    """YouTube content type classifications."""
    EDUCATIONAL = "educational"
    ENTERTAINMENT = "entertainment"
    TUTORIAL = "tutorial"
    REVIEW = "review"
    VLOG = "vlog"
    GAMING = "gaming"
    MUSIC = "music"
    NEWS = "news"


class YouTubeAspectRatio(Enum):
    """YouTube supported aspect ratios."""
    LANDSCAPE = "16:9"  # Standard landscape
    VERTICAL = "9:16"   # YouTube Shorts
    SQUARE = "1:1"      # Square format


@dataclass
class YouTubeEncodingParams:
    """YouTube-optimized encoding parameters."""
    video_codec: str = "H.264"
    audio_codec: str = "AAC"
    pixel_format: str = "yuv420p"
    video_bitrate: str = "8000k"  # For 4K content
    audio_bitrate: str = "128k"
    frame_rate: float = 30.0
    resolution: Tuple[int, int] = (1920, 1080)
    max_file_size_mb: int = 256000  # 256GB limit
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_content_type(cls, content_type: YouTubeContentType, quality: str = "4k") -> 'YouTubeEncodingParams':
        """Create encoding params optimized for content type and quality."""
        
        base_params = cls()
        
        if quality == "8k":
            base_params.resolution = (7680, 4320)
            base_params.video_bitrate = "45000k"
            base_params.frame_rate = 60.0
        elif quality == "4k":
            base_params.resolution = (3840, 2160)
            base_params.video_bitrate = "15000k"
            base_params.frame_rate = 30.0
        elif quality == "1080p":
            base_params.resolution = (1920, 1080)
            base_params.video_bitrate = "8000k"
            base_params.frame_rate = 30.0
        else:  # 720p
            base_params.resolution = (1280, 720)
            base_params.video_bitrate = "5000k"
            base_params.frame_rate = 30.0
        
        # Adjust for content type
        if content_type == YouTubeContentType.GAMING:
            base_params.frame_rate = 60.0
            base_params.video_bitrate = str(int(base_params.video_bitrate.rstrip('k')) * 1.2) + 'k'
        elif content_type == YouTubeContentType.EDUCATIONAL:
            # Lower bitrate for talking head content
            base_params.video_bitrate = str(int(base_params.video_bitrate.rstrip('k')) * 0.8) + 'k'
        elif content_type == YouTubeContentType.MUSIC:
            # Higher audio quality for music
            base_params.audio_bitrate = "320k"
        
        return base_params


@dataclass
class ThumbnailSuggestion:
    """YouTube thumbnail suggestion with visual elements."""
    timestamp: float  # seconds into video
    description: str
    visual_elements: List[str]
    text_overlay: Optional[str] = None
    confidence: float = 0.0
    color_scheme: str = "high_contrast"
    composition_style: str = "rule_of_thirds"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ChapterMarker:
    """YouTube chapter marker for improved navigation."""
    timestamp: float  # seconds into video
    title: str
    description: str
    category: str = "content"  # content, intro, outro, transition
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    def to_youtube_format(self) -> str:
        """Convert to YouTube chapter format (MM:SS Title)."""
        minutes = int(self.timestamp // 60)
        seconds = int(self.timestamp % 60)
        return f"{minutes:02d}:{seconds:02d} {self.title}"


@dataclass
class SEOMetadata:
    """YouTube SEO-optimized metadata."""
    title: str
    description: str
    tags: List[str]
    category: str = "Education"
    language: str = "en"
    thumbnail_suggestions: List[ThumbnailSuggestion] = None
    chapter_markers: List[ChapterMarker] = None
    
    def __post_init__(self):
        if self.thumbnail_suggestions is None:
            self.thumbnail_suggestions = []
        if self.chapter_markers is None:
            self.chapter_markers = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'title': self.title,
            'description': self.description,
            'tags': self.tags,
            'category': self.category,
            'language': self.language,
            'thumbnail_suggestions': [t.to_dict() for t in self.thumbnail_suggestions],
            'chapter_markers': [c.to_dict() for c in self.chapter_markers]
        }


@dataclass
class YouTubeOptimizationSettings:
    """Complete YouTube optimization settings."""
    content_type: YouTubeContentType
    target_audience: str = "general"  # general, technical, academic
    aspect_ratio: YouTubeAspectRatio = YouTubeAspectRatio.LANDSCAPE
    target_duration_range: Tuple[int, int] = (480, 900)  # 8-15 minutes in seconds
    enable_shorts_optimization: bool = False
    enable_thumbnail_generation: bool = True
    enable_seo_optimization: bool = True
    enable_chapter_markers: bool = True
    enable_intro_outro: bool = True
    branding_elements: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'content_type': self.content_type.value,
            'target_audience': self.target_audience,
            'aspect_ratio': self.aspect_ratio.value,
            'target_duration_range': self.target_duration_range,
            'enable_shorts_optimization': self.enable_shorts_optimization,
            'enable_thumbnail_generation': self.enable_thumbnail_generation,
            'enable_seo_optimization': self.enable_seo_optimization,
            'enable_chapter_markers': self.enable_chapter_markers,
            'enable_intro_outro': self.enable_intro_outro,
            'branding_elements': self.branding_elements
        }


class YouTubeOptimizer:
    """YouTube optimization system for cinematic content."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client
        self.optimization_cache = {}
        
        # YouTube best practices
        self.title_max_length = 100
        self.description_max_length = 5000
        self.tags_max_count = 15
        self.optimal_duration_ranges = {
            YouTubeContentType.EDUCATIONAL: (480, 900),  # 8-15 minutes
            YouTubeContentType.TUTORIAL: (300, 1200),   # 5-20 minutes
            YouTubeContentType.ENTERTAINMENT: (180, 600), # 3-10 minutes
            YouTubeContentType.REVIEW: (600, 1800),     # 10-30 minutes
        }
    
    async def optimize_for_youtube(
        self,
        content_metadata: Dict[str, Any],
        cinematic_settings: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> Dict[str, Any]:
        """
        Optimize content for YouTube with comprehensive settings.
        
        Args:
            content_metadata: Video content information (title, description, duration, etc.)
            cinematic_settings: Current cinematic settings
            optimization_settings: YouTube-specific optimization preferences
            
        Returns:
            Complete optimization result with encoding params, SEO metadata, etc.
        """
        try:
            # Generate encoding parameters
            encoding_params = self._generate_encoding_params(
                optimization_settings, content_metadata
            )
            
            # Generate SEO metadata
            seo_metadata = await self._generate_seo_metadata(
                content_metadata, optimization_settings
            )
            
            # Generate thumbnail suggestions
            thumbnail_suggestions = await self._generate_thumbnail_suggestions(
                content_metadata, optimization_settings
            )
            
            # Generate chapter markers
            chapter_markers = await self._generate_chapter_markers(
                content_metadata, optimization_settings
            )
            
            # Generate intro/outro suggestions
            intro_outro = await self._generate_intro_outro_suggestions(
                content_metadata, optimization_settings
            )
            
            # Optimize cinematic settings for YouTube
            optimized_cinematic_settings = self._optimize_cinematic_settings(
                cinematic_settings, optimization_settings
            )
            
            return {
                'encoding_params': encoding_params.to_dict(),
                'seo_metadata': seo_metadata.to_dict(),
                'thumbnail_suggestions': [t.to_dict() for t in thumbnail_suggestions],
                'chapter_markers': [c.to_dict() for c in chapter_markers],
                'intro_outro_suggestions': intro_outro,
                'optimized_cinematic_settings': optimized_cinematic_settings,
                'optimization_summary': {
                    'content_type': optimization_settings.content_type.value,
                    'target_audience': optimization_settings.target_audience,
                    'estimated_performance_score': self._calculate_performance_score(
                        seo_metadata, optimization_settings
                    ),
                    'compliance_status': self._check_youtube_compliance(
                        encoding_params, seo_metadata
                    )
                }
            }
            
        except Exception as e:
            logger.error(f"YouTube optimization failed: {e}")
            return self._create_fallback_optimization(content_metadata, optimization_settings)
    
    def _generate_encoding_params(
        self,
        optimization_settings: YouTubeOptimizationSettings,
        content_metadata: Dict[str, Any]
    ) -> YouTubeEncodingParams:
        """Generate YouTube-optimized encoding parameters."""
        
        # Determine quality based on content type and duration
        duration = content_metadata.get('duration', 600)
        
        if duration > 1800:  # > 30 minutes
            quality = "1080p"  # Lower quality for longer content
        elif optimization_settings.content_type == YouTubeContentType.GAMING:
            quality = "4k"  # High quality for gaming
        elif optimization_settings.content_type == YouTubeContentType.EDUCATIONAL:
            quality = "4k"  # High quality for educational content
        else:
            quality = "4k"  # Default to 4K
        
        encoding_params = YouTubeEncodingParams.from_content_type(
            optimization_settings.content_type, quality
        )
        
        # Adjust for aspect ratio
        if optimization_settings.aspect_ratio == YouTubeAspectRatio.VERTICAL:
            # YouTube Shorts format
            encoding_params.resolution = (1080, 1920)
            encoding_params.video_bitrate = "6000k"
        elif optimization_settings.aspect_ratio == YouTubeAspectRatio.SQUARE:
            encoding_params.resolution = (1080, 1080)
            encoding_params.video_bitrate = "5000k"
        
        return encoding_params
    
    async def _generate_seo_metadata(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> SEOMetadata:
        """Generate SEO-optimized metadata using AI analysis."""
        
        if self.gemini_client and optimization_settings.enable_seo_optimization:
            return await self._generate_seo_with_gemini(content_metadata, optimization_settings)
        else:
            return self._generate_seo_fallback(content_metadata, optimization_settings)
    
    async def _generate_seo_with_gemini(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> SEOMetadata:
        """Generate SEO metadata using Gemini AI."""
        
        content_title = content_metadata.get('title', 'Untitled Video')
        content_description = content_metadata.get('description', '')
        content_type = optimization_settings.content_type.value
        target_audience = optimization_settings.target_audience
        
        prompt = f"""
Generate YouTube SEO-optimized metadata for this video:

Title: {content_title}
Description: {content_description}
Content Type: {content_type}
Target Audience: {target_audience}

Please provide a JSON response with:
{{
    "optimized_title": "<engaging title under 100 characters>",
    "optimized_description": "<detailed description under 5000 characters with keywords>",
    "tags": ["<15 relevant tags>"],
    "category": "<YouTube category>",
    "keywords": ["<primary keywords for SEO>"],
    "hook_suggestions": ["<engaging opening lines>"],
    "cta_suggestions": ["<call-to-action suggestions>"]
}}

Focus on:
- Engaging, clickable titles with keywords
- Comprehensive descriptions with timestamps
- Relevant tags for discoverability
- Clear call-to-actions
- SEO optimization for YouTube algorithm
"""
        
        try:
            response = await self.gemini_client.generate_content(prompt)
            seo_data = self._parse_gemini_seo_response(response)
            
            return SEOMetadata(
                title=seo_data.get('optimized_title', content_title)[:self.title_max_length],
                description=seo_data.get('optimized_description', content_description)[:self.description_max_length],
                tags=seo_data.get('tags', [])[:self.tags_max_count],
                category=seo_data.get('category', 'Education'),
                language='en'
            )
            
        except Exception as e:
            logger.error(f"Gemini SEO generation failed: {e}")
            return self._generate_seo_fallback(content_metadata, optimization_settings)
    
    def _generate_seo_fallback(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> SEOMetadata:
        """Generate fallback SEO metadata using templates."""
        
        content_title = content_metadata.get('title', 'Untitled Video')
        content_description = content_metadata.get('description', '')
        content_type = optimization_settings.content_type
        
        # Generate optimized title
        title_templates = {
            YouTubeContentType.EDUCATIONAL: [
                "Learn {topic} - Complete Guide",
                "Master {topic} in Minutes",
                "{topic} Explained Simply"
            ],
            YouTubeContentType.TUTORIAL: [
                "How to {action} - Step by Step",
                "{action} Tutorial for Beginners",
                "Complete {action} Guide"
            ],
            YouTubeContentType.REVIEW: [
                "{product} Review - Is it Worth It?",
                "Honest {product} Review",
                "{product} - Pros and Cons"
            ]
        }
        
        # Extract key topic from title
        topic = self._extract_main_topic(content_title)
        
        templates = title_templates.get(content_type, ["{topic} - Complete Guide"])
        optimized_title = templates[0].format(topic=topic, action=topic, product=topic)
        
        # Generate tags
        base_tags = [
            topic.lower(),
            content_type.value,
            optimization_settings.target_audience,
            "tutorial" if content_type == YouTubeContentType.TUTORIAL else "educational",
            "guide",
            "how to",
            "learn",
            "explained"
        ]
        
        # Add content-specific tags
        if "math" in content_title.lower():
            base_tags.extend(["mathematics", "math", "calculation", "formula"])
        elif "code" in content_title.lower() or "programming" in content_title.lower():
            base_tags.extend(["programming", "coding", "software", "development"])
        
        # Generate description
        description_template = f"""
{optimized_title}

In this video, we explore {topic} with detailed explanations and practical examples.

🎯 What you'll learn:
- Key concepts and fundamentals
- Practical applications
- Step-by-step guidance
- Real-world examples

📚 Perfect for {optimization_settings.target_audience} learners looking to master {topic}.

👍 Like this video if it helped you!
🔔 Subscribe for more educational content!
💬 Comment below with your questions!

#education #{topic.lower().replace(' ', '')} #{content_type.value}
"""
        
        return SEOMetadata(
            title=optimized_title[:self.title_max_length],
            description=description_template[:self.description_max_length],
            tags=list(set(base_tags))[:self.tags_max_count],
            category="Education",
            language="en"
        )
    
    async def _generate_thumbnail_suggestions(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> List[ThumbnailSuggestion]:
        """Generate thumbnail suggestions for maximum engagement."""
        
        if not optimization_settings.enable_thumbnail_generation:
            return []
        
        duration = content_metadata.get('duration', 600)
        content_title = content_metadata.get('title', '')
        
        suggestions = []
        
        # Opening scene thumbnail (high engagement)
        suggestions.append(ThumbnailSuggestion(
            timestamp=5.0,  # 5 seconds in
            description="Opening scene with clear subject focus",
            visual_elements=["main_subject", "clear_background", "good_lighting"],
            text_overlay=self._generate_thumbnail_text(content_title),
            confidence=0.9,
            color_scheme="high_contrast",
            composition_style="rule_of_thirds"
        ))
        
        # Mid-content thumbnail (key moment)
        mid_point = duration * 0.4  # 40% through the video
        suggestions.append(ThumbnailSuggestion(
            timestamp=mid_point,
            description="Key moment or main concept visualization",
            visual_elements=["key_visual", "engaging_expression", "clear_focus"],
            text_overlay="KEY CONCEPT",
            confidence=0.8,
            color_scheme="vibrant",
            composition_style="centered"
        ))
        
        # Results/conclusion thumbnail
        if duration > 300:  # Only for longer videos
            conclusion_point = duration * 0.8
            suggestions.append(ThumbnailSuggestion(
                timestamp=conclusion_point,
                description="Results or conclusion moment",
                visual_elements=["result_visual", "satisfied_expression", "completion"],
                text_overlay="RESULTS",
                confidence=0.7,
                color_scheme="success_green",
                composition_style="dynamic"
            ))
        
        return suggestions
    
    async def _generate_chapter_markers(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> List[ChapterMarker]:
        """Generate chapter markers for improved navigation."""
        
        if not optimization_settings.enable_chapter_markers:
            return []
        
        duration = content_metadata.get('duration', 600)
        content_title = content_metadata.get('title', '')
        
        markers = []
        
        # Always start with intro
        markers.append(ChapterMarker(
            timestamp=0.0,
            title="Introduction",
            description="Video introduction and overview",
            category="intro"
        ))
        
        # Generate content chapters based on duration and type
        if optimization_settings.content_type == YouTubeContentType.EDUCATIONAL:
            # Educational content structure
            if duration > 300:  # 5+ minutes
                markers.extend([
                    ChapterMarker(
                        timestamp=duration * 0.1,
                        title="Background & Context",
                        description="Setting up the topic and context",
                        category="content"
                    ),
                    ChapterMarker(
                        timestamp=duration * 0.3,
                        title="Core Concepts",
                        description="Main concepts and explanations",
                        category="content"
                    ),
                    ChapterMarker(
                        timestamp=duration * 0.6,
                        title="Examples & Applications",
                        description="Practical examples and applications",
                        category="content"
                    ),
                    ChapterMarker(
                        timestamp=duration * 0.85,
                        title="Summary & Conclusion",
                        description="Key takeaways and conclusion",
                        category="outro"
                    )
                ])
        
        elif optimization_settings.content_type == YouTubeContentType.TUTORIAL:
            # Tutorial structure
            steps = min(5, max(3, int(duration / 120)))  # 1 step per 2 minutes, 3-5 steps
            for i in range(steps):
                step_time = duration * (0.15 + (0.7 * i / (steps - 1)))
                markers.append(ChapterMarker(
                    timestamp=step_time,
                    title=f"Step {i + 1}",
                    description=f"Tutorial step {i + 1}",
                    category="content"
                ))
        
        # Add conclusion if not already present
        if not any(m.category == "outro" for m in markers) and duration > 180:
            markers.append(ChapterMarker(
                timestamp=duration * 0.9,
                title="Conclusion",
                description="Final thoughts and next steps",
                category="outro"
            ))
        
        return sorted(markers, key=lambda x: x.timestamp)
    
    async def _generate_intro_outro_suggestions(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> Dict[str, Any]:
        """Generate intro and outro sequence suggestions."""
        
        if not optimization_settings.enable_intro_outro:
            return {}
        
        content_title = content_metadata.get('title', '')
        content_type = optimization_settings.content_type
        
        intro_suggestions = {
            "duration": 5.0,  # 5 second intro
            "elements": [
                "channel_branding",
                "video_title_display",
                "engaging_hook"
            ],
            "script_suggestions": [
                f"Welcome! Today we're exploring {content_title}",
                f"In this video, you'll learn everything about {content_title}",
                f"Let's dive into {content_title} step by step"
            ],
            "visual_style": "professional_fade_in",
            "audio_style": "upbeat_intro_music"
        }
        
        outro_suggestions = {
            "duration": 10.0,  # 10 second outro
            "elements": [
                "subscribe_reminder",
                "like_button_animation",
                "related_videos",
                "channel_branding"
            ],
            "script_suggestions": [
                "Thanks for watching! Don't forget to subscribe for more content like this.",
                "If this helped you, please like and subscribe!",
                "What would you like to see next? Let me know in the comments!"
            ],
            "visual_style": "call_to_action_overlay",
            "audio_style": "outro_music_fade"
        }
        
        return {
            "intro": intro_suggestions,
            "outro": outro_suggestions,
            "branding_elements": {
                "logo_placement": "bottom_right",
                "color_scheme": "brand_colors",
                "font_style": "modern_sans_serif"
            } if optimization_settings.branding_elements else {}
        }
    
    def _optimize_cinematic_settings(
        self,
        cinematic_settings: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> Dict[str, Any]:
        """Optimize cinematic settings specifically for YouTube."""
        
        optimized_settings = cinematic_settings.copy()
        
        # YouTube-specific optimizations
        if optimization_settings.content_type == YouTubeContentType.EDUCATIONAL:
            # Educational content: prioritize clarity and stability
            if 'camera_movements' in optimized_settings:
                optimized_settings['camera_movements']['intensity'] = min(
                    optimized_settings['camera_movements'].get('intensity', 50), 40
                )
                # Prefer stable movements for educational content
                stable_movements = ['static', 'pan', 'zoom']
                if 'allowed_types' in optimized_settings['camera_movements']:
                    optimized_settings['camera_movements']['allowed_types'] = [
                        t for t in optimized_settings['camera_movements']['allowed_types']
                        if t in stable_movements
                    ]
            
            # Enhance readability
            if 'color_grading' in optimized_settings:
                optimized_settings['color_grading']['contrast'] = max(
                    optimized_settings['color_grading'].get('contrast', 0), 10
                )
        
        elif optimization_settings.content_type == YouTubeContentType.ENTERTAINMENT:
            # Entertainment: more dynamic and engaging
            if 'camera_movements' in optimized_settings:
                optimized_settings['camera_movements']['intensity'] = max(
                    optimized_settings['camera_movements'].get('intensity', 50), 60
                )
            
            if 'color_grading' in optimized_settings:
                optimized_settings['color_grading']['saturation'] = max(
                    optimized_settings['color_grading'].get('saturation', 0), 10
                )
        
        # YouTube Shorts optimizations
        if optimization_settings.enable_shorts_optimization:
            # Optimize for mobile viewing
            if 'advanced_compositing' in optimized_settings:
                optimized_settings['advanced_compositing']['dynamic_lighting'] = True
                optimized_settings['advanced_compositing']['film_grain'] = False  # Can be distracting on mobile
            
            # Enhance visual impact for small screens
            if 'color_grading' in optimized_settings:
                optimized_settings['color_grading']['contrast'] = max(
                    optimized_settings['color_grading'].get('contrast', 0), 20
                )
                optimized_settings['color_grading']['saturation'] = max(
                    optimized_settings['color_grading'].get('saturation', 0), 15
                )
        
        return optimized_settings
    
    def _extract_main_topic(self, title: str) -> str:
        """Extract the main topic from a video title."""
        # Remove common words and extract key terms
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'how', 'what', 'why', 'when', 'where'}
        words = re.findall(r'\b\w+\b', title.lower())
        key_words = [w for w in words if w not in stop_words and len(w) > 2]
        
        if key_words:
            return ' '.join(key_words[:3])  # Take first 3 key words
        else:
            return title[:30]  # Fallback to first 30 characters
    
    def _generate_thumbnail_text(self, title: str) -> str:
        """Generate engaging text overlay for thumbnails."""
        # Extract key words and create short, punchy text
        key_topic = self._extract_main_topic(title)
        
        # Common engaging patterns
        patterns = [
            key_topic.upper(),
            f"LEARN {key_topic.upper()}",
            f"{key_topic.upper()} GUIDE",
            f"MASTER {key_topic.upper()}",
            "EXPLAINED!"
        ]
        
        # Choose based on content
        if "how" in title.lower():
            return f"HOW TO {key_topic.upper()}"
        elif "learn" in title.lower():
            return f"LEARN {key_topic.upper()}"
        else:
            return patterns[0]
    
    def _parse_gemini_seo_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for SEO metadata."""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No valid JSON found in Gemini SEO response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini SEO response: {e}")
            return {}
    
    def _calculate_performance_score(
        self,
        seo_metadata: SEOMetadata,
        optimization_settings: YouTubeOptimizationSettings
    ) -> float:
        """Calculate estimated YouTube performance score (0-100)."""
        
        score = 0.0
        
        # Title optimization (25 points)
        title_length = len(seo_metadata.title)
        if 40 <= title_length <= 70:  # Optimal length
            score += 25
        elif 30 <= title_length <= 90:
            score += 20
        else:
            score += 10
        
        # Description quality (20 points)
        desc_length = len(seo_metadata.description)
        if desc_length >= 200:  # Good description length
            score += 20
        elif desc_length >= 100:
            score += 15
        else:
            score += 5
        
        # Tags optimization (15 points)
        tag_count = len(seo_metadata.tags)
        if 8 <= tag_count <= 15:  # Optimal tag count
            score += 15
        elif 5 <= tag_count <= 20:
            score += 10
        else:
            score += 5
        
        # Content type alignment (20 points)
        if optimization_settings.content_type in [YouTubeContentType.EDUCATIONAL, YouTubeContentType.TUTORIAL]:
            score += 20  # High-performing content types
        else:
            score += 15
        
        # Engagement features (20 points)
        if optimization_settings.enable_thumbnail_generation:
            score += 5
        if optimization_settings.enable_chapter_markers:
            score += 5
        if optimization_settings.enable_intro_outro:
            score += 5
        if optimization_settings.enable_seo_optimization:
            score += 5
        
        return min(100.0, score)
    
    def _check_youtube_compliance(
        self,
        encoding_params: YouTubeEncodingParams,
        seo_metadata: SEOMetadata
    ) -> Dict[str, Any]:
        """Check compliance with YouTube requirements."""
        
        compliance = {
            'overall_status': 'compliant',
            'issues': [],
            'warnings': [],
            'recommendations': []
        }
        
        # Check encoding compliance
        if encoding_params.video_codec != "H.264":
            compliance['issues'].append("Video codec should be H.264 for best compatibility")
        
        if encoding_params.audio_codec != "AAC":
            compliance['issues'].append("Audio codec should be AAC for best compatibility")
        
        if encoding_params.pixel_format != "yuv420p":
            compliance['issues'].append("Pixel format should be yuv420p for best compatibility")
        
        # Check metadata compliance
        if len(seo_metadata.title) > self.title_max_length:
            compliance['issues'].append(f"Title exceeds {self.title_max_length} character limit")
        
        if len(seo_metadata.description) > self.description_max_length:
            compliance['issues'].append(f"Description exceeds {self.description_max_length} character limit")
        
        if len(seo_metadata.tags) > self.tags_max_count:
            compliance['warnings'].append(f"Too many tags (>{self.tags_max_count}), some may be ignored")
        
        # Recommendations
        if len(seo_metadata.title) < 40:
            compliance['recommendations'].append("Consider a longer, more descriptive title")
        
        if len(seo_metadata.description) < 200:
            compliance['recommendations'].append("Add more detail to the description for better SEO")
        
        if len(seo_metadata.tags) < 5:
            compliance['recommendations'].append("Add more relevant tags for better discoverability")
        
        # Set overall status
        if compliance['issues']:
            compliance['overall_status'] = 'non_compliant'
        elif compliance['warnings']:
            compliance['overall_status'] = 'compliant_with_warnings'
        
        return compliance
    
    def _create_fallback_optimization(
        self,
        content_metadata: Dict[str, Any],
        optimization_settings: YouTubeOptimizationSettings
    ) -> Dict[str, Any]:
        """Create fallback optimization when main process fails."""
        
        encoding_params = YouTubeEncodingParams.from_content_type(
            optimization_settings.content_type, "4k"
        )
        
        seo_metadata = SEOMetadata(
            title=content_metadata.get('title', 'Untitled Video')[:self.title_max_length],
            description=content_metadata.get('description', 'Video description')[:self.description_max_length],
            tags=['education', 'tutorial', 'guide'],
            category='Education'
        )
        
        return {
            'encoding_params': encoding_params.to_dict(),
            'seo_metadata': seo_metadata.to_dict(),
            'thumbnail_suggestions': [],
            'chapter_markers': [],
            'intro_outro_suggestions': {},
            'optimized_cinematic_settings': {},
            'optimization_summary': {
                'content_type': optimization_settings.content_type.value,
                'target_audience': optimization_settings.target_audience,
                'estimated_performance_score': 50.0,
                'compliance_status': {'overall_status': 'basic_compliant', 'issues': [], 'warnings': [], 'recommendations': []}
            },
            'fallback_used': True
        }