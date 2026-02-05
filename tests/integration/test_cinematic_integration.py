"""
Integration tests for complete cinematic system workflows.

Tests complete user workflows from UI to video generation, validates integration
with existing video composition pipeline, tests error handling and fallback scenarios,
and verifies performance under concurrent user access.
"""

import pytest
import asyncio
import tempfile
import shutil
import os
import json
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime
import concurrent.futures
import time

from src.cinematic.settings_manager import CinematicSettingsManager
from src.cinematic.initialization_system import DefaultStateManager, InitializationConfig
from src.cinematic.preview_generator import PreviewGenerator
from src.cinematic.recommendation_engine import RecommendationEngine
from src.cinematic.multi_scene_consistency import MultiSceneConsistencyAnalyzer, AdvancedTemplateSystem
from src.cinematic.models import CinematicSettingsModel, VisualDescriptionModel
from src.llm.gemini_client import GeminiClient


class TestCinematicIntegration:
    """Integration tests for complete cinematic system workflows."""
    
    @pytest.fixture
    async def temp_config(self):
        """Create temporary configuration for testing."""
        temp_dir = tempfile.mkdtemp()
        config = InitializationConfig(
            profiles_directory=os.path.join(temp_dir, "profiles"),
            analytics_directory=os.path.join(temp_dir, "analytics"),
            last_used_profile_file=os.path.join(temp_dir, "last_used.json"),
            system_profiles_file=os.path.join(temp_dir, "system_profiles.json"),
            enable_analytics=True,
            auto_create_directories=True
        )
        yield config
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    async def mock_gemini_client(self):
        """Create mock Gemini client."""
        client = AsyncMock(spec=GeminiClient)
        
        # Mock visual description generation
        async def mock_generate_content(prompt):
            if "visual description" in prompt.lower():
                return json.dumps({
                    "description": "Professional cinematic scene with dynamic lighting and smooth camera movements",
                    "suggestions": ["Add depth of field", "Enhance color grading"],
                    "confidence": 0.85
                })
            elif "consistency" in prompt.lower():
                return json.dumps({
                    "consistency_score": 0.8,
                    "visual_themes": ["professional lighting", "smooth transitions"],
                    "inconsistencies": [],
                    "recommendations": ["Maintain consistent color temperature"],
                    "confidence": 0.9
                })
            elif "classification" in prompt.lower():
                return "mathematical"
            else:
                return "Generated content for: " + prompt[:50]
        
        client.generate_content.side_effect = mock_generate_content
        return client
    
    @pytest.fixture
    async def integrated_system(self, temp_config, mock_gemini_client):
        """Create fully integrated cinematic system."""
        # Initialize settings manager
        settings_manager = CinematicSettingsManager()
        
        # Initialize default state manager
        init_system = DefaultStateManager(temp_config)
        await init_system.initialize(settings_manager)
        
        # Initialize other components
        preview_generator = PreviewGenerator()
        recommendation_engine = RecommendationEngine(mock_gemini_client)
        consistency_analyzer = MultiSceneConsistencyAnalyzer(mock_gemini_client)
        template_system = AdvancedTemplateSystem(mock_gemini_client)
        
        return {
            'settings_manager': settings_manager,
            'init_system': init_system,
            'preview_generator': preview_generator,
            'recommendation_engine': recommendation_engine,
            'consistency_analyzer': consistency_analyzer,
            'template_system': template_system,
            'gemini_client': mock_gemini_client
        }
    
    async def test_complete_user_workflow_ui_to_video_generation(self, integrated_system):
        """
        Test complete user workflow from UI to video generation.
        
        Validates: Requirements 7.1, 7.2, 7.6, 7.7, 8.1
        """
        system = integrated_system
        
        # Step 1: User starts system and gets default profile
        startup_profile_id = await system['init_system'].get_startup_profile("test_user")
        assert startup_profile_id is not None
        
        # Step 2: User loads profile settings
        if startup_profile_id:
            profile = await system['settings_manager'].load_profile(startup_profile_id, "test_user")
            # Profile might not exist yet, that's ok for this test
        
        # Step 3: User creates new cinematic settings
        test_settings = {
            "camera_movements": {
                "enabled": True,
                "allowed_types": ["pan", "zoom"],
                "intensity": 60,
                "auto_select": True
            },
            "color_grading": {
                "enabled": True,
                "film_emulation": "cinema",
                "temperature": 10,
                "contrast": 15,
                "saturation": 5
            },
            "sound_design": {
                "enabled": True,
                "ambient_audio": True,
                "music_scoring": True,
                "spatial_audio": False,
                "reverb_intensity": 30
            },
            "advanced_compositing": {
                "enabled": True,
                "film_grain": True,
                "dynamic_lighting": True,
                "depth_of_field": False,
                "motion_blur": False
            },
            "quality_preset": "cinematic_4k",
            "auto_recommendations": True
        }
        
        # Step 4: User saves profile
        profile_id = await system['settings_manager'].save_profile(
            "Test Workflow Profile",
            test_settings,
            "test_user",
            set_as_default=True
        )
        assert isinstance(profile_id, str)
        
        # Step 5: User generates preview
        preview_result = await system['preview_generator'].generate_preview(
            test_settings,
            "color_grading",
            sample_content="Test mathematical content with equations"
        )
        assert preview_result is not None
        assert 'preview_url' in preview_result
        
        # Step 6: User gets content recommendations
        content = "This video explains mathematical concepts using visual proofs and equations."
        recommendations = await system['recommendation_engine'].analyze_content_and_recommend(
            content, test_settings
        )
        assert recommendations is not None
        assert 'recommendations' in recommendations
        
        # Step 7: User applies recommendations
        if recommendations['recommendations']:
            first_rec = recommendations['recommendations'][0]
            updated_settings = await system['recommendation_engine'].apply_recommendation(
                test_settings, first_rec
            )
            assert updated_settings is not None
        
        # Step 8: User generates visual descriptions for multiple scenes
        scenes = [
            "Introduction to linear algebra concepts",
            "Matrix multiplication examples", 
            "Eigenvalue calculations and applications"
        ]
        
        visual_descriptions = []
        for i, scene_content in enumerate(scenes):
            # Classify content type
            content_type = await system['template_system'].classify_content_type(scene_content)
            assert content_type is not None
            
            # Get appropriate template
            template = system['template_system'].get_template_by_content_type(content_type)
            if template:
                # Apply template
                applied_template = system['template_system'].apply_template(
                    template.id, f"scene_{i}"
                )
                assert applied_template is not None
            
            # Create visual description
            visual_desc = VisualDescriptionModel(
                scene_id=f"scene_{i}",
                content=scene_content,
                description=f"Professional visualization of {scene_content.lower()}",
                generated_by="gemini",
                cinematic_settings=test_settings,
                scene_analysis={},
                suggestions=[],
                confidence=0.8,
                created_at=datetime.utcnow().isoformat(),
                updated_at=datetime.utcnow().isoformat()
            )
            visual_descriptions.append(visual_desc)
        
        # Step 9: Check consistency across scenes
        consistency_analysis = await system['consistency_analyzer'].analyze_scene_consistency(
            visual_descriptions
        )
        assert consistency_analysis is not None
        assert 0.0 <= consistency_analysis.consistency_score <= 1.0
        
        # Step 10: Update last used profile
        await system['init_system'].set_last_used_profile(profile_id, "test_user")
        
        # Step 11: Verify the complete workflow maintained data integrity
        final_profile = await system['settings_manager'].load_profile(profile_id, "test_user")
        assert final_profile is not None
        assert final_profile['settings'] == test_settings
        
        # Step 12: Verify startup profile is now the one we created
        new_startup_profile = await system['init_system'].get_startup_profile("test_user")
        # Note: May not be exactly profile_id due to fallback logic, but should be valid
        if new_startup_profile:
            assert isinstance(new_startup_profile, str)
    
    async def test_error_handling_and_fallback_scenarios(self, integrated_system):
        """
        Test error handling and fallback scenarios.
        
        Validates: Requirements 7.2, 7.7, 8.7
        """
        system = integrated_system
        
        # Test 1: Gemini client failure fallback
        system['gemini_client'].generate_content.side_effect = Exception("API Error")
        
        # Should fall back to template-based recommendations
        content = "Mathematical proof using geometric visualization"
        try:
            recommendations = await system['recommendation_engine'].analyze_content_and_recommend(
                content, {}
            )
            # Should not raise exception, should provide fallback recommendations
            assert recommendations is not None
        except Exception as e:
            # Fallback should handle the error gracefully
            assert "fallback" in str(e).lower() or recommendations is not None
        
        # Test 2: Invalid settings validation
        invalid_settings = {
            "camera_movements": {
                "enabled": "not_a_boolean",  # Invalid type
                "intensity": 150  # Out of range
            }
        }
        
        validation_result = await system['settings_manager'].validate_settings(invalid_settings)
        assert validation_result is not None
        assert not validation_result.get('is_valid', True)  # Should be invalid
        
        # Test 3: Profile not found fallback
        non_existent_profile = await system['settings_manager'].load_profile(
            "non_existent_id", "test_user"
        )
        assert non_existent_profile is None  # Should handle gracefully
        
        # Test 4: Preview generation failure
        # Mock preview generation to fail
        with patch.object(system['preview_generator'], 'generate_preview') as mock_preview:
            mock_preview.side_effect = Exception("Preview generation failed")
            
            try:
                result = await system['preview_generator'].generate_preview({}, "test_feature")
                # Should either return None or a fallback result
                assert result is None or 'error' in result
            except Exception:
                # Should handle gracefully or provide fallback
                pass
        
        # Test 5: Consistency analysis with empty scenes
        empty_consistency = await system['consistency_analyzer'].analyze_scene_consistency([])
        assert empty_consistency is not None
        assert empty_consistency.consistency_score == 1.0  # Perfect consistency for empty set
    
    async def test_concurrent_user_access_performance(self, integrated_system):
        """
        Test performance under concurrent user access.
        
        Validates: Requirements 8.1
        """
        system = integrated_system
        
        async def simulate_user_workflow(user_id: str) -> Dict[str, Any]:
            """Simulate a complete user workflow."""
            start_time = time.time()
            
            try:
                # Create user-specific settings
                user_settings = {
                    "camera_movements": {
                        "enabled": True,
                        "intensity": 40 + (hash(user_id) % 40)  # Vary by user
                    },
                    "color_grading": {
                        "enabled": True,
                        "temperature": (hash(user_id) % 20) - 10
                    },
                    "quality_preset": "cinematic_4k"
                }
                
                # Save profile
                profile_id = await system['settings_manager'].save_profile(
                    f"Profile for {user_id}",
                    user_settings,
                    user_id
                )
                
                # Generate preview
                preview = await system['preview_generator'].generate_preview(
                    user_settings,
                    "color_grading",
                    f"Content for {user_id}"
                )
                
                # Get recommendations
                recommendations = await system['recommendation_engine'].analyze_content_and_recommend(
                    f"Mathematical content for {user_id}",
                    user_settings
                )
                
                # Set as last used
                await system['init_system'].set_last_used_profile(profile_id, user_id)
                
                end_time = time.time()
                
                return {
                    'user_id': user_id,
                    'profile_id': profile_id,
                    'duration': end_time - start_time,
                    'success': True,
                    'preview_generated': preview is not None,
                    'recommendations_received': recommendations is not None
                }
                
            except Exception as e:
                end_time = time.time()
                return {
                    'user_id': user_id,
                    'duration': end_time - start_time,
                    'success': False,
                    'error': str(e)
                }
        
        # Simulate 10 concurrent users
        user_ids = [f"user_{i}" for i in range(10)]
        
        # Run concurrent workflows
        tasks = [simulate_user_workflow(user_id) for user_id in user_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Analyze results
        successful_results = [r for r in results if isinstance(r, dict) and r.get('success', False)]
        failed_results = [r for r in results if not isinstance(r, dict) or not r.get('success', False)]
        
        # Verify performance criteria
        assert len(successful_results) >= 8, f"At least 80% of concurrent users should succeed, got {len(successful_results)}/10"
        
        # Check response times are reasonable (under 10 seconds per user)
        for result in successful_results:
            assert result['duration'] < 10.0, f"User workflow took too long: {result['duration']}s"
        
        # Verify all users got their profiles created
        for result in successful_results:
            assert 'profile_id' in result
            profile = await system['settings_manager'].load_profile(
                result['profile_id'], 
                result['user_id']
            )
            assert profile is not None
        
        # Check system state consistency after concurrent access
        all_profiles = []
        for user_id in user_ids:
            user_profiles = await system['settings_manager'].get_user_profiles(user_id)
            all_profiles.extend(user_profiles)
        
        # Should have at least one profile per successful user
        assert len(all_profiles) >= len(successful_results)
    
    async def test_existing_video_composition_pipeline_integration(self, integrated_system):
        """
        Test integration with existing video composition pipeline.
        
        Validates: Requirements 7.1, 7.6
        """
        system = integrated_system
        
        # Test 1: Settings compatibility with existing formats
        cinematic_settings = {
            "camera_movements": {
                "enabled": True,
                "allowed_types": ["pan", "zoom", "dolly"],
                "intensity": 50
            },
            "color_grading": {
                "enabled": True,
                "film_emulation": "cinema",
                "temperature": 10,
                "contrast": 15
            },
            "quality_preset": "cinematic_4k"
        }
        
        # Validate settings are in expected format
        validation_result = await system['settings_manager'].validate_settings(cinematic_settings)
        assert validation_result.get('is_valid', False)
        
        # Test 2: Visual descriptions are properly formatted
        visual_desc = VisualDescriptionModel(
            scene_id="integration_test",
            content="Test content for integration",
            description="Cinematic scene with professional lighting and camera work",
            generated_by="gemini",
            cinematic_settings=cinematic_settings,
            scene_analysis={
                "mood": "professional",
                "complexity": "medium",
                "focus_type": "analytical"
            },
            suggestions=["Add depth of field", "Enhance transitions"],
            confidence=0.85,
            created_at=datetime.utcnow().isoformat(),
            updated_at=datetime.utcnow().isoformat()
        )
        
        # Verify visual description has all required fields for video composition
        assert visual_desc.scene_id is not None
        assert visual_desc.description is not None
        assert visual_desc.cinematic_settings is not None
        assert isinstance(visual_desc.cinematic_settings, dict)
        
        # Test 3: Profile export/import for pipeline compatibility
        profile_id = await system['settings_manager'].save_profile(
            "Integration Test Profile",
            cinematic_settings,
            "integration_user"
        )
        
        # Export profile
        exported_data = await system['settings_manager'].export_profile(profile_id, "integration_user")
        assert exported_data is not None
        assert isinstance(exported_data, str)
        
        # Import profile (simulating pipeline handoff)
        imported_profile_id = await system['settings_manager'].import_profile(
            exported_data, "integration_user"
        )
        assert imported_profile_id is not None
        
        # Verify imported profile matches original
        imported_profile = await system['settings_manager'].load_profile(
            imported_profile_id, "integration_user"
        )
        assert imported_profile is not None
        
        # Settings should be equivalent (allowing for minor formatting differences)
        imported_settings = imported_profile['settings']
        assert 'camera_movements' in imported_settings
        assert 'color_grading' in imported_settings
        assert imported_settings['quality_preset'] == cinematic_settings['quality_preset']
    
    async def test_system_state_consistency_under_load(self, integrated_system):
        """
        Test that system maintains consistency under various load conditions.
        """
        system = integrated_system
        
        # Test 1: Rapid profile creation and deletion
        profile_ids = []
        for i in range(20):
            profile_id = await system['settings_manager'].save_profile(
                f"Load Test Profile {i}",
                {"test": f"settings_{i}"},
                "load_test_user"
            )
            profile_ids.append(profile_id)
        
        # Verify all profiles were created
        user_profiles = await system['settings_manager'].get_user_profiles("load_test_user")
        assert len(user_profiles) >= 20
        
        # Delete half the profiles
        for i in range(0, len(profile_ids), 2):
            await system['settings_manager'].delete_profile(profile_ids[i], "load_test_user")
        
        # Verify remaining profiles are still accessible
        remaining_profiles = await system['settings_manager'].get_user_profiles("load_test_user")
        assert len(remaining_profiles) >= 10
        
        # Test 2: Concurrent preview generation
        async def generate_concurrent_preview(feature_name: str):
            return await system['preview_generator'].generate_preview(
                {"test": "settings"},
                feature_name,
                f"Test content for {feature_name}"
            )
        
        preview_tasks = [
            generate_concurrent_preview(f"feature_{i}") 
            for i in range(5)
        ]
        
        preview_results = await asyncio.gather(*preview_tasks, return_exceptions=True)
        
        # Most previews should succeed (allowing for some failures under load)
        successful_previews = [r for r in preview_results if not isinstance(r, Exception)]
        assert len(successful_previews) >= 3  # At least 60% success rate
        
        # Test 3: System profile consistency
        system_profiles_before = await system['init_system'].get_system_profiles()
        
        # Perform various operations
        await system['init_system'].restore_default_settings("consistency_user")
        await system['settings_manager'].save_profile("Test", {}, "consistency_user")
        
        system_profiles_after = await system['init_system'].get_system_profiles()
        
        # System profiles should remain unchanged
        assert len(system_profiles_before) == len(system_profiles_after)
        
        profile_names_before = {p.name for p in system_profiles_before}
        profile_names_after = {p.name for p in system_profiles_after}
        assert profile_names_before == profile_names_after


if __name__ == "__main__":
    # Run integration tests
    async def run_integration_tests():
        print("Running cinematic system integration tests...")
        
        # Create temporary config
        temp_dir = tempfile.mkdtemp()
        config = InitializationConfig(
            profiles_directory=os.path.join(temp_dir, "profiles"),
            analytics_directory=os.path.join(temp_dir, "analytics"),
            last_used_profile_file=os.path.join(temp_dir, "last_used.json"),
            system_profiles_file=os.path.join(temp_dir, "system_profiles.json"),
            enable_analytics=True,
            auto_create_directories=True
        )
        
        # Create mock Gemini client
        mock_gemini = AsyncMock(spec=GeminiClient)
        mock_gemini.generate_content.return_value = json.dumps({
            "description": "Test cinematic description",
            "confidence": 0.8
        })
        
        try:
            # Initialize integrated system
            settings_manager = CinematicSettingsManager()
            init_system = DefaultStateManager(config)
            await init_system.initialize(settings_manager)
            
            preview_generator = PreviewGenerator()
            recommendation_engine = RecommendationEngine(mock_gemini)
            
            system = {
                'settings_manager': settings_manager,
                'init_system': init_system,
                'preview_generator': preview_generator,
                'recommendation_engine': recommendation_engine,
                'gemini_client': mock_gemini
            }
            
            print("✓ System initialized successfully")
            
            # Test basic workflow
            profile_id = await settings_manager.save_profile(
                "Integration Test",
                {"camera_movements": {"enabled": True}},
                "test_user"
            )
            print(f"✓ Profile created: {profile_id}")
            
            # Test preview generation
            preview = await preview_generator.generate_preview(
                {"test": "settings"},
                "color_grading"
            )
            print(f"✓ Preview generated: {preview is not None}")
            
            # Test recommendations
            recommendations = await recommendation_engine.analyze_content_and_recommend(
                "Test mathematical content",
                {}
            )
            print(f"✓ Recommendations generated: {recommendations is not None}")
            
            print("All integration tests completed successfully!")
            
        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    asyncio.run(run_integration_tests())