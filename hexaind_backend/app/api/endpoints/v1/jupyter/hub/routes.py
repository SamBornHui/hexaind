import logging
import os
import json
import socket
import shutil
import subprocess
import nbformat as nbf
from pathlib import Path as PPath
from contextlib import closing
from typing import Annotated, AsyncGenerator, Generator, List, Tuple

from aiohttp import ClientSession
from fastapi import APIRouter, Depends, Path, status
from motor.motor_asyncio import AsyncIOMotorClient
import toml
from pymongo import MongoClient

from app.config.env_vars import environment, jupyterhub_environment
from app.core.services.jwt_token_utils.jwt_token_utils import JWTBearer, decodeJWT
from app.services.admin.authentication.schemas import ServerBasedRoleNames

from .dao import JupyterServerDao
from .exceptions import (
    JupyterNBDataNotFound,
    JupyterServerException,
    RoleAccessDeniedException,
    ServerAlreadyExistsException,
    ServerNotFoundException,
    UnAuthorizedException,
)
from .schemas import (
    JupyterNBResponse,
    JupyterServer,
    JupyterServerActions,
    JupyterServerCreateBody,
    JupyterServerStatus,
    PydanticObjectId,
    JupyterNBCloneAndPromotePaths,
    JupyterNBCommonResponse,
    JupyterNBCreateRequest,
    FreePortResponse,
)
from .service import JupyterHubService

router = APIRouter(prefix="/hub", tags=["Jupyter", "JupyterHub"])
logger = logging.getLogger(__package__)


async def get_decoded_token(token: Annotated[str, Depends(JWTBearer())]) -> dict:
    decoded_token = decodeJWT(token)
    if decoded_token is None:
        raise UnAuthorizedException()
    return decoded_token


def get_sync_db_client() -> Generator[MongoClient, None, None]:
    with MongoClient(environment.mongo_details) as client:
        yield client


async def get_async_db_client() -> AsyncGenerator[AsyncIOMotorClient, None]:
    with closing(AsyncIOMotorClient(environment.mongo_details)) as client:
        yield client


async def get_user_role(
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
) -> ServerBasedRoleNames:
    if (user_role := decoded_token.get("server_role_value")) is None:
        raise UnAuthorizedException()
    return ServerBasedRoleNames.get_server_role(user_role)


async def get_jupyter_server_dao(
    db_sync_client: Annotated[MongoClient, Depends(get_sync_db_client)],
    db_async_client: Annotated[AsyncIOMotorClient, Depends(get_async_db_client)],
) -> JupyterServerDao:
    return JupyterServerDao(
        db_sync_client=db_sync_client, db_async_client=db_async_client
    )


async def get_jupyter_server_service(
    db_sync_client: Annotated[MongoClient, Depends(get_sync_db_client)],
    db_async_client: Annotated[AsyncIOMotorClient, Depends(get_async_db_client)],
) -> JupyterHubService:
    return JupyterHubService(
        db_sync_client=db_sync_client, db_async_client=db_async_client
    )


async def get_aiohttp_client_session() -> ClientSession:
    async with ClientSession(
        base_url=str(jupyterhub_environment.api_url),
        headers={"Authorization": f"Bearer {jupyterhub_environment.api_token}"},
    ) as client_session:
        yield client_session


async def get_user_actions(
    user_role: Annotated[ServerBasedRoleNames, Depends(get_user_role)]
) -> JupyterServerActions:
    match user_role:
        case ServerBasedRoleNames.DEFAULT_USER:
            return (
                JupyterServerActions.CREATE
                | JupyterServerActions.START
                | JupyterServerActions.STOP
            )
        case ServerBasedRoleNames.PROJECT_ADMIN | ServerBasedRoleNames.SERVER_ADMIN:
            return (
                JupyterServerActions.CREATE
                | JupyterServerActions.DELETE
                | JupyterServerActions.START
                | JupyterServerActions.STOP
            )
        case _:
            raise NotImplementedError()


