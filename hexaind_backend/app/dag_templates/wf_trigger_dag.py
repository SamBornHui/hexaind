from datetime import datetime
from pathlib import Path
from typing import Any, List

import jinja2

template_loader = jinja2.PackageLoader("app.dag_templates", "templates")
template_environment = jinja2.Environment(loader=template_loader)
dag_template = template_environment.get_template("wf_trigger_dag.py.jinja2")


def generate_dag_file(
    dag_id: str,
    site_id: str,
    workflow_id: str,
    project_id: str,
    path: Path,
    workflow_dag_id: str,
    start_date_input: str,
    end_date_input: str | None,
    schedule_interval_minutes: Any = None,
    tags: List[str] | None = None,
) -> str:
    if tags is None:
        tags = []

    # Parsing the input start and end dates
    date_format = "%Y-%m-%d %H:%M:%S"
    start_date = datetime.strptime(start_date_input, date_format)
    end_date = None
    if end_date_input:
        end_date = datetime.strptime(end_date_input, date_format)

    dag_content = dag_template.render(
        dag_id=dag_id,
        schedule_id=dag_id,
        schedule_interval_minutes=schedule_interval_minutes,
        start_date=repr(start_date),
        end_date=repr(end_date),
        workflow_id=workflow_id,
        workflow_dag_id=workflow_dag_id,
        site_id=site_id,
        project_id=project_id,
        tags=tags,
        path=path,
    )

    dag_file = Path("/opt/airflow/dags") / f"{dag_id}.py"
    with dag_file.open("w") as f:
        f.write(dag_content)
    return str(dag_file)
