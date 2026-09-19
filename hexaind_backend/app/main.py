from datetime import datetime, timedelta, timezone
import os
import asyncio
import time
from concurrent.futures import ProcessPoolExecutor
from contextlib import asynccontextmanager
from logging import getLogger
from fastapi.routing import APIRoute
import aioredis
from asgi_correlation_id import CorrelationIdMiddleware
from dotenv import load_dotenv
from fastapi import (
    FastAPI,
    Request,
    Response,
    WebSocket,
    WebSocketDisconnect,
    status,
)
from fastapi import Depends, FastAPI, Request, Response, WebSocket, WebSocketDisconnect, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from app.api.endpoints.v1.access_controls.routes import (
    users_access_control_details_router,
)
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK

from app.api.endpoints.v1.admin.authentication.routes import (
    authentication_router,
    user_last_active,
    active_users,
)
from app.api.endpoints.v1.admin.connector.routes import connectors_router
from app.api.endpoints.v1.admin.healthcheck.routes import healthcheck_router
from app.api.endpoints.v1.admin.org_site_management.routes import role_mngt_router
from app.api.endpoints.v1.admin.projects.routes import projects_router
from app.api.endpoints.v1.AI.thermocalc.routes import thermocalc_router
from app.api.endpoints.v1.apps.datasheet_gen.routes import datasheet_gen_router
from app.api.endpoints.v1.apps.image_analysis.routes import image_analysis_router
from app.api.endpoints.v1.apps.image_datasets.routes import image_dataset_router
from app.api.endpoints.v1.apps.uc1.routes import uc1_configurations_router
from app.api.endpoints.v1.apps.uc2.routes import uc2_router
from app.api.endpoints.v1.apps.uc3.routes import uc3_router
from app.api.endpoints.v1.apphub import apphub_router
from app.api.endpoints.v1.data.assets.routes import assets_router
from app.api.endpoints.v1.data.assets_modifications.routes import (
    assets_modifications_router,
)
from app.api.endpoints.v1.data.bigquery.routes import bigquery_router
from app.api.endpoints.v1.data.snowflake.routes import snowflake_router
from app.api.endpoints.v1.data.cp_recipe_widget.routes import custom_python_router
from app.api.endpoints.v1.data.eda.routes import router as eda_router
from app.api.endpoints.v1.data.folder_management.routes import folder_management_router
from app.api.endpoints.v1.impex.export.routes import router as export_router
from app.api.endpoints.v1.impex.import_.routes import router as import_router
from app.api.endpoints.v1.jupyter.routes import router as jupyter_router
from app.api.endpoints.v1.jupyter.widget.routes import router as jupyter_widget_router
from app.api.endpoints.v1.micron import router as micron_router
from app.api.endpoints.v1.notifications.routes import notifications_router
from app.api.endpoints.v1.workflows.designer.routes import workflow_router
from app.api.endpoints.v1.workflows.runner.routes import workflow_runner_router
from app.api.endpoints.v1.workflows.scheduling.routes import scheduling_router
from app.api.endpoints.v1.workflows.sessions.routes import workflow_session_router
from app.api.endpoints.v1.workflows.workflow_designer.routes import (
    interactive_workflow_designer_router,
)
from app.api.endpoints.v1.apps.scrap_analysis.routes import sam_router
from app.config.env_vars import celery_environment, environment, gateway_environment
from app.core.db.db_utils import get_db_sync
from app.core.services.cloud_utils.utils import get_secret_manager
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.custom_logging import ctx_request, ctx_user, load_logging
from app.env import *
from app.services.notification.notification_micro_service import Notification
from prometheus_client import Counter, Gauge, Summary, generate_latest

# Initialize secret manager at startup
secret_manager = get_secret_manager()
# Load environment variables from a .env file
load_dotenv()
load_logging()
logger = getLogger(__package__)

# @asynccontextmanager
# async def lifespan(app: FastAPI):
#     """Start inactivity monitor on application startup."""
#     asyncio.create_task(monitor_inactivity())
#     yield
#     print("FastAPI shutting down...")

@asynccontextmanager
async def lifespan(app: FastAPI):
    with ProcessPoolExecutor(
        max_workers=environment.max_workers_for_assets_router
    ) as pool:
        yield {"assets_router_process_pool": pool}


"""
FASTAPI APP setup
"""
app = FastAPI(lifespan=lifespan)
DSG_PDF_PATH = os.path.join(EXPORT_PATH, "pdf_files")
os.makedirs(DSG_PDF_PATH, exist_ok=True)


