from pydantic import BaseModel,Field
from typing import Optional
from app.services.data.assets.datasets.schemas import (
    AccessMode)


class CreateDatasetDuplicate(BaseModel):
    user_id: str = Field(...,description = 'user_id'),
    datasetId: str = Field(...,description = 'dataset_id'),
    datasetName: str = Field(...,description= 'dataset_name'),
    folderPath: str = Field(None,description= 'folder path')
    type: str = Field(None,description= 'type')


class CreateDatasetDuplicateRespose(BaseModel):
    status: str = Field(None,description= 'status')
    message: str = Field(None,description= 'message')


class CreateFolder(BaseModel):
    destination_folder: str = Field(None,description = "destination folder")
    folder_name : str = Field(... , description = "folder name")
    description: str = Field(default='',description="description of folder")
    user_id: str = Field(...,description="user id")
    access_mode: AccessMode = Field(default=AccessMode.EXTERNAL, description="access mode")

class CreateFolderResponse(BaseModel):
    status: str = Field(None,description = "status")
    folder_creation_path : str = Field(None,description = "folder_creation_path")

class CreateFolderResponse(BaseModel):
    destination_folder: str = Field(None,description="destination folder")
    folder_name : str = Field(None , description="folder name")

class MoveAssets(BaseModel):
    source: str = Field(... , description="folder name")
    destination: str = Field(... , description="folder name")
    id: str  = Field(... , description="file/folder id")
    type: str = Field(... , description="file/folder type")

class MoveAssetsResponse(BaseModel):
    status: str = Field(None , description="status")
    message: str = Field(None , description="message")


class RenameAssets(BaseModel):
    source: str = Field(... , description="path")
    new_name: str = Field(... , description="new name")
    dataset_type: Optional[str] = ""
    description: Optional[str] = ""

class RenameAssetsResponse(BaseModel):
    status: str = Field(None , description="status")
    message: str = Field(None , description="message")


class DeleteAssets(BaseModel):
    source: str = Field(..., description='path')
    dataset_type: Optional[str] = ""

class DeleteAssetsResponse(BaseModel):
    status: str = Field(None , description="status")
    message: str = Field(None , description="message")


class DownloadAssets(BaseModel):
    source: str = Field(..., description="path")


class MimeTypesDownload:
    txt: str = "text/plain"
    csv: str = "text/csv"
    parquet: str = "application/octet-stream"
    py: str = "text/x-python"
    json: str = "text/json"
    zip: str = "zip"

    @classmethod
    def get_mime_type(cls, extension: str) -> str:
        return getattr(cls, extension.lstrip("."))


class dataset_extension:
    CSV = ".csv"
    PARQUET = ".parquet"
    JSON = ".json"
    TEXT = ".txt"

    @classmethod
    def get_all_dataset_extension(cls) -> dict:
        attributes = dir(cls)
        datasets_types = tuple(
            getattr(cls, attr)
            for attr in attributes
            if not callable(getattr(cls, attr)) and not attr.startswith("__")
        )
        return datasets_types
