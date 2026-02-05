"""
Script models re-export from config/backend/models.
"""

# Import the backend module to set up paths
from .. import *

# Re-export script models
try:
    from models.script import *
except ImportError:
    from config.backend.models.script import *