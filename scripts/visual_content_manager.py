"""
Visual Content Manager for RASO Platform

This module coordinates different visual content generation systems
(Manim, Motion Canvas, Remotion) and provides unified interface.
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from enum import Enum
import logging

from utils.manim_generator import manim_generator, ManimScene
from utils.motion_canvas_generator import motion_canvas_generator, MotionCanvasScene
from utils.ai_model_manager import ai_model_manager
from utils.ai_prompt_manager import ai_prompt_manager
from utils.animation_selector import animation_selector, AnimationRecommendation, VisualType
from utils.blender_3d_generator import blender_3d_generator, Visualization3DType, Molecule3D, NetworkGraph3D
from utils.chart_generator import chart_generator, ChartType, ChartData, ChartStyle, AnimationConfig, AnimationType
from utils.visual_style_manager import visual_style_manager, AnimationType as StyleAnimationType

logger = logging.getLogger(__name__)


@dataclass
class VisualRequest:
    """Request for visual content generation."""
    scene_id: str
    title: str
    content: str
    visual_type: VisualType
    duration: float
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class VisualAsset:
    """Generated visual asset."""
    scene_id: str
    title: str
    visual_type: VisualType
    file_path: Optional[str]
    duration: float
    generation_code: str
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None


class VisualContentManager:
    """Manages visual content generation across different systems."""
    
    def __init__(self):
        self.generators_initialized = False
        self.available_generators = {}
        
    async def initialize(self) -> Dict[str, bool]:
        """Initialize all visual content generators."""
        try:
            results = {}
            
            # Initialize Visual Style Manager
            logger.info("Initializing Visual Style Manager...")
            results['visual_style'] = await visual_style_manager.initialize()
            if results['visual_style']:
                logger.info("✅ Visual Style Manager initialized successfully")
            else:
                logger.warning("❌ Visual Style Manager initialization failed")
            
            # Initialize Animation Selector
            logger.info("Initializing Intelligent Animation Selector...")
            results['animation_selector'] = await animation_selector.initialize()
            if results['animation_selector']:
                logger.info("✅ Intelligent Animation Selector initialized successfully")
            else:
                logger.warning("❌ Intelligent Animation Selector initialization failed")
            
            # Initialize Chart Generator
            logger.info("Initializing Dynamic Chart Generator...")
            results['chart_generator'] = await chart_generator.initialize()
            if results['chart_generator']:
                self.available_generators['chart_generator'] = chart_generator
                logger.info("✅ Dynamic Chart Generator initialized successfully")
            else:
                logger.warning("❌ Dynamic Chart Generator initialization failed")
            
            # Initialize Blender 3D Generator
            logger.info("Initializing Blender 3D Generator...")
            results['blender_3d'] = await blender_3d_generator.initialize()
            if results['blender_3d']:
                self.available_generators['blender_3d'] = blender_3d_generator
                logger.info("✅ Blender 3D Generator initialized successfully")
            else:
                logger.warning("❌ Blender 3D Generator initialization failed")
            
            # Initialize Manim
            logger.info("Initializing Manim generator...")
            results['manim'] = await manim_generator.initialize()
            if results['manim']:
                self.available_generators['manim'] = manim_generator
                logger.info("✅ Manim generator initialized successfully")
            else:
                logger.warning("❌ Manim generator initialization failed")
            
            # Initialize Motion Canvas
            logger.info("Initializing Motion Canvas generator...")
            results['motion_canvas'] = await motion_canvas_generator.initialize()
            if results['motion_canvas']:
                self.available_generators['motion_canvas'] = motion_canvas_generator
                logger.info("✅ Motion Canvas generator initialized successfully")
            else:
                logger.warning("❌ Motion Canvas generator initialization failed")
            
            # Initialize AI Model Manager
            logger.info("Initializing AI Model Manager...")
            results['ai_models'] = await ai_model_manager.initialize_ollama()
            if results['ai_models']:
                logger.info("✅ AI Model Manager initialized successfully")
            else:
                logger.warning("❌ AI Model Manager initialization failed")
            
            self.generators_initialized = True
            
            # Log summary
            available_count = sum(1 for available in results.values() if available)
            logger.info(f"Visual Content Manager initialized: {available_count}/{len(results)} generators available")
            
            return results
            
        except Exception as e:
            logger.error(f"Failed to initialize Visual Content Manager: {e}")
            return {'animation_selector': False, 'visual_style': False, 'chart_generator': False, 'blender_3d': False, 'manim': False, 'motion_canvas': False, 'ai_models': False}
    
    async def generate_visual_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str = "medium"
    ) -> VisualAsset:
        """Generate visual content based on intelligent analysis and recommendation."""
        try:
            if not self.generators_initialized:
                await self.initialize()
            
            # Get intelligent recommendation for animation type and parameters
            recommendation = await animation_selector.recommend_animation(
                title=request.title,
                content=request.content,
                duration=request.duration,
                metadata=request.metadata
            )
            
            logger.info(f"Animation recommendation for scene {request.scene_id}:")
            logger.info(f"  - Content Type: {recommendation.content_analysis.content_type.value}")
            logger.info(f"  - Complexity: {recommendation.content_analysis.complexity_level.value}")
            logger.info(f"  - Visual Type: {recommendation.visual_type.value}")
            logger.info(f"  - Style: {recommendation.animation_style.value}")
            logger.info(f"  - Confidence: {recommendation.content_analysis.confidence_score:.2f}")
            logger.info(f"  - Reasoning: {recommendation.reasoning}")
            
            # Override request visual type if AUTO or use recommendation
            if request.visual_type == VisualType.AUTO:
                request.visual_type = recommendation.visual_type
            
            # Generate content with enhanced parameters
            enhanced_request = self._enhance_request_with_recommendation(request, recommendation)
            
            # Try primary recommendation
            result = await self._generate_with_recommendation(
                enhanced_request, output_dir, quality, recommendation
            )
            
            # Try fallback options if primary fails
            if not result.success and recommendation.fallback_options:
                logger.info(f"Primary generation failed, trying fallback options...")
                
                for fallback_type in recommendation.fallback_options:
                    logger.info(f"Trying fallback: {fallback_type.value}")
                    
                    fallback_request = enhanced_request
                    fallback_request.visual_type = fallback_type
                    
                    result = await self._generate_with_type(fallback_request, output_dir, quality)
                    
                    if result.success:
                        logger.info(f"Fallback {fallback_type.value} succeeded")
                        break
            
            # Add recommendation metadata to result
            if result.metadata:
                result.metadata.update({
                    'recommendation': {
                        'content_type': recommendation.content_analysis.content_type.value,
                        'complexity': recommendation.content_analysis.complexity_level.value,
                        'confidence': recommendation.content_analysis.confidence_score,
                        'reasoning': recommendation.reasoning,
                        'key_concepts': recommendation.content_analysis.key_concepts
                    }
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating visual content: {e}")
            return self._create_error_asset(request, str(e))
    
    def _enhance_request_with_recommendation(
        self,
        request: VisualRequest,
        recommendation: AnimationRecommendation
    ) -> VisualRequest:
        """Enhance request with intelligent recommendation parameters."""
        # Add recommendation parameters to metadata
        enhanced_metadata = request.metadata.copy() if request.metadata else {}
        enhanced_metadata.update({
            'generation_params': recommendation.generation_parameters,
            'content_analysis': {
                'type': recommendation.content_analysis.content_type.value,
                'complexity': recommendation.content_analysis.complexity_level.value,
                'key_concepts': recommendation.content_analysis.key_concepts,
                'mathematical_elements': recommendation.content_analysis.mathematical_elements,
                'process_steps': recommendation.content_analysis.process_steps
            },
            'animation_style': recommendation.animation_style.value
        })
        
        return VisualRequest(
            scene_id=request.scene_id,
            title=request.title,
            content=request.content,
            visual_type=request.visual_type,
            duration=request.duration,
            metadata=enhanced_metadata
        )
    
    async def _generate_with_recommendation(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str,
        recommendation: AnimationRecommendation
    ) -> VisualAsset:
        """Generate content using intelligent recommendation."""
        logger.info(f"Generating {request.visual_type.value} content with intelligent parameters")
        
        return await self._generate_with_type(request, output_dir, quality)
    
    async def _generate_with_type(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate content based on visual type."""
        if request.visual_type == VisualType.MANIM:
            return await self._generate_manim_content(request, output_dir, quality)
        elif request.visual_type == VisualType.MOTION_CANVAS:
            return await self._generate_motion_canvas_content(request, output_dir, quality)
        elif request.visual_type == VisualType.BLENDER_3D:
            return await self._generate_blender_3d_content(request, output_dir, quality)
        elif request.visual_type == VisualType.REMOTION:
            return await self._generate_remotion_content(request, output_dir, quality)
        elif request.visual_type == VisualType.CHART:
            return await self._generate_chart_content(request, output_dir, quality)
        else:
            return self._create_error_asset(request, f"Unsupported visual type: {request.visual_type}")
    
    def _determine_visual_type(self, content: str, metadata: Optional[Dict[str, Any]]) -> VisualType:
        """Automatically determine the best visual type for content."""
        content_lower = content.lower()
        
        # Check for mathematical content (use Manim)
        math_indicators = [
            'equation', 'formula', 'theorem', 'proof', 'derivative', 'integral',
            'matrix', 'vector', 'function', 'graph', 'plot', 'mathematical',
            'algebra', 'calculus', 'geometry', 'statistics', 'probability'
        ]
        
        if any(indicator in content_lower for indicator in math_indicators):
            return VisualType.MANIM
        
        # Check for process/flow content (use Motion Canvas)
        process_indicators = [
            'process', 'workflow', 'flowchart', 'diagram', 'steps', 'procedure',
            'algorithm', 'method', 'approach', 'system', 'architecture',
            'concept', 'relationship', 'connection', 'flow', 'sequence'
        ]
        
        if any(indicator in content_lower for indicator in process_indicators):
            return VisualType.MOTION_CANVAS
        
        # Check metadata for hints
        if metadata:
            concepts = metadata.get('concepts', [])
            if any('math' in str(concept).lower() or 'equation' in str(concept).lower() for concept in concepts):
                return VisualType.MANIM
            
            if any('process' in str(concept).lower() or 'flow' in str(concept).lower() for concept in concepts):
                return VisualType.MOTION_CANVAS
        
        # Default to Motion Canvas for general content
        return VisualType.MOTION_CANVAS
    
    async def _generate_manim_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate Manim visual content with intelligent parameters."""
        try:
            if 'manim' not in self.available_generators:
                return await self._generate_fallback_content(request, output_dir, "Manim not available")
            
            # Get intelligent parameters from metadata
            generation_params = request.metadata.get('generation_params', {}) if request.metadata else {}
            content_analysis = request.metadata.get('content_analysis', {}) if request.metadata else {}
            
            # Get consistent styling from visual style manager
            manim_style = visual_style_manager.get_manim_style_config()
            
            # Analyze content to determine Manim generation type
            content_type = self._analyze_manim_content_type(request.content)
            
            # Override with intelligent analysis if available
            if content_analysis.get('type') == 'mathematical':
                content_type = "equation" if content_analysis.get('mathematical_elements') else "concept"
            
            scene = None
            
            if content_type == "equation" or generation_params.get('equations'):
                # Use specialized Manim equation prompt
                equations = generation_params.get('equations', [])
                if not equations:
                    equations = [self._extract_equation(request.content)]
                
                equation = equations[0] if equations else "f(x) = x"
                
                # Prepare variables for the specialized prompt
                prompt_variables = {
                    "title": request.title,
                    "equation": equation,
                    "context": request.content[:500],  # Limit context length
                    "difficulty": generation_params.get('complexity', 'moderate'),
                    "animation_type": generation_params.get('animation_speed', 'medium'),
                    "duration": str(request.duration),
                    "background_color": manim_style.get('background_color', 'BLACK'),
                    "primary_color": manim_style.get('default_mobject_color', 'BLUE'),
                    "text_color": manim_style.get('text_color', 'WHITE'),
                    "font_size": str(manim_style.get('font_size', 36))
                }
                
                # Generate specialized Manim prompt
                manim_prompt = ai_prompt_manager.generate_prompt(
                    "manim_equation", 
                    prompt_variables,
                    include_examples=True
                )
                
                if manim_prompt:
                    # Get best model for Manim code generation
                    model = ai_model_manager.get_model_for_task("manim_code")
                    
                    if model:
                        # Generate Manim code using AI
                        generated_code = await ai_model_manager.generate_with_model(
                            model, manim_prompt, temperature=0.2, max_tokens=2048
                        )
                        
                        if generated_code:
                            # Extract code from response (remove markdown formatting)
                            import re
                            code_match = re.search(r'```python\n(.*?)\n```', generated_code, re.DOTALL)
                            if code_match:
                                clean_code = code_match.group(1)
                                
                                # Create scene with generated code
                                scene = await manim_generator.create_scene_from_code(
                                    clean_code, request.scene_id
                                )
                
                # Fallback to traditional generation if AI fails
                if not scene:
                    scene = await manim_generator.generate_equation_animation(
                        equation=equation,
                        context=request.content,
                        duration=request.duration,
                        scene_id=request.scene_id,
                        animation_speed=generation_params.get('animation_speed', 'medium'),
                        show_derivation=generation_params.get('show_derivation', False),
                        color_scheme=generation_params.get('color_scheme', 'academic'),
                        style_config=manim_style
                    )
            
            elif content_type == "concept" or generation_params.get('key_concepts'):
                # Use intelligent concept analysis
                key_concepts = generation_params.get('key_concepts', [request.title])
                primary_concept = key_concepts[0] if key_concepts else request.title
                
                scene = await manim_generator.generate_concept_visualization(
                    concept=primary_concept,
                    description=request.content,
                    visual_type="mathematical",
                    duration=request.duration,
                    scene_id=request.scene_id,
                    # Add intelligent parameters with consistent styling
                    complexity=generation_params.get('complexity', 'moderate'),
                    color_scheme=generation_params.get('color_scheme', 'academic'),
                    # Apply visual style manager settings
                    style_config=manim_style
                )
            
            else:
                # General mathematical content with intelligent parameters
                scene = await manim_generator.generate_concept_visualization(
                    concept=request.title,
                    description=request.content,
                    visual_type="general",
                    duration=request.duration,
                    scene_id=request.scene_id,
                    complexity=generation_params.get('complexity', 'moderate'),
                    color_scheme=generation_params.get('color_scheme', 'academic'),
                    # Apply visual style manager settings
                    style_config=manim_style
                )
            
            if not scene:
                return await self._generate_fallback_content(request, output_dir, "Manim generation failed")
            
            # Render the scene
            output_file = await manim_generator.render_scene(scene, output_dir, quality)
            
            if output_file:
                return VisualAsset(
                    scene_id=request.scene_id,
                    title=request.title,
                    visual_type=VisualType.MANIM,
                    file_path=output_file,
                    duration=request.duration,
                    generation_code=scene.manim_code,
                    metadata={
                        'content_type': content_type,
                        'generator': 'manim',
                        'quality': quality,
                        'intelligent_params': generation_params,
                        'content_analysis': content_analysis
                    },
                    success=True
                )
            else:
                return await self._generate_fallback_content(request, output_dir, "Manim rendering failed")
                
        except Exception as e:
            logger.error(f"Manim generation error: {e}")
            return await self._generate_fallback_content(request, output_dir, f"Manim error: {e}")
    
    async def _generate_motion_canvas_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate Motion Canvas visual content with intelligent parameters."""
        try:
            if 'motion_canvas' not in self.available_generators:
                return await self._generate_fallback_content(request, output_dir, "Motion Canvas not available")
            
            # Get intelligent parameters from metadata
            generation_params = request.metadata.get('generation_params', {}) if request.metadata else {}
            content_analysis = request.metadata.get('content_analysis', {}) if request.metadata else {}
            
            # Get consistent styling from visual style manager
            motion_canvas_style = visual_style_manager.get_motion_canvas_style_config()
            
            # Analyze content to determine Motion Canvas generation type
            content_type = self._analyze_motion_canvas_content_type(request.content)
            
            # Override with intelligent analysis if available
            analysis_type = content_analysis.get('type', '')
            if analysis_type in ['procedural', 'algorithmic']:
                content_type = "flowchart"
            elif analysis_type == 'structural':
                content_type = "diagram"
            
            scene = None
            
            if content_type == "flowchart" or generation_params.get('steps'):
                # Use intelligent process extraction or fallback
                process_steps = generation_params.get('steps', [])
                if not process_steps:
                    process_info = self._extract_process_info(request.content)
                    process_steps = process_info['steps']
                    connections = process_info['connections']
                else:
                    # Create connections from steps
                    connections = [(process_steps[i], process_steps[i+1]) 
                                 for i in range(len(process_steps)-1)]
                
                scene = await motion_canvas_generator.generate_flowchart_animation(
                    process_name=request.title,
                    steps=process_steps,
                    connections=connections,
                    duration=request.duration,
                    scene_id=request.scene_id,
                    # Add intelligent parameters with consistent styling
                    show_transitions=generation_params.get('show_transitions', True),
                    highlight_current_step=generation_params.get('highlight_current_step', True),
                    color_scheme=generation_params.get('color_scheme', 'process'),
                    # Apply visual style manager settings
                    style_config=motion_canvas_style
                )
            
            elif content_type == "diagram" or generation_params.get('components'):
                # Use intelligent component extraction
                components = generation_params.get('components', content_analysis.get('key_concepts', []))
                if not components:
                    components = self._extract_diagram_components(request.content)
                
                scene = await motion_canvas_generator.generate_diagram_animation(
                    diagram_type=request.title,
                    components=components,
                    layout=generation_params.get('layout', 'hierarchical'),
                    duration=request.duration,
                    scene_id=request.scene_id,
                    # Add intelligent parameters with consistent styling
                    show_relationships=generation_params.get('show_relationships', True),
                    connection_style=generation_params.get('connection_style', 'clean'),
                    color_scheme=generation_params.get('color_scheme', 'structural'),
                    # Apply visual style manager settings
                    style_config=motion_canvas_style
                )
            
            else:
                # General concept visualization with intelligent parameters
                key_concepts = generation_params.get('key_concepts', [request.title])
                
                scene = await motion_canvas_generator.generate_concept_visualization(
                    concept=key_concepts[0] if key_concepts else request.title,
                    description=request.content,
                    duration=request.duration,
                    scene_id=request.scene_id,
                    # Add intelligent parameters with consistent styling
                    concepts=key_concepts,
                    storytelling_mode=generation_params.get('storytelling_mode', False),
                    concept_connections=generation_params.get('concept_connections', True),
                    color_scheme=generation_params.get('color_scheme', 'conceptual'),
                    # Apply visual style manager settings
                    style_config=motion_canvas_style
                )
            
            if not scene:
                return await self._generate_fallback_content(request, output_dir, "Motion Canvas generation failed")
            
            # Render the scene
            output_file = await motion_canvas_generator.render_scene(scene, output_dir, quality)
            
            if output_file:
                return VisualAsset(
                    scene_id=request.scene_id,
                    title=request.title,
                    visual_type=VisualType.MOTION_CANVAS,
                    file_path=output_file,
                    duration=request.duration,
                    generation_code=scene.typescript_code,
                    metadata={
                        'content_type': content_type,
                        'generator': 'motion_canvas',
                        'quality': quality,
                        'intelligent_params': generation_params,
                        'content_analysis': content_analysis
                    },
                    success=True
                )
            else:
                return await self._generate_fallback_content(request, output_dir, "Motion Canvas rendering failed")
                
        except Exception as e:
            logger.error(f"Motion Canvas generation error: {e}")
            return await self._generate_fallback_content(request, output_dir, f"Motion Canvas error: {e}")
    
    async def _generate_blender_3d_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate Blender 3D visual content with intelligent parameters."""
        try:
            if 'blender_3d' not in self.available_generators:
                return await self._generate_fallback_content(request, output_dir, "Blender 3D not available")
            
            # Get intelligent parameters from metadata
            generation_params = request.metadata.get('generation_params', {}) if request.metadata else {}
            content_analysis = request.metadata.get('content_analysis', {}) if request.metadata else {}
            
            # Get consistent styling from visual style manager
            blender_style = visual_style_manager.get_blender_style_config()
            
            # Determine 3D visualization type based on content
            viz_type = self._determine_3d_visualization_type(request.content, content_analysis)
            
            scene = None
            
            if viz_type == Visualization3DType.MOLECULAR:
                # Generate molecular structure
                molecule = self._extract_molecular_structure(request.content, generation_params)
                scene = await blender_3d_generator.generate_molecular_visualization(
                    molecule=molecule,
                    scene_id=request.scene_id,
                    duration=request.duration,
                    animation_type=generation_params.get('animation_type', 'rotation'),
                    # Apply visual style manager settings
                    style_config=blender_style
                )
            
            elif viz_type == Visualization3DType.NETWORK_GRAPH:
                # Generate network graph
                network = self._extract_network_structure(request.content, generation_params)
                scene = await blender_3d_generator.generate_network_graph_3d(
                    network=network,
                    scene_id=request.scene_id,
                    duration=request.duration,
                    animation_type=generation_params.get('animation_type', 'force_directed'),
                    # Apply visual style manager settings
                    style_config=blender_style
                )
            
            elif viz_type == Visualization3DType.MATHEMATICAL_SURFACE:
                # Generate mathematical surface
                equation = self._extract_mathematical_equation(request.content, generation_params)
                scene = await blender_3d_generator.generate_mathematical_surface(
                    equation=equation,
                    scene_id=request.scene_id,
                    duration=request.duration,
                    x_range=generation_params.get('x_range', (-5, 5)),
                    y_range=generation_params.get('y_range', (-5, 5)),
                    # Apply visual style manager settings
                    style_config=blender_style
                )
            
            else:
                # Default: create a simple 3D geometric visualization
                return await self._generate_fallback_content(
                    request, output_dir, f"3D visualization type {viz_type} not yet implemented"
                )
            
            if not scene:
                return await self._generate_fallback_content(request, output_dir, "3D scene generation failed")
            
            # Render the 3D scene
            output_file = await blender_3d_generator.render_scene(scene, output_dir, quality)
            
            if output_file:
                return VisualAsset(
                    scene_id=request.scene_id,
                    title=request.title,
                    visual_type=VisualType.BLENDER_3D,
                    file_path=output_file,
                    duration=request.duration,
                    generation_code=scene.blender_script,
                    metadata={
                        'visualization_type': viz_type.value,
                        'generator': 'blender_3d',
                        'quality': quality,
                        'intelligent_params': generation_params,
                        'content_analysis': content_analysis,
                        'objects_count': len(scene.objects)
                    },
                    success=True
                )
            else:
                return await self._generate_fallback_content(request, output_dir, "3D rendering failed")
                
        except Exception as e:
            logger.error(f"Blender 3D generation error: {e}")
            return await self._generate_fallback_content(request, output_dir, f"3D error: {e}")
    
    def _determine_3d_visualization_type(
        self,
        content: str,
        content_analysis: Dict[str, Any]
    ) -> Visualization3DType:
        """Determine the best 3D visualization type for content."""
        content_lower = content.lower()
        
        # Check for molecular content
        molecular_keywords = ['molecule', 'molecular', 'atom', 'bond', 'protein', 'dna', 'chemical']
        if any(keyword in content_lower for keyword in molecular_keywords):
            return Visualization3DType.MOLECULAR
        
        # Check for network content
        network_keywords = ['network', 'graph', 'node', 'edge', 'connection', 'topology']
        if any(keyword in content_lower for keyword in network_keywords):
            return Visualization3DType.NETWORK_GRAPH
        
        # Check for mathematical surface content
        surface_keywords = ['surface', 'function', 'equation', 'plot', 'z=', 'f(x,y)']
        if any(keyword in content_lower for keyword in surface_keywords):
            return Visualization3DType.MATHEMATICAL_SURFACE
        
        # Check content analysis
        analysis_type = content_analysis.get('type', '')
        if analysis_type == 'scientific_3d':
            # Default to molecular for scientific 3D content
            return Visualization3DType.MOLECULAR
        
        # Default fallback
        return Visualization3DType.GEOMETRIC_SHAPE
    
    def _extract_molecular_structure(
        self,
        content: str,
        generation_params: Dict[str, Any]
    ) -> Molecule3D:
        """Extract or generate molecular structure from content."""
        # Simple molecular structure extraction (can be enhanced with AI)
        
        # Check if specific molecule is mentioned
        content_lower = content.lower()
        
        if 'water' in content_lower or 'h2o' in content_lower:
            # Water molecule
            return Molecule3D(
                atoms=[
                    {"element": "O", "position": [0, 0, 0], "radius": 1.5},
                    {"element": "H", "position": [1.0, 0.8, 0], "radius": 0.8},
                    {"element": "H", "position": [-1.0, 0.8, 0], "radius": 0.8}
                ],
                bonds=[
                    {"atom1": 0, "atom2": 1, "type": "single"},
                    {"atom1": 0, "atom2": 2, "type": "single"}
                ],
                name="Water (H2O)"
            )
        
        elif 'methane' in content_lower or 'ch4' in content_lower:
            # Methane molecule
            return Molecule3D(
                atoms=[
                    {"element": "C", "position": [0, 0, 0], "radius": 1.2},
                    {"element": "H", "position": [1.0, 1.0, 1.0], "radius": 0.8},
                    {"element": "H", "position": [-1.0, -1.0, 1.0], "radius": 0.8},
                    {"element": "H", "position": [-1.0, 1.0, -1.0], "radius": 0.8},
                    {"element": "H", "position": [1.0, -1.0, -1.0], "radius": 0.8}
                ],
                bonds=[
                    {"atom1": 0, "atom2": 1, "type": "single"},
                    {"atom1": 0, "atom2": 2, "type": "single"},
                    {"atom1": 0, "atom2": 3, "type": "single"},
                    {"atom1": 0, "atom2": 4, "type": "single"}
                ],
                name="Methane (CH4)"
            )
        
        else:
            # Generic molecule
            return Molecule3D(
                atoms=[
                    {"element": "C", "position": [0, 0, 0], "radius": 1.2},
                    {"element": "C", "position": [2, 0, 0], "radius": 1.2},
                    {"element": "O", "position": [3, 1.5, 0], "radius": 1.5},
                    {"element": "H", "position": [-1, 1, 0], "radius": 0.8},
                    {"element": "H", "position": [-1, -1, 0], "radius": 0.8}
                ],
                bonds=[
                    {"atom1": 0, "atom2": 1, "type": "single"},
                    {"atom1": 1, "atom2": 2, "type": "double"},
                    {"atom1": 0, "atom2": 3, "type": "single"},
                    {"atom1": 0, "atom2": 4, "type": "single"}
                ],
                name="Generic Molecule"
            )
    
    def _extract_network_structure(
        self,
        content: str,
        generation_params: Dict[str, Any]
    ) -> NetworkGraph3D:
        """Extract or generate network structure from content."""
        # Simple network structure generation
        
        # Check for specific network mentions
        content_lower = content.lower()
        
        if 'social' in content_lower:
            # Social network
            nodes = [
                {"id": "user1", "size": 1.2, "type": "hub"},
                {"id": "user2", "size": 1.0, "type": "default"},
                {"id": "user3", "size": 1.0, "type": "default"},
                {"id": "user4", "size": 0.8, "type": "secondary"},
                {"id": "user5", "size": 0.8, "type": "secondary"}
            ]
            edges = [
                {"from": "user1", "to": "user2", "weight": 1.0},
                {"from": "user1", "to": "user3", "weight": 0.8},
                {"from": "user2", "to": "user4", "weight": 0.6},
                {"from": "user3", "to": "user5", "weight": 0.7},
                {"from": "user1", "to": "user4", "weight": 0.5}
            ]
        
        elif 'neural' in content_lower or 'brain' in content_lower:
            # Neural network
            nodes = [
                {"id": "input1", "size": 1.0, "type": "important"},
                {"id": "input2", "size": 1.0, "type": "important"},
                {"id": "hidden1", "size": 1.2, "type": "hub"},
                {"id": "hidden2", "size": 1.2, "type": "hub"},
                {"id": "output", "size": 1.5, "type": "important"}
            ]
            edges = [
                {"from": "input1", "to": "hidden1", "weight": 0.8},
                {"from": "input1", "to": "hidden2", "weight": 0.6},
                {"from": "input2", "to": "hidden1", "weight": 0.7},
                {"from": "input2", "to": "hidden2", "weight": 0.9},
                {"from": "hidden1", "to": "output", "weight": 1.0},
                {"from": "hidden2", "to": "output", "weight": 0.8}
            ]
        
        else:
            # Generic network
            nodes = [
                {"id": "node1", "size": 1.0, "type": "default"},
                {"id": "node2", "size": 1.2, "type": "hub"},
                {"id": "node3", "size": 0.8, "type": "secondary"},
                {"id": "node4", "size": 1.0, "type": "default"}
            ]
            edges = [
                {"from": "node1", "to": "node2", "weight": 1.0},
                {"from": "node2", "to": "node3", "weight": 0.7},
                {"from": "node2", "to": "node4", "weight": 0.8},
                {"from": "node1", "to": "node4", "weight": 0.5}
            ]
        
        return NetworkGraph3D(
            nodes=nodes,
            edges=edges,
            layout="spring"
        )
    
    async def _generate_chart_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate dynamic chart and diagram content."""
        try:
            if 'chart_generator' not in self.available_generators:
                return await self._generate_fallback_content(request, output_dir, "Chart generator not available")
            
            # Get intelligent parameters from metadata
            generation_params = request.metadata.get('generation_parameters', {}) if request.metadata else {}
            content_analysis = request.metadata.get('content_analysis', {}) if request.metadata else {}
            
            # Determine chart type based on content
            chart_type = self._determine_chart_type(request.content, generation_params)
            
            # Extract or generate chart data
            chart_data = self._extract_chart_data(request.content, chart_type, generation_params)
            
            # Create chart style using visual style manager
            style_config = visual_style_manager.get_chart_style_config()
            chart_style = ChartStyle(
                color_palette=style_config.get('color_palette', ['viridis'])[0] if style_config.get('color_palette') else 'viridis',
                background_color=style_config.get('background_color', 'white'),
                text_color=style_config.get('text_color', 'black'),
                font_family=style_config.get('font_family', 'Arial'),
                font_size=style_config.get('font_size', 12),
                figure_size=(12, 8),
                dpi=150,
                style_theme=generation_params.get('chart_theme', 'whitegrid')
            )
            
            # Determine if animation is needed
            animate_chart = generation_params.get('animate_chart', True)
            output_path = Path(output_dir) / f"{request.scene_id}_chart.{'mp4' if animate_chart else 'png'}"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            result_path = None
            
            if animate_chart and request.duration > 0:
                # Generate animated chart
                animation_config = AnimationConfig(
                    animation_type=AnimationType.GROW_FROM_ZERO,
                    duration=request.duration,
                    fps=30,
                    easing="ease_in_out"
                )
                
                result_path = await chart_generator.generate_animated_chart(
                    chart_data, chart_style, animation_config, str(output_path)
                )
            else:
                # Generate static chart
                result_path = await chart_generator.generate_static_chart(
                    chart_data, chart_style, str(output_path)
                )
            
            if result_path:
                return VisualAsset(
                    scene_id=request.scene_id,
                    title=request.title,
                    visual_type=VisualType.CHART,
                    file_path=result_path,
                    duration=request.duration,
                    generation_code=f"# Chart generated: {chart_type.value}",
                    metadata={
                        'chart_type': chart_type.value,
                        'generator': 'chart_generator',
                        'quality': quality,
                        'animated': animate_chart,
                        'intelligent_params': generation_params,
                        'content_analysis': content_analysis
                    },
                    success=True
                )
            else:
                return await self._generate_fallback_content(request, output_dir, "Chart generation failed")
                
        except Exception as e:
            logger.error(f"Chart generation error: {e}")
            return await self._generate_fallback_content(request, output_dir, f"Chart error: {e}")
    
    def _determine_chart_type(self, content: str, generation_params: Dict[str, Any]) -> ChartType:
        """Determine the best chart type for content."""
        content_lower = content.lower()
        
        # Check for explicit chart type in parameters
        if 'chart_type' in generation_params:
            chart_type_map = {
                'line': ChartType.LINE_CHART,
                'bar': ChartType.BAR_CHART,
                'scatter': ChartType.SCATTER_PLOT,
                'histogram': ChartType.HISTOGRAM,
                'pie': ChartType.PIE_CHART,
                'heatmap': ChartType.HEATMAP,
                'box': ChartType.BOX_PLOT,
                'network': ChartType.NETWORK_DIAGRAM,
                'flowchart': ChartType.FLOWCHART,
                'timeline': ChartType.TIMELINE
            }
            return chart_type_map.get(generation_params['chart_type'], ChartType.LINE_CHART)
        
        # Auto-detect chart type from content
        if any(keyword in content_lower for keyword in ['timeline', 'chronology', 'history', 'sequence']):
            return ChartType.TIMELINE
        elif any(keyword in content_lower for keyword in ['process', 'workflow', 'steps', 'procedure']):
            return ChartType.FLOWCHART
        elif any(keyword in content_lower for keyword in ['network', 'graph', 'nodes', 'connections']):
            return ChartType.NETWORK_DIAGRAM
        elif any(keyword in content_lower for keyword in ['distribution', 'frequency', 'histogram']):
            return ChartType.HISTOGRAM
        elif any(keyword in content_lower for keyword in ['correlation', 'scatter', 'relationship']):
            return ChartType.SCATTER_PLOT
        elif any(keyword in content_lower for keyword in ['comparison', 'categories', 'bar']):
            return ChartType.BAR_CHART
        elif any(keyword in content_lower for keyword in ['proportion', 'percentage', 'pie']):
            return ChartType.PIE_CHART
        elif any(keyword in content_lower for keyword in ['heatmap', 'matrix', 'correlation matrix']):
            return ChartType.HEATMAP
        elif any(keyword in content_lower for keyword in ['trend', 'time series', 'over time', 'line']):
            return ChartType.LINE_CHART
        else:
            # Default to line chart
            return ChartType.LINE_CHART
    
    def _extract_chart_data(
        self,
        content: str,
        chart_type: ChartType,
        generation_params: Dict[str, Any]
    ) -> ChartData:
        """Extract or generate chart data from content."""
        # Check if data is provided in parameters
        if 'chart_data' in generation_params:
            return ChartData(
                data=generation_params['chart_data'],
                chart_type=chart_type,
                title=generation_params.get('chart_title', 'Data Visualization'),
                x_label=generation_params.get('x_label'),
                y_label=generation_params.get('y_label')
            )
        
        # Generate sample data based on chart type and content
        return chart_generator.generate_sample_data(chart_type, size=20)
    
    def _extract_mathematical_equation(
        self,
        content: str,
        generation_params: Dict[str, Any]
    ) -> str:
        """Extract mathematical equation for surface plotting."""
        content_lower = content.lower()
        
        # Look for common mathematical functions
        if 'sin' in content_lower and 'cos' in content_lower:
            return "sin(x) * cos(y)"
        elif 'x**2' in content_lower or 'x²' in content_lower:
            if 'y**2' in content_lower or 'y²' in content_lower:
                return "(x**2 + y**2) / 10"
            else:
                return "x**2"
        elif 'paraboloid' in content_lower:
            return "(x**2 + y**2) / 10"
        elif 'saddle' in content_lower:
            return "(x**2 - y**2) / 10"
        elif 'wave' in content_lower:
            return "sin(sqrt(x**2 + y**2))"
        else:
            # Default: simple paraboloid
            return "(x**2 + y**2) / 10"
    
    async def _generate_remotion_content(
        self,
        request: VisualRequest,
        output_dir: str,
        quality: str
    ) -> VisualAsset:
        """Generate Remotion visual content (placeholder for future implementation)."""
        logger.info("Remotion generator not yet implemented, using Motion Canvas fallback")
        
        # Use Motion Canvas as fallback for now
        request.visual_type = VisualType.MOTION_CANVAS
        return await self._generate_motion_canvas_content(request, output_dir, quality)
    
    async def _generate_fallback_content(
        self,
        request: VisualRequest,
        output_dir: str,
        reason: str
    ) -> VisualAsset:
        """Generate fallback visual content when primary generators fail."""
        try:
            logger.warning(f"Generating fallback content for {request.scene_id}: {reason}")
            
            # Try to create a simple placeholder video using FFmpeg
            output_path = Path(output_dir) / f"{request.scene_id}_fallback.mp4"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            success = await self._create_placeholder_video(
                str(output_path),
                request.title,
                request.content,
                request.duration
            )
            
            if success:
                return VisualAsset(
                    scene_id=request.scene_id,
                    title=request.title,
                    visual_type=request.visual_type,
                    file_path=str(output_path),
                    duration=request.duration,
                    generation_code="# Fallback placeholder video",
                    metadata={
                        'generator': 'fallback',
                        'reason': reason
                    },
                    success=True
                )
            else:
                return self._create_error_asset(request, f"Fallback generation failed: {reason}")
                
        except Exception as e:
            logger.error(f"Fallback generation error: {e}")
            return self._create_error_asset(request, f"Fallback error: {e}")
    
    async def _create_placeholder_video(
        self,
        output_path: str,
        title: str,
        content: str,
        duration: float
    ) -> bool:
        """Create a placeholder video using FFmpeg."""
        try:
            import subprocess
            
            # Create a simple placeholder video with text
            cmd = [
                "ffmpeg",
                "-f", "lavfi",
                "-i", f"color=c=#1e3a8a:size=1920x1080:duration={duration}",
                "-vf", (
                    f"drawtext=text='{title[:50]}':fontcolor=white:fontsize=60:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2-100,"
                    f"drawtext=text='Visual Content':fontcolor=white:fontsize=40:"
                    f"x=(w-text_w)/2:y=(h-text_h)/2+50"
                ),
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-y", output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and Path(output_path).exists():
                logger.info(f"Placeholder video created: {output_path}")
                return True
            else:
                logger.error(f"Placeholder video creation failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating placeholder video: {e}")
            return False
    
    def _create_error_asset(self, request: VisualRequest, error_message: str) -> VisualAsset:
        """Create an error asset when generation fails."""
        return VisualAsset(
            scene_id=request.scene_id,
            title=request.title,
            visual_type=request.visual_type,
            file_path=None,
            duration=request.duration,
            generation_code="",
            metadata={'error': True},
            success=False,
            error_message=error_message
        )
    
    def _analyze_manim_content_type(self, content: str) -> str:
        """Analyze content to determine Manim generation type."""
        content_lower = content.lower()
        
        # Look for equations
        equation_patterns = [
            r'[a-zA-Z]\s*=\s*[^=]+',  # Variable assignments
            r'\$[^$]+\$',  # LaTeX equations
            r'\\[a-zA-Z]+\{[^}]*\}',  # LaTeX commands
            r'[∫∑∏∂∇]',  # Mathematical symbols
        ]
        
        import re
        for pattern in equation_patterns:
            if re.search(pattern, content):
                return "equation"
        
        # Look for mathematical concepts
        math_keywords = ['theorem', 'proof', 'lemma', 'derivative', 'integral', 'matrix']
        if any(keyword in content_lower for keyword in math_keywords):
            return "concept"
        
        return "general"
    
    def _analyze_motion_canvas_content_type(self, content: str) -> str:
        """Analyze content to determine Motion Canvas generation type."""
        content_lower = content.lower()
        
        # Look for flowchart indicators
        flowchart_keywords = ['step', 'process', 'workflow', 'procedure', 'algorithm', 'method']
        if any(keyword in content_lower for keyword in flowchart_keywords):
            return "flowchart"
        
        # Look for diagram indicators
        diagram_keywords = ['component', 'system', 'architecture', 'structure', 'relationship']
        if any(keyword in content_lower for keyword in diagram_keywords):
            return "diagram"
        
        return "concept"
    
    def _extract_equation(self, content: str) -> str:
        """Extract equation from content."""
        import re
        
        # Look for LaTeX equations
        latex_match = re.search(r'\$([^$]+)\$', content)
        if latex_match:
            return latex_match.group(1)
        
        # Look for simple equations
        equation_match = re.search(r'([a-zA-Z]\s*=\s*[^=\n]+)', content)
        if equation_match:
            return equation_match.group(1)
        
        # Return first mathematical-looking line
        lines = content.split('\n')
        for line in lines:
            if any(char in line for char in '=+-*/^()[]{}'):
                return line.strip()
        
        return "f(x) = x"  # Default equation
    
    def _extract_process_info(self, content: str) -> Dict[str, List]:
        """Extract process steps and connections from content."""
        lines = content.split('\n')
        steps = []
        connections = []
        
        # Simple extraction - look for numbered steps or bullet points
        for line in lines:
            line = line.strip()
            if re.match(r'^\d+\.', line) or line.startswith('- ') or line.startswith('* '):
                step = re.sub(r'^\d+\.\s*', '', line)
                step = re.sub(r'^[-*]\s*', '', step)
                if step:
                    steps.append(step[:50])  # Limit length
        
        # Create sequential connections
        for i in range(len(steps) - 1):
            connections.append((steps[i], steps[i + 1]))
        
        if not steps:
            steps = ["Start", "Process", "End"]
            connections = [("Start", "Process"), ("Process", "End")]
        
        return {"steps": steps, "connections": connections}
    
    def _extract_diagram_components(self, content: str) -> List[str]:
        """Extract diagram components from content."""
        # Simple extraction - look for key terms
        words = content.split()
        components = []
        
        # Look for nouns that could be components
        for word in words:
            word = word.strip('.,!?;:')
            if (len(word) > 3 and 
                word.lower() not in ['the', 'and', 'for', 'with', 'this', 'that', 'from', 'they', 'have', 'been']):
                if word not in components:
                    components.append(word)
                    if len(components) >= 6:  # Limit number of components
                        break
        
        if not components:
            components = ["Component A", "Component B", "Component C"]
        
        return components
    
    def get_available_generators(self) -> Dict[str, bool]:
        """Get status of available generators."""
        return {
            'animation_selector': True,  # Always available (rule-based fallback)
            'visual_style': visual_style_manager.initialized,
            'chart_generator': 'chart_generator' in self.available_generators,
            'blender_3d': 'blender_3d' in self.available_generators,
            'manim': 'manim' in self.available_generators,
            'motion_canvas': 'motion_canvas' in self.available_generators,
            'remotion': False,  # Not implemented yet
            'ai_models': ai_model_manager.ollama_available
        }
    
    def set_visual_style(self, style_name: str) -> bool:
        """Set the visual style for all generators."""
        return visual_style_manager.set_style(style_name)
    
    def get_available_styles(self) -> List[str]:
        """Get list of available visual styles."""
        return visual_style_manager.get_available_styles()
    
    def get_current_style_info(self) -> Dict[str, Any]:
        """Get information about the current visual style."""
        return visual_style_manager.get_current_style_info()
    
    def generate_style_preview(self, style_name: str) -> Dict[str, Any]:
        """Generate a preview of a visual style."""
        return visual_style_manager.generate_style_preview(style_name)
    
    async def create_transition_between_scenes(
        self,
        from_scene: VisualAsset,
        to_scene: VisualAsset,
        output_dir: str
    ) -> Optional[VisualAsset]:
        """Create a smooth transition between two scenes with consistent styling."""
        try:
            # Determine animation types
            from_type = self._visual_type_to_animation_type(from_scene.visual_type)
            to_type = self._visual_type_to_animation_type(to_scene.visual_type)
            
            # Get transition style
            transition_style = visual_style_manager.create_transition_style(from_type, to_type)
            
            # Create transition scene (simplified implementation)
            transition_path = Path(output_dir) / f"transition_{from_scene.scene_id}_to_{to_scene.scene_id}.mp4"
            
            # For now, create a simple fade transition using FFmpeg
            success = await self._create_fade_transition(
                from_scene.file_path,
                to_scene.file_path,
                str(transition_path),
                transition_style['duration']
            )
            
            if success:
                return VisualAsset(
                    scene_id=f"transition_{from_scene.scene_id}_to_{to_scene.scene_id}",
                    title="Scene Transition",
                    visual_type=VisualType.AUTO,
                    file_path=str(transition_path),
                    duration=transition_style['duration'],
                    generation_code="# Transition generated with consistent styling",
                    metadata={
                        'generator': 'visual_style_manager',
                        'transition_type': transition_style['transition_effect'],
                        'from_scene': from_scene.scene_id,
                        'to_scene': to_scene.scene_id
                    },
                    success=True
                )
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error creating transition: {e}")
            return None
    
    def _visual_type_to_animation_type(self, visual_type: VisualType) -> StyleAnimationType:
        """Convert VisualType to StyleAnimationType."""
        mapping = {
            VisualType.MANIM: StyleAnimationType.MATHEMATICAL,
            VisualType.MOTION_CANVAS: StyleAnimationType.CONCEPTUAL,
            VisualType.CHART: StyleAnimationType.DATA_VISUALIZATION,
            VisualType.BLENDER_3D: StyleAnimationType.SCIENTIFIC_3D,
            VisualType.REMOTION: StyleAnimationType.TITLE_SEQUENCE
        }
        return mapping.get(visual_type, StyleAnimationType.CONCEPTUAL)
    
    async def _create_fade_transition(
        self,
        from_path: str,
        to_path: str,
        output_path: str,
        duration: float
    ) -> bool:
        """Create a fade transition between two videos."""
        try:
            import subprocess
            
            cmd = [
                "ffmpeg",
                "-i", from_path,
                "-i", to_path,
                "-filter_complex",
                f"[0:v][1:v]xfade=transition=fade:duration={duration}:offset=0[v]",
                "-map", "[v]",
                "-c:v", "libx264",
                "-preset", "fast",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                "-y", output_path
            ]
            
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode == 0 and Path(output_path).exists():
                return True
            else:
                logger.error(f"Transition creation failed: {stderr.decode()}")
                return False
                
        except Exception as e:
            logger.error(f"Error creating fade transition: {e}")
            return False
    
    def get_system_recommendations(self) -> Dict[str, Any]:
        """Get system recommendations for visual content generation."""
        recommendations = ai_model_manager.get_system_recommendations()
        
        # Add animation selector recommendations
        content_type_info = animation_selector.get_content_type_info()
        recommendations['content_types'] = content_type_info
        recommendations['animation_selector'] = {
            'ai_enhanced': animation_selector.ai_analyzer_available,
            'supported_types': list(content_type_info.keys())
        }
        
        # Add 3D visualization recommendations
        if 'blender_3d' in self.available_generators:
            blender_info = blender_3d_generator.get_system_requirements()
            recommendations['3d_visualization'] = blender_info
        else:
            recommendations['3d_visualization'] = {
                'blender_available': False,
                'recommendation': 'Install Blender 3.4+ for 3D molecular and network visualizations'
            }
        
        return recommendations


# Global instance for easy access
visual_content_manager = VisualContentManager()