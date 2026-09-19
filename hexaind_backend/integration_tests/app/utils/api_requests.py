import json
import requests


class APIRequest:
    def __init__(self, url, headers=None, data=None, files=None, request_type="POST"):
        self.url = url
        self.headers = headers
        self.data = data
        self.files = files
        self.request_type = request_type

    def execute(self, debug_mode: bool = False):
        if self.request_type == "POST":
            if self.files:
                response = requests.post(
                    self.url, headers=self.headers, data=self.data, files=self.files
                )
            else:
                response = requests.post(self.url, headers=self.headers, json=self.data)
        elif self.request_type == "GET":
            response = requests.get(self.url, headers=self.headers, params=self.data)
        elif self.request_type == "DELETE":
            response = requests.delete(self.url, headers=self.headers, data=self.data)
        else:
            raise ValueError(f"Unsupported request type: {self.request_type}")

        response.raise_for_status()
        result = response.json()
        if debug_mode:
            print(f"Response for request : {self.url}", result)
        return result


class TabularCSVUploadRequest(APIRequest):
    def __init__(self, api_url, project_id, headers, file_path, **kwargs):
        name = kwargs.get("name", "default_name")
        description = kwargs.get("description", "default_description")
        file_type = kwargs.get("file_type", "CSV")
        upload_type = kwargs.get("upload_type", "DATASETS")
        workflow_id = kwargs.get("workflow_id", "")

        upload_url = f"{api_url}/v1/sites/1/projects/{project_id}/assets/dataset/tabular/upload?name={name}&upload_type={upload_type}&workflow_id={workflow_id}&description={description}&file_type={file_type}"

        files = {"file": (file_path.name, open(file_path, "rb"), "text/csv")}

        super().__init__(upload_url, headers=headers, files=files, request_type="POST")


class MultipleFileUploadRequest(APIRequest):
    def __init__(
        self,
        api_url,
        project_id,
        headers,
        connector_id,
        workflow_id,
        file_details,
        **kwargs,
    ):
        upload_url = (
            f"{api_url}/v1/sites/1/projects/{project_id}/assets/multiple_file_uploads"
        )

        files = [
            ("files", (file_name, open(file_path, "rb")))
            for file_name, file_path in file_details.items()
        ]

        payload = {
            "folder_name": kwargs.get("folder_name", "default_folder"),
            "connectorId": connector_id,
            "workflowId": workflow_id,
            "post_python": kwargs.get(
                "post_python", "custom_driver.py,scaler.pkl,gp_scaling.pkl"
            ),
        }

        super().__init__(
            upload_url, headers=headers, data=payload, files=files, request_type="POST"
        )


class SaveWorkflowRequest(APIRequest):
    def __init__(self, api_url, project_id, headers, workflow_data, session_id):
        save_url = f"{api_url}/v1/sites/1/projects/{project_id}/sessions/{session_id}/workflow/save"
        super().__init__(
            save_url, headers=headers, data=workflow_data, request_type="POST"
        )


class RunWorkflowRequest(APIRequest):
    def __init__(
        self, api_url, project_id, headers, session_id, rerun_completed_widgets=True
    ):
        run_url = f"{api_url}/v1/sites/1/projects/{project_id}/sessions/{session_id}/workflow/run"
        payload = {"rerun_completed_widgets": rerun_completed_widgets}
        super().__init__(run_url, headers=headers, data=payload, request_type="POST")


class WorkflowStatusRequest(APIRequest):
    def __init__(self, api_url, project_id, headers, session_id):
        status_url = f"{api_url}/v1/sites/1/projects/{project_id}/sessions/{session_id}/workflow/run/status"
        super().__init__(status_url, headers=headers, request_type="GET")


class ModuleUploadRequest(APIRequest):
    def __init__(self, api_url, site_id, project_id, headers, file_path, **kwargs):
        name = kwargs.get("name", "default_name")
        description = kwargs.get("description", "default_description")
        # destination_folder = kwargs.get("destination_folder", "")

        upload_url = (
            f"{api_url}/v1/sites/{site_id}/projects/{project_id}/assets/module/upload"
            f"?name={name}&description={description}"
        )

        data = {}

        files = {
            "file": (file_path.name, open(file_path, "rb"))
        }

        super().__init__(
            upload_url, headers=headers, data=data, files=files, request_type="POST"
        )
