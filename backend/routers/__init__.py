"""
Routers API organizados por domínio.
"""

from fastapi import APIRouter

from .farms import router as farms_router
from .uploads import router as uploads_router
from .dashboard import router as dashboard_router


def get_routers():
    return [
        farms_router,
        uploads_router,
        dashboard_router,
    ]