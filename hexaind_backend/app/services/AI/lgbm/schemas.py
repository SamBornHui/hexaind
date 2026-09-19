from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Literal, Union
from pathlib import Path

from ..automl.schemas import ProblemType
from ..automl.automl_reg.schemas import EvaluationMetric

from app.services.workflows.designer.base_schemas import WidgetType

class InputScaling(str, Enum):

    Min_Max = "Min-Max"

    Standard = "Standard"

    Robust = "Robust"

# Enum for optimization methods
class OptimizationMethod(str, Enum):
    GridSearch = "GridSearch"
    RandomSearch = "RandomSearch"

class LGBMParametersSubclass(BaseModel):
    # selected_scaling_method: ScalingMethod = ScalingMethod.NoneType
    # Test_data_percentage: float = 0.2
    Selected_Optimization_method: OptimizationMethod = OptimizationMethod.GridSearch
    cv: int = 5
    random_state: int = 42
    n_iter: Optional[int] = Field(50, description="Used only for RandomSearch")
    Min_depth: int = 20
    Max_depth: int = 100
    SampleNo_depth: int = 4
    Min_num_leaves: int = 16
    Max_num_leaves: int = 128
    SampleNo_num_leaves: int = 4
    Min_child_samples: int = 20
    Max_child_samples: int = 100
    SampleNo_child_samples: int = 4

class LGBMHyperparameters(BaseModel):

    # GBM: dict = Field(default_factory=dict, description="LightGBM")
    GBM: Union[dict, LGBMParametersSubclass]


class AdditionalHyperparameterTuneKWargs(BaseModel):

    scheduler: str = Field(default="local", description="Launch locally")

    searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

    num_trials: int = Field(default=10, description="Number of trials to run")

    time_out: int = Field(default=600, description="Time limit in seconds for HPO")


class LGBMConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the lgbm")

    widget_type: Literal[WidgetType.LGBM]
    
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for lgbm")
    
    input_cols: List[str] = Field(..., description="input features for lgbm")
        
    output_col: str = Field(..., description="output feature for lgbm")
    
    input_scaling: Optional[InputScaling] = Field(default="Standard", description="Input Scaling for lgbm")

    split_ratio: int = Field(default= 80, description="test train split ratio for lgbm")

    evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for lgbm")

    lgbm_hyperparameters: LGBMHyperparameters = Field(..., description="lgbm Hyperparameters")
    
    additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional lgbm Hyperparameters")


class LGBMResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for lgbm")

    tabular_path: Optional[Path] = Field(None, description="tabular result of lgbm widget")
    
    best_model_top_features: Optional[List[str]] = Field(None, description="Top shap features of the best model")

    models_path: Optional[str] = Field(None, description="models result of lgbm widget")
