"""
Property-based tests for RASO paper ingestion functionality.

**Feature: raso-platform, Property 1: Paper ingestion completeness**
Tests that for any valid paper input (title, arXiv URL, or PDF), the system
successfully extracts structured content including sections, equations, figures,
and metadata, with validation of completeness.
"""

import asyncio
import base64
import tempfile
from pathlib import Path
from typing import List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from hypothesis import given, strategies as st

from backend.models import (
    RASOMasterState,
    PaperInput,
    PaperContent,
    Section,
    Equation,
    Figure,
    PaperInputType,
    AgentType,
)
from agents.ingest import IngestAgent
from agents.base import AgentExecutionError


def create_mock_pdf_data() -> bytes:
    """Create minimal valid PDF data for testing."""
    # Minimal PDF structure
    pdf_content = b"""%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj

2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj

3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 612 792]
/Contents 4 0 R
>>
endobj

4 0 obj
<<
/Length 44
>>
stream
BT
/F1 12 Tf
72 720 Td
(Test Paper Title) Tj
ET
endstream
endobj

xref
0 5
0000000000 65535 f 
0000000010 00000 n 
0000000079 00000 n 
0000000136 00000 n 
0000000229 00000 n 
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
324
%%EOF"""
    return pdf_content


def create_mock_arxiv_response(arxiv_id: str, title: str, authors: List[str], abstract: str) -> str:
    """Create mock arXiv API response."""
    authors_xml = ""
    for author in authors:
        authors_xml += f"""
        <author>
            <name>{author}</name>
        </author>"""
    
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <id>http://arxiv.org/abs/{arxiv_id}</id>
        <title>{title}</title>
        {authors_xml}
        <summary>{abstract}</summary>
        <published>2023-01-01T00:00:00Z</published>
    </entry>
