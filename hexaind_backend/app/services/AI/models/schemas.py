from __future__ import annotations

import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union
from app.services.workflows.designer.base_schemas import WidgetType

from pydantic import BaseModel, Field, constr

class CreateVisualizationsResponse(BaseModel):
    visualization_data: Dict

class ModelsData(BaseModel):
    model: str
    summary_path: str
    data_path: str
    chosen_column: str
    output_col: str
    split_ratio: int
    data_type: str


class CompareModelsRequest(BaseModel):
    models_config: List[ModelsData]
    
class CompareModelsResponse(BaseModel):
    comapre_visualization_data: List[Dict]

class HighlightPointResponse(BaseModel):
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for GPR")
    point_summary: Optional[Dict] = Field(None, description="tabular result of GPR widget")

class HighlightPointRequest(BaseModel):
    model: str
    summary_path: str
    data_path: str
    chosen_column: str
    output_col: str
    split_ratio: int
    data_type: str
    graph_name: str
    coordinates: Dict