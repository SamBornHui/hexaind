import pathlib
import pytest
import pytest_mock
from integration_tests.app.utils.api_requests import *
from integration_tests.app.api.workflows.p2_wf import p2wf
import time

@pytest.mark.integration
def test_p2_with_server_admin(
    api_url, get_server_admin_form_login_response, test_project_id
):
    # common config
    login_response = get_server_admin_form_login_response
    token = login_response.get("access_token")
    headers = {"Authorization": f"Bearer {token}"}
    resources_dir = pathlib.Path(__file__).parent.parent.parent.parent / "resources"

    # modify workflow with latest data
    for widget in p2wf["widgets"]:
        if widget["type"] == "DATA_COPY":
            # Upload a CSV file to create a new dataset
            file_path = resources_dir / "p2/theromocalc_p2_wf_ingestion.csv"
            csv_upload_request = TabularCSVUploadRequest(
                api_url,
                test_project_id,
                headers,
                file_path,
                name="theromocalc_p2_wf_ingestion",
                description="uploaded for testing p2 mobo",
                upload_type='WORKFLOWS',
                workflow_id='6698b27440feaaf9aab0e23e'
            )
            csv_upload_response = csv_upload_request.execute()
            dataset_id = csv_upload_response.get("dataset_id")
            widget["config"]["source"]["configuration"]["dataset_id"] = dataset_id
        elif widget["type"] == "THERMOCALC":
            file_path = resources_dir / "p2/thermocalc_dummy_real_columns.py"
            module_upload_request = ModuleUploadRequest(
                api_url,
                1,
                test_project_id,
                headers,
                file_path,
                name="Thermocalc_dummy_real_columns",
                description="Used for P2 in Thermocalc widget",
            )
            widget['config']['module_id'] = module_upload_request.execute().get("module_id")

    # Save Workflow Request
    save_workflow_request = SaveWorkflowRequest(
        api_url,
        test_project_id,
        headers,
        workflow_data=p2wf,
        session_id="6698b26a84642e56af98a5e7",
    )
    save_workflow_request.execute()

    # Run Workflow Request
    # run_workflow_request = RunWorkflowRequest(
    #     api_url,
    #     test_project_id,
    #     headers,
    #     session_id="6698b26a84642e56af98a5e7",
    #     rerun_completed_widgets=True,
    # )
    # run_workflow_request.execute(debug_mode=True)
    #
    # # Polling for workflow status
    # success = False
    # for _ in range(30):  # 450 sec ~ 7.5 mins
    #     time.sleep(15)
    #     workflow_status_request = WorkflowStatusRequest(
    #         api_url, test_project_id, headers, session_id="6698b26a84642e56af98a5e7"
    #     )
    #     workflow_status_response = workflow_status_request.execute(debug_mode=True)
    #     run_status = workflow_status_response.get("run_status")
    #     print(f"Polling status API: {run_status}")
    #     if run_status == "SUCCEEDED":
    #         success = True
    #         break
    #     elif run_status == "FAILED":
    #         break
    #
    # assert success
