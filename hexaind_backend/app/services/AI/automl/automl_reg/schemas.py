from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional
from pathlib import Path


class InputScaling(str, Enum):

    Min_Max = "Min-Max"

    Standard = "Standard"

    Robust = "Robust"


class EvaluationMetric(str, Enum):

    root_mean_squared_error = "root_mean_squared_error"
    
    mean_squared_error = "mean_squared_error"

    mean_absolute_error = "mean_absolute_error"
    
    mean_absolute_percentage_error = "mean_absolute_percentage_error"


class AutoMLHyperparameters(BaseModel):

    GBM: dict = Field(default_factory=dict, description="LightGBM")

    CAT: dict = Field(default_factory=dict, description="CatBoost")

    XGB: dict = Field(default_factory=dict, description="XGBoost")

    RF: dict = Field(default_factory=dict, description="Random Forest")

    XT: dict = Field(default_factory=dict, description="Extremely Randomized Trees")

    KNN: dict = Field(default_factory=dict, description="K-Nearest Neighbors")

    LR: dict = Field(default_factory=dict, description="Linear Regression")

    NN_TORCH: dict = Field(default_factory=dict, description="Neural Network PyTorch")

    FASTAI: dict = Field(default_factory=dict, description="Neural Network with FastAI backend")

    # AG_AUTOMM: Optional[dict] = Field(default_factory=dict, description="Multi-modal models with AutoGluon's AutoMM framework")
    # custom: Optional[AutoGluonGPWrapper] = None  # Assuming AutoGluonGPWrapper is a defined class elsewhere


class AutoMLConfigReg(BaseModel):

    input_scaling: InputScaling = Field(default="Standard", description="Input Scaling for AutoML")

    evaluation_metric: EvaluationMetric = Field(default="root_mean_squared_error", description="Evaluation Metric for AutoML")

    automl_hyperparameters: AutoMLHyperparameters = Field(..., description="AutoML Hyperparameters")
    


