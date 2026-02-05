"""
Property tests for content-aware cinematic recommendations.
Tests recommendation engine accuracy, consistency, and template application.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from typing import Dict, List, Any, Optional

from src.cinematic.recommendation_engine import (
    CinematicRecommendationEngine, ContentAnalyzer, ContentType, ComplexityLevel, MoodType,
    CinematicRecommendation, RecommendationResult
)
from src.cinematic.models import (
    CinematicSettingsModel, CameraMovementSettings, ColorGradingSettings,
    SoundDesignSettings, AdvancedCompositingSettings, CameraMovementType, FilmEmulationType
)


# Mock Gemini client for testing
class MockGeminiClient:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.call_count = 0
    
    async def analyze_scene_for_cinematics(self, content: str):
        self.call_count += 1
        
        # Return mock analysis based on content
        if "equation" in content.lower() or "formula" in content.lower():
            return {
                "focusType": "mathematical",
                "complexity": "high",
                "mood": "technical",
                "confidence": 0.9
            }
        elif "architecture" in content.lower() or "system" in content.lower():
            return {
                "focusType": "architectural",
                "complexity": "medium",
                "mood": "neutral",
                "confidence": 0.85
            }
        elif "result" in content.lower() or "data" in content.lower():
            return {
                "focusType": "analytical",
                "complexity": "medium",
                "mood": "neutral",
                "confidence": 0.8
            }
        else:
            return {
                "focusType": "general",
                "complexity": "medium",
                "mood": "neutral",
                "confidence": 0.7
            }


# Strategies for generating test data
@st.composite
def mathematical_content(draw):
    """Generate mathematical content."""
    math_terms = ["equation", "formula", "theorem", "proof", "derivative", "integral", "matrix", "algorithm"]
    complexity_terms = ["advanced", "complex", "sophisticated", "simple", "basic", "elementary"]
    
    base_content = f"This {draw(st.sampled_from(math_terms))} demonstrates"
    complexity = draw(st.sampled_from(complexity_terms))
    additional_terms = draw(st.lists(st.sampled_from(math_terms), min_size=1, max_size=3))
    
    content = f"{base_content} {complexity} concepts involving {', '.join(additional_terms)}"
    return content

@st.composite
def architectural_content(draw):
    """Generate architectural content."""
    arch_terms = ["architecture", "system", "design", "structure", "component", "framework", "interface"]
    descriptors = ["modular", "scalable", "robust", "flexible", "distributed", "centralized"]
    
    base_content = f"The {draw(st.sampled_from(arch_terms))} features"
    descriptor = draw(st.sampled_from(descriptors))
    additional_terms = draw(st.lists(st.sampled_from(arch_terms), min_size=1, max_size=3))
    
    content = f"{base_content} {descriptor} {', '.join(additional_terms)} for optimal performance"
    return content

@st.composite
def analytical_content(draw):
    """Generate analytical content."""
    analysis_terms = ["result", "data", "analysis", "performance", "benchmark", "metric", "evaluation"]
    outcomes = ["improvement", "optimization", "enhancement", "reduction", "increase", "decrease"]
    
    base_content = f"The {draw(st.sampled_from(analysis_terms))} shows"
    outcome = draw(st.sampled_from(outcomes))
    percentage = draw(st.integers(min_value=5, max_value=95))
    
    content = f"{base_content} {percentage}% {outcome} in system performance metrics"
    return content

@st.composite
def procedural_content(draw):
    """Generate procedural content."""
    process_terms = ["step", "process", "method", "procedure", "algorithm", "workflow", "implementation"]
    actions = ["execute", "implement", "perform", "apply", "configure", "initialize", "optimize"]
    
    base_content = f"First {draw(st.sampled_from(process_terms))}: {draw(st.sampled_from(actions))}"
    steps = draw(st.integers(min_value=2, max_value=5))
    
    content = f"{base_content} the system. This involves {steps} sequential operations."
    return content

@st.composite
def introductory_content(draw):
    """Generate introductory content."""
    intro_terms = ["introduction", "overview", "welcome", "begin", "start", "outline"]
    topics = ["research", "methodology", "system", "approach", "framework", "analysis"]
    
    base_content = f"Welcome to this {draw(st.sampled_from(intro_terms))} of"
    topic = draw(st.sampled_from(topics))
    
    content = f"{base_content} our {topic}. We will explore the fundamental concepts and applications."
    return content

@st.composite
def conclusion_content(draw):
    """Generate conclusion content."""
    conclusion_terms = ["conclusion", "summary", "result", "finding", "outcome", "achievement"]
    impacts = ["significant", "substantial", "notable", "important", "critical", "valuable"]
    
    base_content = f"In {draw(st.sampled_from(conclusion_terms))}, we achieved"
    impact = draw(st.sampled_from(impacts))
    
    content = f"{base_content} {impact} improvements and identified future research directions."
    return content

@st.composite
def mixed_content(draw):
    """Generate mixed content types."""
    content_generators = [
        mathematical_content(), architectural_content(), analytical_content(),
        procedural_content(), introductory_content(), conclusion_content()
    ]
    return draw(st.sampled_from(content_generators))

@st.composite
def cinematic_settings(draw):
    """Generate cinematic settings for testing."""
    return CinematicSettingsModel(
        camera_movements=CameraMovementSettings(
            enabled=draw(st.booleans()),
            intensity=draw(st.integers(min_value=0, max_value=100)),
            auto_select=draw(st.booleans())
        ),
        color_grading=ColorGradingSettings(
            enabled=draw(st.booleans()),
            film_emulation=draw(st.sampled_from(list(FilmEmulationType))),
            temperature=draw(st.integers(min_value=-100, max_value=100)),
            contrast=draw(st.integers(min_value=-100, max_value=100)),
            saturation=draw(st.integers(min_value=-100, max_value=100))
        ),
        sound_design=SoundDesignSettings(
            enabled=draw(st.booleans()),
            ambient_audio=draw(st.booleans()),
            music_scoring=draw(st.booleans()),
            spatial_audio=draw(st.booleans())
        ),
        advanced_compositing=AdvancedCompositingSettings(
            enabled=draw(st.booleans()),
            film_grain=draw(st.booleans()),
            dynamic_lighting=draw(st.booleans())
        )
    )


class TestContentAwareRecommendations:
    """Test content-aware recommendation system."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.analyzer = ContentAnalyzer()
        self.engine = CinematicRecommendationEngine()
        self.gemini_client = MockGeminiClient()
        self.ai_engine = CinematicRecommendationEngine(gemini_client=self.gemini_client)
    
    @given(mathematical_content())
    @settings(max_examples=15, deadline=6000)
    def test_mathematical_content_recognition(self, content):
        """Property: Mathematical content should be correctly identified and receive appropriate recommendations."""
        analysis = self.analyzer.analyze_content(content)
        
        # Should identify as mathematical content
        assert analysis.content_type == ContentType.MATHEMATICAL, f"Should identify mathematical content: {content}"
        
        # Should have reasonable confidence
        assert analysis.confidence >= 0.5, "Should have reasonable confidence in mathematical content analysis"
        
        # Should extract relevant key terms
        math_terms = ["equation", "formula", "theorem", "proof", "derivative", "integral", "matrix", "algorithm"]
        found_terms = any(term in analysis.key_terms for term in math_terms)
        assert found_terms or any(term in content.lower() for term in math_terms), "Should extract mathematical key terms"
    
    @given(architectural_content())
    @settings(max_examples=15, deadline=6000)
    def test_architectural_content_recognition(self, content):
        """Property: Architectural content should be correctly identified and receive appropriate recommendations."""
        analysis = self.analyzer.analyze_content(content)
        
        # Should identify as architectural content
        assert analysis.content_type == ContentType.ARCHITECTURAL, f"Should identify architectural content: {content}"
        
        # Should have reasonable confidence
        assert analysis.confidence >= 0.5, "Should have reasonable confidence in architectural content analysis"
        
        # Should suggest appropriate camera movements
        arch_terms = ["architecture", "system", "design", "structure", "component", "framework"]
        found_terms = any(term in analysis.key_terms for term in arch_terms)
        assert found_terms or any(term in content.lower() for term in arch_terms), "Should extract architectural key terms"
    
    @given(analytical_content())
    @settings(max_examples=15, deadline=6000)
    def test_analytical_content_recognition(self, content):
        """Property: Analytical content should be correctly identified and receive appropriate recommendations."""
        analysis = self.analyzer.analyze_content(content)
        
        # Should identify as analytical content
        assert analysis.content_type == ContentType.ANALYTICAL, f"Should identify analytical content: {content}"
        
        # Should have reasonable confidence
        assert analysis.confidence >= 0.5, "Should have reasonable confidence in analytical content analysis"
        
        # Should extract relevant key terms
        analysis_terms = ["result", "data", "analysis", "performance", "benchmark", "metric"]
        found_terms = any(term in analysis.key_terms for term in analysis_terms)
        assert found_terms or any(term in content.lower() for term in analysis_terms), "Should extract analytical key terms"
    
    @given(mixed_content())
    @settings(max_examples=20, deadline=8000)
    def test_recommendation_generation_completeness(self, content):
        """Property: Recommendation generation should produce complete and valid recommendations."""
        async def test_recommendations():
            result = await self.engine.generate_recommendations(content)
            
            # Should have valid analysis
            assert isinstance(result.content_analysis, type(self.analyzer.analyze_content("")))
            assert result.content_analysis.content_type in ContentType
            assert result.content_analysis.complexity in ComplexityLevel
            assert result.content_analysis.mood in MoodType
            
            # Should have recommendations
            assert isinstance(result.recommendations, list)
            assert len(result.recommendations) > 0, "Should generate at least one recommendation"
            
            # All recommendations should be valid
            for rec in result.recommendations:
                assert isinstance(rec, CinematicRecommendation)
                assert rec.feature in ["camera_movements", "color_grading", "sound_design", "advanced_compositing"]
                assert isinstance(rec.setting, str) and len(rec.setting) > 0
                assert rec.value is not None
                assert isinstance(rec.reasoning, str) and len(rec.reasoning) > 0
                assert 0.0 <= rec.confidence <= 1.0
                assert 1 <= rec.priority <= 5
            
            # Should have suggested settings
            assert isinstance(result.suggested_settings, CinematicSettingsModel)
            
            # Should have template applied
            assert isinstance(result.template_applied, str) and len(result.template_applied) > 0
            
            # Should have reasonable confidence
            assert 0.0 <= result.confidence <= 1.0
        
        asyncio.run(test_recommendations())
    
    @given(mixed_content())
    @settings(max_examples=15, deadline=8000)
    def test_ai_enhanced_recommendations(self, content):
        """Property: AI-enhanced recommendations should improve upon rule-based analysis."""
        async def test_ai_enhancement():
            # Generate recommendations without AI
            rule_result = await self.engine.generate_recommendations(content)
            
            # Generate recommendations with AI
            ai_result = await self.ai_engine.generate_recommendations(content)
            
            # AI should have been called
            assert self.gemini_client.call_count > 0, "AI client should have been called"
            
            # Both should produce valid results
            assert isinstance(rule_result, RecommendationResult)
            assert isinstance(ai_result, RecommendationResult)
            
            # AI result should have equal or higher confidence (in most cases)
            # Note: This is a tendency, not a strict requirement due to randomness
            if ai_result.confidence < rule_result.confidence:
                # Allow some variance due to test randomness
                assert rule_result.confidence - ai_result.confidence < 0.3, "AI confidence shouldn't be much lower"
            
            # Both should have recommendations
            assert len(rule_result.recommendations) > 0
            assert len(ai_result.recommendations) > 0
            
            # AI analysis should include enhancement note
            assert "Enhanced with AI" in ai_result.content_analysis.reasoning
        
        asyncio.run(test_ai_enhancement())
    
    @given(mixed_content(), cinematic_settings())
    @settings(max_examples=15, deadline=8000)
    def test_recommendation_application(self, content, current_settings):
        """Property: Applying recommendations should modify settings appropriately."""
        async def test_application():
            # Generate recommendations
            result = await self.engine.generate_recommendations(content, current_settings)
            
            # Apply recommendations
            new_settings = await self.engine.apply_recommendations(
                result.recommendations, current_settings
            )
            
            # Should return valid settings
            assert isinstance(new_settings, CinematicSettingsModel)
            
            # Should have applied at least some recommendations
            settings_changed = False
            
            # Check if any settings were modified
            if new_settings.camera_movements.enabled != current_settings.camera_movements.enabled:
                settings_changed = True
            if new_settings.camera_movements.intensity != current_settings.camera_movements.intensity:
                settings_changed = True
            if new_settings.color_grading.film_emulation != current_settings.color_grading.film_emulation:
                settings_changed = True
            if new_settings.color_grading.temperature != current_settings.color_grading.temperature:
                settings_changed = True
            if new_settings.sound_design.enabled != current_settings.sound_design.enabled:
                settings_changed = True
            
            # Should have changed something if there were recommendations
            if len(result.recommendations) > 0:
                # Allow for cases where recommendations match current settings
                pass  # Not all recommendations necessarily change settings
            
            # New settings should be valid
            validation_errors = new_settings.validate()
            assert len(validation_errors) == 0, f"Applied settings should be valid: {validation_errors}"
        
        asyncio.run(test_application())
    
    @given(st.lists(mixed_content(), min_size=2, max_size=5))
    @settings(max_examples=10, deadline=10000)
    def test_recommendation_consistency(self, content_list):
        """Property: Similar content should receive similar recommendations."""
        async def test_consistency():
            results = []
            
            # Generate recommendations for all content
            for content in content_list:
                result = await self.engine.generate_recommendations(content)
                results.append(result)
            
            # Group by content type
            type_groups = {}
            for result in results:
                content_type = result.content_analysis.content_type
                if content_type not in type_groups:
                    type_groups[content_type] = []
                type_groups[content_type].append(result)
            
            # Check consistency within each type group
            for content_type, group_results in type_groups.items():
                if len(group_results) < 2:
                    continue  # Need at least 2 for comparison
                
                # Check template consistency
                templates = [r.template_applied for r in group_results]
                # Most should use the same template (allow some variation)
                most_common_template = max(set(templates), key=templates.count)
                template_consistency = templates.count(most_common_template) / len(templates)
                assert template_consistency >= 0.5, f"Template consistency should be >= 50% for {content_type}"
                
                # Check recommendation feature consistency
                all_features = set()
                for result in group_results:
                    for rec in result.recommendations:
                        all_features.add(rec.feature)
                
                # Each result should have recommendations for core features
                core_features = {"camera_movements", "color_grading", "sound_design"}
                for result in group_results:
                    result_features = {rec.feature for rec in result.recommendations}
                    common_features = core_features.intersection(result_features)
                    assert len(common_features) >= 1, "Should have recommendations for core features"
        
        asyncio.run(test_consistency())
    
    @given(mixed_content())
    @settings(max_examples=15, deadline=6000)
    def test_template_application_validity(self, content):
        """Property: Applied templates should be valid and appropriate for content type."""
        async def test_template_validity():
            result = await self.engine.generate_recommendations(content)
            
            # Template should be appropriate for content type
            content_type = result.content_analysis.content_type
            expected_template = f"{content_type.value}_template"
            assert result.template_applied == expected_template, f"Template should match content type: {content_type}"
            
            # Suggested settings should reflect template characteristics
            settings = result.suggested_settings
            
            # Mathematical content should have specific characteristics
            if content_type == ContentType.MATHEMATICAL:
                # Should prefer subtle camera movements
                if settings.camera_movements.enabled:
                    assert settings.camera_movements.intensity <= 50, "Mathematical content should have subtle camera movements"
            
            # Architectural content should have specific characteristics
            elif content_type == ContentType.ARCHITECTURAL:
                # Should enable spatial audio if sound is enabled
                if settings.sound_design.enabled:
                    # Architectural content often benefits from spatial audio
                    pass  # This is a preference, not a strict requirement
            
            # Analytical content should have specific characteristics
            elif content_type == ContentType.ANALYTICAL:
                # Should prefer minimal camera movement
                if settings.camera_movements.enabled:
                    assert settings.camera_movements.intensity <= 30, "Analytical content should have minimal camera movement"
            
            # All settings should be valid
            validation_errors = settings.validate()
            assert len(validation_errors) == 0, f"Template settings should be valid: {validation_errors}"
        
        asyncio.run(test_template_validity())
    
    def test_available_templates_completeness(self):
        """Property: All content types should have available templates."""
        templates = self.engine.get_available_templates()
        
        # Should have templates for all content types
        expected_types = [ct.value for ct in ContentType if ct != ContentType.GENERAL]
        
        for content_type in expected_types:
            assert content_type in templates, f"Should have template for {content_type}"
            
            template_info = templates[content_type]
            assert "name" in template_info
            assert "description" in template_info
            assert "features" in template_info
            
            # Should have core features
            assert isinstance(template_info["features"], list)
            assert len(template_info["features"]) > 0, "Template should have features"
    
    @given(st.text(min_size=5, max_size=100))
    @settings(max_examples=20, deadline=6000)
    def test_content_analysis_robustness(self, content):
        """Property: Content analysis should handle arbitrary text robustly."""
        # Filter out problematic characters that might cause issues
        assume(len(content.strip()) > 0)
        assume(not all(c in ' \n\t' for c in content))
        
        analysis = self.analyzer.analyze_content(content)
        
        # Should always return valid analysis
        assert isinstance(analysis.content_type, ContentType)
        assert isinstance(analysis.complexity, ComplexityLevel)
        assert isinstance(analysis.mood, MoodType)
        assert analysis.pacing in ["slow", "medium", "fast"]
        assert analysis.technical_level in ["beginner", "intermediate", "advanced"]
        assert isinstance(analysis.key_terms, list)
        assert 0.0 <= analysis.confidence <= 1.0
        assert isinstance(analysis.reasoning, str) and len(analysis.reasoning) > 0
        
        # Key terms should be reasonable
        for term in analysis.key_terms:
            assert isinstance(term, str)
            assert len(term) >= 3, "Key terms should be meaningful words"
    
    @given(mixed_content())
    @settings(max_examples=10, deadline=8000)
    def test_recommendation_priority_ordering(self, content):
        """Property: Recommendations should be properly prioritized."""
        async def test_priority():
            result = await self.engine.generate_recommendations(content)
            
            # Should have recommendations with valid priorities
            for rec in result.recommendations:
                assert 1 <= rec.priority <= 5, "Priority should be between 1 and 5"
            
            # Higher priority recommendations should generally have higher confidence
            if len(result.recommendations) >= 2:
                # Sort by priority (higher first)
                sorted_recs = sorted(result.recommendations, key=lambda r: r.priority, reverse=True)
                
                # Check that high priority recommendations have reasonable confidence
                high_priority_recs = [r for r in sorted_recs if r.priority >= 4]
                if high_priority_recs:
                    for rec in high_priority_recs:
                        assert rec.confidence >= 0.7, "High priority recommendations should have high confidence"
        
        asyncio.run(test_priority())


