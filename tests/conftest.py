"""
Pytest configuration and shared fixtures for RASO platform tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest
from hypothesis import settings

from backend.config import RASOMasterConfig


# Configure Hypothesis for property-based testing
settings.register_profile("ci", max_examples=100, deadline=None)
settings.register_profile("dev", max_examples=10, deadline=None)
settings.load_profile(os.getenv("HYPOTHESIS_PROFILE", "dev"))


@pytest.fixture(scope="session")
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)


@pytest.fixture
def test_config(temp_dir: Path) -> RASOMasterConfig:
    """Create a test configuration with temporary paths."""
    return RASOMasterConfig(
        env="test",
        debug=True,
        log_level="DEBUG",
        data_path=temp_dir / "data",
        temp_path=temp_dir / "temp",
        log_path=temp_dir / "logs",
        database_url="redis://localhost:6379/15",  # Use test database
        secret_key="test-secret-key",
        cors_origins=["http://localhost:3000"],
    )


@pytest.fixture
def sample_paper_content():
    """Sample paper content for testing."""
    return {
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
                "figures": []
            }
        ],
        "equations": [
            {
                "id": "eq1",
                "latex": "\\text{Attention}(Q, K, V) = \\text{softmax}\\left(\\frac{QK^T}{\\sqrt{d_k}}\\right)V",
                "description": "Scaled dot-product attention",
                "sectionId": "intro",
                "isKey": True
            }
        ],
        "figures": [],
        "references": []
    }


@pytest.fixture
def sample_paper_understanding():
    """Sample paper understanding for testing."""
    return {
        "problem": "Sequential models are slow due to their inherent sequential nature",
        "intuition": "Attention mechanisms can replace recurrence entirely",
        "contributions": [
            "Transformer architecture based solely on attention",
            "Parallelizable training process",
            "State-of-the-art results on translation tasks"
        ],
        "keyEquations": [
            {
                "equationId": "eq1",
                "importance": 10,
                "visualizationHint": "Show matrix multiplication and softmax operation",
                "relatedConcepts": ["attention", "transformer", "self-attention"]
            }
        ],
        "visualizableConcepts": [
            {
                "name": "Self-Attention Mechanism",
                "description": "How tokens attend to other tokens in the sequence",
                "visualizationType": "animation",
                "complexity": "medium",
                "relatedEquations": ["eq1"]
            }
        ]
    }


@pytest.fixture
def sample_narration_script():
    """Sample narration script for testing."""
    return {
        "scenes": [
            {
                "id": "scene1",
                "title": "Introduction to Transformers",
                "narration": "Today we'll explore the Transformer architecture...",
                "duration": 30.0,
                "visualType": "motion-canvas",
                "concepts": ["transformer", "attention"]
            },
            {
                "id": "scene2", 
                "title": "Attention Mechanism",
                "narration": "The key innovation is the attention mechanism...",
                "duration": 45.0,
                "visualType": "manim",
                "concepts": ["attention", "self-attention"]
            }
        ],
        "totalDuration": 75.0,
        "wordCount": 150
    }