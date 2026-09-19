import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests


def hexaind_custom_widget_function(
    sessions_df: pd.DataFrame,
    session_name: str,
) -> (pd.DataFrame, pd.DataFrame):
    """
    This function manages a workflow for fetching and processing data pulls based on a session's configuration.
    It fetches data from an external API, creates a new session, and triggers a data pull. It updates a configuration
    JSON file and returns a summary dataframe of the fetched results.
    Parameters
    ----------
    sessions_df : pd.DataFrame
        A DataFrame containing session information. The `session_name` must correspond to a column
        in this DataFrame.
    session_name : str
        The name of the session to use for the data pull, matching a column name in `sessions_df`.
    Returns
    -------
    pd.DataFrame
        A DataFrame containing a summary of the fetched data files. The summary includes file names and paths for the files
        that were retrieved during the data pull process. The DataFrame has one row with column names corresponding to
        the file names and paths.
    Raises
    ------
    Exception
        If the previous data pull has not been marked as completed in the configuration file and `override_dates_from_config`
        is not set to "True", an exception is raised to indicate the need to wait for the previous run to finish.
    """
    # --------------fetch workflow owner id-------------------------
    custom_results_dir = os.getenv("CUSTOM_RESULTS_DIR")
    if custom_results_dir is None:
        raise Exception("Unable to detect run id via custom results dir")
    matches = re.findall(r"r_([a-fA-F0-9]{24})", custom_results_dir)
    current_run_id = matches[-1] if matches else None
    if current_run_id is None:
        raise Exception(f"Unable to detect run id via {custom_results_dir}")
    siteId = 1
    projectId = 1
    workflowId = 1
    runId = current_run_id
    backend_url = f"http://micron_apis_proxy:80/v1/sites/{siteId}/projects/{projectId}/workflow/{workflowId}/run/{runId}/status"
    response = requests.get(backend_url)
    workflow_owner_id = None
    if response.status_code == 200:
        response_data = response.json()
        print("response from run status..got success")
        workflow_owner_id = response_data["workflow"]["owner_id"]
        print(f"workflow_owner_id: {workflow_owner_id}")
    else:
        print(f"Failed to fetch run status data for {runId}. {response.text}")
        workflow_owner_id = "669d4716fa67d7b1d58bbbc3"  # "67650fef7d1ad6470071b112"
        # raise Exception(f"Failed to fetch run status data for {runId}.")
    results_dir = os.getenv("RESULTS_DIR")
    if results_dir is None:
        raise Exception("Expecting RESULTS DIR env var which is not set/set to None")
    # --------------------------------------------------------------------------------------------------
    stage_name = "SAVE_HIGH_LEVEL_DC_DETAILS"
    config_data = {}
    config_file_json = Path(results_dir).parent / f"cpw_{stage_name}.json"
    # config_file_json.parent.mkdir(parents=True, exist_ok=True)
    # current_date_str = datetime.now().strftime("%Y-%m-%d")
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
        raise Exception(f"Failed to fetch session data for {session_id}.")
    # 2. Fetch results
    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={data_pull_job_id}&stage={stage_name}"
    response = requests.get(url)
    df = pd.DataFrame()
    if response.status_code == 200:
        dc_stage_payload = response.json().get("current_stage_inputs", {})
        print(f"results ...: {dc_stage_payload}")
        df["traveler_steps"] = dc_stage_payload.get("traveler_steps", {}).get(
            "selected_values", ["Not Found"]
        )
    else:
        raise Exception(f"Unable to get response for {stage_name} : {response.text}")
    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={data_pull_job_id}&stage=TRAVELER_STEP"
    response = requests.get(url)
    # df = pd.DataFrame()
    traveler_steps_path = ""
    if response.status_code == 200:
        dc_stage_payload = response.json().get("current_stage_results", {})
        df["baseline_line_traveler_id"] = dc_stage_payload.get(
            "baseline_line_traveler_id", "not found"
        )
        traveler_steps_path = dc_stage_payload.get("traveler_steps", {}).get(
            "file_path"
        )
    else:
        raise Exception(f"Unable to get response for {stage_name} : {response.text}")
    url = "http://micron_apis_proxy:80/micron/data_catalog/query/data"
    payload_data_preview = {
        # "": os.getenv("CURRENT_PROJECT_ID"),
        "path": traveler_steps_path,
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

    return df, df2
