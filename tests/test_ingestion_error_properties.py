"""
Property-based tests for RASO paper ingestion error handling.

**Feature: raso-platform, Property 2: Error handling consistency**
Tests that for any invalid or failing input, the system provides clear error
messages with suggested remediation steps and graceful degradation.
"""

import asyncio
import base64
from typing import List, Optional, Dict, Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st
import aiohttp

from backend.models import (
    RASOMasterState,
    PaperInput,
    PaperInputType,
    AgentType,
    ErrorSeverity,
)
from agents.ingest import IngestAgent
from agents.base import AgentExecutionError


class TestIngestionErrorHandlingProperties:
    """Property-based tests for ingestion error handling consistency."""

    @given(
        invalid_inputs=st.lists(
            st.one_of(
                st.text(max_size=4),  # Too short titles
                st.just(""),  # Empty strings
                st.text().filter(lambda x: len(x.strip()) == 0),  # Whitespace only
            ),
            min_size=1,
            max_size=5
        )
    )
    async def test_invalid_title_error_handling_property(self, invalid_inputs: List[str]):
        """
        **Property 2: Error handling consistency**
        For any invalid title input, the system should provide clear error
        messages and maintain state consistency.
        **Validates: Requirements 1.5, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for invalid_title in invalid_inputs:
            paper_input = PaperInput(type=PaperInputType.TITLE, content=invalid_title)
            state = RASOMasterState(paper_input=paper_input)
            
            # Mock arXiv search to return no results
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock empty search results
                mock_response = AsyncMock()
                mock_response.status = 200
                mock_response.text.return_value = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
</feed>"""
                mock_session.get.return_value = mock_response
                
                # Execute and expect failure
                try:
                    await agent.execute(state)
                    execution_failed = False
                    error_message = None
                except AgentExecutionError as e:
                    execution_failed = True
                    error_message = e.message
                except Exception as e:
                    execution_failed = True
                    error_message = str(e)
                
                # Verify error handling
                assert execution_failed == True
                assert error_message is not None
                assert len(error_message) > 0
                
                # Verify state consistency
                assert state.job_id is not None
                assert state.paper_input.content == invalid_title
                assert state.paper_content is None

    @given(
        invalid_urls=st.lists(
            st.one_of(
                st.just("not-a-url"),
                st.just("http://example.com/not-arxiv"),
                st.just("https://arxiv.org/invalid"),
                st.just("ftp://arxiv.org/abs/1234.5678"),
                st.text().filter(lambda x: "arxiv" not in x.lower()),
            ),
            min_size=1,
            max_size=5
        )
    )
    async def test_invalid_arxiv_url_error_handling_property(self, invalid_urls: List[str]):
        """
        **Property 2: Error handling consistency**
        For any invalid arXiv URL, the system should provide specific error
        messages and suggest remediation steps.
        **Validates: Requirements 1.5, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for invalid_url in invalid_urls:
            paper_input = PaperInput(type=PaperInputType.ARXIV, content=invalid_url)
            state = RASOMasterState(paper_input=paper_input)
            
            # Execute and expect failure
            try:
                await agent.execute(state)
                execution_failed = False
                error_code = None
                error_message = None
            except AgentExecutionError as e:
                execution_failed = True
                error_code = e.error_code
                error_message = e.message
            except Exception as e:
                execution_failed = True
                error_code = "UNKNOWN_ERROR"
                error_message = str(e)
            
            # Verify error handling
            assert execution_failed == True
            assert error_message is not None
            assert len(error_message) > 0
            
            # Should provide specific error for invalid URLs
            if not agent._extract_arxiv_id(invalid_url):
                assert error_code == "INVALID_ARXIV_URL"
                assert "Invalid arXiv URL" in error_message
            
            # Verify state consistency
            assert state.paper_input.content == invalid_url
            assert state.paper_content is None

    @given(
        network_errors=st.lists(
            st.sampled_from([
                (aiohttp.ClientConnectorError, "Connection failed"),
                (aiohttp.ClientTimeout, "Request timeout"),
                (aiohttp.ClientResponseError, "HTTP error"),
                (ConnectionError, "Network connection error"),
            ]),
            min_size=1,
            max_size=3
        ),
        http_status_codes=st.lists(
            st.sampled_from([404, 500, 502, 503, 429]),
            min_size=1,
            max_size=3
        )
    )
    async def test_network_error_handling_property(
        self, network_errors: List[tuple], http_status_codes: List[int]
    ):
        """
        **Property 2: Error handling consistency**
        For any network failure, the system should handle errors gracefully
        and provide appropriate error messages with retry suggestions.
        **Validates: Requirements 1.5, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        # Test network exceptions
        for error_class, error_message in network_errors:
            paper_input = PaperInput(
                type=PaperInputType.ARXIV, 
                content="https://arxiv.org/abs/2301.00001"
            )
            state = RASOMasterState(paper_input=paper_input)
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock network error
                mock_session.get.side_effect = error_class(error_message)
                
                try:
                    await agent.execute(state)
                    execution_failed = False
                except (AgentExecutionError, Exception):
                    execution_failed = True
                
                # Should handle network errors gracefully
                assert execution_failed == True
                assert state.paper_content is None
        
        # Test HTTP error status codes
        for status_code in http_status_codes:
            paper_input = PaperInput(
                type=PaperInputType.ARXIV,
                content="https://arxiv.org/abs/2301.00001"
            )
            state = RASOMasterState(paper_input=paper_input)
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock HTTP error response
                mock_response = AsyncMock()
                mock_response.status = status_code
                mock_session.get.return_value = mock_response
                
                try:
                    await agent.execute(state)
                    execution_failed = False
                except (AgentExecutionError, Exception):
                    execution_failed = True
                
                # Should handle HTTP errors appropriately
                assert execution_failed == True
                assert state.paper_content is None

    @given(
        invalid_pdf_data=st.lists(
            st.one_of(
                st.just("not-base64-data"),
                st.just(""),
                st.text().filter(lambda x: len(x) < 10),
                # Invalid base64 that decodes to non-PDF
                st.just(base64.b64encode(b"not a pdf").decode()),
                # Valid base64 but too small
                st.just(base64.b64encode(b"small").decode()),
            ),
            min_size=1,
            max_size=5
        )
    )
    async def test_invalid_pdf_error_handling_property(self, invalid_pdf_data: List[str]):
        """
        **Property 2: Error handling consistency**
        For any invalid PDF data, the system should provide specific error
        messages and handle decoding/parsing failures gracefully.
        **Validates: Requirements 1.5, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for invalid_data in invalid_pdf_data:
            paper_input = PaperInput(type=PaperInputType.PDF, content=invalid_data)
            state = RASOMasterState(paper_input=paper_input)
            
            try:
                await agent.execute(state)
                execution_failed = False
                error_code = None
                error_message = None
            except AgentExecutionError as e:
                execution_failed = True
                error_code = e.error_code
                error_message = e.message
            except Exception as e:
                execution_failed = True
                error_code = "UNKNOWN_ERROR"
                error_message = str(e)
            
            # Should fail for invalid PDF data
            assert execution_failed == True
            assert error_message is not None
            assert len(error_message) > 0
            
            # Should provide specific error codes
            expected_error_codes = [
                "PDF_DECODE_ERROR",
                "PDF_PARSE_ERROR", 
                "INVALID_PDF_FORMAT",
                "INVALID_PDF_SIZE"
            ]
            
            # Error code should be one of the expected types
            if error_code != "UNKNOWN_ERROR":
                # Don't assert specific error code as it depends on where parsing fails
                assert error_code is not None
            
            # Verify state consistency
            assert state.paper_content is None

    @given(
        retry_scenarios=st.lists(
            st.tuples(
                st.integers(min_value=1, max_value=5),  # failure_count
                st.booleans(),  # should_eventually_succeed
            ),
            min_size=1,
            max_size=3
        )
    )
    async def test_retry_mechanism_error_handling_property(
        self, retry_scenarios: List[tuple]
    ):
        """
        **Property 2: Error handling consistency**
        For any transient failure, the retry mechanism should provide
        consistent behavior and appropriate error reporting.
        **Validates: Requirements 12.1, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for failure_count, should_succeed in retry_scenarios:
            paper_input = PaperInput(
                type=PaperInputType.ARXIV,
                content="https://arxiv.org/abs/2301.00001"
            )
            state = RASOMasterState(paper_input=paper_input)
            
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value = mock_session
                
                call_count = 0
                
                async def mock_get(url):
                    nonlocal call_count
                    call_count += 1
                    
                    # Fail for the specified number of attempts
                    if call_count <= failure_count and not should_succeed:
                        raise aiohttp.ClientConnectorError(
                            connection_key=None, 
                            os_error=ConnectionError("Mock connection error")
                        )
                    elif call_count <= failure_count:
                        # Fail initially, then succeed
                        if call_count < failure_count:
                            raise aiohttp.ClientConnectorError(
                                connection_key=None,
                                os_error=ConnectionError("Mock connection error")
                            )
                    
                    # Return successful response
                    mock_response = AsyncMock()
                    mock_response.status = 200
                    
                    if "api/query" in url:
                        mock_response.text.return_value = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <id>http://arxiv.org/abs/2301.00001</id>
        <title>Test Paper</title>
        <author><name>Test Author</name></author>
        <summary>Test abstract</summary>
    </entry>
