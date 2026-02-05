"""
Multi-Scene Consistency and Template System

This module provides visual consistency analysis across multiple scenes and an advanced
template system with customization capabilities for cinematic video production.
"""

import asyncio
import json
import logging
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import hashlib
from datetime import datetime

from ..llm.gemini_client import GeminiClient
from .models import CinematicSettingsModel, VisualDescriptionModel


logger = logging.getLogger(__name__)


class ContentType(Enum):
    """Content classification types for template selection."""
    MATHEMATICAL = "mathematical"
    ARCHITECTURAL = "architectural"
    ANALYTICAL = "analytical"
    PROCEDURAL = "procedural"
    INTRODUCTORY = "introductory"
    CONCLUSION = "conclusion"
    GENERAL = "general"


class ConsistencyLevel(Enum):
    """Visual consistency levels."""
    STRICT = "strict"  # Identical visual elements
    MODERATE = "moderate"  # Similar themes with variation
    FLEXIBLE = "flexible"  # Thematic consistency only


@dataclass
class SceneConsistencyAnalysis:
    """Analysis of visual consistency between scenes."""
    scene_ids: List[str]
    consistency_score: float  # 0-1
    consistency_level: ConsistencyLevel
    visual_themes: List[str]
    inconsistencies: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float


@dataclass
class TemplateDefinition:
    """Advanced template definition with customization capabilities."""
    id: str
    name: str
    description: str
    content_type: ContentType
    visual_elements: Dict[str, Any]
    cinematic_settings: Dict[str, Any]
    customization_options: Dict[str, Any]
    is_editable: bool = True
    created_at: str = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow().isoformat()


@dataclass
class AppliedTemplate:
    """Template applied to specific content with customizations."""
    template_id: str
    scene_id: str
    customizations: Dict[str, Any]
    applied_settings: Dict[str, Any]
    applied_at: str
    is_modified: bool = False


