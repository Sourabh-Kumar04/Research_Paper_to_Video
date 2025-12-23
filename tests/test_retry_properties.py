"""
Property-based tests for RASO retry mechanisms and failure recovery.

**Feature: raso-platform, Property 13: Failure recovery mechanisms**
Tests that the platform implements automatic retry with exponential backoff,
preserves partial progress, enables workflow resumption, and maintains comprehensive logs.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from backend.models import (
    RASOMasterState,
    PaperInput,
    AgentType,
    ErrorSeverity,
    WorkflowStatus,
)
from agents.base import BaseAgent, AgentExecutionError
from agents.retry import (
    RetryConfig,
    RetryStrategy,
    CircuitBreaker,
    CircuitBreakerState,
    retry,
    retry_with_config,
    RetryableOperation,
)
from agents.logging import AgentLogger


class FailingFunction:
    """Mock function that fails a specified number of times."""
    
    def __init__(self, fail_count: int = 2, exception_type: type = Exception):
        self.fail_count = fail_count
        self.call_count = 0
        self.exception_type = exception_type
        self.call_history: List[datetime] = []
    
    async def __call__(self, *args, **kwargs) -> str:
        """Call the function, failing the specified number of times."""
        self.call_count += 1
        self.call_history.append(datetime.now())
        
        if self.call_count <= self.fail_count:
            raise self.exception_type(f"Failure {self.call_count}")
        
        return f"Success after {self.call_count} attempts"
    
    def sync_call(self, *args, **kwargs) -> str:
        """Synchronous version of the call."""
        self.call_count += 1
        self.call_history.append(datetime.now())
        
        if self.call_count <= self.fail_count:
            raise self.exception_type(f"Failure {self.call_count}")
        
        return f"Success after {self.call_count} attempts"


class TestRetryMechanismProperties:
    """Property-based tests for retry mechanisms and failure recovery."""

    @given(
        max_attempts=st.integers(min_value=1, max_value=10),
        base_delay=st.floats(min_value=0.01, max_value=1.0),
        backoff_multiplier=st.floats(min_value=1.1, max_value=5.0),
        fail_count=st.integers(min_value=0, max_value=5),
    )
    def test_exponential_backoff_property(
        self, max_attempts: int, base_delay: float, backoff_multiplier: float, fail_count: int
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any retry configuration, exponential backoff should provide
        increasing delays that respect maximum limits and provide predictable timing.
        **Validates: Requirements 12.1, 12.4**
        """
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            backoff_multiplier=backoff_multiplier,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=False,  # Disable jitter for predictable testing
        )
        
        # Test delay calculation
        delays = []
        for attempt in range(max_attempts):
            delay = config.calculate_delay(attempt)
            delays.append(delay)
            
            # Verify delay is non-negative
            assert delay >= 0.0
            
            # Verify delay respects maximum
            assert delay <= config.max_delay
            
            # For exponential backoff, each delay should be larger (or equal due to max limit)
            if attempt > 0 and delays[attempt - 1] < config.max_delay:
                expected_delay = min(
                    base_delay * (backoff_multiplier ** attempt),
                    config.max_delay
                )
                assert abs(delay - expected_delay) < 0.001  # Allow for floating point precision
        
        # Test retry decision logic
        retryable_error = Exception("Retryable error")
        
        for attempt in range(max_attempts + 2):  # Test beyond limit
            should_retry = config.should_retry(retryable_error, attempt)
            expected = attempt < max_attempts
            assert should_retry == expected

    @given(
        strategy=st.sampled_from(list(RetryStrategy)),
        max_attempts=st.integers(min_value=2, max_value=5),
        base_delay=st.floats(min_value=0.01, max_value=0.1),  # Small delays for fast tests
    )
    async def test_retry_decorator_property(
        self, strategy: RetryStrategy, max_attempts: int, base_delay: float
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any retry strategy and configuration, the retry decorator should
        attempt the specified number of retries with appropriate delays.
        **Validates: Requirements 12.1**
        """
        # Create failing function
        fail_count = max_attempts - 1  # Succeed on last attempt
        failing_func = FailingFunction(fail_count)
        
        # Apply retry decorator
        @retry(
            max_attempts=max_attempts,
            base_delay=base_delay,
            strategy=strategy,
            jitter=False,
        )
        async def decorated_func():
            return await failing_func()
        
        # Execute and measure timing
        start_time = datetime.now()
        result = await decorated_func()
        end_time = datetime.now()
        
        # Verify success
        assert result == f"Success after {max_attempts} attempts"
        assert failing_func.call_count == max_attempts
        
        # Verify timing - should have delays between attempts
        total_duration = (end_time - start_time).total_seconds()
        
        # Calculate expected minimum duration (sum of delays)
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            strategy=strategy,
            jitter=False,
        )
        
        expected_delay_sum = sum(
            config.calculate_delay(attempt) for attempt in range(max_attempts - 1)
        )
        
        # Allow some tolerance for execution time
        assert total_duration >= expected_delay_sum * 0.8

    @given(
        failure_threshold=st.integers(min_value=2, max_value=10),
        recovery_timeout=st.floats(min_value=0.1, max_value=2.0),
        consecutive_failures=st.integers(min_value=1, max_value=15),
    )
    async def test_circuit_breaker_property(
        self, failure_threshold: int, recovery_timeout: float, consecutive_failures: int
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any circuit breaker configuration, the breaker should open after
        the threshold is reached and attempt recovery after the timeout.
        **Validates: Requirements 12.1, 12.3**
        """
        circuit_breaker = CircuitBreaker(
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
        )
        
        # Create always-failing function
        async def always_fail():
            raise Exception("Always fails")
        
        # Test failures up to threshold
        for i in range(consecutive_failures):
            try:
                await circuit_breaker.call(always_fail)
            except Exception:
                pass  # Expected to fail
            
            # Check circuit state
            if i + 1 >= failure_threshold:
                assert circuit_breaker.state == CircuitBreakerState.OPEN
                assert circuit_breaker.failure_count >= failure_threshold
            else:
                assert circuit_breaker.state == CircuitBreakerState.CLOSED
        
        # If circuit opened, test recovery behavior
        if circuit_breaker.state == CircuitBreakerState.OPEN:
            # Should reject calls immediately
            with pytest.raises(Exception, match="Circuit breaker is OPEN"):
                await circuit_breaker.call(always_fail)
            
            # Wait for recovery timeout
            await asyncio.sleep(recovery_timeout + 0.1)
            
            # Should attempt half-open state
            try:
                await circuit_breaker.call(always_fail)
            except Exception:
                pass  # Expected to fail and go back to open
            
            # Should be open again after failure
            assert circuit_breaker.state == CircuitBreakerState.OPEN

    @given(
        initial_errors=st.integers(min_value=0, max_value=5),
        new_error_count=st.integers(min_value=1, max_value=5),
        preserve_progress=st.booleans(),
    )
    def test_partial_progress_preservation_property(
        self, initial_errors: int, new_error_count: int, preserve_progress: bool
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any failure scenario, the system should preserve partial progress
        and maintain state consistency for workflow resumption.
        **Validates: Requirements 12.4**
        """
        # Create state with some progress
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Add initial errors
        for i in range(initial_errors):
            state.add_error(
                agent_type=AgentType.INGEST,
                error_code=f"INITIAL_ERROR_{i}",
                message=f"Initial error {i} for testing",
                severity=ErrorSeverity.WARNING,
            )
        
        # Simulate some progress
        if preserve_progress:
            state.progress.update_progress(
                WorkflowStatus.UNDERSTANDING,
                0.5,
                "Partial progress made"
            )
            state.progress.complete_step(WorkflowStatus.INGESTING)
        
        # Record initial state
        initial_progress = state.progress.overall_progress
        initial_completed_steps = len(state.progress.completed_steps)
        initial_error_count = len(state.errors)
        
        # Add new errors (simulating failures)
        for i in range(new_error_count):
            state.add_error(
                agent_type=AgentType.UNDERSTANDING,
                error_code=f"NEW_ERROR_{i}",
                message=f"New error {i} for testing",
                severity=ErrorSeverity.ERROR,
            )
        
        # Verify progress preservation
        if preserve_progress:
            assert state.progress.overall_progress == initial_progress
            assert len(state.progress.completed_steps) == initial_completed_steps
            assert WorkflowStatus.INGESTING in state.progress.completed_steps
        
        # Verify error accumulation
        assert len(state.errors) == initial_error_count + new_error_count
        
        # Verify state can be serialized/deserialized (for resumption)
        json_data = state.json()
        restored_state = RASOMasterState.parse_raw(json_data)
        
        # Verify all progress and errors are preserved
        assert restored_state.progress.overall_progress == state.progress.overall_progress
        assert len(restored_state.progress.completed_steps) == len(state.progress.completed_steps)
        assert len(restored_state.errors) == len(state.errors)
        
        # Verify error details are preserved
        for original, restored in zip(state.errors, restored_state.errors):
            assert original.agent_type == restored.agent_type
            assert original.error_code == restored.error_code
            assert original.message == restored.message
            assert original.severity == restored.severity

    @given(
        operation_name=st.text(min_size=5, max_size=50),
        max_attempts=st.integers(min_value=2, max_value=5),
        fail_count=st.integers(min_value=0, max_value=3),
    )
    async def test_retryable_operation_logging_property(
        self, operation_name: str, max_attempts: int, fail_count: int
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any retryable operation, comprehensive logs should be maintained
        for debugging and system analysis.
        **Validates: Requirements 12.5**
        """
        # Create mock logger
        mock_logger = MagicMock()
        
        # Create retry configuration
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=0.01,  # Fast for testing
        )
        
        # Create retryable operation
        operation = RetryableOperation(operation_name, config, mock_logger)
        
        # Create function that fails specified number of times
        failing_func = FailingFunction(fail_count)
        
        # Execute operation
        try:
            async with operation:
                result = await operation.execute(failing_func)
                
            # If we get here, operation succeeded
            assert result == f"Success after {fail_count + 1} attempts"
            
        except Exception as e:
            # Operation failed after all retries
            assert fail_count >= max_attempts
        
        # Verify logging calls
        assert mock_logger.info.called
        
        # Check that operation start was logged
        start_calls = [call for call in mock_logger.info.call_args_list 
                      if "Starting retryable operation" in str(call)]
        assert len(start_calls) >= 1
        
        # If there were retries, check retry logging
        if fail_count > 0 and fail_count < max_attempts:
            retry_calls = [call for call in mock_logger.info.call_args_list 
                          if "Retrying" in str(call)]
            assert len(retry_calls) >= min(fail_count, max_attempts - 1)
        
        # Check warning calls for failures
        if fail_count > 0:
            assert mock_logger.warning.called
            warning_calls = [call for call in mock_logger.warning.call_args_list 
                           if "failed" in str(call)]
            assert len(warning_calls) >= min(fail_count + 1, max_attempts + 1)

    @given(
        job_id=st.uuids().map(str),
        agent_type=st.sampled_from(list(AgentType)),
        error_count=st.integers(min_value=1, max_value=10),
    )
    def test_comprehensive_error_logging_property(
        self, job_id: str, agent_type: AgentType, error_count: int
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any error scenario, comprehensive logs should provide sufficient
        information for debugging and system analysis.
        **Validates: Requirements 12.5**
        """
        # Create logger
        logger = AgentLogger(agent_type, job_id)
        
        # Create state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(job_id=job_id, paper_input=paper_input)
        
        # Generate various types of errors
        error_types = [
            (Exception("General error"), "GENERAL_ERROR"),
            (ValueError("Value error"), "VALUE_ERROR"),
            (ConnectionError("Connection error"), "CONNECTION_ERROR"),
            (TimeoutError("Timeout error"), "TIMEOUT_ERROR"),
        ]
        
        # Add errors to state and log them
        logged_errors = []
        for i in range(error_count):
            error_type, error_code = error_types[i % len(error_types)]
            
            # Add error to state
            agent_error = state.add_error(
                agent_type=agent_type,
                error_code=f"{error_code}_{i}",
                message=f"Error {i}: {str(error_type)}",
                severity=ErrorSeverity.ERROR,
            )
            
            logged_errors.append(agent_error)
        
        # Verify error information is comprehensive
        for error in logged_errors:
            # Check required fields
            assert error.agent_type == agent_type
            assert error.error_code is not None
            assert error.message is not None
            assert error.severity is not None
            assert error.timestamp is not None
            
            # Check error details
            assert isinstance(error.details, dict)
            
            # Verify error can be serialized for logging
            error_dict = error.dict()
            assert "agent_type" in error_dict
            assert "error_code" in error_dict
            assert "message" in error_dict
            assert "severity" in error_dict
            assert "timestamp" in error_dict
        
        # Verify state maintains all error information
        assert len(state.errors) == error_count
        
        # Test serialization preserves error information
        json_data = state.json()
        restored_state = RASOMasterState.parse_raw(json_data)
        
        assert len(restored_state.errors) == error_count
        for original, restored in zip(state.errors, restored_state.errors):
            assert original.agent_type == restored.agent_type
            assert original.error_code == restored.error_code
            assert original.message == restored.message
            assert original.severity == restored.severity

    @given(
        max_attempts=st.integers(min_value=2, max_value=5),
        base_delay=st.floats(min_value=0.01, max_value=0.1),
        jitter_enabled=st.booleans(),
    )
    async def test_retry_timing_consistency_property(
        self, max_attempts: int, base_delay: float, jitter_enabled: bool
    ):
        """
        **Property 13: Failure recovery mechanisms**
        For any retry configuration, timing should be consistent and predictable
        within the bounds of the configuration parameters.
        **Validates: Requirements 12.1**
        """
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            strategy=RetryStrategy.EXPONENTIAL,
            jitter=jitter_enabled,
            backoff_multiplier=2.0,
        )
        
        # Create function that always fails
        call_times = []
        
        async def failing_func():
            call_times.append(datetime.now())
            raise Exception("Always fails")
        
        # Execute with retry
        try:
            await retry_with_config(failing_func, config)
        except Exception:
            pass  # Expected to fail
        
        # Verify number of attempts
        assert len(call_times) == max_attempts + 1  # Initial + retries
        
        # Verify timing between attempts
        for i in range(1, len(call_times)):
            actual_delay = (call_times[i] - call_times[i-1]).total_seconds()
            expected_delay = config.calculate_delay(i-1)
            
            if jitter_enabled:
                # With jitter, allow 20% variance
                assert actual_delay >= expected_delay * 0.8
                assert actual_delay <= expected_delay * 1.2 + 0.1  # Add small buffer for execution time
            else:
                # Without jitter, should be very close to expected
                assert abs(actual_delay - expected_delay) <= 0.05  # Small buffer for execution time

    def test_workflow_resumption_property(self):
        """
        **Property 13: Failure recovery mechanisms**
        For any workflow state, the system should enable resumption
        from the point of failure with preserved context.
        **Validates: Requirements 12.4**
        """
        # Create state with partial progress
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Simulate workflow progress
        completed_steps = [
            WorkflowStatus.INGESTING,
            WorkflowStatus.UNDERSTANDING,
        ]
        
        for step in completed_steps:
            state.progress.complete_step(step)
        
        # Set current step
        state.progress.update_progress(
            WorkflowStatus.SCRIPTING,
            0.3,
            "Partially completed scripting"
        )
        
        # Add some errors
        state.add_error(
            agent_type=AgentType.SCRIPT,
            error_code="SCRIPT_ERROR",
            message="Scripting failed midway",
            severity=ErrorSeverity.ERROR,
        )
        
        # Simulate system restart by serializing and deserializing
        json_data = state.json()
        resumed_state = RASOMasterState.parse_raw(json_data)
        
        # Verify resumption context is preserved
        assert resumed_state.job_id == state.job_id
        assert resumed_state.paper_input == state.paper_input
        assert resumed_state.progress.current_step == WorkflowStatus.SCRIPTING
        assert resumed_state.progress.step_progress == 0.3
        assert len(resumed_state.progress.completed_steps) == len(completed_steps)
        
        for step in completed_steps:
            assert step in resumed_state.progress.completed_steps
        
        # Verify errors are preserved
        assert len(resumed_state.errors) == 1
        assert resumed_state.errors[0].error_code == "SCRIPT_ERROR"
        
        # Verify workflow can continue from this point
        assert not resumed_state.should_abort()  # Single error shouldn't abort
        
        # Test that we can continue processing
        resumed_state.progress.update_progress(
            WorkflowStatus.SCRIPTING,
            1.0,
            "Completed scripting after resumption"
        )
        resumed_state.progress.complete_step(WorkflowStatus.SCRIPTING)
        
        assert WorkflowStatus.SCRIPTING in resumed_state.progress.completed_steps
        assert resumed_state.progress.overall_progress > state.progress.overall_progress


if __name__ == "__main__":
    pytest.main([__file__])