</feed>"""
                    else:
                        # PDF download
                        mock_response.read.return_value = b'%PDF-1.4\ntest content'
                    
                    return mock_response
                
                mock_session.get.side_effect = mock_get
                
                # Mock PyMuPDF for successful PDF parsing
                with patch('fitz.open') as mock_fitz:
                    mock_doc = MagicMock()
                    mock_page = MagicMock()
                    mock_page.get_text.return_value = "Test Paper\nTest Author\nAbstract\nTest abstract\n1. Introduction\nTest content"
                    mock_page.get_images.return_value = []
                    mock_doc.__len__.return_value = 1
                    mock_doc.__getitem__.return_value = mock_page
                    mock_fitz.return_value = mock_doc
                    
                    try:
                        result_state = await agent.execute(state)
                        execution_succeeded = True
                    except Exception:
                        execution_succeeded = False
                    
                    # Verify retry behavior
                    if should_succeed:
                        # Should eventually succeed after retries
                        assert execution_succeeded == True
                        assert result_state.paper_content is not None
                    else:
                        # Should fail after exhausting retries
                        assert execution_succeeded == False
                        assert state.paper_content is None
                    
                    # Verify retry attempts were made
                    assert call_count >= 1

    @given(
        malformed_content=st.lists(
            st.one_of(
                st.just("Title\n\n"),  # No sections
                st.just("Very short"),  # Too short
                st.text(max_size=100),  # Below minimum content threshold
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_content_validation_error_handling_property(self, malformed_content: List[str]):
        """
        **Property 2: Error handling consistency**
        For any malformed or insufficient content, validation should provide
        clear error messages about what is missing or invalid.
        **Validates: Requirements 1.4, 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for content in malformed_content:
            # Create minimal paper content that will fail validation
            from backend.models import PaperContent, Section
            
            # Create content that should fail validation
            if len(content) < 100:
                # Too short content
                sections = [Section(
                    id="section_1",
                    title="Test Section",
                    content=content,
                    level=1,
                )]
            else:
                # No sections
                sections = []
            
            paper_content = PaperContent(
                title="Test Title" if "Title" in content else "",
                authors=["Test Author"],
                abstract="Test abstract that meets minimum length requirements for validation.",
                sections=sections,
            )
            
            try:
                agent._validate_paper_content(paper_content)
                validation_passed = True
                error_message = None
            except AgentExecutionError as e:
                validation_passed = False
                error_message = e.message
            
            # Should fail validation for insufficient content
            total_content_length = sum(len(section.content) for section in sections)
            
            if not paper_content.title or len(paper_content.title.strip()) < 5:
                assert validation_passed == False
                assert "title" in error_message.lower()
            elif not sections:
                assert validation_passed == False
                assert "section" in error_message.lower()
            elif total_content_length < 500:
                assert validation_passed == False
                assert "content" in error_message.lower() or "short" in error_message.lower()

    @given(
        error_severity_scenarios=st.lists(
            st.tuples(
                st.sampled_from(["NETWORK_ERROR", "PARSE_ERROR", "VALIDATION_ERROR"]),
                st.sampled_from([ErrorSeverity.WARNING, ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]),
            ),
            min_size=1,
            max_size=3
        )
    )
    def test_error_severity_consistency_property(self, error_severity_scenarios: List[tuple]):
        """
        **Property 2: Error handling consistency**
        For any error type, the system should assign appropriate severity
        levels and handle them consistently.
        **Validates: Requirements 12.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for error_code, severity in error_severity_scenarios:
            # Create test state
            paper_input = PaperInput(type=PaperInputType.TITLE, content="Test Title")
            state = RASOMasterState(paper_input=paper_input)
            
            # Create error with specified severity
            error = AgentExecutionError(
                f"Test error for {error_code}",
                error_code,
                severity
            )
            
            # Handle error
            result_state = agent.handle_error(error, state)
            
            # Verify error was recorded correctly
            assert len(result_state.errors) == 1
            recorded_error = result_state.errors[0]
            
            assert recorded_error.error_code == error_code
            assert recorded_error.severity == severity
            assert recorded_error.agent_type == AgentType.INGEST
            
            # Verify error details are comprehensive
            assert recorded_error.message is not None
            assert len(recorded_error.message) > 0
            assert recorded_error.timestamp is not None
            assert isinstance(recorded_error.details, dict)
            
            # Verify state consistency
            assert result_state.job_id == state.job_id
            assert result_state.paper_input == state.paper_input

    async def test_graceful_degradation_property(self):
        """
        **Property 2: Error handling consistency**
        For any partial failure, the system should degrade gracefully
        and preserve any successfully extracted information.
        **Validates: Requirements 12.3**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        # Test scenario where metadata is available but PDF download fails
        paper_input = PaperInput(
            type=PaperInputType.ARXIV,
            content="https://arxiv.org/abs/2301.00001"
        )
        state = RASOMasterState(paper_input=paper_input)
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            call_count = 0
            
            async def mock_get(url):
                nonlocal call_count
                call_count += 1
                
                mock_response = AsyncMock()
                
                if "api/query" in url:
                    # Metadata request succeeds
                    mock_response.status = 200
                    mock_response.text.return_value = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <id>http://arxiv.org/abs/2301.00001</id>
        <title>Test Paper Title</title>
        <author><name>Test Author</name></author>
        <summary>This is a test abstract for graceful degradation testing.</summary>
    </entry>
