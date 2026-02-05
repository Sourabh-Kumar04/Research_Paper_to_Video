"""
Paper models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export paper models
try:
    from models.paper import *
except ImportError:
    from config.backend.models.paper import *