"""
Animation Template System for the RASO platform.

Provides safe animation templates for Manim, Motion Canvas, and Remotion
with parameter validation, constraint enforcement, and fallback mechanisms.
"""

import re
import ast
import json
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from pathlib import Path

from pydantic import BaseModel, Field, validator

from config.backend.config import get_config
from agents.logging import AgentLogger


class SafetyLevel(str, Enum):
    """Template safety levels."""
    SAFE = "safe"
    RESTRICTED = "restricted"
    UNSAFE = "unsafe"


class TemplateFramework(str, Enum):
    """Supported template frameworks."""
    MANIM = "manim"
    MOTION_CANVAS = "motion-canvas"
    REMOTION = "remotion"


class ParameterType(str, Enum):
    """Parameter data types."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    COLOR = "color"
    DURATION = "duration"


class ValidationRule(BaseModel):
    """Validation rule for template parameters."""
    
    pattern: Optional[str] = Field(default=None, description="Regex pattern for strings")
    min_value: Optional[float] = Field(default=None, description="Minimum value for numbers")
    max_value: Optional[float] = Field(default=None, description="Maximum value for numbers")
    allowed_values: Optional[List[Any]] = Field(default=None, description="Enum-like validation")
    min_length: Optional[int] = Field(default=None, description="Minimum length for strings/arrays")
    max_length: Optional[int] = Field(default=None, description="Maximum length for strings/arrays")
    
    def validate_value(self, value: Any, param_type: ParameterType) -> bool:
        """Validate a value against this rule."""
        try:
            # Type-specific validation
            if param_type == ParameterType.STRING:
                if not isinstance(value, str):
                    return False
                if self.pattern and not re.match(self.pattern, value):
                    return False
                if self.min_length and len(value) < self.min_length:
                    return False
                if self.max_length and len(value) > self.max_length:
                    return False
            
            elif param_type == ParameterType.NUMBER:
                if not isinstance(value, (int, float)):
                    return False
                if self.min_value is not None and value < self.min_value:
                    return False
                if self.max_value is not None and value > self.max_value:
                    return False
            
            elif param_type == ParameterType.BOOLEAN:
                if not isinstance(value, bool):
                    return False
            
            elif param_type == ParameterType.ARRAY:
                if not isinstance(value, list):
                    return False
                if self.min_length and len(value) < self.min_length:
                    return False
                if self.max_length and len(value) > self.max_length:
                    return False
            
            elif param_type == ParameterType.COLOR:
                if not isinstance(value, str):
                    return False
                # Validate hex color format
                if not re.match(r'^#[0-9A-Fa-f]{6}$', value):
                    return False
            
            elif param_type == ParameterType.DURATION:
                if not isinstance(value, (int, float)):
                    return False
                if value <= 0:
                    return False
            
            # Allowed values validation
            if self.allowed_values and value not in self.allowed_values:
                return False
            
            return True
            
        except Exception:
            return False


class TemplateParameter(BaseModel):
    """Template parameter definition."""
    
    name: str = Field(..., description="Parameter name")
    type: ParameterType = Field(..., description="Parameter type")
    required: bool = Field(default=True, description="Whether parameter is required")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    description: str = Field(default="", description="Parameter description")
    validation: Optional[ValidationRule] = Field(default=None, description="Validation rules")
    
    def validate_value(self, value: Any) -> bool:
        """Validate a parameter value."""
        if value is None:
            return not self.required
        
        if self.validation:
            return self.validation.validate_value(value, self.type)
        
        # Basic type validation
        if self.type == ParameterType.STRING:
            return isinstance(value, str)
        elif self.type == ParameterType.NUMBER:
            return isinstance(value, (int, float))
        elif self.type == ParameterType.BOOLEAN:
            return isinstance(value, bool)
        elif self.type == ParameterType.ARRAY:
            return isinstance(value, list)
        elif self.type == ParameterType.OBJECT:
            return isinstance(value, dict)
        elif self.type == ParameterType.COLOR:
            return isinstance(value, str) and re.match(r'^#[0-9A-Fa-f]{6}$', value)
        elif self.type == ParameterType.DURATION:
            return isinstance(value, (int, float)) and value > 0
        
        return True


class AnimationTemplate(BaseModel):
    """Animation template definition."""
    
    id: str = Field(..., description="Unique template identifier")
    name: str = Field(..., description="Human-readable template name")
    framework: TemplateFramework = Field(..., description="Animation framework")
    description: str = Field(..., description="Template description")
    parameters: List[TemplateParameter] = Field(default_factory=list, description="Template parameters")
    code_template: str = Field(..., description="Code template with placeholders")
    safety_level: SafetyLevel = Field(default=SafetyLevel.SAFE, description="Safety level")
    tags: List[str] = Field(default_factory=list, description="Template tags")
    
    # Metadata
    author: str = Field(default="RASO", description="Template author")
    version: str = Field(default="1.0.0", description="Template version")
    created_at: Optional[str] = Field(default=None, description="Creation timestamp")
    
    def validate_parameters(self, params: Dict[str, Any]) -> Dict[str, List[str]]:
        """
        Validate parameters against template definition.
        
        Args:
            params: Parameters to validate
            
        Returns:
            Dictionary of validation errors by parameter name
        """
        errors = {}
        
        # Check required parameters
        for param_def in self.parameters:
            if param_def.required and param_def.name not in params:
                errors[param_def.name] = [f"Required parameter '{param_def.name}' is missing"]
        
        # Validate provided parameters
        for param_name, param_value in params.items():
            param_def = next((p for p in self.parameters if p.name == param_name), None)
            
            if not param_def:
                errors[param_name] = [f"Unknown parameter '{param_name}'"]
                continue
            
            if not param_def.validate_value(param_value):
                errors[param_name] = [f"Invalid value for parameter '{param_name}'"]
        
        return errors
    
    def generate_code(self, params: Dict[str, Any]) -> str:
        """
        Generate code from template with parameters.
        
        Args:
            params: Template parameters
            
        Returns:
            Generated code
        """
        # Validate parameters first
        validation_errors = self.validate_parameters(params)
        if validation_errors:
            error_msg = "; ".join([
                f"{param}: {', '.join(errors)}" 
                for param, errors in validation_errors.items()
            ])
            raise ValueError(f"Parameter validation failed: {error_msg}")
        
        # Add default values for missing optional parameters
        final_params = {}
        for param_def in self.parameters:
            if param_def.name in params:
                final_params[param_def.name] = params[param_def.name]
            elif param_def.default_value is not None:
                final_params[param_def.name] = param_def.default_value
        
        # Generate code by replacing placeholders
        code = self.code_template
        for param_name, param_value in final_params.items():
            placeholder = f"{{{param_name}}}"
            
            # Handle different value types
            if isinstance(param_value, str):
                replacement = f'"{param_value}"'
            elif isinstance(param_value, (list, dict)):
                replacement = json.dumps(param_value)
            else:
                replacement = str(param_value)
            
            code = code.replace(placeholder, replacement)
        
        return code
    
    def is_safe_for_execution(self) -> bool:
        """Check if template is safe for execution."""
        return self.safety_level == SafetyLevel.SAFE


class TemplateRegistry:
    """Registry for managing animation templates."""
    
    def __init__(self):
        """Initialize template registry."""
        self.templates: Dict[str, AnimationTemplate] = {}
        self.logger = AgentLogger(None)
        self._load_builtin_templates()
    
    def register_template(self, template: AnimationTemplate) -> None:
        """
        Register a new template.
        
        Args:
            template: Template to register
        """
        if template.id in self.templates:
            self.logger.warning(f"Template {template.id} already exists, overwriting")
        
        self.templates[template.id] = template
        self.logger.info(f"Registered template: {template.id}")
    
    def get_template(self, template_id: str) -> Optional[AnimationTemplate]:
        """
        Get template by ID.
        
        Args:
            template_id: Template identifier
            
        Returns:
            Template if found, None otherwise
        """
        return self.templates.get(template_id)
    
    def list_templates(
        self, 
        framework: Optional[TemplateFramework] = None,
        safety_level: Optional[SafetyLevel] = None,
        tags: Optional[List[str]] = None,
    ) -> List[AnimationTemplate]:
        """
        List templates with optional filtering.
        
        Args:
            framework: Filter by framework
            safety_level: Filter by safety level
            tags: Filter by tags
            
        Returns:
            List of matching templates
        """
        templates = list(self.templates.values())
        
        if framework:
            templates = [t for t in templates if t.framework == framework]
        
        if safety_level:
            templates = [t for t in templates if t.safety_level == safety_level]
        
        if tags:
            templates = [t for t in templates if any(tag in t.tags for tag in tags)]
        
        return templates
    
    def validate_template_code(self, template: AnimationTemplate) -> List[str]:
        """
        Validate template code for safety.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        code = template.code_template
        
        # Check for dangerous patterns
        dangerous_patterns = [
            r'import\s+os',
            r'import\s+sys',
            r'import\s+subprocess',
            r'exec\s*\(',
            r'eval\s*\(',
            r'__import__',
            r'open\s*\(',
            r'file\s*\(',
            r'input\s*\(',
            r'raw_input\s*\(',
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, code, re.IGNORECASE):
                errors.append(f"Dangerous pattern detected: {pattern}")
        
        # Try to parse as Python (basic syntax check)
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append(f"Syntax error: {str(e)}")
        
        return errors
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates."""
        # Manim templates
        self._register_manim_templates()
        
        # Motion Canvas templates
        self._register_motion_canvas_templates()
        
        # Remotion templates
        self._register_remotion_templates()
    
    def _register_manim_templates(self) -> None:
        """Register built-in Manim templates."""
        
        # Simple equation template
        simple_equation = AnimationTemplate(
            id="manim_simple_equation",
            name="Simple Equation Animation",
            framework=TemplateFramework.MANIM,
            description="Animate a simple mathematical equation",
            parameters=[
                TemplateParameter(
                    name="equation",
                    type=ParameterType.STRING,
                    required=True,
                    description="LaTeX equation string",
                    validation=ValidationRule(min_length=1, max_length=200),
                ),
                TemplateParameter(
                    name="duration",
                    type=ParameterType.DURATION,
                    required=False,
                    default_value=3.0,
                    description="Animation duration in seconds",
                    validation=ValidationRule(min_value=1.0, max_value=30.0),
                ),
                TemplateParameter(
                    name="color",
                    type=ParameterType.COLOR,
                    required=False,
                    default_value="#FFFFFF",
                    description="Equation color",
                ),
            ],
            code_template="""
