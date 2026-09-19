from fastapi import APIRouter

from app.api.endpoints.v1.micron.data_catalog.routes import (
    router as datacatalog_routers,
)

router = APIRouter(prefix="/micron")
router.include_router(datacatalog_routers)
