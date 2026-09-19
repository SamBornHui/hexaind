import uuid
from itertools import chain
from pathlib import Path
from typing import Optional

from app.config.env_vars import environment
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigqueryDataPullJobConfig,
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    DataCatalogStatus,
    DataPullResult,
    DataPullStatus,
    MultiSqlQuery,
    UC3SigmaDataPullConfig,
    UC3SigmaOutput,
)
from app.services.micron.data_catalog.uc3.sigma.pivot import (
    uc3_point_data_pivot_on_full_step,
    uc3_wafer_data_pivot_on_full_step,
)
from app.services.micron.data_catalog.uc3.sigma.query import (
    generate_optional_query,
    generate_wafer_query,
    genereted_point_query,
)
from app.workers.micron.commons import StageConfigJobHandler
from app.workers.micron.utils import (
    copy_parquet_files,
    create_bigquery_manager,
    generate_preview_and_stats_for_all_result_files,
)


def uc3_sigma_method(
    stage_config_job_handler: StageConfigJobHandler,
    stage_job_id: str,
    data_pull_job_id: str,
    user_name: str,
    filtered_lots=None,
    filtered_wafers=None,
    override_uc3_sigma_final_results_folder: Optional[str] = None,
    override_gcp_creds_file: Optional[str] = None,
):
    print("override uc3 values..")
    print(override_uc3_sigma_final_results_folder)
    print(override_gcp_creds_file)
    print("=========================")
    stage_job_config_record = stage_config_job_handler.stage_job_record
    if not isinstance(
        (config := stage_job_config_record.stage_config), UC3SigmaDataPullConfig
    ):
        raise TypeError(f"Invalid Stage {stage_job_config_record.stage}")
    inputs = config.inputs
    print("config----")
    print(config.model_dump())
    print("--------")
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
    cached_traveler_steps = inputs.cached_traveler_steps
    if (
        inputs.metro_step_common_step_ids[0].uc3_sigma_metro_steps is None
        or not inputs.metro_step_common_step_ids[
            0
        ].uc3_sigma_metro_steps.selected_values
    ):
        raise ValueError("no metro_steps are selected")
    steps_prefix_by_user = list(
        chain.from_iterable(
            inputs.metro_step_common_step_ids[0].uc3_sigma_metro_steps.selected_values
        )
    )
    unique_steps_prefixes = frozenset(steps_prefix_by_user)
    steps_list = [
        step for step in cached_traveler_steps if step[:4] in unique_steps_prefixes
    ]
    if inputs.regions is None or not inputs.regions.selected_values:
        region = None
    elif len(inputs.regions.selected_values) > 1:
        raise ValueError("only one region is supported")
    else:
        region = inputs.regions.selected_values[0]

    # lot ids and wafer id's that got from filtering.. in another stages
    if filtered_lots and filtered_wafers:
        # make it as tuple to directly using in queries
        filtered_lots = str(tuple(filtered_lots)).replace(",)", ")")
        filtered_wafers = str(tuple(filtered_wafers)).replace(",)", ")")
    else:
        # ignoring cases where either one of these are filtered for now.
        filtered_wafers = None
        filtered_lots = None

    unique_id = uuid.uuid4().hex
    start_date = inputs.start_date
    end_date = inputs.end_date
    start_date_padding = end_date_padding = inputs.padding_days

    # final results will be present in this folder
    if override_uc3_sigma_final_results_folder:
        uc3_sigma_final_results_folder = (
            Path(override_uc3_sigma_final_results_folder) / f"{unique_id}"
        )
    else:
        uc3_sigma_final_results_folder = (
            environment.tdam_datacatalog_sessions_path(data_pull_job_id)
            / f"{user_name}/results/uc3_sigma/{unique_id}"
        )

    uc3_sigma_final_results_folder.mkdir(exist_ok=True, parents=True)
    wafer_data_file_path = uc3_sigma_final_results_folder / "wafer_data.parquet"
    point_data_file_path = uc3_sigma_final_results_folder / "point_data.parquet"

    # steps = list(set(chain.from_iterable(
    #     list(chain.from_iterable(row.uc3_sigma_metro_steps.selected_values))
    #     for row in inputs.metro_step_common_step_ids
    #     if row.uc3_sigma_metro_steps is not None and row.uc3_sigma_metro_steps.selected_values is not None
    # )))

    include_back = inputs.integrate_back_of_wafer_mesurement
    wafer_drop_na_threshold = 0.95
    points_drop_na_threshold = 0.95

    datacatalog_session_record = stage_config_job_handler.datacatalog_session_record
    job_creation_time = datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_VERIFICATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=0,
            progress_message="Registering query",
        ),
    )
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    if override_gcp_creds_file:
        config.status.job_config["authentication"]["auth_config"][
            "application_credentials_file_path"
        ] = Path(override_gcp_creds_file)
    bigquery_job_config = BigqueryDataPullJobConfig(**config.status.job_config)
    bigquery_job_config.sql_query = []
    bigquery_manager = create_bigquery_manager(
        bigquery_job_config=bigquery_job_config,
        nfs_mount_path=str(environment.hexaind_data).format(user_name=user_name),
    )

    print(f"{len(steps_list)} unique_mfg_process_steps filtered.")
    unique_mfg_process_steps_str = str(tuple(steps_list)).replace(",)", ")")

    wafer_test_id_pairs = inputs.metro_step_common_step_ids[
        0
    ].common_test_ids.selected_values
    print(wafer_test_id_pairs)
    print("------------------------")

    print("completed fetching manufacturing steps")
    optional_query = generate_optional_query(
        wafer_test_id_pairs=wafer_test_id_pairs, include_back=include_back
    )

    # wafer stage
    if inputs.wafer_level:
        print("entered wafer level...")
        wafer_declarations, wafer_query = generate_wafer_query(
            fab=facility,
            design_id=design_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            start_date_padding=start_date_padding,
            end_date_padding=end_date_padding,
            wafer_test_id_pairs=wafer_test_id_pairs,
            unique_mfg_process_steps=unique_mfg_process_steps_str,
            include_back=include_back,
            optional_query=optional_query,
            filtered_lot_ids=filtered_lots,
            filtered_wafer_ids=filtered_wafers,
        )
        wafer_multi_sql_query = MultiSqlQuery(
            sql_query=wafer_query,
            declarations=wafer_declarations,
        )
        wafer_job, wafer_folder_blob_name = (
            bigquery_manager.submit_query_and_export_to_gcs(wafer_multi_sql_query)
        )
        # Stage 2: Register the job at bigquery
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
        current_status.job_stage_status.bigquery_job_id = wafer_job.job_id
        current_status.job_stage_status.progress_percentage = 50
        current_status.job_stage_status.progress_message = (
            "Registered Wafer Query, starting Execution"
        )
        stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        wafer_query_execution_status = bigquery_manager.monitor_job(
            query_jobs=[wafer_job]
        )
        if not wafer_query_execution_status:
            raise Exception(f"Wafer Query Execution got failed. {stage_job_id=}")
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
        current_status.job_stage_status.progress_percentage = 75
        current_status.job_stage_status.progress_message = "Downloading Wafer data"
        stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        wafers_folder_path_temp = (
            environment.tdam_datacatalog_sessions_path(data_pull_job_id)
            / f"{user_name}/results/uc3_sigma/{unique_id}_temp/wafer"
        )
        wafers_folder_path_temp.mkdir(exist_ok=True, parents=True)
        bigquery_manager.download_from_gcs(
            gcs_folder_name=wafer_folder_blob_name,
            job_creation_time=job_creation_time,
            job_name=datacatalog_session_record.name.lower().replace(" ", "_"),
            destination_dirname=str(wafers_folder_path_temp),
            add_base_destination=False,
        )
        print(f"completed fetching wafer level. {wafers_folder_path_temp}")
        # writing to file results folder  to final results folder[unpivoted data]
        copy_parquet_files(wafers_folder_path_temp, wafer_data_file_path)

    # points stage
    if inputs.point_level:
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_VERIFICATION
        current_status.job_stage_status.bigquery_job_id = ""
        current_status.job_stage_status.progress_percentage = 0
        current_status.job_stage_status.progress_message = "Verifing Point Query"
        stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        point_declarations, point_query = genereted_point_query(
            fab=facility,
            design_id=design_id,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            start_date_padding=start_date_padding,
            end_date_padding=end_date_padding,
            point_steps_list=unique_mfg_process_steps_str,
            optional_query=optional_query,
            filtered_lot_ids=filtered_lots,
            filtered_wafer_ids=filtered_wafers,
        )
        point_multi_sql_query = MultiSqlQuery(
            sql_query=point_query,
            declarations=point_declarations,
        )
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_REGISTRATION
        current_status.job_stage_status.bigquery_job_id = ""
        current_status.job_stage_status.progress_percentage = 50
        current_status.job_stage_status.progress_message = (
            "Registered Point Query, starting Execution"
        )
        stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        point_job, point_folder_blob_name = (
            bigquery_manager.submit_query_and_export_to_gcs(point_multi_sql_query)
        )
        point_query_execution_status = bigquery_manager.monitor_job(
            query_jobs=[point_job]
        )
        if not point_query_execution_status:
            raise Exception(f"point Query Execution got failed. {stage_job_id=}")
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
        current_status.job_stage_status.bigquery_job_id = point_job.job_id
        current_status.job_stage_status.progress_percentage = 75
        current_status.job_stage_status.progress_message = "Downloading Point data"
        stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        points_folder_path_temp = (
            environment.tdam_datacatalog_sessions_path(data_pull_job_id)
            / f"{user_name}/results/uc3_sigma/{unique_id}_temp/point"
        )
        points_folder_path_temp.mkdir(exist_ok=True, parents=True)
        bigquery_manager.download_from_gcs(
            gcs_folder_name=point_folder_blob_name,
            job_creation_time=job_creation_time,
            job_name=datacatalog_session_record.name.lower().replace(" ", "_"),
            destination_dirname=str(points_folder_path_temp),
            add_base_destination=False,
        )
        print(f"completed fetching point level. {points_folder_path_temp}")
        # writing to file results folder  to final results folder[unpivoted data]
        copy_parquet_files(points_folder_path_temp, point_data_file_path)

    # pivoting
    ## wafer level
    current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
    current_status.job_stage_status.progress_percentage = 90
    current_status.job_stage_status.bigquery_job_id = ""
    current_status.job_stage_status.progress_message = "Pivoting downloaded data"
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    if inputs.wafer_level:
        wafer_pivot_file = uc3_sigma_final_results_folder / "pivoted_wafer_data.parquet"
        wafer_pivot_file.parent.mkdir(exist_ok=True, parents=True)
        uc3_wafer_data_pivot_on_full_step(
            wafer_data_file_path, wafer_pivot_file, wafer_drop_na_threshold
        )

    if inputs.point_level:
        wafer_pivot_file = uc3_sigma_final_results_folder / "pivoted_point_data.parquet"
        wafer_pivot_file.parent.mkdir(exist_ok=True, parents=True)
        uc3_point_data_pivot_on_full_step(
            point_data_file_path, wafer_pivot_file, points_drop_na_threshold
        )

    current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
    current_status.job_stage_status.progress_percentage = 99
    current_status.job_stage_status.bigquery_job_id = ""
    current_status.job_stage_status.progress_message = "Saving results.."
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    result = UC3SigmaOutput(
        uc3_sigma_data=DataPullResult.model_validate(
            dict(file_path=uc3_sigma_final_results_folder)
        )
    ).model_dump(by_alias=True, mode="json")

    print("### Task Done.(calculating preview..)")
    generate_preview_and_stats_for_all_result_files(str(uc3_sigma_final_results_folder))
    print("### Task Done")

    # updating the stage job and data pull job
    stage_config_job_handler.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )
    stage_config_job_handler.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_job_handler.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )
