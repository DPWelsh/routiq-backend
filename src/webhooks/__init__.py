"""
Webhooks Domain Module
Handles webhook endpoints and N8N workflow triggering
"""

from .router import router as webhooks_router

__all__ = ["webhooks_router"] 