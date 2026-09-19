from pydantic import BaseModel, Field
from typing import List, Optional, Union, Literal
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType

from app.services.AI.automl.schemas import ProblemType

class VariationalParams(BaseModel):

    num_latents: int =  Field(default=4, description="num_latents from user")

    num_inducing: int =  Field(default=4, description="num_inducing from user")

class SpectralKernelParams(BaseModel):

    spectral_selected: bool = Field(default=True, description="spectral_selected from user")

    num_mixtures: int =  Field(default=7, description="num_mixtures from user")

class GPRConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the gpr")

    widget_type: Literal[WidgetType.GPR]
    
    split_ratio: Optional[int] = Field(default= 100, description="test train split ratio for GPR")

    variational: Union[bool, VariationalParams] = False

    spectral_kernel:Union[bool, SpectralKernelParams] = False

    problem_type: ProblemType = Field(default=ProblemType.regression, description="problem type for GP")

    kernel_selected: List[bool]

    mean: str = Field(default="constant", description="mean")

    input_cols: List[str]= Field(..., description="x_inds range from user")

    output_cols: List[str]= Field(..., description=" y_inds range from user")

    training_iterations_max: Optional[int] = Field(default=1500, description="maximum training iterations")

    max_train: Optional[int] = Field(default=1500, description="max_train")


class GPRResponse(BaseModel):

    exception_detail: Optional[str] = Field(None, description="Exception detail for the for GPR")
    
    tabular_path: Optional[Path] = Field(None, description="tabular result of GPR widget")

    models_path: Optional[str] = Field(None, description="models result of GPR widget")