@app.get("/health")
async def health() -> str:
    return "ok"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    redis_obj = aioredis.Redis.from_url(
        str(celery_environment.celery_result_backend_url)
    )
    pubsub = redis_obj.pubsub()
    logger.info("WebSocket connection established.")

    try:
        await pubsub.subscribe("notifications")
        message_count = 0
        while True:
            try:
                # Add keepalive ping
                await asyncio.wait_for(websocket.receive_text(), timeout=30)
                await websocket.send_json({"type": "ping"})
            except asyncio.TimeoutError:
                # Normal keepalive timeout, continue processing
                pass
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1
            )
            if message:
                message_data = message["data"].decode()
                if await redis_obj.sismember("processed_messages", message_data):
                    continue
                await redis_obj.sadd("processed_messages", message_data)
                try:
                    await websocket.send_text(message_data)
                    logger.info(f"Sent message: {message_data}")
                except (
                    WebSocketDisconnect,
                    ConnectionClosedError,
                    ConnectionClosedOK,
                ) as e:
                    logger.warning(f"WebSocket disconnected: {e}")
                    break

                # Process notification in background
                asyncio.create_task(process_notification(message["data"]))
                message_count += 1
                logger.info(f"Message count: {message_count}")

    except (WebSocketDisconnect, ConnectionClosedError, ConnectionClosedOK) as e:
        logger.warning(f"Client disconnected: {e}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        try:
            await pubsub.unsubscribe("notifications")
            await redis_obj.close()
            await websocket.close()
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
        logger.info("Connections closed")


async def process_notification(data: bytes):
    """Separate notification processing task"""
    try:
        notification_obj = Notification(db_sync_client=get_db_sync())
        await notification_obj.process_notification(data)
    except Exception as e:
        logger.error(f"Notification processing failed: {e}")


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.exception(f"Validation Error {str(exc)}")

    errors = exc.errors()
    widgets_present = any("widgets" in error.get("loc", []) for error in errors)

    if widgets_present:
        formatted_errors = []
        missing_fields = []
        for error in errors:
            error_type = error.get("type")
            location = error.get("loc")
            message = error.get("msg")
            widget_name = location[4]
            missing_field = f"{widget_name}_{location[-1]}"

            formatted_errors.append(
                {
                    "type": error_type,
                    "location": location,
                    "message": message,
                    "widget_name": widget_name,
                    "missing_field": f"{widget_name}_{location[-1]}",
                }
            )
            logger.error(f"Details Errors: {formatted_errors}")
            missing_fields.append(missing_field)
            logger.error(f"Missing Fields: {missing_fields}")

        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"errors": formatted_errors, "missing_fields": missing_fields},
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=errors,
        )


REQUEST_COUNT = Counter(
    "api_request_count",
    "Total api request count",
    ["method", "endpoint", "http_status"],
)
REQUEST_LATENCY = Summary(
    "api_request_latency_seconds", "Latency of API requests", ["method", "endpoint"]
)
REQUEST_IN_PROGRESS = Gauge(
    "api_requests_in_progress", "Api requests in progress", ["method", "endpoint"]
)

User_Action = Counter(
    "user_actions_total", "Count of user actions", ["action", "user_email", "user_id"]
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    method = request.method
    path = request.url.path

    logger.info(
        f"[============= START =============] Method: {request.method}, Path: {request.url.path}"
    )
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).inc()
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    REQUEST_COUNT.labels(
        method=method, endpoint=path, http_status=response.status_code
    ).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=path).observe(process_time)
    REQUEST_IN_PROGRESS.labels(method=method, endpoint=path).dec()
    logger.info(
        f"[=============  END  =============] Method: {request.method}, Path: {request.url.path}, Duration: {process_time} seconds"
    )

    return response


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
    action = "default"
    if auth_token:
        auth_token = auth_token.split(" ")[1]
        user = decodeJWT(token=auth_token)
        user_id = user.get("user_id")
        if user_id:
            current_time = datetime.now(timezone.utc)
            last_active = user_last_active.setdefault(
                user_id, current_time
            )  # setdefault returns the value if the key already exists or else it add key with defult value(current time in this case)
            if last_active == current_time:
                active_users.inc()
            logger.info(f"Updated last active timestamp for user {user_id}")
            logger.info(user_last_active)
    resp = ctx_user.set(user)
    response = await call_next(request)
    route = request.scope.get("route", None)
    if isinstance(route, APIRoute):
        action = (
            route.openapi_extra.get("actions", "default")
            if route.openapi_extra
            else "default"
        )
    User_Action.labels(
        user_email=user.get("email") if user else None,
        user_id=user.get("user_id") if user else None,
        action=action,
    ).inc()
    ctx_request.reset(token)
    ctx_user.reset(resp)
    return response


# Metrics for api call
@app.get("/metrics")
async def metrics():
    current_time = datetime.now(timezone.utc)
    inactive_user_ids = [
        user_id
        for user_id, last_active in user_last_active.items()
        if (current_time - last_active).total_seconds()
        > 7200  # Inactive threshold of 2 hours (7200s)
    ]
    for user_id in inactive_user_ids:
        del user_last_active[user_id]
    active_users.set(len(user_last_active))
    logger.info(active_users)
    logger.info(user_last_active)
    return Response(content=generate_latest(), media_type="text/plain")


@app.get("/explore_data")
async def redirect_to_superset():
    response =  {"url":f"{gateway_environment.uri}home"}
    # response.set_cookie("hexaind-token", f"Bearer {token}", samesite=None, domain="172.31.141.2")
    return response


# Include routers from each API module
app.include_router(workflow_router)
app.include_router(scheduling_router)
app.include_router(workflow_session_router)
app.include_router(interactive_workflow_designer_router)
app.include_router(workflow_runner_router)
app.include_router(connectors_router)
app.include_router(notifications_router)
app.include_router(assets_router)
app.include_router(assets_modifications_router)
app.include_router(custom_python_router)
app.include_router(projects_router)
app.include_router(authentication_router)
app.include_router(role_mngt_router)
app.include_router(bigquery_router)
app.include_router(snowflake_router)
app.include_router(thermocalc_router)
app.include_router(datasheet_gen_router)
app.include_router(eda_router)
app.include_router(users_access_control_details_router)
app.include_router(healthcheck_router)
app.include_router(folder_management_router)
app.include_router(image_dataset_router)
app.include_router(image_analysis_router)
app.include_router(export_router)
app.include_router(import_router)
app.include_router(uc1_configurations_router)
app.include_router(uc2_router)
app.include_router(jupyter_router)
app.include_router(jupyter_widget_router)
app.include_router(micron_router)
app.include_router(uc3_router)
app.include_router(sam_router)
app.include_router(apphub_router)

app.mount("/pdf_files", StaticFiles(directory=DSG_PDF_PATH), name="pdf_files")
openapi_schema = app.openapi()
if openapi_schema:
    openapi_schema["security"] = [{"JWTBearer": []}]
