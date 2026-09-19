import sys
import uvicorn
import logging
from dotenv import load_dotenv
from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware
from concurrent.futures import ProcessPoolExecutor
from asgi_correlation_id import CorrelationIdMiddleware

from app.config.env_vars import environment
from app.core.db.db_utils import get_db_async
from app.services.AI.prediction.service import PredictionService
from app.api.endpoints.v1.admin.authentication.routes import authentication_router
from app.api.endpoints.v1.access_controls.routes import (
    users_access_control_details_router,
)
from app.api.endpoints.v1.AI.models.routes import models_router

# Load environment variables from a .env file
load_dotenv()
# load_logging()

logger = logging.getLogger(__package__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(sys.stdout))


@asynccontextmanager
async def lifespan(app: FastAPI):
    with ProcessPoolExecutor(
        max_workers=environment.max_workers_for_assets_router
    ) as pool:
        db_async_client = get_db_async()
        logger.info("\n\n going to redeploy models \n\n")
        prediction_service = PredictionService(db_async_client=db_async_client)
        await prediction_service.redeploy_models()
        yield {"assets_router_process_pool": pool}


"""
FASTAPI APP setup
"""
app = FastAPI(lifespan=lifespan)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["X-CORRELATION-ID"],
)
app.add_middleware(CorrelationIdMiddleware, header_name="X-CORRELATION-ID")


# Include routers from each API module
app.include_router(models_router)
app.include_router(authentication_router)
app.include_router(users_access_control_details_router)

openapi_schema = app.openapi()
if openapi_schema:
    openapi_schema["security"] = [{"JWTBearer": []}]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=81)
