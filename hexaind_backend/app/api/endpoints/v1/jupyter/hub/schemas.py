from __future__ import annotations

from datetime import datetime
from enum import Enum, Flag, auto
from typing import Any, List, Optional

from bson import ObjectId
from bson.errors import InvalidId
from pydantic import (
    BaseModel,
    GetCoreSchemaHandler,
    GetJsonSchemaHandler,
    ValidationInfo,
    computed_field,
    Field
)
from pydantic.json_schema import JsonSchemaValue
from pydantic_core import CoreSchema, core_schema
from pydantic_core.core_schema import ValidationInfo, str_schema

from app.config.env_vars import environment, jupyterhub_environment


class PydanticObjectId(ObjectId):
    """
    Object Id field. Compatible with Pydantic.
    """

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v, _: ValidationInfo):
        if isinstance(v, bytes):
            v = v.decode("utf-8")
        try:
            return PydanticObjectId(v)
        except (InvalidId, TypeError):
            raise ValueError("Id must be of type PydanticObjectId")

    @classmethod
    def __get_pydantic_core_schema__(
        cls, source_type: Any, handler: GetCoreSchemaHandler
    ) -> CoreSchema:  # type: ignore
        return core_schema.json_or_python_schema(
            python_schema=core_schema.with_info_plain_validator_function(cls.validate),
            json_schema=str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(
                lambda instance: str(instance)
            ),
        )

    @classmethod
    def __get_pydantic_json_schema__(
        cls,
        schema: core_schema.CoreSchema,
        handler: GetJsonSchemaHandler,  # type: ignore
    ) -> JsonSchemaValue:
        json_schema = handler(schema)
        json_schema.update(
            type="string",
            example="5eb7cf5a86d9755df3a6c593",
        )
        return json_schema


class JupyterServerResponse(BaseModel):
    status: int
    message: str


class JupyterServerStatus(str, Enum):
    @staticmethod
    def _generate_next_value_(
        name: str, start: int, count: int, last_values: List[Any]
    ) -> Any:
        return name.upper()

    CREATING = auto()
    RUNNING = auto()
    STOPPED = auto()


class JupyterServerActions(Flag):
    START = auto()
    STOP = auto()
    CREATE = auto()
    DELETE = auto()


class JupyterServerCreateBody(BaseModel):
    name: str
    description: str


class JupyterNBPathType(str, Enum):
    MASTER = "MASTER"
    CLONE = "CLONE"


class JupyterNBTypeObj(BaseModel):
    name: str
    description: str = ''
    status: str = 'unknown'
    nb_type: JupyterNBPathType = JupyterNBPathType.MASTER
    launch_url: str
    relative_path: str
    last_activity: Optional[datetime] = None


class JupyterNBResponse(BaseModel):
    result: List[JupyterNBTypeObj]

class JupyterServer(BaseModel):
    _id: PydanticObjectId | None = None
    name: str
    description: str
    project_id: str
    status: JupyterServerStatus
    last_activity: str = ""
    notebooks: Optional[List[JupyterNBTypeObj]] = None

    @computed_field
    def launch_url(self) -> str:
        return f"{jupyterhub_environment.redirect_url}user/{self.project_id}" #?token={jupyterhub_environment.api_token}"
    
class JupyterNBCloneAndPromotePaths(BaseModel):
    source: str
    destination: str

class JupyterNBCommonResponse(BaseModel):
    status: bool
    message: str

class JupyterNBCreateRequest(BaseModel):
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    relative_path: Optional[str] = None


class FreePortResponse(BaseModel):
    status: bool
    message: str
    port: int = None