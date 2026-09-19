import math
import os
import traceback
from datetime import datetime, timezone

import pandas as pd
from google.cloud import bigquery
from google.oauth2 import service_account
from google.oauth2.credentials import Credentials

from app.services.data.bigquery.dynamic_query_params_processing import (
    process_query_parameters,
)


def convert_size(size_bytes):
    if size_bytes == 0:
        return "0B"
    size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_name[i]}"


def download_bigquery_data_using_service_account(
    sink_path,
    project_id=None,
    credentials_path=None,
    service_account_info=None,
    query: str | None = None,
    query_params=None,
):
    """
    Download data from Google BigQuery based on a specific table or a custom SQL query.

    :param project_id: Your Google Cloud project ID.
    :param credentials_path: Path to your Google Cloud service account key file (JSON).
    :param table: The BigQuery table name in the format `dataset.table`.
    :param query: A SQL query string.
    :return: Result file path.
    """
    try:
        if service_account_info:
            credentials = service_account.Credentials.from_service_account_info(
                service_account_info
            )
            client = bigquery.Client(
                credentials=credentials, project=credentials.project_id
            )
        else:
            client = bigquery.Client.from_service_account_json(
                credentials_path, project=project_id
            )

        # Validate input
        if not query:
            raise ValueError("Either a table name or a query must be provided.")

        query_list = process_query_parameters(query, query_params)

        # # Set job configuration
        # job_config = bigquery.QueryJobConfig(
        #     dry_run=False
        # )

        # Execute the query
        query_job = client.query(query)
        results = query_job.result()  # Waits for the query to finish

        # Convert to DataFrame
        df = results.to_dataframe()
        df.to_csv(sink_path, index=False)
        return sink_path

    except Exception as e:
        print(traceback.format_exc())


def download_bigquery_data_using_user_account(
    sink_path, project_id=None, credentials=None, table=None, query=None
):
    """
    Download data from Google BigQuery based on a specific table or a custom SQL query.

    :param project_id: Your Google Cloud project ID.
    :param credentials_path: Path to your Google Cloud service account key file (JSON).
    :param table: The BigQuery table name in the format `dataset.table`.
    :param query: A SQL query string.
    :return: Result file path.
    """
    try:
        if not credentials:
            raise Exception("Did not get proper creds")

        credentials_obj = Credentials.from_authorized_user_info(
            {
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"],
                "refresh_token": credentials["refresh_token"],
                "token_uri": "https://oauth2.googleapis.com/token",
            }
        )

        client = bigquery.Client(credentials=credentials_obj, project=project_id)

        # Validate input
        if not table and not query:
            raise ValueError("Either a table name or a query must be provided.")
        if table and query:
            raise ValueError("Please provide either a table name or a query, not both.")

        # Prepare the query
        if table:
            query = f"SELECT * FROM `{table}`"

        # Execute the query
        query_job = client.query(query)
        results = query_job.result()  # Waits for the query to finish

        # Convert to DataFrame
        df = results.to_dataframe()
        df.to_csv(sink_path, index=False)
        return sink_path

    except Exception as e:
        print(traceback.format_exc())
