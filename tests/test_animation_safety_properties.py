"""
Property-based tests for RASO animation template safety and validation.

**Feature: raso-platform, Property 6: Animation safety and validation**
Tests that animation code uses only safe templates, validates syntax before execution,
and implements retry mechanisms with fallback templates on failure.
"""

import re
import json
from typing import Any, Dict, List
from unittest.mock import patch

import pytest
from hypothesis import given, strategies as st

from animation.templates import (
    TemplateEngine,
    TemplateRegistry,
    AnimationTemplate,
    TemplateParameter,
    ValidationRule,
    SafetyLevel,
    TemplateFramework,
    ParameterType,
)


class TestAnimationSafetyProperties:
    """Property-based tests for animation template safety."""

    @given(
        template_id=st.text(min_size=5, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789_"),
        framework=st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
        safety_level=st.sampled_from([SafetyLevel.SAFE, SafetyLevel.RESTRICTED, SafetyLevel.UNSAFE]),
    )
    def test_safe_template_validation_property(
        self, template_id: str, framework: TemplateFramework, safety_level: SafetyLevel
    ):
        """
        **Property 6: Animation safety and validation**
        For any template with safe safety level, the system should use only
        safe templates and validate syntax before execution.
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        engine = TemplateEngine()
        
        # Create a safe template
        safe_code = """
# Safe animation code
def create_animation():
    return "safe animation"
"""
        
        template = AnimationTemplate(
            id=template_id,
            name="Test Template",
            framework=framework,
            description="Test template for safety validation",
            parameters=[
                TemplateParameter(
                    name="duration",
                    type=ParameterType.DURATION,
                    required=False,
                    default_value=3.0,
                )
            ],
            code_template=safe_code,
            safety_level=safety_level,
        )
        
        # Register template
        engine.registry.register_template(template)
        
        # Test safety validation
        if safety_level == SafetyLevel.SAFE:
            # Should be safe for execution
            assert template.is_safe_for_execution() is True
            
            # Should be able to generate code
            try:
                code = engine.generate_animation_code(
                    template_id=template_id,
                    parameters={"duration": 5.0},
                    validate_safety=True,
                )
                assert code is not None
                assert len(code) > 0
            except ValueError:
                pytest.fail("Safe template should not raise ValueError")
        
        else:
            # Should not be safe for execution
            assert template.is_safe_for_execution() is False
            
            # Should raise error when safety validation enabled
            with pytest.raises(ValueError, match="not safe for execution"):
                engine.generate_animation_code(
                    template_id=template_id,
                    parameters={"duration": 5.0},
                    validate_safety=True,
                )

    @given(
        dangerous_patterns=st.lists(
            st.sampled_from([
                "import os",
                "import sys", 
                "import subprocess",
                "exec(",
                "eval(",
                "__import__",
                "open(",
                "file(",
                "input(",
            ]),
            min_size=1,
            max_size=3
        ),
        template_id=st.text(min_size=5, max_size=30),
    )
    def test_dangerous_code_detection_property(
        self, dangerous_patterns: List[str], template_id: str
    ):
        """
        **Property 6: Animation safety and validation**
        For any template containing dangerous code patterns, the validation
        should detect and reject unsafe templates.
        **Validates: Requirements 5.1, 5.3**
        """
        registry = TemplateRegistry()
        
        # Create template with dangerous code
        dangerous_code = f"""
# Dangerous animation code
{dangerous_patterns[0]}
def create_animation():
    {dangerous_patterns[-1] if len(dangerous_patterns) > 1 else "pass"}
    return "animation"
"""
        
        template = AnimationTemplate(
            id=template_id,
            name="Dangerous Template",
            framework=TemplateFramework.MANIM,
            description="Template with dangerous code",
            parameters=[],
            code_template=dangerous_code,
            safety_level=SafetyLevel.UNSAFE,
        )
        
        # Test validation
        validation_errors = registry.validate_template_code(template)
        
        # Should detect dangerous patterns
        assert len(validation_errors) > 0
        
        # Should identify specific dangerous patterns
        error_text = " ".join(validation_errors).lower()
        assert any(pattern.lower() in error_text for pattern in dangerous_patterns)

    @given(
        param_name=st.text(min_size=1, max_size=20, alphabet="abcdefghijklmnopqrstuvwxyz_"),
        param_type=st.sampled_from([ParameterType.STRING, ParameterType.NUMBER, ParameterType.BOOLEAN]),
        required=st.booleans(),
        test_values=st.lists(st.one_of(st.text(), st.integers(), st.floats(), st.booleans()), min_size=1, max_size=5),
    )
    def test_parameter_validation_property(
        self, param_name: str, param_type: ParameterType, required: bool, test_values: List[Any]
    ):
        """
        **Property 6: Animation safety and validation**
        For any template parameter definition, the validation should correctly
        enforce type constraints and required field validation.
        **Validates: Requirements 5.2, 5.3**
        """
        # Create parameter with validation rules
        validation_rule = None
        if param_type == ParameterType.STRING:
            validation_rule = ValidationRule(min_length=1, max_length=100)
        elif param_type == ParameterType.NUMBER:
            validation_rule = ValidationRule(min_value=0.0, max_value=1000.0)
        
        param = TemplateParameter(
            name=param_name,
            type=param_type,
            required=required,
            validation=validation_rule,
        )
        
        # Test validation for each value
        for value in test_values:
            is_valid = param.validate_value(value)
            
            # Check type compatibility
            if param_type == ParameterType.STRING:
                expected_valid = isinstance(value, str)
                if expected_valid and validation_rule:
                    expected_valid = (
                        len(value) >= validation_rule.min_length and
                        len(value) <= validation_rule.max_length
                    )
            elif param_type == ParameterType.NUMBER:
                expected_valid = isinstance(value, (int, float))
                if expected_valid and validation_rule:
                    expected_valid = (
                        value >= validation_rule.min_value and
                        value <= validation_rule.max_value
                    )
            elif param_type == ParameterType.BOOLEAN:
                expected_valid = isinstance(value, bool)
            else:
                expected_valid = True
            
            assert is_valid == expected_valid

    @given(
        template_params=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(st.text(), st.integers(), st.floats()),
            min_size=1,
            max_size=5,
        ),
        missing_required=st.booleans(),
    )
    def test_template_parameter_validation_property(
        self, template_params: Dict[str, Any], missing_required: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any set of template parameters, the validation should enforce
        parameter constraints and identify missing required parameters.
        **Validates: Requirements 5.2**
        """
        # Create template with parameter definitions
        param_definitions = []
        for param_name, param_value in template_params.items():
            if isinstance(param_value, str):
                param_type = ParameterType.STRING
            elif isinstance(param_value, (int, float)):
                param_type = ParameterType.NUMBER
            else:
                param_type = ParameterType.STRING
            
            param_definitions.append(TemplateParameter(
                name=param_name,
                type=param_type,
                required=True,  # Make all required for this test
            ))
        
        template = AnimationTemplate(
            id="test_template",
            name="Test Template",
            framework=TemplateFramework.MANIM,
            description="Test template",
            parameters=param_definitions,
            code_template="# Test code",
            safety_level=SafetyLevel.SAFE,
        )
        
        # Test with complete parameters
        validation_errors = template.validate_parameters(template_params)
        
        if not missing_required:
            # Should have no errors with all required params
            assert len(validation_errors) == 0
        
        # Test with missing required parameter
        if missing_required and template_params:
            # Remove one required parameter
            incomplete_params = dict(template_params)
            removed_param = list(incomplete_params.keys())[0]
            del incomplete_params[removed_param]
            
            validation_errors = template.validate_parameters(incomplete_params)
            
            # Should have error for missing required parameter
            assert len(validation_errors) > 0
            assert removed_param in validation_errors
            assert "missing" in validation_errors[removed_param][0].lower()

    @given(
        framework=st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
        user_params=st.dictionaries(
            keys=st.text(min_size=1, max_size=20),
            values=st.one_of(
                st.text(min_size=0, max_size=1000),  # Including potentially long strings
                st.integers(),
                st.floats(),
            ),
            min_size=0,
            max_size=10,
        ),
    )
    def test_parameter_sanitization_property(
        self, framework: TemplateFramework, user_params: Dict[str, Any]
    ):
        """
        **Property 6: Animation safety and validation**
        For any user-provided parameters, the system should sanitize input
        to prevent injection attacks and enforce safety constraints.
        **Validates: Requirements 5.1, 5.2**
        """
        engine = TemplateEngine()
        
        # Get a safe template for the framework
        safe_templates = engine.registry.list_templates(
            framework=framework,
            safety_level=SafetyLevel.SAFE,
        )
        
        if not safe_templates:
            pytest.skip(f"No safe templates available for {framework}")
        
        template_id = safe_templates[0].id
        
        # Test parameter sanitization
        safe_params = engine.create_safe_parameters(template_id, user_params)
        
        # Verify sanitization
        for param_name, param_value in safe_params.items():
            if isinstance(param_value, str):
                # Should not contain dangerous characters
                dangerous_chars = ['<', '>', '"', "'", ';']
                assert not any(char in param_value for char in dangerous_chars)
                
                # Should have reasonable length limit
                assert len(param_value) <= 1000
            
            elif isinstance(param_value, (int, float)):
                # Should be within reasonable bounds
                assert -1000000 <= param_value <= 1000000

    @given(
        framework=st.sampled_from([TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]),
        simulate_failure=st.booleans(),
    )
    def test_fallback_template_mechanism_property(
        self, framework: TemplateFramework, simulate_failure: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any framework, the system should provide fallback templates
        when primary templates fail, ensuring animation generation continues.
        **Validates: Requirements 5.4**
        """
        engine = TemplateEngine()
        
        # Test fallback mechanism
        fallback_template_id = engine.get_fallback_template(framework)
        
        # Should always have a fallback for supported frameworks
        assert fallback_template_id is not None
        
        # Fallback template should be safe
        fallback_template = engine.registry.get_template(fallback_template_id)
        assert fallback_template is not None
        assert fallback_template.framework == framework
        assert fallback_template.safety_level == SafetyLevel.SAFE
        
        # Should be able to generate code with fallback
        try:
            code = engine.generate_animation_code(
                template_id=fallback_template_id,
                parameters={},  # Use defaults
                validate_safety=True,
            )
            assert code is not None
            assert len(code) > 0
        except Exception as e:
            pytest.fail(f"Fallback template should not fail: {str(e)}")

    @given(
        code_template=st.text(min_size=10, max_size=500),
        has_syntax_error=st.booleans(),
    )
    def test_syntax_validation_property(
        self, code_template: str, has_syntax_error: bool
    ):
        """
        **Property 6: Animation safety and validation**
        For any code template, the syntax validation should correctly
        identify syntax errors and prevent execution of invalid code.
        **Validates: Requirements 5.3**
        """
        registry = TemplateRegistry()
        
        # Modify code to introduce syntax error if requested
        if has_syntax_error:
            # Add invalid Python syntax
            code_template += "\ndef invalid_function(\n    # Missing closing parenthesis"
        else:
            # Ensure valid Python syntax
            code_template = """
def valid_function():
    return "valid code"
"""
        
        template = AnimationTemplate(
            id="syntax_test",
            name="Syntax Test Template",
            framework=TemplateFramework.MANIM,
            description="Template for syntax testing",
            parameters=[],
            code_template=code_template,
            safety_level=SafetyLevel.SAFE,
        )
        
        # Test syntax validation
        validation_errors = registry.validate_template_code(template)
        
        if has_syntax_error:
            # Should detect syntax errors
            assert len(validation_errors) > 0
            assert any("syntax" in error.lower() for error in validation_errors)
        else:
            # Should not have syntax errors (may have other validation issues)
            syntax_errors = [error for error in validation_errors if "syntax" in error.lower()]
            assert len(syntax_errors) == 0

    def test_builtin_templates_safety_property(self):
        """
        **Property 6: Animation safety and validation**
        All built-in templates should be safe for execution and pass
        validation checks to ensure system reliability.
        **Validates: Requirements 5.1, 5.2, 5.3**
        """
        registry = TemplateRegistry()
        
        # Get all built-in templates
        all_templates = registry.list_templates()
        
        # Should have templates for each framework
        frameworks = [TemplateFramework.MANIM, TemplateFramework.MOTION_CANVAS, TemplateFramework.REMOTION]
        for framework in frameworks:
            framework_templates = [t for t in all_templates if t.framework == framework]
            assert len(framework_templates) > 0, f"No templates found for {framework}"
        
        # Test each built-in template
        for template in all_templates:
            # Should be safe by default
            assert template.safety_level == SafetyLevel.SAFE
            assert template.is_safe_for_execution() is True
            
            # Should pass validation
            validation_errors = registry.validate_template_code(template)
            assert len(validation_errors) == 0, f"Template {template.id} has validation errors: {validation_errors}"
            
            # Should have valid parameters
            for param in template.parameters:
                assert param.name is not None
                assert len(param.name) > 0
                assert param.type in ParameterType
            
            # Should be able to generate code with defaults
            try:
                default_params = {}
                for param in template.parameters:
                    if param.default_value is not None:
                        default_params[param.name] = param.default_value
                    elif not param.required:
                        continue
                    else:
                        # Provide minimal valid value for required params
                        if param.type == ParameterType.STRING:
                            default_params[param.name] = "test"
                        elif param.type == ParameterType.NUMBER:
                            default_params[param.name] = 1.0
                        elif param.type == ParameterType.DURATION:
                            default_params[param.name] = 3.0
                        elif param.type == ParameterType.BOOLEAN:
                            default_params[param.name] = True
                        elif param.type == ParameterType.ARRAY:
                            default_params[param.name] = ["test"]
                        elif param.type == ParameterType.COLOR:
                            default_params[param.name] = "#FFFFFF"
                
                code = template.generate_code(default_params)
                assert code is not None
                assert len(code) > 0
                
            except Exception as e:
                pytest.fail(f"Built-in template {template.id} should generate valid code: {str(e)}")


if __name__ == "__main__":
    pytest.main([__file__])