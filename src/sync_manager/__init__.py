"""
Sync Manager Domain Module
Handles data synchronization between external services and the application
"""

from .router import router as sync_manager_router

__all__ = ["sync_manager_router"] 