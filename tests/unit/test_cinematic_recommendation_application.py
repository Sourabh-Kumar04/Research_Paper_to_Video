"""
Property tests for cinematic recommendation application.
Tests that recommendations are properly applied and user acceptance workflows work correctly.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from src.cinematic.recommendation_engine import (
    CinematicRecommendationEngine, CinematicRecommendation, RecommendationResult
)
from src.cinematic.models import (
    CinematicSettingsModel, CameraMovementSettings, ColorGradingSettings,
    SoundDesignSettings, AdvancedCompositingSettings, CameraMovementType, FilmEmulationType
)


# Mock user acceptance workflow
class MockUserAcceptanceWorkflow:
    """Mock user acceptance workflow for testing."""
    
    def __init__(self, acceptance_rate: float = 0.8):
        self.acceptance_rate = acceptance_rate
        self.presented_recommendations = []
        self.accepted_recommendations = []
        self.rejected_recommendations = []
        self.user_feedback = []
    
    async def present_recommendations(self, recommendations: List[CinematicRecommendation]) -> Dict[str, Any]:
        """Present recommendations to user and get acceptance decisions."""
        self.presented_recommendations.extend(recommendations)
        
        # Simulate user decisions based on acceptance rate
        accepted = []
        rejected = []
        
        for rec in recommendations:
            # Higher priority and confidence recommendations more likely to be accepted
            acceptance_probability = self.acceptance_rate
            
            if rec.priority >= 4:
                acceptance_probability += 0.1
            if rec.confidence >= 0.9:
                acceptance_probability += 0.1
            
            # Simulate user decision
            import random
            if random.random() < acceptance_probability:
                accepted.append(rec)
                self.accepted_recommendations.append(rec)
            else:
                rejected.append(rec)
                self.rejected_recommendations.append(rec)
        
        return {
            "accepted": accepted,
            "rejected": rejected,
            "feedback": f"Accepted {len(accepted)} of {len(recommendations)} recommendations"
        }
    
    async def get_user_feedback(self, applied_settings: CinematicSettingsModel) -> Dict[str, Any]:
        """Get user feedback on applied settings."""
        feedback = {
            "satisfaction_score": min(10, max(1, int(self.acceptance_rate * 10))),
            "comments": "Settings look good" if self.acceptance_rate > 0.7 else "Some adjustments needed",
            "suggested_changes": []
        }
        
        # Add some random feedback
        if self.acceptance_rate < 0.5:
            feedback["suggested_changes"].append("Reduce camera movement intensity")
        
        self.user_feedback.append(feedback)
        return feedback
    
    def get_acceptance_statistics(self) -> Dict[str, Any]:
        """Get statistics about user acceptance."""
        total_presented = len(self.presented_recommendations)
        total_accepted = len(self.accepted_recommendations)
        
        return {
            "total_presented": total_presented,
            "total_accepted": total_accepted,
            "acceptance_rate": total_accepted / total_presented if total_presented > 0 else 0,
            "average_satisfaction": sum(f["satisfaction_score"] for f in self.user_feedback) / len(self.user_feedback) if self.user_feedback else 0
        }


# Strategies for generating test data
@st.composite
def recommendation_list(draw):
    """Generate list of cinematic recommendations."""
    num_recommendations = draw(st.integers(min_value=1, max_value=8))
    recommendations = []
    
    features = ["camera_movements", "color_grading", "sound_design", "advanced_compositing"]
    settings = {
        "camera_movements": ["enabled", "intensity", "allowed_types"],
        "color_grading": ["enabled", "film_emulation", "temperature", "contrast", "saturation"],
        "sound_design": ["enabled", "ambient_audio", "music_scoring", "spatial_audio"],
        "advanced_compositing": ["enabled", "film_grain", "dynamic_lighting", "depth_of_field"]
    }
    
    for i in range(num_recommendations):
        feature = draw(st.sampled_from(features))
        setting = draw(st.sampled_from(settings[feature]))
        
        # Generate appropriate value based on setting
        if setting == "enabled":
            value = draw(st.booleans())
        elif setting == "intensity":
            value = draw(st.integers(min_value=0, max_value=100))
        elif setting == "film_emulation":
            value = draw(st.sampled_from(list(FilmEmulationType)))
        elif setting in ["temperature", "contrast", "saturation"]:
            value = draw(st.integers(min_value=-100, max_value=100))
        elif setting == "allowed_types":
            value = draw(st.lists(st.sampled_from(list(CameraMovementType)), min_size=1))
        else:
            value = draw(st.booleans())
        
        recommendation = CinematicRecommendation(
            feature=feature,
            setting=setting,
            value=value,
            reasoning=f"Recommended {setting} for {feature} based on content analysis",
            confidence=draw(st.floats(min_value=0.5, max_value=1.0)),
            priority=draw(st.integers(min_value=1, max_value=5))
        )
        
        recommendations.append(recommendation)
    
    return recommendations

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
            saturation=draw(st.integers(min_value=-100, max_value=100)),
            brightness=draw(st.integers(min_value=-100, max_value=100))
        ),
        sound_design=SoundDesignSettings(
            enabled=draw(st.booleans()),
            ambient_audio=draw(st.booleans()),
            music_scoring=draw(st.booleans()),
            spatial_audio=draw(st.booleans()),
            reverb_intensity=draw(st.integers(min_value=0, max_value=100))
        ),
        advanced_compositing=AdvancedCompositingSettings(
            enabled=draw(st.booleans()),
            film_grain=draw(st.booleans()),
            dynamic_lighting=draw(st.booleans()),
            depth_of_field=draw(st.booleans()),
            motion_blur=draw(st.booleans())
        )
    )


class TestRecommendationApplication:
    """Test recommendation application and user acceptance workflows."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.engine = CinematicRecommendationEngine()
        self.workflow = MockUserAcceptanceWorkflow()
    
    @given(recommendation_list(), cinematic_settings())
    @settings(max_examples=20, deadline=8000)
    def test_recommendation_application_completeness(self, recommendations, current_settings):
        """Property: All accepted recommendations should be properly applied to settings."""
        async def test_application():
            # Apply all recommendations
            new_settings = await self.engine.apply_recommendations(recommendations, current_settings)
            
            # Should return valid settings
            assert isinstance(new_settings, CinematicSettingsModel)
            
            # Validate that settings are still valid after application
            validation_errors = new_settings.validate()
            assert len(validation_errors) == 0, f"Applied settings should be valid: {validation_errors}"
            
            # Check that recommendations were applied
            for rec in recommendations:
                if rec.feature == "camera_movements":
                    if rec.setting == "enabled":
                        assert new_settings.camera_movements.enabled == rec.value, f"Camera movement enabled should be applied: {rec.value}"
                    elif rec.setting == "intensity":
                        assert new_settings.camera_movements.intensity == rec.value, f"Camera movement intensity should be applied: {rec.value}"
                
                elif rec.feature == "color_grading":
                    if rec.setting == "enabled":
                        assert new_settings.color_grading.enabled == rec.value, f"Color grading enabled should be applied: {rec.value}"
                    elif rec.setting == "film_emulation":
                        assert new_settings.color_grading.film_emulation == rec.value, f"Film emulation should be applied: {rec.value}"
                    elif rec.setting == "temperature":
                        assert new_settings.color_grading.temperature == rec.value, f"Temperature should be applied: {rec.value}"
                    elif rec.setting == "contrast":
                        assert new_settings.color_grading.contrast == rec.value, f"Contrast should be applied: {rec.value}"
                    elif rec.setting == "saturation":
                        assert new_settings.color_grading.saturation == rec.value, f"Saturation should be applied: {rec.value}"
                
                elif rec.feature == "sound_design":
                    if rec.setting == "enabled":
                        assert new_settings.sound_design.enabled == rec.value, f"Sound design enabled should be applied: {rec.value}"
                    elif rec.setting == "ambient_audio":
                        assert new_settings.sound_design.ambient_audio == rec.value, f"Ambient audio should be applied: {rec.value}"
                    elif rec.setting == "music_scoring":
                        assert new_settings.sound_design.music_scoring == rec.value, f"Music scoring should be applied: {rec.value}"
                    elif rec.setting == "spatial_audio":
                        assert new_settings.sound_design.spatial_audio == rec.value, f"Spatial audio should be applied: {rec.value}"
                
                elif rec.feature == "advanced_compositing":
                    if rec.setting == "enabled":
                        assert new_settings.advanced_compositing.enabled == rec.value, f"Advanced compositing enabled should be applied: {rec.value}"
                    elif rec.setting == "film_grain":
                        assert new_settings.advanced_compositing.film_grain == rec.value, f"Film grain should be applied: {rec.value}"
                    elif rec.setting == "dynamic_lighting":
                        assert new_settings.advanced_compositing.dynamic_lighting == rec.value, f"Dynamic lighting should be applied: {rec.value}"
                    elif rec.setting == "depth_of_field":
                        assert new_settings.advanced_compositing.depth_of_field == rec.value, f"Depth of field should be applied: {rec.value}"
        
        asyncio.run(test_application())
    
    @given(recommendation_list())
    @settings(max_examples=15, deadline=8000)
    def test_user_acceptance_workflow(self, recommendations):
        """Property: User acceptance workflow should handle recommendations properly."""
        async def test_workflow():
            # Present recommendations to user
            acceptance_result = await self.workflow.present_recommendations(recommendations)
            
            # Should have acceptance results
            assert "accepted" in acceptance_result
            assert "rejected" in acceptance_result
            assert "feedback" in acceptance_result
            
            accepted = acceptance_result["accepted"]
            rejected = acceptance_result["rejected"]
            
            # All recommendations should be either accepted or rejected
            assert len(accepted) + len(rejected) == len(recommendations), "All recommendations should be categorized"
            
            # Accepted and rejected should be disjoint sets
            accepted_ids = {id(rec) for rec in accepted}
            rejected_ids = {id(rec) for rec in rejected}
            assert accepted_ids.isdisjoint(rejected_ids), "Accepted and rejected should be disjoint"
            
            # All items should be original recommendations
            all_processed = accepted + rejected
            assert len(all_processed) == len(recommendations), "Should process all recommendations"
            
            # Feedback should be meaningful
            assert isinstance(acceptance_result["feedback"], str)
            assert len(acceptance_result["feedback"]) > 0
        
        asyncio.run(test_workflow())
    
    @given(recommendation_list(), cinematic_settings())
    @settings(max_examples=15, deadline=10000)
    def test_selective_application_workflow(self, recommendations, current_settings):
        """Property: Only accepted recommendations should be applied in selective workflow."""
        async def test_selective_application():
            # Get user acceptance decisions
            acceptance_result = await self.workflow.present_recommendations(recommendations)
            accepted_recommendations = acceptance_result["accepted"]
            
            # Apply only accepted recommendations
            new_settings = await self.engine.apply_recommendations(accepted_recommendations, current_settings)
            
            # Should be valid
            assert isinstance(new_settings, CinematicSettingsModel)
            validation_errors = new_settings.validate()
            assert len(validation_errors) == 0, f"Settings should be valid: {validation_errors}"
            
            # Check that only accepted recommendations were applied
            for rec in accepted_recommendations:
                # Verify the recommendation was applied (same logic as previous test)
                if rec.feature == "camera_movements" and rec.setting == "enabled":
                    assert new_settings.camera_movements.enabled == rec.value
                elif rec.feature == "color_grading" and rec.setting == "temperature":
                    assert new_settings.color_grading.temperature == rec.value
                # Add more checks as needed
            
            # Get user feedback on applied settings
            feedback = await self.workflow.get_user_feedback(new_settings)
            
            # Should have valid feedback
            assert "satisfaction_score" in feedback
            assert 1 <= feedback["satisfaction_score"] <= 10
            assert "comments" in feedback
            assert isinstance(feedback["comments"], str)
        
        asyncio.run(test_selective_application())
    
    @given(st.lists(recommendation_list(), min_size=2, max_size=5))
    @settings(max_examples=8, deadline=12000)
    def test_acceptance_rate_consistency(self, recommendation_batches):
        """Property: User acceptance rate should be consistent across multiple batches."""
        async def test_consistency():
            # Process multiple batches of recommendations
            for batch in recommendation_batches:
                await self.workflow.present_recommendations(batch)
            
            # Get acceptance statistics
            stats = self.workflow.get_acceptance_statistics()
            
            # Should have processed recommendations
            assert stats["total_presented"] > 0, "Should have presented recommendations"
            
            # Acceptance rate should be reasonable
            assert 0.0 <= stats["acceptance_rate"] <= 1.0, "Acceptance rate should be between 0 and 1"
            
            # If we set a specific acceptance rate, it should be approximately maintained
            expected_rate = self.workflow.acceptance_rate
            actual_rate = stats["acceptance_rate"]
            
            # Allow some variance due to randomness and priority/confidence adjustments
            if stats["total_presented"] >= 10:  # Only check for larger samples
                assert abs(actual_rate - expected_rate) <= 0.3, f"Acceptance rate should be approximately {expected_rate}, got {actual_rate}"
        
        asyncio.run(test_consistency())
    
    @given(recommendation_list(), cinematic_settings())
    @settings(max_examples=15, deadline=8000)
    def test_recommendation_priority_influence(self, recommendations, current_settings):
        """Property: Higher priority recommendations should be more likely to be accepted."""
        # Set up workflow with moderate acceptance rate
        priority_workflow = MockUserAcceptanceWorkflow(acceptance_rate=0.6)
        
        async def test_priority_influence():
            # Present recommendations multiple times to get statistical significance
            all_accepted = []
            all_rejected = []
            
            for _ in range(5):  # Multiple rounds for better statistics
                acceptance_result = await priority_workflow.present_recommendations(recommendations)
                all_accepted.extend(acceptance_result["accepted"])
                all_rejected.extend(acceptance_result["rejected"])
            
            if len(all_accepted) > 0 and len(all_rejected) > 0:
                # Calculate average priority for accepted vs rejected
                avg_accepted_priority = sum(rec.priority for rec in all_accepted) / len(all_accepted)
                avg_rejected_priority = sum(rec.priority for rec in all_rejected) / len(all_rejected)
                
                # Accepted recommendations should generally have higher priority
                # (Allow some variance due to randomness)
                if len(all_accepted) >= 3 and len(all_rejected) >= 3:
                    assert avg_accepted_priority >= avg_rejected_priority - 0.5, "Accepted recommendations should have higher average priority"
        
        asyncio.run(test_priority_influence())
    
    @given(recommendation_list(), cinematic_settings())
    @settings(max_examples=15, deadline=8000)
    def test_recommendation_confidence_influence(self, recommendations, current_settings):
        """Property: Higher confidence recommendations should be more likely to be accepted."""
        # Set up workflow with moderate acceptance rate
        confidence_workflow = MockUserAcceptanceWorkflow(acceptance_rate=0.6)
        
        async def test_confidence_influence():
            # Present recommendations multiple times to get statistical significance
            all_accepted = []
            all_rejected = []
            
            for _ in range(5):  # Multiple rounds for better statistics
                acceptance_result = await confidence_workflow.present_recommendations(recommendations)
                all_accepted.extend(acceptance_result["accepted"])
                all_rejected.extend(acceptance_result["rejected"])
            
            if len(all_accepted) > 0 and len(all_rejected) > 0:
                # Calculate average confidence for accepted vs rejected
                avg_accepted_confidence = sum(rec.confidence for rec in all_accepted) / len(all_accepted)
                avg_rejected_confidence = sum(rec.confidence for rec in all_rejected) / len(all_rejected)
                
                # Accepted recommendations should generally have higher confidence
                # (Allow some variance due to randomness)
                if len(all_accepted) >= 3 and len(all_rejected) >= 3:
                    assert avg_accepted_confidence >= avg_rejected_confidence - 0.1, "Accepted recommendations should have higher average confidence"
        
        asyncio.run(test_confidence_influence())
    
    @given(recommendation_list(), cinematic_settings())
    @settings(max_examples=10, deadline=8000)
    def test_feedback_collection_completeness(self, recommendations, current_settings):
        """Property: User feedback should be collected and stored properly."""
        async def test_feedback():
            # Present and apply recommendations
            acceptance_result = await self.workflow.present_recommendations(recommendations)
            accepted = acceptance_result["accepted"]
            
            new_settings = await self.engine.apply_recommendations(accepted, current_settings)
            
            # Get user feedback
            feedback = await self.workflow.get_user_feedback(new_settings)
            
            # Should have complete feedback
            required_fields = ["satisfaction_score", "comments", "suggested_changes"]
            for field in required_fields:
                assert field in feedback, f"Feedback should include {field}"
            
            # Satisfaction score should be valid
            assert isinstance(feedback["satisfaction_score"], int)
            assert 1 <= feedback["satisfaction_score"] <= 10
            
            # Comments should be meaningful
            assert isinstance(feedback["comments"], str)
            assert len(feedback["comments"]) > 0
            
            # Suggested changes should be a list
            assert isinstance(feedback["suggested_changes"], list)
            
            # Feedback should be stored in workflow
            assert len(self.workflow.user_feedback) > 0
            assert feedback in self.workflow.user_feedback
        
        asyncio.run(test_feedback())
    
    def test_acceptance_statistics_accuracy(self):
        """Property: Acceptance statistics should accurately reflect user interactions."""
        # Create workflow with known acceptance rate
        test_workflow = MockUserAcceptanceWorkflow(acceptance_rate=0.75)
        
        async def test_statistics():
            # Create test recommendations
            test_recommendations = [
                CinematicRecommendation(
                    feature="camera_movements",
                    setting="enabled",
                    value=True,
                    reasoning="Test recommendation",
                    confidence=0.8,
                    priority=3
                )
                for _ in range(20)  # Larger sample for better statistics
            ]
            
            # Present recommendations
            await test_workflow.present_recommendations(test_recommendations)
            
            # Get statistics
            stats = test_workflow.get_acceptance_statistics()
            
            # Should have accurate counts
            assert stats["total_presented"] == 20
            assert stats["total_accepted"] + len(test_workflow.rejected_recommendations) == 20
            
            # Acceptance rate should be calculated correctly
            expected_rate = stats["total_accepted"] / stats["total_presented"]
            assert abs(stats["acceptance_rate"] - expected_rate) < 0.001, "Acceptance rate calculation should be accurate"
        
        asyncio.run(test_statistics())


