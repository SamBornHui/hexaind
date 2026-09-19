from datetime import datetime
from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class ThermoCalcJobStatus(str, Enum):
    UNREGISTERED = "UNREGISTERED"
    REGISTERED = "REGISTERED"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"  # SUCCESS OR FAILED


class ThermoCalcJob(BaseModel):
    version: Optional[str] = Field(default="1.0", description="thermocalc jobs version")
    id: Optional[str] = Field(default=None, description="Id", alias="_id")

    module_path: str
    input_features: List[str] = Field(default=[], description='Input columns')
    output_features: List[str] = Field(default=[], description='output columns')
    connector_id: str = Field(default='', description="thermocalc_connector_id")

    expected_tasks: int = Field(default=0, description="expected number for this job")
    received_tasks: int = Field(default=0, description="received number for this job")
    processed_tasks: int = Field(default=0, description="processed number for this job")

    status: ThermoCalcJobStatus = Field(
        default=ThermoCalcJobStatus.UNREGISTERED,
        description="depends on expected,received,processed tasks",
    )

    results_file_path: Optional[str] = Field(
        default=None, description="file path where results are stored"
    )

    # tracking info
    run_id: str
    action_id: str
    last_modified_at: Optional[datetime] = Field(
        default=None, description="last updated at time for this record"
    )
    created_at: datetime


class ThermoCalcJobRegisterationRequest(BaseModel):
    expected_tasks: int = Field(default=0, description="expected number for this job")
    input_features: List[str] = Field(default=[], description='Input columns')
    output_features: List[str] = Field(default=[], description='output columns')
    connector_id: str = Field(default=None,description="thermocalc_connector_id")
