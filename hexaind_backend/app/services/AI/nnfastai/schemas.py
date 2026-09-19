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



class NNFastAIHyperparameters(BaseModel):

    FASTAI: dict = Field(default_factory=dict, description="NN FASTAI")
    

class AdditionalHyperparameterTuneKWargs(BaseModel):

    scheduler: str = Field(default="local", description="Launch locally")

    searcher: str = Field(default="auto", description="BO on NN_TORCH and FASTAI models, random on others")

    num_trials: int = Field(default=10, description="Number of trials to run")

    time_out: int = Field(default=600, description="Time limit in seconds for HPO")


class NNFastAIConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the NNFastAI")

    widget_type: Literal[WidgetType.NNFASTAI]
    
    problem_type: Optional[ProblemType] = Field(ProblemType.regression, description="problem type for NNFastAI")
    
    input_cols: List[str] = Field(..., description="input features for NNFastAI")
        
    output_col: str = Field(..., description="output feature for NNFastAI")
    
    input_scaling: Optional[InputScaling] = Field(default="Standard", description="Input Scaling for NNFastAI")

    split_ratio: int = Field(default= 80, description="test train split ratio for NNFastAI")

    evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for NNFastAI")

    fastai_hyperparameters: NNFastAIHyperparameters = Field(..., description="NNFastAI Hyperparameters")
    
    additional_hyperparameter_tune_kwargs: AdditionalHyperparameterTuneKWargs = Field(..., description="Additional NNFastAI Hyperparameters")


class NNFastAIResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for NNFastAI")

    tabular_path: Optional[Path] = Field(None, description="tabular result of NNFastAI widget")

    models_path: Optional[str] = Field(None, description="models result of nnfastai widget")