from manim import *

class EquationScene(Scene):
    def construct(self):
        equation = MathTex({equation})
        equation.set_color({color})
        
        self.play(Write(equation), run_time={duration})
        self.wait(1)
""",
            safety_level=SafetyLevel.SAFE,
            tags=["equation", "basic", "math"],
        )
        
        # Complex derivation template
        complex_derivation = AnimationTemplate(
            id="manim_complex_derivation",
            name="Complex Mathematical Derivation",
            framework=TemplateFramework.MANIM,
            description="Step-by-step mathematical derivation",
            parameters=[
                TemplateParameter(
                    name="steps",
                    type=ParameterType.ARRAY,
                    required=True,
                    description="List of derivation steps",
                    validation=ValidationRule(min_length=2, max_length=10),
                ),
                TemplateParameter(
                    name="step_duration",
                    type=ParameterType.DURATION,
                    required=False,
                    default_value=2.0,
                    description="Duration per step",
                ),
            ],
            code_template="""
from manim import *

class DerivationScene(Scene):
    def construct(self):
        steps = {steps}
        step_duration = {step_duration}
        
        equations = [MathTex(step) for step in steps]
        
        # Position equations
        for i, eq in enumerate(equations):
            eq.shift(UP * (2 - i * 0.8))
        
        # Animate each step
        for i, eq in enumerate(equations):
            if i == 0:
                self.play(Write(eq), run_time=step_duration)
            else:
                self.play(
                    Transform(equations[i-1].copy(), eq),
                    run_time=step_duration
                )
            self.wait(0.5)
