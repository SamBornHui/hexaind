from datetime import datetime, timezone
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomCodeWidgetSettings,
)
from app.services.data.assets.modules.schemas import AccessMode
from app.services.workflows.designer.schemas import (
    CustomCodeActivityConfig,
    InputOutputConfig,
    WidgetInputOutputs,
)


class CustomPythonWidget(BaseModel):
    version: Optional[str] = Field(default="1.0", description="CustomPythonWidget schema version")
    # ------------- information on widget --------------
    id: Optional[str] = Field(default=None, description="Result Id", alias="_id")
    name: str = Field(description="Unique name of custom python widget recipe")
    widget_version: str = Field(description="Widget version. for each name , versions are unique")
    description: str = Field(default="", description="description given to custom python widget recipe")
    reference_links: List[str] = Field(default=[], description="Reference links added to this recipe")
    tags: List[str] = Field(default=[], description="Reference links added to this recipe")

    recipe_id: str = Field(..., description="Recipe id from where widget is published")

    # ------------- widget rules  and settings -----------------------
    widget_inputs_rules: Optional[WidgetInputOutputs] = Field(default=None)
    widget_outputs_rules: Optional[WidgetInputOutputs] = Field(default=None)
    widget_settings: Optional[CustomCodeWidgetSettings] = Field(default=None, description="widget settings")
    help_details: Optional[Dict[str, str]] = Field(default={}, description="contains the help_details")

    # -----------used to create widget----------------
    inputs: List[InputOutputConfig] = Field(default=[], description="Types of widget inputs for this widget recipe")
    outputs: List[InputOutputConfig] = Field(default=[], description="Types of widget outputs for this widget recipe")
    config: CustomCodeActivityConfig
    # -----------------------------------------------

    # access related
    published_by: str  # user id
    published_at: datetime
    project_ids: List[str]  # visible in these projects
    site_ids: List[str]  # visible in these site ids

    # usage stats and access mode
    access_mode: AccessMode
    usage_count: int

    last_modified_by_id: Optional[str] = Field(default=None)
    last_modified_at: Optional[datetime] = Field(default=None)


class CustomPythonWidgetsResponse(BaseModel):
    succeeded: bool
    results: Optional[List[CustomPythonWidget]] = Field(default=None)
    count: Optional[int] = Field(default=None)
    message: Optional[str]


class CPWGenericResponse(BaseModel):
    success: bool
    message: str


class CPWUpdateRequest(BaseModel):
    cpw_id: str
    cpw_data: CustomPythonWidget

class CPWFileUpdateResponse(BaseModel):
    filepath: str

class CodeRequest(BaseModel):
    code: str

class LintError(BaseModel):
    line: int
    message: str