from typing import List, Optional, Union, Any
from enum import Enum
from pydantic import BaseModel, Field
from app.services.workflows.designer.service import Workflow
from app.core.services.action.schemas import ActionRunStatus
from datetime import datetime, timezone

class RunState(str, Enum):

    START = "START"

    STOP = "STOP"

    PAUSE = "PAUSE"

class RunActionsConfig(BaseModel):

    urn: str

    action_id: str

class RunSource(str, Enum):

    API = "API"

    WORKFLOW = "WORKFLOW"

    SCHEDULE = "SCHEDULE"

class RunStatus(str, Enum):        
    
    IDLE = 'IDLE'

    RUNNING = 'RUNNING'
    
    PAUSED = 'PAUSED'
    
    FAILED = 'FAILED'
    
    SUCCEEDED = 'SUCCEEDED'

class Run(BaseModel):

    id: Optional[str] = Field(default=None, description="Runs Id", alias="_id")

    interactive_mode: bool = Field(default=False, description="represents whether run created for actual workflow or interactive session")

    is_single_widget_run: bool = Field(default=False, description="represents whether run is specially widget or overall workflow")

    schedule_to_delete_widgets: List[RunActionsConfig] = Field(default=[], description="list of widgets to be deleted once they are stopped by client")

    name: str = Field(default="", description="Workflow name")

    description: str = Field(default="", description="Workflow description")

    run_source: RunSource = Field(default=RunSource.WORKFLOW, description="RUN triggered via API or Workflow")

    run_source_details: Optional[Any] = Field(default=None, description="stores related info info")

    run_state: RunState = Field(default=RunState.START, description="RunState of Workflow")

    run_status: RunStatus = Field(default=RunStatus.IDLE, description="RunStatus of workflow")

    actions: List[RunActionsConfig] = Field(default=[], description="list of actions associated with run")

    owner_id: str = Field(default=None, description="ID of the user who created the run")
    
    owner_name: str = Field(default=None, description="Name of the user who created the run")

    created_at: datetime = Field(default=None, description="Created Date and Time UTC format")

    recent_run_created_at: Optional[datetime]= Field(default=None, description="This field is used for to identify the recent run of the master copy (the workflow in session), since we are mainting the same run id for multiple runs")

    last_modified_by_id: str = Field(default=None, description="ID of the user who recently modified the workflow")

    last_modified_at: datetime = Field(default=None, description="Created Date and Time UTC format")

    project_id: str = Field(default=None, description="Project ID")

    site_id: str = Field(default=None, description="Project ID")

    workflow_id: Optional[str] = Field(default=None, description="Workflow Id")

    version: Optional[str] = Field(default="1.0", description="Version of the workflow")

class GetAllRunsResponse(BaseModel):

    runs: List[Run]

    total_count: int


class RunResponse(BaseModel):

    run_id: str

class RunWidgetStatus(BaseModel):

    urn: str

    status: ActionRunStatus


class RunStatusResponse(BaseModel):

    workflow: Workflow

    widgets_status: List[RunWidgetStatus]

    is_single_widget_run: Optional[bool] = False


class RunSummaryResponse(BaseModel):
    run: Run
    widgets_status: List[RunWidgetStatus]
    failed_widget_urn: Optional[str] = None
    total_time: Optional[str] = None # last_modified_at - created at times

class WorkflowCopy(BaseModel):

    run_id: str
    workflow: dict