"""
Animation models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export animation models
try:
    from models.animation import *
except ImportError:
    from config.backend.models.animation import *