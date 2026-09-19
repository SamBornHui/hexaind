import datetime
from typing import Optional, List

from pydantic import BaseModel, Field, PositiveInt
from app.services.access_controls.roles.schemas import AppNames


# ToDo: shift to rdbms in future if required
class UsersProjectsMapping(BaseModel):
    version: Optional[str] = Field(default="1.0", description="roles features map schema version")
    id: Optional[str] = Field(default=None, description="Mapping Id", alias="_id")

    user_id: str = Field(...)
    project_id: str = Field(...)
    role_id: str = Field(...)

    is_active: bool
    created_at: datetime.datetime
    created_by: str

    last_modified_at: datetime.datetime
    last_modified_by: str


class UserProjectsMappingWithDetails(UsersProjectsMapping):
    user_name: str = Field(default='')
    project_name: str = Field(default='')
    project_owner_id: str = Field(default='')
    project_owner_name: str = Field(default='')
    last_modified_by_name: str = Field(default='')
    description: str = Field(default='')
    role_name: str = Field(default='')
    last_accessed_at: str = Field(default='')
    created_by_name: str = Field(default='')
    favourited_by: List[str] = Field(default=[])
    server_role_value: Optional[int] = Field(default=4)


class UsersAccessControlDetailsBaseResponse(BaseModel):
    succeeded: bool
    message: str


class CreateMappingRequest(BaseModel):
    user_id: str = Field(...,min_length=1)
    project_id: str = Field(...,min_length=1)
    role_id: str = Field(...,min_length=1)


class CreateMappingRequestMultiple(BaseModel):
    project_id: str = ''
    mappings: List[CreateMappingRequest] = Field(default=[])


class GetRolesBasedOnIdRequest(BaseModel):
    id: str = Field(..., description="The ID of the project/User for which roles are being requested.")
    get_details: bool = Field(default=False, description="Fetches details from other db collections as well.")

class GetUnmappedUsersToProjectRequest(GetRolesBasedOnIdRequest):
    project_id: str = ''
    search_term: str = ''
    page_number: PositiveInt = 1
    page_limit: PositiveInt = 100


class GetRolesBasedOnIdResponse(UsersAccessControlDetailsBaseResponse):
    mappings: Optional[List[UserProjectsMappingWithDetails]] = Field(default=None)


class CreateMappingResponse(UsersAccessControlDetailsBaseResponse):
    mapping_id: Optional[str] = Field(default='')


class DeleteUserProjMappingRequest(BaseModel):
    user_id: str
    project_id: str

class EditAppPermission(BaseModel):
    app_name: AppNames
    default_user: bool

class AppPermission(EditAppPermission):
    id: Optional[str] = Field(default=None, description="Unique ID", alias="_id")
    is_active: Optional[bool] = True
    last_modified_at: datetime.datetime
    last_updated_by: str