@router.post("/server", status_code=status.HTTP_201_CREATED)
async def create_server(
    project_id: Annotated[PydanticObjectId, Path()],
    user_actions: Annotated[JupyterServerActions, Depends(get_user_actions)],
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
    body: JupyterServerCreateBody,
) -> JupyterServer:
    if not (user_actions & JupyterServerActions.CREATE):
        raise RoleAccessDeniedException()
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_project_id_async(
        project_id
    )
    if jupyter_server is not None:
        raise ServerAlreadyExistsException()
    # TODO send request to create
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/post-user
    async with client_session.post(f"/hub/api/users/{project_id}") as response:
        logger.debug(f"response {response}")
        if response.status != status.HTTP_201_CREATED:
            raise JupyterServerException(message="unable to create jupyter server")
    jupyter_server = JupyterServer.model_validate(
        {
            "name": body.name,
            "description": body.description,
            "project_id": str(project_id),
            "status": JupyterServerStatus.CREATING,
        }
    )
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/post-user-server
    async with client_session.post(f"/hub/api/users/{project_id}/server") as response:
        logger.debug(f"response {response}")
        match response.status:
            case status.HTTP_202_ACCEPTED:
                jupyter_server.status = JupyterServerStatus.CREATING
            case status.HTTP_201_CREATED:
                jupyter_server.status = JupyterServerStatus.RUNNING
            case _:
                raise JupyterServerException(message="unable to start jupyter server")
    inserted_id = await jupyter_server_dao.create_jupyter_server_async(jupyter_server)
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_id_async(
        inserted_id
    )
    if jupyter_server is None:
        raise JupyterServerException(message="unable to create server")
    return jupyter_server


@router.get("/server")
async def get_server(
    project_id: Annotated[PydanticObjectId, Path()],
    user_actions: Annotated[JupyterServerActions, Depends(get_user_actions)],
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    jupyter_server_service: Annotated[
        JupyterHubService, Depends(get_jupyter_server_service)
    ],
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
) -> JupyterServer:
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_project_id_async(
        project_id
    )
    if jupyter_server is None:
        raise ServerNotFoundException()
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/get-user
    async with client_session.get(f"/hub/api/users/{project_id}") as response:
        logger.debug(f"response {response}")
        match response.status:
            case status.HTTP_404_NOT_FOUND:
                await jupyter_server_dao.delete_jupyter_server_by_project_id_async(
                    project_id
                )
            case status.HTTP_200_OK:
                body = await response.json()
                logger.debug(f"response body {body}")
                servers: dict = body.get("servers", {})
                server: dict = servers.pop("", {})
                if server.get("ready", False):
                    jupyter_server.status = JupyterServerStatus.RUNNING
                elif server.get("stopped", True):
                    jupyter_server.status = JupyterServerStatus.STOPPED
                else:
                    jupyter_server.status = JupyterServerStatus.CREATING
            case _:
                raise JupyterServerException(message="unable to fetch server status")
    await jupyter_server_dao.replace_jupyter_server_async(jupyter_server)
    user_id = decoded_token.get("user_id")
    result = await jupyter_server_service.fetch_paths_and_types(
        project_id=jupyter_server.project_id, user_id=user_id
    )
    jupyter_server.notebooks = result
    return jupyter_server


@router.get("/server/all")
async def get_all_servers(
    project_id: str,
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    jupyter_server_service: Annotated[
        JupyterHubService, Depends(get_jupyter_server_service)
    ],
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
) -> List[JupyterServer]:
    jupyter_servers = []
    async for jupyter_server in jupyter_server_dao.get_jupyter_servers_in_project_async(
        project_id=project_id
    ):
        # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/get-user
        async with client_session.get(
            f"/hub/api/users/{jupyter_server.project_id}"
        ) as response:
            match response.status:
                case status.HTTP_404_NOT_FOUND:
                    await jupyter_server_dao.delete_jupyter_server_by_project_id_async(
                        PydanticObjectId(jupyter_server.project_id)
                    )
                    continue
                case status.HTTP_200_OK:
                    body = await response.json()
                    logger.debug(f"response body {body}")
                    servers: dict = body.get("servers", {})
                    server: dict = servers.pop("", {})
                    if server.get("ready", False):
                        jupyter_server.status = JupyterServerStatus.RUNNING
                    elif server.get("stopped", True):
                        jupyter_server.status = JupyterServerStatus.STOPPED
                    else:
                        jupyter_server.status = JupyterServerStatus.CREATING
                case _:
                    raise JupyterServerException(
                        message="unable to fetch server status"
                    )
        await jupyter_server_dao.replace_jupyter_server_async(jupyter_server)
        user_id = decoded_token.get("user_id")
        result = await jupyter_server_service.fetch_paths_and_types(
            project_id=jupyter_server.project_id, user_id=user_id
        )
        jupyter_server.notebooks = result
        jupyter_servers.append(jupyter_server)
    return jupyter_servers


