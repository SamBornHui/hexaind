from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field, constr
from typing import List, Optional, Dict, Any
from datetime import datetime
from app.services.workflows.designer.base_schemas import WidgetType

class FeatureParams(BaseModel):
    visualization: str = Field(..., description="Type of visualization")
    color: str = Field(..., description="Color used for visualization")

class Feature(BaseModel):
    fid: int = Field(..., description="Feature ID")
    Name: str = Field(..., description="Name of the feature")
    Value: str = Field(..., description="Value of the feature")
    Params: FeatureParams = Field(..., description="Parameters for the feature")
    Steps: int = Field(..., description="Number of steps")
    selected: bool = Field(..., description="Whether the feature is selected")
    slider: Dict[str, Any] = Field(..., description="Slider settings")
    info: str = Field(..., description="Information about the feature")
    manual: bool = Field(..., description="Whether the feature is manual")

class PostVisualization(BaseModel):
    visualization: str = Field(..., description="Type of post-visualization")
    color: str = Field(..., description="Color used for post-visualization")

class WorkflowItem(BaseModel):
    workflow_id: str = Field(..., description="Workflow item ID")
    retrieve: bool = Field(..., description="Whether to retrieve")
    features: List[Feature] = Field(..., description="List of features")
    post_visualization: PostVisualization = Field(..., description="Post-visualization settings")

class SegmentationConfig(BaseModel):
    original_image: str = Field(..., description="Path to the original image")
    image: str = Field(..., description="Path to the processed image")
    sample_image: str = Field(..., description="Path to the sample image")
    applied: bool = Field(..., description="Whether the process is applied")
    path: bool = Field(..., description="Whether the path is valid")
    orignalpath: str = Field(..., description="Original path to the image")
    draw_val: int = Field(..., description="Draw value")
    popup_val: str = Field(..., description="Popup value")
    popup_unit: str = Field(..., description="Popup unit")
    PixleX: int = Field(..., description="Pixel X coordinate")
    PixleY: int = Field(..., description="Pixel Y coordinate")
    images_names: List[str] = Field(..., description="List of image names")
    workflow: List[WorkflowItem] = Field(..., description="Workflow steps")
    user_id: str = Field(..., description="User ID")


class Image(BaseModel):
    path: str
    folderId: str
    folderName: str

class CategorizationResponse(BaseModel):
    categorization_data: List[Dict]
    
class ImageCategorizationConfig(BaseModel):
    images: List[Image]
    dataset_name: Optional[str] = ""
    modified: Optional[str] = ""
    demo: Optional[str] = ""
    main_file: Optional[str] = ""
    api_type: str

class Annotation(BaseModel):
    annotation_name: str
    label: Optional[str]
    color: Optional[str]
    object_type: str
    annotation_id: int
    coordinates: Dict
    sample_id: str
    project_id: str
    dataset_id: str
    image_path: str
    image_name: Optional[str]
    annotated_image_path: Optional[str]
    annotated_image_name: Optional[str]
    image_dimensions: List[int]
    created_by: str

class Annotations(BaseModel):
    annotations: List[Annotation]

class ChangeAnnotationNameRequest(BaseModel):
    annotation_id: str = Field(..., description="ID of the annotation to be updated")
    annotation_name: str = Field(..., description="New name for the annotation")

class ChangeAnnotationLabelRequest(BaseModel):
    annotation_id: str = Field(..., description="ID of the annotation to be updated")
    label: str = Field(..., description="New label for the annotation")
    color: str = Field(..., description="New color for the annotation")

class UpdateCoordinatesRequest(BaseModel):
    annotation_id: str = Field(..., description="ID of the annotation to be updated",alias="_id")
    coordinates: Dict = Field(..., description="New coordinates for the annotation")

class ImageMaskingObjects(BaseModel):
    coordinates: Dict = Field(..., description="The coordinates defining the region of interest (ROI) in the image.")
    ymax: int = Field(..., description="A placeholder for the 'ymax' value, potentially related to the maximum y-coordinate.")
    path: bool = Field(..., description="A flag indicating if the path is set or not.")
    mask_name: str = Field(..., description="The name of mask")
    apply: bool = Field(..., description="apply mask if true")

class ImageCategory(str,Enum):
    NA = "NA"
    SEM = "SEM"
    OM = "OM"

