from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Union, Literal
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType
from .automl_cls.schemas import AutoMLConfigCls
from .automl_reg.schemas import AutoMLConfigReg


class AdditionalHyperparameterTuneKWargs(BaseModel):

    scheduler: str = Field(default="local", description="Launch locally")

    searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

    num_trials: int = Field(default=10, description="Number of trials to run")

    time_out: int = Field(default=600, description="Time limit in seconds for HPO")


class ProblemType(str, Enum):

    regression = "regression"

    classification = "classification"


class AutoMLConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the AutoML")

    widget_type: Literal[WidgetType.AUTOML]

    problem_type: ProblemType = Field(..., description="problem type for AutoML")
    
    input_cols: List[str] = Field(..., description="input features for AutoML")
        
    output_col: str = Field(..., description="output feature for AutoML")
    
    split_ratio: int = Field(default= 80, description="test train split ratio for AutoML")
    
    additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional AutoML Hyperparameters")

    automl_config: Union[AutoMLConfigCls, AutoMLConfigReg] = Field(..., description="AutoML Config")


class AutoMLResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for AutoML")

    tabular_path: Optional[Path] = Field(None, description="tabular result of AutoML widget")

    models_path: Optional[str] = Field(None, description="models result of CATBoost widget")

