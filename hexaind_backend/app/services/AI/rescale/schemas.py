from pydantic import BaseModel, Field
from typing import Optional, List, Union, Literal, Dict
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType

class RescaleAuth(BaseModel):
    
    token: Optional[str] = Field(default=None, description="token Id")


class HardwareConfig(BaseModel):
    
    coreType: str
    
    slots: int
    
    coresPerSlot: int
    
    walltime: int
    
    type: Optional[str] = Field(default=None)

class AnalysisConfig(BaseModel):
    
    version: str
    
    code: str

class ENVVarsConfig(BaseModel):
    
    DSLS_LICENSE_FILE: Optional[str] = Field(default=None)
    
    LSTC_LICENSE_SERVER: Optional[str] = Field(default=None)

class SoftwareConfig(BaseModel):
    
    hardware: HardwareConfig
    
    analysis: AnalysisConfig
    
    reusable_job_file: str
    
    dynamic_job_file: str
    
    pre_python: Optional[str] = Field(default=None)
    
    post_python: Optional[str] = Field(default=None)
    
    command: str
    
    output_file: str
    
    visualize_files: Optional[List[str]] = Field(default=[])
    
    envVars: ENVVarsConfig
    
    onDemandLicenseSeller: Optional[str] = Field(default=None)


class FilesDetail(BaseModel):
    
    file_name: str
    
    file_path: Union[Path, str]
    
    upload_rescale: bool
    
    rescale_id: Optional[str] = Field(default=None)


class RescaleConnTemplate(BaseModel):
    
    name: str
    
    test_mode: bool
    
    run_job: bool
    
    batch_mode: Optional[bool] = Field(default=False)  ### bydefault False
    
    max_parallel_jobs: Optional[int] = Field(default=1)  ### bydefault len(trials) or 1
    
    input_variables: Optional[List[str]] = Field(default=[])
    
    output_variables: Optional[List[str]] = Field(default=[])
    
    software: SoftwareConfig
    
    files_detail: List[FilesDetail]

class RescaleConfig(BaseModel):

    widget_type: Literal[WidgetType.RESCALE]

    rescale_connector_id: str = Field(..., description="Rescale connection id")

    rescale_configs: RescaleConnTemplate
    
    version: Optional[str] = Field("1.0", description="Version of the widget")
    
    input_file_name: Optional[str] = Field(default=None)



class RescaleResponse(BaseModel):
    
    tabular_path: Optional[Path] = Field(None, description="Tabular file path for the rescale widget")

    exception_detail: Optional[str] = Field(None, description="Exception detail for the rescale widget")
    
    
class RescaleRunningINFO(BaseModel):
    
    run_id: str 
    
    workflow_id: str
    
    user_id: str
    
    project_id: str
    
    running_data: Optional[List[Dict]] = Field(default=[])
    
    stop_pending: Optional[bool] = Field(default=False)
    
    stop_all: Optional[bool] = Field(default=False)
        

class StopRescale(BaseModel):
    
    run_id: Optional[str] = Field(default=None)
    
    stop_all: bool
    
    stop_pending: bool
    
    user_id: str
        