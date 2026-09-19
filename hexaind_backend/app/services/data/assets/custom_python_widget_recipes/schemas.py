import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field

from .dropdown_schemas import *
from app.core.schemas.action_result import ActionResultType
from app.services.data.assets.modules.schemas import AccessMode, Module
from app.services.workflows.designer.schemas import (
    DatasetTypes,
    WidgetInputOutputs,
    WidgetParameterDetails,
)

class WidgetInputOutputDetails(BaseModel):
    reference_name: Optional[str] = Field(
        default=None
    )  # input_1, input_2 or output1, ouput2
    type: Optional[ActionResultType] = Field(default=None)
    sub_type: Optional[Union[DatasetTypes]] = Field(default=None)


class WidgetInputSourceType(str, Enum):
    INPUT_SELECTED_FROM_PRIOR_WIDGET = "INPUT_SELECTED_FROM_PRIOR_WIDGET"
    INPUT_ENTERED_MANUALLY_ON_WIDGET = "INPUT_ENTERED_MANUALLY_ON_WIDGET"


class CustomPythonWidgetRecipeStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"


class CustomCodePythonWidgetInputsMap(BaseModel):

    arg_name: str

    type: str

    default_value: Optional[Any] = None

    is_mandatory: bool = Field(
        default=True,
        description="Only params whose default values there can be non-mandatory",
    )

    source: WidgetInputSourceType = Field(
        ...,
        description="determines whether this value will be coming from prev widget or not",
    )
    mapped_input: Optional[WidgetInputOutputDetails | WidgetParameterDetails] = Field(
        default=None, description="Used to pre-map inputs"
    )

    drop_down_details: Optional[DropDownDetails] = Field(default=None, description="details about drop down")
    
class CustomCodePythonWidgetOutputsMap(BaseModel):
    type: str  # python type
    mapped_output: Optional[WidgetInputOutputDetails] = Field(
        default=None, description="used to pre map outputs"
    )


class CustomCodeWidgetSettings(BaseModel):
    color_code: str
    allow_users_to_modify_configurations: bool


class CustomPythonWidgetRecipe(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="CustomPythonWidgetRecipe schema version"
    )

    id: Optional[str] = Field(default=None, description="recipe id", alias="_id")
    # info
    name: str = Field(description="Unique name of custom python widget")
    recipe_name: Optional[str] = Field(
        default=None, description="recipe name given to custom python widget recipe"
    )
    description: Optional[str] = Field(
        default=None, description="description given to custom python widget recipe"
    )
    reference_links: Optional[List[str]] = Field(
        default=None, description="Reference links added to this recipe"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Reference links added to this recipe"
    )

    # widget input count and rules
    widget_inputs_rules: Optional[WidgetInputOutputs] = Field(default=None)
    widget_outputs_rules: Optional[WidgetInputOutputs] = Field(default=None)

    # ---------used while publishing widget----------------
    module_id: Optional[str] = Field(
        default=None, description="Module id of CustomCode Uploaded"
    )
    inputs_map: Optional[List[CustomCodePythonWidgetInputsMap]] = Field(
        default=None, description="Contains input maps"
    )
    outputs_map: Optional[List[CustomCodePythonWidgetOutputsMap]] = Field(
        default=None, description="Contains outputs map"
    )
    settings: Optional[CustomCodeWidgetSettings] = Field(
        default=None, description="settings stored for widget"
    )
    help_details: Optional[Dict[str, str]] = Field(
        default={}, description="contains the help_details"
    )

    recipe_status: Optional[CustomPythonWidgetRecipeStatus] = Field(
        default=CustomPythonWidgetRecipeStatus.DRAFT,
        description="contains the status of current recipe",
    )

    # -------access------
    project_id: str
    site_id: str
    access_mode: AccessMode

    # validation related : found in module metadata.

    # additional details
    created_by: str  # user id of user created this recipe
    created_at: datetime.datetime

    last_modified_by: str  # user_id of user who last edited this recipe
    last_modified_at: datetime.datetime


class CustomPythonWidgetRecipeViewDetails(CustomPythonWidgetRecipe):
    created_by_name: Optional[str] = Field(default="")
    last_modified_by_name: Optional[str] = Field(default="")

    # fetches corresponding widget
    associated_widgets: Optional[List[str]] = Field(default=None)


