"""Legacy tools module - imports from modular structure.

This module maintains backward compatibility while the implementation
has been moved to the tools/ directory for better organization.
"""

# Import everything from the new modular structure
from .tools import StarfishTools

# Re-export for backward compatibility
__all__ = ["StarfishTools"]
