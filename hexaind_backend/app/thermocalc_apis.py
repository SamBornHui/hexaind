import os

from fastapi import FastAPI
from fastapi import Request
from dotenv import load_dotenv
import uvicorn
from asgi_correlation_id import CorrelationIdMiddleware
from app.api.thermocalc_endpoints.v1.thermocalc.routes import thermocalc_router
from app.core.services.cloud_utils.utils import get_secret_manager
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.custom_logging import ctx_request, ctx_user, load_logging
from logging import getLogger
from fastapi.middleware.cors import CORSMiddleware

# Initialize secret manager at startup
secret_manager = get_secret_manager()

# Load environment variables from a .env file
load_dotenv()
load_logging()
logger = getLogger(__package__)

"""
FASTAPI APP setup
"""
app = FastAPI()

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


@app.middleware("http")
async def populate_context_vars(request: Request, call_next):
    token = ctx_request.set(request)
    auth_token = request.headers.get("Authorization")
    user = None
    if auth_token:
        auth_token = auth_token.split(" ")[1]
        user = decodeJWT(token=auth_token)
    resp = ctx_user.set(user)
    response = await call_next(request)
    ctx_request.reset(token)
    ctx_user.reset(resp)
    return response


# Include routers from each API module
app.include_router(thermocalc_router)


openapi_schema = app.openapi()
if openapi_schema:
    openapi_schema["security"] = [{"JWTBearer": []}]

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=82)
