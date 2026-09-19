from fastapi import APIRouter

from .hub.routes import router as hub_router

router = APIRouter(prefix="/v1/sites/projects/{project_id}/jupyter", tags=["Jupyter"])

router.include_router(hub_router)