""",
            safety_level=SafetyLevel.SAFE,
            tags=["derivation", "steps", "math", "complex"],
        )
        
        self.register_template(simple_equation)
        self.register_template(complex_derivation)
    
    def _register_motion_canvas_templates(self) -> None:
        """Register built-in Motion Canvas templates."""
        
        # Simple diagram template
        simple_diagram = AnimationTemplate(
            id="motion_canvas_simple_diagram",
            name="Simple Concept Diagram",
            framework=TemplateFramework.MOTION_CANVAS,
            description="Create a simple conceptual diagram",
            parameters=[
                TemplateParameter(
                    name="title",
                    type=ParameterType.STRING,
                    required=True,
                    description="Diagram title",
                    validation=ValidationRule(min_length=1, max_length=100),
                ),
                TemplateParameter(
                    name="elements",
                    type=ParameterType.ARRAY,
                    required=True,
                    description="Diagram elements",
                    validation=ValidationRule(min_length=1, max_length=10),
                ),
                TemplateParameter(
                    name="duration",
                    type=ParameterType.DURATION,
                    required=False,
                    default_value=4.0,
                    description="Animation duration",
                ),
            ],
            code_template="""
import {makeScene2D} from '@motion-canvas/2d';
import {createRef, waitFor} from '@motion-canvas/core';
import {Txt, Rect, Line} from '@motion-canvas/2d/lib/components';