class CustomPythonWidgetRecipeUpdateRequest(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="CustomPythonWidgetRecipe schema version"
    )

    id: Optional[str] = Field(default=None, description="recipe id", alias="_id")
    # info
    name: str = Field(description="Unique name of custom python widget")
    recipe_name: Optional[str] = Field(
        default=None, description="recipe name given to custom python widget recipe"
    )
    description: Optional[str] = Field(
        default=None, description="description given to custom python widget recipe"
    )
    reference_links: Optional[List[str]] = Field(
        default=None, description="Reference links added to this recipe"
    )
    tags: Optional[List[str]] = Field(
        default=None, description="Reference links added to this recipe"
    )

    # input count and types
    widget_inputs_rules: Optional[WidgetInputOutputs] = Field(default=None)
    widget_outputs_rules: Optional[WidgetInputOutputs] = Field(default=None)

    recipe_status: Optional[CustomPythonWidgetRecipeStatus] = Field(
        default=CustomPythonWidgetRecipeStatus.DRAFT,
        description="contains the status of current recipe",
    )

    module_id: Optional[str] = Field(
        default=None, description="Module id of CustomCode Uploaded"
    )
    inputs_map: Optional[List[CustomCodePythonWidgetInputsMap]] = Field(
        default=None, description="Contains input maps"
    )
    outputs_map: Optional[List[CustomCodePythonWidgetOutputsMap]] = Field(
        default=None, description="Contains outputs map"
    )
    settings: Optional[CustomCodeWidgetSettings] = Field(
        default=None, description="settings stored for widget"
    )
    help_details: Optional[Dict[str, str]] = Field(
        default={}, description="contains the help_details"
    )

    project_id: str
    site_id: str
    access_mode: AccessMode

    created_at: Optional[datetime.datetime] = Field(
        default=None, description="created at used while updating"
    )
    created_by: Optional[str] = Field(
        default=None, description="created by used while updating existing request"
    )


class CustomPythonWidgetRecipeUpdateResponse(BaseModel):
    succeeded: bool
    custom_python_widget_recipe_id: Optional[str]
    message: Optional[str]


class CustomPythonWidgetRecipesResponse(BaseModel):
    succeeded: bool
    results: Optional[List[CustomPythonWidgetRecipeViewDetails]] = Field(default=None)
    count: Optional[int] = Field(default=None)
    message: Optional[str]


class CustomPythonWidgetRecipePublishResponse(BaseModel):
    succeeded: bool
    custom_python_widget_id: Optional[str]
    message: Optional[str]


class CustomPythonWidgetRecipePublishRequest(BaseModel):
    custom_python_widget_recipe_id: str
    custom_python_widget_id: Optional[str] = Field(default=None)
    widget_version: Optional[str] = Field(default=None)
    user_id: Optional[str] = Field(default=None)
    project_ids: Optional[List[str]] = Field(default=[])
    site_ids: Optional[List[str]] = Field(default=[])
    access_mode: Optional[AccessMode] = Field(default=AccessMode.INTERNAL)


class CPWUsedInAssetNames(str, Enum):
    WORKFLOW = "WORKFLOW"
    SCHEDULE = "SCHEDULE"


class CustomPythonWidgetUsage(BaseModel):
    name: str
    id: str
    type: CPWUsedInAssetNames
    version: Optional[str] = None
    status: Optional[str] = None


class CustomPythonWidgetUsages(BaseModel):
    widget_id: str
    widget_name: str
    widget_version: str
    widget_usage_response: Optional[List[CustomPythonWidgetUsage]] = None


class CustomPythonWidgetGetDetailsRequest(BaseModel):
    recipe_id: Optional[str] = None
    widget_id: Optional[str] = None


class CustomPythonWidgetRecipeValidationResponse(BaseModel):
    succeeded: bool
    validation_status: Optional[bool] = False
    validation_message: Optional[str] = ""
    widget_details: Optional[List[CustomPythonWidgetUsages]] = None


class CPWRCloneRequest(BaseModel):
    recipe_id: str
    recipe_name: str


class CPWRCloneResponse(BaseModel):
    clone_id: str
    message: str
    recipe_details: Optional[CustomPythonWidgetRecipe] = Field(default= None)
    module_details: Optional[Module] = Field(default= None)