@router.delete("/server", status_code=status.HTTP_204_NO_CONTENT)
async def remove_server(
    project_id: Annotated[PydanticObjectId, Path()],
    user_actions: Annotated[JupyterServerActions, Depends(get_user_actions)],
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
):
    if not (user_actions & JupyterServerActions.DELETE):
        raise RoleAccessDeniedException()
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_project_id_async(
        project_id
    )
    if jupyter_server is None:
        raise ServerNotFoundException()
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/delete-user-server
    async with client_session.delete(f"/hub/api/users/{project_id}/server") as response:
        logger.debug(f"response {response}")
        match response.status:
            case status.HTTP_202_ACCEPTED:
                jupyter_server.status = JupyterServerStatus.RUNNING
            case status.HTTP_204_NO_CONTENT:
                jupyter_server.status = JupyterServerStatus.STOPPED
            case _:
                raise JupyterServerException(message="unable to stop jupyter server")
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/delete-user
    async with client_session.delete(f"/hub/api/users/{project_id}") as response:
        logger.debug(f"response {response}")
        if response.status != status.HTTP_204_NO_CONTENT:
            raise JupyterServerException(message="unable to delete jupyter server")
    await jupyter_server_dao.delete_jupyter_server_by_project_id_async(project_id)


@router.post("/server/run")
async def start_server(
    project_id: Annotated[PydanticObjectId, Path()],
    user_actions: Annotated[JupyterServerActions, Depends(get_user_actions)],
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
) -> JupyterServer:
    if not (user_actions & JupyterServerActions.START):
        raise RoleAccessDeniedException()
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_project_id_async(
        project_id
    )
    if jupyter_server is None:
        raise ServerNotFoundException()
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/post-user-server
    async with client_session.post(f"/hub/api/users/{project_id}/server") as response:
        logger.debug(f"response {response}")
        match response.status:
            case status.HTTP_202_ACCEPTED:
                jupyter_server.status = JupyterServerStatus.CREATING
            case status.HTTP_201_CREATED:
                jupyter_server.status = JupyterServerStatus.RUNNING
            case _:
                raise JupyterServerException(message="unable to start jupyter server")
    await jupyter_server_dao.replace_jupyter_server_async(jupyter_server)
    return jupyter_server


@router.delete("/server/run")
async def stop_server(
    project_id: Annotated[PydanticObjectId, Path()],
    user_actions: Annotated[JupyterServerActions, Depends(get_user_actions)],
    jupyter_server_dao: Annotated[JupyterServerDao, Depends(get_jupyter_server_dao)],
    client_session: Annotated[ClientSession, Depends(get_aiohttp_client_session)],
) -> JupyterServer:
    if not (user_actions & JupyterServerActions.STOP):
        raise RoleAccessDeniedException()
    jupyter_server = await jupyter_server_dao.get_jupyter_server_by_project_id_async(
        project_id
    )
    if jupyter_server is None:
        raise ServerNotFoundException()
    # TODO fetch and update server status
    # https://jupyterhub.readthedocs.io/en/stable/reference/rest-api.html#operation/delete-user-server
    async with client_session.delete(f"/hub/api/users/{project_id}/server") as response:
        logger.debug(f"response {response}")
        match response.status:
            case status.HTTP_202_ACCEPTED:
                jupyter_server.status = JupyterServerStatus.RUNNING
            case status.HTTP_204_NO_CONTENT:
                jupyter_server.status = JupyterServerStatus.STOPPED
            case _:
                raise JupyterServerException(message="unable to stop jupyter server")
    await jupyter_server_dao.replace_jupyter_server_async(jupyter_server)
    return jupyter_server