export default makeScene2D(function* (view) {
    const title = createRef<Txt>();
    const elements = {elements};
    const duration = {duration};
    
    view.add(
        <Txt
            ref={title}
            text={{title}}
            fontSize={48}
            fill={'#ffffff'}
            y={-200}
        />
    );
    
    yield* title().opacity(1, duration / 4);
    
    // Animate elements
    for (let i = 0; i < elements.length; i++) {
        const element = (
            <Rect
                width={200}
                height={100}
                fill={'#3b82f6'}
                x={-300 + i * 150}
                y={0}
            >
                <Txt text={elements[i]} fontSize={24} fill={'#ffffff'} />
            </Rect>
        );
        
        view.add(element);
        yield* element.opacity(1, duration / elements.length);
    }
    
    yield* waitFor(1);
});
""",
            safety_level=SafetyLevel.SAFE,
            tags=["diagram", "concept", "basic"],
        )
        
        self.register_template(simple_diagram)
    
    def _register_remotion_templates(self) -> None:
        """Register built-in Remotion templates."""
        
        # Title sequence template
        title_sequence = AnimationTemplate(
            id="remotion_title_sequence",
            name="Title Sequence",
            framework=TemplateFramework.REMOTION,
            description="Animated title sequence with subtitle",
            parameters=[
                TemplateParameter(
                    name="title",
                    type=ParameterType.STRING,
                    required=True,
                    description="Main title text",
                    validation=ValidationRule(min_length=1, max_length=100),
                ),
                TemplateParameter(
                    name="subtitle",
                    type=ParameterType.STRING,
                    required=False,
                    default_value="",
                    description="Subtitle text",
                ),
                TemplateParameter(
                    name="duration",
                    type=ParameterType.DURATION,
                    required=False,
                    default_value=3.0,
                    description="Animation duration",
                ),
                TemplateParameter(
                    name="background_color",
                    type=ParameterType.COLOR,
                    required=False,
                    default_value="#1e293b",
                    description="Background color",
                ),
            ],
            code_template="""
import React from 'react';
import {
    AbsoluteFill,
    interpolate,
    spring,
    useCurrentFrame,
    useVideoConfig,
} from 'remotion';

