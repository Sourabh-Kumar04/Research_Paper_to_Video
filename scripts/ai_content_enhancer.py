"""
AI-Powered Content Enhancement System for RASO Platform

This module provides AI-powered content enhancement capabilities including
automatic script improvement, fact-checking, content adaptation, visual
suggestions, and quality assessment.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from utils.ai_model_manager import ai_model_manager, ModelType
from utils.ai_prompt_manager import ai_prompt_manager, PromptType, ContentDifficulty

logger = logging.getLogger(__name__)


class EnhancementType(Enum):
    """Types of content enhancement."""
    SCRIPT_IMPROVEMENT = "script_improvement"
    FACT_CHECKING = "fact_checking"
    AUDIENCE_ADAPTATION = "audience_adaptation"
    VISUAL_SUGGESTIONS = "visual_suggestions"
    QUALITY_ASSESSMENT = "quality_assessment"
    CONTENT_EXPANSION = "content_expansion"
    CLARITY_IMPROVEMENT = "clarity_improvement"
    ENGAGEMENT_OPTIMIZATION = "engagement_optimization"


class AudienceLevel(Enum):
    """Target audience levels for content adaptation."""
    ELEMENTARY = "elementary"
    MIDDLE_SCHOOL = "middle_school"
    HIGH_SCHOOL = "high_school"
    UNDERGRADUATE = "undergraduate"
    GRADUATE = "graduate"
    PROFESSIONAL = "professional"
    GENERAL_PUBLIC = "general_public"


class QualityMetric(Enum):
    """Quality assessment metrics."""
    CLARITY = "clarity"
    ACCURACY = "accuracy"
    ENGAGEMENT = "engagement"
    COMPLETENESS = "completeness"
    COHERENCE = "coherence"
    EDUCATIONAL_VALUE = "educational_value"
    TECHNICAL_DEPTH = "technical_depth"


@dataclass
class EnhancementRequest:
    """Request for content enhancement."""
    content_id: str
    title: str
    content: str
    enhancement_types: List[EnhancementType]
    target_audience: Optional[AudienceLevel] = None
    subject_area: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class QualityScore:
    """Quality assessment score for a specific metric."""
    metric: QualityMetric
    score: float  # 0.0 to 1.0
    explanation: str
    suggestions: List[str]


@dataclass
class ContentEnhancement:
    """Result of content enhancement."""
    original_content: str
    enhanced_content: str
    enhancement_type: EnhancementType
    improvements: List[str]
    confidence_score: float
    metadata: Dict[str, Any]


@dataclass
class QualityAssessment:
    """Comprehensive quality assessment of content."""
    content_id: str
    overall_score: float
    metric_scores: List[QualityScore]
    strengths: List[str]
    weaknesses: List[str]
    recommendations: List[str]
    metadata: Dict[str, Any]


class AIContentEnhancer:
    """AI-powered content enhancement system."""
    
    def __init__(self):
        self.enhancement_prompts = {}
        self.quality_thresholds = self._initialize_quality_thresholds()
        self.audience_adaptations = self._initialize_audience_adaptations()
        self._initialize_enhancement_prompts()
        
    def _initialize_quality_thresholds(self) -> Dict[QualityMetric, float]:
        """Initialize quality score thresholds."""
        return {
            QualityMetric.CLARITY: 0.7,
            QualityMetric.ACCURACY: 0.8,
            QualityMetric.ENGAGEMENT: 0.6,
            QualityMetric.COMPLETENESS: 0.7,
            QualityMetric.COHERENCE: 0.75,
            QualityMetric.EDUCATIONAL_VALUE: 0.7,
            QualityMetric.TECHNICAL_DEPTH: 0.6
        }
    
    def _initialize_audience_adaptations(self) -> Dict[AudienceLevel, Dict[str, Any]]:
        """Initialize audience-specific adaptation parameters."""
        return {
            AudienceLevel.ELEMENTARY: {
                "vocabulary_level": "simple",
                "sentence_length": "short",
                "concepts_per_minute": 1,
                "use_analogies": True,
                "use_examples": True,
                "technical_terms": "minimal"
            },
            AudienceLevel.MIDDLE_SCHOOL: {
                "vocabulary_level": "moderate",
                "sentence_length": "medium",
                "concepts_per_minute": 2,
                "use_analogies": True,
                "use_examples": True,
                "technical_terms": "basic"
            },
            AudienceLevel.HIGH_SCHOOL: {
                "vocabulary_level": "advanced",
                "sentence_length": "medium",
                "concepts_per_minute": 3,
                "use_analogies": True,
                "use_examples": True,
                "technical_terms": "moderate"
            },
            AudienceLevel.UNDERGRADUATE: {
                "vocabulary_level": "academic",
                "sentence_length": "varied",
                "concepts_per_minute": 4,
                "use_analogies": False,
                "use_examples": True,
                "technical_terms": "standard"
            },
            AudienceLevel.GRADUATE: {
                "vocabulary_level": "advanced_academic",
                "sentence_length": "complex",
                "concepts_per_minute": 5,
                "use_analogies": False,
                "use_examples": False,
                "technical_terms": "advanced"
            },
            AudienceLevel.PROFESSIONAL: {
                "vocabulary_level": "professional",
                "sentence_length": "varied",
                "concepts_per_minute": 6,
                "use_analogies": False,
                "use_examples": False,
                "technical_terms": "expert"
            },
            AudienceLevel.GENERAL_PUBLIC: {
                "vocabulary_level": "accessible",
                "sentence_length": "short_to_medium",
                "concepts_per_minute": 2,
                "use_analogies": True,
                "use_examples": True,
                "technical_terms": "explained"
            }
        }
    
    def _initialize_enhancement_prompts(self):
        """Initialize specialized prompts for content enhancement."""
        
        # Script Improvement Prompt
        self.enhancement_prompts[EnhancementType.SCRIPT_IMPROVEMENT] = """You are an expert educational content editor. Improve the following educational script while maintaining its core message and accuracy.