class MultiSceneConsistencyAnalyzer:
    """Analyzes and maintains visual consistency across multiple scenes."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client
        self.consistency_cache = {}
        
    async def analyze_scene_consistency(
        self,
        scenes: List[VisualDescriptionModel],
        consistency_level: ConsistencyLevel = ConsistencyLevel.MODERATE
    ) -> SceneConsistencyAnalysis:
        """
        Analyze visual consistency across multiple scenes.
        
        Args:
            scenes: List of scene descriptions to analyze
            consistency_level: Desired level of consistency
            
        Returns:
            SceneConsistencyAnalysis with consistency metrics and recommendations
        """
        if len(scenes) < 2:
            return SceneConsistencyAnalysis(
                scene_ids=[s.scene_id for s in scenes],
                consistency_score=1.0,
                consistency_level=consistency_level,
                visual_themes=[],
                inconsistencies=[],
                recommendations=[],
                confidence=1.0
            )
        
        # Generate cache key for consistency analysis
        cache_key = self._generate_consistency_cache_key(scenes, consistency_level)
        if cache_key in self.consistency_cache:
            logger.info("Using cached consistency analysis")
            return self.consistency_cache[cache_key]
        
        try:
            # Use Gemini for advanced consistency analysis if available
            if self.gemini_client:
                analysis = await self._analyze_with_gemini(scenes, consistency_level)
            else:
                analysis = await self._analyze_with_templates(scenes, consistency_level)
            
            # Cache the analysis
            self.consistency_cache[cache_key] = analysis
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing scene consistency: {e}")
            # Return fallback analysis
            return self._create_fallback_analysis(scenes, consistency_level)
    
    async def _analyze_with_gemini(
        self,
        scenes: List[VisualDescriptionModel],
        consistency_level: ConsistencyLevel
    ) -> SceneConsistencyAnalysis:
        """Analyze consistency using Gemini AI."""
        
        # Prepare scene descriptions for analysis
        scene_descriptions = []
        for scene in scenes:
            scene_descriptions.append({
                'id': scene.scene_id,
                'content': scene.content,
                'description': scene.description,
                'settings': scene.cinematic_settings
            })
        
        # Create consistency analysis prompt
        prompt = self._create_consistency_prompt(scene_descriptions, consistency_level)
        
        try:
            response = await self.gemini_client.generate_content(prompt)
            analysis_data = self._parse_gemini_consistency_response(response)
            
            return SceneConsistencyAnalysis(
                scene_ids=[s.scene_id for s in scenes],
                consistency_score=analysis_data.get('consistency_score', 0.7),
                consistency_level=consistency_level,
                visual_themes=analysis_data.get('visual_themes', []),
                inconsistencies=analysis_data.get('inconsistencies', []),
                recommendations=analysis_data.get('recommendations', []),
                confidence=analysis_data.get('confidence', 0.8)
            )
            
        except Exception as e:
            logger.error(f"Gemini consistency analysis failed: {e}")
            return await self._analyze_with_templates(scenes, consistency_level)
    
    async def _analyze_with_templates(
        self,
        scenes: List[VisualDescriptionModel],
        consistency_level: ConsistencyLevel
    ) -> SceneConsistencyAnalysis:
        """Analyze consistency using template-based approach."""
        
        visual_themes = []
        inconsistencies = []
        recommendations = []
        
        # Extract visual elements from each scene
        scene_elements = []
        for scene in scenes:
            elements = self._extract_visual_elements(scene.description)
            scene_elements.append({
                'scene_id': scene.scene_id,
                'elements': elements
            })
        
        # Find common themes
        all_elements = []
        for scene_elem in scene_elements:
            all_elements.extend(scene_elem['elements'])
        
        # Count element frequency
        element_counts = {}
        for element in all_elements:
            element_counts[element] = element_counts.get(element, 0) + 1
        
        # Identify themes (elements appearing in multiple scenes)
        threshold = max(2, len(scenes) // 2)
        visual_themes = [
            element for element, count in element_counts.items()
            if count >= threshold
        ]
        
        # Identify inconsistencies
        for i, scene_elem in enumerate(scene_elements):
            missing_themes = [
                theme for theme in visual_themes
                if theme not in scene_elem['elements']
            ]
            
            if missing_themes:
                inconsistencies.append({
                    'scene_id': scene_elem['scene_id'],
                    'type': 'missing_themes',
                    'missing_elements': missing_themes,
                    'severity': 'medium' if len(missing_themes) > len(visual_themes) // 2 else 'low'
                })
        
        # Generate recommendations
        if inconsistencies:
            recommendations.append(
                "Consider adding consistent visual themes across all scenes"
            )
            recommendations.append(
                "Ensure lighting and color palette remain consistent"
            )
        
        # Calculate consistency score
        total_possible_consistency = len(scenes) * len(visual_themes)
        actual_consistency = sum(
            len([t for t in visual_themes if t in scene_elem['elements']])
            for scene_elem in scene_elements
        )
        
        consistency_score = (
            actual_consistency / total_possible_consistency
            if total_possible_consistency > 0 else 1.0
        )
        
        return SceneConsistencyAnalysis(
            scene_ids=[s.scene_id for s in scenes],
            consistency_score=consistency_score,
            consistency_level=consistency_level,
            visual_themes=visual_themes,
            inconsistencies=inconsistencies,
            recommendations=recommendations,
            confidence=0.7
        )
    
    def _extract_visual_elements(self, description: str) -> List[str]:
        """Extract visual elements from a scene description."""
        # Simple keyword-based extraction
        visual_keywords = [
            'lighting', 'camera', 'angle', 'color', 'composition',
            'movement', 'focus', 'depth', 'contrast', 'brightness',
            'shadow', 'highlight', 'warm', 'cool', 'dynamic', 'static'
        ]
        
        elements = []
        description_lower = description.lower()
        
        for keyword in visual_keywords:
            if keyword in description_lower:
                elements.append(keyword)
        
        return elements
    
    def _create_consistency_prompt(
        self,
        scene_descriptions: List[Dict[str, Any]],
        consistency_level: ConsistencyLevel
    ) -> str:
        """Create prompt for Gemini consistency analysis."""
        
        scenes_text = "\n\n".join([
            f"Scene {i+1} (ID: {scene['id']}):\n"
            f"Content: {scene['content']}\n"
            f"Visual Description: {scene['description']}"
            for i, scene in enumerate(scene_descriptions)
        ])
        
        return f"""