export const TitleSequence: React.FC = () => {
    const frame = useCurrentFrame();
    const {fps} = useVideoConfig();
    
    const title = {title};
    const subtitle = {subtitle};
    const duration = {duration};
    const backgroundColor = {background_color};
    
    const titleProgress = spring({
        fps,
        frame,
        config: {
            damping: 200,
        },
    });
    
    const subtitleProgress = spring({
        fps,
        frame: frame - 20,
        config: {
            damping: 200,
        },
    });
    
    const titleOpacity = interpolate(titleProgress, [0, 1], [0, 1]);
    const titleY = interpolate(titleProgress, [0, 1], [50, 0]);
    
    const subtitleOpacity = interpolate(subtitleProgress, [0, 1], [0, 1]);
    const subtitleY = interpolate(subtitleProgress, [0, 1], [30, 0]);
    
    return (
        <AbsoluteFill style={{backgroundColor}}>
            <div
                style={{
                    display: 'flex',
                    flexDirection: 'column',
                    justifyContent: 'center',
                    alignItems: 'center',
                    height: '100%',
                    fontFamily: 'Inter, sans-serif',
                }}
            >
                <h1
                    style={{
                        fontSize: '4rem',
                        fontWeight: 'bold',
                        color: '#ffffff',
                        margin: 0,
                        opacity: titleOpacity,
                        transform: `translateY(${{titleY}}px)`,
                    }}
                >
                    {title}
                </h1>
                {subtitle && (
                    <h2
                        style={{
                            fontSize: '2rem',
                            color: '#94a3b8',
                            margin: '1rem 0 0 0',
                            opacity: subtitleOpacity,
                            transform: `translateY(${{subtitleY}}px)`,
                        }}
                    >
                        {subtitle}
                    </h2>
                )}
            </div>
        </AbsoluteFill>
    );
};
""",
            safety_level=SafetyLevel.SAFE,
            tags=["title", "intro", "text"],
        )
        
        self.register_template(title_sequence)


class TemplateEngine:
    """Engine for template processing and code generation."""
    
    def __init__(self):
        """Initialize template engine."""
        self.registry = TemplateRegistry()
        self.config = get_config()
        self.logger = AgentLogger(None)
    
    def generate_animation_code(
        self,
        template_id: str,
        parameters: Dict[str, Any],
        validate_safety: bool = True,
    ) -> str:
        """
        Generate animation code from template.
        
        Args:
            template_id: Template identifier
            parameters: Template parameters
            validate_safety: Whether to validate safety
            
        Returns:
            Generated code
            
        Raises:
            ValueError: If template not found or validation fails
        """
        template = self.registry.get_template(template_id)
        if not template:
            raise ValueError(f"Template not found: {template_id}")
        
        # Safety validation
        if validate_safety and not template.is_safe_for_execution():
            raise ValueError(f"Template {template_id} is not safe for execution")
        
        # Generate code
        try:
            code = template.generate_code(parameters)
            
            self.logger.info(
                f"Generated code from template {template_id}",
                template_id=template_id,
                framework=template.framework.value,
                safety_level=template.safety_level.value,
            )
            
            return code
            
        except Exception as e:
            self.logger.error(f"Code generation failed: {str(e)}")
            raise
    
    def validate_template_syntax(self, template_id: str) -> List[str]:
        """
        Validate template syntax and safety.
        
        Args:
            template_id: Template identifier
            
        Returns:
            List of validation errors
        """
        template = self.registry.get_template(template_id)
        if not template:
            return [f"Template not found: {template_id}"]
        
        return self.registry.validate_template_code(template)
    
    def get_fallback_template(self, framework: TemplateFramework) -> Optional[str]:
        """
        Get fallback template for framework.
        
        Args:
            framework: Animation framework
            
        Returns:
            Fallback template ID if available
        """
        safe_templates = self.registry.list_templates(
            framework=framework,
            safety_level=SafetyLevel.SAFE,
        )
        
        if safe_templates:
            # Return simplest template (by tag priority)
            basic_templates = [t for t in safe_templates if "basic" in t.tags]
            if basic_templates:
                return basic_templates[0].id
            
            return safe_templates[0].id
        
        return None
    
    def create_safe_parameters(
        self,
        template_id: str,
        user_parameters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Create safe parameters by sanitizing user input.
        
        Args:
            template_id: Template identifier
            user_parameters: User-provided parameters
            
        Returns:
            Sanitized parameters
        """
        template = self.registry.get_template(template_id)
        if not template:
            return {}
        
        safe_params = {}
        
        for param_def in template.parameters:
            param_name = param_def.name
            
            if param_name in user_parameters:
                value = user_parameters[param_name]
                
                # Sanitize based on type
                if param_def.type == ParameterType.STRING:
                    # Remove potentially dangerous characters
                    value = re.sub(r'[<>"\';]', '', str(value))
                    value = value[:param_def.validation.max_length if param_def.validation and param_def.validation.max_length else 1000]
                
                elif param_def.type == ParameterType.NUMBER:
                    try:
                        value = float(value)
                        if param_def.validation:
                            if param_def.validation.min_value is not None:
                                value = max(value, param_def.validation.min_value)
                            if param_def.validation.max_value is not None:
                                value = min(value, param_def.validation.max_value)
                    except (ValueError, TypeError):
                        value = param_def.default_value
                
                # Validate sanitized value
                if param_def.validate_value(value):
                    safe_params[param_name] = value
                elif param_def.default_value is not None:
                    safe_params[param_name] = param_def.default_value
            
            elif param_def.default_value is not None:
                safe_params[param_name] = param_def.default_value
        
        return safe_params


# Global template engine instance
template_engine = TemplateEngine()