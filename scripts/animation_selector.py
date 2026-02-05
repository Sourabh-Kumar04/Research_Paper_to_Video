"""
Intelligent Animation Selection System for RASO Platform

This module analyzes content and automatically selects the most appropriate
animation type, visual style, and generation parameters for educational videos.
"""

import re
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from enum import Enum
import logging
import json

from utils.ai_model_manager import ai_model_manager, ModelType
from utils.ai_prompt_manager import ai_prompt_manager, PromptType

logger = logging.getLogger(__name__)


class VisualType(Enum):
    """Types of visual content that can be generated."""
    MANIM = "manim"  # Mathematical animations, equations, proofs
    MOTION_CANVAS = "motion-canvas"  # Concept diagrams, flowcharts
    REMOTION = "remotion"  # UI elements, title sequences
    BLENDER_3D = "blender-3d"  # 3D visualizations, molecular models, network graphs
    CHART = "chart"  # Dynamic charts, graphs, data visualizations
    AUTO = "auto"  # Automatically choose best type


class ContentType(Enum):
    """Types of content that can be detected."""
    MATHEMATICAL = "mathematical"
    ALGORITHMIC = "algorithmic"
    CONCEPTUAL = "conceptual"
    PROCEDURAL = "procedural"
    STRUCTURAL = "structural"
    DATA_VISUALIZATION = "data_visualization"
    SCIENTIFIC_3D = "scientific_3d"
    NARRATIVE = "narrative"


