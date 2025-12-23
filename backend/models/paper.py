"""
Paper-related data models for the RASO platform.

Models for paper input, content extraction, and structured representation
of research papers including sections, equations, figures, and references.
"""

from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field, validator, HttpUrl


class PaperInputType(str, Enum):
    """Types of paper input supported by RASO."""
    TITLE = "title"
    ARXIV = "arxiv"
    PDF = "pdf"


class PaperInput(BaseModel):
    """Input specification for a research paper."""
    
    type: PaperInputType = Field(..., description="Type of paper input")
    content: str = Field(..., description="Paper content (title, URL, or base64 PDF)")
    options: Optional[Dict[str, Any]] = Field(default=None, description="Processing options")
    
    @validator("content")
    def validate_content(cls, v, values):
        """Validate content based on input type."""
        input_type = values.get("type")
        
        if input_type == PaperInputType.TITLE:
            if len(v.strip()) < 5:
                raise ValueError("Paper title must be at least 5 characters")
        elif input_type == PaperInputType.ARXIV:
            if not ("arxiv.org" in v.lower() or v.startswith("http")):
                raise ValueError("arXiv input must be a valid URL")
        elif input_type == PaperInputType.PDF:
            if not v:
                raise ValueError("PDF content cannot be empty")
        
        return v
    
    class Config:
        schema_extra = {
            "examples": [
                {
                    "type": "title",
                    "content": "Attention Is All You Need",
                    "options": {"search_limit": 5}
                },
                {
                    "type": "arxiv", 
                    "content": "https://arxiv.org/abs/1706.03762",
                    "options": {"include_figures": True}
                },
                {
                    "type": "pdf",
                    "content": "base64_encoded_pdf_data...",
                    "options": {"extract_equations": True}
                }
            ]
        }


class Section(BaseModel):
    """A section within a research paper."""
    
    id: str = Field(..., description="Unique section identifier")
    title: str = Field(..., description="Section title")
    content: str = Field(..., description="Section text content")
    level: int = Field(..., ge=1, le=6, description="Section hierarchy level")
    equations: List[str] = Field(default_factory=list, description="Equation IDs in this section")
    figures: List[str] = Field(default_factory=list, description="Figure IDs in this section")
    
    @validator("title")
    def validate_title(cls, v):
        """Validate section title."""
        if not v.strip():
            raise ValueError("Section title cannot be empty")
        return v.strip()
    
    @validator("content")
    def validate_content(cls, v):
        """Validate section content."""
        if len(v.strip()) < 10:
            raise ValueError("Section content must be at least 10 characters")
        return v.strip()


class Equation(BaseModel):
    """A mathematical equation within a research paper."""
    
    id: str = Field(..., description="Unique equation identifier")
    latex: str = Field(..., description="LaTeX representation of the equation")
    description: Optional[str] = Field(default=None, description="Human-readable description")
    section_id: str = Field(..., description="ID of the containing section")
    is_key: bool = Field(default=False, description="Whether this is a key equation for visualization")
    
    @validator("latex")
    def validate_latex(cls, v):
        """Validate LaTeX equation."""
        if not v.strip():
            raise ValueError("LaTeX equation cannot be empty")
        # Basic LaTeX validation
        if not any(char in v for char in ["=", "\\", "{", "}"]):
            raise ValueError("Invalid LaTeX equation format")
        return v.strip()


class FigureType(str, Enum):
    """Types of figures in research papers."""
    DIAGRAM = "diagram"
    CHART = "chart"
    PHOTO = "photo"
    ILLUSTRATION = "illustration"
    PLOT = "plot"
    TABLE = "table"


class Figure(BaseModel):
    """A figure within a research paper."""
    
    id: str = Field(..., description="Unique figure identifier")
    caption: str = Field(..., description="Figure caption")
    image_data: Optional[bytes] = Field(default=None, description="Binary image data")
    image_path: Optional[Path] = Field(default=None, description="Path to image file")
    section_id: str = Field(..., description="ID of the containing section")
    type: FigureType = Field(default=FigureType.DIAGRAM, description="Type of figure")
    
    @validator("caption")
    def validate_caption(cls, v):
        """Validate figure caption."""
        if len(v.strip()) < 5:
            raise ValueError("Figure caption must be at least 5 characters")
        return v.strip()
    
    class Config:
        arbitrary_types_allowed = True


