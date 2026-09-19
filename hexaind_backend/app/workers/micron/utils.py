from pathlib import Path
from typing import Dict, List, Optional, Tuple

import polars as pl
from google.cloud.bigquery import QueryJob

from app.services.data.assets.datasets.schemas import (
    TabularDatasetInformationAndMetadata,
)
from app.services.data.assets.datasets.service import DatasetsService
from app.services.micron.data_catalog.fd_trace.schemas import (
    BigQueryAppDefaultCredFile,
    BigqueryDataPullJobConfig,
    BigQueryServiceAccountFile,
    MultiSqlQuery,
)

from .commons import StageConfigJobHandler
from .gcp_hooks import BigQueryJobsManager


def create_bigquery_manager(
    bigquery_job_config: BigqueryDataPullJobConfig, nfs_mount_path: str
) -> BigQueryJobsManager:
    if bigquery_job_config.authentication is None:
        raise ValueError(
            "Unable to run bigquery operations. Please provide bigquery job configuration."
        )
    match bigquery_job_config.authentication.auth_config:
        case BigQueryAppDefaultCredFile(
            application_credentials_file_path=application_credentials_file,
            project_id=gcp_project_id,
        ):
            bigquery_manager = BigQueryJobsManager(
                application_credentials_file=application_credentials_file,
                gcs_bucket_name=bigquery_job_config.gcs_bucket_name,
                gcp_project_id=gcp_project_id,
                nfs_mount_path=nfs_mount_path,
            )
        case BigQueryServiceAccountFile(
            service_account_file=application_credentials_file,
        ):
            bigquery_manager = BigQueryJobsManager(
                application_credentials_file=application_credentials_file,
                gcs_bucket_name=bigquery_job_config.gcs_bucket_name,
                nfs_mount_path=nfs_mount_path,
            )
    return bigquery_manager


def fetch_top_level_cache_value(
    stage_config_obj: StageConfigJobHandler, cache_key: str, ttl_days: int = 30
) -> Optional[Path]:
    if not cache_key:
        return None
    cache_record: Optional[Dict[str, str]] = (
        stage_config_obj.fd_trace_job_dao.fetch_top_level_cache_with_ttl_sync(
            cache_key=cache_key, ttl_days=ttl_days
        )
    )
    if (
        cache_record is None
        or (cache_path := cache_record.get("value")) is None
        or not (final_result_file := Path(cache_path)).exists()
    ):
        return None
    return final_result_file


def fetch_top_level_cache_value_per_query(
    stage_config_obj: StageConfigJobHandler, multisql_queries: List[MultiSqlQuery]
) -> List[Optional[Path]]:
    cached_final_result_files: List[Optional[Path]] = [None] * len(multisql_queries)
    for index, multisql_query in enumerate(multisql_queries):
        if not multisql_query.cache_keys:
            continue
        # if one cache key is available then there is a cache available
        for cache_key in multisql_query.cache_keys:
            final_result_file = fetch_top_level_cache_value(
                stage_config_obj, cache_key=cache_key
            )
            if not final_result_file:
                continue
            cached_final_result_files[index] = final_result_file
            print(f"Found cache for key {cache_key} and SQL[{index}]")
            break

    return cached_final_result_files


def bigquery_manager_query_registration(
    bigquery_manager: BigQueryJobsManager, sql_query: str, declarations_query: str = ""
) -> Tuple[List[Optional[str]], List[QueryJob], List[str], List[int]]:
    query = MultiSqlQuery(
        sql_query=sql_query,
        declarations=declarations_query,
        cache_keys=None,
    )
    job, folder_blob = bigquery_manager.submit_query_and_export_to_gcs(query=query)
    return [job.job_id], [job], [folder_blob], [0]


def bigquery_manager_query_monitoring(
    bigquery_manager: BigQueryJobsManager,
    bq_job_objects: List[QueryJob],
    stage_job_id: str,
):
    query_execution_status = bigquery_manager.monitor_job(query_jobs=bq_job_objects)
    if not query_execution_status:
        raise Exception(
            f"Bigquery jobs for the stage got failed. Stage job id: {stage_job_id}"
        )


def bigquery_manager_results_download(
    bigquery_manager: BigQueryJobsManager,
    result_folder_blobs: List[str],
    job_creation_time,
    job_name,
    destination_folder_path,
):
    for blob_result in result_folder_blobs:
        print(f"blob_result: {blob_result}")
        bigquery_manager.download_from_gcs(
            gcs_folder_name=blob_result,
            job_creation_time=job_creation_time,
            job_name=job_name,
            destination_dirname=destination_folder_path,
            add_base_destination=False,
        )


def add_suffix_to_filename(file_path: str, suffix: str = "_test") -> str:
    file_path_ = Path(file_path)
    return str(file_path_.with_stem(file_path_.stem + suffix))


def copy_parquet_files(
    source, destination, single_file: bool = True
):  # used to convert folder parquet to single file / vice-versa
    df = pl.scan_parquet(source)
    if single_file:
        if not (str(destination).endswith(".parquet")):
            raise ValueError(
                "Expected .parquet for writing to single file found {destination}"
            )
    df.sink_parquet(destination)


def generate_preview_and_stats_for_all_result_files(file_path: str):
    try:
        files_to_calculate = []
        data_files_path = Path(file_path)
        if not data_files_path.exists():
            raise KeyError("file not found")
        if data_files_path.is_file() and data_files_path.suffix in {".csv", ".parquet"}:
            files_to_calculate = [file_path]
        if data_files_path.is_dir():
            files_to_calculate = [
                str(path)
                for path in data_files_path.rglob("*")
                if path.suffix in {".csv", ".parquet"}
            ]

        for fpath_ in files_to_calculate:
            td_info, metadata, se_results = (
                DatasetsService.generate_tabular_dataset_info_and_update_metadata(
                    input_data_path=str(fpath_)
                )
            )
            json_data = TabularDatasetInformationAndMetadata(
                tabular_dataset_info=td_info, metadata=metadata
            )
            td_path = Path(fpath_)
            json_path = td_path.parent / f"{td_path.name.split('.')[0]}.json"
            with json_path.open("w") as file:
                file.write(json_data.model_dump_json())
    except Exception as e:
        print(f"Failed to generate preview and stats for files in {file_path} : {e}")
