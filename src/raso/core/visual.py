"""
Visual models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export visual models
try:
    from models.visual import *
except ImportError:
    from config.backend.models.visual import *