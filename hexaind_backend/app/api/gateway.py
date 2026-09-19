import logging
import os
import re
import secrets
import string
from contextlib import asynccontextmanager
from typing import TypedDict

import httpx
import requests
from aiohttp import ClientSession
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from multidict import MultiDict
from starlette.middleware.base import BaseHTTPMiddleware

from app.config.env_vars import gateway_environment
from app.core.db.db_utils import get_db_async
from app.core.services.jwt_token_utils.jwt_token_utils import decodeJWT
from app.custom_logging import load_logging
from app.services.admin.authentication.schemas import SuperSetData, User
from app.services.admin.authentication.service import AuthenticationService
from app.services.superset.service import SupersetService


class DecodedToken(TypedDict):
    email: str
    server_role_value: int
    type: str
    user_id: str
    expires: float


load_logging()

logger = logging.getLogger(__package__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with ClientSession(base_url=f"{gateway_environment.superset_url}") as session:
        yield {"session": session}


app = FastAPI(title="HEXAIND Gateway", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
    expose_headers=["X-CORRELATION-ID"],
)


@app.get("/health")
async def health():
    return "ok"


def generate_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    password = "".join(secrets.choice(alphabet) for _ in range(length))
    return password


async def superset_init() -> SupersetService:
    return await SupersetService.authenticate_and_create_client(
        url=str(gateway_environment.superset_url),
        username=gateway_environment.username,
        password=gateway_environment.password,
    )


def get_authentication_service(
    db_async_client=Depends(get_db_async),
) -> AuthenticationService:
    return AuthenticationService(db_async_client=db_async_client)


async def generate_superset_user(
    hexaind_user_id: str,
    project_id: str,
    user: User,
    superset_client: SupersetService,
    auth_service: AuthenticationService,
) -> SuperSetData:
    gamma_role = await superset_client.role.from_id(4)
    sql_lab_role = await superset_client.role.from_id(5)
    project_role = (await superset_client.role.from_name(project_id))[0]

    # Check if user already has Superset data
    if user.data_superset is not None:
        superset_user = await superset_client.user.from_id(
            user.data_superset.superset_user_id
        )
        superset_user.roles = [gamma_role, sql_lab_role, project_role]
        user.data_superset.role=[role.id for role in superset_user.roles]
        await superset_client.user.update(user)
    else:
        password = generate_password()
        superset_user = await superset_client.user.create(
            email=user.email,
            first_name=user.first_name if user.first_name else "",
            last_name=user.last_name if user.last_name else "",
            username=user.email,
            password=password,
            roles=[gamma_role, sql_lab_role, project_role],
        )
        logger.info("Superset user created successfully.")

        user.data_superset = SuperSetData(
            username=superset_user.username,
            password=password,
            superset_user_id=superset_user.id,
            role=[role.id for role in superset_user.roles],
        )
    await auth_service.update_user_async(hexaind_user_id, user.data_superset)
    return user.data_superset


@app.get("/home")
async def home(
    token: str,
    request: Request,
    projectId: str = "",
    superset_client: SupersetService = Depends(superset_init),
    auth_service: AuthenticationService = Depends(get_authentication_service),
):
    decoded_token: DecodedToken = request.state.decoded_token
    hexaind_user_id = decoded_token["user_id"]

    try:
        user = await auth_service.get_user_with_id(hexaind_user_id)
    except KeyError:
        logger.exception("user not found")
        raise HTTPException(status_code=404, detail="User not found")

    superset_user_data = await generate_superset_user(
        hexaind_user_id, projectId, user, superset_client, auth_service
    )

    response = RedirectResponse(url="/savedqueryview/list/")
    response.set_cookie("hexaind-token", f"Bearer {token}")
    response.set_cookie("project_id", projectId)

    # if request.cookies.get("session") is None:
    url = f"{gateway_environment.superset_url}login"
    form_data = {
        "username": superset_user_data.username,
        "password": superset_user_data.password,
    }
    login_response = requests.post(
        url,
        data=form_data,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    session_cookie_value = login_response.cookies["session"]
    response.set_cookie("session", session_cookie_value)

    return response


@app.get("/redirect")
async def redirect_to_hexaind():
    response = RedirectResponse(url=str(os.getenv("HEXAIND_FRONT_END_URL")))
    return response


# List of paths to be excluded from authorization
EXCLUDED_PATHS = ["/health", "/redirect"]


# Authorization middleware
class AuthorizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Skip authorization check for paths in EXCLUDED_PATHS
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            logger.debug(f"excluded {request.url.path}")
            response = await call_next(request)
        else:
            cookie_token = request.cookies.get("hexaind-token")
            auth_token = request.headers.get("Authorization")
            query_token = request.query_params.get("token")

            if query_token:
                token = query_token
            elif auth_token and auth_token.lower().startswith("bearer "):
                token = auth_token.split(" ")[1]
            elif cookie_token and cookie_token.lower().startswith("bearer "):
                token = cookie_token.split(" ")[1]
            else:
                logger.debug(
                    f"empty tokens {cookie_token=}, {auth_token=}, {query_token=}"
                )
                return RedirectResponse(url=f"{os.getenv('HEXAIND_FRONT_END_URL')}/login")

            decoded_token = decodeJWT(token)

            if not decoded_token:
                logger.debug("invalid token")
                return RedirectResponse(url=f"{os.getenv('HEXAIND_FRONT_END_URL')}/login")

            request.state.decoded_token = decoded_token

            response = await call_next(request)
            if cookie_token is None:
                response.set_cookie("hexaind-token", f"Bearer {token}")

        return response


app.add_middleware(AuthorizationMiddleware)


async def gateway(request: Request) -> Response:
    path = request.url.path
    session = request.state.session

    try:
        request_headers = MultiDict()
        for key, value in request.headers.items():
            if key not in ("host"):
                request_headers.add(key, value)
        async with session.request(
            method=request.method,
            url=path,
            params=request.query_params,
            headers=request_headers,
            cookies=request.cookies,
            data=await request.body(),
        ) as response:
            response_headers = MultiDict()
            for key, value in response.headers.items():
                if key.lower() not in (
                    "content-length",
                    "date",
                    "server",
                    "content-encoding",
                ):
                    response_headers.add(key, value)
            result = Response(
                content=await response.read(),
                status_code=response.status,
                headers=response_headers,
                media_type=response.content_type,
            )
            return result
    except Exception as e:
        logger.exception("internal exception")
        raise HTTPException(status_code=500, detail="Internal Server Error") from e


@app.post("/api/v1/dataset/")
async def create_dataset(request: Request, data_dict: dict):
    project_id = request.cookies.get("project_id")
    token = request.cookies.get("hexaind-token") or request.headers.get("Authorization")

    cleaned_sql = re.sub(r"\s+", " ", data_dict["sql"]).strip()
    data_dict["sql"] = cleaned_sql

    # url = f"{os.getenv('HEXAIND3_BACKEND_URL')}/v1/sites/1/projects/{project_id}/connectors/external_data_pull"
    payload = {
        "superset_connector_id": data_dict["database"],
        "query": data_dict["sql"],
        "token": token,
    }

    headers = {
        "Authorization": token,  # if token.startswith("Bearer ") else f"Bearer {token}",
        "Content-Type": "application/json",
    }

    # response = requests.post(url, json=payload, headers=headers)
    async with httpx.AsyncClient(
        base_url=str("http://workflow_apis:8000"), timeout=None
    ) as client:
        # Call the create database API
        queries_url = "/v1/sites/1/projects/connectors/external_data_pull"
        response = await client.post(queries_url, headers=headers, json=payload)
        logger.info(f"RESPONSE: {response.text}")

    return await gateway(request)


app.add_api_route("{path:path}", gateway, methods=["GET", "POST", "PUT", "DELETE"])
