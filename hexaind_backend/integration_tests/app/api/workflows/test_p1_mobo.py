import pathlib
import pytest
import pytest_mock
from integration_tests.app.utils.api_requests import *
from integration_tests.app.api.workflows.p1_mobo_wf import mobo_wf
import time

@pytest.mark.integration
def test_p1_with_mobo_widget_with_server_admin(
    api_url, get_server_admin_form_login_response, test_project_id
):
    # common config
    login_response = get_server_admin_form_login_response
    token = login_response.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    resources_dir = pathlib.Path(__file__).parent.parent.parent.parent / "resources"

    # modify workflow with latest data
    for widget in mobo_wf["widgets"]:
        if widget["type"] == "DATA_COPY":
            # Upload a CSV file to create a new dataset
            file_path = resources_dir / "mobo_p1/CSV_widget_tabular_data_30_datapoints.csv"
            csv_upload_request = TabularCSVUploadRequest(
                api_url,
                test_project_id,
                headers,
                file_path,
                name="CSV_widget_tabular_data_30_datapoints",
                description="uploaded for testing p1 mobo",
                upload_type='WORKFLOWS',
                workflow_id='66954ada4649cf54ee4c3daa'
            )
            csv_upload_response = csv_upload_request.execute()
            dataset_id = csv_upload_response.get("dataset_id")
            widget["config"]["source"]["configuration"]["dataset_id"] = dataset_id
        elif widget["type"] == "RESCALE":
            for file_details in widget["config"]["rescale_configs"]["files_detail"]:
                file_name = file_details['file_name']
                file_details = {
                    file_name: resources_dir / f"mobo_p1/rescale_widget/{file_name}"
                }
                multiple_file_upload_request = MultipleFileUploadRequest(
                    api_url,
                    test_project_id,
                    headers,
                    connector_id="66955348c109e706996ab008",
                    workflow_id="66954ada4649cf54ee4c3daa",
                    file_details=file_details,
                    folder_name="connection",
                    post_python="custom_driver.py,scaler.pkl,gp_scaling.pkl",
                )
                multiple_file_upload_response = multiple_file_upload_request.execute()
                response_dict = {
                    res["file_name"]: res["file_path"]
                    for res in multiple_file_upload_response["files"]
                }
                file_details["file_path"] = response_dict[file_name]

    # Save Workflow Request
    save_workflow_request = SaveWorkflowRequest(
        api_url,
        test_project_id,
        headers,
        workflow_data=mobo_wf,
        session_id="66954ab855badd3e7005b0b2",
    )
    save_workflow_request.execute()

    # Run Workflow Request
    run_workflow_request = RunWorkflowRequest(
        api_url,
        test_project_id,
        headers,
        session_id="66954ab855badd3e7005b0b2",
        rerun_completed_widgets=True,
    )
    run_workflow_request.execute(debug_mode=True)

    # Polling for workflow status
    success = False
    for _ in range(30):  # 450 sec ~ 7.5 mins
        time.sleep(15)
        workflow_status_request = WorkflowStatusRequest(
            api_url, test_project_id, headers, session_id="66954ab855badd3e7005b0b2"
        )
        workflow_status_response = workflow_status_request.execute(debug_mode=True)
        run_status = workflow_status_response.get("run_status")
        print(f"Polling status API: {run_status}")
        if run_status == "SUCCEEDED":
            success = True
            break
        elif run_status == "FAILED":
            break

    assert success