Analyze the visual consistency across these cinematic scenes for a {consistency_level.value} consistency level:

{scenes_text}

Please provide a JSON response with the following structure:
{{
    "consistency_score": <float 0-1>,
    "visual_themes": [<list of common visual elements>],
    "inconsistencies": [
        {{
            "scene_id": "<scene_id>",
            "type": "<inconsistency_type>",
            "description": "<description>",
            "severity": "<low|medium|high>"
        }}
    ],
    "recommendations": [<list of improvement suggestions>],
    "confidence": <float 0-1>
}}

Focus on:
- Visual continuity (lighting, color palette, camera style)
- Narrative flow between scenes
- Cinematic coherence
- Technical consistency
"""
    
    def _parse_gemini_consistency_response(self, response: str) -> Dict[str, Any]:
        """Parse Gemini response for consistency analysis."""
        try:
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx >= 0 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                logger.warning("No valid JSON found in Gemini response")
                return {}
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini consistency response: {e}")
            return {}
    
    def _generate_consistency_cache_key(
        self,
        scenes: List[VisualDescriptionModel],
        consistency_level: ConsistencyLevel
    ) -> str:
        """Generate cache key for consistency analysis."""
        scene_data = []
        for scene in scenes:
            scene_data.append({
                'id': scene.scene_id,
                'description': scene.description,
                'settings': scene.cinematic_settings
            })
        
        cache_input = {
            'scenes': scene_data,
            'consistency_level': consistency_level.value
        }
        
        cache_str = json.dumps(cache_input, sort_keys=True)
        return hashlib.md5(cache_str.encode()).hexdigest()
    
    def _create_fallback_analysis(
        self,
        scenes: List[VisualDescriptionModel],
        consistency_level: ConsistencyLevel
    ) -> SceneConsistencyAnalysis:
        """Create fallback analysis when other methods fail."""
        return SceneConsistencyAnalysis(
            scene_ids=[s.scene_id for s in scenes],
            consistency_score=0.5,
            consistency_level=consistency_level,
            visual_themes=['consistent_lighting', 'professional_composition'],
            inconsistencies=[],
            recommendations=[
                'Review visual descriptions for consistency',
                'Ensure similar lighting across scenes'
            ],
            confidence=0.3
        )


class AdvancedTemplateSystem:
    """Advanced template system with customization capabilities."""
    
    def __init__(self, gemini_client: Optional[GeminiClient] = None):
        self.gemini_client = gemini_client
        self.templates = {}
        self.applied_templates = {}
        self._initialize_default_templates()
    
    def _initialize_default_templates(self):
        """Initialize default templates for different content types."""
        
        # Mathematical content template
        self.templates['mathematical'] = TemplateDefinition(
            id='mathematical',
            name='Mathematical Content',
            description='Optimized for mathematical and analytical content',
            content_type=ContentType.MATHEMATICAL,
            visual_elements={
                'camera_movement': 'smooth_zoom',
                'lighting': 'bright_analytical',
                'color_palette': 'high_contrast',
                'composition': 'centered_focus',
                'transitions': 'clean_cuts'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['zoom', 'pan'],
                    'intensity': 30
                },
                'color_grading': {
                    'enabled': True,
                    'contrast': 20,
                    'saturation': -10,
                    'brightness': 10
                }
            },
            customization_options={
                'intensity_range': (10, 50),
                'color_temperature_range': (-20, 20),
                'movement_speed': ['slow', 'medium', 'fast']
            }
        )
        
        # Architectural content template
        self.templates['architectural'] = TemplateDefinition(
            id='architectural',
            name='Architectural Content',
            description='Emphasizes structure and spatial relationships',
            content_type=ContentType.ARCHITECTURAL,
            visual_elements={
                'camera_movement': 'sweeping_pan',
                'lighting': 'dramatic_directional',
                'color_palette': 'warm_professional',
                'composition': 'rule_of_thirds',
                'transitions': 'smooth_dissolve'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['pan', 'dolly', 'crane'],
                    'intensity': 60
                },
                'color_grading': {
                    'enabled': True,
                    'temperature': 10,
                    'contrast': 15,
                    'saturation': 5
                }
            },
            customization_options={
                'movement_amplitude': (30, 80),
                'lighting_intensity': (40, 90),
                'color_warmth': (-10, 30)
            }
        )
        
        # Add more default templates...
        self._add_remaining_default_templates()
    
    def _add_remaining_default_templates(self):
        """Add remaining default templates."""
        
        # Analytical content template
        self.templates['analytical'] = TemplateDefinition(
            id='analytical',
            name='Analytical Content',
            description='For data analysis and research presentations',
            content_type=ContentType.ANALYTICAL,
            visual_elements={
                'camera_movement': 'steady_focus',
                'lighting': 'even_professional',
                'color_palette': 'neutral_analytical',
                'composition': 'grid_based',
                'transitions': 'data_wipe'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['static', 'zoom'],
                    'intensity': 25
                },
                'color_grading': {
                    'enabled': True,
                    'contrast': 25,
                    'saturation': -5,
                    'brightness': 5
                }
            },
            customization_options={
                'data_emphasis': ['charts', 'graphs', 'tables'],
                'transition_speed': ['slow', 'medium'],
                'focus_style': ['sharp', 'soft']
            }
        )
        
        # Procedural content template
        self.templates['procedural'] = TemplateDefinition(
            id='procedural',
            name='Procedural Content',
            description='Step-by-step instructional content',
            content_type=ContentType.PROCEDURAL,
            visual_elements={
                'camera_movement': 'step_by_step_zoom',
                'lighting': 'clear_instructional',
                'color_palette': 'high_visibility',
                'composition': 'sequential_focus',
                'transitions': 'step_progression'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['zoom', 'pan'],
                    'intensity': 40
                },
                'color_grading': {
                    'enabled': True,
                    'contrast': 30,
                    'brightness': 15,
                    'saturation': 10
                }
            },
            customization_options={
                'step_emphasis': ['highlight', 'zoom', 'pause'],
                'progression_speed': ['slow', 'medium', 'fast'],
                'visual_cues': ['arrows', 'highlights', 'callouts']
            }
        )
        
        # Introductory content template
        self.templates['introductory'] = TemplateDefinition(
            id='introductory',
            name='Introductory Content',
            description='Welcoming and engaging opening content',
            content_type=ContentType.INTRODUCTORY,
            visual_elements={
                'camera_movement': 'welcoming_approach',
                'lighting': 'warm_inviting',
                'color_palette': 'engaging_vibrant',
                'composition': 'centered_welcome',
                'transitions': 'smooth_fade_in'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['dolly', 'zoom'],
                    'intensity': 50
                },
                'color_grading': {
                    'enabled': True,
                    'temperature': 15,
                    'contrast': 10,
                    'saturation': 15,
                    'brightness': 10
                }
            },
            customization_options={
                'energy_level': ['calm', 'moderate', 'high'],
                'warmth_factor': (0, 30),
                'engagement_style': ['professional', 'friendly', 'dynamic']
            }
        )
        
        # Conclusion content template
        self.templates['conclusion'] = TemplateDefinition(
            id='conclusion',
            name='Conclusion Content',
            description='Provides closure and inspiration',
            content_type=ContentType.CONCLUSION,
            visual_elements={
                'camera_movement': 'closing_pullback',
                'lighting': 'inspirational_glow',
                'color_palette': 'satisfying_resolution',
                'composition': 'final_perspective',
                'transitions': 'fade_to_conclusion'
            },
            cinematic_settings={
                'camera_movements': {
                    'enabled': True,
                    'allowed_types': ['crane', 'dolly'],
                    'intensity': 45
                },
                'color_grading': {
                    'enabled': True,
                    'temperature': 5,
                    'contrast': 15,
                    'saturation': 5,
                    'brightness': 8
                }
            },
            customization_options={
                'closure_style': ['gentle', 'impactful', 'inspiring'],
                'final_mood': ['satisfied', 'motivated', 'contemplative'],
                'visual_resolution': ['wide', 'close', 'medium']
            }
        )
    
    async def classify_content_type(
        self,
        content: str,
        context: Optional[str] = None
    ) -> ContentType:
        """
        Classify ambiguous content to determine appropriate template.
        
        Args:
            content: The content to classify
            context: Additional context for classification
            
        Returns:
            ContentType enum value
        """
        if self.gemini_client:
            return await self._classify_with_gemini(content, context)
        else:
            return self._classify_with_keywords(content)
    
    async def _classify_with_gemini(
        self,
        content: str,
        context: Optional[str] = None
    ) -> ContentType:
        """Classify content using Gemini AI."""
        
        context_text = f"\nContext: {context}" if context else ""
        
        prompt = f"""
