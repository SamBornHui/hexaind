import os
import re
from datetime import datetime, timedelta
from glob import glob
from pathlib import Path

import pandas as pd

from app.services.micron.data_catalog.fd_trace.schemas import (
    BigQueryDataPullJobStage,
    BigQueryDataPullJobStatus,
    BigQueryJobStatus,
    FdDataPullJobConfig,
    UC2SigmaDataPullInput,
)
from app.workers.micron.gcp_hooks import BigQueryJobsManager
from app.workers.micron.uc2_sigma_helpers import uc2_sigma_data_pull
from app.workers.micron.utils import (
    bigquery_manager_query_monitoring,
    bigquery_manager_query_registration,
    bigquery_manager_results_download,
)


def check_subset_to_gql(
    file_path,
    run_parameters,
    wafer_parameters,
    measurement_steps,
    measurement_parameters,
    point_steps,
    point_parameters,
):
    # this method confirms that the selected values we got are infact from gql and not added by user ..etc
    df = pd.read_parquet(file_path)

    if not set(run_parameters).issubset(df["run_parameters"].unique()):
        return False
    if not set(wafer_parameters).issubset(df["wafer_parameters"].unique()):
        return False
    if not set(measurement_steps).issubset(df["measurement_steps"].unique()):
        return False
    if not set(measurement_parameters).issubset(df["measurement_parameters"].unique()):
        return False
    if not set(point_steps).issubset(df["point_steps"].unique()):
        return False
    if not set(point_parameters).issubset(df["point_parameters"].unique()):
        return False

    return True


