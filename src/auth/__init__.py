"""
Authentication Domain Module
Handles user authentication, authorization, and JWT token management
"""

from .router import router as auth_router

__all__ = ["auth_router"] 