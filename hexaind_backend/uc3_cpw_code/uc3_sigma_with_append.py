import json
import os
import re
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import requests
from dask.dataframe import concat, read_parquet

from app.workers.micron.worker import task_micron_data_pull


def is_valid_date(date_string):
    # True if the string is in valid YYYY-MM-DD format, False otherwise.
    try:
        # Try parsing the date string
        datetime.strptime(date_string, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def update_json_file(config_data, file_path: Path):
    with open(file_path, "w") as json_file:
        json.dump(config_data, json_file, indent=4)


def append_with_dask(old_parquet_path: str, new_parquet_path: str) -> str:
    """
    Updates an existing Parquet file by concatenating it with new data from another Parquet file using Dask.
    Parameters:
    old_parquet_path (str): Path to the existing Parquet file to update.
    new_parquet_path (str): Path to the new Parquet file with data to append.
    Returns:
    str: Path to the updated Parquet file.
    """
    if not old_parquet_path:
        print("No old file provided")
        return new_parquet_path
    if not Path(old_parquet_path).exists():
        print("old parquet path doesnt exists..inserting new data in old parquet path")
        new_data = read_parquet(new_parquet_path)
        new_data.to_parquet(old_parquet_path, write_index=False)
    else:
        old_data = read_parquet(old_parquet_path)
        print(
            f"Successfully read old parquet file from {old_parquet_path}. Shape: {old_data.shape}"
        )
        # Step 2: Read the new Parquet file
        new_data = read_parquet(new_parquet_path)
        print(
            f"Successfully read new parquet file from {new_parquet_path}. Shape: {new_data.shape}"
        )
        # Step 3: Concatenate the new data to the old data
        if old_data is not None:
            updated_data = concat([old_data, new_data], ignore_index=True)
        else:
            updated_data = new_data
        print(f"Updated data shape after concatenation: {updated_data.shape}")
        # Step 4: Write the updated data back to the old Parquet file
        updated_data.to_parquet(old_parquet_path, write_index=False)
        print(f"Successfully updated Parquet file at {old_parquet_path}")
    return old_parquet_path


def hexaind_custom_widget_function(
    sessions_df: pd.DataFrame,
    session_name: str,
    data_pull_prefrence: str,
    start_date: str,
    end_date: str,
) -> (pd.DataFrame, pd.DataFrame, pd.DataFrame):
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
    data_pull_prefrence : str
        Specifies the data pull behavior:
        - "Pull Data Only": Pull data without modifying or appending to an existing configuration.
        - "Append to Existing": Append pulled data to an existing configuration.
        - "Create as New": Create a new configuration with the pulled data.
        - "Pull & Append": Pull data and append to the current configuration.
    start_date : str
        The start date for the data pull, in the format 'YYYY-MM-DD'.
    end_date : str
        The end date for the data pull, in the format 'YYYY-MM-DD'.

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
    if data_pull_prefrence not in [
        "Pull Data Only",
        "Append to Existing",
        "Create as New",
        "Pull & Append",
    ]:  # if not existing config it will create its own [NO DATES REQUIRED]
        print(f"overrding data_pull_prefrence {data_pull_prefrence} to Pull Data Only")
        data_pull_prefrence = "Pull Data Only"

    persist_session = "False"
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

    # if stage_name not in ["UC3_SIGMA_DATA", "PROBE_DATA_PULL"]:
    stage_name = (
        "UC3_SIGMA_DATA"  # hard coding stage name as uc3 sigma here for this widget
    )
    # fetch start_date and end_date
    config_data = {}
    config_file_json = Path(results_dir).parent / f"cpw_{stage_name}.json"
    # update uc3_data_pull_config_intransit.json
    transit_config_file_path = (
        Path(results_dir).parent / f"cpw_{stage_name}_intransit.json"
    )
    print(f"Config Path: {config_file_json}")
    print(f"config intransit path : {transit_config_file_path}")
    if data_pull_prefrence != "Pull Data Only":
        config_file_json.parent.mkdir(parents=True, exist_ok=True)
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        # Append to Existing,Create as New,Pull & Append
        if data_pull_prefrence == "Append to Existing":
            # already some data got pulled..at some point
            if config_file_json.exists():
                with open(config_file_json, "r") as json_file:
                    loaded_data = json.load(json_file)
                print(f"Loaded json {loaded_data}")
                if loaded_data.get("status") != "completed":
                    print("current config pull is not yet done. {loaded_data}")
                    raise Exception(
                        "Previous run did not mark as completed, wait till previous run is done or use override option"
                    )
                start_date = loaded_data.get("next_start_date")
                end_date = current_date_str
            else:
                # file not exists and start_date is given
                if not is_valid_date(start_date):
                    print(
                        f"Selected Append to existing. however no file exists and start date {start_date} is not valid."
                    )
                    raise Exception(
                        f"Selected Append to existing. however no file exists and start date {start_date} is not valid."
                    )
                end_date = current_date_str
        elif data_pull_prefrence == "Create as New":
            if config_file_json.exists():  # store it in backup
                with open(config_file_json, "r") as json_file:
                    loaded_data = json.load(json_file)
                backup_file = Path(results_dir).parent / f"cpw_{stage_name}_backup.json"
                update_json_file(loaded_data, file_path=backup_file)
            if not is_valid_date(date_string=start_date):
                raise Exception(
                    f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
                )
            if not is_valid_date(date_string=end_date):
                raise Exception(
                    f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
                )
        elif data_pull_prefrence == "Pull & Append":
            if not is_valid_date(date_string=start_date):
                raise Exception(
                    f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
                )
            if not is_valid_date(date_string=end_date):
                raise Exception(
                    f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
                )
        config_data = {
            "start_date": start_date,
            "end_date": end_date,
        }
        config_data["next_start_date"] = config_data["end_date"]
        config_data["status"] = "inprogress"
        config_data["message"] = "fetched start date and end date"
        config_data["results_dir"] = (
            results_dir  # results dir contains p_{project_id} and r_{run_id}
        )
        update_json_file(config_data, file_path=transit_config_file_path)

    else:
        # verified valid start and end date
        if not is_valid_date(date_string=start_date):
            raise Exception(
                f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
            )
        if not is_valid_date(date_string=end_date):
            raise Exception(
                f"Start date expected for {data_pull_prefrence} to be in 'YYYY-MM-DD' format"
            )
        config_data = {
            "start_date": start_date,
            "end_date": end_date,
        }
        config_data["next_start_date"] = config_data["end_date"]
        config_data["status"] = "inprogress"
        config_data["message"] = "fetched start date and end date"
        config_data["results_dir"] = (
            results_dir  # results dir contains p_{project_id} and r_{run_id}
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
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""
    # 2. Fetch sigma DC payload (UC3_SIGMA_DATA)
    url = f"http://micron_apis_proxy:80/micron/data_catalog/fd/fd_data_pull_results?data_pull_job_id={data_pull_job_id}&stage={stage_name}"
    response = requests.get(url)
    if response.status_code == 200:
        dc_stage_payload = response.json().get("current_stage_inputs", {})
        print(f"Sigma DC Payload: {dc_stage_payload}")
    else:
        print(f"Failed to fetch Sigma DC Payload. status code:{response.status_code}")
        print(f"response - text : {response.text}")
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""
    # 3. Create new session using /data_catalog/create_session
    user_id = workflow_owner_id  # "6710b78c646947ee6e1c0831"
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
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""
    # 4. update db via API
    print(
        "--------------------------------------------------------------------------------------"
    )
    print(f"modifying start and end_dates with config_data, {config_data}")
    dc_stage_payload["start_date"] = config_data["start_date"]
    dc_stage_payload["end_date"] = config_data["end_date"]

    user_name = (
        f"databrickadmin_dc_wf_{current_run_id}"  # user in folder path for segregation
    )
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
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""
    # data pull
    response_json = response.json()
    data_pull_job_id = response_json.get("data_pull_job_id")
    stage_job_id = response_json.get("stage_job_id")
    user_name = response_json.get("user_name")
    print(f" ==== {data_pull_job_id} ======== {stage_job_id} ==== ")
    task_micron_data_pull(data_pull_job_id, stage_job_id, user_name, True)
    if data_pull_prefrence != "Pull Data Only":
        # update config data in actual json
        config_data["status"] = "completed"
        config_data["next_start_date"] = config_data["end_date"]
        config_data["dp_job_id"] = data_pull_job_id
        update_json_file(config_data, config_file_json)
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
        return (
            pd.DataFrame(),
            pd.DataFrame(),
            pd.DataFrame(),
        )  # pd.DataFrame(),pd.DataFrame(),"", ""
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
            return (
                pd.DataFrame(),
                pd.DataFrame(),
                pd.DataFrame(),
            )  # pd.DataFrame(),pd.DataFrame(),"", ""
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
    duplicate_summary_df = summary_df.copy()
    pdfiles = []
    for file_name in duplicate_summary_df:
        latest_pulled_file = duplicate_summary_df[file_name]
        if "pivot" in file_name:
            print(
                f"skipping this file for append.. as its pivoted..{latest_pulled_file}"
            )
            continue
        appended_file_name = f"appended_{stage_name}_{file_name}"
        data_appended_file_path = str(
            Path(results_dir).parent / f"appended_{stage_name}_{file_name}"
        )
        print("appending {file_name} files with out pivot in their names...")
        try:
            # ["Pull Data Only", "Append to Existing", "Create as New", "Pull & Append"]
            if (
                data_pull_prefrence == "Pull Data Only"
            ):  # we can send non appended file... appendeding not required
                print("Not appending for Pull Data Only")
                pdfiles.append(latest_pulled_file)
                continue
            if (
                data_pull_prefrence == "Create as New"
            ):  # old append file gets written to another and new is generate
                print("Create as New => need to append data to new file")
                backup_data_appended_file = str(
                    Path(results_dir).parent / f"old_appended_{stage_name}_{file_name}"
                )
                Path(backup_data_appended_file).unlink(missing_ok=True)
                if Path(data_appended_file_path).exists():
                    shutil.copyfile(data_appended_file_path, backup_data_appended_file)
                Path(data_appended_file_path).unlink(missing_ok=True)

            summary_df[appended_file_name] = append_with_dask(
                data_appended_file_path, latest_pulled_file
            )
            pdfiles.append(data_appended_file_path)
        except Exception as e:
            print(f"Got exception while truing to append file {e}")
            summary_df[appended_file_name] = str(e)
        # summary_df
    df1 = pd.DataFrame()
    df2 = pd.DataFrame()
    for f in pdfiles:
        try:
            if ("wafer" in f) and ("pivot" not in f):
                df1 = pd.read_parquet(f)
            if ("point" in f) and ("pivot" not in f):
                df2 = pd.read_parquet(f)
        except Exception as e:
            print(f"Found issue {e} while reading file {f}")
    return df1, df2, pd.DataFrame([summary_df])
