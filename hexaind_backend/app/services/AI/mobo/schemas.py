from enum import Enum
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Union, Optional, Literal

from app.services.workflows.designer.base_schemas import WidgetType



class FileDetails(BaseModel):
    
    file_name: str
    
    file_path: Path
    
class MOBOExperimentType(str, Enum):

    OPTIMIZATION = "OPTIMIZATION"

    ACTIVE_LEARNING = "ACTIVE_LEARNING"

class MOBOExperimentOutputVariablesObjectives(str, Enum):

    MINIMUM = "MINIMUM"

    MAXIMUM = "MAXIMUM"

class MOBORunState(BaseModel):

    source_file_path: str = Field(..., description="input file path")

    master_source_csv_file_path: str = Field(..., description="input file with additional columns created by AX package")

    master_source_json_file_path: str = Field(..., description="input file with additional fields created AX package")

    experiment_folder_location: str = Field(..., description="MOBO experiment folder path for storing all records required for MOBO optimization flow")


class FeatureDetail(BaseModel):
    
    name: str
    
    dataType: str
    
    selected: bool
    
    input: Optional[bool]
    
    output: Optional[bool]


class MOBOConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the workflow")

    widget_type: Union[Literal[WidgetType.MOBO], Literal[WidgetType.ACTIVE_LEARNING]  ]

    experiment_type: MOBOExperimentType = Field(default=MOBOExperimentType.OPTIMIZATION, description="mobo algorithm type")

    features_detail:  Optional[List[FeatureDetail]] = Field(None, description="features detail of selected dataset ")
    
    input_variables: List[str] = Field(..., description="input features for mobo")
    
    input_variables_constraints: List[List[float]] = Field(..., description="filters on input features")
    
    output_variables: List[str] = Field(..., description="output features for mobo")
    
    output_variables_objectives: List[MOBOExperimentOutputVariablesObjectives] = Field(..., description="user defined mobo experiment name ")
    
    output_variables_thresholds: List[float] = Field(..., description="thresholds for the output features, this is more like boundary for recommendations")
    
    num_iterations: int = Field(..., description="number of times to run the experiment or target no.of batches")
    
    batch_size: int = Field(..., description="specifies no.of recommendations will be generated in one batch")

    constraints_module_id: Optional[str] = Field(default=None, description="module id for the user uploaded mobo recommendations validation scripts")

    outcome_constraints_active: Optional[bool] = Field(default=False, description="Outcome constraints tog ")

    outcome_constraints_variable: Optional[str]= Field(default=None, description="user defined mobo experiment name ")

    outcome_constraints_operator: Optional[str] = Field(default=None, description="user defined mobo experiment name ")

    outcome_constaints_inputvalue: Optional[int] = Field(default=None, description="user defined mobo experiment name ")

    dataset: Optional[str] = Field(default=None, description="dataset path of previous run for mobo")


class MOBOResponse(BaseModel):
    
    tabular_path: Optional[Path] = Field(None, description="tabular result of mobo widget")

    terminate: Optional[bool] = Field(None, description="termination flag detail mobo widget")

    exception_detail: Optional[str] = Field(None, description="Exception detail for the mobo widget")



class CreateFolderResponse(BaseModel):
    
    folder_path: str
