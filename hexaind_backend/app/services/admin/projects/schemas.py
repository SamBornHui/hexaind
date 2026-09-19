from pydantic import BaseModel, Field
from enum import Enum
from typing import List, Union, Optional
from datetime import datetime, timezone


class SupersetRoleData(BaseModel):
    role_id: int


class Project(BaseModel):
    version: str = Field(default="1.0", description="Version of the Project", read_only=True)
    id: Optional[str] = Field(default=None, description="Project Id", alias="_id")
    name: str = Field(..., description="user defined name for a Project")
    description: str = Field(default="", description="user defined description for a Project")
    site_id: str = Field(default=None, description="Site ID")
    owner_id: str = Field(default=None, description="ID of the user who created the Project")
    owner_name: str = Field(default=None, description="Name of the user who created the Project")
    created_at: Optional[datetime] = Field(default=None, description="created datetime")
    created_by: Optional[str] = Field(default=None,description="created by user id")
    last_modified_by_id: str = Field(default=None, description="ID of the user who recently modified the Project")
    last_accessed_at: Optional[datetime] = Field(default=None, description="Last Accessed(including assets under project) Date and Time UTC format")
    last_modified_at: datetime = Field(default=None, description="Created Date and Time UTC format")
    shared_with: List[str] = Field(default=[], description="User IDs list to who Project Shared")
    favorited_by: List[str] = Field(default=[], description="Favourited users list")
    is_active: bool = Field(default=True, description="Is Active")
    superset_data: Optional[SupersetRoleData] = None


class users_roles_map(BaseModel):
    user_id: str
    role_id: str

class CreateNewProjectRequest(BaseModel):
    name: str
    description: str
    project_administrator_id: Optional[str] = Field(default="")
    project_administrator_name: Optional[str] = Field(default="")
    users_roles_mappings: List[users_roles_map] = Field(default=[])

class CreateNewProjectResponse(BaseModel):
    succeeded: bool
    message: str
    project_id: str

class CreateProjectResponse(BaseModel):

    project_id: str

class ProjectListResponse(BaseModel):

    projects: List[Project]
    
    total_count: int


class UpdateProjectResponse(BaseModel):

    success: bool
    message: Optional[str] = ''

class DeleteProjectResponse(BaseModel):

    success: bool
    message: Optional[str] = ''
