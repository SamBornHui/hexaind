from datetime import datetime, timezone
import os
import shutil
from pathlib import Path
from time import sleep
import uuid

from airflow_client.api.dag_run_api import DAGRunApi
from airflow_client.api_client import ApiClient
from airflow_client.configuration import Configuration
from airflow_client.models.dag_run import DAGRun
from airflow_client.models.dag_state import DagState

from app.config.env_vars import airflow_environment, environment, jupyterhub_environment
from app.core.celery.celery_worker import create_celery_app
from app.core.schemas.action_result import (
    ActionResult,
    ActionResultType,
    StringActionResult,
)
from app.services.workflows.designer.schemas import JupyterConfig
from app.services.workflows.designer.service import WorkflowDesignerService
from app.services.workflows.sessions.service import WorkflowSessionService
from app.workers.utils import common_widget_manager
import base64

app = create_celery_app("jupyterhub_widget_worker")


def copy2_(src, dst, *, follow_symlinks=True):
    dst = shutil.copy2(src, dst, follow_symlinks=follow_symlinks)
    os.chmod(dst, 0o777, follow_symlinks=follow_symlinks)
    return dst


def generate_airflow_api_client() -> ApiClient:
    credentials = f"{airflow_environment.username}:{airflow_environment.password}"
    encoded_credentials = base64.b64encode(credentials.encode("utf-8")).decode("utf-8")
    return ApiClient(
        configuration=Configuration(
            host=f"{airflow_environment.url}api/v1",
        ),
        header_name="Authorization",
        header_value=f"Basic {encoded_credentials}",
    )


@app.task(name="task_jupyter")
def task_jupyterhub_widget(action_id: str):
    with common_widget_manager(app, action_id) as (
        action_handler,
        run_record,
        widget,
        new_dataset_dir,
    ):
        match widget.config:
            case JupyterConfig():
                pass
            case _:
                raise ValueError("invalid widget config")
        if run_record.workflow_id is None:
            raise ValueError("no workflow_id is set")
        workflow_designer_service = WorkflowDesignerService()
        workflow = workflow_designer_service.get_workflow_by_id(run_record.workflow_id)
        project_data = jupyterhub_environment.project_data(run_record.project_id)
        project_modules = jupyterhub_environment.project_modules(run_record.project_id)
        if not workflow.is_master:
            workflow_session_service = WorkflowSessionService()
            workflow_session = workflow_session_service.get_sessions_from_workflow_sync(
                workflow.id
            )
            workflow_dir = jupyterhub_environment.workflow_dir(
                run_record.project_id, workflow_session.workflow_id
            )
            published_dir = workflow_dir / "published" / workflow.workflow_version
            notebook_exec_dir = (
                workflow_dir
                / "published"
                / workflow.workflow_version
                / "runs"
                / f"r_{run_record.id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
            )
            shutil.copytree(
                published_dir / "master clone", notebook_exec_dir, copy_function=copy2_
            )
        else:
            workflow_dir = jupyterhub_environment.workflow_dir(
                run_record.project_id, run_record.workflow_id
            )
            notebook_exec_dir = workflow_dir / "master"
        airflow_api_client = generate_airflow_api_client()
        dag_run_api = DAGRunApi(airflow_api_client)
        dag_id = "jupyter_widget_dag"
        dag_run_id = f"jupyter_widget_run_{run_record.id}_{uuid.uuid4().hex}"
        dag_run = dag_run_api.post_dag_run(
            dag_id,
            DAGRun(
                dag_run_id=dag_run_id,
                conf={
                    "NOTEBOOK_IMAGE": widget.config.notebook_image,
                    "NOTEBOOK_DIR": widget.config.notebook_dir,
                    "NOTEBOOK_FILE": str(
                        Path(widget.config.notebook_dir)
                        / (notebook_exec_dir / widget.config.notebook_file).relative_to(
                            workflow_dir
                        )
                    ),
                    "CPU_LIMIT": widget.config.cpu_limit,
                    "MEMORY_LIMIT": widget.config.memory_limit,
                    "WORKFLOW_DIR": str(
                        environment.hexaind_destination
                        / workflow_dir.relative_to(environment.hexaind_data)
                    ),
                    "PROJECT_DATA": str(
                        environment.hexaind_destination
                        / project_data.relative_to(environment.hexaind_data)
                    ),
                    "PROJECT_MODULES": str(
                        environment.hexaind_destination
                        / project_modules.relative_to(environment.hexaind_data)
                    ),
                    "GOOGLE_APPLICATION_CREDENTIALS": environment.google_application_credentials,
                    "EXTERNAL_GOOGLE_CREDS_PATH": environment.external_google_creds_path,
                    "MLFLOW_TRACKING_URI": environment.mlflow_tracking_uri,
                },
            ),
        )
        while dag_run.state not in (DagState.FAILED, DagState.SUCCESS):
            sleep(10)
            dag_run = dag_run_api.get_dag_run(dag_id, dag_run_id)

        if dag_run.state == DagState.FAILED:
            raise RuntimeError("Jupyter Widget Run Failed")

        action_result_id = action_handler.create_action_result_record(
            ActionResult(
                output_name=dag_id,
                type=ActionResultType.STRING,
                result=StringActionResult(string_value=dag_run_id),
            )
        )
        action_handler.action_success_handler(
            action_result_id=action_result_id, append_results=False
        )
