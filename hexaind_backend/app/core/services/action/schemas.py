from typing import Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field, model_validator
from datetime import datetime, timezone
from app.services.workflows.designer.schemas import Widget
from app.core.schemas.action_result import ActionResultType, FailureActionResult, JSONActionResult, DictionaryActionResult, StringActionResult, IntegerActionResult, FloatActionResult, ListOffloatsActionResult, ListOfIntegersActionResult, ListOfStringsActionResult, FileActionResult
from app.services.data.assets.datasets.schemas import Dataset
from app.services.AI.thermocalc.schemas import ThermocalcSubJobConfig

class ActionRunStatus(str, Enum):

    IDLE = "IDLE"

    SCHEDULED = "SCHEDULED"

    RUNNING = "RUNNING"

    FAILED = "FAILED"

    PAUSED = "PAUSED"

    STOPPED = "STOPPED"

    SUCCEEDED = "SUCCEEDED"

class CycleIntermediateResults(BaseModel):

    invocation_num: int = Field(..., description= "no.of times the current widget executed with in cycle")

    result_record_ids: List[str] = Field(..., description="intermediate result record id's")
class CustomRunState(BaseModel):

    total_invoke_count: int = Field(default=0, description= "no.of times the current widget executed with in cycle")

    custom_state: dict = Field(default=dict(), description="store the meta data of action run which will be maintained/used across the cycle path")

    cycle_intermediate_results: List[CycleIntermediateResults] = Field(default=[], description="intermediate results created between cycle runs")

class Action(BaseModel):

    id: Optional[str] = Field(default=None, description="Action Id", alias="_id")

    version: Optional[str] = Field(default="1.0", description="Action Record schema version")

    run_id: str = Field(..., description="RUN ID or API JOB id")

    is_cycle: bool = Field(default=False, description="If the current widget is part of cycle then it will be true")

    action_config: Widget = Field(..., description="Action Config")

    sub_action_config: Optional[Union[ThermocalcSubJobConfig]] = Field(default=None, description="If the current action is producing any sub-actions, then we need config for child actions")

    sub_action_ids: List[str] = Field(default=[], description="If the current action produces any child actions all id's of childs will be added here")

    processed_sub_action_ids: List[str] = Field(default=[], description="From all sub-actions created, If processing is done on the sub-action that record id will be added here. To track which all processes which are not.")

    depends_on: List[str] = Field(default=[], description="URNs of the actions it depends on")

    delete_on_complete: bool = Field(default=False, description="if widget execution stopped by client then this will become true") 

    status: ActionRunStatus = Field(..., description="Action Running status")

    result_ids: List[str] = Field(default=[], description="Results")

    celery_task_id: Optional[str] = Field(default=None, description="once we submitted this job, we will get back the unique id from celery, this will be useful to stop the workflow")

    custom_run_state: Optional[CustomRunState] = Field(default=None, description="cycle state for widgets")

class WidgetResultResponse(BaseModel):

    result_type: ActionResultType

    result_value: Union[Dataset, 
                        FailureActionResult,
                        IntegerActionResult, 
                        FloatActionResult,
                        StringActionResult,   
                        ListOfIntegersActionResult,
                        ListOffloatsActionResult,
                        ListOfStringsActionResult,                      
                        JSONActionResult,
                        DictionaryActionResult,
                        FileActionResult]

    output_name: Optional[str] = Field(default=None, description="Output Name from widget")
    final_result: Optional[Any] = None

    @model_validator(mode="after")
    def generate_final_result(self) -> "WidgetResultResponse":
        match self.result_value:
            case Dataset(id=id):
                self.final_result = id
            case FailureActionResult(error_description=error_description):
                self.final_result=error_description
            case IntegerActionResult(integer_value=integer_value):
                self.final_result=integer_value
            case FloatActionResult(float_value=float_value):
                self.final_result = float_value
            case StringActionResult(string_value=string_value):
                self.final_result = string_value
            case ListOfIntegersActionResult(integers_list_value=integers_list_value):
                self.final_result=integers_list_value
            case ListOffloatsActionResult(floats_list_value=floats_list_value):
                self.final_result=floats_list_value
            case ListOfStringsActionResult(strings_list_value=strings_list_value):
                self.final_result=strings_list_value
            case JSONActionResult(json_value=json_value):
                self.final_result=json_value
            case DictionaryActionResult(dict_value=dict_value):
                self.final_result=dict_value
            case FileActionResult(file_path_value=file_path_value):
                self.final_result=file_path_value
            case _:
                self.final_result=None
            
        return self
            
                

