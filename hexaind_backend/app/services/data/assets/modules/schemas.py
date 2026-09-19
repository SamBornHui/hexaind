from pydantic import BaseModel, Field, constr
from typing import List, Optional, Any, Dict
from enum import Enum
from pathlib import Path
import datetime


class ModuleType(str, Enum):
    PYTHON = "PYTHON"


class UploadStatus(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    INPROGRESS = "INPROGRESS"


class AccessMode(str, Enum):
    INTERNAL = "INTERNAL"
    EXTERNAL = "EXTERNAL"


class UploadStats(BaseModel):
    percentage: str


class ModuleExtenstion(str, Enum):

    PY = "PY"

    ZIP = "ZIP"


class ModuleLocation(BaseModel):
    extension: ModuleExtenstion
    path: str
    size: Optional[str] = ""
    last_modified_by: Optional[str] = ""
    last_modified_at: Optional[datetime.datetime] = None


class FunctionArgument(BaseModel):
    name: str
    type: Optional[str] = None
    kind: Optional[str] = None
    default_value: Optional[Any] = None


class CustomCodeMetadata(BaseModel):
    file_names: List[str]
    entry_file: str
    function_name: str
    function_signature: str
    function_inputs: Optional[List[FunctionArgument]] = Field(default=[])
    function_outputs: Optional[List[str]] = Field(default=[])
    pydoc_string: Optional[str] = Field(
        default="", description="pydoc_string for method"
    )
    validation_request_id: Optional[str] = Field(default=None)
    is_validated: Optional[bool] = Field(
        default=False, description="Updated post validation"
    )


class CustomCodeMetadataResponse(BaseModel):
    metadata: Optional[CustomCodeMetadata] = Field(
        default=None, description="Contains metadata fetched for request file"
    )
    help_details: Optional[Dict[str, str]] = Field(
        default={}, description="Contains parsed pydoc string details"
    )
    succeeded: bool
    message: str


class Module(BaseModel):
    id: Optional[str] = Field(default=None, description="Module Id", alias="_id")
    version: Optional[str] = Field(default="1.0")
    user_id: str
    project_id: str
    site_id: str
    action_id: str
    name: str
    description: str
    module_type: ModuleType
    upload_status: UploadStatus
    upload_stats: UploadStats
    metadata: Optional[CustomCodeMetadata] = Field(default=None)
    created_at: datetime.datetime
    module_location: ModuleLocation
    access_mode: AccessMode
    tags: List[str]
    created_by: Optional[str] = None


class ModulesListResponse(BaseModel):

    modules: List[Module]

    total_count: int


class ModuleUploadResponse(BaseModel):

    module_id: str


class FileDetails(BaseModel):
    file_name: str
    file_path: Path


class FileDetailsList(BaseModel):
    files: List[FileDetails]


class FileContentResponse(BaseModel):
    content: str


class CreateModuleRequest(BaseModel):
    file_path: str
    metadata: CustomCodeMetadata
    name: str


class CreateModuleResponse(BaseModel):
    module_id: Optional[str] = Field(default=None)
    succeeded: bool
    message: str


class CodeValidationParameters(BaseModel):
    param_name: Optional[str] = Field(default=None)
    type: str
    value: str  # can use both relative and absolute paths for validation.


class CodeValidationRequest(BaseModel):
    file_path: str
    metadata: CustomCodeMetadata
    validation_inputs: List[CodeValidationParameters]
    validation_outputs: List[CodeValidationParameters]


class CodeValidationResponse(BaseModel):
    succeeded: bool
    message: str


class FilePathRequest(BaseModel):
    file_path: str


class FileCopyRequest(BaseModel):
    source_path: str
    destination_path: str


class FileCopyResponse(BaseModel):
    status: bool
    message: str


class VizFolderDetail(BaseModel):
    folder_path: Path
    trial_index: int
