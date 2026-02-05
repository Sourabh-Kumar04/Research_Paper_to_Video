"""
Content-Aware Cinematic Recommendation System
Analyzes content and provides intelligent cinematic setting recommendations.
"""

import asyncio
import re
import json
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from datetime import datetime

from .models import CinematicSettingsModel, CameraMovementType, FilmEmulationType

logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content type classifications."""
    MATHEMATICAL = "mathematical"
    ARCHITECTURAL = "architectural"
    ANALYTICAL = "analytical"
    PROCEDURAL = "procedural"
    INTRODUCTORY = "introductory"
    CONCLUSION = "conclusion"
    GENERAL = "general"


class ComplexityLevel(Enum):
    """Content complexity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class MoodType(Enum):
    """Content mood types."""
    SERIOUS = "serious"
    POSITIVE = "positive"
    WELCOMING = "welcoming"
    NEUTRAL = "neutral"
    TECHNICAL = "technical"


@dataclass
class ContentAnalysis:
    """Content analysis result."""
    content_type: ContentType
    complexity: ComplexityLevel
    mood: MoodType
    pacing: str  # "slow", "medium", "fast"
    technical_level: str  # "beginner", "intermediate", "advanced"
    key_terms: List[str]
    confidence: float
    reasoning: str


@dataclass
class CinematicRecommendation:
    """Cinematic setting recommendation."""
    feature: str
    setting: str
    value: Any
    reasoning: str
    confidence: float
    priority: int  # 1-5, higher is more important


@dataclass
class RecommendationResult:
    """Complete recommendation result."""
    content_analysis: ContentAnalysis
    recommendations: List[CinematicRecommendation]
    suggested_settings: CinematicSettingsModel
    template_applied: str
    confidence: float
    generated_at: str


