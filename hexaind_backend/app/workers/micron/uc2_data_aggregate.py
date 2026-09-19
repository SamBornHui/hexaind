import uuid
from pathlib import Path

from app.config.env_vars import environment
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigqueryDataPullJobConfig,
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    DataCatalogStatus,
    DataPullResult,
    DataPullStatus,
    FinalDataAggregateConfig,
    FinalDataAggregateOutput,
)
from app.services.micron.data_catalog.fd_trace.service import FdTraceDataPullService
from app.workers.micron.commons import StageConfigJobHandler
from app.workers.micron.utils import (
    create_bigquery_manager,
    generate_preview_and_stats_for_all_result_files,
)


def final_data_aggregate_method(
    stage_config_job_handler: StageConfigJobHandler,
    stage_job_id: str,
    data_pull_job_id: str,
    user_name: str,
):
    stage_job_config_record = stage_config_job_handler.stage_job_record
    if not isinstance(
        (config := stage_job_config_record.stage_config), FinalDataAggregateConfig
    ):
        raise TypeError(f"Invalid Stage {stage_job_config_record.stage}")
    inputs = config.inputs
    if inputs is None:
        raise ValueError("no inputs are given")
    if inputs.facilities is None or not inputs.facilities.selected_values:
        raise ValueError("no facility is selected")
    if len(inputs.facilities.selected_values) > 1:
        raise ValueError("only one facility is supported")
    facility = inputs.facilities.selected_values[0]
    if inputs.design_ids is None or not inputs.design_ids.selected_values:
        raise ValueError("no design_id is selected")
    if len(inputs.design_ids.selected_values) > 1:
        raise ValueError("only one design_id is supported")
    design_id = inputs.design_ids.selected_values[0]
    if inputs.traveler_ids is None or not inputs.traveler_ids.selected_values:
        raise ValueError("no traveler_ids are selected")
    traveler_ids = inputs.traveler_ids.selected_values
    if inputs.traveler_steps is None or not inputs.traveler_steps.selected_values:
        raise ValueError("no traveler_steps are selected")
    traveler_steps = inputs.traveler_steps.selected_values
    if inputs.recipes is None or not inputs.recipes.selected_values:
        raise ValueError("no recipes are selected")
    recipes = inputs.recipes.selected_values
    if inputs.tool_ids is None or not inputs.tool_ids.selected_values:
        raise ValueError("no tool_ids are selected")
    tool_ids = inputs.tool_ids.selected_values
    if inputs.step_ids is None or not inputs.step_ids.selected_values:
        raise ValueError("no step_ids are selected")
    step_ids = inputs.step_ids.selected_values
    if inputs.sensors is None or not inputs.sensors.selected_values:
        raise ValueError("no sensors are selected")
    sensors = inputs.sensors.selected_values
    start_date = inputs.start_date
    end_date = inputs.end_date
    final_data_aggregate_context_file = inputs.recipes.file_path

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_VERIFICATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=0,
            progress_message="Query Verification",
        ),
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    multi_sql_queries = FdTraceDataPullService.get_final_data_aggregate_queries(
        facility=facility,
        design_id=design_id,
        traveler_ids=traveler_ids,
        traveler_steps=traveler_steps,
        recipes=recipes,
        tool_ids=tool_ids,
        step_ids=step_ids,
        sensors=sensors,
        start_date=start_date,
        end_date=end_date,
        final_data_aggregate_context_file=final_data_aggregate_context_file,
    )

    datacatalog_session_record = stage_config_job_handler.datacatalog_session_record
    job_creation_time = datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    bigquery_job_config = BigqueryDataPullJobConfig(**config.status.job_config)
    bigquery_job_config.sql_query = multi_sql_queries

    bigquery_manager = create_bigquery_manager(
        bigquery_job_config=bigquery_job_config,
        nfs_mount_path=str(environment.hexaind_data).format(user_name=user_name),
    )

    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 25
    current_status.job_stage_status.progress_message = "Query Execution"
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )
    unique_downloaded_id = uuid.uuid4()
    result_files = []
    for index, multi_sql_query in enumerate(multi_sql_queries):
        try:
            # submitting job
            bq_job, result_folder_blob_name = (
                bigquery_manager.submit_query_and_export_to_gcs(multi_sql_query)
            )
            # monitoring job
            query_execution_status = bigquery_manager.monitor_job(query_jobs=[bq_job])
            if not query_execution_status:
                raise Exception(f"Bigquery jobs for stage got failed. {stage_job_id=}")
            # downloading job results
            destination_folder_path_ = (
                Path(
                    environment.tdam_datacatalog_databrick_session_path_format.format(
                        data_pull_job_id
                    )
                )
                / f"{user_name}/results/uc3_final_data_aggregation/temp_{unique_downloaded_id}/{index}"
            )
            destination_folder_path_.mkdir(exist_ok=True, parents=True)
            destination_folder_path = str(destination_folder_path_)
            bigquery_manager.download_from_gcs(
                gcs_folder_name=result_folder_blob_name,
                job_creation_time=job_creation_time,
                job_name=datacatalog_session_record.name.lower().replace(" ", "_"),
                destination_dirname=destination_folder_path,
                add_base_destination=False,
            )
            result_files.append(destination_folder_path_)
        except Exception as e:
            print(f"failed to complete query execution {e} :  {multi_sql_query}")
            continue

    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.bigquery_job_id = ""
    current_status.job_stage_status.progress_message = "Query Result Download"
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
    current_status.job_stage_status.progress_percentage = 85
    current_status.job_stage_status.bigquery_job_id = ""
    current_status.job_stage_status.progress_message = "Saving Results"
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    uc2_fd_aggr_final_destination = (
        Path(
            environment.tdam_datacatalog_databrick_session_path_format.format(
                data_pull_job_id
            )
        )
        / f"{user_name}/results/uc3_final_data_aggregation/{unique_downloaded_id}/result.parquet"
    )
    uc2_fd_aggr_final_destination.parent.mkdir(exist_ok=True, parents=True)
    FdTraceDataPullService.get_final_data_aggregate(
        result_files, uc2_fd_aggr_final_destination
    )

    result = FinalDataAggregateOutput(
        final_data=DataPullResult.model_validate(
            dict(file_path=uc2_fd_aggr_final_destination)
        )
    ).model_dump(by_alias=True, mode="json")

    # updating the stage job and data pull job
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )

    stage_config_job_handler.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_job_handler.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )
    print("### Task Done(calculating preview and stats)")
    generate_preview_and_stats_for_all_result_files(str(uc2_fd_aggr_final_destination))
    print("### Task Done")