class ComplexityLevel(Enum):
    """Complexity levels for content."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ADVANCED = "advanced"


class AnimationStyle(Enum):
    """Animation styles for different content types."""
    CLEAN_MINIMAL = "clean_minimal"
    ACADEMIC_FORMAL = "academic_formal"
    ENGAGING_DYNAMIC = "engaging_dynamic"
    TECHNICAL_PRECISE = "technical_precise"
    STORYTELLING = "storytelling"


@dataclass
class ContentAnalysis:
    """Analysis results for content."""
    content_type: ContentType
    complexity_level: ComplexityLevel
    key_concepts: List[str]
    mathematical_elements: List[str]
    process_steps: List[str]
    visual_elements: List[str]
    confidence_score: float
    metadata: Dict[str, Any]


@dataclass
class AnimationRecommendation:
    """Recommendation for animation generation."""
    visual_type: VisualType
    animation_style: AnimationStyle
    content_analysis: ContentAnalysis
    generation_parameters: Dict[str, Any]
    fallback_options: List[VisualType]
    reasoning: str


class IntelligentAnimationSelector:
    """Intelligent system for selecting appropriate animations based on content analysis."""
    
    def __init__(self):
        self.content_patterns = self._initialize_content_patterns()
        self.style_preferences = self._initialize_style_preferences()
        self.ai_analyzer_available = False
        
    def _initialize_content_patterns(self) -> Dict[ContentType, Dict[str, Any]]:
        """Initialize patterns for content type detection."""
        return {
            ContentType.MATHEMATICAL: {
                "keywords": [
                    "equation", "formula", "theorem", "proof", "derivative", "integral",
                    "matrix", "vector", "function", "graph", "plot", "mathematical",
                    "algebra", "calculus", "geometry", "statistics", "probability",
                    "optimization", "linear", "differential", "polynomial", "exponential"
                ],
                "patterns": [
                    r'[a-zA-Z]\s*=\s*[^=]+',  # Variable assignments
                    r'\$[^$]+\$',  # LaTeX equations
                    r'\\[a-zA-Z]+\{[^}]*\}',  # LaTeX commands
                    r'[∫∑∏∂∇αβγδεθλμπσφψω]',  # Mathematical symbols
                    r'\b\d+\s*[+\-*/^]\s*\d+',  # Mathematical expressions
                    r'\b[a-zA-Z]\([a-zA-Z0-9,\s]+\)',  # Function calls
                ],
                "visual_type": VisualType.MANIM,
                "complexity_indicators": ["proof", "theorem", "optimization", "differential"]
            },
            
            ContentType.ALGORITHMIC: {
                "keywords": [
                    "algorithm", "pseudocode", "complexity", "big-o", "recursion",
                    "iteration", "sorting", "searching", "tree", "graph", "dynamic",
                    "programming", "optimization", "heuristic", "greedy", "divide",
                    "conquer", "backtracking", "branch", "bound"
                ],
                "patterns": [
                    r'\bfor\s+\w+\s+in\s+',  # For loops
                    r'\bwhile\s+\w+',  # While loops
                    r'\bif\s+\w+\s+then',  # Conditional statements
                    r'\breturn\s+\w+',  # Return statements
                    r'O\([^)]+\)',  # Big-O notation
                    r'\b\w+\(\w+\)',  # Function calls
                ],
                "visual_type": VisualType.MOTION_CANVAS,
                "complexity_indicators": ["dynamic programming", "recursion", "optimization"]
            },
            
            ContentType.CONCEPTUAL: {
                "keywords": [
                    "concept", "idea", "principle", "theory", "framework", "model",
                    "approach", "methodology", "paradigm", "philosophy", "perspective",
                    "viewpoint", "understanding", "interpretation", "analysis", "synthesis"
                ],
                "patterns": [
                    r'\bconcept\s+of\s+\w+',
                    r'\btheory\s+of\s+\w+',
                    r'\bprinciple\s+of\s+\w+',
                    r'\bframework\s+for\s+\w+',
                ],
                "visual_type": VisualType.MOTION_CANVAS,
                "complexity_indicators": ["framework", "paradigm", "methodology"]
            },
            
            ContentType.PROCEDURAL: {
                "keywords": [
                    "step", "process", "procedure", "method", "workflow", "protocol",
                    "sequence", "stages", "phases", "instructions", "guide", "tutorial",
                    "implementation", "execution", "operation", "task", "activity"
                ],
                "patterns": [
                    r'\bstep\s+\d+',  # Numbered steps
                    r'\bfirst\b.*\bsecond\b.*\bthird\b',  # Sequential indicators
                    r'\bnext\b.*\bthen\b.*\bfinally\b',  # Process flow
                    r'^\d+\.\s+',  # Numbered lists
                    r'^[-*]\s+',  # Bullet points
                ],
                "visual_type": VisualType.MOTION_CANVAS,
                "complexity_indicators": ["workflow", "protocol", "implementation"]
            },
            
            ContentType.STRUCTURAL: {
                "keywords": [
                    "architecture", "structure", "component", "system", "design",
                    "organization", "hierarchy", "relationship", "connection", "interface",
                    "module", "layer", "framework", "pattern", "topology", "network"
                ],
                "patterns": [
                    r'\bcomponent\s+\w+',
                    r'\bsystem\s+architecture',
                    r'\bhierarchy\s+of\s+\w+',
                    r'\brelationship\s+between\s+\w+',
                ],
                "visual_type": VisualType.MOTION_CANVAS,
                "complexity_indicators": ["architecture", "hierarchy", "topology"]
            },
            
            ContentType.DATA_VISUALIZATION: {
                "keywords": [
                    "data", "chart", "graph", "plot", "visualization", "statistics",
                    "analysis", "trend", "pattern", "distribution", "correlation",
                    "regression", "clustering", "classification", "dataset", "metrics",
                    "histogram", "scatter", "bar chart", "line chart", "pie chart", "heatmap"
                ],
                "patterns": [
                    r'\bdata\s+shows',
                    r'\bgraph\s+of\s+\w+',
                    r'\bplot\s+\w+\s+vs\s+\w+',
                    r'\bstatistics\s+indicate',
                    r'\btrend\s+analysis',
                    r'\bchart\s+shows',
                    r'\bhistogram\s+of',
                    r'\bscatter\s+plot',
                    r'\bbar\s+chart',
                    r'\bline\s+graph',
                ],
                "visual_type": VisualType.CHART,  # Prefer charts for data visualization
                "complexity_indicators": ["regression", "clustering", "correlation", "statistical analysis"]
            },
            
            ContentType.SCIENTIFIC_3D: {
                "keywords": [
                    "molecular", "molecule", "atom", "bond", "protein", "dna", "rna",
                    "crystal", "lattice", "structure", "3d", "spatial", "geometry",
                    "network", "graph", "topology", "node", "edge", "connection",
                    "surface", "volume", "mesh", "model", "simulation", "visualization"
                ],
                "patterns": [
                    r'\bmolecular\s+structure',
                    r'\bprotein\s+folding',
                    r'\bcrystal\s+lattice',
                    r'\bnetwork\s+topology',
                    r'\b3d\s+model',
                    r'\bspatial\s+relationship',
                    r'\batomic\s+structure',
                    r'\bmolecule\s+\w+',
                ],
                "visual_type": VisualType.BLENDER_3D,
                "complexity_indicators": ["molecular dynamics", "protein folding", "network analysis", "3d modeling"]
            },
            
            ContentType.NARRATIVE: {
                "keywords": [
                    "story", "narrative", "example", "case", "scenario", "situation",
                    "context", "background", "history", "evolution", "development",
                    "journey", "experience", "perspective", "viewpoint"
                ],
                "patterns": [
                    r'\bfor\s+example\b',
                    r'\bconsider\s+the\s+case',
                    r'\bimagine\s+that\b',
                    r'\bstory\s+of\s+\w+',
                ],
                "visual_type": VisualType.MOTION_CANVAS,
                "complexity_indicators": ["evolution", "development", "perspective"]
            }
        }
    
    def _initialize_style_preferences(self) -> Dict[ContentType, AnimationStyle]:
        """Initialize style preferences for different content types."""
        return {
            ContentType.MATHEMATICAL: AnimationStyle.TECHNICAL_PRECISE,
            ContentType.ALGORITHMIC: AnimationStyle.TECHNICAL_PRECISE,
            ContentType.CONCEPTUAL: AnimationStyle.CLEAN_MINIMAL,
            ContentType.PROCEDURAL: AnimationStyle.ENGAGING_DYNAMIC,
            ContentType.STRUCTURAL: AnimationStyle.ACADEMIC_FORMAL,
            ContentType.DATA_VISUALIZATION: AnimationStyle.TECHNICAL_PRECISE,
            ContentType.SCIENTIFIC_3D: AnimationStyle.TECHNICAL_PRECISE,
            ContentType.NARRATIVE: AnimationStyle.STORYTELLING
        }
    
    async def initialize(self) -> bool:
        """Initialize the animation selector with AI capabilities."""
        try:
            # Check if AI model manager is available
            if ai_model_manager.ollama_available:
                self.ai_analyzer_available = True
                logger.info("✅ Intelligent Animation Selector initialized with AI analysis")
            else:
                logger.info("⚠️  Intelligent Animation Selector initialized without AI analysis")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Intelligent Animation Selector: {e}")
            return False
    
    async def analyze_content(
        self,
        title: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentAnalysis:
        """Analyze content to determine type, complexity, and key elements."""
        try:
            # Combine title and content for analysis
            full_text = f"{title}\n\n{content}"
            
            # Rule-based analysis
            rule_based_analysis = self._rule_based_analysis(full_text, metadata)
            
            # AI-enhanced analysis if available
            if self.ai_analyzer_available:
                ai_analysis = await self._ai_enhanced_analysis(full_text, rule_based_analysis)
                if ai_analysis:
                    return ai_analysis
            
            return rule_based_analysis
            
        except Exception as e:
            logger.error(f"Error analyzing content: {e}")
            return self._create_fallback_analysis(title, content)
    
    def _rule_based_analysis(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ContentAnalysis:
        """Perform rule-based content analysis."""
        text_lower = text.lower()
        
        # Score each content type
        type_scores = {}
        detected_elements = {
            "mathematical": [],
            "processes": [],
            "concepts": [],
            "visual_cues": []
        }
        
        for content_type, patterns in self.content_patterns.items():
            score = 0
            
            # Check keywords
            keyword_matches = 0
            for keyword in patterns["keywords"]:
                if keyword in text_lower:
                    keyword_matches += 1
                    score += 1
            
            # Check regex patterns
            pattern_matches = 0
            for pattern in patterns["patterns"]:
                matches = re.findall(pattern, text, re.IGNORECASE | re.MULTILINE)
                pattern_matches += len(matches)
                score += len(matches) * 2  # Patterns are weighted higher
                
                # Store specific matches
                if content_type == ContentType.MATHEMATICAL and matches:
                    detected_elements["mathematical"].extend(matches[:3])  # Limit to 3
            
            # Complexity indicators
            complexity_bonus = 0
            for indicator in patterns["complexity_indicators"]:
                if indicator in text_lower:
                    complexity_bonus += 2
            
            score += complexity_bonus
            type_scores[content_type] = {
                "score": score,
                "keyword_matches": keyword_matches,
                "pattern_matches": pattern_matches,
                "complexity_bonus": complexity_bonus
            }
        
        # Determine primary content type
        best_type = max(type_scores.keys(), key=lambda t: type_scores[t]["score"])
        best_score = type_scores[best_type]["score"]
        
        # Determine complexity level
        complexity = self._determine_complexity(text, type_scores[best_type])
        
        # Extract key concepts
        key_concepts = self._extract_key_concepts(text)
        
        # Extract process steps if procedural
        process_steps = []
        if best_type in [ContentType.PROCEDURAL, ContentType.ALGORITHMIC]:
            process_steps = self._extract_process_steps(text)
        
        # Extract visual elements
        visual_elements = self._extract_visual_elements(text)
        
        # Calculate confidence score
        total_possible_score = sum(len(p["keywords"]) + len(p["patterns"]) * 2 + len(p["complexity_indicators"]) * 2 
                                 for p in self.content_patterns.values())
        confidence = min(best_score / max(total_possible_score * 0.1, 1), 1.0)
        
        return ContentAnalysis(
            content_type=best_type,
            complexity_level=complexity,
            key_concepts=key_concepts,
            mathematical_elements=detected_elements["mathematical"],
            process_steps=process_steps,
            visual_elements=visual_elements,
            confidence_score=confidence,
            metadata={
                "analysis_method": "rule_based",
                "type_scores": {t.value: s["score"] for t, s in type_scores.items()},
                "best_score": best_score
            }
        )
    
    async def _ai_enhanced_analysis(
        self,
        text: str,
        rule_based_analysis: ContentAnalysis
    ) -> Optional[ContentAnalysis]:
        """Enhance analysis using AI models with specialized prompts."""
        try:
            # Get appropriate model for content analysis
            model = ai_model_manager.get_model_for_task("content_analysis")
            if not model:
                return None
            
            # Use specialized content analysis prompt
            analysis_variables = {
                "title": "Content Analysis",
                "content": text[:2000],  # Limit content length
                "target_audience": "general",
                "subject_area": "educational"
            }
            
            # Generate specialized prompt
            prompt = ai_prompt_manager.generate_prompt(
                "content_analysis", 
                analysis_variables,
                include_examples=False
            )
            
            if not prompt:
                return None
            
            # Generate AI analysis using optimized prompt
            response = await ai_model_manager.generate_with_model(
                model, prompt, temperature=0.1, max_tokens=1024
            )
            
            if not response:
                return None
            
            # Parse AI response
            ai_analysis = self._parse_ai_analysis(response, rule_based_analysis)
            return ai_analysis
            
        except Exception as e:
            logger.error(f"AI-enhanced analysis failed: {e}")
            return None
    
    def _create_analysis_prompt(self, text: str, rule_analysis: ContentAnalysis) -> str:
        """Create prompt for AI content analysis."""
        return f"""Analyze the following educational content and provide a detailed analysis:

