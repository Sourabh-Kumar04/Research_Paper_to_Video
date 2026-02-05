"""
Multi-Platform Social Media Adaptation System

This module provides platform-specific settings adaptation for Instagram, TikTok, LinkedIn,
aspect ratio conversion, content pacing adjustments, file size optimization, and
platform-specific engagement elements.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
from datetime import datetime
import math

from ..llm.gemini_client import GeminiClient
from .models import CinematicSettingsModel
from .youtube_optimizer import YouTubeEncodingParams


logger = logging.getLogger(__name__)


class SocialPlatform(Enum):
    """Supported social media platforms."""
    YOUTUBE = "youtube"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    LINKEDIN = "linkedin"
    TWITTER = "twitter"
    FACEBOOK = "facebook"


@dataclass
class PlatformRequirements:
    """Technical requirements for a social media platform."""
    max_duration: int  # seconds
    max_file_size: int  # MB
    recommended_resolution: Tuple[int, int]
    aspect_ratios: List[str]
    video_codec: str
    audio_codec: str
    frame_rate_range: Tuple[float, float]
    bitrate_range: Tuple[int, int]  # kbps
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class ContentOptimization:
    """Content optimization settings for platform-specific adaptations."""
    pacing_multiplier: float = 1.0  # 1.0 = normal, >1.0 = faster
    visual_density: str = "medium"  # low, medium, high
    text_size: str = "medium"  # small, medium, large
    subtitles_required: bool = False
    engagement_style: str = "standard"  # standard, dynamic, minimal
    attention_span_seconds: int = 30
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class PlatformAdaptation:
    """Complete platform adaptation result."""
    platform: SocialPlatform
    original_settings: Dict[str, Any]
    adapted_settings: Dict[str, Any]
    encoding_params: Dict[str, Any]
    content_optimizations: ContentOptimization
    adaptations_applied: List[Dict[str, Any]]
    estimated_performance_score: float
    compliance_status: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'platform': self.platform.value,
            'original_settings': self.original_settings,
            'adapted_settings': self.adapted_settings,
            'encoding_params': self.encoding_params,
            'content_optimizations': self.content_optimizations.to_dict(),
            'adaptations_applied': self.adaptations_applied,
            'estimated_performance_score': self.estimated_performance_score,
            'compliance_status': self.compliance_status
        }


class SocialMediaAdapter:
    """Multi-platform social media adaptation system."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client
        self.platform_requirements = self._initialize_platform_requirements()
        self.adaptation_cache = {}
    
    def _initialize_platform_requirements(self) -> Dict[SocialPlatform, PlatformRequirements]:
        """Initialize platform-specific technical requirements."""
        return {
            SocialPlatform.YOUTUBE: PlatformRequirements(
                max_duration=43200,  # 12 hours
                max_file_size=256000,  # 256GB
                recommended_resolution=(1920, 1080),
                aspect_ratios=["16:9", "9:16", "1:1"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(24.0, 60.0),
                bitrate_range=(1000, 50000)
            ),
            
            SocialPlatform.INSTAGRAM: PlatformRequirements(
                max_duration=60,  # 60 seconds for feed posts
                max_file_size=4000,  # 4GB
                recommended_resolution=(1080, 1080),
                aspect_ratios=["1:1", "4:5", "9:16"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(23.0, 60.0),
                bitrate_range=(1000, 8000)
            ),
            
            SocialPlatform.TIKTOK: PlatformRequirements(
                max_duration=180,  # 3 minutes
                max_file_size=287,  # 287MB
                recommended_resolution=(1080, 1920),
                aspect_ratios=["9:16"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(23.0, 60.0),
                bitrate_range=(1000, 10000)
            ),
            
            SocialPlatform.LINKEDIN: PlatformRequirements(
                max_duration=600,  # 10 minutes
                max_file_size=5000,  # 5GB
                recommended_resolution=(1920, 1080),
                aspect_ratios=["16:9", "1:1"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(10.0, 60.0),
                bitrate_range=(1000, 20000)
            ),
            
            SocialPlatform.TWITTER: PlatformRequirements(
                max_duration=140,  # 2 minutes 20 seconds
                max_file_size=512,  # 512MB
                recommended_resolution=(1280, 720),
                aspect_ratios=["16:9", "1:1"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(25.0, 60.0),
                bitrate_range=(1000, 6000)
            ),
            
            SocialPlatform.FACEBOOK: PlatformRequirements(
                max_duration=240,  # 4 minutes
                max_file_size=4000,  # 4GB
                recommended_resolution=(1920, 1080),
                aspect_ratios=["16:9", "1:1", "9:16"],
                video_codec="H.264",
                audio_codec="AAC",
                frame_rate_range=(23.0, 60.0),
                bitrate_range=(1000, 8000)
            )
        }
    
    async def adapt_for_platforms(
        self,
        base_settings: Dict[str, Any],
        content_metadata: Dict[str, Any],
        target_platforms: List[SocialPlatform]
    ) -> Dict[SocialPlatform, PlatformAdaptation]:
        """
        Adapt content for multiple social media platforms.
        
        Args:
            base_settings: Base cinematic settings
            content_metadata: Video content information
            target_platforms: List of platforms to adapt for
            
        Returns:
            Dictionary mapping platforms to their adaptations
        """
        adaptations = {}
        
        for platform in target_platforms:
            try:
                adaptation = await self._adapt_for_single_platform(
                    base_settings, content_metadata, platform
                )
                adaptations[platform] = adaptation
                
            except Exception as e:
                logger.error(f"Failed to adapt for {platform.value}: {e}")
                # Create fallback adaptation
                adaptations[platform] = self._create_fallback_adaptation(
                    base_settings, platform
                )
        
        return adaptations
    
    async def _adapt_for_single_platform(
        self,
        base_settings: Dict[str, Any],
        content_metadata: Dict[str, Any],
        platform: SocialPlatform
    ) -> PlatformAdaptation:
        """Adapt content for a single platform."""
        
        requirements = self.platform_requirements[platform]
        
        # Create platform-specific settings
        adapted_settings = await self._adapt_cinematic_settings(
            base_settings, platform, content_metadata
        )
        
        # Generate encoding parameters
        encoding_params = self._generate_platform_encoding_params(
            platform, content_metadata
        )
        
        # Create content optimizations
        content_optimizations = self._create_content_optimizations(
            platform, content_metadata
        )
        
        # Track adaptations applied
        adaptations_applied = self._track_adaptations(
            base_settings, adapted_settings, platform
        )
        
        # Calculate performance score
        performance_score = self._calculate_platform_performance_score(
            platform, adapted_settings, content_metadata
        )
        
        # Check compliance
        compliance_status = self._check_platform_compliance(
            platform, encoding_params, content_metadata
        )
        
        return PlatformAdaptation(
            platform=platform,
            original_settings=base_settings,
            adapted_settings=adapted_settings,
            encoding_params=encoding_params,
            content_optimizations=content_optimizations,
            adaptations_applied=adaptations_applied,
            estimated_performance_score=performance_score,
            compliance_status=compliance_status
        )
    
    async def _adapt_cinematic_settings(
        self,
        base_settings: Dict[str, Any],
        platform: SocialPlatform,
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt cinematic settings for platform-specific requirements."""
        
        adapted_settings = base_settings.copy()
        
        if platform == SocialPlatform.INSTAGRAM:
            # Instagram optimizations
            adapted_settings = self._adapt_for_instagram(adapted_settings, content_metadata)
            
        elif platform == SocialPlatform.TIKTOK:
            # TikTok optimizations
            adapted_settings = self._adapt_for_tiktok(adapted_settings, content_metadata)
            
        elif platform == SocialPlatform.LINKEDIN:
            # LinkedIn optimizations
            adapted_settings = self._adapt_for_linkedin(adapted_settings, content_metadata)
            
        elif platform == SocialPlatform.TWITTER:
            # Twitter optimizations
            adapted_settings = self._adapt_for_twitter(adapted_settings, content_metadata)
        
        elif platform == SocialPlatform.FACEBOOK:
            # Facebook optimizations
            adapted_settings = self._adapt_for_facebook(adapted_settings, content_metadata)
        
        return adapted_settings
    
    def _adapt_for_instagram(
        self, 
        settings: Dict[str, Any], 
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt settings specifically for Instagram."""
        adapted = settings.copy()
        
        # Instagram prefers square or portrait aspect ratios
        adapted['aspect_ratio'] = '1:1'  # Default to square
        adapted['resolution'] = (1080, 1080)
        
        # Increase visual appeal for mobile viewing
        if 'color_grading' in adapted:
            adapted['color_grading']['saturation'] = min(
                adapted['color_grading'].get('saturation', 1.0) * 1.2, 2.0
            )
            adapted['color_grading']['contrast'] = min(
                adapted['color_grading'].get('contrast', 1.0) * 1.1, 1.5
            )
        
        # Optimize for mobile attention spans
        if 'transitions' in adapted:
            adapted['transitions']['speed'] = min(
                adapted['transitions'].get('speed', 1.0) * 1.3, 2.0
            )
        
        # Add Instagram-specific elements
        adapted['platform_optimizations'] = {
            'add_captions': True,
            'hook_duration': 3,  # Strong hook in first 3 seconds
            'visual_density': 'high',
            'engagement_cues': True
        }
        
        return adapted
    
    def _adapt_for_tiktok(
        self, 
        settings: Dict[str, Any], 
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt settings specifically for TikTok."""
        adapted = settings.copy()
        
        # TikTok requires vertical format
        adapted['aspect_ratio'] = '9:16'
        adapted['resolution'] = (1080, 1920)
        
        # Optimize for very short attention spans
        if 'transitions' in adapted:
            adapted['transitions']['speed'] = min(
                adapted['transitions'].get('speed', 1.0) * 1.5, 2.5
            )
        
        # Enhance visual impact for mobile
        if 'color_grading' in adapted:
            adapted['color_grading']['saturation'] = min(
                adapted['color_grading'].get('saturation', 1.0) * 1.3, 2.2
            )
            adapted['color_grading']['brightness'] = min(
                adapted['color_grading'].get('brightness', 1.0) * 1.1, 1.3
            )
        
        # TikTok-specific optimizations
        adapted['platform_optimizations'] = {
            'add_captions': True,
            'hook_duration': 2,  # Even stronger hook in first 2 seconds
            'visual_density': 'very_high',
            'engagement_cues': True,
            'trending_elements': True,
            'music_sync': True
        }
        
        return adapted
    
    def _adapt_for_linkedin(
        self, 
        settings: Dict[str, Any], 
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt settings specifically for LinkedIn."""
        adapted = settings.copy()
        
        # LinkedIn prefers professional 16:9 format
        adapted['aspect_ratio'] = '16:9'
        adapted['resolution'] = (1920, 1080)
        
        # Professional, clean aesthetic
        if 'color_grading' in adapted:
            adapted['color_grading']['saturation'] = max(
                adapted['color_grading'].get('saturation', 1.0) * 0.9, 0.7
            )
            adapted['color_grading']['contrast'] = min(
                adapted['color_grading'].get('contrast', 1.0) * 1.05, 1.2
            )
        
        # Slower, more professional pacing
        if 'transitions' in adapted:
            adapted['transitions']['speed'] = max(
                adapted['transitions'].get('speed', 1.0) * 0.8, 0.5
            )
        
        # LinkedIn-specific optimizations
        adapted['platform_optimizations'] = {
            'add_captions': True,
            'professional_tone': True,
            'hook_duration': 5,  # Longer hook for professional content
            'visual_density': 'medium',
            'call_to_action': 'professional'
        }
        
        return adapted
    
    def _adapt_for_twitter(
        self, 
        settings: Dict[str, Any], 
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt settings specifically for Twitter."""
        adapted = settings.copy()
        
        # Twitter supports both 16:9 and square
        adapted['aspect_ratio'] = '16:9'
        adapted['resolution'] = (1280, 720)
        
        # Optimize for quick consumption
        if 'transitions' in adapted:
            adapted['transitions']['speed'] = min(
                adapted['transitions'].get('speed', 1.0) * 1.2, 2.0
            )
        
        # Twitter-specific optimizations
        adapted['platform_optimizations'] = {
            'add_captions': True,
            'hook_duration': 3,
            'visual_density': 'medium',
            'engagement_cues': True,
            'hashtag_friendly': True
        }
        
        return adapted
    
    def _adapt_for_facebook(
        self, 
        settings: Dict[str, Any], 
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Adapt settings specifically for Facebook."""
        adapted = settings.copy()
        
        # Facebook supports multiple formats
        adapted['aspect_ratio'] = '16:9'  # Default to landscape
        adapted['resolution'] = (1920, 1080)
        
        # Facebook-specific optimizations
        adapted['platform_optimizations'] = {
            'add_captions': True,
            'hook_duration': 3,
            'visual_density': 'medium',
            'engagement_cues': True,
            'auto_play_friendly': True,
            'sound_optional': True  # Many Facebook videos play without sound initially
        }
        
        return adapted
    
    def _generate_platform_encoding_params(
        self,
        platform: SocialPlatform,
        content_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate platform-specific encoding parameters."""
        
        requirements = self.platform_requirements[platform]
        
        # Base encoding parameters
        encoding_params = {
            'video_codec': requirements.video_codec,
            'audio_codec': requirements.audio_codec,
            'resolution': requirements.recommended_resolution,
            'frame_rate': min(30.0, requirements.frame_rate_range[1]),
            'pixel_format': 'yuv420p'
        }
        
        # Calculate optimal bitrate based on content and platform
        content_complexity = content_metadata.get('complexity_score', 0.5)
        duration = content_metadata.get('duration', 60)
        
        # Adjust bitrate based on platform and content
        base_bitrate = requirements.bitrate_range[0]
        max_bitrate = requirements.bitrate_range[1]
        
        # Higher complexity content needs higher bitrate
        complexity_multiplier = 1.0 + (content_complexity * 0.5)
        target_bitrate = int(base_bitrate * complexity_multiplier)
        
        # Ensure within platform limits
        encoding_params['video_bitrate'] = min(target_bitrate, max_bitrate)
        encoding_params['audio_bitrate'] = 128  # Standard audio bitrate
        
        # Platform-specific optimizations
        if platform == SocialPlatform.TIKTOK:
            # TikTok benefits from higher quality for mobile viewing
            encoding_params['video_bitrate'] = min(
                encoding_params['video_bitrate'] * 1.2, max_bitrate
            )
        elif platform == SocialPlatform.INSTAGRAM:
            # Instagram has strict file size limits
            encoding_params['video_bitrate'] = min(
                encoding_params['video_bitrate'], 6000
            )
        
        # Add file size estimation
        estimated_size_mb = self._estimate_file_size(
            encoding_params, duration
        )
        encoding_params['estimated_file_size_mb'] = estimated_size_mb
        
        return encoding_params
    
    def _create_content_optimizations(
        self,
        platform: SocialPlatform,
        content_metadata: Dict[str, Any]
    ) -> ContentOptimization:
        """Create platform-specific content optimizations."""
        
        content_type = content_metadata.get('content_type', 'general')
        
        if platform == SocialPlatform.TIKTOK:
            return ContentOptimization(
                pacing_multiplier=1.5,
                visual_density="high",
                text_size="large",
                subtitles_required=True,
                engagement_style="dynamic",
                attention_span_seconds=15
            )
        elif platform == SocialPlatform.INSTAGRAM:
            return ContentOptimization(
                pacing_multiplier=1.3,
                visual_density="high",
                text_size="medium",
                subtitles_required=True,
                engagement_style="dynamic",
                attention_span_seconds=20
            )
        elif platform == SocialPlatform.LINKEDIN:
            return ContentOptimization(
                pacing_multiplier=0.8,
                visual_density="medium",
                text_size="medium",
                subtitles_required=True,
                engagement_style="standard",
                attention_span_seconds=45
            )
        elif platform == SocialPlatform.TWITTER:
            return ContentOptimization(
                pacing_multiplier=1.2,
                visual_density="medium",
                text_size="medium",
                subtitles_required=True,
                engagement_style="dynamic",
                attention_span_seconds=25
            )
        else:  # YouTube and others
            return ContentOptimization(
                pacing_multiplier=1.0,
                visual_density="medium",
                text_size="medium",
                subtitles_required=False,
                engagement_style="standard",
                attention_span_seconds=60
            )
    
    def _track_adaptations(
        self,
        original_settings: Dict[str, Any],
        adapted_settings: Dict[str, Any],
        platform: SocialPlatform
    ) -> List[Dict[str, Any]]:
        """Track what adaptations were applied."""
        
        adaptations = []
        
        # Check for aspect ratio changes
        if original_settings.get('aspect_ratio') != adapted_settings.get('aspect_ratio'):
            adaptations.append({
                'type': 'aspect_ratio',
                'original': original_settings.get('aspect_ratio'),
                'adapted': adapted_settings.get('aspect_ratio'),
                'reason': f'Platform {platform.value} optimization'
            })
        
        # Check for resolution changes
        if original_settings.get('resolution') != adapted_settings.get('resolution'):
            adaptations.append({
                'type': 'resolution',
                'original': original_settings.get('resolution'),
                'adapted': adapted_settings.get('resolution'),
                'reason': f'Platform {platform.value} requirements'
            })
        
        # Check for color grading changes
        original_color = original_settings.get('color_grading', {})
        adapted_color = adapted_settings.get('color_grading', {})
        
        for param in ['saturation', 'contrast', 'brightness']:
            if original_color.get(param) != adapted_color.get(param):
                adaptations.append({
                    'type': f'color_grading_{param}',
                    'original': original_color.get(param),
                    'adapted': adapted_color.get(param),
                    'reason': f'Platform {platform.value} visual optimization'
                })
        
        # Check for transition speed changes
        original_transitions = original_settings.get('transitions', {})
        adapted_transitions = adapted_settings.get('transitions', {})
        
        if original_transitions.get('speed') != adapted_transitions.get('speed'):
            adaptations.append({
                'type': 'transition_speed',
                'original': original_transitions.get('speed'),
                'adapted': adapted_transitions.get('speed'),
                'reason': f'Platform {platform.value} pacing optimization'
            })
        
        return adaptations
    
    def _calculate_platform_performance_score(
        self,
        platform: SocialPlatform,
        adapted_settings: Dict[str, Any],
        content_metadata: Dict[str, Any]
    ) -> float:
        """Calculate estimated performance score for the platform."""
        
        score = 0.0
        max_score = 100.0
        
        # Aspect ratio optimization (20 points)
        requirements = self.platform_requirements[platform]
        current_aspect = adapted_settings.get('aspect_ratio', '16:9')
        if current_aspect in requirements.aspect_ratios:
            score += 20.0
        
        # Resolution optimization (15 points)
        current_resolution = adapted_settings.get('resolution', (1920, 1080))
        recommended_resolution = requirements.recommended_resolution
        
        # Calculate resolution match score
        resolution_match = min(
            current_resolution[0] / recommended_resolution[0],
            current_resolution[1] / recommended_resolution[1]
        )
        score += 15.0 * resolution_match
        
        # Content type alignment (20 points)
        content_type = content_metadata.get('content_type', 'general')
        platform_preferences = {
            SocialPlatform.TIKTOK: ['entertainment', 'educational', 'trending'],
            SocialPlatform.INSTAGRAM: ['lifestyle', 'visual', 'entertainment'],
            SocialPlatform.LINKEDIN: ['professional', 'educational', 'business'],
            SocialPlatform.TWITTER: ['news', 'commentary', 'quick_tips']
        }
        
        if content_type in platform_preferences.get(platform, []):
            score += 20.0
        else:
            score += 10.0  # Partial credit for general content
        
        # Duration optimization (15 points)
        duration = content_metadata.get('duration', 60)
        max_duration = requirements.max_duration
        
        if duration <= max_duration:
            # Bonus for optimal duration ranges per platform
            optimal_ranges = {
                SocialPlatform.TIKTOK: (15, 60),
                SocialPlatform.INSTAGRAM: (15, 30),
                SocialPlatform.LINKEDIN: (30, 120),
                SocialPlatform.TWITTER: (15, 45)
            }
            
            optimal_range = optimal_ranges.get(platform, (30, 300))
            if optimal_range[0] <= duration <= optimal_range[1]:
                score += 15.0
            else:
                score += 10.0
        else:
            score += 5.0  # Penalty for exceeding duration
        
        # Visual optimization (15 points)
        platform_optimizations = adapted_settings.get('platform_optimizations', {})
        
        optimization_features = [
            'add_captions', 'hook_duration', 'visual_density', 'engagement_cues'
        ]
        
        for feature in optimization_features:
            if feature in platform_optimizations:
                score += 15.0 / len(optimization_features)
        
        # Engagement potential (15 points)
        engagement_score = self._calculate_engagement_potential(
            platform, adapted_settings, content_metadata
        )
        score += 15.0 * engagement_score
        
        return min(score, max_score)
    
    def _calculate_engagement_potential(
        self,
        platform: SocialPlatform,
        settings: Dict[str, Any],
        content_metadata: Dict[str, Any]
    ) -> float:
        """Calculate engagement potential score (0.0 to 1.0)."""
        
        engagement_factors = []
        
        # Hook strength
        platform_opts = settings.get('platform_optimizations', {})
        hook_duration = platform_opts.get('hook_duration', 5)
        
        # Shorter hooks generally perform better on social media
        hook_score = max(0.0, 1.0 - (hook_duration - 2) / 8)
        engagement_factors.append(hook_score)
        
        # Visual appeal
        color_grading = settings.get('color_grading', {})
        saturation = color_grading.get('saturation', 1.0)
        contrast = color_grading.get('contrast', 1.0)
        
        # Higher saturation and contrast generally perform better on social
        visual_score = min(1.0, (saturation + contrast - 1.0) / 1.0)
        engagement_factors.append(visual_score)
        
        # Content type alignment
        content_type = content_metadata.get('content_type', 'general')
        high_engagement_types = ['entertainment', 'educational', 'trending', 'lifestyle']
        
        content_score = 1.0 if content_type in high_engagement_types else 0.6
        engagement_factors.append(content_score)
        
        # Platform-specific features
        feature_score = 0.0
        if platform_opts.get('engagement_cues'):
            feature_score += 0.3
        if platform_opts.get('add_captions'):
            feature_score += 0.3
        if platform_opts.get('trending_elements'):
            feature_score += 0.4
        
        engagement_factors.append(min(1.0, feature_score))
        
        return sum(engagement_factors) / len(engagement_factors)
    
    def _check_platform_compliance(
        self,
        platform: SocialPlatform,
        encoding_params: Dict[str, Any],
        content_metadata: Dict[str, Any]
    ) -> str:
        """Check compliance with platform requirements."""
        
        requirements = self.platform_requirements[platform]
        issues = []
        
        # Check duration
        duration = content_metadata.get('duration', 0)
        if duration > requirements.max_duration:
            issues.append(f"Duration {duration}s exceeds limit {requirements.max_duration}s")
        
        # Check file size
        estimated_size = encoding_params.get('estimated_file_size_mb', 0)
        if estimated_size > requirements.max_file_size:
            issues.append(f"File size {estimated_size}MB exceeds limit {requirements.max_file_size}MB")
        
        # Check frame rate
        frame_rate = encoding_params.get('frame_rate', 30)
        if not (requirements.frame_rate_range[0] <= frame_rate <= requirements.frame_rate_range[1]):
            issues.append(f"Frame rate {frame_rate} outside range {requirements.frame_rate_range}")
        
        # Check bitrate
        bitrate = encoding_params.get('video_bitrate', 0)
        if not (requirements.bitrate_range[0] <= bitrate <= requirements.bitrate_range[1]):
            issues.append(f"Bitrate {bitrate} outside range {requirements.bitrate_range}")
        
        if not issues:
            return "compliant"
        elif len(issues) <= 2:
            return "minor_issues"
        else:
            return "major_issues"
    
    def _estimate_file_size(
        self,
        encoding_params: Dict[str, Any],
        duration: float
    ) -> float:
        """Estimate file size in MB."""
        
        video_bitrate = encoding_params.get('video_bitrate', 2000)  # kbps
        audio_bitrate = encoding_params.get('audio_bitrate', 128)   # kbps
        
        total_bitrate_kbps = video_bitrate + audio_bitrate
        total_bitrate_mbps = total_bitrate_kbps / 1000.0
        
        # File size = bitrate * duration / 8 (convert bits to bytes)
        file_size_mb = (total_bitrate_mbps * duration) / 8.0
        
        # Add 10% overhead for container and metadata
        return file_size_mb * 1.1
    
    def _create_fallback_adaptation(
        self,
        base_settings: Dict[str, Any],
        platform: SocialPlatform
    ) -> PlatformAdaptation:
        """Create a fallback adaptation when normal adaptation fails."""
        
        requirements = self.platform_requirements[platform]
        
        # Basic safe adaptations
        adapted_settings = base_settings.copy()
        adapted_settings['resolution'] = requirements.recommended_resolution
        adapted_settings['aspect_ratio'] = requirements.aspect_ratios[0]
        
        encoding_params = {
            'video_codec': requirements.video_codec,
            'audio_codec': requirements.audio_codec,
            'resolution': requirements.recommended_resolution,
            'frame_rate': 30.0,
            'video_bitrate': requirements.bitrate_range[0],
            'audio_bitrate': 128,
            'estimated_file_size_mb': 50.0  # Conservative estimate
        }
        
        content_optimizations = ContentOptimization()
        
        return PlatformAdaptation(
            platform=platform,
            original_settings=base_settings,
            adapted_settings=adapted_settings,
            encoding_params=encoding_params,
            content_optimizations=content_optimizations,
            adaptations_applied=[{
                'type': 'fallback',
                'reason': 'Adaptation failed, using safe defaults'
            }],
            estimated_performance_score=50.0,
            compliance_status="basic_compliance"
        )
    
    async def analyze_content_for_platforms(
        self,
        content_metadata: Dict[str, Any],
        target_platforms: List[SocialPlatform]
    ) -> Dict[str, Any]:
        """Analyze content and provide platform-specific recommendations."""
        
        if not self.gemini_client:
            return self._basic_content_analysis(content_metadata, target_platforms)
        
        try:
            # Use Gemini for advanced content analysis
            analysis_prompt = self._create_content_analysis_prompt(
                content_metadata, target_platforms
            )
            
            analysis_result = await self.gemini_client.generate_content_async(
                analysis_prompt
            )
            
            return self._parse_content_analysis(analysis_result, target_platforms)
            
        except Exception as e:
            logger.error(f"Gemini content analysis failed: {e}")
            return self._basic_content_analysis(content_metadata, target_platforms)
    
    def _create_content_analysis_prompt(
        self,
        content_metadata: Dict[str, Any],
        target_platforms: List[SocialPlatform]
    ) -> str:
        """Create prompt for Gemini content analysis."""
        
        platforms_str = ", ".join([p.value for p in target_platforms])
        
        return f"""
        Analyze the following video content for social media optimization across {platforms_str}:
        
        Content Metadata:
        - Title: {content_metadata.get('title', 'Unknown')}
        - Description: {content_metadata.get('description', 'No description')}
        - Duration: {content_metadata.get('duration', 0)} seconds
        - Content Type: {content_metadata.get('content_type', 'general')}
        - Topics: {content_metadata.get('topics', [])}
        
        Please provide:
        1. Content classification (educational, entertainment, professional, etc.)
        2. Optimal platform ranking for this content
        3. Key engagement strategies for each platform
        4. Recommended adaptations (pacing, visual style, etc.)
        5. Potential viral elements or hooks
        6. Audience targeting recommendations
        
        Format as JSON with clear recommendations for each platform.
        """
    
    def _parse_content_analysis(
        self,
        analysis_result: str,
        target_platforms: List[SocialPlatform]
    ) -> Dict[str, Any]:
        """Parse Gemini analysis result."""
        
        try:
            # Try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', analysis_result, re.DOTALL)
            
            if json_match:
                analysis_data = json.loads(json_match.group())
                return analysis_data
            else:
                # Fallback to text parsing
                return {
                    'content_classification': 'general',
                    'platform_ranking': [p.value for p in target_platforms],
                    'engagement_strategies': {},
                    'recommendations': analysis_result
                }
                
        except Exception as e:
            logger.error(f"Failed to parse content analysis: {e}")
            return self._basic_content_analysis({}, target_platforms)
    
    def _basic_content_analysis(
        self,
        content_metadata: Dict[str, Any],
        target_platforms: List[SocialPlatform]
    ) -> Dict[str, Any]:
        """Basic content analysis without AI."""
        
        content_type = content_metadata.get('content_type', 'general')
        duration = content_metadata.get('duration', 60)
        
        # Basic platform ranking based on content type and duration
        platform_scores = {}
        
        for platform in target_platforms:
            score = 50.0  # Base score
            
            # Duration-based scoring
            requirements = self.platform_requirements[platform]
            if duration <= requirements.max_duration:
                score += 20.0
            
            # Content type alignment
            if platform == SocialPlatform.TIKTOK and content_type in ['entertainment', 'educational']:
                score += 15.0
            elif platform == SocialPlatform.LINKEDIN and content_type in ['professional', 'educational']:
                score += 15.0
            elif platform == SocialPlatform.INSTAGRAM and content_type in ['lifestyle', 'visual']:
                score += 15.0
            
            platform_scores[platform.value] = score
        
        # Sort platforms by score
        ranked_platforms = sorted(
            platform_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return {
            'content_classification': content_type,
            'platform_ranking': [p[0] for p in ranked_platforms],
            'platform_scores': platform_scores,
            'engagement_strategies': {
                'general': 'Focus on strong opening hook and clear value proposition'
            },
            'recommendations': 'Basic analysis - consider enabling AI analysis for detailed insights'
        }