import os
import time
import uuid
from pathlib import Path
from typing import List, Optional, Tuple, Union

from google.cloud import bigquery, storage
from google.cloud.bigquery.job import QueryJob

from app.services.micron.data_catalog.fd_trace.schemas import (
    MultiSqlQuery,
    QueryParameterType,
)

# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "/home/tdam_model_response/.config/gcloud/application_default_credentials.json"


class BigQueryJobsManager:
    def __init__(
        self,
        application_credentials_file=None,
        service_account_file=None,
        gcs_bucket_name="",
        gcp_project_id="",
        nfs_mount_path="",
    ):
        self.gcp_project_id = gcp_project_id
        self.gcs_bucket_name = gcs_bucket_name
        self.nfs_mount_path = nfs_mount_path

        if application_credentials_file:
            # self.credentials = Credentials.from_authorized_user_file(application_credentials_file
            self.bq_client = bigquery.Client(project=self.gcp_project_id)
            self.storage_client = storage.Client(project=self.gcp_project_id)

        elif service_account_file:
            raise ValueError("Not supporting service account credentials file.")
        else:
            raise ValueError("Missing service account or application credentials file.")

    def __del__(self):
        """Destructor to clean up resources."""
        print("Cleaning up BigQueryJobsManager resources...")
        if self.bq_client:
            try:
                self.bq_client.close()  # Close the BigQuery client
                print("BigQuery client disconnected.")
            except Exception as e:
                print(f"Error while closing BigQuery client: {e}")

        if self.storage_client:
            try:
                self.storage_client.close()  # Close the Storage client
                print("Storage client disconnected.")
            except Exception as e:
                print(f"Error while closing Storage client: {e}")

    def submit_query_and_export_to_gcs(
        self, query: MultiSqlQuery
    ) -> Tuple[QueryJob, str]:
        # Generate a unique folder name using UUID
        unique_id = uuid.uuid4().hex
        gcs_uri = f"gs://{self.gcs_bucket_name}/{unique_id}/results-*.parquet"

        # Assemble the export query
        export_query = f"{query.declarations} EXPORT DATA OPTIONS(uri='{gcs_uri}', format='Parquet') AS {query.sql_query}"
        job_config = None
        if query.query_params:
            job_config = bigquery.QueryJobConfig()
            job_config.dry_run = False
            query_parameters = []
            for name, (parameter_type, value_type, value) in query.query_params.items():
                match parameter_type:
                    case QueryParameterType.SCALAR:
                        parameter = bigquery.ScalarQueryParameter(
                            name, value_type.value, value
                        )
                    case QueryParameterType.ARRAY:
                        parameter = bigquery.ArrayQueryParameter(
                            name, value_type.value, value
                        )
                    case _:
                        continue
                query_parameters.append(parameter)
            job_config.query_parameters = query_parameters
        query_job = self.bq_client.query(export_query, job_config=job_config)
        print(f"Query job {query_job.job_id} started...")

        # Return the query job and the GCS folder name for monitoring and further processing
        return query_job, unique_id

    def monitor_job(
        self, query_jobs: Union[QueryJob, List[QueryJob]], check_interval: int = 1
    ) -> bool:
        """
        Monitors one or multiple BigQuery jobs until completion or failure.

         Args:
             query_job (Union[QueryJob, List[QueryJob]]): A BigQuery job object or a list of job objects.
             check_interval (int): How often to check the job status, in seconds.

         Returns:
             Dict[str, bool]: A dictionary where the keys are job IDs and the values are booleans
                             indicating whether each job completed successfully (True) or failed (False).
        """
        if isinstance(query_jobs, QueryJob):
            query_jobs = [query_jobs]  # Convert single QueryJob to a list

        job_status = {job.job_id: None for job in query_jobs}

        print("Monitoring jobs...")
        try:
            while any(status is None for status in job_status.values()):
                for query_job in query_jobs:
                    if job_status[query_job.job_id] is None:
                        query_job.reload()
                        if query_job.done():
                            if query_job.error_result:
                                print(
                                    f"Job {query_job.job_id} failed with error: {query_job.error_result}"
                                )
                                job_status[query_job.job_id] = False
                                raise Exception(
                                    "Bigquery job got failed. Job id is {query_job.job_id}"
                                )
                            else:
                                print(f"Job {query_job.job_id} completed successfully.")
                                job_status[query_job.job_id] = True
                        else:
                            print(
                                f"Job {query_job.job_id} is currently in state {query_job.state}. Waiting for completion..."
                            )

                time.sleep(check_interval)

            return job_status

        except Exception as e:
            print(f"An error occurred while monitoring the jobs: {e}")
            return {job.job_id: False for job in query_jobs}

    def download_from_gcs(
        self,
        gcs_folder_name: str,
        job_creation_time: str = "",
        job_name="",
        destination_dirname: str = "",
        use_blob_folder=True,
        add_base_destination=True,
    ) -> Optional[Path]:
        """
        Downloads all files from a specified GCS folder to a local directory.

        Args:
            gcs_folder_name (str): The name of the folder in GCS to download files from.
            destination_dirname (str): The local directory name where files should be downloaded.
            add_base_destination (bool): if true base destination is added else not
        """
        try:
            base_destination = self.nfs_mount_path + f"/{job_name}_{job_creation_time}"
            if add_base_destination:
                if destination_dirname == "":
                    destination_path = base_destination + "/bin"
                else:
                    destination_path = base_destination + destination_dirname
                    use_blob_folder = False
            else:
                destination_path = destination_dirname
                use_blob_folder = False

            blobs = self.storage_client.list_blobs(
                self.gcs_bucket_name, prefix=f"{gcs_folder_name}/"
            )

            print("**************************")
            print(f"destination_path: {destination_path}")
            print("**************************")
            os.makedirs(
                destination_path, exist_ok=True
            )  # Ensure the destination directory exists.

            if use_blob_folder:
                destination_path = os.path.join(destination_path, gcs_folder_name)

            os.makedirs(
                destination_path, exist_ok=True
            )  # Ensure the destination directory exists.

            # Download each blob in the folder
            for blob in blobs:
                if not blob.name.endswith(
                    "/"
                ):  # Avoid creating empty directories for 'folder' blobs
                    blob_filename = os.path.basename(
                        blob.name
                    )  # Get the base name of the file
                    blob_path = os.path.join(destination_path, blob_filename)
                    try:
                        blob.download_to_filename(blob_path)
                        print(f"Downloaded {blob.name} to {blob_path}")
                    except Exception as e:
                        print(f"Unable to download file {blob_path}: {e}")
                        print(f"continuing with next file if its in queue")
                    finally:
                        if os.stat(blob_path).st_size == 0:
                            print(f"this {blob_path} size is zero, therefore removed.")
                            os.remove(blob_path)
                            # print(f"Blob {blob.name} deleted.")
            # deleting the gcs fodler that we created to store the bigquery job result
            try:
                blob = self.storage_client.bucket(self.gcs_bucket_name).blob(
                    gcs_folder_name
                )
                blob.delete()
                print(f"GCS folder blob {gcs_folder_name} deleted.")
            except Exception as e:
                print(f"Unable delete the bucket folder due to {str(e)}")

            if use_blob_folder:
                return Path(destination_path)
            else:
                return Path(base_destination)

        except Exception as e:
            print(f"Failed to download files: {e}")
            return None
