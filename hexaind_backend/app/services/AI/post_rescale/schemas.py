from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Union, Optional, Dict, Literal
from pathlib import Path
from app.services.workflows.designer.base_schemas import WidgetType



class FileDetails(BaseModel):
    file_name: str
    file_path: Path



class PostRescaleConfig(BaseModel):
 
    version: Optional[str] = Field(default="1.0", description="Version of the mobo post-processing widget")

    widget_type: Literal[WidgetType.POST_RESCALE] 

    post_rescale_module_id: str = Field(description="module id for the user uploaded mobo post-processing scripts folder")

class PostRescaleResponse(BaseModel):
    
    json_path: Optional[Path] = Field(None, description="Json file file path for the post rescale widget")

    exception_detail: Optional[str] = Field(None, description="Exception detail for the post rescale widget")