class Reference(BaseModel):
    """A bibliographic reference within a research paper."""
    
    id: str = Field(..., description="Unique reference identifier")
    title: str = Field(..., description="Reference title")
    authors: List[str] = Field(..., description="List of authors")
    year: Optional[int] = Field(default=None, description="Publication year")
    venue: Optional[str] = Field(default=None, description="Publication venue")
    url: Optional[HttpUrl] = Field(default=None, description="Reference URL")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier")
    
    @validator("authors")
    def validate_authors(cls, v):
        """Validate authors list."""
        if not v:
            raise ValueError("At least one author is required")
        return [author.strip() for author in v if author.strip()]
    
    @validator("year")
    def validate_year(cls, v):
        """Validate publication year."""
        if v is not None:
            current_year = datetime.now().year
            if v < 1900 or v > current_year + 1:
                raise ValueError(f"Year must be between 1900 and {current_year + 1}")
        return v


class PaperContent(BaseModel):
    """Complete structured content of a research paper."""
    
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(..., description="List of paper authors")
    abstract: str = Field(..., description="Paper abstract")
    sections: List[Section] = Field(..., description="Paper sections")
    equations: List[Equation] = Field(default_factory=list, description="Mathematical equations")
    figures: List[Figure] = Field(default_factory=list, description="Figures and images")
    references: List[Reference] = Field(default_factory=list, description="Bibliographic references")
    
    # Metadata
    arxiv_id: Optional[str] = Field(default=None, description="arXiv identifier")
    doi: Optional[str] = Field(default=None, description="Digital Object Identifier")
    publication_date: Optional[datetime] = Field(default=None, description="Publication date")
    keywords: List[str] = Field(default_factory=list, description="Paper keywords")
    
    @validator("title")
    def validate_title(cls, v):
        """Validate paper title."""
        if len(v.strip()) < 5:
            raise ValueError("Paper title must be at least 5 characters")
        return v.strip()
    
    @validator("authors")
    def validate_authors(cls, v):
        """Validate authors list."""
        if not v:
            raise ValueError("At least one author is required")
        return [author.strip() for author in v if author.strip()]
    
    @validator("abstract")
    def validate_abstract(cls, v):
        """Validate paper abstract."""
        if len(v.strip()) < 50:
            raise ValueError("Abstract must be at least 50 characters")
        return v.strip()
    
    @validator("sections")
    def validate_sections(cls, v):
        """Validate sections list."""
        if not v:
            raise ValueError("At least one section is required")
        
        # Check for duplicate section IDs
        section_ids = [section.id for section in v]
        if len(section_ids) != len(set(section_ids)):
            raise ValueError("Section IDs must be unique")
        
        return v
    
    def get_section_by_id(self, section_id: str) -> Optional[Section]:
        """Get a section by its ID."""
        for section in self.sections:
            if section.id == section_id:
                return section
        return None
    
    def get_equation_by_id(self, equation_id: str) -> Optional[Equation]:
        """Get an equation by its ID."""
        for equation in self.equations:
            if equation.id == equation_id:
                return equation
        return None
    
    def get_figure_by_id(self, figure_id: str) -> Optional[Figure]:
        """Get a figure by its ID."""
        for figure in self.figures:
            if figure.id == figure_id:
                return figure
        return None
    
    def get_key_equations(self) -> List[Equation]:
        """Get all equations marked as key equations."""
        return [eq for eq in self.equations if eq.is_key]
    
    def get_word_count(self) -> int:
        """Calculate total word count of the paper."""
        total_words = len(self.abstract.split())
        for section in self.sections:
            total_words += len(section.content.split())
        return total_words
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Attention Is All You Need",
                "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar"],
                "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...",
                "sections": [
                    {
                        "id": "intro",
                        "title": "Introduction", 
                        "content": "Recurrent neural networks, long short-term memory...",
                        "level": 1,
                        "equations": ["eq1"],
                        "figures": ["fig1"]
                    }
                ],
                "equations": [
                    {
                        "id": "eq1",
                        "latex": "\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V",
                        "description": "Scaled dot-product attention",
                        "section_id": "intro",
                        "is_key": True
                    }
                ],
                "figures": [],
                "references": [],
                "arxiv_id": "1706.03762",
                "keywords": ["attention", "transformer", "neural networks"]
            }
        }