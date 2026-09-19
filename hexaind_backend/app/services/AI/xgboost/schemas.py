from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Literal, Union
from pathlib import Path

from ..automl.schemas import ProblemType

from app.services.workflows.designer.base_schemas import WidgetType


class InputScaling(str, Enum):

    Min_Max = "Min-Max"

    Standard = "Standard"

    Robust = "Robust"
    

class SplitType(str, Enum):
    
    Random = "Random"
    
    Sequential = "Sequential"
    

class EncodingType(str, Enum):
        
    Onehot = "Onehot"
    
    Mean = "Mean"


class XGBoostParams(BaseModel):
    
    input_scaling: Union[InputScaling, None] = Field(InputScaling.Standard, description="Input Scaling for XGBoost")
    
    split_type: Union[SplitType, None ] = Field(..., description="Split Type for XGBoost")

    split_ratio: int = Field(..., description="test train split ratio for XGBoost")
    
    k_fold: Union[int, None] = Field(..., description="k fold for XGBoost")
    
    n_estimators: int = Field(..., description="n_estimators for XGBoost")
    
    max_depth: int = Field(..., description="max_depth for XGBoost")
    
    subsample: float = Field(..., description="subsample for XGBoost")
    
    learning_rate: float = Field(..., description="learning_rate for XGBoost")
    
    colsample_bytree: float = Field(..., description="colsample_bytree for XGBoost")
        
    colsample_bylevel: float = Field(..., description="colsample_bylevel for XGBoost")
    
    colsample_bynode: float = Field(..., description="colsample_bynode for XGBoost")
    
    num_parallel_tree: int = Field(..., description="num_parallel_tree for XGBoost")
    
    encoding_type: Union[EncodingType, None] = Field(..., description="Encoding Type for XGBoost")
    
    split_random_state: Union[int, None] = Field(default=None, description="split_random_state for XGBoost")


class XGBoostConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the XGBoost")

    widget_type: Literal[WidgetType.XGBOOST]
    
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for XGBoost")
    
    input_cols: List[str] = Field(..., description="input features for XGBoost")
        
    output_col: str = Field(..., description="output feature for XGBoost")
    
    hyper_params: XGBoostParams = Field(..., description="XGBoost Hyperparameters")


class XGBoostResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for XGBoost")

    tabular_path: Optional[Path] = Field(None, description="tabular result of XGBoost widget")

    models_path: Optional[str] = Field(None, description="models result of XGBoost widget")





#### old schema
# class XGBoostHyperparameters(BaseModel):

#     XGB: dict = Field(default_factory=dict, description="XG Boost")
    

# class AdditionalHyperparameterTuneKWargs(BaseModel):

#     scheduler: str = Field(default="local", description="Launch locally")

#     searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

#     num_trials: int = Field(default=10, description="Number of trials to run")

#     time_out: int = Field(default=600, description="Time limit in seconds for HPO")


# class XGBoostConfig(BaseModel):

#     version: Optional[str] = Field(default="1.0", description="Version of the XGBoost")

#     widget_type: Literal[WidgetType.XGBOOST]
    
#     problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for XGBoost")
    
#     input_cols: List[str] = Field(..., description="input features for XGBoost")
        
#     output_col: str = Field(..., description="output feature for XGBoost")
    
#     input_scaling: Optional[InputScaling] = Field(default="Standard", description="Input Scaling for XGBoost")

#     split_ratio: int = Field(default= 80, description="test train split ratio for XGBoost")

#     evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for XGBoost")

#     xgb_hyperparameters: XGBoostHyperparameters = Field(..., description="XGBoost Hyperparameters")
    
#     additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional XGBoost Hyperparameters")