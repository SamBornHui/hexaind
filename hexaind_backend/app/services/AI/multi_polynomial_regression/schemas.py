from pydantic import BaseModel, Field, conint, validator
from enum import Enum
from typing import List, Union, Dict, Optional, Literal
from ..automl.schemas import ProblemType
from ..automl.automl_reg.schemas import EvaluationMetric
from app.services.workflows.designer.base_schemas import WidgetType
from pathlib import Path

class SplitType(str, Enum):
    Random = "Random"
    Sequential = "Sequential"

class InputScalingType(str, Enum):
    Standard = "Standard"
    Min_Max  = "Min_Max"
    Robust = "Robust"

class CategoricalEncodingType(str, Enum):
    One_hot = "One_hot"
    Mean = "Mean"
class FeatureDegree(BaseModel):
    feature_name : str 
    feature_value : conint(ge=0, le=10) = Field(default=2, description="Feature degess")

class MPRConfig(BaseModel):
    version: Optional[str] = Field(default="1.0", description="Version of the MPR") 
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for MPR")
    widget_type: Literal[WidgetType.MPR]
    input_cols : List[str] = Field(... , description="feature column for multi polynomial regression" )
    output_col : str =  Field(... , description="target column for multi polynomial regression" )
    split_ratio : conint(ge=0, lt=100) = Field(default=20 , description="split ratio" )
    split_type : Union[SplitType,None ]= Field(..., description="split type for data")
    input_scaling : Union[InputScalingType, None]  = Field(..., description="input scaling type")
    polynomial_degree:  Union[conint(ge=0, le=10), None] = Field(..., description="Positive integer or list of integers ranging from 0 to 10")
    polynomial_degree_feature: Union[List[FeatureDegree], None] =  Field(..., description="Polynomial degree for features")
    cross_validation_folds: Union[conint(ge=2, le=100), None] = Field(..., description="Cross validation folds")
    random_state: Union[conint(ge=0, le=100), None] = Field(..., description="random state")
    categorical_encoding: Union[CategoricalEncodingType, None] = Field(..., description="categorical encoding")

@validator('Polynomial_degree')
def check_Polynomial_degree(cls, v, values):
    # If custom_value is a list, ensure its length matches the number of input features
    if isinstance(v, list):
        input_cols = values.get('input_cols')
        if input_cols and len(v) != len(input_cols):
            raise ValueError(f'The length of custom_value list must be equal to the number of input_columns (expected {len(input_cols)}, got {len(v)}).')
    return v



class MPRResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for linear regression")

    tabular_path: Optional[Path] = Field(None, description="tabular result of linear regression widget")

    models_path: Optional[str] = Field(None, description="models result of MPR widget")