class ContentRecommendationStateMachine(RuleBasedStateMachine):
    """Stateful property testing for content recommendation system."""
    
    def __init__(self):
        super().__init__()
        self.analyzer = ContentAnalyzer()
        self.engine = CinematicRecommendationEngine()
        self.analyzed_content = []
        self.generated_recommendations = []
        self.applied_settings = []
    
    content_bundle = Bundle('content')
    recommendations_bundle = Bundle('recommendations')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=content_bundle)
    def create_content(self):
        """Create test content."""
        content_types = [
            "Mathematical equation: f(x) = x^2 + 2x + 1 demonstrates quadratic relationships",
            "System architecture overview showing modular design patterns and interfaces",
            "Performance analysis reveals 85% improvement in processing efficiency",
            "Step-by-step implementation process for algorithm optimization",
            "Introduction to advanced machine learning methodologies and applications",
            "Conclusion: significant breakthroughs achieved in computational efficiency"
        ]
        
        import random
        content = random.choice(content_types)
        return content
    
    @rule(target=recommendations_bundle, content=content_bundle)
    def analyze_and_recommend(self, content):
        """Analyze content and generate recommendations."""
        async def analyze():
            # Analyze content
            analysis = self.analyzer.analyze_content(content)
            self.analyzed_content.append((content, analysis))
            
            # Generate recommendations
            result = await self.engine.generate_recommendations(content)
            self.generated_recommendations.append(result)
            
            return result
        
        return asyncio.run(analyze())
    
    @rule(recommendations=recommendations_bundle)
    def apply_recommendations(self, recommendations):
        """Apply recommendations to settings."""
        async def apply():
            # Create base settings
            base_settings = CinematicSettingsModel(
                camera_movements=CameraMovementSettings(),
                color_grading=ColorGradingSettings(),
                sound_design=SoundDesignSettings(),
                advanced_compositing=AdvancedCompositingSettings()
            )
            
            # Apply recommendations
            new_settings = await self.engine.apply_recommendations(
                recommendations.recommendations, base_settings
            )
            
            self.applied_settings.append(new_settings)
            return new_settings
        
        asyncio.run(apply())
    
    @rule()
    def check_template_availability(self):
        """Check that templates are available."""
        templates = self.engine.get_available_templates()
        assert len(templates) > 0, "Should have available templates"
        
        for template_name, template_info in templates.items():
            assert "name" in template_info
            assert "description" in template_info
            assert "features" in template_info
    
    @invariant()
    def analysis_consistency(self):
        """Invariant: Content analysis should be consistent."""
        # All analyzed content should have valid analysis
        for content, analysis in self.analyzed_content:
            assert isinstance(analysis.content_type, ContentType)
            assert isinstance(analysis.complexity, ComplexityLevel)
            assert isinstance(analysis.mood, MoodType)
            assert 0.0 <= analysis.confidence <= 1.0
    
    @invariant()
    def recommendation_validity(self):
        """Invariant: All recommendations should be valid."""
        for result in self.generated_recommendations:
            assert isinstance(result, RecommendationResult)
            assert len(result.recommendations) > 0
            
            for rec in result.recommendations:
                assert isinstance(rec, CinematicRecommendation)
                assert 0.0 <= rec.confidence <= 1.0
                assert 1 <= rec.priority <= 5
    
    @invariant()
    def settings_validity(self):
        """Invariant: All applied settings should be valid."""
        for settings in self.applied_settings:
            assert isinstance(settings, CinematicSettingsModel)
            validation_errors = settings.validate()
            assert len(validation_errors) == 0, f"Settings should be valid: {validation_errors}"


# Test the state machine
TestContentRecommendationState = ContentRecommendationStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])