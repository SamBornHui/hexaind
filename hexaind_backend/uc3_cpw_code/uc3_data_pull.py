import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import pandas as pd
import requests

from app.workers.micron.worker import task_micron_data_pull


def update_transit_json(config_data, file_path: Optional[Path] = None):
    # update uc3_data_pull_config_intransit.json
    transit_config_file_path = (
        Path(os.getenv("RESULTS_DIR")).parent / "uc3_data_pull_config_intransit.json"
    )
    if not file_path:
        file_path = transit_config_file_path
    with open(file_path, "w") as json_file:
        json.dump(config_data, json_file, indent=4)


def hexaind_custom_widget_function(
    sessions_df: pd.DataFrame,
    session_name: str,
    stage_name: str,
    start_date: str,
    end_date: str,
    default_start_date: str,
    override_dates_from_config: str,
    pull_as_session: str,
) -> pd.DataFrame:
    """
    This function manages a workflow for fetching and processing data pulls based on a session's configuration.
    It fetches data from an external API, creates a new session, and triggers a data pull. It updates a configuration
    JSON file and returns a summary dataframe of the fetched results.

    Parameters
    ----------
    sessions_df : pd.DataFrame
        A DataFrame containing session information where `session_name` corresponds to a column in this DataFrame.

    session_name : str
        The name of the session to be used for data pull, which corresponds to a column name in the `sessions_df` DataFrame.

    stage_name : str
        The name of the stage for data pull (though this parameter is currently unused in the function).

    start_date : str
        The start date for the data pull in the format 'YYYY-MM-DD'. This value may be overridden by the configuration file
        if the override option is not set.

    end_date : str
        The end date for the data pull in the format 'YYYY-MM-DD'. This value is used if provided or defaults to the current date.

    default_start_date : str
        The default start date if no `start_date` is provided or if `override_dates_from_config` is set to False.

    override_dates_from_config : str
        If set to "True", the start and end dates are taken from the configuration file, overriding the passed parameters.

    pull_as_session : str
        If set to "True", the function pulls data based on the session and does not update the configuration. If "False",
        it updates the configuration with the current start and end dates.

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
    persist_session = "False"

    # fetch start_date and end_date
    config_data = {}
    if pull_as_session != "True":
        config_file_json = (
            Path(os.getenv("RESULTS_DIR")).parent / "uc3_data_pull_config.json"
        )
        print(f"Config Path: {config_file_json}")
        config_file_json.parent.mkdir(parents=True, exist_ok=True)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        if not override_dates_from_config:
            if config_file_json.exists():
                with open(config_file_json, "r") as json_file:
                    loaded_data = json.load(json_file)
                print(f"Loaded json {loaded_data}")
                if loaded_data.get("current_pull_status") != "completed":
                    print("current config pull is not yet done. {loaded_data}")
                    raise Exception(
                        "Previous run did not mark as completed, wait till previous run is done or use override option"
                    )
                start_date = loaded_data.get("next_start_date")
            if (
                default_start_date == ""
            ):  # get 6 months old data if no startdate or default start date is provided
                six_months_ago = datetime.now() - timedelta(days=180)
                default_start_date = six_months_ago.strftime("%Y-%m-%d")
            config_data = {
                "start_date": start_date if start_date else default_start_date,
                "end_date": current_date_str,
            }
        else:
            config_data = {
                "start_date": start_date if start_date else default_start_date,
                "end_date": end_date if end_date else current_date_str,
            }
            config_data["next_start_date"] = config_data["start_date"]

        config_data["status"] = "inprogress"
        config_data["message"] = "fetched start date and end date"
        config_data["results_dir"] = os.getenv(
            "RESULTS_DIR"
        )  # results dir contains p_{project_id} and r_{run_id}
        update_transit_json(config_data)

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
        return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    # 2. Fetch sigma DC payload (UC3_SIGMA_DATA)
    if stage_name not in ["UC3_SIGMA_DATA", "PROBE_DATA_PULL"]:
        stage_name = "UC3_SIGMA_DATA"
    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={data_pull_job_id}&stage={stage_name}"
    response = requests.get(url)
    if response.status_code == 200:
        dc_stage_payload = response.json().get("current_stage_inputs", {})
        print(f"Sigma DC Payload: {dc_stage_payload}")
    else:
        print(f"Failed to fetch Sigma DC Payload. status code:{response.status_code}")
        print(f"response - text : {response.text}")
        return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    # 3. Create new session using /data_catalog/create_session
    user_id = "6710b78c646947ee6e1c0831"
    new_session_url = f"http://micron_apis_proxy:80/micron/data_catalog/create_data_catalog_session_without_token/{user_id}"
    payload = {
        "project_id": os.getenv("CURRENT_PROJECT_ID"),
        "name": "WF_CREATED_SESSION_INTERNAL",
        "description": "created via wf",
        "data_source_type": "FD_TRACE",
    }
    response = requests.post(new_session_url, json=payload)
    if response.status_code == 200:
        new_session_data = response.json()
        print(f"new_session_data...{new_session_data}")
        new_data_pull_job_id = new_session_data.get("data_pull_job_id", None)
        print(f"New Data Pull Job ID: {new_data_pull_job_id}")
    else:
        print("Failed to create new session.")
        print(f"Failed to create new session. status code:{response.status_code}")
        print(f"response - text : {response.text}")
        return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    # 4. update db via API
    print(
        "--------------------------------------------------------------------------------------"
    )
    if pull_as_session != "True":
        print(f"modifying start and end_dates with config_data, {config_data}")
        dc_stage_payload["start_date"] = config_data["start_date"]
        dc_stage_payload["end_date"] = config_data["end_date"]

    user_name = "databrickadmin"
    if stage_name == "UC3_SIGMA_DATA":
        url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/sigma_data_pull_no_token/{user_name}?data_pull_job_id={new_data_pull_job_id}"
    else:
        url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/probe_data_pull_no_token/{user_name}?data_pull_job_id={new_data_pull_job_id}"
    response = requests.post(url, json=dc_stage_payload)
    if response.status_code == 200:
        print(f"Data pull triggered for {new_data_pull_job_id}.")
        print(f"Sigma Data Pull Response {response.text}")
    else:
        print("Failed to trigger data pull.")
        print(f"Failed to trigger data pull. status code:{response.status_code}")
        print(f"response - text : {response.text}")
        return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    # data pull
    response_json = response.json()
    data_pull_job_id = response_json.get("data_pull_job_id")
    stage_job_id = response_json.get("stage_job_id")
    user_name = response_json.get("user_name")
    print(f" ==== {data_pull_job_id} ======== {stage_job_id} ==== ")
    task_micron_data_pull(data_pull_job_id, stage_job_id, user_name, True)

    if pull_as_session != "True":
        # update config data in actual json
        config_data["status"] = "completed"
        config_data["next_start_date"] = config_data["end_date"]
        update_transit_json(config_data, config_file_json)

    # 8. Once polling is done, fetch the data pull results
    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={new_data_pull_job_id}&stage={stage_name}"
    response = requests.get(url)
    if response.status_code == 200:
        key_map = {"UC3_SIGMA_DATA": "uc3_sigma_data", "PROBE_DATA_PULL": "probe_data"}
        file_path = (
            response.json()
            .get("current_stage_results", {})
            .get(key_map[stage_name], {})
            .get("file_path", "")
        )
        print(f"File path: {file_path}")
    else:
        print("Failed to fetch data pull results.")
        print(f"Failed to fetch data pull results. status code:{response.status_code}")
        print(f"response - text : {response.text}")
        return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    if persist_session != "True":
        new_session_url = f"http://micron_apis_proxy:80/micron/data_catalog/sessions/{new_session_data['session_id']}"
        response = requests.delete(new_session_url, json=payload)
        if response.status_code == 204:
            print(f"Session got deleted Session ID: {new_session_data['session_id']}")
        else:
            print("Failed to create delete session.")
            print(
                f"Failed to create delete session. status code:{response.status_code}"
            )
            print(f"response - text : {response.text}")
            return pd.DataFrame()  # pd.DataFrame(),pd.DataFrame(),"", ""

    folder_path = Path(file_path)
    files = [
        file
        for file in folder_path.rglob("*")
        if file.is_file() and str(file).endswith(".parquet")
    ]
    print("fetched files..")
    summary_df = {}

    for i in files:
        print(f"filename: {i}")
        summary_df[i.name] = str(i)

    return pd.DataFrame([summary_df])
