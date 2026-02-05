"""
Audio models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export audio models
try:
    from models.audio import *
except ImportError:
    from config.backend.models.audio import *