ORIGINAL SCRIPT:
Title: {title}
Content: {content}

IMPROVEMENT GOALS:
- Enhance clarity and flow
- Improve engagement and pacing
- Strengthen educational structure
- Add smooth transitions
- Optimize for {target_audience} audience
- Subject area: {subject_area}

REQUIREMENTS:
- Maintain factual accuracy
- Keep the same approximate length
- Preserve key concepts and learning objectives
- Use appropriate vocabulary for target audience
- Add engaging hooks and transitions
- Include clear examples where helpful

Provide the improved script in this JSON format:
{{
    "enhanced_content": "...",
    "improvements": ["improvement1", "improvement2", "improvement3"],
    "confidence_score": 0.85,
    "key_changes": ["change1", "change2"]
}}

Improve the script now:"""

        # Fact-Checking Prompt
        self.enhancement_prompts[EnhancementType.FACT_CHECKING] = """You are an expert fact-checker and educational content validator. Analyze the following content for factual accuracy and provide corrections.

CONTENT TO VERIFY:
Title: {title}
Content: {content}
Subject Area: {subject_area}

FACT-CHECKING REQUIREMENTS:
- Identify potentially inaccurate statements
- Check for outdated information
- Verify statistical claims and data
- Validate technical concepts and definitions
- Check for logical inconsistencies
- Suggest corrections with reliable sources

Provide your analysis in this JSON format:
{{
    "accuracy_score": 0.85,
    "verified_facts": ["fact1", "fact2"],
    "potential_issues": [
        {{
            "issue": "description of issue",
            "severity": "low|medium|high",
            "suggestion": "correction or verification needed",
            "confidence": 0.8
        }}
    ],
    "corrections": [
        {{
            "original": "original text",
            "corrected": "corrected text",
            "reason": "explanation"
        }}
    ],
    "overall_assessment": "summary of factual accuracy"
}}

Analyze the content now:"""

        # Audience Adaptation Prompt
        self.enhancement_prompts[EnhancementType.AUDIENCE_ADAPTATION] = """You are an expert educational content adapter. Adapt the following content for the specified target audience while maintaining educational value.

ORIGINAL CONTENT:
Title: {title}
Content: {content}

TARGET AUDIENCE: {target_audience}
ADAPTATION PARAMETERS:
- Vocabulary Level: {vocabulary_level}
- Sentence Length: {sentence_length}
- Concepts per Minute: {concepts_per_minute}
- Use Analogies: {use_analogies}
- Use Examples: {use_examples}
- Technical Terms: {technical_terms}

ADAPTATION REQUIREMENTS:
- Adjust vocabulary and complexity appropriately
- Modify sentence structure for readability
- Add or remove examples as needed
- Include analogies if appropriate for audience
- Explain technical terms at appropriate level
- Maintain core learning objectives