def handle_one_query_at_a_time(
    bigquery_manager: BigQueryJobsManager,
    stage_config_obj,
    stage_job_id,
    query,
    path,
    progress_message_prefix="",
    job_name="",
):
    job_creation_time = stage_config_obj.datacatalog_session_record.created_at.strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    job_name = (
        stage_config_obj.datacatalog_session_record.name.lower().replace(" ", "_")
        + f"_{job_name}"
    )

    current_status = BigQueryDataPullJobStatus(
        job_stage=BigQueryDataPullJobStage.QUERY_REGISTRATION,
        job_stage_status=BigQueryJobStatus(
            total_bytes_processed="122434242",
            total_bytes_billed="$100",
            progress_percentage=25,
            progress_message=f"[{progress_message_prefix}] started query registration.",
        ),
    )

    bq_job_ids, bq_job_objects, result_folder_blobs, bq_job_indexes = (
        bigquery_manager_query_registration(bigquery_manager, query)
    )
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_EXECUTION
    current_status.job_stage_status.progress_percentage = 50
    current_status.job_stage_status.progress_message = (
        f"[{progress_message_prefix}] started query execution."
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_query_monitoring(bigquery_manager, bq_job_objects, stage_job_id)
    current_status.job_stage = BigQueryDataPullJobStage.QUERY_RESULT_DOWNLOAD
    current_status.job_stage_status.progress_percentage = 75
    current_status.job_stage_status.progress_message = (
        f"[{progress_message_prefix}] started query results downloading."
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )

    bigquery_manager_results_download(
        bigquery_manager,
        result_folder_blobs,
        job_creation_time,
        job_name,
        path,
    )

    current_status.job_stage_status.progress_percentage = 100
    current_status.job_stage_status.progress_message = (
        f"[{progress_message_prefix}] completed query results downloaded."
    )
    stage_config_obj.fd_trace_job_dao.update_fd_data_stage_job_record_bigquery_status_sync(
        job_id=stage_job_id, new_status=current_status
    )


class UC2SigmaHelper:
    def __init__(self, bigquery_manager, stage_config_obj, stage_job_id, output_path):
        self.bigquery_manager: BigQueryJobsManager = bigquery_manager
        self.stage_config_obj = stage_config_obj
        self.stage_job_id = stage_job_id
        self.output_path = output_path

    def get_sigma_wafer(
        self,
        facility,
        design_id,
        start_date,
        end_date,
        step,
        attr_items,
        test_items,
        debug=False,
        progress_message_prefix="",
        job_name="",
    ):
        """
        Generates and executes a SQL query to retrieve wafer attribute data for a specific facility,
        design, date range, and step, then processes the data into a pivoted format.

        Parameters:
            facility (str): The facility code (e.g., '10').
            design_id (str): ID of the design to filter data.
            start_date (str): The start date for data filtering (YYYY-MM-DD).
            end_date (str): The end date for data filtering (YYYY-MM-DD).
            step (str): Manufacturing process step.
            attr_items (pd.DataFrame): DataFrame containing additional attribute items to include.
            test_items (pd.DataFrame): DataFrame with test items; filters results to specific tests.
            debug (bool): If True, returns additional DataFrame for debugging.

        Returns:
            pd.DataFrame: Pivoted DataFrame with wafer test data per wafer ID and test type.
            pd.DataFrame (optional): Detailed DataFrame with original query results if debug=True.
        """
        # Define a subcategory label to use in the data pivoting
        subdata = "WaferData"

        # Extract unique test parameter IDs from the test_items DataFrame
        test_ids = list(test_items["PARAMETER"].drop_duplicates())

        # If there's only one test ID, format it for SQL as a tuple with a single string; else as a tuple of IDs
        if len(test_ids) == 1:
            test_ids = f"('{test_ids[0]}')"
        else:
            test_ids = tuple(test_ids)

        # Construct SQL query with the provided facility, date range, design ID, and step
        sql = f"""
        WITH LOTS AS (
            SELECT DISTINCT LOT_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_lot`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
        )
        SELECT DISTINCT
            sw.DWH_SRCID, sw.DESIGN_ID, sw.LOT_ID, sw.WAFER_ID, sw.WAFER_SCRIBE,
            sw.MFG_PROCESS_STEP, sw.RUN_COMPLETE_DATE, sw.RUN_COMPLETE_DATETIME,
            sw.WAFER_TYPE, sw.WAFER_SPEC_ID, sws.TEST_VALUE, sws.COMMON_TEST_ID
        FROM (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, LOT_ID, WAFER_ID,
                WAFER_SCRIBE, MFG_PROCESS_STEP, WAFER_RUN_OID, RUN_OID,
                RUN_COMPLETE_DATE, RUN_COMPLETE_DATETIME, WAFER_TYPE, WAFER_SPEC_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sw
        INNER JOIN (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, RUN_OID, WAFER_SPEC_ID,
                LOT_ID, WAFER_ID, WAFER_SCRIBE, RUN_COMPLETE_DATE,
                RUN_COMPLETE_DATETIME, TEST_VALUE, COMMON_TEST_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer_summary`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND COMMON_TEST_ID IN {test_ids}
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sws
        ON (
            sw.DWH_SRCID = sws.DWH_SRCID AND
            sw.MFG_FACILITY_ID = sws.MFG_FACILITY_ID AND
            sw.RUN_OID = sws.RUN_OID AND
            sw.WAFER_SPEC_ID = sws.WAFER_SPEC_ID AND
            sw.LOT_ID = sws.LOT_ID AND
            sw.WAFER_ID = sws.WAFER_ID AND
            sw.WAFER_SCRIBE = sws.WAFER_SCRIBE AND
            sw.RUN_COMPLETE_DATE = sws.RUN_COMPLETE_DATE AND
            sw.RUN_COMPLETE_DATETIME = sws.RUN_COMPLETE_DATETIME
        )
        """

        # Execute the query and load the result as a DataFrame
        # record = conn.query(sql)
        # result = record.result()
        downloaded_path = str(self.output_path) + f"_temp/{job_name}"
        Path(downloaded_path).mkdir(parents=True, exist_ok=True)
        handle_one_query_at_a_time(
            self.bigquery_manager,
            self.stage_config_obj,
            self.stage_job_id,
            sql,
            downloaded_path,
            progress_message_prefix=progress_message_prefix,
            job_name=job_name,
        )
        df = pd.read_parquet(downloaded_path)

        # Create a unique name for each test type based on the step, subdata, wafer type, spec ID, and test ID
        df["PIVOT_COLUMN_NAME"] = (
            f"{step}::{subdata}::"
            + df["WAFER_TYPE"]
            + "::"
            + df["WAFER_SPEC_ID"]
            + "::"
            + df["COMMON_TEST_ID"]
        )

        # Define essential columns to keep in the output
        essential_columns = [
            "DWH_SRCID",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "WAFER_SCRIBE",
            "RUN_COMPLETE_DATE",
            "RUN_COMPLETE_DATETIME",
            "TEST_VALUE",
            "PIVOT_COLUMN_NAME",
        ]

        # Remove duplicates and sort the DataFrame by RUN_COMPLETE_DATETIME for organization
        df = (
            df[essential_columns]
            .drop_duplicates()
            .sort_values(by="RUN_COMPLETE_DATETIME", ascending=True)
            .reset_index(drop=True)
        )

        # Check if attribute items are provided; if so, prepare to add relevant columns
        if len(attr_items) > 0:
            collected_attr_parameters = list(attr_items["PARAMETER"].drop_duplicates())
            if "Run Complete Datetime" in collected_attr_parameters:
                # Rename date columns for additional detail in output
                df = df.rename(
                    columns={
                        "RUN_COMPLETE_DATE": f"{step}::{subdata}::RunCompleteDate",
                        "RUN_COMPLETE_DATETIME": f"{step}::{subdata}::RunCompleteDateTime",
                    }
                )
                essential_columns += [
                    f"{step}::{subdata}::RunCompleteDate",
                    f"{step}::{subdata}::RunCompleteDateTime",
                ]

        # Remove old date columns after renaming
        essential_columns.remove("RUN_COMPLETE_DATE")
        essential_columns.remove("RUN_COMPLETE_DATETIME")

        # Select only the final essential columns
        df = df[essential_columns]

        # Define index columns (without 'PIVOT_COLUMN_NAME' and 'TEST_VALUE') for the pivot
        index_columns = [
            column
            for column in essential_columns
            if column not in ["PIVOT_COLUMN_NAME", "TEST_VALUE"]
        ]
        # Pivot the data so each test type becomes its own column, with 'TEST_VALUE' as the values
        out = df.pivot_table(
            index=index_columns,
            columns="PIVOT_COLUMN_NAME",
            values="TEST_VALUE",
            aggfunc="last",
        ).reset_index()

        pivoted_output_path = Path(str(self.output_path) + f"/{job_name}")
        pivoted_output_path.mkdir(parents=True, exist_ok=True)
        out.to_parquet(pivoted_output_path / "results.parquet")

        # If debug mode is enabled, return both the pivoted and original DataFrames
        if debug:
            return out, df
        else:
            return out, None

    def get_sigma_measurement(
        self,
        facility,
        design_id,
        start_date,
        end_date,
        step,
        attr_items,
        test_items,
        debug=False,
        progress_message_prefix="",
        job_name="",
    ):
        """
        Fetches and processes wafer measurement data for a specified facility, design, and manufacturing step.
        Constructs a SQL query to retrieve relevant data, processes it, and pivots it for easy analysis.
        Parameters:
            facility (str): The facility identifier (e.g., '10').
            design_id (str): The design identifier to filter data.
            start_date (str): Start date for data filtering in 'YYYY-MM-DD' format.
            end_date (str): End date for data filtering in 'YYYY-MM-DD' format.
            step (str): The manufacturing step to filter data.
            attr_items (pd.DataFrame): DataFrame of attribute items to include.
            test_items (pd.DataFrame): DataFrame of test items to use as filters.
            debug (bool): If True, returns additional unpivoted DataFrame for debugging.
        Returns:
            pd.DataFrame: Pivoted DataFrame with wafer measurement data.
            pd.DataFrame (optional): Unpivoted DataFrame with the original query result if debug=True.
        """
        # Define a label to use for the data category in pivoted columns
        subdata = "MeasurementData"
        # Extract unique test parameter IDs from the test_items DataFrame
        test_ids = list(test_items["PARAMETER"].drop_duplicates())
        # Check if any test ID contains the keyword 'ALL' (special case for selecting all test data)
        contains_all = any("ALL" in item for item in test_ids)
        # If 'ALL' is found, skip test filtering; otherwise, format test_ids as a tuple for SQL use
        if not contains_all:
            if len(test_ids) == 1:
                test_ids = f"('{test_ids[0]}')"
            else:
                test_ids = tuple(test_ids)
        # Construct the main SQL query for retrieving relevant wafer data
        sql = f"""
        WITH LOTS AS (
            SELECT DISTINCT LOT_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_lot`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
        )
        SELECT DISTINCT
            sw.DWH_SRCID, sw.DESIGN_ID, sw.LOT_ID, sw.WAFER_ID, sw.WAFER_SCRIBE,
            sw.MFG_PROCESS_STEP, sw.RUN_COMPLETE_DATE, sw.RUN_COMPLETE_DATETIME,
            sw.WAFER_TYPE, sw.WAFER_SPEC_ID, sws.TEST_VALUE, sws.COMMON_TEST_ID
        FROM (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, LOT_ID, WAFER_ID,
                WAFER_SCRIBE, MFG_PROCESS_STEP, WAFER_RUN_OID, RUN_OID,
                RUN_COMPLETE_DATE, RUN_COMPLETE_DATETIME, WAFER_TYPE, WAFER_SPEC_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sw
        INNER JOIN (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, RUN_OID, WAFER_SPEC_ID,
                LOT_ID, WAFER_ID, WAFER_SCRIBE, RUN_COMPLETE_DATE,
                RUN_COMPLETE_DATETIME, TEST_VALUE, COMMON_TEST_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_measurement_summary`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND COMMON_TEST_ID IN {test_ids}
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sws
        ON (
            sw.DWH_SRCID = sws.DWH_SRCID AND
            sw.MFG_FACILITY_ID = sws.MFG_FACILITY_ID AND
            sw.RUN_OID = sws.RUN_OID AND
            sw.WAFER_SPEC_ID = sws.WAFER_SPEC_ID AND
            sw.LOT_ID = sws.LOT_ID AND
            sw.WAFER_ID = sws.WAFER_ID AND
            sw.WAFER_SCRIBE = sws.WAFER_SCRIBE AND
            sw.RUN_COMPLETE_DATE = sws.RUN_COMPLETE_DATE AND
            sw.RUN_COMPLETE_DATETIME = sws.RUN_COMPLETE_DATETIME
        )
        """
        # If 'ALL' is in test_ids, remove the filtering condition for COMMON_TEST_ID from the query
        if contains_all:
            sql = sql.replace(f"AND COMMON_TEST_ID IN {test_ids}", "")
        # Execute the SQL query and store the result in a DataFrame
        # record = conn.query(sql)
        # result = record.result()
        # df = result.to_dataframe()
        downloaded_path = str(self.output_path) + f"_temp/{job_name}"
        Path(downloaded_path).mkdir(parents=True, exist_ok=True)
        handle_one_query_at_a_time(
            self.bigquery_manager,
            self.stage_config_obj,
            self.stage_job_id,
            sql,
            downloaded_path,
            progress_message_prefix=progress_message_prefix,
            job_name=job_name,
        )
        df = pd.read_parquet(downloaded_path)

        # Create a unique column name for each measurement type based on various attributes
        df["PIVOT_COLUMN_NAME"] = (
            f"{step}::{subdata}::"
            + df["WAFER_TYPE"]
            + "::"
            + df["WAFER_SPEC_ID"]
            + "::"
            + df["COMMON_TEST_ID"]
        )
        # Define the main columns to retain for the final DataFrame
        essential_columns = [
            "DWH_SRCID",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "WAFER_SCRIBE",
            "RUN_COMPLETE_DATE",
            "RUN_COMPLETE_DATETIME",
            "TEST_VALUE",
            "PIVOT_COLUMN_NAME",
        ]
        # Remove duplicates, sort by completion date for clarity, and reset the index
        df = (
            df[essential_columns]
            .drop_duplicates()
            .sort_values(by="RUN_COMPLETE_DATETIME", ascending=True)
            .reset_index(drop=True)
        )
        # If there are attribute items, process them and add relevant columns if needed
        if len(attr_items) > 0:
            collected_attr_parameters = list(attr_items["PARAMETER"].drop_duplicates())
            if "Run Complete Datetime" in collected_attr_parameters:
                # Rename columns to give more descriptive names in the output DataFrame
                df = df.rename(
                    columns={
                        "RUN_COMPLETE_DATE": f"{step}::{subdata}::RunCompleteDate",
                        "RUN_COMPLETE_DATETIME": f"{step}::{subdata}::RunCompleteDateTime",
                    }
                )
                # Append these columns to essential columns for final selection
                essential_columns += [
                    f"{step}::{subdata}::RunCompleteDate",
                    f"{step}::{subdata}::RunCompleteDateTime",
                ]
        # Remove the original date columns now that they've been renamed
        essential_columns.remove("RUN_COMPLETE_DATE")
        essential_columns.remove("RUN_COMPLETE_DATETIME")
        # Select only the essential columns
        df = df[essential_columns]
        # Create a list of index columns, excluding 'PIVOT_COLUMN_NAME' and 'TEST_VALUE'
        index_columns = [
            column
            for column in essential_columns
            if column not in ["PIVOT_COLUMN_NAME", "TEST_VALUE"]
        ]
        # Pivot the data so each unique measurement type (PIVOT_COLUMN_NAME) has its own column
        out = df.pivot_table(
            index=index_columns,
            columns="PIVOT_COLUMN_NAME",
            values="TEST_VALUE",
            aggfunc="last",
        ).reset_index()

        pivoted_output_path = Path(str(self.output_path) + f"/{job_name}")
        pivoted_output_path.mkdir(parents=True, exist_ok=True)
        out.to_parquet(pivoted_output_path / "results.parquet")

        # If debug mode is enabled, return both the pivoted DataFrame and original DataFrame
        if debug:
            return out, df
        else:
            return out, None

    def get_sigma_point(
        self,
        facility,
        design_id,
        start_date,
        end_date,
        step,
        attr_items,
        test_items,
        debug=False,
        progress_message_prefix="",
        job_name="",
    ):
        """
        Fetches and processes wafer point data for a specified facility, design, and manufacturing step.
        Constructs a SQL query to retrieve relevant data, processes it, and pivots it for easy analysis.
        Parameters:
            facility (str): The facility identifier (e.g., '10').
            design_id (str): The design identifier to filter data.
            start_date (str): Start date for data filtering in 'YYYY-MM-DD' format.
            end_date (str): End date for data filtering in 'YYYY-MM-DD' format.
            step (str): The manufacturing step to filter data.
            attr_items (pd.DataFrame): DataFrame of attribute items to include.
            test_items (pd.DataFrame): DataFrame of test items to use as filters.
            debug (bool): If True, returns additional unpivoted DataFrame for debugging.
        Returns:
            pd.DataFrame: Pivoted DataFrame with wafer point data.
            pd.DataFrame (optional): Unpivoted DataFrame with the original query result if debug=True.
        """
        # Define a label to use for the data category in pivoted columns
        subdata = "PointData"
        # Extract unique test parameter IDs from the test_items DataFrame
        test_ids = list(test_items["PARAMETER"].drop_duplicates())
        # Check if any test ID contains the keyword 'ALL' (special case for selecting all test data)
        contains_all = any("ALL" in item for item in test_ids)
        # If 'ALL' is found, skip test filtering; otherwise, format test_ids as a tuple for SQL use
        if not contains_all:
            if len(test_ids) == 1:
                test_ids = f"('{test_ids[0]}')"
            else:
                test_ids = tuple(test_ids)
        # Construct the main SQL query for retrieving relevant wafer point data
        sql = f"""
        WITH LOTS AS (
            SELECT DISTINCT LOT_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_lot`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
        )
        SELECT DISTINCT
            sw.DWH_SRCID, sw.DESIGN_ID, sw.LOT_ID, sw.WAFER_ID, sw.WAFER_SCRIBE,
            sw.MFG_PROCESS_STEP, sw.RUN_COMPLETE_DATE, sw.RUN_COMPLETE_DATETIME,
            sw.WAFER_TYPE, sw.WAFER_SPEC_ID, sws.TEST_VALUE, sws.COMMON_TEST_ID
        FROM (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, LOT_ID, WAFER_ID,
                WAFER_SCRIBE, MFG_PROCESS_STEP, WAFER_RUN_OID, RUN_OID,
                RUN_COMPLETE_DATE, RUN_COMPLETE_DATETIME, WAFER_TYPE, WAFER_SPEC_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sw
        INNER JOIN (
            SELECT DISTINCT
                DWH_SRCID, DESIGN_ID, MFG_FACILITY_ID, RUN_OID, WAFER_SPEC_ID,
                LOT_ID, WAFER_ID, WAFER_SCRIBE, RUN_COMPLETE_DATE,
                RUN_COMPLETE_DATETIME, TEST_VALUE, COMMON_TEST_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_point`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND COMMON_TEST_ID IN {test_ids}
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
            AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
        ) sws
        ON (
            sw.DWH_SRCID = sws.DWH_SRCID AND
            sw.MFG_FACILITY_ID = sws.MFG_FACILITY_ID AND
            sw.RUN_OID = sws.RUN_OID AND
            sw.WAFER_SPEC_ID = sws.WAFER_SPEC_ID AND
            sw.LOT_ID = sws.LOT_ID AND
            sw.WAFER_ID = sws.WAFER_ID AND
            sw.WAFER_SCRIBE = sws.WAFER_SCRIBE AND
            sw.RUN_COMPLETE_DATE = sws.RUN_COMPLETE_DATE AND
            sw.RUN_COMPLETE_DATETIME = sws.RUN_COMPLETE_DATETIME
        )
        """
        # If 'ALL' is in test_ids, remove the filtering condition for COMMON_TEST_ID from the query
        if contains_all:
            sql = sql.replace(f"AND COMMON_TEST_ID IN {test_ids}", "")
        # Execute the SQL query and store the result in a DataFrame
        # record = conn.query(sql)
        # result = record.result()
        # df = result.to_dataframe()
        downloaded_path = str(self.output_path) + f"_temp/{job_name}"
        Path(downloaded_path).mkdir(parents=True, exist_ok=True)
        handle_one_query_at_a_time(
            self.bigquery_manager,
            self.stage_config_obj,
            self.stage_job_id,
            sql,
            downloaded_path,
            progress_message_prefix=progress_message_prefix,
            job_name=job_name,
        )
        df = pd.read_parquet(downloaded_path)
        # Create a unique column name for each measurement type based on various attributes
        df["PIVOT_COLUMN_NAME"] = (
            f"{step}::{subdata}::"
            + df["WAFER_TYPE"]
            + "::"
            + df["WAFER_SPEC_ID"]
            + "::"
            + df["COMMON_TEST_ID"]
        )
        # Define the main columns to retain for the final DataFrame
        essential_columns = [
            "DWH_SRCID",
            "DESIGN_ID",
            "LOT_ID",
            "WAFER_ID",
            "WAFER_SCRIBE",
            "RUN_COMPLETE_DATE",
            "RUN_COMPLETE_DATETIME",
            "TEST_VALUE",
            "PIVOT_COLUMN_NAME",
        ]
        # Remove duplicates, sort by completion date for clarity, and reset the index
        df = (
            df[essential_columns]
            .drop_duplicates()
            .sort_values(by="RUN_COMPLETE_DATETIME", ascending=True)
            .reset_index(drop=True)
        )
        # If there are attribute items, process them and add relevant columns if needed
        if len(attr_items) > 0:
            collected_attr_parameters = list(attr_items["PARAMETER"].drop_duplicates())
            if "Run Complete Datetime" in collected_attr_parameters:
                # Rename columns to give more descriptive names in the output DataFrame
                df = df.rename(
                    columns={
                        "RUN_COMPLETE_DATE": f"{step}::{subdata}::RunCompleteDate",
                        "RUN_COMPLETE_DATETIME": f"{step}::{subdata}::RunCompleteDateTime",
                    }
                )
                # Append these columns to essential columns for final selection
                essential_columns += [
                    f"{step}::{subdata}::RunCompleteDate",
                    f"{step}::{subdata}::RunCompleteDateTime",
                ]
        # Remove the original date columns now that they've been renamed
        essential_columns.remove("RUN_COMPLETE_DATE")
        essential_columns.remove("RUN_COMPLETE_DATETIME")
        # Select only the essential columns
        df = df[essential_columns]
        # Create a list of index columns, excluding 'PIVOT_COLUMN_NAME' and 'TEST_VALUE'
        index_columns = [
            column
            for column in essential_columns
            if column not in ["PIVOT_COLUMN_NAME", "TEST_VALUE"]
        ]
        # Pivot the data so each unique measurement type (PIVOT_COLUMN_NAME) has its own column
        out = df.pivot_table(
            index=index_columns,
            columns="PIVOT_COLUMN_NAME",
            values="TEST_VALUE",
            aggfunc="last",
        ).reset_index()

        pivoted_output_path = Path(str(self.output_path) + f"/{job_name}")
        pivoted_output_path.mkdir(parents=True, exist_ok=True)
        out.to_parquet(pivoted_output_path / "results.parquet")
        # If debug mode is enabled, return both the pivoted DataFrame and original DataFrame
        if debug:
            return out, df
        else:
            return out, None

    def get_sigma_runwafer(
        self,
        facility,
        design_id,
        start_date,
        end_date,
        step,
        attr_items,
        test_items,
        debug=False,
        progress_message_prefix="",
        job_name="",
    ):
        """
        Fetches and processes wafer point data for a specified facility, design, and manufacturing step.
        Constructs a SQL query to retrieve relevant data, processes it, and pivots it for easy analysis.
        Parameters:
            facility (str): The facility identifier (e.g., '10').
            design_id (str): The design identifier to filter data.
            start_date (str): Start date for data filtering in 'YYYY-MM-DD' format.
            end_date (str): End date for data filtering in 'YYYY-MM-DD' format.
            step (str): The manufacturing step to filter data.
            attr_items (pd.DataFrame): DataFrame of attribute items to include.
            test_items (pd.DataFrame): DataFrame of test items to use as filters.
            debug (bool): If True, returns additional unpivoted DataFrame for debugging.
        Returns:
            pd.DataFrame: Pivoted DataFrame with wafer point data.
            pd.DataFrame (optional): Unpivoted DataFrame with the original query result if debug=True.
        """
        # Define a label to use for the data category in pivoted columns
        subdata = "RunWaferData"
        # Prepare test IDs from test_items parameter (list of unique test item names/IDs)
        if len(test_items) > 0:
            # Extract unique test parameter IDs as a list
            test_ids = list(test_items["PARAMETER"].drop_duplicates())
            # Format test_ids as a SQL-compatible tuple
            if len(test_ids) == 1:
                test_ids = f"('{test_ids[0]}')"
            else:
                test_ids = tuple(test_ids)
        else:
            test_ids = ""
        # Construct the main SQL query for retrieving relevant wafer run data
        sql = f"""
    WITH LOTS AS (
    SELECT DISTINCT
    LOT_ID
    FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_lot`
    WHERE 1=1
    AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}' 
    AND MFG_PROCESS_STEP = '{step}'
    AND DESIGN_ID = '{design_id}'
    )
    SELECT DISTINCT
    sw.DWH_SRCID,
    sw.DESIGN_ID,
    sw.LOT_ID,
    sw.WAFER_ID,
    sw.WAFER_SCRIBE,
    sw.MFG_PROCESS_STEP,
    sw.RUN_COMPLETE_DATE,
    sw.RUN_COMPLETE_DATETIME,
    srs.TEST_VALUE,
    srs.COMMON_TEST_ID,
    sr.RUN_ID,
    sr.EQUIPMENT_ID,
    sr.PROCESS_ID,
    sr.PROCESS_START_DATETIME,
    sr.PROCESS_END_DATETIME,
    sr.RUN_CREATE_DATETIME,
    sr.UPDATE_DATETIME
    FROM (
      SELECT DISTINCT
      DWH_SRCID,
      DESIGN_ID,
      MFG_FACILITY_ID,
      LOT_ID,
      WAFER_ID,
      WAFER_SCRIBE,
      MFG_PROCESS_STEP,
      WAFER_RUN_OID,
      RUN_OID,
      RUN_COMPLETE_DATE,
      RUN_COMPLETE_DATETIME,
      FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_wafer`
      WHERE 1=1
      AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}' 
      AND MFG_PROCESS_STEP = '{step}'
      AND DESIGN_ID = '{design_id}'
      AND LOT_ID IN (SELECT DISTINCT LOT_ID FROM LOTS)
    ) sw
    INNER JOIN(
      SELECT DISTINCT
      DWH_SRCID,
      MFG_FACILITY_ID,
      RUN_OID,
      RUN_ID,
      EQUIPMENT_ID,
      PROCESS_ID,
      RUN_COMPLETE_DATE,
      RUN_COMPLETE_DATETIME,
      PROCESS_START_DATETIME,
      PROCESS_END_DATETIME,
      RUN_CREATE_DATETIME,
      UPDATE_DATETIME,
      FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_run` 
      WHERE 1=1
      AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}' 
    ) sr
    ON (
      sw.DWH_SRCID = sr.DWH_SRCID AND
      sw.MFG_FACILITY_ID = sr.MFG_FACILITY_ID AND
      sw.RUN_OID = sr.RUN_OID AND
      sw.RUN_COMPLETE_DATE = sr.RUN_COMPLETE_DATE AND
      sw.RUN_COMPLETE_DATETIME = sr.RUN_COMPLETE_DATETIME
    )
    INNER JOIN (
      SELECT DISTINCT
      DWH_SRCID,
      MFG_FACILITY_ID,
      RUN_OID,
      RUN_COMPLETE_DATE,
      RUN_COMPLETE_DATETIME,
      TEST_VALUE,
      COMMON_TEST_ID
      FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_run_summary` 
      WHERE 1=1
      AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}' 
      AND COMMON_TEST_ID IN {test_ids}
    ) srs
    ON (
    sw.DWH_SRCID = srs.DWH_SRCID AND
    sw.MFG_FACILITY_ID = srs.MFG_FACILITY_ID AND
    sw.RUN_OID = srs.RUN_OID AND
    sw.RUN_COMPLETE_DATE = srs.RUN_COMPLETE_DATE AND
    sw.RUN_COMPLETE_DATETIME = srs.RUN_COMPLETE_DATETIME
    )
    """
        # Remove unnecessary joins and columns if no test items are specified
        if len(test_items) == 0:
            str1 = f"""
    INNER JOIN (
      SELECT DISTINCT
      DWH_SRCID,
      MFG_FACILITY_ID,
      RUN_OID,
      RUN_COMPLETE_DATE,
      RUN_COMPLETE_DATETIME,
      TEST_VALUE,
      COMMON_TEST_ID
      FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_run_summary` 
      WHERE 1=1
      AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}' 
      AND COMMON_TEST_ID IN {test_ids}
    ) srs
    ON (
    sw.DWH_SRCID = srs.DWH_SRCID AND
    sw.MFG_FACILITY_ID = srs.MFG_FACILITY_ID AND
    sw.RUN_OID = srs.RUN_OID AND
    sw.RUN_COMPLETE_DATE = srs.RUN_COMPLETE_DATE AND
    sw.RUN_COMPLETE_DATETIME = srs.RUN_COMPLETE_DATETIME
    )
    """
            str2 = f"""
    srs.TEST_VALUE,
    srs.COMMON_TEST_ID,
    """
            # Remove test data joins and columns from the SQL query
            sql = sql.replace(str1, "")
            sql = sql.replace(str2, "")
        # Execute the query and convert the result to a DataFrame
        # record = conn.query(sql)
        # result = record.result()
        # df = result.to_dataframe()
        downloaded_path = str(self.output_path) + f"_temp/{job_name}"
        Path(downloaded_path).mkdir(parents=True, exist_ok=True)
        handle_one_query_at_a_time(
            self.bigquery_manager,
            self.stage_config_obj,
            self.stage_job_id,
            sql,
            downloaded_path,
            progress_message_prefix=progress_message_prefix,
            job_name=job_name,
        )
        df = pd.read_parquet(downloaded_path)
        # Pivot and prepare output DataFrame based on whether test_items are present
        if len(test_items) > 0:
            df["PIVOT_COLUMN_NAME"] = f"{step}::{subdata}::" + df["COMMON_TEST_ID"]
            essential_columns = [
                "DWH_SRCID",
                "DESIGN_ID",
                "LOT_ID",
                "WAFER_ID",
                "WAFER_SCRIBE",
                "RUN_ID",
                "EQUIPMENT_ID",
                "PROCESS_ID",
                "RUN_COMPLETE_DATE",
                "RUN_COMPLETE_DATETIME",
                "PROCESS_START_DATETIME",
                "PROCESS_END_DATETIME",
                "RUN_CREATE_DATETIME",
                "UPDATE_DATETIME",
                "TEST_VALUE",
                "PIVOT_COLUMN_NAME",
            ]
        else:
            essential_columns = [
                "DWH_SRCID",
                "DESIGN_ID",
                "LOT_ID",
                "WAFER_ID",
                "WAFER_SCRIBE",
                "RUN_ID",
                "EQUIPMENT_ID",
                "PROCESS_ID",
                "RUN_COMPLETE_DATE",
                "RUN_COMPLETE_DATETIME",
                "PROCESS_START_DATETIME",
                "PROCESS_END_DATETIME",
                "RUN_CREATE_DATETIME",
                "UPDATE_DATETIME",
            ]
        # Drop duplicates, sort by completion time, and reset index
        df = (
            df[essential_columns]
            .drop_duplicates()
            .sort_values(by="RUN_COMPLETE_DATETIME", ascending=True)
            .reset_index(drop=True)
        )
        # Add columns based on requested attribute items
        if len(attr_items) > 0:
            collected_attr_parameters = list(attr_items["PARAMETER"].drop_duplicates())
            columns_to_add = []
            if ("RunCompleteDatetime" in collected_attr_parameters) or (
                "RunCompleteDateTime" in collected_attr_parameters
            ):
                df = df.rename(
                    columns={
                        "RUN_COMPLETE_DATE": f"{step}::{subdata}::RunCompleteDate",
                        "RUN_COMPLETE_DATETIME": f"{step}::{subdata}::RunCompleteDateTime",
                    }
                )
                essential_columns.append(f"{step}::{subdata}::RunCompleteDate")
                essential_columns.append(f"{step}::{subdata}::RunCompleteDateTime")
            if "EquipmentId" in collected_attr_parameters:
                df = df.rename(
                    columns={"EQUIPMENT_ID": f"{step}::{subdata}::EquipmentId"}
                )
                essential_columns.append(f"{step}::{subdata}::EquipmentId")
            if "ProcessId" in collected_attr_parameters:
                df = df.rename(columns={"PROCESS_ID": f"{step}::{subdata}::ProcessId"})
                essential_columns.append(f"{step}::{subdata}::ProcessId")
            if "RunId" in collected_attr_parameters:
                df = df.rename(columns={"RUN_ID": f"{step}::{subdata}::RunId"})
                essential_columns.append(f"{step}::{subdata}::RunId")
            if "ProcessStartDateTime" in collected_attr_parameters:
                df = df.rename(
                    columns={
                        "PROCESS_START_DATETIME": f"{step}::{subdata}::ProcessStartDateTime"
                    }
                )
                essential_columns.append(f"{step}::{subdata}::ProcessStartDateTime")
            if "ProcessEndDateTime" in collected_attr_parameters:
                df = df.rename(
                    columns={
                        "PROCESS_END_DATETIME": f"{step}::{subdata}::ProcessEndDateTime"
                    }
                )
                essential_columns.append(f"{step}::{subdata}::ProcessEndDateTime")
            if "RunCreateDateTime" in collected_attr_parameters:
                df = df.rename(
                    columns={
                        "RUN_CREATE_DATETIME": f"{step}::{subdata}::RunCreateDateTime"
                    }
                )
                essential_columns.append(f"{step}::{subdata}::RunCreateDateTime")
            if "UpdateDateTime" in collected_attr_parameters:
                df = df.rename(
                    columns={"UPDATE_DATETIME": f"{step}::{subdata}::UpdateDateTime"}
                )
                essential_columns.append(f"{step}::{subdata}::UpdateDateTime")
        # Remove non-essential columns after renaming
        columns_to_remove = [
            "RUN_COMPLETE_DATE",
            "RUN_COMPLETE_DATETIME",
            "EQUIPMENT_ID",
            "PROCESS_ID",
            "RUN_ID",
            "PROCESS_START_DATETIME",
            "PROCESS_END_DATETIME",
            "RUN_CREATE_DATETIME",
            "UPDATE_DATETIME",
        ]
        for col in columns_to_remove:
            if col in essential_columns:
                essential_columns.remove(col)
        df = df[essential_columns]
        # Pivot if test items were provided
        if len(test_items) > 0:
            index_columns = [
                column
                for column in essential_columns
                if column not in ["PIVOT_COLUMN_NAME", "TEST_VALUE"]
            ]
            out = df.pivot_table(
                index=index_columns,
                columns="PIVOT_COLUMN_NAME",
                values="TEST_VALUE",
                aggfunc="last",
            ).reset_index()
        else:
            out = df.copy()

        pivoted_output_path = Path(str(self.output_path) + f"/{job_name}")
        pivoted_output_path.mkdir(parents=True, exist_ok=True)
        out.to_parquet(pivoted_output_path / "results.parquet")
        # Return either the pivoted DataFrame (out) alone or with the full DataFrame (df) based on debug mode
        if debug:
            return out, df
        else:
            return out, None

    def get_space_calc(
        self,
        facility,
        design_id,
        start_date,
        end_date,
        step,
        attr_items,
        test_items,
        days_to_pad=5,
        debug=False,
        progress_message_prefix="",
        job_name="",
    ):
        """
        Fetches and processes wafer point data for a specified facility, design, and manufacturing step.
        Constructs a SQL query to retrieve relevant data, processes it, and pivots it for easy analysis.
        Parameters:
            facility (str): The facility identifier (e.g., '10').
            design_id (str): The design identifier to filter data.
            start_date (str): Start date for data filtering in 'YYYY-MM-DD' format.
            end_date (str): End date for data filtering in 'YYYY-MM-DD' format.
            step (str): The manufacturing step to filter data.
            attr_items (pd.DataFrame): DataFrame of attribute items to include.
            test_items (pd.DataFrame): DataFrame of test items to use as filters.
            debug (bool): If True, returns additional unpivoted DataFrame for debugging.
        Returns:
            pd.DataFrame: Pivoted DataFrame with wafer point data.
            pd.DataFrame (optional): Unpivoted DataFrame with the original query result if debug=True.
        """
        # Define a label to use for the data category in pivoted columns
        subdata = "WaferData"
        # Extract unique test parameter IDs from the test_items DataFrame
        test_ids = list(test_items["PARAMETER"].drop_duplicates())
        if len(test_ids) == 1:
            test_ids = f"('{test_ids[0]}')"
        else:
            test_ids = tuple(test_ids)
        padded_start_date = (
            datetime.strptime(start_date, "%Y-%m-%d") - timedelta(days=days_to_pad)
        ).strftime("%Y-%m-%d")
        padded_end_date = (
            datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=days_to_pad)
        ).strftime("%Y-%m-%d")
        # Construct the main SQL query for retrieving relevant wafer space calc data
        sql = f"""
        WITH LOTS AS (
            SELECT DISTINCT LOT_ID
            FROM `gdw-prod-data.fab_{facility}_sigma.idl_sigma_lot`
            WHERE 1=1
            AND RUN_COMPLETE_DATE BETWEEN '{start_date}' AND '{end_date}'
            AND MFG_PROCESS_STEP = '{step}'
            AND DESIGN_ID = '{design_id}'
        )
        SELECT
        TRIM(S.EXVAL_01) AS DESIGN_ID,
        TRIM(S.EXVAL_12) AS LOT_ID,
        TRIM(S.DAVAL_03) AS WAFER_ID,
        TRIM(S.EXVAL_13) AS WAFER_SCRIBE,
        TRIM(S.PARAMETER_NAME) AS PARAMETER,
        CAST(S.EXT_MV AS float64) AS `MEAN`,
        CAST(S.EXT_SIGMA AS float64) AS STDEV,
        CAST(S.EXT_MAX AS float64) AS `MAX`,
        CAST(S.EXT_MIN AS float64) AS `MIN`,
        CAST(C2.EXT_MV_UCL AS float64) AS UCL,
        CAST(C2.EXT_MV_LCL AS float64) AS LCL,
        CAST(C2.EXT_MV_CENTER AS float64) AS CENTER,
        CAST(C2.MV_UAL AS float64) AS UAL,
        CAST(C2.MV_LAL AS float64) AS LAL,
        CAST(S.SPEC_LOWER AS float64) AS LOWSPEC,
        CAST(S.SPEC_UPPER AS float64) AS HIGHSPEC,
        CAST(S.SPEC_TARGET AS float64) AS SPECTARGET,
        CAST(S.EXT_MEDIAN AS float64) AS MEDIAN,
        S.SAMPLE_DATE AS SAMPLE_DATE
        FROM
        `gdw-prod-data.fab_{facility}_spc.T_EXT_SAMPLES` S
        INNER JOIN
        `gdw-prod-data.fab_{facility}_spc.T_EXT_SAMPLES_CALC` C
        ON
        S.SAMPLE_ID = C.SAMPLE_ID
        INNER JOIN
        `gdw-prod-data.fab_{facility}_spc.T_EXT_SAMPLES_CALC2` C2
        ON
        C.CALC2_ID = C2.CALC2_ID
        WHERE 1=1
        AND TRIM(S.EXVAL_12) IN (SELECT DISTINCT LOT_ID FROM LOTS)
        AND TRIM(S.EXVAL_04) = '{step}'
        AND TRIM(S.PARAMETER_NAME) IN {test_ids}
        AND S.SAMPLE_DATE BETWEEN '{padded_start_date}' AND '{padded_end_date}'
        """
        print("-------------SPACE----")
        print(sql)
        print("=======================================")
        # Execute the SQL query and store the result in a DataFrame
        # record = conn.query(sql)
        # result = record.result()
        # df = result.to_dataframe()
        downloaded_path = str(self.output_path) + f"_temp/{job_name}"
        Path(downloaded_path).mkdir(parents=True, exist_ok=True)
        handle_one_query_at_a_time(
            self.bigquery_manager,
            self.stage_config_obj,
            self.stage_job_id,
            sql,
            downloaded_path,
            progress_message_prefix=progress_message_prefix,
            job_name=job_name,
        )
        df = pd.read_parquet(downloaded_path)
        gb = test_items.groupby(["PARAMETER", "STAT"])
        # Add DWH_SRCID column for consistency
        df["DWH_SRCID"] = f"FAB {facility}"
        df = df.sort_values(by="SAMPLE_DATE", ascending=True).reset_index(drop=True)
        out = (
            df[["DWH_SRCID", "DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )
        for name, group in gb:
            parameter = name[0]
            stat = name[1]
            df_slice = df[df["PARAMETER"] == parameter]
            # Define the main columns to retain for the final DataFrame
            essential_columns = [
                "DWH_SRCID",
                "DESIGN_ID",
                "LOT_ID",
                "WAFER_ID",
                "WAFER_SCRIBE",
                stat,
            ]
            # Select only the essential columns, store as subdata
            df_slice = df_slice[essential_columns].drop_duplicates()
            # Create a unique column name for each measurement type based on various attributes
            df_slice["PIVOT_COLUMN_NAME"] = f"{step}::{subdata}::{parameter}({stat})"
            # Create a list of index columns, excluding 'PIVOT_COLUMN_NAME' and 'TEST_VALUE'
            index_columns = [
                column
                for column in essential_columns
                if column not in ["PIVOT_COLUMN_NAME", stat]
            ]
            # Pivot the data so each unique measurement type (PIVOT_COLUMN_NAME) has its own column
            df_slice_pivot = df_slice.pivot_table(
                index=index_columns,
                columns="PIVOT_COLUMN_NAME",
                values=stat,
                aggfunc="last",
            ).reset_index()
            # Merge the data on indices
            out = out.merge(
                df_slice_pivot,
                how="outer",
                on=["DWH_SRCID", "DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
            )

        pivoted_output_path = Path(str(self.output_path) + f"/{job_name}")
        pivoted_output_path.mkdir(parents=True, exist_ok=True)
        out.to_parquet(pivoted_output_path / "results.parquet")
        # If debug mode is enabled, return both the pivoted DataFrame and original DataFrame
        if debug:
            return out, df
        else:
            return out, None


def read_gql(fname):
    """
    Reads a GQL (GraphQL) file and extracts data items, specifically lines that start
    with 'AttrItem' or 'TestItem'. Parses each line based on '=' or ASCII DEL
    character (0x7f) and organizes the extracted data into a DataFrame.

    Parameters:
        fname (str): The filename or path of the GQL file to read.

    Returns:
        pd.DataFrame: A DataFrame containing extracted information with columns:
                      'ITEM', 'DATASET', 'TABLE', 'STEP', 'PARAMETER', 'STAT'.
    """

    # Open the file in read mode
    fd = open(fname, "r")
    # Read the entire file content as a single string
    sqlFile = fd.read()
    # Close the file after reading
    fd.close()

    # Split the file content into lines for easy filtering
    gql_items = sqlFile.split("\n")

    # Filter lines that start with 'AttrItem' or 'TestItem'
    # - This filter relies on specific GQL format, so changes in format may break this
    gql_items = [i for i in gql_items if i.startswith(("AttrItem", "TestItem"))]

    sub_items_list = []
    # For each filtered line, split the content by '=' or ASCII DEL (0x7f) to separate fields
    for item in gql_items:
        sub_items = re.split(r"=|\x7f", item)
        sub_items_list.append(sub_items)

    # Create a DataFrame from the list of lists (sub_items_list) with parsed fields
    data_to_pull = pd.DataFrame(sub_items_list)
    # Assign column names to the DataFrame to represent each parsed field
    data_to_pull.columns = ["ITEM", "DATASET", "TABLE", "STEP", "PARAMETER", "STAT"]

    return data_to_pull  # Return the organized DataFrame with extracted data


def uc2_sigma_data_pull_new(
    bigquery_manager: BigQueryJobsManager, stage_config_obj, stage_job_id, output_dir
):
    fd_data_pull_job_config: FdDataPullJobConfig = stage_config_obj.stage_job_record
    inputs: UC2SigmaDataPullInput = fd_data_pull_job_config.stage_config.inputs

    if inputs is None:
        raise ValueError(
            "The inputs for UC2 sigma data pull is None , UC2SigmaDataPullInput"
        )
    facility = str(inputs.facilities.selected_values[0])
    start_date = inputs.start_date
    end_date = inputs.end_date
    days_to_pad = 10  # TODO: make this input from user
    steps = inputs.traveler_steps.selected_values
    design_id = inputs.design_ids.selected_values[0]

    # FIND IF ITS ONLY GQL FLOW
    only_gql_flow = (
        inputs.gql_file_details is not None and inputs.gql_file_details.gql_file_path
    ) and str(inputs.measurement_steps.file_path) == "."
    # having file in measurement steps => not just gql flow ,
    # TODO : add explicit variable to find this as there can be add_item
    sigma_measurement_steps = inputs.measurement_steps.selected_values
    sigma_point_steps = inputs.point_steps.selected_values
    sigma_measurement_parameters = inputs.measurement_parameters.selected_values
    sigma_point_parameters = inputs.point_parameters.selected_values
    sigma_run_parameters = inputs.run_parameters.selected_values
    sigma_wafer_parameters = inputs.wafer_parameters.selected_values
    only_gql_flow = (
        check_subset_to_gql(
            inputs.gql_file_details.parquet_file_path,
            sigma_run_parameters,
            sigma_wafer_parameters,
            sigma_measurement_steps,
            sigma_measurement_parameters,
            sigma_point_steps,
            sigma_point_parameters,
        )
        if only_gql_flow
        else False
    )

    if not only_gql_flow:  # for non gql flow or both using old queries
        uc2_sigma_data_pull(
            bigquery_manager, stage_config_obj, stage_job_id, output_dir
        )
        return

    print("======================ONLY GQL FLOW==========================")
    # Only for GQL we go with new flow
    data_to_pull = read_gql(inputs.gql_file_details.gql_file_path)
    # This needs to be an isolated folder where only the current relevant GQL items are pulled
    temp_output_dir = str(output_dir) + "_temp_uc2_sigma"
    # Create the output directory if it doesn't already exist
    os.makedirs(temp_output_dir, exist_ok=True)
    # Group the input data by the 'DATASET', 'TABLE', and 'STEP' columns
    gb = data_to_pull.groupby(["DATASET", "TABLE", "STEP"])
    # Loop over each group in the grouped data with a progress bar

    uc2_sigma_helper = UC2SigmaHelper(
        bigquery_manager, stage_config_obj, stage_job_id, temp_output_dir
    )
    count = 0
    group_count = len(gb)
    for name, group in gb:
        # Extract specific identifiers for each group
        dataset = name[0]  # Dataset name (e.g., 'Sigma')
        table = name[1]  # Table name (e.g., 'Wafer')
        step = name[2]  # Step name (process step within the workflow)
        # Separate items in the group into attributes and tests
        # AttrItem contains metadata for processing, and TestItem contains test parameters for analysis
        attr_items = group[group["ITEM"] == "AttrItem"].reset_index(drop=True)
        test_items = group[group["ITEM"] == "TestItem"].reset_index(drop=True)

        job_name = f"{dataset}_{table}_{step}"

        progress_message_prefix = f"[{count}/{group_count}] "
        # Call different functions based on dataset and table type
        # Each condition applies a specific data extraction function and saves the output in parquet format
        if (dataset == "Sigma") and (table == "Wafer"):
            # For Sigma Wafer data, call the 'get_sigma_wafer' function with relevant parameters
            uc2_sigma_helper.get_sigma_wafer(
                facility,
                design_id,
                str(start_date),
                str(end_date),
                step,
                attr_items,
                test_items,
                debug=False,
                progress_message_prefix=progress_message_prefix,
                job_name=job_name,
            )
        if (dataset == "Sigma") and (table == "Measurement"):
            # For Sigma Measurement data, call the 'get_sigma_measurement' function
            uc2_sigma_helper.get_sigma_measurement(
                facility,
                design_id,
                str(start_date),
                str(end_date),
                step,
                attr_items,
                test_items,
                debug=False,
                progress_message_prefix=progress_message_prefix,
                job_name=job_name,
            )

        if (dataset == "Sigma") and (table == "Point"):
            # For Sigma Point data, call the 'get_sigma_point' function
            uc2_sigma_helper.get_sigma_point(
                facility,
                design_id,
                str(start_date),
                str(end_date),
                step,
                attr_items,
                test_items,
                debug=False,
                progress_message_prefix=progress_message_prefix,
                job_name=job_name,
            )

        if (dataset == "Sigma") and ((table == "Run") or (table == "RunWafer")):
            # For Sigma Run or RunWafer data, call the 'get_sigma_runwafer' function
            uc2_sigma_helper.get_sigma_runwafer(
                facility,
                design_id,
                str(start_date),
                str(end_date),
                step,
                attr_items,
                test_items,
                debug=False,
                progress_message_prefix=progress_message_prefix,
                job_name=job_name,
            )

        if (dataset == "SPACE Calculated Data") and (table == "Wafer"):
            # For SPACE Calculated data, call the 'get_space_calc' function
            uc2_sigma_helper.get_space_calc(
                facility,
                design_id,
                str(start_date),
                str(end_date),
                step,
                attr_items,
                test_items,
                debug=False,
                progress_message_prefix=progress_message_prefix,
                job_name=job_name,
            )
            # Save the output DataFrame to a parquet file
            # out.to_parquet(os.path.join(output_dir, f'{dataset}_{table}_{step}.parquet'), index=False)
        count += 1

    # Find the list of all files that were downloaded by using the GQL pipeline
    files = glob(f"{temp_output_dir}/*")
    # Initialize an empty DataFrame to store the combined data from multiple files
    gcp_data = pd.DataFrame()
    # Loop through each file in the list of files
    for file in files:
        # Read the current file in the loop, loading it as a temporary DataFrame
        temp = pd.read_parquet(file)
        # If gcp_data is empty, it means this is the first file being read
        if len(gcp_data) == 0:
            # Copy the contents of the first file into gcp_data to initialize it
            gcp_data = temp.copy()
        else:
            # For all subsequent files, merge them with gcp_data
            # Use an outer join on specific key columns to include all rows from both dataframes
            # 'how="outer"' keeps all data from both DataFrames even if they don't match in key columns
            gcp_data = pd.merge(
                gcp_data,  # The DataFrame we're building up with each file
                temp,  # The current file's data we're merging
                how="outer",  # Use outer join to keep all rows from both sources
                on=["DWH_SRCID", "DESIGN_ID", "LOT_ID", "WAFER_ID", "WAFER_SCRIBE"],
                # Columns used as keys to align rows
            )
    # Generate the Parent Lot Column
    gcp_data["PARENT_LOT"] = gcp_data["LOT_ID"].apply(lambda x: str(x).split(".")[0])

    gcp_data.to_parquet(str(output_dir) + "/joined_results.parquet")
