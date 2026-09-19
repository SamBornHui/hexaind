## USE SCHEMAS FROM `app.core.services.action.schemas` 

# from typing import List, Optional, Union
# from enum import Enum
# from pydantic import BaseModel, Field
# from datetime import datetime, timezone
# from app.services.workflows.designer.schemas import Widget
# from app.services.AI.thermocalc.schemas import ThermocalcSubJobConfig
# from app.core.schemas.action_result import (
#     ActionResultType,
#     FailureActionResult,
#     FloatActionResult,
#     IntegerActionResult,
#     JSONActionResult,
#     ListOffloatsActionResult,
#     ListOfIntegersActionResult,
#     ListOfStringsActionResult,
#     StringActionResult,
#     DictionaryActionResult
# )
# from app.services.data.assets.datasets.schemas import Dataset

# class ActionRunStatus(str, Enum):

#     IDLE = "IDLE"

#     SCHEDULED = "SCHEDULED"

#     RUNNING = "RUNNING"

#     FAILED = "FAILED"

#     PAUSED = "PAUSED"

#     STOPPED = "STOPPED"

#     SUCCEEDED = "SUCCEEDED"

# class CycleIntermediateResults(BaseModel):

#     invocation_num: int = Field(..., description= "no.of times the current widget executed with in cycle")

#     result_record_ids: List[str] = Field(..., description="intermediate result record id's")
# class CustomRunState(BaseModel):

#     total_invoke_count: int = Field(default=0, description= "no.of times the current widget executed with in cycle")

#     custom_state: dict = Field(default=dict(), description="store the meta data of action run which will be maintained/used across the cycle path")

#     cycle_intermediate_results: List[CycleIntermediateResults] = Field(default=[], description="intermediate results created between cycle runs")

# class Action(BaseModel):

#     id: Optional[str] = Field(default=None, description="Action Id", alias="_id")

#     version: Optional[str] = Field(default="1.0", description="Action Record schema version")

#     run_id: str = Field(..., description="RUN ID or API JOB id")

#     is_cycle: bool = Field(default=False, description="If the current widget is part of cycle then it will be true")

#     action_config: Widget = Field(..., description="Action Config")

#     sub_action_config: Optional[Union[ThermocalcSubJobConfig]] = Field(default=None, description="If the current action is producing any sub-actions, then we need config for child actions")

#     sub_action_ids: List[str] = Field(default=[], description="If the current action produces any child actions all id's of childs will be added here")

#     depends_on: List[str] = Field(default=[], description="URNs of the actions it depends on")

#     delete_on_complete: bool = Field(default=False, description="if widget execution stopped by client then this will become true") 

#     status: ActionRunStatus = Field(..., description="Action Running status")

#     result_ids: List[str] = Field(default=[], description="Results")

#     custom_run_state: Optional[CustomRunState] = Field(default=None, description="cycle state for widgets")

# class WidgetResultResponse(BaseModel):

#     result_type: ActionResultType

#     result_value: Union[
#         Dataset,
#         FailureActionResult,
#         StringActionResult,
#         JSONActionResult,
#         IntegerActionResult,
#         FloatActionResult,
#         ListOfStringsActionResult,
#         ListOfIntegersActionResult,
#         ListOffloatsActionResult,
#         DictionaryActionResult
#     ]

#     output_name: Optional[str] = Field(default=None, description="Output Name from widget")
