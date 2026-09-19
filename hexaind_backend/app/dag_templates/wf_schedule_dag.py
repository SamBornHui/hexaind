from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, Optional

import jinja2
from docker.types import Mount

from app.config.env_vars import (
    environment,
    celery_environment,
    airflow_environment,
    rescale_environment,
    jupyterhub_environment,
    thermocalc_environment,
    gateway_environment,
)
from app.core.services.cloud_utils.utils import get_secret_manager
from app.services.workflows.scheduling.schemas import RepeatType

template_loader = jinja2.PackageLoader("app.dag_templates", "templates")
template_environment = jinja2.Environment(loader=template_loader)
dag_template = template_environment.get_template("wf_scheduler_dag.py.jinja2")


def generate_dag_file(
    task_name: str,
    dag_id: str,
    site_id: str,
    workflow_id: str,
    project_id: str,
    token: str,
    start_date_input: str,
    end_date_input: str | None,
    schedule_interval_minutes: Any = None,
    tags: List[Any] = None,
    repeat_type: Optional[RepeatType] = RepeatType.NONE,
    repeat_value: Optional[int] = 1,
) -> str:
    if tags is None:
        tags = []

    # Parsing the input start and end dates
    date_format = "%Y-%m-%d %H:%M:%S"
    start_date = datetime.strptime(start_date_input, date_format)
    end_date = None
    if end_date_input:
        end_date = datetime.strptime(end_date_input, date_format)

    # Get cloud environment settings from configured provider
    secret_manager = get_secret_manager()
    cloud_env = secret_manager.env
    
    dag_content = dag_template.render(
        dag_id=dag_id,
        schedule_id=dag_id,
        schedule_interval_minutes=repr(schedule_interval_minutes),
        start_date=repr(start_date),
        end_date=repr(end_date),
        workflow_id=workflow_id,
        site_id=site_id,
        project_id=project_id,
        token=token,
        tags=tags,
        task_id=task_name.strip().replace(" ", "_"),
        repeat_type=repeat_type.value,
        repeat_val=repeat_value,
        mounts=[
            repr(mount)
            for mount in [
                Mount(
                    source=environment.container_socket,
                    target="/var/run/docker.sock",
                    type="bind",
                ),
                Mount(
                    source="hexaind-data",
                    target=str(environment.hexaind_data),
                    type="volume",
                ),
                Mount(
                    source="hexaind-drive",
                    target=str(environment.hexaind_drive),
                    type="volume",
                ),
                Mount(
                    source="hexaind-logs",
                    target=str(environment.hexaind_home / "logs"),
                    type="volume",
                ),
            ]
        ],
        environment={
            key: str(value)
            for key, value in {
                **environment.model_dump(by_alias=True),
                **celery_environment.model_dump(by_alias=True),
                **airflow_environment.model_dump(by_alias=True),
                **rescale_environment.model_dump(by_alias=True),
                **jupyterhub_environment.model_dump(by_alias=True),
                **thermocalc_environment.model_dump(by_alias=True),
                **gateway_environment.model_dump(by_alias=True),
                **cloud_env.model_dump(by_alias=True),
            }.items()
            if value is not None
        },
    )

    dag_file = Path("/opt/airflow/dags") / f"{dag_id}.py"
    with dag_file.open("w") as f:
        f.write(dag_content)
    return str(dag_file)
