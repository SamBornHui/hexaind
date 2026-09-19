from __future__ import annotations
from pydantic import BaseModel, Field, RootModel, ConfigDict, EmailStr, computed_field
from typing import Optional, Union, Literal, Annotated, List
from datetime import datetime, timezone
from enum import Enum
import time
from app.config.env_vars import environment

class ServerBasedRoleNames(str,Enum):
    SERVER_ADMIN='Server Admin'
    PROJECT_ADMIN='Project Admin'
    DEFAULT_USER='Default User'

    @staticmethod
    def get_server_role(server_role_value: int) -> 'ServerBasedRoleNames':
        if server_role_value == 1:
            return ServerBasedRoleNames.SERVER_ADMIN
        elif server_role_value == 2:
            return ServerBasedRoleNames.PROJECT_ADMIN
        elif server_role_value == 4:
            return ServerBasedRoleNames.DEFAULT_USER
        else:
            raise ValueError(f"Expecting [1,2,4] for server role value {server_role_value}")

    def get_server_role_value(self) -> int:
        role_values = {
            ServerBasedRoleNames.SERVER_ADMIN: 1,
            ServerBasedRoleNames.PROJECT_ADMIN: 2,
            ServerBasedRoleNames.DEFAULT_USER: 4,
        }
        return role_values[self]
    
    def get_server_role_id(self) -> str:
        role_ids = {
            ServerBasedRoleNames.SERVER_ADMIN: "1",
            ServerBasedRoleNames.PROJECT_ADMIN: "2",
            ServerBasedRoleNames.DEFAULT_USER: "4",
        }
        return role_ids[self]

class UserEmail(EmailStr):
    @classmethod
    def _validate(cls, __input_value: str) -> str:
        result = super()._validate(__input_value)
        return result.lower() #converting to lower

class UserLoginSchema(BaseModel):
    email: UserEmail = Field(...)
    password: str = Field(...)
    class Config:
        json_schema_extra = {
            'example': {
                'email': 'joe@xyz.com',
                'password': 'any'
            }
        }

class SuperSetData(BaseModel):
    password: str
    username: str
    role: List[int]
    superset_user_id: int


class User(BaseModel):
    id: Optional[str] = Field(default=None, description='Server role Id', alias='_id')
    name: str = Field(..., description='User name')
    email: UserEmail = Field(..., description='User email')
    invited_by_id: str = Field(..., description='Invited user id')
    invited_by: str = Field(default='', description='Invited user name')
    created_at: Optional[datetime] = Field(default=None,description="Created/Added time to platform")
    updated_at: Optional[datetime] = Field(default=None, description='Last Updated Date Time')
    updated_by: Optional[str] = Field(default="",description="last updated by user id")
    status: str = Field(..., description='New, Invited, Active, Inactive, MarkedForDelete' )
    last_login_date: Optional[datetime] = Field(default=None, description='Last Login Date')
    login_status: bool = False
    server_role_value: int = Field(..., description='role value like 1,2,4,..')
    server_role: Optional[str] = Field(default='', description='server role name')
    server_role_id: Optional[str] = Field(default='', description='server role id')
    role_updated_at: Optional[datetime] = Field(default=None, description='last role updated at')
    role_updated_by_id: Optional[str] = Field(default='', description='last role updated by which user_id')
    role_updated_by_name: Optional[str] = Field(default='')
    is_sso_user: bool = False
    last_invite_sent_at: Optional[datetime] = Field(default=None)
    # using for hexaind2 integration
    first_name: Optional[str] = Field(default='', description="stores first name")
    last_name: Optional[str] = Field(default='', description="stores last name")
    is_pwd_reset: Optional[bool]= Field(default=False, description="Indicates the Pwd reset by Admin")
    user_projects_count: Optional[int] = 0
    last_activity_at: Optional[int] = 0
    data_superset: Optional[SuperSetData] = None

    @computed_field
    def login_activity(self) -> Literal['ACTIVE', 'INACTIVE', 'LOGOUT']:
        current_time = int(time.time())
        if not self.login_status:
            return 'LOGOUT'
        elif current_time - self.last_activity_at <= environment.user_inactive_after_secs:  # 5 minutes in seconds
            return 'ACTIVE'
        elif current_time - self.last_activity_at >= environment.user_logout_after_secs:  # 30 days
            return 'LOGOUT'
        else:
            return 'INACTIVE'
    
    @computed_field
    def inactive_days(self) -> int:
        last_activity_stamp = datetime.fromtimestamp(self.last_activity_at)
        days_difference = (datetime.now() - last_activity_stamp).days
        return days_difference


