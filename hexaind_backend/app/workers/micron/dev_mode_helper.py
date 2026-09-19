import logging
import time

from app.config.env_vars import environment
from app.core.celery.celery_worker import create_celery_app
from app.services.micron.data_catalog.fd_trace.dummy_files import DUMMY_FILES
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    DataCatalogStatus,
    DataPullResult,
    DataPullStatus,
    DesignIdDataPullOutput,
    FacilitiesDataPullOutput,
    FdContextDataPullOutput,
    FDDataPullStages,
    FdTraceDataPullOutput,
    FinalDataAggregateOutput,
    LotIdsDataPullOutput,
    ProbeContextDataPullOutput,
    ProbeDataPullOutputs,
    SensorsDataPullOutput,
    TechNodesDataPullOutput,
    TravelersIdDataPullOutput,
    TravelerStepDataPullOutput,
    UC2SigmaDataPullOutput,
    UC3SigmaOutput,
    WaferIdsDataPullOutput,
)
from app.workers.micron.commons import StageConfigJobHandler
from app.workers.micron.fd_helpers import post_process_probe_datapull
from app.workers.micron.utils import generate_preview_and_stats_for_all_result_files


def dev_mode_task(
    stage_config_job_handler: StageConfigJobHandler,
    stage_job_id: str,
    data_pull_job_id: str,
):
    final_result_file = None
    # Stage 1: Dry Run the query and get back result size
    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_VERIFICATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message="1/5 Completed",
        ),
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    time.sleep(5)

    # Stage 2: Register the job at bigquery
    dummy_job_id = "0123456789"
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_REGISTRATION
    current_status.job_stage_status.bigquery_job_id = dummy_job_id
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        "2/5 Completed. Successfully submitted job to bigquery"
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    time.sleep(5)

    # stage 3: query job monitoring
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        "3/5 Completed. Query is running at bigquery"
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    time.sleep(5)

    # stage 4: query results downloading from gcs bucket
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 90
    current_status.job_stage_status.progress_message = (
        "4/5 Completed. Downloading the reuslts"
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    time.sleep(5)

    # stage 5: placing the files in nfs mount or persistent storage
    current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
    current_status.job_stage_status.progress_percentage = 99
    current_status.job_stage_status.progress_message = (
        "5/5 Completed. Successfully saved the results."
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    match stage_config_job_handler.stage_job_record.stage:
        case FDDataPullStages.FACILITIES:
            final_result_file = DUMMY_FILES["facilities"]
            result = FacilitiesDataPullOutput(
                facilities=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TECH_NODE:
            final_result_file = DUMMY_FILES["tech_nodes"]
            result = TechNodesDataPullOutput(
                tech_nodes=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.DESIGN_ID:
            final_result_file = DUMMY_FILES["design_ids"]
            result = DesignIdDataPullOutput(
                design_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TRAVELER_ID:
            final_result_file = DUMMY_FILES["traveler_ids"]
            result = TravelersIdDataPullOutput(
                traveler_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TRAVELER_STEP:
            final_result_file = DUMMY_FILES["traveler_steps"]
            # finding baseline_line_traveler_id
            baseline_line_traveler_id = "BASE LINE TRAVELER ID"
            result = TravelerStepDataPullOutput(
                traveler_steps=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                ),
                baseline_line_traveler_id=baseline_line_traveler_id,
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_SENSOR:
            final_result_file = DUMMY_FILES["sensors"]
            result = SensorsDataPullOutput(
                sensors=DataPullResult.model_validate(dict(file_path=final_result_file))
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_CONTEXT:
            final_result_file = DUMMY_FILES["contexts"]
            result = FdContextDataPullOutput(
                fd_contexts=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_TRACE:
            final_result_file = DUMMY_FILES["traces"]
            result = FdTraceDataPullOutput(
                fd_trace=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.LOT_ID:
            final_result_file = DUMMY_FILES["lot_ids"]
            result = LotIdsDataPullOutput(
                lot_ids=DataPullResult.model_validate(dict(file_path=final_result_file))
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.WAFER_ID:
            final_result_file = DUMMY_FILES["lot_ids"]
            result = WaferIdsDataPullOutput(
                wafer_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FINAL_DATA_AGGREGATE:
            final_result_file = DUMMY_FILES["final_data_aggr"]
            result = FinalDataAggregateOutput(
                final_data=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.UC2_SIGMA_DATA:
            final_result_file = DUMMY_FILES["uc2_sigma"]
            result = UC2SigmaDataPullOutput(
                uc2_sigma_data=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.UC3_SIGMA_DATA:
            final_result_file = DUMMY_FILES["uc2_sigma"]
            result = UC3SigmaOutput(
                uc3_sigma_data=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.PROBE_CONTEXT:
            final_result_file = DUMMY_FILES["probe_context"]
            result = ProbeContextDataPullOutput(
                paretoname=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                ),
                paretotitle=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                ),
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.PROBE_DATA_PULL:
            final_result_file = DUMMY_FILES["probe_datapull"]
            if not stage_config_job_handler.stage_job_record.stage_config.inputs.uploaded_probe_data:
                final_result_file = post_process_probe_datapull(
                    final_result_file,
                    stage_config_job_handler.stage_job_record.stage_config.inputs,
                )
            result = ProbeDataPullOutputs(
                probe_data=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case _:
            final_result_file = None
            result = {
                "error": f"Invalid stage type in worker: {stage_config_job_handler.stage_job_record.stage}"
            }

    # updating the stage job and data pull job
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )
    print(f"### Dummy Task Done.(calculating preview..)")
    if final_result_file:
        generate_preview_and_stats_for_all_result_files(str(final_result_file))
    print(f"### Task Done")
    stage_config_job_handler.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_job_handler.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )
