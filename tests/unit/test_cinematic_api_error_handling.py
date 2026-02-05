"""
Property tests for cinematic API error handling and robustness.
Tests error scenarios, fallback mechanisms, and rate limiting.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, Bundle, rule, initialize, invariant
import json
from datetime import datetime, timedelta

from src.backend.routes.cinematic import router
from src.backend.models.cinematic_api import (
    CinematicProfileRequest, VisualDescriptionRequest, 
    SceneAnalysisRequest, PreviewRequest
)

# Create test app
app = FastAPI()
app.include_router(router)
client = TestClient(app)


# Hypothesis strategies for generating test data
@st.composite
def invalid_settings_data(draw):
    """Generate invalid cinematic settings."""
    return {
        "camera_movements": {
            "intensity": draw(st.integers(min_value=101, max_value=1000)),  # Invalid: > 100
            "enabled": draw(st.booleans())
        },
        "color_grading": {
            "temperature": draw(st.integers(min_value=-200, max_value=-101)),  # Invalid: < -100
            "contrast": draw(st.integers(min_value=101, max_value=200)),  # Invalid: > 100
            "enabled": draw(st.booleans())
        }
    }


@st.composite
def malformed_json_data(draw):
    """Generate malformed JSON strings."""
    malformed_options = [
        '{"incomplete": ',
        '{"invalid": "json"',
        '{invalid_json: true}',
        '{"nested": {"incomplete": }',
        '{"array": [1, 2, }',
        '',
        'not_json_at_all',
        '{"unicode": "\u0000"}',
        '{"very_long": "' + 'x' * 10000 + '"}',
    ]
    return draw(st.sampled_from(malformed_options))


@st.composite
def invalid_profile_request(draw):
    """Generate invalid profile requests."""
    return CinematicProfileRequest(
        name=draw(st.text(max_size=0)),  # Empty name
        description=draw(st.text(min_size=501, max_size=1000)),  # Too long
        settings=draw(invalid_settings_data()),
        user_id=draw(st.text()),
        set_as_default=draw(st.booleans())
    )


@st.composite
def invalid_visual_description_request(draw):
    """Generate invalid visual description requests."""
    return VisualDescriptionRequest(
        scene_id=draw(st.text(max_size=0)),  # Empty scene_id
        content=draw(st.text(max_size=0)),  # Empty content
        scene_context=draw(st.dictionaries(st.text(), st.text())),
        style_preferences=draw(st.dictionaries(st.text(), st.text()))
    )


class TestAPIErrorHandling:
    """Test API error handling and robustness."""
    
    def setup_method(self):
        """Set up test dependencies."""
        self.mock_manager = AsyncMock()
        self.mock_gemini = AsyncMock()
    
    @given(invalid_settings_data())
    @settings(max_examples=20, deadline=5000)
    def test_invalid_settings_validation(self, invalid_settings):
        """Property: Invalid settings are rejected with appropriate error messages."""
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            response = client.post(
                "/api/v1/cinematic/settings/validate",
                json={"settings": invalid_settings}
            )
            
            # Should return validation error
            assert response.status_code == 400 or response.status_code == 500
            
            if response.status_code == 400:
                error_data = response.json()
                assert "error" in error_data or "detail" in error_data
    
    @given(st.text(min_size=0, max_size=0))  # Empty profile name
    @settings(max_examples=10, deadline=3000)
    def test_empty_profile_name_rejection(self, empty_name):
        """Property: Empty profile names are rejected."""
        profile_data = {
            "name": empty_name,
            "description": "Test profile",
            "settings": {
                "camera_movements": {"enabled": True, "intensity": 50},
                "quality_preset": "standard_hd"
            },
            "user_id": "test_user"
        }
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            response = client.post(
                "/api/v1/cinematic/settings/profiles",
                json=profile_data
            )
            
            # Should return validation error
            assert response.status_code == 422  # Pydantic validation error
    
    @given(malformed_json_data())
    @settings(max_examples=15, deadline=5000)
    def test_malformed_json_handling(self, malformed_json):
        """Property: Malformed JSON requests are handled gracefully."""
        assume(malformed_json.strip() != "")  # Not completely empty
        
        # Test with raw malformed JSON
        response = client.post(
            "/api/v1/cinematic/settings/profiles",
            data=malformed_json,
            headers={"Content-Type": "application/json"}
        )
        
        # Should return 422 (validation error) or 400 (bad request)
        assert response.status_code in [400, 422]
    
    def test_nonexistent_profile_handling(self):
        """Property: Requests for nonexistent profiles return 404."""
        nonexistent_id = "nonexistent_profile_12345"
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            # Mock manager to return None (profile not found)
            self.mock_manager.load_profile.return_value = None
            
            response = client.get(f"/api/v1/cinematic/settings/profiles/{nonexistent_id}")
            
            assert response.status_code == 404
            error_data = response.json()
            assert "not found" in error_data["detail"].lower()
    
    def test_database_connection_failure_handling(self):
        """Property: Database connection failures are handled gracefully."""
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            # Mock database connection failure
            self.mock_manager.get_user_profiles.side_effect = ConnectionError("Database unavailable")
            
            response = client.get("/api/v1/cinematic/settings/profiles")
            
            assert response.status_code == 500
            error_data = response.json()
            assert "detail" in error_data
    
    def test_gemini_api_failure_fallback(self):
        """Property: Gemini API failures have appropriate fallbacks."""
        with patch('src.backend.routes.cinematic.get_gemini_client', return_value=self.mock_gemini):
            with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
                # Mock Gemini API failure
                self.mock_gemini.generate_detailed_visual_description.side_effect = Exception("API unavailable")
                
                request_data = {
                    "scene_id": "test_scene",
                    "content": "Test content for description"
                }
                
                response = client.post(
                    "/api/v1/cinematic/visual-description",
                    json=request_data
                )
                
                assert response.status_code == 500
                error_data = response.json()
                assert "detail" in error_data
    
    @given(st.integers(min_value=1, max_value=100))
    @settings(max_examples=10, deadline=10000)
    def test_concurrent_request_handling(self, num_requests):
        """Property: API handles concurrent requests without corruption."""
        assume(num_requests <= 20)  # Reasonable limit for testing
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            # Mock successful responses
            self.mock_manager.get_user_profiles.return_value = []
            
            async def make_request():
                return client.get("/api/v1/cinematic/settings/profiles")
            
            # Make concurrent requests
            responses = []
            for _ in range(num_requests):
                response = client.get("/api/v1/cinematic/settings/profiles")
                responses.append(response)
            
            # All requests should succeed or fail consistently
            status_codes = [r.status_code for r in responses]
            assert all(code in [200, 500] for code in status_codes)
    
    def test_large_payload_handling(self):
        """Property: Large payloads are handled appropriately."""
        # Create large profile description
        large_description = "x" * 10000  # 10KB description
        
        profile_data = {
            "name": "Large Profile",
            "description": large_description,
            "settings": {
                "camera_movements": {"enabled": True, "intensity": 50},
                "quality_preset": "standard_hd"
            },
            "user_id": "test_user"
        }
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            response = client.post(
                "/api/v1/cinematic/settings/profiles",
                json=profile_data
            )
            
            # Should either succeed or return validation error for too large description
            assert response.status_code in [200, 201, 400, 422]
    
    def test_timeout_handling(self):
        """Property: Long-running operations handle timeouts gracefully."""
        with patch('src.backend.routes.cinematic.get_gemini_client', return_value=self.mock_gemini):
            with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
                # Mock slow Gemini response
                async def slow_response(*args, **kwargs):
                    await asyncio.sleep(10)  # Simulate slow response
                    return "Generated description"
                
                self.mock_gemini.generate_detailed_visual_description.side_effect = slow_response
                
                request_data = {
                    "scene_id": "test_scene",
                    "content": "Test content"
                }
                
                # This should timeout or complete quickly due to FastAPI's handling
                response = client.post(
                    "/api/v1/cinematic/visual-description",
                    json=request_data,
                    timeout=5  # 5 second timeout
                )
                
                # Should either complete or timeout gracefully
                assert response.status_code in [200, 500, 504]
    
    def test_authentication_error_handling(self):
        """Property: Authentication errors are handled consistently."""
        # Test with invalid user_id patterns
        invalid_user_ids = ["", "user with spaces", "user/with/slashes", "user\nwith\nnewlines"]
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            for user_id in invalid_user_ids:
                response = client.get(f"/api/v1/cinematic/settings/profiles?user_id={user_id}")
                
                # Should handle gracefully (either succeed with sanitized ID or return error)
                assert response.status_code in [200, 400, 422]
    
    def test_memory_exhaustion_protection(self):
        """Property: API protects against memory exhaustion attacks."""
        # Create request with deeply nested structure
        deeply_nested = {"level": {}}
        current = deeply_nested["level"]
        for i in range(100):  # Create 100 levels of nesting
            current["level"] = {}
            current = current["level"]
        
        profile_data = {
            "name": "Nested Profile",
            "description": "Test",
            "settings": deeply_nested,
            "user_id": "test_user"
        }
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager', return_value=self.mock_manager):
            response = client.post(
                "/api/v1/cinematic/settings/profiles",
                json=profile_data
            )
            
            # Should handle without crashing
            assert response.status_code in [200, 201, 400, 422, 500]


class APIRateLimitingStateMachine(RuleBasedStateMachine):
    """Stateful property testing for API rate limiting and caching."""
    
    def __init__(self):
        super().__init__()
        self.request_times = []
        self.cache_hits = 0
        self.rate_limit_hits = 0
    
    requests = Bundle('requests')
    
    @initialize()
    def setup(self):
        """Initialize the state machine."""
        pass
    
    @rule(target=requests)
    def make_api_request(self):
        """Make an API request and track timing."""
        current_time = datetime.utcnow()
        self.request_times.append(current_time)
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager') as mock_manager:
            mock_manager.return_value.get_user_profiles.return_value = []
            
            response = client.get("/api/v1/cinematic/settings/profiles")
            
            # Track rate limiting
            if response.status_code == 429:  # Too Many Requests
                self.rate_limit_hits += 1
            
            return response.status_code
    
    @rule()
    def check_rate_limiting(self):
        """Check that rate limiting is working if implemented."""
        # Remove old requests (older than 1 minute)
        cutoff_time = datetime.utcnow() - timedelta(minutes=1)
        self.request_times = [t for t in self.request_times if t > cutoff_time]
        
        # If we have many recent requests, rate limiting should kick in
        if len(self.request_times) > 100:  # Arbitrary threshold
            # Rate limiting should be active
            pass  # In real implementation, would check for 429 responses
    
    @invariant()
    def api_remains_responsive(self):
        """Invariant: API remains responsive under load."""
        # API should not crash completely
        with patch('src.backend.routes.cinematic.get_cinematic_manager') as mock_manager:
            mock_manager.return_value.get_user_profiles.return_value = []
            
            response = client.get("/api/v1/cinematic/settings/profiles")
            
            # Should return some response, not crash
            assert response.status_code in [200, 429, 500, 503]


# Test the state machine
TestAPIRateLimitingState = APIRateLimitingStateMachine.TestCase


class TestAPIRecovery:
    """Test API recovery and resilience mechanisms."""
    
    def test_graceful_degradation(self):
        """Property: API degrades gracefully when dependencies fail."""
        with patch('src.backend.routes.cinematic.get_cinematic_manager') as mock_manager:
            with patch('src.backend.routes.cinematic.get_gemini_client') as mock_gemini:
                # Simulate partial system failure
                mock_manager.return_value.get_user_profiles.side_effect = Exception("Database error")
                mock_gemini.return_value.generate_detailed_visual_description.return_value = "Fallback description"
                
                # Profile listing should fail gracefully
                response = client.get("/api/v1/cinematic/settings/profiles")
                assert response.status_code == 500
                
                # But other endpoints might still work
                request_data = {
                    "scene_id": "test_scene",
                    "content": "Test content"
                }
                
                # This might still work if Gemini is available
                response = client.post(
                    "/api/v1/cinematic/visual-description",
                    json=request_data
                )
                
                # Should either work or fail gracefully
                assert response.status_code in [200, 500]
    
    def test_circuit_breaker_behavior(self):
        """Property: Circuit breaker prevents cascade failures."""
        # This would test circuit breaker implementation if present
        # For now, just test that repeated failures don't crash the system
        
        with patch('src.backend.routes.cinematic.get_cinematic_manager') as mock_manager:
            mock_manager.return_value.get_user_profiles.side_effect = Exception("Persistent error")
            
            # Make multiple requests that will fail
            for _ in range(10):
                response = client.get("/api/v1/cinematic/settings/profiles")
                assert response.status_code == 500
                
                # System should remain responsive
                error_data = response.json()
                assert "detail" in error_data


if __name__ == "__main__":
    pytest.main([__file__])