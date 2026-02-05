"""
Video models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export video models
try:
    from models.video import *
except ImportError:
    from config.backend.models.video import *