from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Literal
from pydantic import BaseModel, Field, conlist

from app.services.micron.data_catalog.fd_trace.schemas import *

class MicronDataCatalogSessionInput(BaseModel):
     
     project_id: str = Field(..., description="End date for the data pull")
     
     name: str = Field(..., description="End date for the data pull")

     description: str = Field(..., description="End date for the data pull")

     data_source_type: DataSourceType

class MicronDataCatalogSessionOutput(BaseModel):
     
     session_id: str = Field(..., description="record id of the data catalog data pull session")

     data_pull_job_id: str = Field(..., description="Data Pull job id attached to the current session")

class MicronDataCatalog(MicronDataCatalogSessionInput):

     id: Optional[str] = Field(default=None, description="data catalog session Id", alias="_id")

     user_id: str = Field(..., description="End date for the data pull")
     
     created_at: datetime = Field(..., description="End date for the data pull")

     owner_name: str = Field(..., description="User name")

     data_pull_job_id: str = Field(name="each stage config", default=None)

     is_deleted: bool = Field(description="flag to check if document is deleted", default=False)

class GetAllMicronDataCatalogSessionResponse(BaseModel):

    datacatalog_sessions: List[MicronDataCatalog]

    total_count: int