class ContentAnalyzer:
    """Analyzes content to determine characteristics for cinematic recommendations."""
    
    def __init__(self):
        # Content type patterns
        self.mathematical_patterns = [
            r'\b(?:equation|formula|theorem|proof|calculate|derivative|integral|matrix|vector)\b',
            r'\b(?:algorithm|complexity|O\(|big-o|logarithm|exponential)\b',
            r'[∑∏∫∂∇∆]|[α-ωΑ-Ω]|\b(?:sin|cos|tan|log|ln|exp)\b',
            r'\b(?:function|variable|parameter|coefficient|constant)\b'
        ]
        
        self.architectural_patterns = [
            r'\b(?:architecture|system|design|structure|component|module)\b',
            r'\b(?:framework|pattern|interface|api|service|layer)\b',
            r'\b(?:database|server|client|network|protocol|infrastructure)\b',
            r'\b(?:class|object|inheritance|polymorphism|encapsulation)\b'
        ]
        
        self.analytical_patterns = [
            r'\b(?:result|data|analysis|performance|benchmark|metric)\b',
            r'\b(?:comparison|evaluation|assessment|measurement|statistics)\b',
            r'\b(?:graph|chart|table|figure|visualization|plot)\b',
            r'\b(?:correlation|regression|variance|deviation|distribution)\b'
        ]
        
        self.procedural_patterns = [
            r'\b(?:step|process|method|procedure|algorithm|workflow)\b',
            r'\b(?:first|second|third|next|then|finally|lastly)\b',
            r'\b(?:implementation|execution|operation|instruction|guide)\b',
            r'\b(?:iterate|loop|condition|branch|decision|control)\b'
        ]
        
        self.introductory_patterns = [
            r'\b(?:introduction|overview|welcome|begin|start|outline)\b',
            r'\b(?:motivation|background|context|purpose|goal|objective)\b',
            r'\b(?:problem|challenge|question|hypothesis|research)\b',
            r'\b(?:scope|limitation|assumption|definition|terminology)\b'
        ]
        
        self.conclusion_patterns = [
            r'\b(?:conclusion|summary|result|finding|outcome|achievement)\b',
            r'\b(?:future|work|research|improvement|enhancement|extension)\b',
            r'\b(?:limitation|challenge|issue|problem|solution|recommendation)\b',
            r'\b(?:impact|significance|contribution|implication|application)\b'
        ]
        
        # Complexity indicators
        self.high_complexity_terms = [
            'advanced', 'complex', 'sophisticated', 'intricate', 'elaborate',
            'comprehensive', 'detailed', 'thorough', 'extensive', 'in-depth'
        ]
        
        self.low_complexity_terms = [
            'simple', 'basic', 'elementary', 'fundamental', 'straightforward',
            'easy', 'clear', 'obvious', 'direct', 'minimal'
        ]
        
        # Mood indicators
        self.positive_terms = [
            'success', 'achievement', 'breakthrough', 'improvement', 'solution',
            'effective', 'efficient', 'optimal', 'excellent', 'outstanding'
        ]
        
        self.serious_terms = [
            'problem', 'challenge', 'difficult', 'critical', 'important',
            'significant', 'crucial', 'essential', 'vital', 'necessary'
        ]
        
        self.technical_terms = [
            'implementation', 'specification', 'protocol', 'standard', 'format',
            'syntax', 'semantic', 'compilation', 'execution', 'optimization'
        ]
    
    def analyze_content(self, content: str, context: Optional[Dict[str, Any]] = None) -> ContentAnalysis:
        """Analyze content to determine characteristics."""
        content_lower = content.lower()
        
        # Determine content type
        content_type = self._determine_content_type(content_lower)
        
        # Determine complexity
        complexity = self._determine_complexity(content_lower, content)
        
        # Determine mood
        mood = self._determine_mood(content_lower)
        
        # Determine pacing
        pacing = self._determine_pacing(content_lower, content_type)
        
        # Determine technical level
        technical_level = self._determine_technical_level(content_lower, complexity)
        
        # Extract key terms
        key_terms = self._extract_key_terms(content)
        
        # Calculate confidence
        confidence = self._calculate_analysis_confidence(content, content_type, complexity, mood)
        
        # Generate reasoning
        reasoning = self._generate_analysis_reasoning(content_type, complexity, mood, pacing)
        
        return ContentAnalysis(
            content_type=content_type,
            complexity=complexity,
            mood=mood,
            pacing=pacing,
            technical_level=technical_level,
            key_terms=key_terms,
            confidence=confidence,
            reasoning=reasoning
        )
    
    def _determine_content_type(self, content_lower: str) -> ContentType:
        """Determine the primary content type."""
        type_scores = {
            ContentType.MATHEMATICAL: self._count_pattern_matches(content_lower, self.mathematical_patterns),
            ContentType.ARCHITECTURAL: self._count_pattern_matches(content_lower, self.architectural_patterns),
            ContentType.ANALYTICAL: self._count_pattern_matches(content_lower, self.analytical_patterns),
            ContentType.PROCEDURAL: self._count_pattern_matches(content_lower, self.procedural_patterns),
            ContentType.INTRODUCTORY: self._count_pattern_matches(content_lower, self.introductory_patterns),
            ContentType.CONCLUSION: self._count_pattern_matches(content_lower, self.conclusion_patterns)
        }
        
        # Find the type with highest score
        max_score = max(type_scores.values())
        if max_score == 0:
            return ContentType.GENERAL
        
        for content_type, score in type_scores.items():
            if score == max_score:
                return content_type
        
        return ContentType.GENERAL
    
    def _determine_complexity(self, content_lower: str, original_content: str) -> ComplexityLevel:
        """Determine content complexity level."""
        # Count complexity indicators
        high_complexity_count = sum(1 for term in self.high_complexity_terms if term in content_lower)
        low_complexity_count = sum(1 for term in self.low_complexity_terms if term in content_lower)
        
        # Consider sentence length and structure
        sentences = original_content.split('.')
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences) if sentences else 0
        
        # Consider technical terminology density
        technical_density = sum(1 for term in self.technical_terms if term in content_lower) / len(content_lower.split())
        
        # Calculate complexity score
        complexity_score = 0
        
        if high_complexity_count > low_complexity_count:
            complexity_score += 2
        elif low_complexity_count > high_complexity_count:
            complexity_score -= 2
        
        if avg_sentence_length > 20:
            complexity_score += 1
        elif avg_sentence_length < 10:
            complexity_score -= 1
        
        if technical_density > 0.1:
            complexity_score += 1
        
        # Determine complexity level
        if complexity_score >= 2:
            return ComplexityLevel.HIGH
        elif complexity_score <= -2:
            return ComplexityLevel.LOW
        else:
            return ComplexityLevel.MEDIUM
    
    def _determine_mood(self, content_lower: str) -> MoodType:
        """Determine content mood."""
        positive_count = sum(1 for term in self.positive_terms if term in content_lower)
        serious_count = sum(1 for term in self.serious_terms if term in content_lower)
        technical_count = sum(1 for term in self.technical_terms if term in content_lower)
        
        # Check for welcoming language
        welcoming_terms = ['welcome', 'introduction', 'hello', 'greetings', 'overview']
        welcoming_count = sum(1 for term in welcoming_terms if term in content_lower)
        
        # Determine dominant mood
        mood_scores = {
            MoodType.POSITIVE: positive_count,
            MoodType.SERIOUS: serious_count,
            MoodType.TECHNICAL: technical_count,
            MoodType.WELCOMING: welcoming_count
        }
        
        max_score = max(mood_scores.values())
        if max_score == 0:
            return MoodType.NEUTRAL
        
        for mood, score in mood_scores.items():
            if score == max_score:
                return mood
        
        return MoodType.NEUTRAL
    
    def _determine_pacing(self, content_lower: str, content_type: ContentType) -> str:
        """Determine appropriate pacing for content."""
        # Fast pacing indicators
        fast_terms = ['quick', 'rapid', 'fast', 'immediate', 'instant', 'brief']
        fast_count = sum(1 for term in fast_terms if term in content_lower)
        
        # Slow pacing indicators
        slow_terms = ['detailed', 'thorough', 'comprehensive', 'careful', 'gradual']
        slow_count = sum(1 for term in slow_terms if term in content_lower)
        
        # Content type influences pacing
        if content_type == ContentType.MATHEMATICAL:
            return "slow"  # Math needs careful explanation
        elif content_type == ContentType.ANALYTICAL:
            return "slow"  # Data needs time to digest
        elif content_type == ContentType.PROCEDURAL:
            return "medium"  # Steps need clear pacing
        elif content_type == ContentType.INTRODUCTORY:
            return "medium"  # Welcoming but informative
        
        # Use term counts
        if fast_count > slow_count:
            return "fast"
        elif slow_count > fast_count:
            return "slow"
        else:
            return "medium"
    
    def _determine_technical_level(self, content_lower: str, complexity: ComplexityLevel) -> str:
        """Determine technical level of content."""
        beginner_terms = ['basic', 'introduction', 'simple', 'overview', 'fundamental']
        advanced_terms = ['advanced', 'sophisticated', 'complex', 'detailed', 'comprehensive']
        
        beginner_count = sum(1 for term in beginner_terms if term in content_lower)
        advanced_count = sum(1 for term in advanced_terms if term in content_lower)
        
        # Complexity influences technical level
        if complexity == ComplexityLevel.HIGH:
            return "advanced"
        elif complexity == ComplexityLevel.LOW:
            return "beginner"
        
        # Use term counts
        if advanced_count > beginner_count:
            return "advanced"
        elif beginner_count > advanced_count:
            return "beginner"
        else:
            return "intermediate"
    
    def _extract_key_terms(self, content: str) -> List[str]:
        """Extract key terms from content."""
        # Simple keyword extraction (could be enhanced with NLP)
        words = re.findall(r'\b[a-zA-Z]{4,}\b', content.lower())
        
        # Filter common words
        common_words = {
            'this', 'that', 'with', 'have', 'will', 'from', 'they', 'been',
            'were', 'said', 'each', 'which', 'their', 'time', 'would', 'there',
            'what', 'about', 'when', 'where', 'more', 'some', 'like', 'into'
        }
        
        key_terms = [word for word in words if word not in common_words]
        
        # Count frequency and return top terms
        term_counts = {}
        for term in key_terms:
            term_counts[term] = term_counts.get(term, 0) + 1
        
        # Sort by frequency and return top 10
        sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
        return [term for term, count in sorted_terms[:10]]
    
    def _count_pattern_matches(self, content: str, patterns: List[str]) -> int:
        """Count matches for a list of regex patterns."""
        total_matches = 0
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            total_matches += len(matches)
        return total_matches
    
    def _calculate_analysis_confidence(self, content: str, content_type: ContentType, 
                                     complexity: ComplexityLevel, mood: MoodType) -> float:
        """Calculate confidence in the analysis."""
        base_confidence = 0.7
        
        # Longer content generally gives more confidence
        word_count = len(content.split())
        if word_count > 100:
            base_confidence += 0.1
        elif word_count < 20:
            base_confidence -= 0.2
        
        # Strong type indicators increase confidence
        if content_type != ContentType.GENERAL:
            base_confidence += 0.1
        
        # Clear complexity indicators increase confidence
        if complexity != ComplexityLevel.MEDIUM:
            base_confidence += 0.05
        
        # Clear mood indicators increase confidence
        if mood != MoodType.NEUTRAL:
            base_confidence += 0.05
        
        return min(1.0, max(0.1, base_confidence))
    
    def _generate_analysis_reasoning(self, content_type: ContentType, complexity: ComplexityLevel,
                                   mood: MoodType, pacing: str) -> str:
        """Generate human-readable reasoning for the analysis."""
        reasoning_parts = []
        
        # Content type reasoning
        type_reasons = {
            ContentType.MATHEMATICAL: "Contains mathematical terminology and concepts",
            ContentType.ARCHITECTURAL: "Discusses system design and structural elements",
            ContentType.ANALYTICAL: "Focuses on data analysis and performance metrics",
            ContentType.PROCEDURAL: "Describes step-by-step processes or methods",
            ContentType.INTRODUCTORY: "Introduces concepts and provides overview",
            ContentType.CONCLUSION: "Summarizes findings and discusses implications",
            ContentType.GENERAL: "General content without specific domain focus"
        }
        reasoning_parts.append(type_reasons[content_type])
        
        # Complexity reasoning
        complexity_reasons = {
            ComplexityLevel.HIGH: "Uses advanced terminology and complex concepts",
            ComplexityLevel.MEDIUM: "Balances accessibility with technical depth",
            ComplexityLevel.LOW: "Uses simple language and basic concepts"
        }
        reasoning_parts.append(complexity_reasons[complexity])
        
        # Mood reasoning
        mood_reasons = {
            MoodType.POSITIVE: "Emphasizes achievements and positive outcomes",
            MoodType.SERIOUS: "Addresses important challenges and critical issues",
            MoodType.WELCOMING: "Uses inviting language for introduction",
            MoodType.TECHNICAL: "Focuses on technical implementation details",
            MoodType.NEUTRAL: "Maintains objective and balanced tone"
        }
        reasoning_parts.append(mood_reasons[mood])
        
        # Pacing reasoning
        pacing_reasons = {
            "fast": "Suggests quick presentation for efficiency",
            "medium": "Requires balanced pacing for comprehension",
            "slow": "Needs careful pacing for complex material"
        }
        reasoning_parts.append(pacing_reasons[pacing])
        
        return ". ".join(reasoning_parts) + "."