@router.get("/server/notebooks_data/{user_id}")
async def get_notebooks_in_server(
    user_id: str,
    project_id: Annotated[PydanticObjectId, Path()],
    jupyter_server_service: Annotated[
        JupyterHubService, Depends(get_jupyter_server_service)
    ],
) -> JupyterNBResponse:

    result = await jupyter_server_service.fetch_paths_and_types(
        project_id=project_id, user_id=user_id
    )

    if not result:
        logger.exception("Data not found")
        raise JupyterNBDataNotFound()

    return JupyterNBResponse(result=result)


@router.post("/server/jnb_copy_folder")
async def copy_folder_in_jnb(
    project_id: Annotated[PydanticObjectId, Path()],
    jupyter_server_service: Annotated[
        JupyterHubService, Depends(get_jupyter_server_service)
    ],
    config: JupyterNBCloneAndPromotePaths,
) -> JupyterNBCommonResponse:
    try:
        base_dir = f"{environment.jupyter_hub_folder}"
        config.source = f"{base_dir}/{config.source}"
        config.destination = f"{base_dir}/{config.destination}"
        # TODO How are the paths actually sent from the UI? folder names or entire paths

        result = await jupyter_server_service.clone_or_promote(
            src=config.source, dest=config.destination
        )

        if not result:
            logger.exception("Unable to clone the notebook")
            raise Exception("Unable to clone the notebook")

        return JupyterNBCommonResponse(status=True, message="Clone Succesfully")

    except Exception as e:
        logger.exception(f"Unable to clone: exception - {e}")
        return JupyterNBCommonResponse(
            status=False, message=f"Unable to Clone, {str(e)}"
        )


def create_notebook(notebook_path: PPath):
    """
    Function to create a notebook with the provided template code and set proper permissions.
    """
    try:
        # Template Python code to be added as a cell in the notebook
        code = """
import requests
import os

project_id = os.environ.get("JUPYTERHUB_USER", None)
# The API endpoint
url = f"http://workflow_apis:8000/v1/sites/projects/{project_id}/jupyter/hub/server/get_free_port"

# A GET request to the API
response = requests.get(url)

# Print the response
print(response.json())

data = response.json()
port = None
if data and data['status']:
    port = data['port']
    print(f'{port} port successfully Bound')
else:
    print('unable to bind port')

host_info = !hostname -i
host = host_info[0]
native_host = os.environ.get('NATIVE_HOST')
        """

        # Create a new notebook
        nb = nbf.v4.new_notebook()

        # Add a new code cell with the template
        code_cell = nbf.v4.new_code_cell(code)
        nb.cells.append(code_cell)

        # Write the notebook to file
        with open(notebook_path, "w") as f:
            nbf.write(nb, f)

    except:
        logger.exception(f"Failed to create notebook at {notebook_path}", exc_info=True)


@router.post("/server/create_folders")
async def create_user_folder(
    project_id: Annotated[PydanticObjectId, Path()],
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
):
    original_umask = None
    try:
        # this is needed as jupyter hub containers are not running as root but others are
        original_umask = os.umask(0)  # Ensure permission handling
        user_id = decoded_token.get("user_id")
        base_dir = f"{environment.jupyter_hub_folder}/p_{project_id}"
        user_jnbs = f"{base_dir}/u_{user_id}"
        master_jnbs = f"{base_dir}/master_notebooks"

        # Create the necessary directories
        os.makedirs(master_jnbs, exist_ok=True)
        os.makedirs(user_jnbs, exist_ok=True)

        # Symlink master notebooks if not already created
        if not os.path.exists(user_jnbs + "/master_nb_link"):
            os.symlink(
                master_jnbs, user_jnbs + "/master_nb_link", target_is_directory=True
            )

        # Define the path for the new notebook
        notebook_path = PPath(user_jnbs) / "external_app_bind.ipynb"

        # Create the notebook if it does not already exist
        if not notebook_path.exists():
            create_notebook(notebook_path)

        os.umask(original_umask)
        return JupyterNBCommonResponse(
            status=True, message="Refreshed folders and notebook created successfully"
        )

    except Exception as e:
        logger.exception(f"Unable to clone: exception - {e}")
        if original_umask:
            os.umask(original_umask)
        return JupyterNBCommonResponse(
            status=False,
            message=f"Unable to refresh user folders and create notebook, {str(e)}",
        )


