import pathlib
import pytest
import pytest_mock
from integration_tests.app.utils.api_requests import *
from integration_tests.app.api.workflows.p3_wf import p3_wf
import time

@pytest.mark.integration
def test_p3_with_server_admin(
    api_url, get_server_admin_form_login_response, test_project_id
):
    # common config
    login_response = get_server_admin_form_login_response
    token = login_response.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    resources_dir = pathlib.Path(__file__).parent.parent.parent.parent / "resources"

    # modify workflow with latest data
    for widget in p3_wf["widgets"]:
        if widget["type"] == "DATA_COPY":
            # Upload a CSV file to create a new dataset
            file_path = resources_dir / "p3/bced_v2_initial.csv"
            csv_upload_request = TabularCSVUploadRequest(
                api_url,
                test_project_id,
                headers,
                file_path,
                name="bced_v2_initial",
                description="uploaded for testing p3",
                upload_type='WORKFLOWS',
                workflow_id='669791eabeb903bc34831a7f'
            )
            csv_upload_response = csv_upload_request.execute()
            dataset_id = csv_upload_response.get("dataset_id")
            widget["config"]["source"]["configuration"]["dataset_id"] = dataset_id
        elif widget["type"] == "RESCALE":
            for file_details in widget["config"]["rescale_configs"]["files_detail"]:
                file_name = file_details['file_name']
                file_details = {
                    file_name: resources_dir / f"p3/{file_name}"
                }
                multiple_file_upload_request = MultipleFileUploadRequest(
                    api_url,
                    test_project_id,
                    headers,
                    connector_id="669795af9523d8940a1777c2",
                    workflow_id="669791eabeb903bc34831a7f",
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
        workflow_data=p3_wf,
        session_id="669791c1ea21b33ffc20b459",
    )
    save_workflow_request.execute()

    # Run Workflow Request
    run_workflow_request = RunWorkflowRequest(
        api_url,
        test_project_id,
        headers,
        session_id="669791c1ea21b33ffc20b459",
        rerun_completed_widgets=True,
    )
    run_workflow_request.execute(debug_mode=True)

    # Polling for workflow status 900 sec ~ 15 mins
    success = False
    for _ in range(30):  # 450 sec ~ 7.5 mins
        time.sleep(15)
        workflow_status_request = WorkflowStatusRequest(
            api_url, test_project_id, headers, session_id="669791c1ea21b33ffc20b459"
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