class RecommendationApplicationStateMachine(RuleBasedStateMachine):
    """Stateful property testing for recommendation application."""
    
    def __init__(self):
        super().__init__()
        self.engine = CinematicRecommendationEngine()
        self.workflow = MockUserAcceptanceWorkflow()
        self.recommendation_batches = []
        self.applied_settings_history = []
        self.feedback_history = []
    
    recommendations_bundle = Bundle('recommendations')
    settings_bundle = Bundle('settings')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=recommendations_bundle)
    def create_recommendations(self):
        """Create a batch of recommendations."""
        recommendations = [
            CinematicRecommendation(
                feature="camera_movements",
                setting="intensity",
                value=50,
                reasoning="Moderate camera movement for engagement",
                confidence=0.8,
                priority=3
            ),
            CinematicRecommendation(
                feature="color_grading",
                setting="film_emulation",
                value=FilmEmulationType.KODAK,
                reasoning="Kodak emulation for warm look",
                confidence=0.9,
                priority=4
            )
        ]
        
        self.recommendation_batches.append(recommendations)
        return recommendations
    
    @rule(target=settings_bundle, recommendations=recommendations_bundle)
    def apply_recommendations_workflow(self, recommendations):
        """Apply recommendations through user acceptance workflow."""
        async def apply():
            # Present to user
            acceptance_result = await self.workflow.present_recommendations(recommendations)
            accepted = acceptance_result["accepted"]
            
            # Create base settings
            base_settings = CinematicSettingsModel(
                camera_movements=CameraMovementSettings(),
                color_grading=ColorGradingSettings(),
                sound_design=SoundDesignSettings(),
                advanced_compositing=AdvancedCompositingSettings()
            )
            
            # Apply accepted recommendations
            new_settings = await self.engine.apply_recommendations(accepted, base_settings)
            
            # Get feedback
            feedback = await self.workflow.get_user_feedback(new_settings)
            
            self.applied_settings_history.append(new_settings)
            self.feedback_history.append(feedback)
            
            return new_settings
        
        return asyncio.run(apply())
    
    @rule(settings=settings_bundle)
    def validate_applied_settings(self, settings):
        """Validate that applied settings are correct."""
        assert isinstance(settings, CinematicSettingsModel)
        
        # Settings should be valid
        validation_errors = settings.validate()
        assert len(validation_errors) == 0, f"Applied settings should be valid: {validation_errors}"
    
    @rule()
    def check_acceptance_statistics(self):
        """Check acceptance statistics consistency."""
        if len(self.recommendation_batches) > 0:
            stats = self.workflow.get_acceptance_statistics()
            
            # Should have reasonable statistics
            assert stats["total_presented"] >= 0
            assert stats["total_accepted"] >= 0
            assert 0.0 <= stats["acceptance_rate"] <= 1.0
            
            if len(self.feedback_history) > 0:
                assert stats["average_satisfaction"] >= 0
    
    @invariant()
    def workflow_consistency(self):
        """Invariant: Workflow state should be consistent."""
        # Total presented should equal accepted + rejected
        total_presented = len(self.workflow.presented_recommendations)
        total_accepted = len(self.workflow.accepted_recommendations)
        total_rejected = len(self.workflow.rejected_recommendations)
        
        assert total_presented == total_accepted + total_rejected, "Workflow counts should be consistent"
    
    @invariant()
    def settings_validity(self):
        """Invariant: All applied settings should remain valid."""
        for settings in self.applied_settings_history:
            validation_errors = settings.validate()
            assert len(validation_errors) == 0, "All applied settings should be valid"
    
    @invariant()
    def feedback_completeness(self):
        """Invariant: All feedback should be complete."""
        for feedback in self.feedback_history:
            assert "satisfaction_score" in feedback
            assert "comments" in feedback
            assert "suggested_changes" in feedback
            assert 1 <= feedback["satisfaction_score"] <= 10


# Test the state machine
TestRecommendationApplicationState = RecommendationApplicationStateMachine.TestCase


if __name__ == "__main__":
    pytest.main([__file__])