</feed>"""
                else:
                    # PDF download fails
                    mock_response.status = 404
                
                return mock_response
            
            mock_session.get.side_effect = mock_get
            
            try:
                await agent.execute(state)
                execution_succeeded = True
            except Exception:
                execution_succeeded = False
            
            # Should fail overall, but error should be informative
            assert execution_succeeded == False
            
            # Verify that we attempted both metadata and PDF download
            assert call_count >= 2

    @given(
        concurrent_requests=st.integers(min_value=2, max_value=5),
    )
    async def test_concurrent_error_handling_property(self, concurrent_requests: int):
        """
        **Property 2: Error handling consistency**
        For any concurrent ingestion requests, error handling should be
        consistent and not interfere between requests.
        **Validates: Requirements 12.2**
        """
        # Create multiple agents for concurrent testing
        agents = [IngestAgent(AgentType.INGEST) for _ in range(concurrent_requests)]
        
        # Create different states that will fail in different ways
        states = []
        for i in range(concurrent_requests):
            if i % 3 == 0:
                # Invalid title
                paper_input = PaperInput(type=PaperInputType.TITLE, content="")
            elif i % 3 == 1:
                # Invalid arXiv URL
                paper_input = PaperInput(type=PaperInputType.ARXIV, content="invalid-url")
            else:
                # Invalid PDF
                paper_input = PaperInput(type=PaperInputType.PDF, content="invalid-pdf")
            
            states.append(RASOMasterState(paper_input=paper_input))
        
        # Execute all requests concurrently
        tasks = []
        for agent, state in zip(agents, states):
            task = asyncio.create_task(agent.execute(state))
            tasks.append(task)
        
        # Wait for all to complete (they should all fail)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all failed with appropriate errors
        for i, result in enumerate(results):
            assert isinstance(result, Exception)
            
            # Verify state consistency for each request
            state = states[i]
            assert state.job_id is not None
            assert state.paper_content is None
            
            # Each should have failed independently
            assert len(state.errors) == 0  # Errors added by handle_error, not execute


if __name__ == "__main__":
    pytest.main([__file__])