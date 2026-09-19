from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Literal
from pathlib import Path

from ..automl.schemas import ProblemType
from ..automl.automl_reg.schemas import EvaluationMetric

from app.services.workflows.designer.base_schemas import WidgetType

class InputScaling(str, Enum):

    Min_Max = "Min-Max"

    Standard = "Standard"

    Robust = "Robust"


class CATBoostHyperparameters(BaseModel):

    CAT: dict = Field(default_factory=dict, description="CAT Boost")
    

class AdditionalHyperparameterTuneKWargs(BaseModel):

    scheduler: str = Field(default="local", description="Launch locally")

    searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

    num_trials: int = Field(default=10, description="Number of trials to run")

    time_out: int = Field(default=600, description="Time limit in seconds for HPO")


class CATBoostConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the CATBoost")
    
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for catboost")

    widget_type: Literal[WidgetType.CATBOOST]
    
    input_cols: List[str] = Field(..., description="input features for CATBoost")
        
    output_col: str = Field(..., description="output feature for CATBoost")
    
    input_scaling: Optional[InputScaling] = Field(default="Standard", description="Input Scaling for CATBoost")

    split_ratio: int = Field(default= 80, description="test train split ratio for CATBoost")

    evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for CATBoost")

    catboost_hyperparameters: CATBoostHyperparameters = Field(..., description="CATBoost Hyperparameters")
    
    additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional CATBoost Hyperparameters")


class CATBoostResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for CATBoost")

    tabular_path: Optional[Path] = Field(None, description="tabular result of CATBoost widget")

    models_path: Optional[str] = Field(None, description="models result of CATBoost widget")


