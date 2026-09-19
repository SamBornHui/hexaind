from enum import Enum
from pathlib import Path
from typing import List, Optional, Union, Literal
from pydantic import BaseModel, Field, validator

from app.services.workflows.designer.base_schemas import WidgetType


class ProblemType(str, Enum):

    regression = "regression"

    classification = "classification"


class Sampling(str, Enum):
    
    over_sampling = "smote"

    under_sampling = "randomus"

    none = "none"


class SVMRConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the svmr")

    widget_type: Literal[WidgetType.SVM]

    kernel: str = Field(default="sigmoid", help="SVM kernel type")

    C: float = Field(default=1.0, help="regularization term for SVM kernel")

    gamma: Optional[float] = Field(
        default=None,
        help="single training point influence hyperparameter for SVM kernel",
    )

    coef0: Optional[float] = Field(
        default=None, help="term used for poly and sigmoid kernels"
    )

    degree: Optional[int] = Field(default=None, help="degree for polynomial kernel")

    epsilon: Optional[float] = Field(default=0.1, help="degree for polynomial kernel")

    tol: Optional[float] = Field(default=0.001, help="degree for polynomial kernel")

    input_cols: List[str] = Field(..., description="x_inds range from user")

    output_cols: List[str] = Field(..., description=" y_inds range from user")

    problem_type: ProblemType = Field(..., description="problem type for SVM")

    sampling: Sampling = Field(default=None, description="sampling")

    @validator("gamma", always=True)
    def validate_gamma(cls, v, values):
        if values["kernel"] == "linear" and v is not None:
            raise ValueError("Gamma should not be specified for linear kernel")
        return v

    @validator("coef0", always=True)
    def validate_coef0(cls, v, values):
        if values["kernel"] not in ["poly", "sigmoid"] and v is not None:
            raise ValueError(
                "coef0 should only be specified for polynomial or sigmoid kernels"
            )
        return v

    @validator("degree", always=True)
    def validate_degree(cls, v, values):
        if values["kernel"] != "poly" and v is not None:
            raise ValueError("degree should only be specified for polynomial kernel")
        return v


class SVMConfig(BaseModel):
    problem_type: str = Field(
        default="regression", description="problem type of the svm"
    )
    config: Union[SVMRConfig] = Field(
        ..., description="Configuration for the svm types"
    )


class SVMRResponse(BaseModel):
    exception_detail: Optional[str] = Field(
        None, description="Exception detail for the for SVMR"
    )
    tabular_path: Optional[Path] = Field(
        None, description="tabular result of SVMR widget"
    )

    models_path: Optional[str] = Field(None, description="models result of SVM widget")
