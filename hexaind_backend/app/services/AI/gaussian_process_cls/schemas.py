from pydantic import BaseModel, Field
from pydantic.v1 import validator
from enum import Enum
from typing import List, Optional, Union, Literal
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType
from app.services.AI.automl.schemas import ProblemType


class Sampling(str, Enum):

    oversampling = "smote"

    undersampling = "randomus"

    none = 'none'


class MeanConfig(str, Enum):
    
    constant = 'constant'

    linear = 'linear'

    zero = 'zero'


class SpectralKernel(BaseModel):
    
    spectral_kernel: bool = Field(False, description="Boolean for spectral-mixture kernel")
    
    num_mixtures: int = Field(4, description="Number of mixtures in spectral-mixture kernel")


class CovariancFunction(BaseModel):
    
    kernel_selected: bool = Field(..., description="Boolean for kernel_selected kernel")
    
    covariance_function_selection: List[bool] = Field(..., description="covariance_function_selection flag value")


class GPCConfig(BaseModel):

    version: Optional[str] = Field(default="1.0", description="Version of the GPC")

    widget_type: Literal[WidgetType.GPC]
    
    input_cols: List[str] = Field(..., description="input features for GPC")
        
    output_col: str = Field(..., description="output feature for GPC")

    problem_type: ProblemType = Field(default=ProblemType.classification, description="problem type for GP")

    max_train: Optional[int] = Field(default=1500, description="Number of training points to switch to sparse approximation")

    sampler_type: Sampling = Field(default="smote", description="sampler_type for GPC")

    covariance_function: CovariancFunction = Field(..., description="List of kernels for use. Multiple active results in linear combination of kernels.")
    
    mean: MeanConfig = Field(..., description="Type of mean function options ['constant','linearl','zero']")

    spectral_kernel_setting: Union[SpectralKernel, bool] = Field(..., description="Boolean or dict for spectral-mixture kernel")

    variational: bool = Field(False, description="Boolean for variational inference")

    num_inducing: Optional[int] = Field(None, description="Number of inducing points for sparse approximation")

    num_latents: Optional[int] = Field(None, description="Number of latent GPs for multi-output model")

    lr_init: float = Field(1e-1, description="Initial learning rate")
    
    lr_end: float = Field(1e-6, description="End learning rate")

    num_epochs: Optional[int] = Field(default=250, description="Maximum number of training epochs")

    batch_size: Optional[int] = Field(default=250, description="Batch size for variational GPs")

    patience: Optional[int] = Field(default=10, description="Patience to reduce lr in scheduler")

        
    @validator('num_inducing', 'num_latents', pre=True, always=True)
    def set_variational_dependent_fields(cls, v, values, field):
        if values.get('variational'):
            if field.name == 'num_inducing':
                return v if v is not None else 200
            elif field.name == 'num_latents':
                return v if v is not None else 4
        return v



class GPCResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for GPC")

    tabular_path: Optional[Path] = Field(None, description="tabular result of GPC widget")

    models_path: Optional[str] = Field(None, description="models result of GPC widget")