class ImageMasking(BaseModel):
    image_masking: List[ImageMaskingObjects]
    dataset_id: str = Field(..., description="dataset ID")
    category: ImageCategory = Field(..., description="image type")
    image: str = Field(..., description="The path to the modified image.")
    base_image: str = Field(..., description="The path to the base image.")
    
    
class MaskedObjRequest(BaseModel):
    categorized_data_id: str = Field(..., description="dataset ID")
    image: str = Field(..., description="The path to the modified image.")
    category: ImageCategory = Field(..., description="image type")
    reset_from: Optional[str] = Field(default=None, description="reset from base image")
    
class DeleteMaskObjects(BaseModel):
    categorized_data_id: str = Field(..., description="dataset ID")
    image: str = Field(..., description="The path to the modified image.")
    category: ImageCategory = Field(..., description="image type")
    # mask_obj_id: str = Field(..., description="mask_obj_id", alias="_id")
    coordinates: Dict = Field(..., description="The coordinates defining the region of interest (ROI) in the image.")
    
class UpdateMaskConfig(BaseModel):
    categorized_data_id: str = Field(..., description="dataset ID")
    image: str = Field(..., description="The path to the modified image.")
    category: ImageCategory = Field(..., description="image type")
    # mask_obj_id: str = Field(..., description="mask_obj_id", alias="_id")
    mask_name:str = Field(..., description="mask name")
    old_coordinates: Dict = Field(..., description="The coordinates defining the region of interest (ROI) in the image.")
    new_coordinates: Dict = Field(..., description="The coordinates defining the region of interest (ROI) in the image.")
    apply_change : bool = Field(..., description="apply")
    
class Masks(BaseModel):
    image_masking: List[ImageMaskingObjects]
    categorized_data_id: str = Field(..., description="dataset ID")
    category: ImageCategory = Field(..., description="image type")
    image: str = Field(..., description="The path to the modified image.")
    base_image: str = Field(..., description="The path to the base image.")
    apply_all: bool = Field(..., description="if apply then apply to all images")


class QuantTechRequest(BaseModel):
    path_image: List[str]
    cutoff: int = Field(..., description="cut off value")
    local_state_1: int = Field(..., description="local_state_1 value")
    quantTech: str = Field(..., description="Name of applied quantification technique")
    user_id: str =Field(..., description="userid of the session user")
    metadata: str = Field(..., description="The path to the image metadata.")
    local_state_2: Optional[int] = Field(..., description="local_state_2 value")
    coarsening: Optional[int] = Field(None, description="coarsening for the for SpatialStatistics")
    ang_int: Optional[int] = Field(None, description="ang_int for the for SpatialStatistics")

class BatchProcessingRequest(BaseModel):
    path_image: List[str]
    cutoff: int = Field(..., description="cut off value")
    quantTech: str = Field(..., description="Name of applied quantification technique")
    datasetId: str = Field(..., description="Id of the dataset")
    metadata: Optional[str] = Field(..., description="The path to the image metadata.")
    local_states: List = Optional[List[List[int]]]
    coarsening: Optional[int] = Field(None, description="coarsening for the for SpatialStatistics")
    ang_int: Optional[int] = Field(None, description="ang_int for the for SpatialStatistics")
    
class SpatialStatisticsConfig(BaseModel):
    version: Optional[str] = Field(default="1.0", description="Version of the image dataset")
    widget_type: Literal[WidgetType.SPATIAL_STATISTICS]
    cutoff: int = Field(..., description="cut off value")
    quantTech: str = Field(..., description="Name of applied quantification technique")
    datasetId: str = Field(..., description="Id of the dataset")
    metadata: str = Field(..., description="The path to the image metadata.")
    local_states: List = Optional[List[List[int]]]
    coarsening: Optional[int] = Field(None, description="coarsening for the for SpatialStatistics")
    ang_int: Optional[int] = Field(None, description="ang_int for the for SpatialStatistics")

class SpatialStatisticsResponse(BaseModel):
    exception_detail: Optional[str] = Field(None, description="Exception detail for the for SpatialStatistics")
    tabular_path: Optional[Path] = Field(None, description="tabular result of SpatialStatistics widget")


class DeleteSegmentedAnnotation(BaseModel):
    imaga_path : str = Field(..., description="imaga_path")
    unique_object_id : str = Field(..., description="Unique_object_id")

class WorkflowImagesPathRequest(BaseModel):
    path: str = Field(..., description="imaga_path")
    