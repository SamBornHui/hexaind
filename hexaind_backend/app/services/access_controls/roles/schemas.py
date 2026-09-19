import datetime
from enum import Enum
from typing import Optional, Union, Any, List

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import BaseModel, Field


class DatasetBasedFeatures(BaseModel):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False


class MLModelBasedFeatures(BaseModel):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False


class ConnectorBasedFeatures(BaseModel):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False


class WorkflowsBasedFeatures(BaseModel):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False
    execute: bool = False
    publish: bool = False
    update_versioned: bool = False


class RecipeBasedFeatures(BaseModel):
    create: bool = False
    read: bool = False
    update: bool = False
    delete: bool = False
    execute: bool = False


class AssetsBasedFeatures(BaseModel):
    datasets: DatasetBasedFeatures = Field(default_factory=DatasetBasedFeatures)
    ml_models: MLModelBasedFeatures = Field(default_factory=MLModelBasedFeatures)
    workflows: WorkflowsBasedFeatures = Field(default_factory=WorkflowsBasedFeatures)
    recipes: RecipeBasedFeatures = Field(default_factory=RecipeBasedFeatures)
    connectors: ConnectorBasedFeatures = Field(default_factory=ConnectorBasedFeatures)


class JupyterToolBasedFeatures(BaseModel):
    execute: bool = False


class DSGToolBasedFeatures(BaseModel):
    execute: bool = False


class ToolBasedFeatures(BaseModel):
    jupyter: JupyterToolBasedFeatures = Field(default_factory=JupyterToolBasedFeatures)
    dsg_tool: DSGToolBasedFeatures = Field(default_factory=DSGToolBasedFeatures)


class JobBasedFeatures(BaseModel):
    read: bool = False


class HelpSupportBasedFeatures(BaseModel):
    read: bool = False


class ResourcesBasedFeatures(BaseModel):
    jobs: JobBasedFeatures = Field(default_factory=JobBasedFeatures)
    help_support: HelpSupportBasedFeatures = Field(
        default_factory=HelpSupportBasedFeatures
    )


class ManageUsersInProjectBasedFeatures(BaseModel):
    add: bool = False
    read: bool = False
    modify: bool = False  # change role..etc
    delete: bool = False


class ManageUsersBasedFeatures(BaseModel):
    add: bool = False
    read: bool = False
    modify: bool = False
    delete: bool = False


class ProjectAdminBasedFeatures(BaseModel):
    create: bool = False
    delete: bool = False
    update: bool = False
    read: bool = False


class ProjectBasedFeatures(BaseModel):
    assets: AssetsBasedFeatures = Field(default_factory=AssetsBasedFeatures)
    tools: ToolBasedFeatures = Field(default_factory=ToolBasedFeatures)
    resources: ResourcesBasedFeatures = Field(default_factory=ResourcesBasedFeatures)
    # will be for enabled person who creates project
    manage_project_users: ManageUsersInProjectBasedFeatures = Field(
        default_factory=ManageUsersInProjectBasedFeatures
    )
    projects: ProjectAdminBasedFeatures = Field(
        default_factory=ProjectAdminBasedFeatures
    )


class ServerBasedFeatures(BaseModel):
    manage_users: ManageUsersBasedFeatures = Field(
        default_factory=ManageUsersBasedFeatures
    )


class RoleType(str, Enum):
    SERVER_ROLE = "SERVER_ROLE"
    PROJECT_ROLE = "PROJECT_ROLE"


class RoleCreationType(str, Enum):
    SYSTEM_GENERATED_ROLE = "SYSTEM_GENERATED_ROLE"
    CUSTOM_ROLE = "CUSTOM_ROLE"


class SystemGeneratedProjectRoles(str, Enum):
    FULL_ACCESS = "FULL ACCESS"
    LIMITED_ACCESS = "LIMITED ACCESS"
    PROJECT_ADMINISTRATOR = "PROJECT ADMINISTRATOR"


class RolesFeaturesMap(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="roles features map schema version"
    )
    id: Optional[str] = Field(default=None, description="Role Id", alias="_id")
    name: str = Field(description="Name of role.")
    description: str = Field(description="Role description.")
    role_type: RoleType = Field(default=RoleType.PROJECT_ROLE)
    features: Optional[Union[ProjectBasedFeatures | ServerBasedFeatures]] = Field(
        default=None, description="Features map"
    )
    created_at: datetime.datetime
    created_by: Optional[str] = Field(default=None)
    is_active: bool
    last_modified_at: datetime.datetime
    last_modified_by: Optional[str] = Field(default=None)
    source_type: RoleCreationType = Field(
        default=RoleCreationType.SYSTEM_GENERATED_ROLE
    )


class RolesFeaturesMapUpdateRequest(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="roles features map schema version"
    )
    id: Optional[str] = Field(default=None, description="Role Id", alias="_id")
    name: str = Field(description="Name of role.")
    description: str = Field(description="Role description.")
    role_type: RoleType = Field(default=RoleType.PROJECT_ROLE)
    features: Optional[Union[ProjectBasedFeatures | ServerBasedFeatures]] = Field(
        default=None, description="Features map"
    )


class RolesFeaturesMapGetRequest(BaseModel):
    roles_id: str


class RoleFeaturesMapRequestName(BaseModel):
    role_name: str


class RolesFeaturesMapGetResponse(BaseModel):
    succeeded: bool
    message: str
    role_info: Optional[RolesFeaturesMap] = None


class RoleIdRoleName(BaseModel):
    name: str
    id: str
    role_type: RoleType


class GetAllRolesResponse(BaseModel):
    succeeded: bool
    message: str
    results: Optional[List[RoleIdRoleName]] = Field(
        default=None, description="contains roleid rolenames list"
    )


class RolesFeaturesMapCreateRequest(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="roles features map schema version"
    )
    name: str = Field(description="Name of role.")
    description: str = Field(description="Role description.")
    role_type: RoleType = Field(default=RoleType.PROJECT_ROLE)
    features: Optional[Union[ProjectBasedFeatures | ServerBasedFeatures]] = Field(
        default=None, description="Features map"
    )
    source_type: RoleCreationType = Field(
        default=RoleCreationType.SYSTEM_GENERATED_ROLE
    )


class RolesFeaturesMapCreateResponse(BaseModel):
    succeeded: bool
    message: str
    role_id: Optional[str] = None


class AppNames(str, Enum):
    DatasheetGenerator = "DatasheetGenerator"
    UC6 = "UC6"
    UC7_DataCatalog = "UC7_DataCatalog"
    UC12 = "UC12"
    UC1_Configuration = "UC1_Configuration"
    DataCatalog = "DataCatalog"
    UC2_Result_Visualization = "UC2_Result_Visualization"
    ScrapAnalysis = "ScrapAnalysis"