class CinematicRecommendationEngine:
    """Generates cinematic setting recommendations based on content analysis."""
    
    def __init__(self, gemini_client=None):
        self.content_analyzer = ContentAnalyzer()
        self.gemini_client = gemini_client
        
        # Template configurations for different content types
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> Dict[ContentType, Dict[str, Any]]:
        """Initialize cinematic templates for different content types."""
        return {
            ContentType.MATHEMATICAL: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.ZOOM, CameraMovementType.STATIC],
                    "intensity": 30,  # Subtle movements to avoid distraction
                    "reasoning": "Subtle camera movements maintain focus on mathematical content"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.CINEMA,
                    "contrast": 20,
                    "saturation": -10,
                    "temperature": -5,
                    "reasoning": "Cool, high-contrast look enhances mathematical clarity"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": False,
                    "music_scoring": True,
                    "spatial_audio": False,
                    "reverb_intensity": 10,
                    "reasoning": "Minimal audio distractions with subtle musical scoring"
                }
            },
            
            ContentType.ARCHITECTURAL: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.PAN, CameraMovementType.CRANE],
                    "intensity": 60,
                    "reasoning": "Sweeping movements reveal system architecture and relationships"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.KODAK,
                    "contrast": 15,
                    "saturation": 10,
                    "highlights": -10,
                    "reasoning": "Balanced color grading emphasizes structural elements"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "spatial_audio": True,
                    "reverb_intensity": 40,
                    "reasoning": "Spatial audio enhances sense of architectural space"
                }
            },
            
            ContentType.ANALYTICAL: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.STATIC, CameraMovementType.ZOOM],
                    "intensity": 20,
                    "reasoning": "Minimal movement allows focus on data and analysis"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.FUJI,
                    "brightness": 10,
                    "contrast": 10,
                    "saturation": 5,
                    "reasoning": "Clean, bright look enhances data visibility"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": False,
                    "music_scoring": False,
                    "dynamic_range_compression": True,
                    "reasoning": "Clear audio without musical distractions for data focus"
                }
            },
            
            ContentType.PROCEDURAL: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.DOLLY, CameraMovementType.PAN],
                    "intensity": 50,
                    "reasoning": "Guided movements follow procedural flow"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.KODAK,
                    "temperature": 5,
                    "brightness": 5,
                    "reasoning": "Warm, inviting look guides through process steps"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "reverb_intensity": 25,
                    "reasoning": "Supportive audio guides through procedural steps"
                }
            },
            
            ContentType.INTRODUCTORY: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.ZOOM, CameraMovementType.DOLLY],
                    "intensity": 70,
                    "reasoning": "Welcoming movements draw viewer into content"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.KODAK,
                    "temperature": 15,
                    "saturation": 15,
                    "brightness": 10,
                    "reasoning": "Warm, vibrant look creates welcoming atmosphere"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "spatial_audio": False,
                    "reverb_intensity": 35,
                    "reasoning": "Rich audio creates engaging introduction"
                }
            },
            
            ContentType.CONCLUSION: {
                "camera_movements": {
                    "enabled": True,
                    "preferred_types": [CameraMovementType.DOLLY, CameraMovementType.CRANE],
                    "intensity": 60,
                    "reasoning": "Concluding movements provide sense of completion"
                },
                "color_grading": {
                    "enabled": True,
                    "film_emulation": FilmEmulationType.CINEMA,
                    "temperature": 10,
                    "contrast": 15,
                    "saturation": 10,
                    "reasoning": "Cinematic look emphasizes importance of conclusions"
                },
                "sound_design": {
                    "enabled": True,
                    "ambient_audio": True,
                    "music_scoring": True,
                    "reverb_intensity": 40,
                    "reasoning": "Full audio treatment for impactful conclusion"
                }
            }
        }
    
    async def generate_recommendations(self, content: str, 
                                     current_settings: Optional[CinematicSettingsModel] = None,
                                     context: Optional[Dict[str, Any]] = None) -> RecommendationResult:
        """Generate cinematic recommendations for content."""
        
        # Analyze content
        analysis = self.content_analyzer.analyze_content(content, context)
        
        # Get AI-enhanced analysis if available
        if self.gemini_client:
            try:
                ai_analysis = await self.gemini_client.analyze_scene_for_cinematics(content)
                if ai_analysis:
                    analysis = self._merge_ai_analysis(analysis, ai_analysis)
            except Exception as e:
                logger.warning(f"AI analysis failed, using rule-based analysis: {e}")
        
        # Generate recommendations
        recommendations = self._generate_recommendations_from_analysis(analysis, current_settings)
        
        # Apply template and create suggested settings
        template_name, suggested_settings = self._apply_template_and_customize(analysis, recommendations)
        
        # Calculate overall confidence
        overall_confidence = self._calculate_recommendation_confidence(analysis, recommendations)
        
        return RecommendationResult(
            content_analysis=analysis,
            recommendations=recommendations,
            suggested_settings=suggested_settings,
            template_applied=template_name,
            confidence=overall_confidence,
            generated_at=datetime.utcnow().isoformat()
        )
    
    def _merge_ai_analysis(self, rule_analysis: ContentAnalysis, ai_analysis: Dict[str, Any]) -> ContentAnalysis:
        """Merge rule-based analysis with AI analysis."""
        # Use AI analysis to enhance rule-based analysis
        if "focusType" in ai_analysis:
            try:
                ai_content_type = ContentType(ai_analysis["focusType"])
                # Use AI type if confidence is high, otherwise blend
                if ai_analysis.get("confidence", 0) > 0.8:
                    rule_analysis.content_type = ai_content_type
            except ValueError:
                pass  # Invalid AI content type, keep rule-based
        
        if "complexity" in ai_analysis:
            try:
                ai_complexity = ComplexityLevel(ai_analysis["complexity"])
                rule_analysis.complexity = ai_complexity
            except ValueError:
                pass
        
        if "mood" in ai_analysis:
            try:
                ai_mood = MoodType(ai_analysis["mood"])
                rule_analysis.mood = ai_mood
            except ValueError:
                pass
        
        # Enhance confidence with AI input
        rule_analysis.confidence = min(1.0, rule_analysis.confidence + 0.1)
        
        # Update reasoning
        rule_analysis.reasoning += " Enhanced with AI content analysis."
        
        return rule_analysis
    
    def _generate_recommendations_from_analysis(self, analysis: ContentAnalysis,
                                              current_settings: Optional[CinematicSettingsModel]) -> List[CinematicRecommendation]:
        """Generate specific recommendations based on analysis."""
        recommendations = []
        
        # Get template for content type
        template = self.templates.get(analysis.content_type, self.templates[ContentType.GENERAL])
        
        # Camera movement recommendations
        if "camera_movements" in template:
            camera_template = template["camera_movements"]
            recommendations.append(CinematicRecommendation(
                feature="camera_movements",
                setting="enabled",
                value=camera_template["enabled"],
                reasoning=camera_template["reasoning"],
                confidence=0.9,
                priority=3
            ))
            
            if camera_template["enabled"]:
                recommendations.append(CinematicRecommendation(
                    feature="camera_movements",
                    setting="intensity",
                    value=camera_template["intensity"],
                    reasoning=f"Intensity of {camera_template['intensity']} suits {analysis.content_type.value} content",
                    confidence=0.8,
                    priority=2
                ))
        
        # Color grading recommendations
        if "color_grading" in template:
            color_template = template["color_grading"]
            recommendations.append(CinematicRecommendation(
                feature="color_grading",
                setting="film_emulation",
                value=color_template["film_emulation"],
                reasoning=color_template["reasoning"],
                confidence=0.85,
                priority=4
            ))
        
        # Sound design recommendations
        if "sound_design" in template:
            sound_template = template["sound_design"]
            recommendations.append(CinematicRecommendation(
                feature="sound_design",
                setting="enabled",
                value=sound_template["enabled"],
                reasoning=sound_template["reasoning"],
                confidence=0.8,
                priority=3
            ))
        
        # Complexity-based adjustments
        if analysis.complexity == ComplexityLevel.HIGH:
            recommendations.append(CinematicRecommendation(
                feature="camera_movements",
                setting="intensity",
                value=max(20, template.get("camera_movements", {}).get("intensity", 50) - 20),
                reasoning="Reduced camera movement intensity for complex content to maintain focus",
                confidence=0.9,
                priority=5
            ))
        
        # Mood-based adjustments
        if analysis.mood == MoodType.SERIOUS:
            recommendations.append(CinematicRecommendation(
                feature="color_grading",
                setting="temperature",
                value=-10,
                reasoning="Cooler color temperature for serious content tone",
                confidence=0.8,
                priority=3
            ))
        elif analysis.mood == MoodType.POSITIVE:
            recommendations.append(CinematicRecommendation(
                feature="color_grading",
                setting="temperature",
                value=10,
                reasoning="Warmer color temperature for positive content tone",
                confidence=0.8,
                priority=3
            ))
        
        return recommendations
    
    def _apply_template_and_customize(self, analysis: ContentAnalysis, 
                                    recommendations: List[CinematicRecommendation]) -> Tuple[str, CinematicSettingsModel]:
        """Apply template and customize based on recommendations."""
        
        # Start with base template
        template = self.templates.get(analysis.content_type, self.templates[ContentType.GENERAL])
        template_name = f"{analysis.content_type.value}_template"
        
        # Create base settings from template
        from .models import (
            CameraMovementSettings, ColorGradingSettings, 
            SoundDesignSettings, AdvancedCompositingSettings
        )
        
        # Camera movements
        camera_template = template.get("camera_movements", {})
        camera_settings = CameraMovementSettings(
            enabled=camera_template.get("enabled", True),
            intensity=camera_template.get("intensity", 50),
            auto_select=True
        )
        
        # Color grading
        color_template = template.get("color_grading", {})
        color_settings = ColorGradingSettings(
            enabled=color_template.get("enabled", True),
            film_emulation=color_template.get("film_emulation", FilmEmulationType.KODAK),
            temperature=color_template.get("temperature", 0),
            contrast=color_template.get("contrast", 0),
            saturation=color_template.get("saturation", 0),
            brightness=color_template.get("brightness", 0),
            auto_adjust=True
        )
        
        # Sound design
        sound_template = template.get("sound_design", {})
        sound_settings = SoundDesignSettings(
            enabled=sound_template.get("enabled", True),
            ambient_audio=sound_template.get("ambient_audio", True),
            music_scoring=sound_template.get("music_scoring", True),
            spatial_audio=sound_template.get("spatial_audio", False),
            reverb_intensity=sound_template.get("reverb_intensity", 30)
        )
        
        # Advanced compositing (enable based on content complexity)
        compositing_settings = AdvancedCompositingSettings(
            enabled=analysis.complexity != ComplexityLevel.LOW,
            film_grain=analysis.content_type in [ContentType.CONCLUSION, ContentType.INTRODUCTORY],
            dynamic_lighting=True,
            depth_of_field=analysis.complexity == ComplexityLevel.HIGH
        )
        
        # Apply recommendations to customize settings
        for rec in recommendations:
            if rec.feature == "camera_movements":
                if rec.setting == "enabled":
                    camera_settings.enabled = rec.value
                elif rec.setting == "intensity":
                    camera_settings.intensity = rec.value
            elif rec.feature == "color_grading":
                if rec.setting == "film_emulation":
                    color_settings.film_emulation = rec.value
                elif rec.setting == "temperature":
                    color_settings.temperature = rec.value
            elif rec.feature == "sound_design":
                if rec.setting == "enabled":
                    sound_settings.enabled = rec.value
        
        # Create final settings model
        suggested_settings = CinematicSettingsModel(
            camera_movements=camera_settings,
            color_grading=color_settings,
            sound_design=sound_settings,
            advanced_compositing=compositing_settings,
            quality_preset="cinematic_4k",  # Default to high quality
            auto_recommendations=True
        )
        
        return template_name, suggested_settings
    
    def _calculate_recommendation_confidence(self, analysis: ContentAnalysis, 
                                           recommendations: List[CinematicRecommendation]) -> float:
        """Calculate overall confidence in recommendations."""
        # Base confidence from analysis
        base_confidence = analysis.confidence
        
        # Average recommendation confidence
        if recommendations:
            avg_rec_confidence = sum(rec.confidence for rec in recommendations) / len(recommendations)
            base_confidence = (base_confidence + avg_rec_confidence) / 2
        
        # Adjust based on content type certainty
        if analysis.content_type != ContentType.GENERAL:
            base_confidence += 0.1
        
        # Adjust based on number of recommendations
        if len(recommendations) >= 5:
            base_confidence += 0.05
        
        return min(1.0, base_confidence)
    
    async def apply_recommendations(self, recommendations: List[CinematicRecommendation],
                                  current_settings: CinematicSettingsModel) -> CinematicSettingsModel:
        """Apply recommendations to current settings."""
        # Create a copy of current settings
        new_settings = CinematicSettingsModel(
            camera_movements=current_settings.camera_movements,
            color_grading=current_settings.color_grading,
            sound_design=current_settings.sound_design,
            advanced_compositing=current_settings.advanced_compositing,
            quality_preset=current_settings.quality_preset,
            auto_recommendations=current_settings.auto_recommendations
        )
        
        # Apply each recommendation
        for rec in recommendations:
            if rec.feature == "camera_movements":
                if rec.setting == "enabled":
                    new_settings.camera_movements.enabled = rec.value
                elif rec.setting == "intensity":
                    new_settings.camera_movements.intensity = rec.value
            elif rec.feature == "color_grading":
                if rec.setting == "film_emulation":
                    new_settings.color_grading.film_emulation = rec.value
                elif rec.setting == "temperature":
                    new_settings.color_grading.temperature = rec.value
                elif rec.setting == "contrast":
                    new_settings.color_grading.contrast = rec.value
                elif rec.setting == "saturation":
                    new_settings.color_grading.saturation = rec.value
            elif rec.feature == "sound_design":
                if rec.setting == "enabled":
                    new_settings.sound_design.enabled = rec.value
                elif rec.setting == "ambient_audio":
                    new_settings.sound_design.ambient_audio = rec.value
                elif rec.setting == "music_scoring":
                    new_settings.sound_design.music_scoring = rec.value
        
        return new_settings
    
    def get_available_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get available cinematic templates."""
        return {
            content_type.value: {
                "name": f"{content_type.value.title()} Template",
                "description": f"Optimized for {content_type.value} content",
                "features": list(template.keys())
            }
            for content_type, template in self.templates.items()
        }