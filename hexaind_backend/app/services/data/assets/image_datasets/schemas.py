from pydantic import BaseModel, Field, root_validator
from enum import Enum
from typing import List, Literal, Optional
from uuid import uuid4
from app.services.workflows.designer.base_schemas import WidgetType
FOLDER_STRUCTURE_JSON_FILE = 'folder_struct.json' 

class ImageFileType(str, Enum):
    JPG = ".jpg"
    JPEG = ".jpeg"
    PNG = ".png"
    TIFF = ".tiff"
    TIF = ".tif"
    BMP = ".bmp"
    gif = ".gif"
    RAW = ".raw"
    WEBP = ".webp"
    svg = ".svg"



MEDIA_TYPES = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    '.bmp': 'image/bmp',
    '.gif': 'image/gif',
    '.raw': 'image/x-raw',
    '.webp': 'image/webp',
    '.svg': 'image/svg+xml'
    }

class ImageMetaDataExtn(str, Enum):
    TIFF_METADATA = '.hdr'

class MetaDataExtns(str, Enum):
    CSV = ".csv"

class FileNode(BaseModel):
    name: str
    is_folder: bool
    extension: Optional[str] = None
    size: Optional[int] = None
    parent: Optional[str] = None
    created_by: Optional[str] = ""
    last_modified_at: Optional[str] = ""
    type: Optional[str] = ""
    dataset_type: Optional[str] = "IMAGE"
    user_id: Optional[str] = ""
    created_at: Optional[str] = ""
    full_path: Optional[str] = ""
    children: Optional[List['FileNode']] = []  # Recursive type definition

    class Config:
        from_attributes = True

FileNode.model_rebuild()

class ImageDatasetSubFolders(str, Enum):
    UPLOADS = "uploaded"
    THUMBNAILS = "thumbnails"
    IMAGES_METADATA = "images_metadata"
    CSV_METADATA = "csv_metadata"

class FileUploadDetails(BaseModel):
    file_path: str
    user_id: str
    user_name: str
    is_folder: Optional[bool] = False
    uid: Optional[str] = ""
    dataset_id: Optional[str] = ""

class ImagesUploadResponse(BaseModel):
    base_folder: str
    uploads: Optional[str] = ""
    thumbnails: Optional[str] = ""
    images_metadata: Optional[str] =""
    uploaded_file_det_list: Optional[List[FileUploadDetails]] = []
    folder_struct: Optional[List[FileNode]] = []
    csv_metadata: Optional[List[FileNode]] = []

class ImageDatasets(BaseModel):
    dataset_id: str = Field(..., description="dataset ID")
    dataset_name: str = Field(..., description="dataset name")
    dataset_location: str = Field(..., description="dataset location")
    segmented: bool = False
    defect_metadata_path: Optional[str] = Field(..., description="metadata file path")
   
class ImagesDatasetResponse(BaseModel):
    image_datasets:List[ImageDatasets] = []


class ImgDatasets(BaseModel):
    dataset_id: str = Field(..., description="dataset ID")
    dataset_name: str = Field(..., description="dataset name")
    defect_metadata_path: Optional[str] = Field(..., description="metadata file path")
    
class ImageDatasetConfig(BaseModel):
    version: Optional[str] = Field(default="1.0", description="Version of the image dataset")
    widget_type: Literal[WidgetType.IMAGE_DATASET]
    image_datasets:List[ImgDatasets]
    image_type: str = Field(..., description="imae type")

class RegionPropertiesConfig(BaseModel):
    version: Optional[str] = Field(default="1.0", description="Version of the image dataset")
    widget_type: Literal[WidgetType.REGION_PROPERTY]
    region_properties: List[str] = Field(default="", description="region properties for the image")