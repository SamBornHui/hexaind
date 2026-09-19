from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, RootModel


class SnowFlakeDatasetTypes(str, Enum):
    TABLE = "TABLE"
    QUERY = "QUERY"


class AuthenticationResponse(BaseModel):
    status: bool
    message: str


class SFGenericResponse(BaseModel):
    status: bool
    message: str

class SFDatasetTableConfig(BaseModel):
    database_name: str
    schema_name: str
    table_name: str

class SFDatasetQueryConfig(BaseModel):
    query: str = Field(..., description="Snowflake SQL Query output to be copied")
    query_params: Dict[str, Any] = {}


class SFGetDbsRequest(BaseModel):
    snowflake_connector_id: str


class SFGetDbsResponse(SFGenericResponse):
    databases_list: List[str] = []


class SFGetDbSchemasRequest(BaseModel):
    snowflake_connector_id: str
    database_name: str


class SFGetDbSchemasResponse(SFGenericResponse):
    schemas_list: List[str] = []


class SFGetDbTablesRequest(BaseModel):
    snowflake_connector_id: str
    database_name: str
    schema_name: str


class SFGetDbTablesResponse(SFGenericResponse):
    tables_list: List[str] = []


class SFPreviewRequest(BaseModel):
    snowflake_connector_id: str
    database_name: Optional[str] = ""
    schema_name: Optional[str] = ""
    table_name: Optional[str] = ""
    query_config: Optional[SFDatasetQueryConfig] = None

class SFPreviewResponse(SFGenericResponse):
    columns: List
    data: List