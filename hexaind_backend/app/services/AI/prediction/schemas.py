from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from pathlib import Path

from app.services.workflows.designer.base_schemas import WidgetType


class DeployModel(BaseModel):
    
    ml_id: str = Field(..., description='model_id')


class CompatibleModel(BaseModel):
    
    input_cols: List[str] = Field(...,description = "input/s colums")
    

class PredictionConfig(BaseModel):
    
    version: Optional[str] = Field(default="1.0", description="Version of the Prediction widget")
    
    ml_id: str = Field(..., description="model_id")
       
    widget_type: Literal[WidgetType.PREDICTION] = Field(..., description="Widget type")

    

class PredictionResponse(BaseModel):
    
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for prediction widget")

    tabular_path: Optional[Path] = Field(None, description="tabular result of prediction widget")