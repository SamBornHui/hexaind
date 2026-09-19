import logging
import traceback
import uuid
from pathlib import Path
from typing import Any, Dict, Optional

import pyarrow as pa
import pyarrow.parquet as pq
import sqlalchemy
from pydantic import BaseModel
from sqlalchemy.engine import create_engine
from sqlalchemy.exc import SQLAlchemyError

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.core.services.action.schemas import (
    ActionRunStatus,
)
from app.core.services.action_handler.handler import ActionHandler
from app.services.data.assets.datasets.schemas import (
    DatasetMetadata,
    DatasetSourceFormats,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.workflows.designer.schemas import WidgetType
from app.workers.data_copy.data_pull_sql.helpers import BigQueryJobsManager
from app.services.micron.data_catalog.fd_trace.schemas import MultiSqlQuery

logger = logging.getLogger(__package__)

app = create_celery_app("sql_data_pull_worker")


class SQLDataPullConfig(BaseModel):
    connection_details: (
        Any  # Can be SQLAlchemy connection string or BigQuery Client object
    )
    query: str
    dataset_name: str
    batch_size: Optional[int] = 1000
    gcs_bucket: Optional[str] = None
    gcs_path: Optional[str] = None


@app.task(name="task_sql_data_pull")
def task_sql_data_pull(action_id: str, user_id: str, sql_config: Dict[str, Any], **kwargs):
    action_handler = ActionHandler(action_id)
    action = action_handler.get_action_record()

    if action.action_config.type != WidgetType.API_JOBS:
        raise Exception(
            f"Invalid action: {action.action_config.type} not supported by {WidgetType.API_JOBS} worker"
        )

    action_handler.update_run_status(status=ActionRunStatus.RUNNING)

    try:
        logger.info(f"{'*' * 30} SQL Data Pull Started {'*' * 30}")

        sql_params = SQLDataPullConfig(**sql_config)
        dataset_service = DatasetsService(db_sync_client=action_handler.db_client)

        project_id = kwargs.get("project_id")
        if not project_id:
            raise ValueError("Project ID is required.")

        output_dir: Path = environment.datasets_folder / f"p_{project_id}"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{uuid.uuid4()}.parquet"

        if sql_params.connection_details["connector_type"] == "BIGQUERY":
            bigquery_job_manager = BigQueryJobsManager(
                service_credentials=sql_params.connection_details,
                # gcs_bucket_name=sql_params.gcs_bucket,
                nfs_mount_path=environment.datasets_folder,
            )
            multi_query = MultiSqlQuery(
                sql_query=sql_params.query,
            )
            query_job, unique_id = bigquery_job_manager.submit_query_and_export_to_gcs(query=multi_query)
            job_status = bigquery_job_manager.monitor_job(query_job)
            if not job_status:
                raise Exception("BigQuery job failed.")

            output_path = bigquery_job_manager.download_from_gcs(unique_id, project_id)
            # gcs_temp_path = f"{sql_params.gcs_path}/{uuid.uuid4()}.parquet"
            # pull_bigquery_data(sql_params, gcs_temp_path)
            # download_from_gcs(sql_params.gcs_bucket, gcs_temp_path, output_path)
        else:
            pull_sql_data(sql_params, output_path)

        dataset_metadata = DatasetMetadata(
            data_source=DatasetSourceFormats.GENERATED_IN_WORKFLOW_EXECUTION_FORMAT.format(
                WidgetType.API_JOBS.value.lower()
            )
        )
        dataset_id = dataset_service.save_tabular_dataset_helper_sync(
            str(output_path),
            project_id=project_id,
            user_id=user_id,
            site_id=kwargs.get("site_id", "1"),
            action_id=action_id,
            # name=f"Dataset from SQL Pull ({action_handler.action_id})",
            name=sql_params.dataset_name,
            description=f"Dataset created from SQL query execution (Action ID: {action_handler.action_id})",
            metadata=dataset_metadata,
        )

        action_handler.action_success_handler(action_result_id=dataset_id)
        logger.info(f"{'*' * 30} SQL Data Pull Completed {'*' * 30}")

    except SQLAlchemyError as sql_err:
        logger.exception(f"SQLAlchemy Error: {sql_err}")
        action_handler.action_failure_handler(
            action_id=action_handler.action_id,
            exception_msg=str(sql_err),
            traceback_msg=traceback.format_exc(),
        )
    except Exception as e:
        logger.exception(f"Error in SQL Data Pull: {str(e)}")
        action_handler.action_failure_handler(
            action_id=action_id,
            exception_msg=str(e),
            traceback_msg=traceback.format_exc(),
        )


def pull_sql_data(sql_params: SQLDataPullConfig, output_path: Path):
    logger.info(f"Executing SQL query: {sql_params.query}")

    engine = create_engine(sql_params.connection_details["connection_string"])

    try:
        with engine.connect() as conn:
            result = conn.execution_options(stream_results=True).execute(
                sqlalchemy.text(sql_params.query)
            )
            schema = None
            writer = None

            while True:
                batch = result.fetchmany(sql_params.batch_size)
                if not batch:
                    break

                table = pa.Table.from_pylist([dict(row) for row in batch])
                if writer is None:
                    schema = table.schema
                    writer = pq.ParquetWriter(output_path, schema)

                writer.write_table(table)

            if writer:
                writer.close()
        logger.info(f"Successfully saved data to {output_path}")
    except Exception as e:
        logger.error(f"Error pulling SQL data: {str(e)}")
        raise
