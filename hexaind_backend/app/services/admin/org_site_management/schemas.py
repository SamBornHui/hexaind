from pydantic import BaseModel, Field
from datetime  import date


class Site(BaseModel):
    id: str = Field(default='-1', description='Site Id', alias='_id')
    name: str = Field(..., description='Site Name')
    organization_id: str = Field(default='1001', description='Organization Id')
    description: str = Field(..., description='Site description')
    users_roles: list = Field(default=[])
    admin_users: list = Field(default=[])
    storage_destination: str = Field(..., description='Storage Location')
    date_created: date = Field(default='2023-09-19')
    is_active: int = Field(default=1)

class Role(BaseModel):
    id: str = Field(default='-1', description='Site Id', alias='_id')
    role_type: str = Field(...)
