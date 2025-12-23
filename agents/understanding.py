"""
Paper Understanding Agent for the RASO platform.

Analyzes research paper content using LLM services to extract key insights,
identify problems, contributions, equations, and visualizable concepts.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from pydantic import BaseModel, Field

from agents.base import BaseAgent
from backend.models.paper import PaperContent, Equation, Section
from backend.models.understanding import (
    PaperUnderstanding,
    KeyEquation,
    VisualizableConcept,
)
from backend.services.llm import llm_service, LLMRequest
from agents.retry import retry


class UnderstandingPrompts:
    """Prompt templates for paper understanding tasks."""
    
    PROBLEM_ANALYSIS = """
    Analyze the following research paper and identify the core problem statement and research motivation.
    
    Paper Title: {title}
    Abstract: {abstract}
    
    Introduction Section:
    {introduction}
    
    Please provide:
    1. The main problem this research addresses
    2. Why this problem is important
    3. What gaps in existing work this research fills
    
    Format your response as a clear, concise problem statement (2-3 sentences).
    """
    
    CONTRIBUTION_EXTRACTION = """
    Extract the key contributions and novel insights from this research paper.
    
    Paper Title: {title}
    Abstract: {abstract}
    
    Full Paper Sections:
    {sections_text}
    
    Please identify:
    1. The main technical contributions
    2. Novel methods or approaches introduced
    3. Key findings or results
    4. Theoretical or practical advances
    
    List each contribution as a separate bullet point. Be specific and technical.
    """
    
    EQUATION_ANALYSIS = """
    Analyze the mathematical content in this research paper and identify key equations.
    
    Paper Title: {title}
    
    Equations found in the paper:
    {equations_text}
    
    For each equation, assess:
    1. Its importance to the main contribution (scale 1-10)
    2. Whether it's suitable for visual explanation
    3. What concepts it represents
    4. How it relates to the paper's main ideas
    
    Focus on equations that are:
    - Central to the paper's contribution
    - Novel or modified from existing work
    - Complex enough to benefit from visualization
    - Representative of key algorithmic steps
    
    Format as JSON:
    {{
        "key_equations": [
            {{
                "equation_id": "eq1",
                "importance": 8,
                "visualization_hint": "Show matrix multiplication steps",
                "related_concepts": ["attention", "transformer"]
            }}
        ]
    }}
    """
    
    CONCEPT_IDENTIFICATION = """
    Identify concepts and processes in this research paper that would benefit from visual animation.
    
    Paper Title: {title}
    Abstract: {abstract}
    
    Key Contributions:
    {contributions}
    
    Consider concepts that are:
    1. Abstract but can be made concrete through visualization
    2. Processes or algorithms with clear steps
    3. Architectural components or system designs
    4. Data flows or transformations
    5. Comparisons between approaches
    
    For each concept, determine:
    - Visualization type: animation, diagram, chart, or simulation
    - Complexity level: simple, medium, or complex
    - Related equations or technical details
    
    Format as JSON:
    {{
        "visualizable_concepts": [
            {{
                "name": "Self-Attention Mechanism",
                "description": "How tokens attend to other tokens",
                "visualization_type": "animation",
                "complexity": "medium",
                "related_equations": ["eq1", "eq2"]
            }}
        ]
    }}
    """


class UnderstandingAgent(BaseAgent):
    """Agent responsible for understanding and analyzing research papers."""
    
    name = "UnderstandingAgent"
    description = "Analyzes research papers to extract problems, contributions, and visualizable concepts"
    
    def __init__(self):
        """Initialize the understanding agent."""
        super().__init__()
        self.prompts = UnderstandingPrompts()
    
    @retry(max_attempts=3, base_delay=2.0)
    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute paper understanding analysis.
        
        Args:
            state: Current workflow state containing paper content
            
        Returns:
            Updated state with paper understanding
        """
        self.validate_input(state)
        
        try:
            paper_content = PaperContent(**state["paper_content"])
            
            self.log_progress("Starting paper understanding analysis", state)
            
            # Analyze problem statement
            problem = await self._analyze_problem(paper_content)
            
            # Extract contributions
            contributions = await self._extract_contributions(paper_content)
            
            # Analyze equations
            key_equations = await self._analyze_equations(paper_content)
            
            # Identify visualizable concepts
            visualizable_concepts = await self._identify_concepts(paper_content, contributions)
            
            # Create understanding object
            understanding = PaperUnderstanding(
                problem=problem,
                intuition=self._generate_intuition(problem, contributions),
                contributions=contributions,
                key_equations=key_equations,
                visualizable_concepts=visualizable_concepts,
            )
            
            # Update state
            state["understanding"] = understanding.dict()
            state["current_agent"] = "ScriptAgent"
            
            self.log_progress("Paper understanding analysis completed", state)
            
            return state
            
        except Exception as e:
            return self.handle_error(e, state)
    
    def validate_input(self, state: Dict[str, Any]) -> None:
        """Validate input state for understanding analysis."""
        if "paper_content" not in state:
            raise ValueError("Paper content not found in state")
        
        paper_content = state["paper_content"]
        
        if not paper_content.get("title"):
            raise ValueError("Paper title is required for understanding")
        
        if not paper_content.get("abstract"):
            raise ValueError("Paper abstract is required for understanding")
        
        if not paper_content.get("sections"):
            raise ValueError("Paper sections are required for understanding")
    
    async def _analyze_problem(self, paper_content: PaperContent) -> str:
        """Analyze and extract the core problem statement."""
        # Find introduction section
        introduction = ""
        for section in paper_content.sections:
            if any(keyword in section.title.lower() for keyword in ["introduction", "intro", "background"]):
                introduction = section.content
                break
        
        # If no introduction found, use first section
        if not introduction and paper_content.sections:
            introduction = paper_content.sections[0].content
        
        prompt = self.prompts.PROBLEM_ANALYSIS.format(
            title=paper_content.title,
            abstract=paper_content.abstract,
            introduction=introduction[:2000],  # Limit length
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=300,
        )
        
        return response.content.strip()
    
    async def _extract_contributions(self, paper_content: PaperContent) -> List[str]:
        """Extract key contributions from the paper."""
        # Combine relevant sections
        sections_text = ""
        for section in paper_content.sections:
            # Focus on key sections
            if any(keyword in section.title.lower() for keyword in [
                "contribution", "method", "approach", "result", "conclusion", "summary"
            ]):
                sections_text += f"\n\n{section.title}:\n{section.content}"
        
        # If no specific sections found, use all sections (truncated)
        if not sections_text:
            sections_text = "\n\n".join([
                f"{section.title}:\n{section.content[:500]}"
                for section in paper_content.sections[:3]
            ])
        
        prompt = self.prompts.CONTRIBUTION_EXTRACTION.format(
            title=paper_content.title,
            abstract=paper_content.abstract,
            sections_text=sections_text[:3000],  # Limit length
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=500,
        )
        
        # Parse contributions from response
        contributions = []
        for line in response.content.split('\n'):
            line = line.strip()
            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*')):
                # Remove bullet point and clean up
                contribution = re.sub(r'^[•\-\*]\s*', '', line).strip()
                if contribution:
                    contributions.append(contribution)
        
        # If no bullet points found, split by sentences
        if not contributions:
            sentences = response.content.split('.')
            contributions = [s.strip() for s in sentences if len(s.strip()) > 20][:5]
        
        return contributions[:5]  # Limit to 5 contributions
    
    async def _analyze_equations(self, paper_content: PaperContent) -> List[KeyEquation]:
        """Analyze equations and identify key ones for visualization."""
        if not paper_content.equations:
            return []
        
        # Prepare equations text
        equations_text = ""
        for eq in paper_content.equations:
            equations_text += f"\nEquation {eq.id}: {eq.latex}"
            if eq.description:
                equations_text += f" ({eq.description})"
        
        prompt = self.prompts.EQUATION_ANALYSIS.format(
            title=paper_content.title,
            equations_text=equations_text[:2000],
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.1,
            max_tokens=800,
        )
        
        # Parse JSON response
        try:
            import json
            result = json.loads(response.content)
            key_equations = []
            
            for eq_data in result.get("key_equations", []):
                # Validate equation exists
                equation_id = eq_data.get("equation_id")
                if any(eq.id == equation_id for eq in paper_content.equations):
                    key_equations.append(KeyEquation(
                        equation_id=equation_id,
                        importance=eq_data.get("importance", 5),
                        visualization_hint=eq_data.get("visualization_hint", ""),
                        related_concepts=eq_data.get("related_concepts", []),
                    ))
            
            return key_equations
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse equation analysis JSON: {e}")
            
            # Fallback: mark first few equations as key
            key_equations = []
            for i, eq in enumerate(paper_content.equations[:3]):
                key_equations.append(KeyEquation(
                    equation_id=eq.id,
                    importance=7,
                    visualization_hint="Mathematical visualization",
                    related_concepts=[],
                ))
            
            return key_equations
    
    async def _identify_concepts(
        self, 
        paper_content: PaperContent, 
        contributions: List[str]
    ) -> List[VisualizableConcept]:
        """Identify concepts suitable for visual animation."""
        contributions_text = "\n".join([f"- {contrib}" for contrib in contributions])
        
        prompt = self.prompts.CONCEPT_IDENTIFICATION.format(
            title=paper_content.title,
            abstract=paper_content.abstract,
            contributions=contributions_text,
        )
        
        response = await llm_service.generate(
            prompt=prompt,
            temperature=0.2,
            max_tokens=1000,
        )
        
        # Parse JSON response
        try:
            import json
            result = json.loads(response.content)
            concepts = []
            
            for concept_data in result.get("visualizable_concepts", []):
                concepts.append(VisualizableConcept(
                    name=concept_data.get("name", ""),
                    description=concept_data.get("description", ""),
                    visualization_type=concept_data.get("visualization_type", "animation"),
                    complexity=concept_data.get("complexity", "medium"),
                    related_equations=concept_data.get("related_equations", []),
                ))
            
            return concepts
            
        except (json.JSONDecodeError, KeyError) as e:
            self.logger.warning(f"Failed to parse concept identification JSON: {e}")
            
            # Fallback: create basic concepts from contributions
            concepts = []
            for i, contribution in enumerate(contributions[:3]):
                concepts.append(VisualizableConcept(
                    name=f"Concept {i+1}",
                    description=contribution,
                    visualization_type="animation",
                    complexity="medium",
                    related_equations=[],
                ))
            
            return concepts
    
    def _generate_intuition(self, problem: str, contributions: List[str]) -> str:
        """Generate intuitive explanation connecting problem to solution."""
        # Simple heuristic to generate intuition
        if not contributions:
            return f"This research addresses: {problem}"
        
        main_contribution = contributions[0] if contributions else "novel approach"
        
        intuition = f"The key insight is that {main_contribution.lower()}. "
        intuition += f"This addresses the problem by providing a new way to {problem.lower()}."
        
        return intuition
    
    async def analyze_problem_statement(self, paper_content: PaperContent) -> str:
        """
        Public method to analyze problem statement.
        
        Args:
            paper_content: Paper content to analyze
            
        Returns:
            Problem statement
        """
        return await self._analyze_problem(paper_content)
    
    async def extract_contributions(self, paper_content: PaperContent) -> List[str]:
        """
        Public method to extract contributions.
        
        Args:
            paper_content: Paper content to analyze
            
        Returns:
            List of contributions
        """
        return await self._extract_contributions(paper_content)
    
    async def identify_key_equations(self, paper_content: PaperContent) -> List[KeyEquation]:
        """
        Public method to identify key equations.
        
        Args:
            paper_content: Paper content to analyze
            
        Returns:
            List of key equations
        """
        return await self._analyze_equations(paper_content)
    
    async def find_visualizable_concepts(self, paper_content: PaperContent) -> List[VisualizableConcept]:
        """
        Public method to find visualizable concepts.
        
        Args:
            paper_content: Paper content to analyze
            
        Returns:
            List of visualizable concepts
        """
        contributions = await self._extract_contributions(paper_content)
        return await self._identify_concepts(paper_content, contributions)