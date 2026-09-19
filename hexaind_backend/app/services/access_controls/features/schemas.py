from enum import Enum
from typing import Optional, List

from pydantic import BaseModel, Field


class HTTPEndPointMethodType(str, Enum):
    GET = 'GET'
    POST = 'POST'
    PATCH = 'PATCH'
    PUT = 'PUT'
    DELETE = 'DELETE'


# This DB will be updated by developer
class EndPointsFeatureMappings(BaseModel):
    version: Optional[str] = Field(
        default="1.0", description="roles features map schema version")
    id: Optional[str] = Field(default=None, description="Id", alias="_id")

    endpoint: str
    method: HTTPEndPointMethodType
    exclude: bool = False
    bypassed_server_roles: List[int] = Field(default=[], description="Allowed server level role values")
    features_keys: Optional[List[List[str]]] = Field(default=[])