Provide the adapted content in this JSON format:
{{
    "adapted_content": "...",
    "adaptations_made": ["adaptation1", "adaptation2"],
    "vocabulary_changes": ["change1", "change2"],
    "structural_changes": ["change1", "change2"],
    "confidence_score": 0.9
}}

Adapt the content now:"""

        # Visual Suggestions Prompt (already exists in ai_prompt_manager, but enhanced here)
        self.enhancement_prompts[EnhancementType.VISUAL_SUGGESTIONS] = """You are an expert visual learning designer. Analyze the content and provide specific, actionable visual enhancement suggestions.

CONTENT TO ANALYZE:
Title: {title}
Content: {content}
Subject: {subject_area}
Target Audience: {target_audience}

VISUAL ANALYSIS REQUIREMENTS:
- Identify concepts that would benefit from visualization
- Suggest specific animation types and timing
- Recommend visual metaphors and analogies
- Propose interactive elements
- Consider cognitive load and visual hierarchy
- Suggest color schemes and visual styles

AVAILABLE VISUAL TOOLS:
- Manim (mathematical animations, equations, proofs)
- Motion Canvas (concept diagrams, flowcharts, processes)
- Charts and Graphs (data visualization, statistics)
- 3D Visualizations (molecular structures, networks, geometric)

Provide detailed suggestions in this JSON format:
{{
    "visual_concepts": [
        {{
            "concept": "specific concept to visualize",
            "visual_type": "manim|motion_canvas|chart|3d",
            "animation_type": "specific animation approach",
            "description": "detailed description of visualization",
            "timing": "when in the content this should appear",
            "importance": "high|medium|low",
            "implementation_notes": "specific technical notes"
        }}
    ],
    "visual_metaphors": ["metaphor1", "metaphor2"],
    "color_scheme": {{
        "primary": "#color",
        "secondary": "#color",
        "accent": "#color",
        "reasoning": "why this scheme works"
    }},
    "layout_recommendations": ["recommendation1", "recommendation2"],
    "interactive_elements": ["element1", "element2"],
    "accessibility_considerations": ["consideration1", "consideration2"]
}}

Generate visual suggestions now:"""

        # Quality Assessment Prompt
        self.enhancement_prompts[EnhancementType.QUALITY_ASSESSMENT] = """You are an expert educational content quality assessor. Evaluate the following content across multiple quality dimensions.

CONTENT TO ASSESS:
Title: {title}
Content: {content}
Subject Area: {subject_area}
Target Audience: {target_audience}

QUALITY DIMENSIONS TO EVALUATE:
1. Clarity - How clear and understandable is the content?
2. Accuracy - How factually correct and up-to-date is the information?
3. Engagement - How engaging and interesting is the content?
4. Completeness - How complete and comprehensive is the coverage?
5. Coherence - How well-structured and logically organized is the content?
6. Educational Value - How effective is it for learning?
7. Technical Depth - How appropriate is the technical level?

Provide your assessment in this JSON format:
{{
    "overall_score": 0.85,
    "metric_scores": [
        {{
            "metric": "clarity",
            "score": 0.8,
            "explanation": "detailed explanation of score",
            "suggestions": ["suggestion1", "suggestion2"]
        }}
    ],
    "strengths": ["strength1", "strength2", "strength3"],
    "weaknesses": ["weakness1", "weakness2"],
    "recommendations": [
        {{
            "priority": "high|medium|low",
            "recommendation": "specific recommendation",
            "expected_impact": "description of expected improvement"
        }}
    ],
    "readability_score": 0.75,
    "engagement_indicators": ["indicator1", "indicator2"]
}}