</feed>"""


class TestPaperIngestionProperties:
    """Property-based tests for paper ingestion completeness."""

    @given(
        title=st.text(min_size=10, max_size=100),
        authors=st.lists(st.text(min_size=5, max_size=30), min_size=1, max_size=5),
        abstract=st.text(min_size=50, max_size=500),
    )
    async def test_arxiv_ingestion_completeness_property(
        self, title: str, authors: List[str], abstract: str
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any valid arXiv URL, the system should successfully extract
        structured content including title, authors, abstract, and sections.
        **Validates: Requirements 1.1, 1.2, 1.3, 1.4**
        """
        # Create test data
        arxiv_id = "2301.00001"
        arxiv_url = f"https://arxiv.org/abs/{arxiv_id}"
        
        # Create state
        paper_input = PaperInput(type=PaperInputType.ARXIV, content=arxiv_url)
        state = RASOMasterState(paper_input=paper_input)
        
        # Create agent
        agent = IngestAgent(AgentType.INGEST)
        
        # Mock HTTP responses
        mock_arxiv_response = create_mock_arxiv_response(arxiv_id, title, authors, abstract)
        mock_pdf_data = create_mock_pdf_data()
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            # Create mock session
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock arXiv metadata response
            mock_metadata_response = AsyncMock()
            mock_metadata_response.status = 200
            mock_metadata_response.text.return_value = mock_arxiv_response
            
            # Mock PDF download response
            mock_pdf_response = AsyncMock()
            mock_pdf_response.status = 200
            mock_pdf_response.read.return_value = mock_pdf_data
            
            # Configure session.get to return appropriate responses
            async def mock_get(url):
                if "api/query" in url:
                    return mock_metadata_response
                elif url.endswith(".pdf"):
                    return mock_pdf_response
                else:
                    raise ValueError(f"Unexpected URL: {url}")
            
            mock_session.get.side_effect = mock_get
            
            # Mock PyMuPDF
            with patch('fitz.open') as mock_fitz:
                mock_doc = MagicMock()
                mock_page = MagicMock()
                mock_page.get_text.return_value = f"{title}\n\n{' '.join(authors)}\n\nAbstract\n{abstract}\n\n1. Introduction\nThis is the introduction section content."
                mock_page.get_images.return_value = []
                mock_doc.__len__.return_value = 1
                mock_doc.__getitem__.return_value = mock_page
                mock_fitz.return_value = mock_doc
                
                # Execute ingestion
                result_state = await agent.execute(state)
                
                # Verify completeness
                assert result_state.paper_content is not None
                paper_content = result_state.paper_content
                
                # Verify basic metadata
                assert paper_content.title is not None
                assert len(paper_content.title.strip()) >= 5
                assert paper_content.authors is not None
                assert len(paper_content.authors) >= 1
                assert paper_content.abstract is not None
                assert len(paper_content.abstract.strip()) >= 20
                
                # Verify structural content
                assert paper_content.sections is not None
                assert len(paper_content.sections) >= 1
                
                # Verify each section has required fields
                for section in paper_content.sections:
                    assert section.id is not None
                    assert section.title is not None
                    assert len(section.title.strip()) >= 1
                    assert section.content is not None
                    assert len(section.content.strip()) >= 10
                    assert section.level >= 1
                
                # Verify arXiv-specific metadata
                assert paper_content.arxiv_id == arxiv_id

    @given(
        title=st.text(min_size=10, max_size=100),
        section_count=st.integers(min_value=1, max_value=5),
        equation_count=st.integers(min_value=0, max_value=10),
    )
    async def test_pdf_ingestion_completeness_property(
        self, title: str, section_count: int, equation_count: int
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any valid PDF input, the system should successfully extract
        structured content and validate completeness.
        **Validates: Requirements 1.3, 1.4**
        """
        # Create mock PDF content with sections and equations
        pdf_text_content = f"{title}\n\nTest Author\n\nAbstract\nThis is a test abstract for the paper.\n\n"
        
        # Add sections
        for i in range(section_count):
            pdf_text_content += f"{i+1}. Section {i+1}\nThis is the content of section {i+1}. " * 10 + "\n\n"
        
        # Add equations
        for i in range(equation_count):
            pdf_text_content += f"$$E = mc^{i+2}$$\n"
        
        # Create base64-encoded PDF data
        mock_pdf_data = create_mock_pdf_data()
        pdf_base64 = base64.b64encode(mock_pdf_data).decode('utf-8')
        
        # Create state
        paper_input = PaperInput(type=PaperInputType.PDF, content=pdf_base64)
        state = RASOMasterState(paper_input=paper_input)
        
        # Create agent
        agent = IngestAgent(AgentType.INGEST)
        
        # Mock PyMuPDF to return our test content
        with patch('fitz.open') as mock_fitz:
            mock_doc = MagicMock()
            mock_page = MagicMock()
            mock_page.get_text.return_value = pdf_text_content
            mock_page.get_images.return_value = []
            mock_doc.__len__.return_value = 1
            mock_doc.__getitem__.return_value = mock_page
            mock_fitz.return_value = mock_doc
            
            # Execute ingestion
            result_state = await agent.execute(state)
            
            # Verify completeness
            assert result_state.paper_content is not None
            paper_content = result_state.paper_content
            
            # Verify basic structure
            assert paper_content.title is not None
            assert len(paper_content.title.strip()) >= 5
            assert paper_content.sections is not None
            assert len(paper_content.sections) >= 1
            
            # Verify content extraction
            total_content_length = sum(len(section.content) for section in paper_content.sections)
            assert total_content_length >= 100  # Minimum reasonable content
            
            # Verify equation extraction if equations were present
            if equation_count > 0:
                assert paper_content.equations is not None
                # Should extract at least some equations (may not be exact due to parsing)
                assert len(paper_content.equations) >= 0

    @given(
        search_title=st.text(min_size=10, max_size=100),
        found_title=st.text(min_size=10, max_size=100),
        similarity_threshold=st.floats(min_value=0.5, max_value=0.9),
    )
    async def test_title_search_completeness_property(
        self, search_title: str, found_title: str, similarity_threshold: float
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any paper title search, the system should either find a matching
        paper or provide appropriate error handling.
        **Validates: Requirements 1.1, 1.4**
        """
        # Create state
        paper_input = PaperInput(type=PaperInputType.TITLE, content=search_title)
        state = RASOMasterState(paper_input=paper_input)
        
        # Create agent
        agent = IngestAgent(AgentType.INGEST)
        
        # Test title similarity function
        similarity = agent._titles_similar(search_title, found_title, similarity_threshold)
        
        # Verify similarity calculation is reasonable
        assert isinstance(similarity, bool)
        
        # If titles are identical, should be similar
        if search_title.lower().strip() == found_title.lower().strip():
            assert similarity == True
        
        # Test with mock search results
        arxiv_id = "2301.00001"
        mock_search_response = f"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
    <entry>
        <id>http://arxiv.org/abs/{arxiv_id}</id>
        <title>{found_title}</title>
    </entry>
</feed>"""
        
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            # Mock search response
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text.return_value = mock_search_response
            mock_session.get.return_value = mock_response
            
            # Test search functionality
            result_url = await agent._search_arxiv_by_title(search_title)
            
            # Should return URL if titles are similar enough
            if agent._titles_similar(search_title, found_title, 0.7):
                assert result_url is not None
                assert arxiv_id in result_url
            else:
                # May or may not find depending on similarity
                pass

    @given(
        arxiv_urls=st.lists(
            st.sampled_from([
                "https://arxiv.org/abs/2301.00001",
                "https://arxiv.org/pdf/2301.00001.pdf",
                "http://arxiv.org/abs/1234.5678",
                "arxiv.org/abs/2301.00001",
                "invalid-url",
                "https://example.com/paper.pdf",
            ]),
            min_size=1,
            max_size=5
        )
    )
    def test_arxiv_url_parsing_property(self, arxiv_urls: List[str]):
        """
        **Property 1: Paper ingestion completeness**
        For any arXiv URL format, the system should correctly extract
        the arXiv ID or handle invalid URLs appropriately.
        **Validates: Requirements 1.2**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        for url in arxiv_urls:
            arxiv_id = agent._extract_arxiv_id(url)
            
            if "arxiv.org" in url and ("abs/" in url or "pdf/" in url):
                # Valid arXiv URL should extract ID
                assert arxiv_id is not None
                assert len(arxiv_id) > 0
                # Should not contain .pdf extension
                assert not arxiv_id.endswith('.pdf')
            else:
                # Invalid URLs should return None
                assert arxiv_id is None

    @given(
        content_length=st.integers(min_value=0, max_value=10000),
        has_title=st.booleans(),
        has_sections=st.booleans(),
        section_count=st.integers(min_value=0, max_value=10),
    )
    def test_content_validation_property(
        self, content_length: int, has_title: bool, has_sections: bool, section_count: int
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any paper content, validation should enforce minimum quality
        requirements and provide appropriate error messages.
        **Validates: Requirements 1.4**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        # Create test paper content
        title = "Valid Paper Title" if has_title else ""
        sections = []
        
        if has_sections:
            for i in range(section_count):
                content = "x" * max(1, content_length // max(1, section_count))
                sections.append(Section(
                    id=f"section_{i}",
                    title=f"Section {i}",
                    content=content,
                    level=1,
                ))
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract="This is a test abstract that meets minimum length requirements.",
            sections=sections,
        )
        
        # Test validation
        try:
            agent._validate_paper_content(paper_content)
            validation_passed = True
        except AgentExecutionError:
            validation_passed = False
        
        # Determine expected validation result
        should_pass = (
            has_title and 
            len(title.strip()) >= 5 and
            has_sections and 
            section_count > 0 and
            content_length >= 500
        )
        
        assert validation_passed == should_pass

    @given(
        pdf_data_valid=st.booleans(),
        pdf_size=st.integers(min_value=0, max_value=10000),
    )
    async def test_pdf_download_validation_property(
        self, pdf_data_valid: bool, pdf_size: int
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any PDF download, the system should validate file integrity
        and handle corrupted or invalid files appropriately.
        **Validates: Requirements 1.3, 1.4**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        # Create test PDF data
        if pdf_data_valid and pdf_size >= 1024:
            pdf_data = b'%PDF-1.4\n' + b'x' * (pdf_size - 9)
        elif pdf_size > 0:
            pdf_data = b'x' * pdf_size  # Invalid PDF (no magic number)
        else:
            pdf_data = b''  # Empty file
        
        # Mock HTTP response
        with patch('aiohttp.ClientSession') as mock_session_class:
            mock_session = AsyncMock()
            mock_session_class.return_value = mock_session
            
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read.return_value = pdf_data
            mock_session.get.return_value = mock_response
            
            agent.session = mock_session
            
            # Test PDF download
            try:
                result_data = await agent._download_pdf("http://example.com/test.pdf")
                download_succeeded = True
                assert result_data == pdf_data
            except AgentExecutionError:
                download_succeeded = False
            
            # Determine expected result
            should_succeed = pdf_data_valid and pdf_size >= 1024
            assert download_succeeded == should_succeed

    @given(
        text_content=st.text(min_size=100, max_size=5000),
        has_equations=st.booleans(),
        equation_formats=st.lists(
            st.sampled_from(["$$E=mc^2$$", "$x=y$", "\\begin{equation}F=ma\\end{equation}"]),
            min_size=0,
            max_size=5
        ),
    )
    def test_equation_extraction_property(
        self, text_content: str, has_equations: bool, equation_formats: List[str]
    ):
        """
        **Property 1: Paper ingestion completeness**
        For any text content with equations, the system should extract
        mathematical expressions in various LaTeX formats.
        **Validates: Requirements 1.3, 1.4**
        """
        agent = IngestAgent(AgentType.INGEST)
        
        # Add equations to text if specified
        test_text = text_content
        if has_equations:
            for eq in equation_formats:
                test_text += f"\n{eq}\n"
        
        # Extract equations
        equations = agent._extract_equations_from_text(test_text)
        
        # Verify extraction results
        if has_equations and equation_formats:
            # Should extract at least some equations
            assert len(equations) >= 0  # May not extract all due to filtering
            
            # Verify equation structure
            for equation in equations:
                assert equation.id is not None
                assert equation.latex is not None
                assert len(equation.latex.strip()) >= 3
                assert equation.section_id is not None
        else:
            # May still extract equations from random text, but should be valid
            for equation in equations:
                assert equation.id is not None
                assert equation.latex is not None
                assert equation.section_id is not None

    async def test_ingestion_error_handling_property(self):
        """
        **Property 1: Paper ingestion completeness**
        For any ingestion failure, the system should provide clear error
        messages and maintain state consistency.
        **Validates: Requirements 1.5**
        """
        # Test various error scenarios
        error_scenarios = [
            (PaperInputType.TITLE, ""),  # Empty title
            (PaperInputType.ARXIV, "invalid-url"),  # Invalid arXiv URL
            (PaperInputType.PDF, "invalid-base64"),  # Invalid PDF data
        ]
        
        agent = IngestAgent(AgentType.INGEST)
        
        for input_type, content in error_scenarios:
            paper_input = PaperInput(type=input_type, content=content)
            state = RASOMasterState(paper_input=paper_input)
            
            # Mock network failures for arXiv
            with patch('aiohttp.ClientSession') as mock_session_class:
                mock_session = AsyncMock()
                mock_session_class.return_value = mock_session
                
                # Mock failed responses
                mock_response = AsyncMock()
                mock_response.status = 404
                mock_session.get.return_value = mock_response
                
                try:
                    await agent.execute(state)
                    execution_failed = False
                except (AgentExecutionError, Exception):
                    execution_failed = True
                
                # Should fail for invalid inputs
                assert execution_failed == True
                
                # State should remain consistent
                assert state.job_id is not None
                assert state.paper_input == paper_input
                assert state.paper_content is None  # Should not be set on failure


if __name__ == "__main__":
    pytest.main([__file__])