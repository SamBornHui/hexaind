import os
from pathlib import Path
from typing import Optional

from app.config.env_vars import environment
from app.services.micron.data_catalog.fd_trace.dummy_files import DUMMY_FILES
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigqueryDataPullJobConfig,
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
    LotIdsDataPullOutput,
    MultiSqlQuery,
    ProbeContextDataPullOutput,
    SensorsDataPullOutput,
    TechNodesDataPullOutput,
    TravelersIdDataPullOutput,
    TravelerStepDataPullConfig,
    TravelerStepDataPullOutput,
)
from app.services.micron.data_catalog.fd_trace.service import FdTraceDataPullService
from app.utils.file_utils import FileUtils
from app.workers.micron.commons import StageConfigJobHandler
from app.workers.micron.fd_helpers import (
    clean_fd_context,
    clean_probe_context,
    preprocess_traveler_steps,
)
from app.workers.micron.utils import (
    create_bigquery_manager,
    fetch_top_level_cache_value_per_query,
)


def bigquery_job_method(
    stage_config_obj: StageConfigJobHandler,
    stage_job_id: str,
    data_pull_job_id: str,
    user_name: str,
    pull_directly_to_hexaind_platform: bool = False,
    override_destination: Optional[str] = None,
):
    print_msg = f"Job: {data_pull_job_id}-{stage_job_id}-{user_name}"

    print("****************************")
    print(f"{print_msg}: New Task Init.")
    print("****************************")

    datacatalog_session_record = stage_config_obj.datacatalog_session_record

    job_creation_time = datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )

    stage_job_config_record = stage_config_obj.stage_job_record

    bigquery_job_config = BigqueryDataPullJobConfig(
        **stage_job_config_record.stage_config.status.job_config
    )
    multisql_queries = []
    if isinstance(bigquery_job_config.sql_query, str):
        print("********************************")
        print(f"{print_msg}: Got a single Query")
        print("********************************")

        sql_query = MultiSqlQuery(
            sql_query=bigquery_job_config.sql_query,
            destination_folder_path=None,
            cache_keys=[],
        )

        multisql_queries.append(sql_query)

    elif isinstance(bigquery_job_config.sql_query, list):
        print("***********************************")
        print(f"{print_msg}: Got a list of Queries")
        print("***********************************")

        multisql_queries = bigquery_job_config.sql_query

    else:
        raise Exception(
            f"Unable to run bigquery job. Expecting list or str, but got {type(bigquery_job_config.sql_query)} for worker."
        )

    # started processing the task
    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_VERIFICATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=0,
            progress_message="Connecting to BigQuery...",
        ),
    )

    print(f"{print_msg}: ### checking if cache keys are available in DB")
    result_files = fetch_top_level_cache_value_per_query(
        stage_config_obj, multisql_queries=multisql_queries
    )

    results_found_in_cache = [
        final_result_file is not None for final_result_file in result_files
    ]

    # check if all the values found in cache DB
    found_all_values_in_cache = any(item is not None for item in result_files)

    if not found_all_values_in_cache:
        print(
            f"{print_msg}: ### haven't found all the cache keys need to pull remaining from BigQuery"
        )

        bigquery_manager = create_bigquery_manager(
            bigquery_job_config=bigquery_job_config,
            nfs_mount_path=str(environment.hexaind_data).format(user_name=user_name),
        )

        print(f"{print_msg}: ### Stage 1: Dry Run the query and get back result size")
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        print("**************************")
        print(f"{print_msg}: Stage 1 Done")
        print("**************************")

        print(f"{print_msg}: ### Stage 2: Register the real job at bigquery")
        bq_job_ids, bq_job_objects, result_fodler_blobs, bq_job_indexes = [], [], [], []
        for index, sub_query_obj in enumerate(multisql_queries):
            if result_files[index] is None:
                # submit jobs which are not found in cache
                bq_job, result_folder_blob_name = (
                    bigquery_manager.submit_query_and_export_to_gcs(query=sub_query_obj)
                )
                bq_job_ids.append(bq_job.job_id)
                bq_job_objects.append(bq_job)
                result_fodler_blobs.append(result_folder_blob_name)
                bq_job_indexes.append(index)

        current_status.job_stage = BigQueryDataPullJobStage.QUERY_REGISTRATION
        # TODO store the bucket folder path also in db
        current_status.job_stage_status.bigquery_job_id = bq_job_ids
        current_status.job_stage_status.progress_percentage = 20
        current_status.job_stage_status.progress_message = (
            "Successfully connected. Sending request to BigQuery..."
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        print(f"{print_msg}: ### Stage 3: Actual query job monitoring")
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
        current_status.job_stage_status.progress_percentage = 40
        current_status.job_stage_status.progress_message = (
            "Fetching the catalog items...(1/2)"
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )
        query_execution_status = bigquery_manager.monitor_job(query_jobs=bq_job_objects)
        if not query_execution_status:
            raise Exception(
                f"Bigquery jobs for the stage got failed. Stage job id: {stage_job_id}"
            )

        print(f"{print_msg}: ### Stage 4: query results downloading from gcs bucket")
        current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
        current_status.job_stage_status.progress_percentage = 60
        current_status.job_stage_status.progress_message = (
            "Fetching the catalog items...(2/2)"
        )
        stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
            job_id=stage_job_id, new_status=current_status
        )

        # Stage 4: query results downloading from gcs bucket
        try:
            for index, blob_result in enumerate(result_fodler_blobs):
                destination_folder_path = ""
                if multisql_queries[index].destination_folder_path:
                    destination_folder_path = str(
                        multisql_queries[index].destination_folder_path
                    )

                final_result_file = bigquery_manager.download_from_gcs(
                    gcs_folder_name=blob_result,
                    job_creation_time=job_creation_time,
                    job_name=datacatalog_session_record.name.lower().replace(" ", "_"),
                    destination_dirname=destination_folder_path,
                )

                # update result file in result_files
                result_files[bq_job_indexes[index]] = final_result_file
                # TODO: save the result into cache
                print(
                    "The result will be in: ",
                    os.path.join(
                        str(environment.hexaind_data).format(user_name=user_name),
                        data_pull_job_id,
                        destination_folder_path,
                    ),
                )

        except Exception as e:
            print(f"{print_msg}: Error while downloading BigQuery job result: {e}")

    else:
        print(f"{print_msg}: ### Found all the values in cache.")

    final_result_files = list(file for file in result_files if file is not None)

    print(f"{print_msg}: ### preparing the result for a given stage")

    # Got all the result files from BigQuery.
    match stage_config_obj.stage_job_record.stage:
        case FDDataPullStages.FACILITIES:
            result = FacilitiesDataPullOutput(
                facilities=DataPullResult.model_validate(
                    dict(file_path=DUMMY_FILES["facilities"])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TECH_NODE:
            result = TechNodesDataPullOutput(
                tech_nodes=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.DESIGN_ID:
            result = DesignIdDataPullOutput(
                design_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TRAVELER_ID:
            result = TravelersIdDataPullOutput(
                traveler_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.TRAVELER_STEP:
            # finding baseline_line_traveler_id
            if not isinstance(
                stage_job_config_record.stage_config, TravelerStepDataPullConfig
            ):
                raise Exception()
            inputs = stage_job_config_record.stage_config.inputs
            if inputs is None:
                raise Exception()
            baseline_line_traveler_id = FdTraceDataPullService.get_baseline_traveler_id(
                inputs
            )
            final_result_file = (
                Path(final_result_files[0]).parent / "traveler_steps.parquet"
            )
            preprocess_traveler_steps(final_result_files, final_result_file)
            result = TravelerStepDataPullOutput(
                traveler_steps=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                ),
                baseline_line_traveler_id=baseline_line_traveler_id,
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_SENSOR:
            result = SensorsDataPullOutput(
                sensors=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_CONTEXT:
            # post-process fd_context
            # note: pull_directly_to_hexaind_platform var is used here not to do post processing on data
            final_result_file = (
                final_result_files[0]
                if pull_directly_to_hexaind_platform
                else clean_fd_context(result_path=final_result_files[0])
            )
            if override_destination is not None:
                print(f"override destination => {override_destination}")
                FileUtils.create_deep_copy_file_or_folder(
                    str(final_result_file), override_destination, dirs_exist_ok=True
                )

            result = FdContextDataPullOutput(
                fd_contexts=DataPullResult.model_validate(
                    dict(file_path=final_result_file)
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.FD_TRACE:
            result = FdTraceDataPullOutput(
                fd_trace=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.LOT_ID:
            result = LotIdsDataPullOutput(
                lot_ids=DataPullResult.model_validate(
                    dict(file_path=final_result_files[0])
                )
            ).model_dump(by_alias=True, mode="json")
        case FDDataPullStages.PROBE_CONTEXT:
            # combine and save the results into original file and
            result_path = clean_probe_context(result_path=str(final_result_files[0]))
            result = ProbeContextDataPullOutput(
                paretoname=DataPullResult.model_validate(dict(file_path=result_path)),
                paretotitle=DataPullResult.model_validate(dict(file_path=result_path)),
            ).model_dump(by_alias=True, mode="json")
        case _:
            result = {
                "error": f"Invalid stage type in worker: {stage_config_obj.stage_job_record.stage}"
            }

    print(f"{print_msg}: ### updating all the DB records")
    current_status.job_stage = BigQueryDataPullJobStage.SAVING_RESULTS
    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = "Fetched the catalog items."
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    # updating the stage job and data pull job
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_current_status_and_result_sync(
        job_id=stage_job_id, new_status=DataPullStatus.SUCCESS, result=result
    )

    stage_config_obj.fd_trace_service.update_fd_data_pull_job_record_current_stage_sync(
        job_id=data_pull_job_id,
        current_stage=stage_config_obj.stage_job_record.stage,
        current_stage_status=DataCatalogStatus.IDLE,
    )

    print(f"{print_msg}: ### Task Done.")
