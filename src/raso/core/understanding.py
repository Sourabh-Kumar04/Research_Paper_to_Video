"""
Understanding models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export understanding models
try:
    from models.understanding import *
except ImportError:
    from config.backend.models.understanding import *