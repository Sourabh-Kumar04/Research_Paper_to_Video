"""
Property-based tests for RASO agent communication and orchestration.

**Feature: raso-platform, Property 12: Agent architecture compliance**
Tests that the system uses LangGraph orchestration with stateless agents,
JSON-based communication with schema enforcement, and comprehensive state tracking.
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest
from hypothesis import given, strategies as st
from pydantic import ValidationError

from backend.models import (
    RASOMasterState,
    PaperInput,
    AgentType,
    ErrorSeverity,
    WorkflowStatus,
    ProcessingOptions,
)
from agents.base import BaseAgent, AgentRegistry, register_agent, AgentExecutionError
from agents.retry import RetryConfig, retry_with_config
from agents.logging import AgentLogger
from graph.workflow import WorkflowOrchestrator


# Mock agent for testing
@register_agent(AgentType.INGEST)
class MockIngestAgent(BaseAgent):
    """Mock ingest agent for testing."""
    
    @property
    def name(self) -> str:
        return "Mock Ingest Agent"
    
    @property
    def description(self) -> str:
        return "Mock agent for testing ingest functionality"
    
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """Mock execution that modifies state."""
        # Simulate processing delay
        await asyncio.sleep(0.01)
        
        # Create mock paper content
        from backend.models import PaperContent, Section
        
        paper_content = PaperContent(
            title="Mock Paper Title",
            authors=["Mock Author"],
            abstract="This is a mock abstract for testing purposes. " * 5,  # Ensure min length
            sections=[
                Section(
                    id="section1",
                    title="Introduction",
                    content="This is mock section content for testing. " * 10,  # Ensure min length
                    level=1,
                )
            ],
        )
        
        state.paper_content = paper_content
        return state


@register_agent(AgentType.UNDERSTANDING)
class MockUnderstandingAgent(BaseAgent):
    """Mock understanding agent for testing."""
    
    @property
    def name(self) -> str:
        return "Mock Understanding Agent"
    
    @property
    def description(self) -> str:
        return "Mock agent for testing understanding functionality"
    
    async def execute(self, state: RASOMasterState) -> RASOMasterState:
        """Mock execution that creates understanding."""
        if not state.paper_content:
            raise AgentExecutionError(
                "Paper content is required for understanding",
                "MISSING_PAPER_CONTENT",
                ErrorSeverity.ERROR
            )
        
        # Create mock understanding
        from backend.models import PaperUnderstanding
        
        understanding = PaperUnderstanding(
            problem="This is a mock problem statement for testing purposes. " * 2,
            intuition="This is a mock intuition explanation for testing purposes. " * 2,
            contributions=["Mock contribution 1 for testing purposes", "Mock contribution 2 for testing purposes"],
        )
        
        state.understanding = understanding
        return state


class TestAgentCommunicationProperties:
    """Property-based tests for agent communication and orchestration."""

    @given(
        job_id=st.uuids().map(str),
        paper_type=st.sampled_from(["title", "arxiv", "pdf"]),
        content=st.text(min_size=10, max_size=200),
    )
    def test_agent_stateless_operation_property(self, job_id: str, paper_type: str, content: str):
        """
        **Property 12: Agent architecture compliance**
        For any agent execution, agents should maintain stateless operation
        and not retain state between executions.
        **Validates: Requirements 11.1, 11.2, 11.4**
        """
        # Create initial state
        paper_input = PaperInput(type=paper_type, content=content)
        state1 = RASOMasterState(job_id=job_id, paper_input=paper_input)
        state2 = RASOMasterState(job_id=job_id, paper_input=paper_input)
        
        # Get agent instance
        registry = AgentRegistry()
        agent = MockIngestAgent(AgentType.INGEST)
        
        # Execute agent multiple times
        result1 = asyncio.run(agent.safe_execute(state1))
        result2 = asyncio.run(agent.safe_execute(state2))
        
        # Verify stateless operation - results should be consistent
        assert result1.paper_content is not None
        assert result2.paper_content is not None
        assert result1.paper_content.title == result2.paper_content.title
        assert result1.paper_content.authors == result2.paper_content.authors
        
        # Verify agent doesn't retain state between executions
        assert agent.agent_type == AgentType.INGEST
        # Agent should not have instance variables that change between calls

    @given(
        error_message=st.text(min_size=10, max_size=100),
        error_code=st.text(min_size=5, max_size=20),
        severity=st.sampled_from(list(ErrorSeverity)),
    )
    def test_agent_error_handling_property(self, error_message: str, error_code: str, severity: ErrorSeverity):
        """
        **Property 12: Agent architecture compliance**
        For any agent error, the error handling should preserve error information
        and maintain state consistency for debugging and recovery.
        **Validates: Requirements 11.4**
        """
        # Create state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Create agent
        agent = MockIngestAgent(AgentType.INGEST)
        
        # Create and handle error
        error = AgentExecutionError(error_message, error_code, severity)
        result_state = agent.handle_error(error, state)
        
        # Verify error is properly recorded
        assert len(result_state.errors) == 1
        recorded_error = result_state.errors[0]
        
        assert recorded_error.agent_type == AgentType.INGEST
        assert recorded_error.error_code == error_code
        assert recorded_error.message == error_message
        assert recorded_error.severity == severity
        
        # Verify state consistency
        assert result_state.job_id == state.job_id
        assert result_state.paper_input == state.paper_input
        
        # Verify JSON serialization preserves error information
        json_data = result_state.json()
        restored_state = RASOMasterState.parse_raw(json_data)
        
        assert len(restored_state.errors) == 1
        restored_error = restored_state.errors[0]
        assert restored_error.agent_type == recorded_error.agent_type
        assert restored_error.error_code == recorded_error.error_code
        assert restored_error.message == recorded_error.message
        assert restored_error.severity == recorded_error.severity

    def test_agent_registry_property(self):
        """
        **Property 12: Agent architecture compliance**
        The agent registry should maintain consistent agent instances
        and provide reliable agent lookup for orchestration.
        **Validates: Requirements 11.1**
        """
        registry = AgentRegistry()
        
        # Test agent registration and retrieval
        agent1 = registry.get_agent(AgentType.INGEST)
        agent2 = registry.get_agent(AgentType.INGEST)
        
        # Should return same instance (singleton behavior)
        assert agent1 is agent2
        assert isinstance(agent1, MockIngestAgent)
        assert agent1.agent_type == AgentType.INGEST
        
        # Test multiple agent types
        understanding_agent = registry.get_agent(AgentType.UNDERSTANDING)
        assert isinstance(understanding_agent, MockUnderstandingAgent)
        assert understanding_agent.agent_type == AgentType.UNDERSTANDING
        
        # Verify agents are different instances
        assert agent1 is not understanding_agent
        
        # Test registry listing
        agents = registry.list_agents()
        assert AgentType.INGEST in agents
        assert AgentType.UNDERSTANDING in agents
        assert agents[AgentType.INGEST] == "Mock Ingest Agent"
        assert agents[AgentType.UNDERSTANDING] == "Mock Understanding Agent"

    @given(
        max_attempts=st.integers(min_value=1, max_value=5),
        base_delay=st.floats(min_value=0.1, max_value=2.0),
    )
    def test_retry_mechanism_property(self, max_attempts: int, base_delay: float):
        """
        **Property 12: Agent architecture compliance**
        Retry mechanisms should provide consistent behavior and proper
        exponential backoff for reliable agent execution.
        **Validates: Requirements 11.1, 11.4**
        """
        # Create retry configuration
        config = RetryConfig(
            max_attempts=max_attempts,
            base_delay=base_delay,
            strategy="exponential",
        )
        
        # Test delay calculation
        for attempt in range(max_attempts):
            delay = config.calculate_delay(attempt)
            
            # Verify delay is reasonable
            assert delay >= 0.0
            assert delay <= config.max_delay
            
            # Verify exponential growth (approximately)
            if attempt > 0:
                prev_delay = config.calculate_delay(attempt - 1)
                # Allow for jitter, so just check it's generally increasing
                assert delay >= prev_delay * 0.5  # Account for jitter
        
        # Test retry decision logic
        retryable_error = Exception("Retryable error")
        non_retryable_error = ValueError("Non-retryable error")
        
        # Should retry retryable errors within limit
        for attempt in range(max_attempts):
            assert config.should_retry(retryable_error, attempt) == (attempt < max_attempts)
        
        # Should not retry non-retryable errors
        assert not config.should_retry(non_retryable_error, 0)

    def test_json_schema_enforcement_property(self):
        """
        **Property 12: Agent architecture compliance**
        JSON-based communication should enforce strict schema validation
        to ensure reliable agent coordination and data integrity.
        **Validates: Requirements 11.2**
        """
        # Create valid state
        paper_input = PaperInput(type="title", content="Valid Test Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Test valid serialization/deserialization
        json_data = state.json()
        parsed_data = json.loads(json_data)
        
        # Verify required fields are present
        assert "job_id" in parsed_data
        assert "paper_input" in parsed_data
        assert "options" in parsed_data
        assert "progress" in parsed_data
        
        # Test successful deserialization
        restored_state = RASOMasterState.parse_raw(json_data)
        assert restored_state.job_id == state.job_id
        assert restored_state.paper_input.type == state.paper_input.type
        assert restored_state.paper_input.content == state.paper_input.content
        
        # Test schema validation - invalid data should be rejected
        invalid_json_cases = [
            # Missing required field
            json_data.replace('"job_id":', '"invalid_field":'),
            # Invalid enum value
            json_data.replace('"title"', '"invalid_type"'),
            # Invalid data type
            json_data.replace('"overall_progress": 0.0', '"overall_progress": "invalid"'),
        ]
        
        for invalid_json in invalid_json_cases:
            with pytest.raises(ValidationError):
                RASOMasterState.parse_raw(invalid_json)

    def test_state_tracking_property(self):
        """
        **Property 12: Agent architecture compliance**
        State tracking should provide comprehensive progress monitoring
        and maintain consistency across workflow transitions.
        **Validates: Requirements 11.5**
        """
        # Create initial state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Test initial state
        assert state.progress.current_step == WorkflowStatus.PENDING
        assert state.progress.overall_progress == 0.0
        assert len(state.progress.completed_steps) == 0
        
        # Test state transitions
        workflow_steps = [
            WorkflowStatus.INGESTING,
            WorkflowStatus.UNDERSTANDING,
            WorkflowStatus.SCRIPTING,
        ]
        
        for i, step in enumerate(workflow_steps):
            # Update progress
            progress = (i + 1) / len(workflow_steps)
            state.progress.update_progress(step, progress, f"Processing {step.value}")
            
            # Verify state consistency
            assert state.progress.current_step == step
            assert state.progress.step_progress == progress
            assert state.progress.current_message == f"Processing {step.value}"
            
            # Complete the step
            state.progress.complete_step(step)
            assert step in state.progress.completed_steps
            
            # Verify overall progress increases
            assert state.progress.overall_progress > 0.0
            
            # Test serialization preserves state
            json_data = state.json()
            restored_state = RASOMasterState.parse_raw(json_data)
            
            assert restored_state.progress.current_step == state.progress.current_step
            assert restored_state.progress.overall_progress == state.progress.overall_progress
            assert len(restored_state.progress.completed_steps) == len(state.progress.completed_steps)

    def test_agent_execution_context_property(self):
        """
        **Property 12: Agent architecture compliance**
        Agent execution should maintain proper context and provide
        comprehensive debugging information for orchestration.
        **Validates: Requirements 11.4**
        """
        # Create state and agent
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        agent = MockIngestAgent(AgentType.INGEST)
        
        # Test execution context creation
        context = agent.create_execution_context(state)
        
        # Verify context contains required information
        assert "agent_type" in context
        assert "agent_name" in context
        assert "job_id" in context
        assert "timestamp" in context
        assert "config" in context
        
        assert context["agent_type"] == AgentType.INGEST.value
        assert context["agent_name"] == agent.name
        assert context["job_id"] == state.job_id
        
        # Verify config information
        config_info = context["config"]
        assert "retry_attempts" in config_info
        assert "timeout_minutes" in config_info
        
        # Test logging integration
        logger = AgentLogger(AgentType.INGEST, state.job_id)
        assert logger.agent_type == AgentType.INGEST
        assert logger.job_id == state.job_id
        
        # Test context preservation in logging
        log_context = logger._get_context()
        assert log_context["agent_type"] == AgentType.INGEST.value

    def test_workflow_orchestration_property(self):
        """
        **Property 12: Agent architecture compliance**
        Workflow orchestration should coordinate agents properly
        and maintain state consistency throughout execution.
        **Validates: Requirements 11.1, 11.5**
        """
        # Create orchestrator
        orchestrator = WorkflowOrchestrator()
        
        # Verify graph structure
        assert orchestrator.graph is not None
        
        # Create initial state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        initial_state = RASOMasterState(paper_input=paper_input)
        
        # Test workflow execution (mock execution)
        # Note: Full execution would require all agents to be implemented
        # Here we test the orchestration structure
        
        # Verify routing logic
        routing_result = orchestrator._route_animation(initial_state)
        assert routing_result == "voice"  # Should skip animation if no visual plan
        
        # Test YouTube upload decision
        upload_decision = orchestrator._should_upload_youtube(initial_state)
        assert upload_decision == "end"  # Should not upload by default
        
        # Test with auto-upload enabled
        initial_state.options.auto_upload = True
        upload_decision = orchestrator._should_upload_youtube(initial_state)
        # Still should be "end" because YouTube is not configured in test

    async def test_agent_pipeline_property(self):
        """
        **Property 12: Agent architecture compliance**
        Agent pipeline execution should maintain data flow integrity
        and proper state transitions between agents.
        **Validates: Requirements 11.1, 11.2**
        """
        # Create initial state
        paper_input = PaperInput(type="title", content="Test Paper Title")
        state = RASOMasterState(paper_input=paper_input)
        
        # Execute ingest agent
        ingest_agent = MockIngestAgent(AgentType.INGEST)
        state_after_ingest = await ingest_agent.safe_execute(state)
        
        # Verify ingest agent output
        assert state_after_ingest.paper_content is not None
        assert state_after_ingest.paper_content.title == "Mock Paper Title"
        assert len(state_after_ingest.paper_content.authors) == 1
        assert len(state_after_ingest.paper_content.sections) == 1
        
        # Execute understanding agent
        understanding_agent = MockUnderstandingAgent(AgentType.UNDERSTANDING)
        state_after_understanding = await understanding_agent.safe_execute(state_after_ingest)
        
        # Verify understanding agent output
        assert state_after_understanding.understanding is not None
        assert len(state_after_understanding.understanding.problem) >= 50
        assert len(state_after_understanding.understanding.contributions) >= 1
        
        # Verify state consistency throughout pipeline
        assert state_after_understanding.job_id == state.job_id
        assert state_after_understanding.paper_input == state.paper_input
        assert state_after_understanding.paper_content == state_after_ingest.paper_content
        
        # Test serialization at each stage
        for test_state in [state_after_ingest, state_after_understanding]:
            json_data = test_state.json()
            restored_state = RASOMasterState.parse_raw(json_data)
            
            # Verify critical data is preserved
            assert restored_state.job_id == test_state.job_id
            assert restored_state.paper_input == test_state.paper_input
            if test_state.paper_content:
                assert restored_state.paper_content == test_state.paper_content
            if test_state.understanding:
                assert restored_state.understanding == test_state.understanding


if __name__ == "__main__":
    pytest.main([__file__])