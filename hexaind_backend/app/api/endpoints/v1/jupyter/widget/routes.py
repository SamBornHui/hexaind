from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from jupyterhub_client.api.default_api import DefaultApi
from jupyterhub_client.api_client import ApiClient
from jupyterhub_client.configuration import Configuration
from jupyterhub_client.exceptions import ApiException
from pydantic import BaseModel, StrictBool, StrictStr

from app.config.env_vars import environment, jupyterhub_environment
from app.services.workflows.designer.schemas import JupyterServerConfig
from app.services.workflows.sessions.service import WorkflowSessionService

logger = logging.getLogger(__package__)


router = APIRouter(prefix="/widget", tags=["Jupyter", "JupyterWidget"])


def generate_jupyterhub_api_client() -> DefaultApi:
    configuration = Configuration(
        host=f"{jupyterhub_environment.api_url}/hub/api",
        access_token=jupyterhub_environment.api_token,
    )
    api_client = ApiClient(configuration)
    return DefaultApi(api_client)


class ServerResponse(BaseModel):
    ready: StrictBool
    url: StrictStr


@router.post("/servers/{project_id}/{workflow_session_id}")
def create_server(
    project_id: str,
    workflow_session_id: str,
    server_config: JupyterServerConfig,
    run_id: Optional[str] = None,
    jupyterhub_api: DefaultApi = Depends(generate_jupyterhub_api_client),
) -> ServerResponse:
    try:
        workflow_session_service = WorkflowSessionService()
        workflow_session = workflow_session_service.get_workflow_session(
            workflow_session_id
        )
        workflow_id = workflow_session.workflow_id
        server_name = f"{project_id}_{workflow_id}"

        workflow_dir = jupyterhub_environment.workflow_dir(project_id, workflow_id)
        project_data = jupyterhub_environment.project_data(project_id)
        project_modules = jupyterhub_environment.project_modules(project_id)
        runs_dir: Optional[Path] = None
        if run_id:
            runs_dir = next(
                (
                    workflow_dir
                    / "published"
                    / "runs"
                ).rglob(f"r_{run_id}*"),
                None,
            )
        # checking if server doesn't exists
        user = jupyterhub_api.get_current_user()
        if not user.servers or server_name not in user.servers:
            notebook_dir = Path(server_config.notebook_dir)
            env: Dict[str, str] = {
                "GOOGLE_APPLICATION_CREDENTIALS": environment.google_application_credentials,
                "PROJECT_DATA": str(notebook_dir / "project" / "data"),
                "PROJECT_MODULES": str(notebook_dir / "project" / "modules"),
                "WORKFLOW_DATA": str(notebook_dir / "data"),
                "MLFLOW_TRACKING_URI": environment.mlflow_tracking_uri,
            }
            mounts = [
                dict(
                    target=str(notebook_dir),
                    source=str(
                        environment.hexaind_destination
                        / workflow_dir.relative_to(environment.hexaind_data)
                    ),
                    type="bind",
                    read_only=False,
                ),
                dict(
                    target=str(notebook_dir / "project" / "data"),
                    source=str(
                        environment.hexaind_destination
                        / project_data.relative_to(environment.hexaind_data)
                    ),
                    type="bind",
                    read_only=False,
                ),
                dict(
                    target=str(notebook_dir / "project" / "modules"),
                    source=str(
                        environment.hexaind_destination
                        / project_modules.relative_to(environment.hexaind_data)
                    ),
                    type="bind",
                    read_only=False,
                ),
            ]
            if environment.external_google_creds_path and environment.google_application_credentials:
                mounts.append(
                    dict(
                        target=environment.google_application_credentials,
                        source=environment.external_google_creds_path,
                        type="bind",
                        read_only=True,
                    )
                )
            # creating server
            jupyterhub_api.post_user_server_name(
                name=user.name if user.name else "",
                server_name=server_name,
                body={
                    "cpu_limit": server_config.cpu_limit,
                    "memory_limit": server_config.memory_limit,
                    "notebook_image": server_config.notebook_image,
                    "notebook_dir": server_config.notebook_dir,
                    "mounts": mounts,
                    "environment": env,
                },
            )
            # refreshing user
            user = jupyterhub_api.get_current_user()
        # checking if server doesn't exist
        if not user.servers or server_name not in user.servers:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create server",
            )
        server = user.servers[server_name]
        return ServerResponse(
            ready=server.ready or False,
            url=f"{server.full_url}/lab/tree/{runs_dir.relative_to(workflow_dir)}"
            if runs_dir
            else server.full_url or "",
        )
    except ApiException as e:
        raise HTTPException(
            status_code=e.status,  # type: ignore
            detail=e.data,
        )


@router.get("/servers/{project_id}/{workflow_session_id}")
def get_server(
    project_id: str,
    workflow_session_id: str,
    run_id: Optional[str] = None,
    jupyterhub_api: DefaultApi = Depends(generate_jupyterhub_api_client),
) -> ServerResponse:
    try:
        user = jupyterhub_api.get_current_user()
        workflow_session_service = WorkflowSessionService()
        workflow_session = workflow_session_service.get_workflow_session(
            workflow_session_id
        )
        workflow_id = workflow_session.workflow_id
        server_name = f"{project_id}_{workflow_id}"

        workflow_dir = jupyterhub_environment.workflow_dir(project_id, workflow_id)
        runs_dir: Optional[Path] = None
        if run_id:
            runs_dir = next(
                (
                    workflow_dir
                    / "published"
                    / workflow_session.saved_workflows[0].workflow_version
                    / "runs"
                ).rglob(f"r_{run_id}_*.ipynb"),
                None,
            )
        # checking if server doesn't exist
        if not user.servers or server_name not in user.servers:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Unable to create server",
            )
        server = user.servers[server_name]
        return ServerResponse(
            ready=server.ready or False,
            url=f"{server.full_url}/lab/tree/{runs_dir.relative_to(workflow_dir)}"
            if runs_dir
            else server.full_url or "",
        )
    except ApiException as e:
        raise HTTPException(
            status_code=e.status,  # type: ignore
            detail=e.data,
        )


@router.get("/notebooks/{project_id}/{workflow_session_id}")
async def get_notebooks(
    project_id: str,
    workflow_session_id: str,
) -> List[str]:
    workflow_session_service = WorkflowSessionService()
    workflow_session = workflow_session_service.get_workflow_session(
        workflow_session_id
    )
    workflow_working_dir = (
        jupyterhub_environment.workflow_dir(project_id, workflow_session.workflow_id)
        / "master"
    )
    return [path.name for path in workflow_working_dir.glob("*.ipynb")]