@router.post("/server/create_notebook")
async def create_notebook_in_server(
    project_id: Annotated[PydanticObjectId, Path()],
    create_request: JupyterNBCreateRequest,
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
):
    original_umask = None
    try:
        original_umask = os.umask(
            0
        )  # this is needed as jupyter hub containers are not running as root but others are
        user_id = decoded_token.get("user_id")
        user_jnbs = f"{environment.jupyter_hub_folder}/p_{project_id}/u_{user_id}"
        os.makedirs(user_jnbs, exist_ok=True)
        notebook_path = f"{user_jnbs}/{create_request.name}"
        if os.path.exists(notebook_path):
            raise ValueError(
                f"Already a notebook exists in same destination {create_request.name}"
            )
        os.makedirs(notebook_path, exist_ok=True)

        content = {"cells": [], "metadata": {}, "nbformat": 4, "nbformat_minor": 5}
        # main python notebook
        with open(f"{notebook_path}/main.ipynb", "w") as f:
            json.dump(content, f, indent=4)

        # metadata content
        pyproject_content = {
            "project": {
                "name": create_request.name,
                "version": "0.1.0",
                "description": create_request.description,
            }
        }
        with open(f"{notebook_path}/pyproject.toml", "w") as f:
            toml.dump(pyproject_content, f)
        os.umask(original_umask)
        return JupyterNBCommonResponse(status=True, message=f"Created Notebook")
    except Exception as e:
        logger.exception(f"Unable to clone: exception - {e}")
        if original_umask:
            os.umask(original_umask)
        return JupyterNBCommonResponse(
            status=False,
            message=f"Unable to create notebook {str(e)}",
        )


@router.post("/server/update_notebook_metadata")
async def update_notebook_metadata(
    project_id: Annotated[PydanticObjectId, Path()],
    update_request: JupyterNBCreateRequest,
    decoded_token: Annotated[dict, Depends(get_decoded_token)],
):
    original_umask = None
    try:
        original_umask = os.umask(
            0
        )  # this is needed as jupyter hub containers are not running as root but others are
        if not update_request.relative_path:
            raise ValueError(
                f"relative path cannot be empty for update metadata request"
            )

        pyproject_toml_file = f"{environment.jupyter_hub_folder}/{update_request.relative_path}/pyproject.toml"
        with open(pyproject_toml_file, "r") as f:
            pyproject_data = toml.load(f)
        if "project" in pyproject_data:
            pyproject_data["project"]["description"] = update_request.description
        with open(f"pyproject_toml_file", "w") as f:
            toml.dump(pyproject_data, f)
        os.umask(original_umask)
        return JupyterNBCommonResponse(
            status=True, message=f"Modified notebook description"
        )
    except Exception as e:
        logger.exception(f"Unable to clone: exception - {e}")
        if original_umask:
            os.umask(original_umask)
        return JupyterNBCommonResponse(
            status=False,
            message=f"Unable to modify notebook description {str(e)}",
        )


def run_bash_command(project_id: str, port: str) -> bool:
    try:
        # Define the socat command
        socat_command = f"socat TCP-LISTEN:{port},fork TCP:jupyter-{project_id}:{port}"

        # Run the command in the background
        process = subprocess.Popen(socat_command, shell=True)
        logger.info(f"socat is running with PID: {process.pid}")

        # No need to wait for the process to complete
        return True

    except Exception as e:
        logger.error(f"Failed to start socat: {e}")
        return False


@router.get("/server/get_free_port")
async def get_free_port(
    project_id: str,
) -> FreePortResponse:
    try:
        start_range = environment.external_app_port_start
        end_range = environment.external_app_port_end

        free_port = None
        # Find a free port
        """Find a free port within the provided range"""
        for port in range(start_range, end_range + 1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("localhost", port)) != 0:
                    free_port = port
                    break

        if not free_port:
            raise Exception(f"No free port found between {start_range} and {end_range}")
        else:
            if not run_bash_command(project_id, free_port):
                logger.error(f"Failed to bind port {free_port}", exc_info=True)
                raise Exception(f"Failed to bind port {free_port}")

        return FreePortResponse(status=True, message="Free port found", port=free_port)

    except Exception as e:
        return FreePortResponse(
            status=False, message=f"Error finding free port: {str(e)}", port=None
        )
