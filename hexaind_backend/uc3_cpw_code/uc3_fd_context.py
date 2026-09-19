import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


def is_valid_date(date_string):
    # True if the string is in valid YYYY-MM-DD format, False otherwise.
    try:
        # Try parsing the date string
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def hexaind_custom_widget_function(
    sessions_df: pd.DataFrame,
    session_name: str,
    start_date: str,
    end_date: str,
) -> (pd.DataFrame, pd.DataFrame):
    data_pull_prefrence = "PULL DATA ONLY"
    if not is_valid_date(date_string=start_date):
        raise Exception(
            f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
        )
    if not is_valid_date(date_string=end_date):
        raise Exception(
            f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
        )

    # 1. Find session_id based on session_name in sessions_df
    session_id = str(sessions_df[session_name][0])
    print(f"selected session id to clone {session_id}")
    url = f"http://micron_apis_proxy:80/micron/data_catalog/sessions/{session_id}"
    response = requests.get(url)
    if response.status_code == 200:
        session_data = response.json()
        data_pull_job_id = session_data.get("data_pull_job_id", None)
        print(f"data_pull_job_id: {data_pull_job_id}")
    else:
        print(f"Failed to fetch session data for {session_id}.")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""

    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={data_pull_job_id}&stage=SAVE_HIGH_LEVEL_DC_DETAILS"
    response = requests.get(url)
    dc_stage_payload = {}
    if response.status_code == 200:
        dc_stage_payload = response.json().get("current_stage_inputs", {})
    else:
        raise Exception(
            f"Unable to get response for  SAVE_HIGH_LEVEL_DC_DETAILS : {response.text}"
        )

    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/generate_final_data_aggregate_context?data_pull_job_id={data_pull_job_id}"
    dc_stage_payload["start_date"] = start_date
    dc_stage_payload["end_date"] = end_date
    response = requests.post(url, json=dc_stage_payload)
    # df = pd.DataFrame()
    df1 = pd.DataFrame()
    fd_context_and_tools_joined_path = ""
    if response.status_code == 200:
        resp = response.json()
        print(resp)
        fd_context_and_tools_joined_path = resp["recipes"]["file_path"]
        df1 = pd.DataFrame([{"file_path": fd_context_and_tools_joined_path}])
    else:
        raise Exception(
            f"Unable to get response for generate final fd context data : {response.text}"
        )

    url = "http://micron_apis_proxy:80/micron/data_catalog/query/data"
    payload_data_preview = {
        # "": os.getenv("CURRENT_PROJECT_ID"),
        "path": fd_context_and_tools_joined_path,
        "ignore_pagination": True,
        # "page_size": 10000000,
    }
    df2 = pd.DataFrame()
    response = requests.post(url, json=payload_data_preview)
    # df = pd.DataFrame()
    if response.status_code == 200:
        data_preview_response = response.json().get("data", {})
        df2 = pd.DataFrame(data_preview_response)
    else:
        raise Exception(f"Unable to get response for preview data : {response.text}")

    return df1, df2