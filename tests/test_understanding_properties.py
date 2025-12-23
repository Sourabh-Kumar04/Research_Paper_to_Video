"""
Property-based tests for RASO paper understanding agent completeness.

**Feature: raso-platform, Property 3: Paper understanding completeness**
Tests that for any successfully ingested paper, the understanding phase produces
a complete analysis including problem statement, contributions, key equations, and visualizable concepts.
"""

import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock, patch

import pytest
from hypothesis import given, strategies as st

from agents.understanding import UnderstandingAgent
from backend.models.paper import PaperContent, Section, Equation, Figure, Reference
from backend.models.understanding import PaperUnderstanding, KeyEquation, VisualizableConcept
from backend.services.llm import LLMResponse, LLMProvider


class TestUnderstandingCompletenessProperties:
    """Property-based tests for understanding agent completeness."""

    @given(
        title=st.text(min_size=10, max_size=200),
        abstract=st.text(min_size=50, max_size=1000),
        num_sections=st.integers(min_value=1, max_value=10),
        num_equations=st.integers(min_value=0, max_value=5),
    )
    @pytest.mark.asyncio
    async def test_understanding_completeness_property(
        self, title: str, abstract: str, num_sections: int, num_equations: int
    ):
        """
        **Property 3: Paper understanding completeness**
        For any successfully ingested paper with title, abstract, and sections,
        the understanding phase should produce a complete analysis with all required components.
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        agent = UnderstandingAgent()
        
        # Generate test paper content
        sections = []
        for i in range(num_sections):
            sections.append(Section(
                id=f"section_{i}",
                title=f"Section {i+1}",
                content=f"This is the content of section {i+1}. " * 10,
                level=1,
                equations=[],
                figures=[],
            ))
        
        equations = []
        for i in range(num_equations):
            equations.append(Equation(
                id=f"eq_{i}",
                latex=f"x_{i} = y_{i} + z_{i}",
                description=f"Equation {i+1} description",
                section_id=f"section_0",
                is_key=True,
            ))
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract=abstract,
            sections=sections,
            equations=equations,
            figures=[],
            references=[],
        )
        
        # Mock LLM responses
        mock_responses = {
            "problem": "This research addresses the fundamental challenge of...",
            "contributions": "• Novel algorithm for processing\n• Improved performance metrics\n• Theoretical analysis",
            "equations": json.dumps({
                "key_equations": [
                    {
                        "equation_id": f"eq_{i}",
                        "importance": 8,
                        "visualization_hint": f"Show equation {i} steps",
                        "related_concepts": ["concept1", "concept2"]
                    }
                    for i in range(min(num_equations, 3))
                ]
            }),
            "concepts": json.dumps({
                "visualizable_concepts": [
                    {
                        "name": "Test Concept 1",
                        "description": "A visualizable concept for testing",
                        "visualization_type": "animation",
                        "complexity": "medium",
                        "related_equations": [f"eq_0"] if num_equations > 0 else []
                    },
                    {
                        "name": "Test Concept 2", 
                        "description": "Another visualizable concept",
                        "visualization_type": "diagram",
                        "complexity": "simple",
                        "related_equations": []
                    }
                ]
            })
        }
        
        # Mock LLM service calls
        call_count = 0
        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            responses = [
                mock_responses["problem"],
                mock_responses["contributions"],
                mock_responses["equations"],
                mock_responses["concepts"]
            ]
            response_content = responses[call_count % len(responses)]
            call_count += 1
            
            return LLMResponse(
                content=response_content,
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
        
        with patch('agents.understanding.llm_service.generate', side_effect=mock_generate):
            # Execute understanding analysis
            state = {"paper_content": paper_content.dict()}
            result_state = await agent.execute(state)
            
            # Verify completeness of understanding
            assert "understanding" in result_state
            understanding_data = result_state["understanding"]
            understanding = PaperUnderstanding(**understanding_data)
            
            # Verify all required components are present and non-empty
            assert understanding.problem is not None
            assert len(understanding.problem.strip()) > 0
            
            assert understanding.intuition is not None
            assert len(understanding.intuition.strip()) > 0
            
            assert understanding.contributions is not None
            assert len(understanding.contributions) > 0
            assert all(len(contrib.strip()) > 0 for contrib in understanding.contributions)
            
            assert understanding.key_equations is not None
            # Should have key equations if paper has equations
            if num_equations > 0:
                assert len(understanding.key_equations) > 0
                for key_eq in understanding.key_equations:
                    assert key_eq.equation_id is not None
                    assert key_eq.importance > 0
                    assert key_eq.visualization_hint is not None
            
            assert understanding.visualizable_concepts is not None
            assert len(understanding.visualizable_concepts) > 0
            for concept in understanding.visualizable_concepts:
                assert concept.name is not None
                assert len(concept.name.strip()) > 0
                assert concept.description is not None
                assert len(concept.description.strip()) > 0
                assert concept.visualization_type in ["animation", "diagram", "chart", "simulation"]
                assert concept.complexity in ["simple", "medium", "complex"]

    @given(
        sections_with_keywords=st.lists(
            st.tuples(
                st.sampled_from(["Introduction", "Method", "Results", "Conclusion", "Background"]),
                st.text(min_size=50, max_size=500)
            ),
            min_size=1,
            max_size=5
        ),
        title=st.text(min_size=10, max_size=100),
        abstract=st.text(min_size=50, max_size=300),
    )
    @pytest.mark.asyncio
    async def test_problem_analysis_completeness_property(
        self, sections_with_keywords: List[tuple], title: str, abstract: str
    ):
        """
        **Property 3: Paper understanding completeness**
        For any paper with identifiable sections, the problem analysis should
        extract a meaningful problem statement from the content.
        **Validates: Requirements 2.1**
        """
        agent = UnderstandingAgent()
        
        # Create sections from test data
        sections = []
        for i, (section_title, content) in enumerate(sections_with_keywords):
            sections.append(Section(
                id=f"section_{i}",
                title=section_title,
                content=content,
                level=1,
                equations=[],
                figures=[],
            ))
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract=abstract,
            sections=sections,
            equations=[],
            figures=[],
            references=[],
        )
        
        # Mock LLM response for problem analysis
        mock_problem = "This research addresses the challenge of improving computational efficiency in large-scale systems."
        
        with patch('agents.understanding.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=mock_problem,
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test problem analysis
            problem = await agent.analyze_problem_statement(paper_content)
            
            # Verify problem statement completeness
            assert problem is not None
            assert len(problem.strip()) > 0
            assert len(problem.split()) >= 5  # At least 5 words
            
            # Verify LLM was called with appropriate prompt
            mock_generate.assert_called_once()
            call_args = mock_generate.call_args
            prompt = call_args[1]["prompt"] if "prompt" in call_args[1] else call_args[0][0]
            
            # Verify prompt contains paper information
            assert title in prompt
            assert abstract in prompt

    @given(
        contributions_text=st.lists(st.text(min_size=20, max_size=200), min_size=1, max_size=10),
        title=st.text(min_size=10, max_size=100),
        abstract=st.text(min_size=50, max_size=300),
    )
    @pytest.mark.asyncio
    async def test_contribution_extraction_completeness_property(
        self, contributions_text: List[str], title: str, abstract: str
    ):
        """
        **Property 3: Paper understanding completeness**
        For any paper content, the contribution extraction should identify
        and structure the key contributions from the research.
        **Validates: Requirements 2.2**
        """
        agent = UnderstandingAgent()
        
        # Create paper with method/results sections
        sections = [
            Section(
                id="method",
                title="Method",
                content="Our approach introduces several key innovations...",
                level=1,
                equations=[],
                figures=[],
            ),
            Section(
                id="results",
                title="Results",
                content="The experimental results demonstrate significant improvements...",
                level=1,
                equations=[],
                figures=[],
            ),
        ]
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract=abstract,
            sections=sections,
            equations=[],
            figures=[],
            references=[],
        )
        
        # Mock LLM response with bullet points
        mock_contributions = "\n".join([f"• {contrib}" for contrib in contributions_text[:5]])
        
        with patch('agents.understanding.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=mock_contributions,
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test contribution extraction
            contributions = await agent.extract_contributions(paper_content)
            
            # Verify contributions completeness
            assert contributions is not None
            assert len(contributions) > 0
            assert len(contributions) <= 5  # Should limit to 5 contributions
            
            # Verify each contribution is meaningful
            for contrib in contributions:
                assert contrib is not None
                assert len(contrib.strip()) > 0
                assert len(contrib.split()) >= 3  # At least 3 words

    @given(
        equations_data=st.lists(
            st.tuples(
                st.text(min_size=5, max_size=50, alphabet="abcdefghijklmnopqrstuvwxyz0123456789=+\\"),
                st.text(min_size=10, max_size=100)
            ),
            min_size=1,
            max_size=5
        ),
        title=st.text(min_size=10, max_size=100),
    )
    @pytest.mark.asyncio
    async def test_equation_analysis_completeness_property(
        self, equations_data: List[tuple], title: str
    ):
        """
        **Property 3: Paper understanding completeness**
        For any paper with equations, the equation analysis should identify
        key equations with importance scores and visualization hints.
        **Validates: Requirements 2.3**
        """
        agent = UnderstandingAgent()
        
        # Create equations from test data
        equations = []
        for i, (latex, description) in enumerate(equations_data):
            equations.append(Equation(
                id=f"eq_{i}",
                latex=latex,
                description=description,
                section_id="section_0",
                is_key=True,
            ))
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract="Test abstract",
            sections=[Section(
                id="section_0",
                title="Main Section",
                content="Content with equations",
                level=1,
                equations=[eq.id for eq in equations],
                figures=[],
            )],
            equations=equations,
            figures=[],
            references=[],
        )
        
        # Mock LLM response with equation analysis
        mock_analysis = {
            "key_equations": [
                {
                    "equation_id": f"eq_{i}",
                    "importance": 7 + i,
                    "visualization_hint": f"Show steps for equation {i}",
                    "related_concepts": ["concept1", "concept2"]
                }
                for i in range(len(equations_data))
            ]
        }
        
        with patch('agents.understanding.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=json.dumps(mock_analysis),
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test equation analysis
            key_equations = await agent.identify_key_equations(paper_content)
            
            # Verify equation analysis completeness
            assert key_equations is not None
            assert len(key_equations) > 0
            
            # Verify each key equation has required properties
            for key_eq in key_equations:
                assert key_eq.equation_id is not None
                assert any(eq.id == key_eq.equation_id for eq in equations)  # Valid equation ID
                assert key_eq.importance > 0
                assert key_eq.importance <= 10
                assert key_eq.visualization_hint is not None
                assert len(key_eq.visualization_hint.strip()) > 0
                assert key_eq.related_concepts is not None

    @given(
        num_concepts=st.integers(min_value=1, max_value=5),
        title=st.text(min_size=10, max_size=100),
        abstract=st.text(min_size=50, max_size=300),
    )
    @pytest.mark.asyncio
    async def test_concept_identification_completeness_property(
        self, num_concepts: int, title: str, abstract: str
    ):
        """
        **Property 3: Paper understanding completeness**
        For any paper content, the concept identification should find
        visualizable concepts with proper categorization and complexity assessment.
        **Validates: Requirements 2.4, 2.5**
        """
        agent = UnderstandingAgent()
        
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract=abstract,
            sections=[Section(
                id="section_0",
                title="Main Section",
                content="This section describes the main concepts and approaches.",
                level=1,
                equations=[],
                figures=[],
            )],
            equations=[],
            figures=[],
            references=[],
        )
        
        # Mock LLM response with concepts
        mock_concepts = {
            "visualizable_concepts": [
                {
                    "name": f"Concept {i+1}",
                    "description": f"Description of concept {i+1} for visualization",
                    "visualization_type": ["animation", "diagram", "chart"][i % 3],
                    "complexity": ["simple", "medium", "complex"][i % 3],
                    "related_equations": []
                }
                for i in range(num_concepts)
            ]
        }
        
        with patch('agents.understanding.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=json.dumps(mock_concepts),
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test concept identification
            concepts = await agent.find_visualizable_concepts(paper_content)
            
            # Verify concept identification completeness
            assert concepts is not None
            assert len(concepts) > 0
            
            # Verify each concept has required properties
            for concept in concepts:
                assert concept.name is not None
                assert len(concept.name.strip()) > 0
                
                assert concept.description is not None
                assert len(concept.description.strip()) > 0
                
                assert concept.visualization_type in ["animation", "diagram", "chart", "simulation"]
                assert concept.complexity in ["simple", "medium", "complex"]
                assert concept.related_equations is not None

    @given(
        invalid_json_response=st.text(min_size=10, max_size=200),
        title=st.text(min_size=10, max_size=100),
    )
    @pytest.mark.asyncio
    async def test_fallback_handling_completeness_property(
        self, invalid_json_response: str, title: str
    ):
        """
        **Property 3: Paper understanding completeness**
        For any invalid or malformed LLM response, the understanding agent should
        provide fallback analysis to maintain completeness of the understanding phase.
        **Validates: Requirements 2.1, 2.2, 2.3, 2.4, 2.5**
        """
        agent = UnderstandingAgent()
        
        # Create minimal paper content
        paper_content = PaperContent(
            title=title,
            authors=["Test Author"],
            abstract="Test abstract for fallback testing",
            sections=[Section(
                id="section_0",
                title="Main Section",
                content="Content for fallback testing",
                level=1,
                equations=["eq_0"],
                figures=[],
            )],
            equations=[Equation(
                id="eq_0",
                latex="x = y + z",
                description="Test equation",
                section_id="section_0",
                is_key=True,
            )],
            figures=[],
            references=[],
        )
        
        # Mock LLM to return invalid JSON (should trigger fallback)
        with patch('agents.understanding.llm_service.generate') as mock_generate:
            mock_generate.return_value = LLMResponse(
                content=invalid_json_response,  # Invalid JSON
                model="test-model",
                provider=LLMProvider.OLLAMA,
                response_time=1.0,
            )
            
            # Test equation analysis with fallback
            key_equations = await agent.identify_key_equations(paper_content)
            
            # Should still return results via fallback
            assert key_equations is not None
            if paper_content.equations:
                assert len(key_equations) > 0
                
                # Verify fallback creates valid key equations
                for key_eq in key_equations:
                    assert key_eq.equation_id is not None
                    assert key_eq.importance > 0
                    assert key_eq.visualization_hint is not None
            
            # Test concept identification with fallback
            concepts = await agent.find_visualizable_concepts(paper_content)
            
            # Should still return results via fallback
            assert concepts is not None
            # Fallback should create concepts from contributions (which may be empty in fallback)


if __name__ == "__main__":
    pytest.main([__file__])