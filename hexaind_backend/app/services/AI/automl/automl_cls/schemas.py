from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Optional, Dict, Union
from pathlib import Path


class EvaluationMetricCls(str, Enum):

    accuracy = "accuracy"
    
    f1_weighted = "f1_weighted"

    log_loss = "log_loss"


class AutoMLHyperparametersCls(BaseModel):

    GBM: List[Union[Dict, str]] = Field(..., description=" GBM ")

    CAT: Dict = Field(..., description="CatBoost")

    XGB: Dict = Field(..., description="XGBoost")

    RF: List[Dict] = Field(..., description="Random Forest")

    XT: List[Dict] = Field(..., description="Extremely Randomized Trees")

    KNN: List[Dict] = Field(..., description="K-Nearest Neighbors")

    LR: Dict = Field(..., description="Linear Regression")

    NN_TORCH: Dict = Field(..., description="Neural Network PyTorch")

    FASTAI: Dict = Field(..., description="Neural Network with FastAI backend")


class AutoMLConfigCls(BaseModel):
    
    evaluation_metric_cls: EvaluationMetricCls = Field(..., description="Evaluation Metric for AutoML")

    automl_hyperparameters_cls: AutoMLHyperparametersCls = Field(..., description="AutoML Hyperparameters")
    

