from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from app.services.data.assets.custom_python_widget_recipes.schemas import (
    CustomPythonWidgetRecipe,
)


# Export Schemas
class WorkflowExportRequest(BaseModel):
    workflow_id: str = Field(..., description="Workflow ID to export")


# Import Schemas
class WorkflowImportRequest(BaseModel):
    workflow_name: str = Field(
        ..., description="Name of the workflow being created after import"
    )
    workflow_description: str = Field(
        ..., description="Description of the workflow being created after import"
    )
    user_id: str = Field(..., description="User ID of the user importing the workflow")
    user_name: str = Field(
        ..., description="User name of the user importing the workflow"
    )


# Common Schemas
class WorkflowData(BaseModel):
    widgets: List[Dict] = Field(
        default_factory=list, description="All widgets in the workflow"
    )
    start: List[str] = Field(default_factory=list, description="Start widget")
    end: List[str] = Field(default_factory=list, description="End widget")
    client_tags: Optional[Dict] = Field(None, description="Client Tags")


class WidgetInfo(BaseModel):
    path: str
    recipe: CustomPythonWidgetRecipe


class CustomWidgets(BaseModel):
    widget_info: Dict[str, WidgetInfo] = Field(
        default_factory=dict,
        description="Module ID to Module path, Recipe mapping",
    )
    widget_ids: Dict[str, str] = Field(
        default_factory=dict, description="Widget IDs to Module ID mapping"
    )


# workflow import/export model
class WorkflowModel(BaseModel):
    workflow_data: WorkflowData
    custom_widgets: Optional[CustomWidgets]
    # mobo_widgets
