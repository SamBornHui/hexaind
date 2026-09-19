import logging
import os
import time
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigqueryDataPullJobConfig,
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    DataCatalogStatus,
    DataPullResult,
    DataPullStatus,
    FdDataPullJobConfig,
    FDDataPullStages,
    UC2SigmaDataPullOutput,
    UC3FDContextApplyFiltersOutput,
)
from app.services.micron.data_catalog.schemas import MicronDataCatalog
from app.workers.micron.bigquery_job_helper import bigquery_job_method
from app.workers.micron.commons import (
    StageConfigJobHandler,
    common_data_pull_stage_manager,
)
from app.workers.micron.dev_mode_helper import dev_mode_task
from app.workers.micron.uc2_data_aggregate import final_data_aggregate_method
from app.workers.micron.uc2_sigma_helpers_new import uc2_sigma_data_pull_new
from app.workers.micron.uc3_probe_helpers import probe_datapull_method
from app.workers.micron.uc3_sigma_helpers import uc3_sigma_method
from app.workers.micron.utils import (
    create_bigquery_manager,
    generate_preview_and_stats_for_all_result_files,
)

HEXAIND_DATA: str = str(environment.hexaind_data)

logger = logging.getLogger(__package__)

app = create_celery_app("micron_data_pull_stage_worker")

SINGLE_QUERY_STAGES = [
    FDDataPullStages.FACILITIES,
    FDDataPullStages.TECH_NODE,
    FDDataPullStages.DESIGN_ID,
    FDDataPullStages.TRAVELER_ID,
    FDDataPullStages.FD_CONTEXT,
    FDDataPullStages.FD_SENSOR,
]

MULTIPLE_QUERY_STAGES = [FDDataPullStages.TRAVELER_STEP, FDDataPullStages.FD_TRACE]


@app.task(name="task_data_processing_stage")
def task_data_processing_stage(
    data_pull_job_id: str, stage_job_id: str, user_name: str
):
    print_msg = f"Job: {data_pull_job_id}-{stage_job_id}-{user_name}"

    print("****************************")
    print(f"{print_msg}: New Task Init.")
    print("****************************")

    with common_data_pull_stage_manager(
        app, data_pull_job_id, stage_job_id
    ) as stage_config_obj:
        datacatalog_session_record: MicronDataCatalog = (
            stage_config_obj.datacatalog_session_record
        )

        job_creation_time = datacatalog_session_record.created_at.strftime(
            "%Y-%m-%d_%H-%M-%S"
        )

        if (
            stage_config_obj.stage_job_record.stage
            == FDDataPullStages.UC3_FD_CONTEXT_APPLY_FILTERS
        ):
            aggregated_results_file = (
                HEXAIND_DATA.format(user_name=user_name)
                + f"/task_data_processing_stage_{job_creation_time}/data_pull_job_id.parquet"
            )
            combined_df = pd.concat(
                [
                    pd.read_parquet(filter_obj.path)
                    for filter_obj in stage_config_obj.stage_job_record.stage_config.inputs.filters
                ],
                ignore_index=True,
            )
            aggregated_results_file_path = Path(aggregated_results_file)
            aggregated_results_file_path.parent.mkdir(parents=True, exist_ok=True)
            current_status = BigQueryDataPullJobStatus(
                job_stage=BigQueryDataPullJobStage.SAVING_RESULTS,
                job_stage_status=BigQueryJobStatus(
                    total_bytes_processed="121",
                    total_bytes_billed="$0",
                    progress_percentage=100,
                    progress_message="Completed aggregating results...",
                ),
            )
            combined_df.to_parquet(aggregated_results_file)
            current_status.job_stage_status.bigquery_job_id = "NotApplicable"
            stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
                job_id=stage_job_id, new_status=current_status
            )
            time.sleep(5)

            result = UC3FDContextApplyFiltersOutput(
                aggregated_file_path=aggregated_results_file
            ).model_dump(by_alias=True, mode="json")
            # TODO: USE UC3FDContextApplyFiltersDataPullConfig()
        else:
            result = {
                "error": f"Invalid stage type in worker: {stage_config_obj.stage_job_record.stage}"
            }

        # updating the stage job and data pull job
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
            job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
        )
        stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
            job_id=data_pull_job_id,
            current_stage=stage_config_obj.stage_job_record.stage,
            current_stage_status=DataCatalogStatus.IDLE,
        )


