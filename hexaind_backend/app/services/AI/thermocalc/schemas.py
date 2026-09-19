from pydantic import BaseModel, Field, conint
from typing import List, Optional, Literal
from enum import Enum
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType


class ScriptFile(BaseModel):
    file_path:str
    file_name:str

class JsonConfig(BaseModel):
    name:str = Field(...,description= 'json config')
    batch_size: conint(ge=1, le=100) = Field(..., description='Batch size between 1 and 100')

class ThermocalcGetResultApiParams(BaseModel):
    job_id:str =Field(...,description='job_id')
    start_idx :int =Field(...,description='start idx')
    end_idx :int =Field(...,description='start idx')


class ThermocalcConfig(BaseModel):

    version: Optional[str] = Field("1.0", description="Version of the widget")

    widget_type: Literal[WidgetType.THERMOCALC] # Field(default=WidgetType.THERMOCALC, description="config belongs to widget of type defined here", frozen=True)
    
    thermocalc_connector_id:str = Field(...,description='connector id')

    module_id: str = Field(...,description='user uploaded module id')

    input_features: List[str]=Field(...,description='Input columns')

    output_features: List[str]=Field(...,description='output columns')

class ThermocalcSubJobConfig(BaseModel):

    start: int = Field(..., description="batch starting index in the source file")

    end: int = Field(..., description="batch ending index in the source file")

    source_file_path: str = Field(..., description="input data file to feed into thermocalc")

class ThermocalcResponse(BaseModel):
    output_file_path:str = Field(...,description = "file path")

class ThermocalcResultAPIParams(BaseModel):
    job_id:str = Field(...,description = "file path")

class JobStatus(str, Enum):
    pending = "pending"
    running = "running"
    abort = "abort"
    deleted = "deleted"

class ThermocalcJobStatusConfig(BaseModel):
    job_id:str = Field(...,description="job_id")
    # job_status : JobStatus =Field(...,description="job status")



class UserCodeParams(BaseModel):
    code_path: str


class Features(BaseModel):
    input_features: List[str]=Field(...,description='Input columns')
    output_features: List[str]=Field(...,description='output columns')