Classify the following content into one of these categories:
- mathematical: Mathematical formulas, equations, calculations, proofs
- architectural: System design, structure, frameworks, diagrams
- analytical: Data analysis, research findings, comparisons, evaluations
- procedural: Step-by-step instructions, tutorials, how-to content
- introductory: Opening statements, welcomes, overviews, introductions
- conclusion: Closing statements, summaries, final thoughts, wrap-ups
- general: Content that doesn't fit other categories

Content: {content}{context_text}

Respond with only the category name (lowercase).
"""
        
        try:
            response = await self.gemini_client.generate_content(prompt)
            classification = response.strip().lower()
            
            # Map response to ContentType enum
            type_mapping = {
                'mathematical': ContentType.MATHEMATICAL,
                'architectural': ContentType.ARCHITECTURAL,
                'analytical': ContentType.ANALYTICAL,
                'procedural': ContentType.PROCEDURAL,
                'introductory': ContentType.INTRODUCTORY,
                'conclusion': ContentType.CONCLUSION,
                'general': ContentType.GENERAL
            }
            
            return type_mapping.get(classification, ContentType.GENERAL)
            
        except Exception as e:
            logger.error(f"Gemini content classification failed: {e}")
            return self._classify_with_keywords(content)
    
    def _classify_with_keywords(self, content: str) -> ContentType:
        """Classify content using keyword matching."""
        content_lower = content.lower()
        
        # Define keyword patterns for each content type
        patterns = {
            ContentType.MATHEMATICAL: [
                'equation', 'formula', 'calculate', 'proof', 'theorem',
                'derivative', 'integral', 'matrix', 'algorithm', 'function'
            ],
            ContentType.ARCHITECTURAL: [
                'system', 'architecture', 'design', 'structure', 'framework',
                'component', 'module', 'interface', 'pattern', 'diagram'
            ],
            ContentType.ANALYTICAL: [
                'analysis', 'data', 'results', 'findings', 'comparison',
                'evaluation', 'research', 'study', 'statistics', 'metrics'
            ],
            ContentType.PROCEDURAL: [
                'step', 'procedure', 'process', 'method', 'tutorial',
                'instruction', 'guide', 'how to', 'first', 'next', 'then'
            ],
            ContentType.INTRODUCTORY: [
                'introduction', 'welcome', 'overview', 'begin', 'start',
                'hello', 'today', 'we will', 'this presentation', 'agenda'
            ],
            ContentType.CONCLUSION: [
                'conclusion', 'summary', 'finally', 'in summary', 'to conclude',
                'wrap up', 'end', 'thank you', 'questions', 'contact'
            ]
        }
        
        # Count matches for each content type
        type_scores = {}
        for content_type, keywords in patterns.items():
            score = sum(1 for keyword in keywords if keyword in content_lower)
            type_scores[content_type] = score
        
        # Return type with highest score, or GENERAL if no clear winner
        if type_scores:
            max_score = max(type_scores.values())
            if max_score > 0:
                return max(type_scores, key=type_scores.get)
        
        return ContentType.GENERAL
    
    def get_template(self, template_id: str) -> Optional[TemplateDefinition]:
        """Get template by ID."""
        return self.templates.get(template_id)
    
    def get_template_by_content_type(self, content_type: ContentType) -> Optional[TemplateDefinition]:
        """Get template by content type."""
        for template in self.templates.values():
            if template.content_type == content_type:
                return template
        return None
    
    def apply_template(
        self,
        template_id: str,
        scene_id: str,
        customizations: Optional[Dict[str, Any]] = None
    ) -> AppliedTemplate:
        """
        Apply template to a scene with optional customizations.
        
        Args:
            template_id: ID of template to apply
            scene_id: ID of scene to apply template to
            customizations: Optional customization parameters
            
        Returns:
            AppliedTemplate instance
        """
        template = self.get_template(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        customizations = customizations or {}
        
        # Apply customizations to template settings
        applied_settings = self._apply_customizations(
            template.cinematic_settings.copy(),
            customizations,
            template.customization_options
        )
        
        applied_template = AppliedTemplate(
            template_id=template_id,
            scene_id=scene_id,
            customizations=customizations,
            applied_settings=applied_settings,
            applied_at=datetime.utcnow().isoformat()
        )
        
        # Store applied template
        self.applied_templates[scene_id] = applied_template
        
        return applied_template
    
    def _apply_customizations(
        self,
        base_settings: Dict[str, Any],
        customizations: Dict[str, Any],
        customization_options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply customizations to base template settings."""
        
        for key, value in customizations.items():
            if key in customization_options:
                # Validate customization against options
                options = customization_options[key]
                
                if isinstance(options, list):
                    # Choice from list
                    if value in options:
                        self._apply_setting_value(base_settings, key, value)
                elif isinstance(options, tuple) and len(options) == 2:
                    # Range validation
                    min_val, max_val = options
                    if isinstance(value, (int, float)) and min_val <= value <= max_val:
                        self._apply_setting_value(base_settings, key, value)
        
        return base_settings
    
    def _apply_setting_value(
        self,
        settings: Dict[str, Any],
        key: str,
        value: Any
    ):
        """Apply a customization value to settings."""
        
        # Map customization keys to settings paths
        key_mappings = {
            'intensity_range': 'camera_movements.intensity',
            'color_temperature_range': 'color_grading.temperature',
            'movement_speed': 'camera_movements.intensity',
            'energy_level': 'camera_movements.intensity',
            'warmth_factor': 'color_grading.temperature'
        }
        
        if key in key_mappings:
            setting_path = key_mappings[key]
            self._set_nested_value(settings, setting_path, value)
    
    def _set_nested_value(
        self,
        settings: Dict[str, Any],
        path: str,
        value: Any
    ):
        """Set value in nested dictionary using dot notation."""
        keys = path.split('.')
        current = settings
        
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        
        current[keys[-1]] = value
    
    def get_applied_template(self, scene_id: str) -> Optional[AppliedTemplate]:
        """Get applied template for a scene."""
        return self.applied_templates.get(scene_id)
    
    def modify_applied_template(
        self,
        scene_id: str,
        modifications: Dict[str, Any]
    ) -> AppliedTemplate:
        """
        Modify an applied template while preserving editability.
        
        Args:
            scene_id: ID of scene with applied template
            modifications: Modifications to apply
            
        Returns:
            Updated AppliedTemplate
        """
        applied_template = self.applied_templates.get(scene_id)
        if not applied_template:
            raise ValueError(f"No applied template found for scene {scene_id}")
        
        template = self.get_template(applied_template.template_id)
        if not template or not template.is_editable:
            raise ValueError("Template is not editable")
        
        # Apply modifications
        for key, value in modifications.items():
            self._set_nested_value(applied_template.applied_settings, key, value)
        
        applied_template.is_modified = True
        applied_template.applied_at = datetime.utcnow().isoformat()
        
        return applied_template
    
    def list_templates(self) -> List[TemplateDefinition]:
        """List all available templates."""
        return list(self.templates.values())
    
    def create_custom_template(
        self,
        name: str,
        description: str,
        content_type: ContentType,
        visual_elements: Dict[str, Any],
        cinematic_settings: Dict[str, Any],
        customization_options: Optional[Dict[str, Any]] = None
    ) -> TemplateDefinition:
        """Create a new custom template."""
        
        template_id = name.lower().replace(' ', '_')
        
        template = TemplateDefinition(
            id=template_id,
            name=name,
            description=description,
            content_type=content_type,
            visual_elements=visual_elements,
            cinematic_settings=cinematic_settings,
            customization_options=customization_options or {},
            is_editable=True
        )
        
        self.templates[template_id] = template
        return template