def uc2_sigma_method(stage_config_obj, stage_job_id, data_pull_job_id, user_name):
    stage_job_config_record: FdDataPullJobConfig = stage_config_obj.stage_job_record
    bigquery_job_config: BigqueryDataPullJobConfig = BigqueryDataPullJobConfig(
        **stage_job_config_record.stage_config.status.job_config
    )
    bigquery_manager = create_bigquery_manager(
        bigquery_job_config=bigquery_job_config,
        nfs_mount_path=HEXAIND_DATA.format(user_name=user_name),
    )

    unique_file_identifier = str(uuid.uuid4())
    uc2_sigma_results_folder_path = (
        Path(
            environment.tdam_datacatalog_databrick_session_path_format.format(
                data_pull_job_id
            )
        )
        / f"{user_name}/results/uc2_sigma/{unique_file_identifier}"
    )

    uc2_sigma_results_folder_path.mkdir(exist_ok=True, parents=True)

    res = uc2_sigma_data_pull_new(
        bigquery_manager,
        stage_config_obj,
        stage_job_id,
        str(uc2_sigma_results_folder_path),
    )

    print(f"--results--{res}")

    print(f"### updating all the DB records")
    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.SAVING_RESULTS,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=100,
            progress_message="..saving results.",
        ),
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    result = UC2SigmaDataPullOutput(
        uc2_sigma_data=DataPullResult.model_validate(
            dict(file_path=uc2_sigma_results_folder_path)
        )
    ).model_dump(by_alias=True, mode="json")

    # updating the stage job and data pull job
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )

    stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_obj.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )

    print("### Task Done.(calculating preview..)")
    generate_preview_and_stats_for_all_result_files(str(uc2_sigma_results_folder_path))
    print("### Task Done")


@app.task(name="task_data_pull_stage")
def task_micron_data_pull(
    data_pull_job_id: str,
    stage_job_id: str,
    user_name: str,
    pull_directly_to_hexaind_platform: bool = False,
    override_destination: Optional[str] = None,
):
    with common_data_pull_stage_manager(
        app, data_pull_job_id, stage_job_id
    ) as stage_config_job_handler:
        if environment.dev_mode:
            dev_mode_task(
                stage_config_job_handler,
                stage_job_id,
                data_pull_job_id=data_pull_job_id,
            )
        else:
            if pull_directly_to_hexaind_platform:
                override_path = str(
                    environment.override_tdam_datacatalog_sessions_path_for_cpw(
                        stage_job_id,
                        stage_config_job_handler.stage_job_record.stage.value,
                    )
                )
                override_gcp_creds_file = os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
            else:
                override_path = None
                override_gcp_creds_file = None
            match stage_config_job_handler.stage_job_record.stage:
                case FDDataPullStages.UC2_SIGMA_DATA:  # UC2 JOB CONFIG
                    uc2_sigma_method(
                        stage_config_job_handler,
                        stage_job_id,
                        data_pull_job_id,
                        user_name,
                    )
                case FDDataPullStages.UC3_SIGMA_DATA:  # UC3 JOB CONFIG
                    # check if lots and wafers are filtered
                    selected_lots = None
                    selected_wafers = None
                    lot_ids_stage_id = stage_config_job_handler.data_pull_job_record.lot_ids_stage_job_id
                    wafer_ids_stage_id = stage_config_job_handler.data_pull_job_record.wafer_ids_stage_job_id
                    lots_stage = stage_config_job_handler.fd_trace_job_dao.get_fd_data_pull_job_config_record_sync(
                        lot_ids_stage_id
                    )
                    wafers_stage = stage_config_job_handler.fd_trace_job_dao.get_fd_data_pull_job_config_record_sync(
                        wafer_ids_stage_id
                    )
                    if (
                        lots_stage.stage_config is not None
                        and lots_stage.stage_config.outputs is not None
                    ):
                        selected_lots = (
                            lots_stage.stage_config.outputs.lot_ids.selected_values
                        )
                    if (
                        wafers_stage.stage_config is not None
                        and wafers_stage.stage_config.outputs is not None
                    ):
                        selected_wafers = (
                            wafers_stage.stage_config.outputs.wafer_ids.selected_values
                        )

                    uc3_sigma_method(
                        stage_config_job_handler,
                        stage_job_id,
                        data_pull_job_id,
                        user_name,
                        selected_lots,
                        selected_wafers,
                        override_path,
                        override_gcp_creds_file=override_gcp_creds_file,
                    )
                case FDDataPullStages.FINAL_DATA_AGGREGATE:  # FINAL DATA AGGREGATE CONFIG
                    final_data_aggregate_method(
                        stage_config_job_handler,
                        stage_job_id,
                        data_pull_job_id,
                        user_name,
                    )
                case FDDataPullStages.PROBE_DATA_PULL:
                    probe_datapull_method(
                        stage_config_job_handler,
                        stage_job_id,
                        data_pull_job_id,
                        user_name,
                        override_path,
                        override_gcp_creds_file=override_gcp_creds_file,
                    )
                case _:  # BIGQUERY JOB CONFIG
                    bigquery_job_method(
                        stage_config_job_handler,
                        stage_job_id,
                        data_pull_job_id,
                        user_name,
                        pull_directly_to_hexaind_platform=pull_directly_to_hexaind_platform,
                        override_destination=override_destination,
                    )
