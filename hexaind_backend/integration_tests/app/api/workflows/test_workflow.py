import requests
import pytest
import pathlib
import time


@pytest.mark.integration
def test_sample_workflow_via_server_admin(
    api_url, get_server_admin_form_login_response, test_project_id
):
    login_response = get_server_admin_form_login_response
    token = login_response.get("access_token")

    headers = {"Authorization": f"Bearer {token}"}

    # Upload a CSV file to create a new dataset
    name = "test_upload"
    description = "uploaded for testing"
    file_type = "CSV"
    upload_type = 'WORKFLOWS'
    workflow_id = '668ac62745ca9c5bddcd65d6'
    upload_url = f"{api_url}/v1/sites/1/projects/{test_project_id}/assets/dataset/tabular/upload?name={name}&upload_type={upload_type}&workflow_id={workflow_id}&description={description}&file_type={file_type}"
    cwd = pathlib.Path(str(__file__))
    file_path = str(cwd.parent.absolute() / "sample.csv")
    with open(file_path, "rb") as file:
        files = {"file": ("sample.csv", file, "text/csv")}
        response = requests.post(upload_url, headers=headers, files=files)
        response.raise_for_status()

    dataset_id = response.json().get("dataset_id")

    # Save workflow in master
    latest_wf = {
        "widgets": [
            {
                "_id": None,
                "on_success": ["454d0fff-135d-46d8-9c6b-d57ee0061bdc"],
                "on_failure": [],
                "on_complete": [],
                "inputs": [],
                "outputs": [
                    {
                        "urn": "19bb7799-ddda-40fb-a648-cb322d5d781d",
                        "type": "DATASET",
                        "name": "test-dataset_CSV_FILE-eFPr_Tabular",
                    }
                ],
                "name": "CSV_FILE-eFPr",
                "description": "DefaultWidgetDescription",
                "type": "DATA_COPY",
                "client_tags": {
                    "PositionX": 412,
                    "PositionY": 213.11111450195312,
                    "Width": 90,
                    "Height": 90,
                    "Color": "#1A7A7F",
                    "ClientType": "CSV_FILE",
                },
                "config": {
                    "version": "1.0",
                    "inputs": [],
                    "source": {
                        "type": "LOCAL",
                        "configuration": {"version": "1.0", "dataset_id": dataset_id},
                        "widget_type": "DATA_COPY",
                    },
                    "sink": {
                        "dataset_name": "csv_dataset",
                        "dataset_description": "csv_dataset_description",
                    },
                    "widget_type": "DATA_COPY",
                },
                "state": "IDLE",
                "use_gpu": False,
                "retry_interval_in_sec": 30,
                "retry_count": 30,
                "widget_id": "",
                "urn": "19bb7799-ddda-40fb-a648-cb322d5d781d",
            },
            {
                "_id": None,
                "on_success": [],
                "on_failure": [],
                "on_complete": [],
                "inputs": [
                    {
                        "urn": "19bb7799-ddda-40fb-a648-cb322d5d781d",
                        "type": "DATASET",
                        "name": "test-dataset_CSV_FILE-eFPr_Tabular",
                    }
                ],
                "outputs": [],
                "name": "SAVE-EKoP",
                "description": "DefaultWidgetDescription",
                "type": "SAVE",
                "client_tags": {
                    "PositionX": 595,
                    "PositionY": 98.11111450195312,
                    "Width": 90,
                    "Height": 90,
                    "Color": "#1A7A7F",
                    "ClientType": "SAVE",
                },
                "config": {
                    "version": "1.0",
                    "datasetConfig": [
                        {
                            "dataset_name": "test-dataset_CSV_FILE-eFPr_Tabular",
                            "destination_type": "HEXAIND_PLATFORM",
                            "destination_config": {
                                "destination_folder_path": "",
                                "save_options": "SAVE_AS",
                                "save_option_config": {
                                    "file_name": "test-dataset_SAVE-EKoP_457"
                                },
                                "file_Format": "CSV",
                            },
                        }
                    ],
                    "widget_type": "SAVE",
                },
                "state": "IDLE",
                "use_gpu": False,
                "retry_interval_in_sec": 30,
                "retry_count": 30,
                "widget_id": "",
                "urn": "454d0fff-135d-46d8-9c6b-d57ee0061bdc",
            },
        ],
        "start": ["19bb7799-ddda-40fb-a648-cb322d5d781d"],
        "end": ["454d0fff-135d-46d8-9c6b-d57ee0061bdc"],
        "user_id": "664c569824e6fd041c96c25b",
        "user_name": "TestUser",
        "client_tags": {
            "StartWidgetPosition": {"X": 220, "Y": 160},
            "EndWidgetPosition": {"X": 780, "Y": 160},
            "Arrows": [
                {
                    "start_urn": "START",
                    "start_connector_point_type": 2,
                    "end_urn": "19bb7799-ddda-40fb-a648-cb322d5d781d",
                    "end_connector_point_type": 1,
                    "arrow_type": 0,
                },
                {
                    "start_urn": "19bb7799-ddda-40fb-a648-cb322d5d781d",
                    "start_connector_point_type": 2,
                    "end_urn": "454d0fff-135d-46d8-9c6b-d57ee0061bdc",
                    "end_connector_point_type": 1,
                    "arrow_type": 0,
                },
                {
                    "start_urn": "454d0fff-135d-46d8-9c6b-d57ee0061bdc",
                    "start_connector_point_type": 2,
                    "end_urn": "END",
                    "end_connector_point_type": 1,
                    "arrow_type": 0,
                },
            ],
        },
    }

    save_wf_url = f"{api_url}/v1/sites/1/projects/{test_project_id}/sessions/668ac62745ca9c5bddcd65d8/workflow/save"
    response = requests.post(save_wf_url, headers=headers, json=latest_wf)
    response.raise_for_status()

    # Run master workflow
    run_wf_url = f"{api_url}/v1/sites/1/projects/{test_project_id}/sessions/668ac62745ca9c5bddcd65d8/workflow/run"
    response = requests.post(
        run_wf_url, headers=headers, json={"rerun_completed_widgets": True}
    )
    response.raise_for_status()

    success = False
    for count in range(30):
        time.sleep(10)
        status_url = f"{api_url}/v1/sites/1/projects/{test_project_id}/sessions/668ac62745ca9c5bddcd65d8/workflow/run/status"
        response = requests.get(status_url, headers=headers)
        response.raise_for_status()

        run_status = response.json().get("run_status")
        if run_status == "SUCCEEDED":
            success = True
            break
        elif run_status == "FAILED":
            break
    assert success
