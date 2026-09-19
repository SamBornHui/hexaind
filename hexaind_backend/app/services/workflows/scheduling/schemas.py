from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field, field_validator
from typing import List, Any, Optional, Union, Literal

from app.services.workflows.runner.schemas import RunStatus


class ScheduleType(str, Enum):
    ONCE = "ONCE"
    RECURRING = "RECURRING"

class RepeatType(str, Enum):
    NONE = "None"
    DAYS = "Days"
    WEEKS = "Weeks"
    MONTHS = "Months"
    YEARS = "Years"

class CronWeekDays(int, Enum):
    SUN = 0
    MON = 1
    TUE = 2
    WED = 3
    THU = 4
    FRI = 5
    SAT = 6

class ScheduleStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    RUNNING = "RUNNING"
    FAILED = "FAILED"
    CANCELED = "CANCELED"
    COMPLETED = "COMPLETED"
    UNKNOWN = "UNKNOWN"  # used of ease of implementation


class SchedulingEventType(str, Enum):
    WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF = "WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF"
    ANY_FILE_IN_FOLDER_TRIGGER_WF = "ANY_FILE_IN_FOLDER_TRIGGER_WF"


class WorkflowTriggerBasedConfig(BaseModel):
    # add version here
    workflow_id: str
    event_type: Literal[SchedulingEventType.WF_COMPLETION_VIA_SCHEDULE_TRIGGER_WF]
    condition: RunStatus

    @field_validator("condition")
    @classmethod
    def allow_only_specific_run_status(cls, status: RunStatus) -> RunStatus:
        if status not in [RunStatus.SUCCEEDED, RunStatus.FAILED]:
            raise ValueError("Currently only succeeded and failed states are allowing.")
        return status


class FileTriggerBasedConfig(BaseModel):
    folder_path: str
    event_type: Literal[SchedulingEventType.ANY_FILE_IN_FOLDER_TRIGGER_WF]
    file_name: Optional[str] = Field(default=None)


class EventBasedConfig(BaseModel):
    event_type: SchedulingEventType
    config: Union[WorkflowTriggerBasedConfig, FileTriggerBasedConfig]


class WFSchedule(BaseModel):

    dag_id: Optional[str] = Field(default=None, description="dag Id", alias="_id")
    name: str = Field(default="", description="Workflow name")
    # dag_id: str = Field(default=None, description="DAG ID")
    project_id: str = Field(default=None, description="Project ID")
    site_id: str = Field(default=None, description="Site ID")
    workflow_id: str = Field(default=None, description="Workflow Id")
    version: Optional[str] = Field(default="1.0", description="Version of the Schedule")
    start_date: str = Field(default=None)
    end_date: str = Field(default=None)
    scheduled_interval: str = Field(default=None)
    schedule_interval_metadata: Optional[Any] = Field(default=None)
    schedule_type: ScheduleType = Field(default=ScheduleType.ONCE)
    event_based_config: Optional[EventBasedConfig] = Field(default=None)
    is_active: bool = Field(default=False)
    dag_file_path: str = ""
    created_by_id: str = Field(
        default=None, description="ID of the user who created the run"
    )
    created_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )
    last_modified_by_id: str = Field(
        default=None, description="ID of the user who recently modified the workflow"
    )
    last_modified_at: datetime = Field(
        default=None, description="Created Date and Time UTC format"
    )
    repeat_type: Optional[RepeatType] = Field(default=RepeatType.NONE)
    repeat_value: Optional[int] = Field(default=1)
    cron_week_days: Optional[List[CronWeekDays]] = Field(default=[1])
    job_trigger_dt_times: Optional[List[str]] = Field(default=[])


class WfScheduleInfo(WFSchedule):
    created_by_name: Optional[str] = "Unknown"
    run_id: str
    run_status: str
    run_created_at: Optional[str] = None
    workflow_name: str
    workflow_version: str
    schedule_status: Optional[ScheduleStatus] = ScheduleStatus.SCHEDULED
    next_run: Optional[str] = None


class ScheduleRequest(BaseModel):
    name: str
    workflow_id: str
    start_date: str = Field(
        default="2024-01-01 00:00:00", example="2023-01-01 00:00:00"
    )
    end_date: str = Field(default="2024-12-31 00:00:00", example="2023-01-01 00:00:00")
    schedule_type: ScheduleType = Field(default=ScheduleType.ONCE)
    schedule_interval_metadata: Optional[Any] = Field(default=None)
    schedule_interval: str = None
    event_based_config: Optional[EventBasedConfig] = Field(default=None)
    tags: List[str] = Field(default=[])
    repeat_type: Optional[RepeatType] = Field(default=RepeatType.NONE)
    repeat_value: Optional[int] = Field(default=1)
    cron_week_days: Optional[List[CronWeekDays]] = Field(default=[1])


class UpdateScheduleRequest(BaseModel):
    schedule_id: str
    name: str
    workflow_id: str
    start_date: str = Field(
        default="2024-01-01 00:00:00", example="2023-01-01 00:00:00"
    )
    end_date: str = Field(default="2024-12-31 00:00:00", example="2023-01-01 00:00:00")
    schedule_type: ScheduleType = Field(default=ScheduleType.ONCE)
    schedule_interval: str = None
    event_based_config: Optional[EventBasedConfig] = Field(default=None)
    schedule_interval_metadata: Optional[Any] = Field(default=None)
    tags: List[str] = Field(default=[])
    repeat_type: Optional[RepeatType] = Field(default=RepeatType.NONE)
    repeat_value: Optional[int] = Field(default=1)
    cron_week_days: Optional[List[CronWeekDays]] = Field(default=[1])


class ScheduleResponse(BaseModel):
    schedule_id: str
    succeeded: bool


class PauseRequest(BaseModel):
    schedule_id: str
    is_paused: bool


class PauseResponse(BaseModel):
    succeeded: bool
    message: str


class DeleteRequest(BaseModel):
    schedule_id: str


class DeleteResponse(BaseModel):
    succeeded: bool
    message: str


class GetAllSchedulesRequest(BaseModel):
    get_details: bool = True


class GetAllSchedulesResponse(BaseModel):
    succeeded: bool = True
    message: str = ""
    total_count: int
    schedules: Optional[List[Union[WFSchedule | WfScheduleInfo]]] = None