CONTENT:
{text[:2000]}  # Limit content length

INITIAL ANALYSIS:
- Detected Type: {rule_analysis.content_type.value}
- Complexity: {rule_analysis.complexity_level.value}
- Confidence: {rule_analysis.confidence_score:.2f}

Please provide a JSON response with the following structure:
{{
    "content_type": "mathematical|algorithmic|conceptual|procedural|structural|data_visualization|narrative",
    "complexity_level": "simple|moderate|complex|advanced",
    "key_concepts": ["concept1", "concept2", "concept3"],
    "mathematical_elements": ["element1", "element2"],
    "process_steps": ["step1", "step2", "step3"],
    "visual_elements": ["visual1", "visual2"],
    "confidence_score": 0.85,
    "reasoning": "Brief explanation of the analysis"
}}

Focus on:
1. Identifying the primary educational content type
2. Assessing complexity based on technical depth
3. Extracting key concepts that should be visualized
4. Identifying mathematical formulas or expressions
5. Finding procedural steps or processes
6. Suggesting visual elements that would enhance understanding
"""
    
    def _parse_ai_analysis(
        self,
        ai_response: str,
        fallback_analysis: ContentAnalysis
    ) -> ContentAnalysis:
        """Parse AI analysis response."""
        try:
            # Try to extract JSON from response
            json_match = re.search(r'\{.*\}', ai_response, re.DOTALL)
            if not json_match:
                return fallback_analysis
            
            ai_data = json.loads(json_match.group())
            
            # Map string values to enums
            content_type_map = {
                "mathematical": ContentType.MATHEMATICAL,
                "algorithmic": ContentType.ALGORITHMIC,
                "conceptual": ContentType.CONCEPTUAL,
                "procedural": ContentType.PROCEDURAL,
                "structural": ContentType.STRUCTURAL,
                "data_visualization": ContentType.DATA_VISUALIZATION,
                "narrative": ContentType.NARRATIVE
            }
            
            complexity_map = {
                "simple": ComplexityLevel.SIMPLE,
                "moderate": ComplexityLevel.MODERATE,
                "complex": ComplexityLevel.COMPLEX,
                "advanced": ComplexityLevel.ADVANCED
            }
            
            content_type = content_type_map.get(
                ai_data.get("content_type", ""), 
                fallback_analysis.content_type
            )
            
            complexity = complexity_map.get(
                ai_data.get("complexity_level", ""), 
                fallback_analysis.complexity_level
            )
            
            return ContentAnalysis(
                content_type=content_type,
                complexity_level=complexity,
                key_concepts=ai_data.get("key_concepts", fallback_analysis.key_concepts),
                mathematical_elements=ai_data.get("mathematical_elements", fallback_analysis.mathematical_elements),
                process_steps=ai_data.get("process_steps", fallback_analysis.process_steps),
                visual_elements=ai_data.get("visual_elements", fallback_analysis.visual_elements),
                confidence_score=ai_data.get("confidence_score", fallback_analysis.confidence_score),
                metadata={
                    "analysis_method": "ai_enhanced",
                    "ai_reasoning": ai_data.get("reasoning", ""),
                    "fallback_used": False
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI analysis: {e}")
            return fallback_analysis
    
    def _determine_complexity(self, text: str, type_score: Dict[str, int]) -> ComplexityLevel:
        """Determine complexity level based on content analysis."""
        complexity_indicators = {
            ComplexityLevel.ADVANCED: [
                "theorem", "proof", "optimization", "differential", "integral",
                "complexity analysis", "advanced", "sophisticated", "intricate"
            ],
            ComplexityLevel.COMPLEX: [
                "algorithm", "framework", "methodology", "analysis", "implementation",
                "architecture", "system", "model", "approach"
            ],
            ComplexityLevel.MODERATE: [
                "method", "process", "procedure", "concept", "principle",
                "technique", "strategy", "pattern"
            ],
            ComplexityLevel.SIMPLE: [
                "basic", "simple", "introduction", "overview", "summary",
                "example", "illustration", "demonstration"
            ]
        }
        
        text_lower = text.lower()
        complexity_scores = {}
        
        for level, indicators in complexity_indicators.items():
            score = sum(1 for indicator in indicators if indicator in text_lower)
            complexity_scores[level] = score
        
        # Add bonus for pattern complexity
        if type_score["complexity_bonus"] > 0:
            complexity_scores[ComplexityLevel.COMPLEX] += type_score["complexity_bonus"]
        
        # Determine complexity based on highest score
        if complexity_scores[ComplexityLevel.ADVANCED] > 0:
            return ComplexityLevel.ADVANCED
        elif complexity_scores[ComplexityLevel.COMPLEX] > 1:
            return ComplexityLevel.COMPLEX
        elif complexity_scores[ComplexityLevel.MODERATE] > 0:
            return ComplexityLevel.MODERATE
        else:
            return ComplexityLevel.SIMPLE
    
    def _extract_key_concepts(self, text: str) -> List[str]:
        """Extract key concepts from text."""
        # Simple extraction based on capitalized words and technical terms
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        
        # Filter out common words
        common_words = {
            "The", "This", "That", "These", "Those", "When", "Where", "What", "How",
            "Figure", "Table", "Section", "Chapter", "Paper", "Study", "Research"
        }
        
        concepts = []
        for word in words:
            if word not in common_words and len(word) > 3:
                if word not in concepts:
                    concepts.append(word)
                    if len(concepts) >= 5:  # Limit to 5 concepts
                        break
        
        return concepts
    
    def _extract_process_steps(self, text: str) -> List[str]:
        """Extract process steps from text."""
        steps = []
        
        # Look for numbered steps
        numbered_steps = re.findall(r'^\d+\.\s*(.+)$', text, re.MULTILINE)
        if numbered_steps:
            steps.extend(numbered_steps[:6])  # Limit to 6 steps
        
        # Look for bullet points
        if not steps:
            bullet_steps = re.findall(r'^[-*]\s*(.+)$', text, re.MULTILINE)
            if bullet_steps:
                steps.extend(bullet_steps[:6])
        
        # Look for sequential indicators
        if not steps:
            sequential_patterns = [
                r'first[,:]?\s*(.+?)(?:\.|second|then|next)',
                r'second[,:]?\s*(.+?)(?:\.|third|then|next)',
                r'then[,:]?\s*(.+?)(?:\.|finally|next)',
                r'finally[,:]?\s*(.+?)(?:\.|$)'
            ]
            
            for pattern in sequential_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
                if matches:
                    steps.extend([match.strip()[:100] for match in matches])  # Limit length
        
        return steps[:6]  # Maximum 6 steps
    
    def _extract_visual_elements(self, text: str) -> List[str]:
        """Extract visual elements that should be emphasized."""
        visual_cues = []
        
        # Look for references to visual elements
        visual_patterns = [
            r'figure\s+\d+',
            r'table\s+\d+',
            r'diagram\s+\w+',
            r'graph\s+\w+',
            r'chart\s+\w+',
            r'plot\s+\w+',
            r'illustration\s+\w+',
            r'visualization\s+\w+'
        ]
        
        for pattern in visual_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            visual_cues.extend(matches)
        
        return visual_cues[:4]  # Limit to 4 visual elements
    
    def _create_fallback_analysis(self, title: str, content: str) -> ContentAnalysis:
        """Create fallback analysis when other methods fail."""
        return ContentAnalysis(
            content_type=ContentType.CONCEPTUAL,
            complexity_level=ComplexityLevel.MODERATE,
            key_concepts=[title] if title else ["Content"],
            mathematical_elements=[],
            process_steps=[],
            visual_elements=[],
            confidence_score=0.3,
            metadata={"analysis_method": "fallback"}
        )
    
    async def recommend_animation(
        self,
        title: str,
        content: str,
        duration: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AnimationRecommendation:
        """Recommend the best animation approach for given content."""
        try:
            # Analyze content
            analysis = await self.analyze_content(title, content, metadata)
            
            # Get base visual type from content patterns
            base_visual_type = self.content_patterns[analysis.content_type]["visual_type"]
            
            # Determine animation style
            animation_style = self.style_preferences[analysis.content_type]
            
            # Create generation parameters
            generation_params = self._create_generation_parameters(
                analysis, duration, animation_style
            )
            
            # Determine fallback options
            fallback_options = self._determine_fallback_options(base_visual_type, analysis)
            
            # Create reasoning
            reasoning = self._create_reasoning(analysis, base_visual_type, animation_style)
            
            return AnimationRecommendation(
                visual_type=base_visual_type,
                animation_style=animation_style,
                content_analysis=analysis,
                generation_parameters=generation_params,
                fallback_options=fallback_options,
                reasoning=reasoning
            )
            
        except Exception as e:
            logger.error(f"Error creating animation recommendation: {e}")
            return self._create_fallback_recommendation(title, content, duration)
    
    def _create_generation_parameters(
        self,
        analysis: ContentAnalysis,
        duration: float,
        style: AnimationStyle
    ) -> Dict[str, Any]:
        """Create generation parameters based on analysis."""
        base_params = {
            "duration": duration,
            "complexity": analysis.complexity_level.value,
            "key_concepts": analysis.key_concepts,
            "style": style.value
        }
        
        # Add content-type specific parameters
        if analysis.content_type == ContentType.MATHEMATICAL:
            base_params.update({
                "equations": analysis.mathematical_elements,
                "animation_speed": "slow" if analysis.complexity_level in [ComplexityLevel.COMPLEX, ComplexityLevel.ADVANCED] else "medium",
                "show_derivation": len(analysis.mathematical_elements) > 0,
                "color_scheme": "academic"
            })
        
        elif analysis.content_type == ContentType.PROCEDURAL:
            base_params.update({
                "steps": analysis.process_steps,
                "show_transitions": True,
                "step_timing": duration / max(len(analysis.process_steps), 1),
                "highlight_current_step": True,
                "color_scheme": "process"
            })
        
        elif analysis.content_type == ContentType.ALGORITHMIC:
            base_params.update({
                "algorithm_steps": analysis.process_steps,
                "show_complexity": True,
                "code_highlighting": True,
                "execution_flow": True,
                "color_scheme": "technical"
            })
        
        elif analysis.content_type == ContentType.STRUCTURAL:
            base_params.update({
                "components": analysis.key_concepts,
                "show_relationships": True,
                "layout": "hierarchical",
                "connection_style": "clean",
                "color_scheme": "structural"
            })
        
        elif analysis.content_type == ContentType.DATA_VISUALIZATION:
            base_params.update({
                "chart_type": "auto",
                "show_data_points": True,
                "animate_data_entry": True,
                "highlight_trends": True,
                "animate_chart": True,
                "chart_theme": "whitegrid",
                "color_scheme": "viridis"
            })
        
        else:  # CONCEPTUAL, NARRATIVE
            base_params.update({
                "concepts": analysis.key_concepts,
                "storytelling_mode": analysis.content_type == ContentType.NARRATIVE,
                "concept_connections": True,
                "color_scheme": "conceptual"
            })
        
        return base_params
    
    def _determine_fallback_options(
        self,
        primary_type: VisualType,
        analysis: ContentAnalysis
    ) -> List[VisualType]:
        """Determine fallback options if primary type fails."""
        fallbacks = []
        
        if primary_type == VisualType.MANIM:
            # If Manim fails, try Motion Canvas for simpler visualizations
            fallbacks = [VisualType.MOTION_CANVAS, VisualType.CHART, VisualType.AUTO]
        
        elif primary_type == VisualType.MOTION_CANVAS:
            # If Motion Canvas fails, try Manim for mathematical content or charts for data
            if analysis.content_type in [ContentType.MATHEMATICAL, ContentType.DATA_VISUALIZATION]:
                fallbacks = [VisualType.MANIM, VisualType.CHART, VisualType.AUTO]
            else:
                fallbacks = [VisualType.CHART, VisualType.AUTO]
        
        elif primary_type == VisualType.CHART:
            # If Chart fails, try Motion Canvas or Manim based on content
            if analysis.content_type == ContentType.MATHEMATICAL:
                fallbacks = [VisualType.MANIM, VisualType.MOTION_CANVAS, VisualType.AUTO]
            else:
                fallbacks = [VisualType.MOTION_CANVAS, VisualType.AUTO]
        
        elif primary_type == VisualType.BLENDER_3D:
            # If 3D fails, try charts for data or motion canvas for concepts
            if analysis.content_type == ContentType.DATA_VISUALIZATION:
                fallbacks = [VisualType.CHART, VisualType.MOTION_CANVAS, VisualType.AUTO]
            else:
                fallbacks = [VisualType.MOTION_CANVAS, VisualType.CHART, VisualType.AUTO]
        
        else:  # AUTO or others
            fallbacks = [VisualType.MOTION_CANVAS, VisualType.CHART, VisualType.MANIM]
        
        return fallbacks
    
    def _create_reasoning(
        self,
        analysis: ContentAnalysis,
        visual_type: VisualType,
        style: AnimationStyle
    ) -> str:
        """Create reasoning explanation for the recommendation."""
        reasoning_parts = []
        
        # Content type reasoning
        reasoning_parts.append(
            f"Content identified as {analysis.content_type.value} "
            f"with {analysis.complexity_level.value} complexity"
        )
        
        # Visual type reasoning
        if visual_type == VisualType.MANIM:
            reasoning_parts.append(
                "Manim recommended for mathematical precision and equation rendering"
            )
        elif visual_type == VisualType.MOTION_CANVAS:
            reasoning_parts.append(
                "Motion Canvas recommended for conceptual diagrams and process visualization"
            )
        elif visual_type == VisualType.CHART:
            reasoning_parts.append(
                "Dynamic charts recommended for data visualization and statistical analysis"
            )
        elif visual_type == VisualType.BLENDER_3D:
            reasoning_parts.append(
                "3D visualization recommended for complex spatial relationships and molecular structures"
            )
        
        # Style reasoning
        style_reasons = {
            AnimationStyle.TECHNICAL_PRECISE: "precise technical presentation",
            AnimationStyle.CLEAN_MINIMAL: "clean, distraction-free learning",
            AnimationStyle.ENGAGING_DYNAMIC: "dynamic, engaging presentation",
            AnimationStyle.ACADEMIC_FORMAL: "formal academic presentation",
            AnimationStyle.STORYTELLING: "narrative-driven explanation"
        }
        
        reasoning_parts.append(f"Style chosen for {style_reasons[style]}")
        
        # Confidence reasoning
        if analysis.confidence_score > 0.8:
            reasoning_parts.append("High confidence in content analysis")
        elif analysis.confidence_score > 0.6:
            reasoning_parts.append("Moderate confidence in content analysis")
        else:
            reasoning_parts.append("Low confidence - using conservative approach")
        
        return ". ".join(reasoning_parts) + "."
    
    def _create_fallback_recommendation(
        self,
        title: str,
        content: str,
        duration: float
    ) -> AnimationRecommendation:
        """Create fallback recommendation when analysis fails."""
        fallback_analysis = self._create_fallback_analysis(title, content)
        
        return AnimationRecommendation(
            visual_type=VisualType.MOTION_CANVAS,  # Safe default
            animation_style=AnimationStyle.CLEAN_MINIMAL,
            content_analysis=fallback_analysis,
            generation_parameters={
                "duration": duration,
                "complexity": "moderate",
                "key_concepts": [title] if title else ["Content"],
                "style": "clean_minimal",
                "color_scheme": "default"
            },
            fallback_options=[VisualType.MANIM, VisualType.AUTO],
            reasoning="Fallback recommendation due to analysis failure. Using safe defaults."
        )
    
    def get_content_type_info(self) -> Dict[str, Any]:
        """Get information about supported content types."""
        return {
            content_type.value: {
                "description": self._get_content_type_description(content_type),
                "recommended_visual_type": patterns["visual_type"].value,
                "complexity_indicators": patterns["complexity_indicators"],
                "example_keywords": patterns["keywords"][:5]  # First 5 keywords
            }
            for content_type, patterns in self.content_patterns.items()
        }
    
    def _get_content_type_description(self, content_type: ContentType) -> str:
        """Get description for content type."""
        descriptions = {
            ContentType.MATHEMATICAL: "Mathematical equations, formulas, proofs, and quantitative analysis",
            ContentType.ALGORITHMIC: "Algorithms, pseudocode, computational procedures, and complexity analysis",
            ContentType.CONCEPTUAL: "Abstract concepts, theories, principles, and conceptual frameworks",
            ContentType.PROCEDURAL: "Step-by-step processes, workflows, procedures, and instructions",
            ContentType.STRUCTURAL: "System architectures, component relationships, and structural designs",
            ContentType.DATA_VISUALIZATION: "Data analysis, charts, graphs, statistical visualizations",
            ContentType.NARRATIVE: "Stories, examples, case studies, and narrative explanations"
        }
        return descriptions.get(content_type, "General content type")


# Global instance for easy access
animation_selector = IntelligentAnimationSelector()