class UserDetails(BaseModel):
    id: str
    name: str
    user_id: Optional[str] = Field(default="")
    user_name: Optional[str] = Field(default="")
    email: UserEmail
    invited_by: str
    server_role_value: int
    server_role: str
    role_updated_at: Optional[datetime] = Field(default=None)
    role_updated_by_id: Optional[str] = Field(default="")
    role_updated_by_name: Optional[str] = Field(default="")


class UserDetailsRequest(BaseModel):
    server_role_values: List[int] = Field(default=[2,4], description="by default fetch project admin and default users")
    skip_own: bool = Field(default=True)
    search_term: str = ''
    page_number: int = 1
    page_limit: int = 100
    fetch_role_details: bool = False

class UserDetailsResponse(BaseModel):
    succeeded: bool
    message: str
    results: Optional[List[UserDetails]] = Field(default=None)
    results_count: Optional[int] = Field(default=-1)


class LoginResponse(BaseModel):
    user_data: User
    access_token: str
    refresh_token: str

class InviteUsersResponse(BaseModel):
    message: str
    inv_email_sent_to: List[str]
    inv_email_failed_to: List[str]

class RoleEnum(str, Enum):
    server_admin = '1'
    project_admin = '2'
    default_user = '3'

class InviteUserSchema(BaseModel):
    name: str = Field(...)
    email: UserEmail = Field(...)
    server_role_id: RoleEnum = Field(default=RoleEnum.default_user)
    is_sso_user: bool = Field(default=False)

    class Config:
        use_enum_values = True
        json_schema_extra = {
            'example': {
                'name': 'Rajesh',
                'email': 'rajesh@xyz.com',
                'server_role_id': '2',
                'is_sso_user': False
            }
        }

class RegisterUserSchema(BaseModel):
    email: UserEmail = Field(...)
    password: str = Field(...)
    conf_password: str = Field(...)
    email_verification_token: str = Field(...)
    first_name: str = Field(default='')
    last_name: str = Field(default='')

    class Config:
        json_schema_extra = {
            'example': {
                'email': 'username@databrick.tech',
                'password': 'password',
                'conf_password': 'password',
                'email_verification_token': 'valid Email Verification Token received in Mail',
                'first_name': 'Joseph',
                'last_name': 'Joe'
            }
        }



class UserIdRoleValueMap(BaseModel):
    user_id: str
    server_role_value: int
    server_role: Optional[str] = None
class UpdateUserRolesRequest(BaseModel):
    changes: List[UserIdRoleValueMap]

class UpdateUserRolesResponse(BaseModel):
    succeeded: bool
    message: str


class ChangeUserNamesSchema(BaseModel):
    email: UserEmail = Field(...)
    name: str = Field(default='')
    first_name: str = Field(default='')
    last_name: str = Field(default='')

    class Config:
        json_schema_extra = {
            'example': {
                'email': 'username@databrick.tech',
                'name': 'Name',
                'first_name': 'First Name',
                'last_name': 'Last Name'
            }
        }

class TokensSchema(BaseModel):
    access_token: str
    refresh_token: str

class ChangePasswordSchema(BaseModel):
    email: UserEmail = Field(...)
    old_password: str = Field(...)
    password: str = Field(...)
    conf_password: str = Field(...)

    class Config:
        json_schema_extra = {
            'example': {
                'email': 'joe@xyz.com',
                'old_password': 'password',
                'password': 'password',
                'conf_password': 'password'
            }
        }
