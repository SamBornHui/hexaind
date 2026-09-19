from functools import cached_property
from app.services.workflows.designer.schemas import *
from app.services.workflows.runner.schemas import RunStatusResponse, RunStatus
from app.core.services.action.schemas import WidgetResultResponse
from typing import Set
from pydantic import BaseModel, Field, TypeAdapter, ValidationError, model_validator

class SaveWorkflowRequest(BaseModel):

    # widgets: Union[List[Widget], List[dict]] = Field(default=[], description="List of Widgets in the workflow")
    widgets: List[dict] = Field(default=[], description="List of Widgets in the workflow")

    start: Union[List[str], str] = Field(default=[], description="single or multiple widgets at the begining of the workflow")

    end: Union[List[str], str] = Field(default=[], description="single or multiple actions at the end of the workflow")

    user_id: str = Field(..., description="current active user id")

    user_name: str = Field(..., description="current active user name")

    client_tags: Optional[dict] = Field(default={}, description="JSON object representing a list of properties used by the UX for the workflow.")

    @property
    def valid_widgets(self) -> List[Widget]:
        return self._valid_widgets
    
    @property
    def invalid_widgets(self) -> List[dict]:
        return self._invalid_widgets
    
    @property
    def validation_errors(self) -> List[dict]:
        return self._validation_errors
    
    @model_validator(mode="after")
    def check_widgets(self) -> "SaveWorkflowRequest":
        self._invalid_widgets: List[dict] = []
        self._valid_widgets: List[Widget] = []
        self._validation_errors: List[dict] = []
        for widget_data in self.widgets:
            try:
                self._valid_widgets.append(Widget.model_validate(widget_data))
            except ValidationError as e:
                self._invalid_widgets.append(widget_data)
                self._validation_errors.append({"urn": widget_data.get("urn", "unknown"), "errors": e.errors()})
        return self
            

    
class SaveWorkflowResponse(BaseModel):
    invalid_widgets: List[dict]

class SaveAsWorkflowRequest(BaseModel):

    name: str = Field(..., description="user defined name for workflow")

    version_tag: str = Field(..., description="user defined workflow version")

    description: str = Field(..., description="user defined workflow description")

    user_id: str = Field(..., description="current active user id")

    user_name: str = Field(..., description="current active user name")

class DuplicateWorkflowRequest(BaseModel):

    name: str = Field(..., description="user defined name for workflow")

    version_tag: str = Field(..., description="user defined workflow version")

    description: str = Field(..., description="user defined workflow description")

    user_id: str = Field(..., description="current active user id")

    user_name: str = Field(..., description="current active user name")
    
    workflow_id: str = Field(..., description="id of the workflow")
    
    is_template: Optional[bool] = Field(default=False, description="Indicates that version is the template")

class SaveAsWorkflowResponse(BaseModel):

    workflow_id: str = Field(..., description="workflow id")

class RunWorkflowInSession(BaseModel):

    rerun_completed_widgets : bool = Field(default=False, description="Re-run already completed widgets. only used when run_from_start=True")

class RunWidgetRequest(BaseModel):

    run_from_start: bool = Field(default=False, description="Flag to tell run from start")

    run_completed_widgets : bool = Field(default=False, description="Re-run already completed widgets. only used when run_from_start=True")

class WorkflowSessionRunStatus(RunStatusResponse):

    run_status: RunStatus = Field(..., description="Current session Run status")

class WorkflowSessionWidgetResults(WidgetResultResponse):
    pass

class WorkflowChanges(BaseModel):
    
    new_widgets: Set[str] = Field(default={}, description="newly addded widget urns")

    removed_connections: dict = Field(default={}, description="dictioanry of removed connections")

    deleted_widgets: Set[str] = Field(default={}, description="deleted widget urns")

    config_changed_widgets: Set[str] = Field(default={}, description="config changed widget urns")

    affected_widgets: Set[str] = Field(default={}, description="all widget urns got affected in new workflow")
