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

class KNNHyperparameters(BaseModel):

    KNN: dict = Field(default_factory=dict, description="K Nearest Neighores")
    

class AdditionalHyperparameterTuneKWargs(BaseModel):

    scheduler: str = Field(default="local", description="Launch locally")

    searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

    num_trials: int = Field(default=10, description="Number of trials to run")

    time_out: int = Field(default=600, description="Time limit in seconds for HPO")


class KNNConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the KNN")
    
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for KNN")

    widget_type: Literal[WidgetType.KNEIGHBORS]
    
    input_cols: List[str] = Field(..., description="input features for KNN")
        
    output_col: str = Field(..., description="output feature for KNN")
    
    input_scaling: Optional[InputScaling] = Field(default="Standard", description="Input Scaling for KNN")

    split_ratio: int = Field(default= 80, description="test train split ratio for KNN")

    evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for KNN")

    knn_hyperparameters: KNNHyperparameters = Field(..., description="KNN Hyperparameters")
    
    additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional KNN Hyperparameters")


class KNNResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for KNN")

    tabular_path: Optional[Path] = Field(None, description="tabular result of KNN widget")

    models_path: Optional[str] = Field(None, description="models result of KNN widget")