Assess the content quality now:"""

    async def enhance_content(
        self,
        request: EnhancementRequest
    ) -> List[ContentEnhancement]:
        """Enhance content using AI-powered analysis and improvement."""
        try:
            enhancements = []
            
            for enhancement_type in request.enhancement_types:
                logger.info(f"Applying {enhancement_type.value} enhancement to content {request.content_id}")
                
                enhancement = await self._apply_enhancement(
                    request, enhancement_type
                )
                
                if enhancement:
                    enhancements.append(enhancement)
                    logger.info(f"✅ {enhancement_type.value} enhancement completed with confidence {enhancement.confidence_score:.2f}")
                else:
                    logger.warning(f"❌ {enhancement_type.value} enhancement failed")
            
            return enhancements
            
        except Exception as e:
            logger.error(f"Error enhancing content: {e}")
            return []
    
    async def _apply_enhancement(
        self,
        request: EnhancementRequest,
        enhancement_type: EnhancementType
    ) -> Optional[ContentEnhancement]:
        """Apply a specific type of enhancement."""
        try:
            # Get appropriate AI model for the enhancement task
            if enhancement_type in [EnhancementType.SCRIPT_IMPROVEMENT, EnhancementType.CONTENT_EXPANSION]:
                model = ai_model_manager.get_model_for_task("educational_content")
            elif enhancement_type == EnhancementType.FACT_CHECKING:
                model = ai_model_manager.get_model_for_task("content_analysis")
            else:
                model = ai_model_manager.get_model_for_task("content_analysis")
            
            if not model:
                logger.error(f"No suitable model available for {enhancement_type.value}")
                return None
            
            # Prepare prompt variables
            prompt_variables = self._prepare_prompt_variables(request, enhancement_type)
            
            # Get enhancement prompt
            prompt_template = self.enhancement_prompts.get(enhancement_type)
            if not prompt_template:
                logger.error(f"No prompt template for {enhancement_type.value}")
                return None
            
            # Generate prompt
            prompt = prompt_template.format(**prompt_variables)
            
            # Generate enhancement using AI
            response = await ai_model_manager.generate_with_model(
                model, prompt, temperature=0.3, max_tokens=3000
            )
            
            if not response:
                return None
            
            # Parse response
            enhancement_result = self._parse_enhancement_response(
                response, request, enhancement_type
            )
            
            return enhancement_result
            
        except Exception as e:
            logger.error(f"Error applying {enhancement_type.value} enhancement: {e}")
            return None
    
    def _prepare_prompt_variables(
        self,
        request: EnhancementRequest,
        enhancement_type: EnhancementType
    ) -> Dict[str, Any]:
        """Prepare variables for enhancement prompts."""
        base_variables = {
            "title": request.title,
            "content": request.content[:2000],  # Limit content length
            "subject_area": request.subject_area or "general",
            "target_audience": request.target_audience.value if request.target_audience else "general_public"
        }
        
        # Add audience-specific parameters for adaptation
        if enhancement_type == EnhancementType.AUDIENCE_ADAPTATION and request.target_audience:
            audience_params = self.audience_adaptations.get(request.target_audience, {})
            base_variables.update(audience_params)
        
        return base_variables
    
    def _parse_enhancement_response(
        self,
        response: str,
        request: EnhancementRequest,
        enhancement_type: EnhancementType
    ) -> Optional[ContentEnhancement]:
        """Parse AI response for enhancement results."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.warning(f"No JSON found in {enhancement_type.value} response")
                return None
            
            result_data = json.loads(json_match.group())
            
            # Extract enhancement data based on type
            if enhancement_type == EnhancementType.SCRIPT_IMPROVEMENT:
                enhanced_content = result_data.get("enhanced_content", request.content)
                improvements = result_data.get("improvements", [])
                confidence = result_data.get("confidence_score", 0.5)
                
            elif enhancement_type == EnhancementType.AUDIENCE_ADAPTATION:
                enhanced_content = result_data.get("adapted_content", request.content)
                improvements = result_data.get("adaptations_made", [])
                confidence = result_data.get("confidence_score", 0.5)
                
            elif enhancement_type == EnhancementType.FACT_CHECKING:
                # For fact-checking, enhanced content includes corrections
                corrections = result_data.get("corrections", [])
                enhanced_content = self._apply_corrections(request.content, corrections)
                improvements = [f"Corrected: {c['reason']}" for c in corrections]
                confidence = result_data.get("accuracy_score", 0.5)
                
            else:
                # Generic enhancement parsing
                enhanced_content = result_data.get("enhanced_content", request.content)
                improvements = result_data.get("improvements", [])
                confidence = result_data.get("confidence_score", 0.5)
            
            return ContentEnhancement(
                original_content=request.content,
                enhanced_content=enhanced_content,
                enhancement_type=enhancement_type,
                improvements=improvements,
                confidence_score=confidence,
                metadata={
                    "ai_response": result_data,
                    "model_used": "ai_enhanced",
                    "enhancement_timestamp": asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing {enhancement_type.value} response: {e}")
            return None
    
    def _apply_corrections(self, content: str, corrections: List[Dict[str, str]]) -> str:
        """Apply fact-checking corrections to content."""
        enhanced_content = content
        
        for correction in corrections:
            original = correction.get("original", "")
            corrected = correction.get("corrected", "")
            
            if original and corrected:
                enhanced_content = enhanced_content.replace(original, corrected)
        
        return enhanced_content
    
    async def assess_quality(
        self,
        content_id: str,
        title: str,
        content: str,
        subject_area: Optional[str] = None,
        target_audience: Optional[AudienceLevel] = None
    ) -> QualityAssessment:
        """Perform comprehensive quality assessment of content."""
        try:
            # Get model for content analysis
            model = ai_model_manager.get_model_for_task("content_analysis")
            if not model:
                return self._create_fallback_assessment(content_id, title, content)
            
            # Prepare prompt variables
            prompt_variables = {
                "title": title,
                "content": content[:2000],
                "subject_area": subject_area or "general",
                "target_audience": target_audience.value if target_audience else "general_public"
            }
            
            # Generate quality assessment prompt
            prompt = self.enhancement_prompts[EnhancementType.QUALITY_ASSESSMENT].format(**prompt_variables)
            
            # Generate assessment using AI
            response = await ai_model_manager.generate_with_model(
                model, prompt, temperature=0.2, max_tokens=2048
            )
            
            if not response:
                return self._create_fallback_assessment(content_id, title, content)
            
            # Parse assessment response
            assessment = self._parse_quality_assessment(response, content_id)
            
            if assessment:
                logger.info(f"Quality assessment completed for {content_id}: {assessment.overall_score:.2f}")
                return assessment
            else:
                return self._create_fallback_assessment(content_id, title, content)
                
        except Exception as e:
            logger.error(f"Error assessing content quality: {e}")
            return self._create_fallback_assessment(content_id, title, content)
    
    def _parse_quality_assessment(
        self,
        response: str,
        content_id: str
    ) -> Optional[QualityAssessment]:
        """Parse AI response for quality assessment."""
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                return None
            
            assessment_data = json.loads(json_match.group())
            
            # Parse metric scores
            metric_scores = []
            for metric_data in assessment_data.get("metric_scores", []):
                try:
                    metric = QualityMetric(metric_data["metric"])
                    score = QualityScore(
                        metric=metric,
                        score=metric_data["score"],
                        explanation=metric_data["explanation"],
                        suggestions=metric_data.get("suggestions", [])
                    )
                    metric_scores.append(score)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error parsing metric score: {e}")
                    continue
            
            return QualityAssessment(
                content_id=content_id,
                overall_score=assessment_data.get("overall_score", 0.5),
                metric_scores=metric_scores,
                strengths=assessment_data.get("strengths", []),
                weaknesses=assessment_data.get("weaknesses", []),
                recommendations=assessment_data.get("recommendations", []),
                metadata={
                    "ai_assessment": assessment_data,
                    "assessment_timestamp": asyncio.get_event_loop().time()
                }
            )
            
        except Exception as e:
            logger.error(f"Error parsing quality assessment: {e}")
            return None
    
    def _create_fallback_assessment(
        self,
        content_id: str,
        title: str,
        content: str
    ) -> QualityAssessment:
        """Create fallback quality assessment when AI analysis fails."""
        # Simple rule-based assessment
        content_length = len(content)
        word_count = len(content.split())
        
        # Basic scoring based on content characteristics
        clarity_score = min(0.8, word_count / 500)  # Assume longer content is clearer
        completeness_score = min(0.9, content_length / 1000)  # Longer content is more complete
        
        fallback_scores = [
            QualityScore(
                metric=QualityMetric.CLARITY,
                score=clarity_score,
                explanation="Basic assessment based on content length and structure",
                suggestions=["Consider adding more detailed explanations"]
            ),
            QualityScore(
                metric=QualityMetric.COMPLETENESS,
                score=completeness_score,
                explanation="Assessment based on content length",
                suggestions=["Consider expanding key concepts"]
            )
        ]
        
        overall_score = sum(score.score for score in fallback_scores) / len(fallback_scores)
        
        return QualityAssessment(
            content_id=content_id,
            overall_score=overall_score,
            metric_scores=fallback_scores,
            strengths=["Content provided"],
            weaknesses=["Limited AI analysis available"],
            recommendations=["Enable AI models for detailed assessment"],
            metadata={"assessment_method": "fallback", "ai_available": False}
        )
    
    async def suggest_visual_enhancements(
        self,
        title: str,
        content: str,
        subject_area: Optional[str] = None,
        target_audience: Optional[AudienceLevel] = None
    ) -> Dict[str, Any]:
        """Generate visual enhancement suggestions for content."""
        try:
            # Use existing visual suggestions prompt from ai_prompt_manager
            prompt_variables = {
                "title": title,
                "content": content[:1500],  # Limit content length
                "subject": subject_area or "general",
                "audience_level": target_audience.value if target_audience else "general_public",
                "duration": "5"  # Default duration
            }
            
            # Generate visual suggestions using specialized prompt
            visual_prompt = ai_prompt_manager.generate_prompt(
                "visual_suggestions",
                prompt_variables,
                include_examples=False
            )
            
            if not visual_prompt:
                return {"error": "Visual suggestions prompt not available"}
            
            # Get model for visual analysis
            model = ai_model_manager.get_model_for_task("content_analysis")
            if not model:
                return {"error": "No AI model available for visual analysis"}
            
            # Generate suggestions
            response = await ai_model_manager.generate_with_model(
                model, visual_prompt, temperature=0.4, max_tokens=2048
            )
            
            if not response:
                return {"error": "Failed to generate visual suggestions"}
            
            # Parse response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                suggestions = json.loads(json_match.group())
                logger.info(f"Generated {len(suggestions.get('visual_concepts', []))} visual suggestions")
                return suggestions
            else:
                return {"error": "Failed to parse visual suggestions"}
                
        except Exception as e:
            logger.error(f"Error generating visual suggestions: {e}")
            return {"error": str(e)}
    
    async def optimize_for_engagement(
        self,
        content: str,
        target_audience: AudienceLevel,
        subject_area: str
    ) -> Dict[str, Any]:
        """Optimize content for maximum engagement."""
        try:
            engagement_prompt = """You are an expert in educational engagement optimization. Analyze and optimize the following content for maximum learner engagement.

CONTENT TO OPTIMIZE:
{content}

TARGET AUDIENCE: {target_audience}
SUBJECT AREA: {subject_area}

ENGAGEMENT OPTIMIZATION GOALS:
- Add compelling hooks and attention-grabbers
- Improve pacing and rhythm
- Include interactive elements and questions
- Add storytelling elements where appropriate
- Optimize for emotional connection
- Include variety in presentation style

Provide optimization suggestions in JSON format:
{{
    "optimized_content": "...",
    "engagement_techniques": ["technique1", "technique2"],
    "interactive_elements": ["element1", "element2"],
    "pacing_improvements": ["improvement1", "improvement2"],
    "emotional_hooks": ["hook1", "hook2"],
    "engagement_score": 0.85
}}

Optimize for engagement now:"""
            
            # Format prompt
            formatted_prompt = engagement_prompt.format(
                content=content[:1500],
                target_audience=target_audience.value,
                subject_area=subject_area
            )
            
            # Get model and generate optimization
            model = ai_model_manager.get_model_for_task("educational_content")
            if not model:
                return {"error": "No AI model available"}
            
            response = await ai_model_manager.generate_with_model(
                model, formatted_prompt, temperature=0.4, max_tokens=2048
            )
            
            if response:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            
            return {"error": "Failed to generate engagement optimization"}
            
        except Exception as e:
            logger.error(f"Error optimizing for engagement: {e}")
            return {"error": str(e)}
    
    def get_enhancement_recommendations(
        self,
        quality_assessment: QualityAssessment
    ) -> List[EnhancementType]:
        """Get recommended enhancement types based on quality assessment."""
        recommendations = []
        
        # Check quality scores against thresholds
        for metric_score in quality_assessment.metric_scores:
            threshold = self.quality_thresholds.get(metric_score.metric, 0.7)
            
            if metric_score.score < threshold:
                if metric_score.metric == QualityMetric.CLARITY:
                    recommendations.append(EnhancementType.CLARITY_IMPROVEMENT)
                elif metric_score.metric == QualityMetric.ENGAGEMENT:
                    recommendations.append(EnhancementType.ENGAGEMENT_OPTIMIZATION)
                elif metric_score.metric == QualityMetric.ACCURACY:
                    recommendations.append(EnhancementType.FACT_CHECKING)
                elif metric_score.metric == QualityMetric.COMPLETENESS:
                    recommendations.append(EnhancementType.CONTENT_EXPANSION)
        
        # Always recommend script improvement if overall score is low
        if quality_assessment.overall_score < 0.7:
            recommendations.append(EnhancementType.SCRIPT_IMPROVEMENT)
        
        # Always recommend visual suggestions for educational content
        recommendations.append(EnhancementType.VISUAL_SUGGESTIONS)
        
        return list(set(recommendations))  # Remove duplicates


# Global instance
ai_content_enhancer = AIContentEnhancer()