class SiteRoleSchema(BaseModel):
    site_id: str
    role_id: str

class RefreshTokenSchema(BaseModel):
    email: UserEmail = Field(...)
    access_token: str = Field(...)
    refresh_token: str = Field(...)

    class Config:
        json_schema_extra = {
            'example': {
                'email': 'joe@xyz.com',
                'access_token': 'Valid Access Token',
                'refresh_token': 'Valid Refresh Token'
            }
        }

class SSOEnum(str, Enum):
    GCP = 'GCP'
    AZURE = 'Azure'

class AzureTokensSchema(BaseModel):
    type: Literal[f"{SSOEnum.AZURE}"]
    access_token: str 
    raw_token: str 

    model_config= ConfigDict(
        json_schema_extra = {
            'example': {
                'type': f"{SSOEnum.AZURE}",
                'access_token': 'azure accessToken',
                'raw_token': 'azure idToken>rawIdToken'
            }
        })

class GcpTokensSchema(BaseModel):
    type: Literal[f"{SSOEnum.GCP}"]
    gcp_id_token: str 
    model_config= ConfigDict(
        json_schema_extra = {
            'example': {
                'type': f"{SSOEnum.GCP}",
                'gcp_id_token': 'gcp id_token'
            }
        })

class SSOLoginSchema(RootModel):
    root: Annotated[Union[GcpTokensSchema, AzureTokensSchema], Field(discriminator="type")]
    model_config= ConfigDict(
        arbitrary_types_allowed = True,
        json_schema_extra  = {
            "example": {
                "type": f"{SSOEnum.AZURE}/{SSOEnum.GCP}",
                "access_token": 'azure accessToken for AZURE SSO ignore if not Azure',
                "raw_token": 'azure idToken>rawIdToken for AZURE SSO ignore if not Azure', 
                "gcp_id_token": 'gcp id_token for GCP SSO ignore if not GCP'
            }
        })

class InviteBulkUsersSchema(BaseModel):
    email_ids: List[UserEmail] = Field(...)
    server_role_id: RoleEnum = Field(default=RoleEnum.default_user)
    is_sso_user: bool = Field(default=False)

    class Config:
        use_enum_values = True
class ServerRole(BaseModel):
    id: Optional[str] = Field(default=None, description='User Id', alias='_id')
    role_name: str
    role_value: int

class UserStatus(str, Enum):
    INVITED = "Invited"
    ACTIVE = 'Active'
    INACTIVE = 'Inactive'
    NOT_INVITED = "Not Invited"

    @classmethod
    def has_member_value(cls, value):
        return value in cls._value2member_map_

class ActivateUserSchema(BaseModel):
    email: UserEmail
    email_verification_token: str

class GenericResponse(BaseModel):
    status: bool
    message: str

class UpdateUserByAdminSchema(BaseModel):
    user_id: str
    name: str
    email: UserEmail
    status: str
    server_role_id: Optional[RoleEnum] = None
    is_sso_user: Optional[bool] = None
    
class PlatformLoginMethodsSchema(BaseModel):
    form_login_allowed: bool =True
    sso_login_allowed: bool =True

class PasswordResetResponse(BaseModel):
    status: bool
    message: str
    new_pwd: Optional[str] = ''

class PasswordResetSchema(BaseModel):
    email: UserEmail
    reason: str = Field(default='Reason Not Provided')

class UpdateUserName(BaseModel):
    user_id: str
    name: str
    email: UserEmail

class ADUser(BaseModel):
    email: UserEmail
    name: str
    first_name: str
    last_name: str

class ActiveDirectoryUsers(BaseModel):
    azure_ad_users_list: Union[None, List[ADUser]]
    gcp_ad_users_list: Union[None, List[ADUser]]

class DeleteUserResponse(BaseModel):
    status: bool
    msg: str
    user_id: str